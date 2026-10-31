import cv2
import numpy as np
from PIL import Image

from src.lesions import lesion_map

class SeverityEngine:
    """
    Automated Quantitative Disease Severity Staging Engine:
    Segments the main leaf and its visible lesions (src/lesions.py) to estimate
    the percentage of infected leaf surface area and map it to a 4-stage scale
    (<10%, 10-25%, 25-50%, >50%).

    Note: this is a heuristic proxy. Lesions are found by colour contrast, not a
    trained segmentation model, and the stage thresholds are project-defined
    (not an official USDA/FAO standard).
    """

    @staticmethod
    def unavailable(predicted_class: str):
        """Result used when no Grad-CAM map is available to estimate severity."""
        return {
            "is_healthy": "healthy" in predicted_class.lower(),
            "available": False,
            "severity_pct": None,
            "stage_number": None,
            "stage_name": "Severity not available",
            "stage_badge": "N/A",
            "risk_level": "Undetermined",
            "action_plan": "Follow the standard treatment guidelines below.",
            "color_hex": "#64748B",
            "leaf_pixels": 0,
            "lesion_pixels": 0
        }
    
    @staticmethod
    def calculate_severity(pil_image: Image.Image, cam_heatmap: np.ndarray, predicted_class: str):
        # cam_heatmap is kept for API compatibility; severity now comes from the pixel-level lesion map
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
                "available": True,
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

        # Leaf segmentation + pixel-level lesion detection (src/lesions.py)
        leaf_mask, lesion_bool, severity_pct = lesion_map(pil_image)
        leaf_pixel_count = int(leaf_mask.sum())
        lesion_pixel_count = int(lesion_bool.sum())
        lesion_mask = lesion_bool.astype(np.uint8) * 255
        severity_pct = min(100.0, severity_pct)
        
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
            "available": True,
            "severity_pct": severity_pct,
            "stage_number": stage_num,
            "stage_name": stage_name,
            "stage_badge": badge,
            "risk_level": risk,
            "action_plan": action,
            "color_hex": color,
            "leaf_pixels": leaf_pixel_count,
            "lesion_pixels": lesion_pixel_count,
            "lesion_mask": lesion_mask,
            "leaf_mask": leaf_mask
        }
