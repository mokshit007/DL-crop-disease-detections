import os
import tempfile
from datetime import datetime
from fpdf import FPDF
from PIL import Image

class PlantHealthPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(34, 139, 34) # Forest Green
        self.cell(0, 10, 'AI Plant Disease Diagnostic Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Model: EfficientNetV2-S', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, 'Automated Agronomic Assessment - Powered by SOTA Deep Learning', 0, 0, 'C')

def generate_pdf_report(original_img: Image.Image, gradcam_img: Image.Image, diagnosis_data: dict) -> bytes:
    """
    Generates a PDF diagnostic report with side-by-side images and treatment recommendations.
    Returns bytes of the generated PDF file.
    """
    pdf = PlantHealthPDF()
    pdf.add_page()
    
    # Save temporary images for FPDF embedding
    temp_dir = tempfile.mkdtemp()
    orig_path = os.path.join(temp_dir, "orig.jpg")
    cam_path = os.path.join(temp_dir, "cam.jpg")
    
    original_img.convert('RGB').resize((300, 300)).save(orig_path, "JPEG", quality=90)
    gradcam_img.convert('RGB').resize((300, 300)).save(cam_path, "JPEG", quality=90)
    
    # Section: Key Diagnosis
    top_pred = diagnosis_data['top_predictions'][0]
    treatment = diagnosis_data['treatment']
    
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 8, f"Target Crop: {treatment['crop']}", 0, 1)
    
    # Diagnosis box
    pdf.set_fill_color(240, 248, 240)
    pdf.set_draw_color(34, 139, 34)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 9, f" Diagnosis: {treatment['disease']}  (Confidence: {top_pred['confidence']:.1f}%)", 1, 1, fill=True)
    pdf.ln(2)
    
    # Quantitative Severity Staging Box
    if 'severity' in diagnosis_data and not diagnosis_data['severity'].get('is_healthy', False):
        sev = diagnosis_data['severity']
        pdf.set_fill_color(254, 243, 199)
        pdf.set_draw_color(217, 119, 6)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(180, 83, 9)
        pdf.cell(0, 7, f" Infection Staging: {sev['stage_name']} | Infected Leaf Area: {sev['severity_pct']}%", 1, 1, fill=True)
        pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 6, f"Pathogen Classification: {treatment['pathogen']}", 0, 1)
    pdf.ln(2)
    
    # Visual Inspection Images Side-by-Side
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(34, 139, 34)
    pdf.cell(95, 6, "Original Leaf Specimen", 0, 0, 'C')
    pdf.cell(95, 6, "AI Grad-CAM Attention Heatmap", 0, 1, 'C')
    
    y_pos = pdf.get_y()
    pdf.image(orig_path, x=25, y=y_pos, w=65, h=65)
    pdf.image(cam_path, x=120, y=y_pos, w=65, h=65)
    pdf.set_y(y_pos + 68)
    
    # Section: Actionable Treatment Plan
    def add_section(title, text, color=(0, 102, 0)):
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(*color)
        pdf.cell(0, 6, title, 0, 1)
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(30, 30, 30)
        # Safe ASCII cleanup
        safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
        pdf.multi_cell(0, 5, safe_text)
        pdf.ln(2)
        
    add_section("Observed Symptoms:", treatment['symptoms'])
    add_section("Organic & Biological Remedies:", treatment['organic'], color=(46, 139, 87))
    add_section("Recommended Chemical Treatments:", treatment['chemical'], color=(178, 34, 34))
    add_section("Prevention & Cultural Management:", treatment['prevention'], color=(70, 130, 180))
    
    # Output to byte string
    pdf_output_path = os.path.join(temp_dir, "report.pdf")
    pdf.output(pdf_output_path)
    
    with open(pdf_output_path, 'rb') as f:
        pdf_bytes = f.read()
        
    # Cleanup temp files
    try:
        os.remove(orig_path)
        os.remove(cam_path)
        os.remove(pdf_output_path)
        os.rmdir(temp_dir)
    except Exception:
        pass
        
    return pdf_bytes
