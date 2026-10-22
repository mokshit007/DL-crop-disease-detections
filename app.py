import os
import streamlit as st
from PIL import Image
import pandas as pd

from src.predict import CropDiseasePredictor, DEFAULT_MODEL_PATH, DEFAULT_ARCH
from src.report_generator import generate_pdf_report

st.set_page_config(
    page_title="CropSense AI - Smart Plant Pathology",
    page_icon="🌿",
    layout="wide"
)

# Custom CSS for polished agritech dashboard styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0fdf4;
        border: 1px solid #86efac;
        padding: 1.2rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
    }
    .warning-card {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background-color: #16a34a;
        color: white;
        font-weight: 600;
        border-radius: 0.5rem;
        padding: 0.6rem 1.5rem;
    }
    .stButton>button:hover {
        background-color: #15803d;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_predictor():
    if not os.path.exists(DEFAULT_MODEL_PATH) or not os.path.exists('class_names.json'):
        return None
    return CropDiseasePredictor()

predictor = load_predictor()

# App Header
st.title("🌿 CropSense AI — Plant Disease Diagnostic Hub")
MODEL_NAMES = {"baseline": "EfficientNetV2-S", "cbam": "EfficientNetV2-S + CBAM", "msaf": "EfficientNetV2-MSAF"}
st.caption(f"Powered by {MODEL_NAMES[DEFAULT_ARCH]} (38 Botanical Classes) | Grad-CAM Explainable AI | Real-Time Agronomic Remedies")

if predictor is None:
    st.error(f"Model checkpoints or class mappings not found. Please verify {DEFAULT_MODEL_PATH} exists.")
    st.stop()

# Input Selection Tabs
tab_upload, tab_camera = st.tabs(["📁 Upload Leaf Image", "📸 Live Camera Capture"])
input_image = None

with tab_upload:
    uploaded_file = st.file_uploader(
        "Select a leaf photo from your device (JPG, JPEG, PNG)",
        type=["jpg", "jpeg", "png"],
        key="uploader"
    )
    if uploaded_file is not None:
        input_image = Image.open(uploaded_file)

with tab_camera:
    camera_file = st.camera_input("Snap a live photo of a plant leaf in the field", key="camera")
    if camera_file is not None:
        input_image = Image.open(camera_file)

if input_image is not None:
    st.markdown("---")
    
    # Run Prediction Button
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        run_analysis = st.button("🔍 Diagnose Plant Health", use_container_width=True)

    if run_analysis:
        with st.spinner("Validating botanical image quality and analyzing pathology..."):
            diagnosis = predictor.predict(input_image)
            
        # ==============================================================
        # 1. VALIDATION CHECK: INVALID IMAGE OR MULTIPLE LEAVES
        # ==============================================================
        if not diagnosis['is_valid_leaf']:
            st.error("## 🛑 Something is wrong with the uploaded image!")
            
            err_code = diagnosis.get('error_code')
            msg = diagnosis['validity_message']
            
            if err_code == 'multiple_leaves':
                st.warning(f"### 🌿 **Multiple Leaves / Cluttered Foliage Detected**\n\n{msg}")
                st.info(
                    "💡 **Why this happened:** The deep learning model is calibrated for **clinical single-leaf inspection**. "
                    "When multiple overlapping leaves, branches, or dense canopies are present, fungal lesions cannot be accurately isolated.\n\n"
                    "👉 **What you need to do:** Please zoom in or capture a close-up photo of **one single leaf** showing the symptoms."
                )
            else:
                st.warning(f"### 📄 **Non-Plant Image Detected**\n\n{msg}")
                st.info(
                    "💡 **Why this happened:** The uploaded image does not contain living botanical plant tissue "
                    "(it appears to be a document, screenshot, paper, text, screen, or random object).\n\n"
                    "👉 **What you need to do:** Please upload a clear photo of an actual crop or plant leaf."
                )
                
            col_img, col_guide = st.columns([1, 1], gap="large")
            with col_img:
                st.image(diagnosis['original_image'], caption="Uploaded Image (Rejected - Cannot Be Diagnosed)", use_container_width=True)
            with col_guide:
                st.markdown("""
                ### 📋 How to capture an image correctly:
                1. **Single Leaf Only:** Fill 60%–80% of the camera frame with a single leaf.
                2. **Zoom In Close:** Avoid photographing whole trees, bushes, or branches with multiple leaves.
                3. **Natural Lighting:** Ensure clear, even daylight without extreme shadows, reflections, or motion blur.
                4. **Sharp Focus:** Keep the camera steady and focused on the visible spots, lesions, or discoloration.
                """)
                
        # ==============================================================
        # 2. VALID SINGLE LEAF DETECTED: RUN FULL DIAGNOSIS
        # ==============================================================
        else:
            top_pred = diagnosis['top_predictions'][0]
            treatment = diagnosis['treatment']
            
            if top_pred['confidence'] < 75.0:
                st.warning(f"⚠️ **Moderate Confidence ({top_pred['confidence']:.1f}%):** The lesion pattern is ambiguous or obscured. Consider taking a closer photo under even natural lighting.")

            # Main Dashboard Layout
            col_visuals, col_details = st.columns([1, 1], gap="large")
            
            with col_visuals:
                st.subheader("🖼️ Visual Inspection & Explainable AI")
                
                img_tabs = st.tabs(["Original Specimen", "🔥 Grad-CAM Attention Heatmap"])
                with img_tabs[0]:
                    st.image(diagnosis['original_image'], caption="Uploaded Leaf Specimen", use_container_width=True)
                with img_tabs[1]:
                    st.image(diagnosis['gradcam_image'], caption="Grad-CAM Activation: Red & yellow zones pinpoint the exact leaf lesions and patterns the model analyzed.", use_container_width=True)
                    
            with col_details:
                st.subheader("📊 Diagnostic Verdict")
                
                # Highlight Banner
                if "healthy" in top_pred['class'].lower():
                    st.success(f"### ✅ {treatment['crop']} — Healthy")
                    st.write(f"**Confidence:** {top_pred['confidence']:.1f}%")
                else:
                    st.error(f"### 🚨 {treatment['crop']} — {treatment['disease']}")
                    st.write(f"**Confidence:** {top_pred['confidence']:.1f}%  |  **Pathogen:** {treatment['pathogen']}")
                    
                st.markdown("#### Top Probabilities")
                df = pd.DataFrame(diagnosis['top_predictions'])
                df_chart = df.set_index('clean_name')[['confidence']]
                st.bar_chart(df_chart, height=220)

            # Actionable Treatment & Agronomic Solutions
            st.markdown("---")
            
            # Quantitative Disease Severity Staging Section
            st.subheader("📏 Estimated Disease Severity (Infected Leaf Area)")
            sev = diagnosis.get('severity')
            if sev and not sev.get('available', True):
                st.info("Severity could not be estimated for this image (no attention map available). Follow the treatment plan below.")
            elif sev and not sev.get('is_healthy', False):
                col_s1, col_s2, col_s3 = st.columns([1, 1, 2])
                with col_s1:
                    st.metric(label="Infected Surface Area", value=f"{sev['severity_pct']}%")
                with col_s2:
                    st.metric(label="Estimated Severity Stage", value=f"Stage {sev['stage_number']}")
                with col_s3:
                    st.write(f"**Classification:** {sev['stage_name']}")
                    st.write(f"**Epidemiological Risk:** {sev['risk_level']}")
                
                st.progress(min(1.0, max(0.0, sev['severity_pct'] / 100.0)), text=f"Lesion Surface Coverage: {sev['severity_pct']}% of leaf tissue")
                st.warning(f"**🔬 Staging Action Plan:** {sev['action_plan']}")
                st.caption("Severity is an estimate from Grad-CAM attention inside the segmented leaf, not a lab measurement. Confirm with a local agronomist before chemical treatment.")
            else:
                st.success("### 🌿 0% Necrotic Lesion Area (Stage 0: Pristine Foliage)\nNo active pathological lesions or chlorotic spread detected.")

            st.markdown("---")
            st.subheader("💊 Actionable Treatment & Crop Management Plan")
            
            t_col1, t_col2 = st.columns(2, gap="medium")
            
            with t_col1:
                with st.expander("🔍 Observed Symptoms & Pathogen Details", expanded=True):
                    st.write(f"**Pathogen:** {treatment['pathogen']}")
                    st.write(f"**Typical Symptoms:** {treatment['symptoms']}")
                    
                with st.expander("🌿 Organic & Biological Remedies", expanded=True):
                    st.write(treatment['organic'])
                    
            with t_col2:
                with st.expander("🧪 Recommended Chemical Controls", expanded=True):
                    st.write(treatment['chemical'])
                    
                with st.expander("🛡️ Long-Term Cultural Prevention", expanded=True):
                    st.write(treatment['prevention'])

            # Exportable PDF Health Report
            st.markdown("---")
            st.subheader("📄 Download Official Diagnostic Report")
            
            with st.spinner("Compiling high-resolution PDF diagnostic report..."):
                pdf_bytes = generate_pdf_report(
                    diagnosis['original_image'],
                    diagnosis['gradcam_image'],
                    diagnosis,
                    model_name=MODEL_NAMES[DEFAULT_ARCH]
                )
                
            file_name = f"CropSense_Report_{treatment['crop']}_{treatment['disease'].replace(' ', '_')}.pdf"
            st.download_button(
                label="📥 Download Diagnostic PDF Report",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=False
            )

else:
    # Empty State Guidance
    st.info("👆 Upload a clear leaf photo or take a picture using your camera above to begin instant diagnosis.")
    
    with st.expander("ℹ️ Supported Crops & Diseases (Click to view full coverage)"):
        st.markdown("""
        **Covered Crops (14 species):** Apple, Blueberry, Cherry, Corn (Maize), Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, Tomato.  
        **Detection Capabilities:** 38 health and disease categories including Early/Late Blights, Powdery Mildews, Rusts, Bacterial Spots, Black Rots, Citrus Greening, Spider Mites, and Viral infections.
        """)
