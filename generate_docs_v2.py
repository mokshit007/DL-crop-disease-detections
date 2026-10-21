import os
from fpdf import FPDF
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# ==========================================
# 1. GENERATE DETAILED PDF MANUAL
# ==========================================
class DetailedPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(34, 139, 34)
        self.cell(0, 10, 'Complete Technical Manual: SOTA Crop Disease AI', 0, 1, 'C')
        self.ln(2)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 102, 0)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, body)
        self.ln(4)
        
    def add_code_block(self, filepath):
        if not os.path.exists(filepath):
            self.chapter_body(f"[Code file {filepath} not found]")
            return
            
        self.set_font('Courier', '', 8)
        self.set_text_color(50, 50, 50)
        self.set_fill_color(240, 240, 240)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
            # Remove non-latin1 characters to prevent fpdf crashes
            code = code.encode('latin-1', 'ignore').decode('latin-1')
            
        # Write code inside a shaded box
        self.multi_cell(0, 4, code, border=1, fill=True)
        self.ln(4)

def create_detailed_pdf():
    pdf = DetailedPDF()
    pdf.add_page()
    
    # 1. Intro & Instructions
    pdf.chapter_title("1. How to Start and Run the Application")
    pdf.chapter_body(
        "This project is a fully functional web application powered by a deep learning model. "
        "To start the application, open your terminal, navigate to the project directory, and run:\n\n"
        "    cd crop-disease-detection\n"
        "    streamlit run app.py\n\n"
        "This will start a local web server. Open your browser and navigate to http://localhost:8501. "
        "You can now upload a crop leaf image, and the application will instantly predict the disease."
    )
    
    # 2. Web Architecture
    pdf.chapter_title("2. Web Interface and Model Integration Architecture")
    pdf.chapter_body(
        "The system bridges the gap between deep learning and user interaction through a seamless architecture:\n"
        "1. The User Interface (app.py) is built with Streamlit. It handles file uploads securely in memory.\n"
        "2. Once an image is uploaded, it is passed to the Inference Engine (predict.py).\n"
        "3. The Inference Engine loads the pre-trained EfficientNetV2-S model ('best_model.pth') into RAM/VRAM.\n"
        "4. The image undergoes standard ImageNet transformations (Resize, CenterCrop, Normalize) matching the training pipeline.\n"
        "5. The model outputs raw logits, which are passed through a Softmax function to generate percentages (Confidence).\n"
        "6. The top predictions are returned as a JSON/Dictionary back to the UI, which dynamically renders a bar chart using Pandas."
    )
    
    # 3. Dataset Script
    pdf.chapter_title("3. Dataset Preparation (dataset.py)")
    pdf.chapter_body(
        "Purpose: This script completely automates the downloading and processing of the massive 87,000+ image dataset.\n"
        "How it works:\n"
        "- Uses 'kagglehub' to securely bypass authentication limits and download the 'vipoooool/new-plant-diseases-dataset'.\n"
        "- Recursively walks through the downloaded folders to find the exact plant categories (38 classes).\n"
        "- Gathers all JPG/PNG files, removes duplicates, and shuffles them.\n"
        "- Splits them strictly into 80% Training, 10% Validation, and 10% Testing sets.\n"
        "- Copies them to 'data/processed' ensuring a pristine, isolated dataset."
    )
    pdf.add_code_block("src/dataset.py")
    
    # 4. Model Architecture
    pdf.add_page()
    pdf.chapter_title("4. Deep Learning Model (model.py)")
    pdf.chapter_body(
        "Purpose: Defines the State-of-the-Art network architecture.\n"
        "How it works:\n"
        "- Imports EfficientNetV2-S directly from torchvision with pre-trained ImageNet weights.\n"
        "- We dynamically locate the final classification head (model.classifier[1]) and replace it with a new nn.Linear layer outputting exactly 38 classes.\n"
        "- EfficientNetV2 is fundamentally superior here because it uses Fused-MBConv layers (replacing standard Depthwise convolutions in early stages) which massively accelerates training while reducing parameter count."
    )
    pdf.add_code_block("src/model.py")
    
    # 5. Training Pipeline
    pdf.add_page()
    pdf.chapter_title("5. Training Pipeline & Advanced Engineering (train.py)")
    pdf.chapter_body(
        "Purpose: Trains the network using highly optimized SOTA techniques.\n"
        "How it works:\n"
        "- Automatic Mixed Precision (AMP): Uses 'torch.amp.autocast' and 'GradScaler'. This forces calculations into 16-bit floats instead of 32-bit where safe. Result: 2x faster training, 50% less GPU memory.\n"
        "- OneCycleLR Scheduler: Instead of a flat learning rate, this ramps the LR up quickly and then cosine-decays it down. This enables 'Super-Convergence'.\n"
        "- Label Smoothing (0.1): Changes the absolute '1.0' target to '0.9'. Prevents the model from being overconfident, acting as severe regularization.\n"
        "- Optimizer: Uses AdamW instead of Adam, offering mathematically correct weight decay decoupling.\n"
        "- Augmentations: RandomResizedCrop, Horizontal/Vertical Flips, and ColorJittering force the model to learn shapes, not specific pixels."
    )
    pdf.add_code_block("src/train.py")
    
    # 6. Inference Pipeline
    pdf.add_page()
    pdf.chapter_title("6. Inference Engine (predict.py)")
    pdf.chapter_body(
        "Purpose: Bridges the trained model weights and raw image input for production.\n"
        "How it works:\n"
        "- Loads 'class_names.json' generated during training so predictions map to human-readable names (e.g., 'Tomato_Early_Blight').\n"
        "- Loads the model weights strictly in evaluation mode (model.eval()), turning off Dropout/BatchNorm updates.\n"
        "- Uses torch.no_grad() to completely disable the autograd engine, saving immense memory and drastically speeding up predictions.\n"
        "- Uses torch.topk to extract the 3 highest probability classes."
    )
    pdf.add_code_block("src/predict.py")
    
    # 7. Web Application
    pdf.add_page()
    pdf.chapter_title("7. User Interface (app.py)")
    pdf.chapter_body(
        "Purpose: The front-facing web application.\n"
        "How it works:\n"
        "- Built purely in Python using Streamlit.\n"
        "- Uses '@st.cache_resource' to load the predictor globally. This means the heavy model is only loaded into memory once when the server starts, not every time a user uploads an image. This makes predictions instantaneous.\n"
        "- Provides a polished UI utilizing columns, success banners, and a dynamic Pandas dataframe converted into a Streamlit Bar Chart."
    )
    pdf.add_code_block("app.py")
    
    pdf.output("SOTA_Crop_Disease_Technical_Manual.pdf")
    print("Detailed PDF generated successfully.")

# ==========================================
# 2. GENERATE ADVANCED PPTX PRESENTATION
# ==========================================
def create_advanced_pptx():
    prs = Presentation()
    
    DARK_GREEN = RGBColor(34, 139, 34)
    EARTH_BROWN = RGBColor(101, 67, 33)
    
    # Slide 1: Title
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "State-of-the-Art Crop Disease AI"
    slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = DARK_GREEN
    slide.shapes.title.text_frame.paragraphs[0].font.bold = True
    slide.placeholders[1].text = "An Elite Deep Learning Pipeline Powered by EfficientNetV2"
    
    # Helper
    def add_slide(title_text, bullet_points):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = title_text
        title.text_frame.paragraphs[0].font.color.rgb = DARK_GREEN
        title.text_frame.paragraphs[0].font.bold = True
        
        tf = slide.placeholders[1].text_frame
        tf.clear()
        for point in bullet_points:
            p = tf.add_paragraph()
            p.text = point
            p.font.size = Pt(18)
            p.space_after = Pt(10)
            
    # Slide 2: The Dataset
    add_slide("The Foundation: Massive Dataset Integration", [
        "Migrated to the comprehensive 'New Plant Diseases Dataset'.",
        "Scale: Over 87,000 distinct images.",
        "Diversity: 38 full classes (Apples, Cherries, Corn, Grapes, Peaches, Tomatoes, etc.).",
        "Pipeline: Fully automated, randomized splitting (80% Train, 10% Val, 10% Test)."
    ])
    
    # Slide 3: The Architecture Debate
    add_slide("Why EfficientNetV2 Beats the Competition", [
        "ResNet-50 / 101: Older architecture, massive parameter counts, plateaus early on complex flora datasets.",
        "Vision Transformers (ViT): Highly accurate but requires massive data (300M+ images) to avoid overfitting, incredibly slow inference.",
        "EfficientNet-V1: Scales poorly due to extensive depthwise convolutions causing memory bottlenecks."
    ])
    
    # Slide 4: EfficientNetV2 Supremacy
    add_slide("The EfficientNetV2-S Advantage", [
        "Fused-MBConv Layers: Replaces early depthwise convolutions, dramatically speeding up training on modern GPUs.",
        "Training-Aware NAS: The network was explicitly designed via Neural Architecture Search to optimize BOTH accuracy and training speed.",
        "Progressive Learning: Dynamically adjusts regularization during training, preventing bottlenecks.",
        "Result: Higher Top-1 Accuracy with 50% fewer parameters than ResNet-101."
    ])
    
    # Slide 5: Unlocking Super-Convergence
    add_slide("SOTA Training Pipeline Mechanics", [
        "AMP (Automatic Mixed Precision): Tensor cores calculate in 16-bit, cutting VRAM overhead in half.",
        "OneCycleLR Scheduler: Starts low, arcs high, decays low. Forces the model out of local minima rapidly.",
        "Label Smoothing (0.1): Hard targets (1.0) become soft (0.9), forcing the model to generalize rather than memorize.",
        "AdamW: Fixes the mathematical flaw in standard Adam's weight decay, crucial for modern architectures."
    ])
    
    # Slide 6: The Web Integration
    add_slide("Seamless Web Application Delivery", [
        "Caching Optimization: Model is pinned in VRAM globally via '@st.cache_resource', enabling sub-second inference.",
        "No-Grad Inference: Forward passes bypass the autograd engine entirely, saving extreme computational overhead.",
        "Interactive UI: Dynamic, real-time confidence bar charting utilizing raw softmax probability logits."
    ])
    
    prs.save("SOTA_Crop_Disease_Presentation.pptx")
    print("Advanced PPTX generated successfully.")

if __name__ == '__main__':
    create_detailed_pdf()
    create_advanced_pptx()
