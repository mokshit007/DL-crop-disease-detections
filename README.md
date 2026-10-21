# CropSense AI — State-of-the-Art Plant Disease Diagnosis

A production-grade Deep Learning system for automated crop leaf disease detection, explainable AI diagnostics (Grad-CAM), and actionable agronomic remedies.

---

## 🌟 Key Features

1. **State-of-the-Art Architecture:** Powered by **EfficientNetV2-S**, achieving **99.94% Validation Accuracy** using Fused-MBConv layers, Automatic Mixed Precision (AMP), OneCycleLR scheduling, and Label Smoothing.
2. **Comprehensive Coverage:** Supports **14 distinct crop species** and **38 individual plant health and disease categories** trained on over 87,000 real-world agricultural specimens.
3. **Explainable AI (Grad-CAM):** Overlays visual attention heatmaps directly on the leaf, showing farmers and researchers the exact lesions and fungal patterns the model used to make its verdict.
4. **Actionable Treatment Plans:** Instant breakdown of pathogen identification, primary symptoms, organic/biological controls, registered chemical sprays, and long-term cultural prevention techniques.
5. **Smart Leaf Gatekeeper (OOD Filter):** Automatically detects non-botanical uploads (documents, screenshots, blank screens) and warns the user instead of making silent speculative predictions.
6. **Live Camera Input:** Field-ready input supporting live camera snapshots directly from phones, tablets, or webcams alongside standard file uploads.
7. **Exportable PDF Health Reports:** One-click generation of official, print-ready diagnostic reports containing original photos, Grad-CAM heatmaps, and treatment regimens.

---

## 🌾 Supported Crops & Conditions (38 Classes)

- **Apple:** Scab, Black Rot, Cedar Apple Rust, Healthy
- **Blueberry:** Healthy
- **Cherry:** Powdery Mildew, Healthy
- **Corn (Maize):** Gray Leaf Spot, Common Rust, Northern Leaf Blight, Healthy
- **Grape:** Black Rot, Esca (Black Measles), Leaf Blight, Healthy
- **Orange:** Huanglongbing (Citrus Greening)
- **Peach:** Bacterial Spot, Healthy
- **Bell Pepper:** Bacterial Spot, Healthy
- **Potato:** Early Blight, Late Blight, Healthy
- **Raspberry:** Healthy
- **Soybean:** Healthy
- **Squash:** Powdery Mildew
- **Strawberry:** Leaf Scorch, Healthy
- **Tomato:** Bacterial Spot, Early Blight, Late Blight, Leaf Mold, Septoria Spot, Spider Mites, Target Spot, Yellow Leaf Curl Virus, Mosaic Virus, Healthy

---

## 🚀 How to Run the Application

1. Open your terminal (PowerShell or Command Prompt).
2. Navigate to the project root:
   ```bash
   cd crop-disease-detection
   ```
3. Launch the web interface:
   ```bash
   streamlit run app.py
   ```
4. Open your browser at **http://localhost:8501**.

---

## 📁 Project Architecture

```
crop-disease-detection/
├── app.py                     # Streamlit application with Grad-CAM, treatments & camera
├── models/
│   └── best_model.pth         # Trained EfficientNetV2-S weights (99.94% accuracy)
├── class_names.json           # 38-class index mappings
├── src/
│   ├── model.py               # EfficientNetV2-S definition
│   ├── predict.py             # Inference pipeline & leaf validation
│   ├── gradcam.py             # Grad-CAM explainable AI implementation
│   ├── treatments.py          # Agronomic knowledge base (organic & chemical remedies)
│   ├── report_generator.py    # Downloadable PDF report compiler
│   ├── dataset.py             # Automated KaggleHub dataset fetcher & preprocessor
│   ├── train.py               # SOTA training pipeline (AMP + OneCycleLR + Smoothing)
│   └── evaluate.py            # Model evaluation & metrics
├── requirements.txt           # Python environment dependencies
└── README.md
```
