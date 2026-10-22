import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
import matplotlib

class GradCAM:
    def __init__(self, model, target_layer=None):
        self.model = model
        self.model.eval()

        # In torchvision efficientnet_v2_s, model.features[-1] is Conv2dNormActivation (last conv block)
        if target_layer is None:
            self.target_layer = model.features[-1]
        else:
            self.target_layer = target_layer

        self.activations = None
        self.gradients = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            # grad_output is a tuple; grad_output[0] is gradient w.r.t output
            self.gradients = grad_output[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(self, input_tensor, target_class_idx=None):
        """
        input_tensor: 1 x 3 x H x W normalized tensor with requires_grad
        target_class_idx: int (if None, uses predicted class)
        returns: (normalized numpy 2D array [0, 1], target_class_idx, raw logits [1, num_classes])
        """
        self.model.zero_grad()

        # Forward pass
        output = self.model(input_tensor)

        if target_class_idx is None:
            target_class_idx = output.argmax(dim=1).item()

        # Target score
        score = output[0, target_class_idx]
        score.backward()

        # Global average pooling of gradients
        # gradients: [1, C, H, W]
        # activations: [1, C, H, W]
        gradients = self.gradients
        activations = self.activations

        weights = torch.mean(gradients, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * activations, dim=1, keepdim=True)

        # ReLU to keep only features that positively contribute to the class
        cam = F.relu(cam)

        # Normalize
        cam = cam.squeeze().cpu().numpy()
        cam_min, cam_max = np.min(cam), np.max(cam)
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam, target_class_idx, output.detach()

    def overlay_heatmap(self, original_image: Image.Image, cam: np.ndarray, alpha=0.45, colormap='jet'):
        """
        Overlays the Grad-CAM heatmap onto the original PIL image.
        """
        orig_w, orig_h = original_image.size

        # Resize heatmap to original image dimensions
        cam_pil = Image.fromarray((cam * 255).astype(np.uint8))
        cam_resized = cam_pil.resize((orig_w, orig_h), resample=Image.Resampling.BILINEAR)
        cam_arr = np.array(cam_resized) / 255.0

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
