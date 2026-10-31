import json
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import numpy as np
import cv2

from src.model import get_model
from src.treatments import get_treatment_details
from src.gradcam import GradCAM
from src.lesions import lesion_map
from src.severity import SeverityEngine

# Checkpoint served by the app and the architecture it was trained with (see src/model.py)
DEFAULT_MODEL_PATH = 'models/best_model.pth'
DEFAULT_ARCH = 'baseline'

class CropDiseasePredictor:
    def __init__(self, model_path=DEFAULT_MODEL_PATH, class_names_path='class_names.json', arch=DEFAULT_ARCH):
        self.arch = arch
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        with open(class_names_path, 'r') as f:
            self.class_names = json.load(f)
            
        self.model = get_model(len(self.class_names), pretrained=False, arch=arch).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
        self.model.eval()
        
        # Initialize Grad-CAM
        self.gradcam = GradCAM(self.model)
        
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def validate_leaf_specimen(self, pil_image: Image.Image):
        """
        Comprehensive Botanical Validation:
        1. Checks for non-plant images (documents, screenshots, blank surfaces, arbitrary objects).
        2. Detects multiple leaves or cluttered foliage (branches, canopies, multiple leaf clusters).
        Returns: (is_valid: bool, error_code: str, error_message: str)
        """
        img = np.array(pil_image.convert('RGB'))
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        total_pixels = img.shape[0] * img.shape[1]
        
        # Botanical pigment color masks
        # Green foliage
        green_mask = (h >= 25) & (h <= 95) & (s >= 30) & (v >= 30)
        # Yellow, chlorotic, or rust lesions
        yellow_rust_mask = (h >= 10) & (h < 25) & (s >= 25) & (v >= 30)
        # Necrotic brown tissue
        brown_mask = ((h < 10) | (h > 170)) & (s >= 20) & (v >= 20) & (v <= 180)
        
        plant_mask = (green_mask | yellow_rust_mask | brown_mask).astype(np.uint8) * 255
        plant_ratio = np.sum(plant_mask > 0) / total_pixels
        
        # 1. Non-plant / document / screen check
        # In a text document or computer screenshot, plant ratio is essentially 0 (< 5%)
        if plant_ratio < 0.05:
            return False, 'non_plant', 'No botanical plant leaf detected in the image (it appears to be a document, screenshot, or non-botanical object).'
            
        avg_leaf_sat = np.mean(s[plant_mask > 0]) / 255.0 if np.sum(plant_mask > 0) > 0 else 0
        if avg_leaf_sat < 0.15:
            return False, 'non_plant', 'Natural plant leaf pigmentation not detected. Please upload an image of a real agricultural leaf.'
            
        # 2. Multi-leaf / cluttered foliage detection
        # Morphological closing to join parts of the same leaf blade
        kernel_size = max(5, int(min(img.shape[:2]) * 0.025))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        cleaned_mask = cv2.morphologyEx(plant_mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False, 'no_leaf', 'No distinct botanical leaf structure could be segmented.'
            
        # Extract areas of distinct leaf clusters (larger than 1.5% of the frame)
        leaf_areas = [cv2.contourArea(c) for c in contours]
        significant_areas = sorted([a for a in leaf_areas if a > (0.015 * total_pixels)], reverse=True)
        
        # Condition A: Multiple large distinct leaves present in the frame
        if len(significant_areas) >= 2:
            largest = significant_areas[0]
            second = significant_areas[1]
            # If the secondary leaf is substantial (> 8% of frame and > 35% of the primary leaf)
            if second > (0.08 * total_pixels) and (second / largest > 0.35):
                return False, 'multiple_leaves', f'Multiple leaves detected in the frame ({len(significant_areas)} separate leaf structures identified). The AI requires a close-up of a single isolated leaf for accurate pathology diagnosis.'
                
        # Condition B: Cluttered foliage / multiple small leaves (e.g. tree branch, bush, distant field)
        if len(significant_areas) >= 5:
            return False, 'multiple_leaves', f'Cluttered foliage / multiple leaves detected ({len(significant_areas)} separate leaves found on screen). Please zoom in or capture one single leaf.'
            
        return True, 'valid_single_leaf', 'Valid single leaf detected.'

    def predict(self, image_input):
        """
        Runs comprehensive diagnosis:
        - Image validation (rejects non-plant & multiple-leaves images)
        - Neural classification
        - Grad-CAM visual attention mapping
        - Treatment extraction
        """
        if isinstance(image_input, Image.Image):
            pil_image = image_input.convert('RGB')
        else:
            pil_image = Image.open(image_input).convert('RGB')
            
        is_leaf, error_code, validity_msg = self.validate_leaf_specimen(pil_image)
        
        # If the image is invalid (non-plant or multiple leaves), abort inference early
        if not is_leaf:
            return {
                'is_valid_leaf': False,
                'error_code': error_code,
                'validity_message': validity_msg,
                'original_image': pil_image,
                'top_predictions': [],
                'treatment': None,
                'gradcam_image': None
            }
        
        # Preprocess tensor for model
        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        tensor.requires_grad = True
        
        # Single forward/backward pass: Grad-CAM returns the logits it computed, so the
        # classification and the heatmap always come from the same forward pass.
        cam_map = None
        try:
            cam_map, _, outputs = self.gradcam.generate_heatmap(tensor)
            gradcam_image = None
        except Exception as e:
            print(f"Grad-CAM generation error: {e}")
            with torch.no_grad():
                outputs = self.model(tensor)
            gradcam_image = pil_image
            
        probs = F.softmax(outputs, dim=1)[0]
        top_probs, top_indices = torch.topk(probs, 3)
        
        top_predictions = []
        for i in range(3):
            cls_key = self.class_names[top_indices[i].item()]
            clean_display = cls_key.replace('___', ' - ').replace('_', ' ')
            top_predictions.append({
                'class': cls_key,
                'clean_name': clean_display,
                'confidence': float(top_probs[i].item() * 100)
            })
            
        best_class = top_predictions[0]['class']
            
        # Lesion-area severity estimate (% leaf surface area); needs a valid Grad-CAM map
        severity_info = None
        if cam_map is not None:
            try:
                severity_info = SeverityEngine.calculate_severity(pil_image, cam_map, best_class)
            except Exception as e:
                print(f"Severity calculation error: {e}")
        if severity_info is None:
            severity_info = SeverityEngine.unavailable(best_class)

        # Lesion-guided Grad-CAM: the coarse class map is sharpened with the pixel-level lesion mask,
        # so heat lands on the spots the model attended to (cf. Guided Grad-CAM).
        if cam_map is not None:
            try:
                if severity_info.get('leaf_mask') is not None:
                    leaf, lesions = severity_info['leaf_mask'], severity_info['lesion_mask'] > 0
                else:
                    leaf, lesions, _ = lesion_map(pil_image)
                    if 'healthy' in best_class.lower():
                        lesions = None
                gradcam_image = self.gradcam.overlay_heatmap(pil_image, cam_map, alpha=0.5, leaf_mask=leaf, lesion_mask=lesions)
            except Exception as e:
                print(f"Lesion-guided Grad-CAM error: {e}")
                gradcam_image = self.gradcam.overlay_heatmap(pil_image, cam_map, alpha=0.45)

        # Get structured treatment data
        treatment_info = get_treatment_details(best_class)
        
        return {
            'is_valid_leaf': True,
            'error_code': None,
            'validity_message': validity_msg,
            'top_predictions': top_predictions,
            'treatment': treatment_info,
            'severity': severity_info,
            'gradcam_image': gradcam_image,
            'original_image': pil_image
        }
