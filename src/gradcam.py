import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image, ImageFilter
import matplotlib

class GradCAM:
    """
    Augmentation-smoothed, multi-layer Grad-CAM.

    Plain Grad-CAM on the last 7x7 map (1 cell = 32x32 px) peaks beside lesions rather than on them and
    leaves holes. Here the map is averaged over flipped / rescaled copies of the input (test-time augmentation
    smoothing) and fused across three depths: stage 5 (14x14, lesion-level detail, LayerCAM weighting),
    stage 6 and the final block (7x7, class-level coverage, Grad-CAM weighting).
    """
    LAYER_WEIGHTS = {5: 0.5, 6: 0.25, 7: 0.25}
    SCALES = (224, 288, 352)

    def __init__(self, model, target_layer=None):
        self.model = model
        self.model.eval()

        # torchvision efficientnet_v2_s: features[5] 160ch @14x14, features[6] 256ch @7x7, features[7] 1280ch @7x7
        if target_layer is None and hasattr(model, 'features') and len(model.features) >= 8:
            self.layers = {i: model.features[i] for i in self.LAYER_WEIGHTS}
            self.weights = self.LAYER_WEIGHTS
        else:
            self.layers = {7: target_layer if target_layer is not None else model.features[-1]}
            self.weights = {7: 1.0}

        self.activations = {}
        self.gradients = {}
        self._register_hooks()

    def _register_hooks(self):
        for i, layer in self.layers.items():
            def forward_hook(module, input, output, i=i):
                self.activations[i] = output.detach()

            def backward_hook(module, grad_input, grad_output, i=i):
                self.gradients[i] = grad_output[0].detach()

            layer.register_forward_hook(forward_hook)
            layer.register_full_backward_hook(backward_hook)

    def _layer_cams(self, input_tensor, target_class_idx):
        """One forward/backward pass; returns {layer: cam [1,1,H,W] scaled to [0, 1]} and the logits."""
        self.model.zero_grad()
        output = self.model(input_tensor)
        if target_class_idx is None:
            target_class_idx = output.argmax(dim=1).item()
        output[0, target_class_idx].backward()

        cams = {}
        for i in self.layers:
            A, G = self.activations[i], self.gradients[i]
            if i == 7:
                # Grad-CAM: channel weights = spatially averaged gradients
                cam = (G.mean(dim=(2, 3), keepdim=True) * A).sum(1, keepdim=True)
            else:
                # LayerCAM: per-location positive gradients keep fine detail at shallower layers
                cam = (F.relu(G) * A).sum(1, keepdim=True)
            cam = F.relu(cam)
            cam = F.interpolate(cam, size=input_tensor.shape[-2:], mode='bilinear', align_corners=False)
            cams[i] = cam / (cam.max() + 1e-8)
        return cams, target_class_idx, output.detach()

    def generate_heatmap(self, input_tensor, target_class_idx=None):
        """
        input_tensor: 1 x 3 x H x W normalized tensor
        target_class_idx: int (if None, uses predicted class)
        returns: (normalized numpy 2D array [0, 1], target_class_idx, raw logits [1, num_classes])
        """
        H, W = input_tensor.shape[-2:]
        base = input_tensor.detach()

        # Un-augmented pass first: its logits are the prediction returned to the caller
        _, target_class_idx, logits = self._layer_cams(base.clone().requires_grad_(True), target_class_idx)

        total = torch.zeros(1, 1, H, W, device=base.device)
        for size in self.SCALES:
            scaled = F.interpolate(base, size=(size, size), mode='bilinear', align_corners=False)
            for flip_h in (False, True):
                for flip_v in (False, True):
                    t = scaled
                    if flip_h:
                        t = t.flip(3)
                    if flip_v:
                        t = t.flip(2)
                    cams, _, _ = self._layer_cams(t.clone().requires_grad_(True), target_class_idx)
                    for i, cam in cams.items():
                        if flip_v:
                            cam = cam.flip(2)
                        if flip_h:
                            cam = cam.flip(3)
                        cam = F.interpolate(cam, size=(H, W), mode='bilinear', align_corners=False)
                        total += self.weights[i] * cam / (cam.max() + 1e-8)

        cam = total.squeeze().cpu().numpy()
        cam_min, cam_max = np.min(cam), np.max(cam)
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam, target_class_idx, logits

    def overlay_heatmap(self, original_image: Image.Image, cam: np.ndarray, alpha=0.45, colormap='jet',
                        leaf_mask=None, lesion_mask=None):
        """
        Overlays the Grad-CAM heatmap onto the original PIL image.
        leaf_mask / lesion_mask (bool, image size, optional): heat outside the leaf is removed, and inside it
        the coarse map is concentrated onto the detected lesion pixels, so hot colours sit on the spots.
        """
        orig_w, orig_h = original_image.size

        # Resize heatmap to original image dimensions
        cam_pil = Image.fromarray((cam * 255).astype(np.uint8))
        cam_resized = cam_pil.resize((orig_w, orig_h), resample=Image.Resampling.BILINEAR)
        cam_arr = np.array(cam_resized) / 255.0

        if leaf_mask is not None:
            if lesion_mask is not None and lesion_mask.any():
                # Soften the lesion mask slightly so spots read as warm blobs rather than hard pixels
                sigma = max(1.0, min(orig_w, orig_h) / 300)
                guide = np.array(Image.fromarray(lesion_mask.astype(np.uint8) * 255)
                                 .filter(ImageFilter.GaussianBlur(sigma))) / 255.0
                guide = np.clip(guide * 1.5, 0, 1)
                cam_arr = cam_arr * (0.15 + 0.85 * guide)
            cam_arr = cam_arr * leaf_mask
            if cam_arr.max() > 1e-8:
                # gamma < 1 lifts lesions in moderately attended regions so they stay visible
                cam_arr = (cam_arr / cam_arr.max()) ** 0.6

        # Apply colormap (matplotlib.cm.get_cmap is removed in Matplotlib 3.11)
        cmap = matplotlib.colormaps[colormap]
        colored_cam = cmap(cam_arr)[:, :, :3]  # Drop alpha from colormap -> [H, W, 3] in [0, 1]
        colored_cam = (colored_cam * 255).astype(np.uint8)

        # Convert original to RGB array
        orig_arr = np.array(original_image.convert('RGB'))

        # Blend
        blended = (1 - alpha) * orig_arr + alpha * colored_cam
        blended = np.clip(blended, 0, 255).astype(np.uint8)

        return Image.fromarray(blended)
