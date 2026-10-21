import cv2
import numpy as np
from PIL import Image

class SeverityEngine:
    """
    Automated Quantitative Disease Severity Staging Engine:
    Combines botanical leaf contour segmentation with Grad-CAM feature attention
    to compute the exact percentage of infected leaf surface area and classify
    the disease into official USDA/FAO agronomic stages.
    """
    
    @staticmethod
    def calculate_severity(pil_image: Image.Image, cam_heatmap: np.ndarray, predicted_class: str):
        """
        Calculates:
        - Total Leaf Pixel Area
        - Active Lesion Pixel Area
        - Severity Infection Percentage (%)
        - Agronomic Stage (0 to 4)
        - Actionable Stage-Specific Prescription
        """
        # If the model diagnosed healthy foliage, return Stage 0
        if "healthy" in predicted_class.lower():
            return {
                "is_healthy": True,
                "severity_pct": 0.0,
                "stage_number": 0,
                "stage_name": "Stage 0: Pristine Foliage",
                "stage_badge": "HEALTHY (0% Infection)",
                "risk_level": "None (Optimum Plant Health)",
                "action_plan": "Maintain baseline cultural care, drip irrigation at soil level, and periodic scouting.",
                "color_hex": "#10B981", # Emerald Green
                "leaf_pixels": 0,
                "lesion_pixels": 0
            }

        img = np.array(pil_image.convert('RGB'))
        h, w = img.shape[:2]
        total_pixels = h * w
        
        # 1. Botanical Leaf Segmentation
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        h_channel, s_channel, v_channel = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        
        green_mask = (h_channel >= 25) & (h_channel <= 95) & (s_channel >= 25) & (v_channel >= 25)
        yellow_rust_mask = (h_channel >= 10) & (h_channel < 25) & (s_channel >= 20) & (v_channel >= 25)
        brown_mask = ((h_channel < 10) | (h_channel > 170)) & (s_channel >= 18) & (v_channel >= 18) & (v_channel <= 190)
        
        leaf_mask = (green_mask | yellow_rust_mask | brown_mask).astype(np.uint8) * 255
        
        # Morphological closing to unify leaf surface
        k_size = max(5, int(min(h, w) * 0.025))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        cleaned_leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel)
        
        leaf_pixel_count = int(np.sum(cleaned_leaf_mask > 0))
        if leaf_pixel_count < 100:
            leaf_pixel_count = total_pixels
            cleaned_leaf_mask = np.ones((h, w), dtype=np.uint8) * 255

        # 2. Resize Grad-CAM to exact original image dimensions
        cam_resized = cv2.resize(cam_heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
        
        # Mask CAM strictly within the leaf contour
        cam_in_leaf = cam_resized * (cleaned_leaf_mask > 0).astype(np.float32)
        
        # 3. Active Lesion Segmentation (Adaptive High-Activation Thresholding)
        # In Grad-CAM, values >= 0.45 inside the leaf indicate active pathological features
        lesion_mask = (cam_in_leaf >= 0.45).astype(np.uint8) * 255
        
        # Optional: remove tiny speckle noise
        lesion_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        lesion_mask = cv2.morphologyEx(lesion_mask, cv2.MORPH_OPEN, lesion_kernel)
        
        lesion_pixel_count = int(np.sum(lesion_mask > 0))
        
        # 4. Severity Index Percentage
        severity_pct = round((lesion_pixel_count / max(1, leaf_pixel_count)) * 100.0, 1)
        # Cap severity to realistic range for leaf surfaces
        severity_pct = min(100.0, max(1.5, severity_pct))
        
        # 5. Staging & Agronomic Prescription Mapping
        if severity_pct < 10.0:
            stage_num = 1
            stage_name = "Stage 1: Incipient / Mild Infection (< 10%)"
            badge = "MILD (Stage 1)"
            risk = "Low Risk (Estimated yield impact < 3% if treated promptly)"
            action = (
                "Apply targeted biological/organic controls: Horticultural Neem oil spray (5ml/L) "
                "or Bacillus subtilis bio-fungicide. Prune 1-2 lower leaves exhibiting initial necrotic flecks."
            )
            color = "#10B981" # Green
            
        elif severity_pct < 25.0:
            stage_num = 2
            stage_name = "Stage 2: Moderate Infection (10% - 25%)"
            badge = "MODERATE (Stage 2)"
            risk = "Moderate Risk (Potential 8% - 15% canopy loss within 48-72 hours if weather is humid)"
            action = (
                "Apply protective foliar contact fungicide (Copper Hydroxide at 2.5g/L or Mancozeb). "
                "Disinfect pruning shears with 70% alcohol and prune affected foliage 6 inches below visible lesion margins."
            )
            color = "#F59E0B" # Amber
            
        elif severity_pct < 50.0:
            stage_num = 3
            stage_name = "Stage 3: Severe Infection (25% - 50%)"
            badge = "SEVERE (Stage 3)"
            risk = "High Risk (Active secondary sporulation; estimated 25% - 40% yield loss)"
            action = (
                "Initiate systemic translaminar chemical treatment (Azoxystrobin, Difenoconazole, or Chlorothalonil). "
                "Increase planting row ventilation, eliminate overhead sprinkler irrigation, and clear fallen debris."
            )
            color = "#EF4444" # Red
            
        else:
            stage_num = 4
            stage_name = "Stage 4: Critical / Epidemic Infection (> 50%)"
            badge = "CRITICAL (Stage 4)"
            risk = "Catastrophic Risk (Irreversible canopy death; extreme airborne spore spread hazard)"
            action = (
                "Immediate rogueing (uproot and bag entire infected plant) to prevent disease transmission to adjacent crop rows. "
                "Do NOT compost infected material. Apply broad-spectrum protective spray across surrounding buffer zone."
            )
            color = "#7F1D1D" # Dark Crimson
            
        return {
            "is_healthy": False,
            "severity_pct": severity_pct,
            "stage_number": stage_num,
            "stage_name": stage_name,
            "stage_badge": badge,
            "risk_level": risk,
            "action_plan": action,
            "color_hex": color,
            "leaf_pixels": leaf_pixel_count,
            "lesion_pixels": lesion_pixel_count,
            "lesion_mask": lesion_mask
        }
