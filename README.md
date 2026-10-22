# CropSense AI — Plant Disease Diagnosis with Multi-Scale Attention

A deep learning system for crop leaf disease detection with explainable AI (Grad-CAM), a severity estimate, and treatment recommendations, plus a proposed architecture, **EfficientNetV2-MSAF**, evaluated against the stock model on a leakage-free split.

---

## 🌟 Key Features

1. **Two models, honestly compared:** the deployed **EfficientNetV2-S** and the proposed **EfficientNetV2-MSAF** (Multi-Scale Attention Fusion), trained with an identical recipe and tested on the same leaf-disjoint split (see [Results](#-results)).
2. **Comprehensive Coverage:** **14 crop species** and **38 health and disease classes** (~87,900 images).
3. **Explainable AI (Grad-CAM):** heatmaps over the leaf showing the regions behind each prediction.
4. **Actionable Treatment Plans:** pathogen, symptoms, organic and chemical controls, and cultural prevention for every class.
5. **Leaf Gatekeeper:** rejects non-plant images (documents, screenshots) and multi-leaf / cluttered photos before inference.
6. **Severity Estimate:** share of the segmented leaf flagged by Grad-CAM, mapped to 4 stages. This is a heuristic estimate, not a lab measurement or an official standard.
7. **Live Camera Input** and **PDF diagnostic reports** in the Streamlit app.

---

## 🧠 Proposed Architecture: EfficientNetV2-MSAF

Drawbacks of the stock EfficientNetV2-S head, and what MSAF changes (`src/model.py`):

| Drawback | MSAF change |
|---|---|
| Decides from the final 7×7 map only (1 cell = 32×32 px), so small lesions are averaged away | Taps three scales: stage 3 (64 ch, 28×28), stage 5 (160 ch, 14×14), head (1280 ch, 7×7) |
| No explicit lesion focus | A CBAM channel + spatial attention block on every scale |
| Global average pooling dilutes small, strong activations | Learnable GeM pooling per scale, then LayerNorm |
| Fine features break first under blur / noise | Concatenated multi-scale descriptor + scale-dropout during training |

Cost: **+220,841 parameters (+1.09%)**, 20.45M total.

---

## 📊 Results

**Leaf-disjoint split.** The Kaggle dataset ships rotated / flipped copies of each photo. A random file split placed copies of the same leaf in train and test: **67.5%** of the original test images had a sibling in train/val. `src/splits.py` groups every copy of a leaf into one split (train 70,146 / val 8,832 / test 8,889 images).

All three models: 8 epochs, batch 32, AdamW + OneCycleLR, label smoothing 0.1, AMP, same augmentation, same split, one seed. Corruptions were **not** used in training.

| Model | Params | Clean acc | Mean corrupted acc (6 conditions) | Motion blur | Sensor noise | Low light | ECE ↓ | Field photos (8) |
|---|---|---|---|---|---|---|---|---|
| EfficientNetV2-S (baseline) | 20.23M | **99.62%** | 82.20% | 54.45% | 80.66% | 90.03% | 10.57% | 6 / 8 |
| EfficientNetV2-S + CBAM | 20.43M | 99.51% | **83.08%** | **62.95%** | 78.21% | 89.97% | 10.17% | 8 / 8 |
| **EfficientNetV2-MSAF** | 20.45M | 99.51% | 83.00% | 50.13% | **85.44%** | **94.35%** | **5.14%** | 8 / 8 |

What this shows:
- **Calibration:** MSAF halves the expected calibration error (10.57% → 5.14%), so its confidence values are much more trustworthy.
- **Robustness is mixed:** +4.8 pts under sensor noise and +4.3 pts in low light, but −4.3 pts under motion blur; the 6-condition mean improves by only +0.8 pts, within single-seed noise.
- **Clean accuracy** is saturated (~99.5–99.6%) for every model, so it cannot separate architectures.
- **Explainability trade-off:** standard Grad-CAM gives noisy maps on MSAF (its per-scale LayerNorm cancels the averaged gradient weights). The app therefore keeps **EfficientNetV2-S** (`models/best_model.pth`) so heatmaps and severity estimates stay reliable.

### Field-augmented training

`--field-aug` adds Gaussian blur (σ 0.5–3) and sensor noise (std ≤ 0.12), each to 30% of training images. Motion blur, JPEG, low light and overexposure are **never** seen in training, so they measure generalisation.

| Model | Clean acc | Mean corrupted acc | Seen (2) | Unseen (4) | Motion blur | ECE ↓ | Field photos (8) |
|---|---|---|---|---|---|---|---|
| EfficientNetV2-S | 99.62% | 82.20% | 81.61% | 82.50% | 54.45% | 10.57% | 6 / 8 |
| EfficientNetV2-S + field aug. | 99.58% | **95.67%** | 99.27% | **93.88%** | **86.31%** | 10.56% | 6 / 8 |
| EfficientNetV2-MSAF | 99.51% | 83.00% | 83.54% | 82.72% | 50.13% | **5.14%** | 8 / 8 |
| **EfficientNetV2-MSAF + field aug.** | 99.56% | 94.83% | 99.27% | 92.62% | 81.85% | 5.45% | 8 / 8 |

- **Augmentation drives robustness:** mean corrupted accuracy rises by 12–13 pts, and motion blur (never trained on) jumps from ~50–54% to 82–86%.
- **MSAF drives calibration and field-photo accuracy:** ECE stays about half the baseline's, with or without augmentation, and all 8 field photos are correct.
- **Under the same augmentation MSAF is slightly behind on robustness** (−0.8 pts mean, −4.5 pts motion blur).
- **Proposed system (MSAF + field aug.) vs. the original model:** mean corrupted accuracy 82.2% → 94.8%, ECE 10.6% → 5.5%, field photos 6/8 → 8/8, clean accuracy 99.56%.

Full numbers: `results/ablation_results.json`; charts: `results/ablation_robustness.png`, `results/field_aug_robustness.png`.

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

## 🚀 How to Run

From the `crop-disease-detection` folder:

```bash
streamlit run app.py
```

Then open **http://localhost:8501**. To serve a different checkpoint, change `DEFAULT_MODEL_PATH` / `DEFAULT_ARCH` in `src/predict.py`.

### Reproduce the comparison

```bash
python -m src.dataset
```

```bash
powershell -ExecutionPolicy Bypass -File .\run_ablation.ps1
```

```bash
python generate_pitch_deck.py
```

`run_ablation.ps1` trains `baseline`, `msaf`, `cbam`, `baseline_field` and `msaf_field` (about 40–55 min each on a 4 GB RTX 3050) and then runs `src/compare.py`. It is safe to re-run after an interruption: finished models are skipped and an unfinished one resumes from its last epoch. Watch progress with `python scripts\watch_training.py`. The deck generator reads every number from `results/`.

Train a single model:

```bash
python -m src.train --arch msaf --epochs 8 --field-aug
```

---

## 📁 Project Structure

```
crop-disease-detection/
├── app.py                     # Streamlit app: upload/camera, gatekeeper, Grad-CAM, severity, treatments, PDF
├── generate_pitch_deck.py     # Builds CropSense_AI_Official_Presentation.pptx from results/
├── run_ablation.ps1           # Trains baseline / MSAF / CBAM, then runs the comparison
├── models/
│   ├── best_model.pth         # Deployed EfficientNetV2-S (original file split)
│   ├── baseline.pth           # EfficientNetV2-S, leaf-disjoint split
│   ├── cbam.pth               # EfficientNetV2-S + CBAM, leaf-disjoint split
│   ├── msaf.pth               # EfficientNetV2-MSAF, leaf-disjoint split
│   ├── baseline_field.pth     # EfficientNetV2-S + field augmentation
│   └── msaf_field.pth         # EfficientNetV2-MSAF + field augmentation
├── class_names.json           # 38-class index mapping
├── src/
│   ├── model.py               # Baseline, CBAM and MSAF architectures
│   ├── attention.py           # CBAM (channel + spatial attention) and GeM pooling
│   ├── splits.py              # Leaf-disjoint split + one-copy-per-leaf sampler
│   ├── train.py               # Training (AMP, OneCycleLR, label smoothing, per-epoch resume)
│   ├── compare.py             # Clean / corruption / calibration / field-photo comparison
│   ├── evaluate.py            # Test-set report + leakage audit of the original split
│   ├── predict.py             # Inference pipeline and leaf gatekeeper
│   ├── gradcam.py             # Grad-CAM
│   ├── severity.py            # Severity estimate from Grad-CAM + leaf segmentation
│   ├── treatments.py          # Agronomic knowledge base
│   ├── report_generator.py    # PDF report
│   ├── dataset.py             # KaggleHub download + leaf-grouped split
│   └── benchmark_suite.py     # Parameter / latency profiling
├── scripts/
│   ├── render_equations.py    # LaTeX equation images for the deck
│   └── watch_training.py      # Live view of the training log
├── results/                   # Metrics, charts, equation images
├── requirements.txt
└── README.md
```

---

## ⚠️ Limitations

- Training images are lab-style PlantVillage photos on plain backgrounds; field accuracy is checked on only 8 real photos plus simulated corruptions.
- Closed-world: any leaf is mapped to one of the 38 classes.
- One training run per model; differences under ~1 pt are within noise.
- Motion blur is still the hardest condition (82–86% with field augmentation).
- The severity estimate is a Grad-CAM heuristic with project-defined thresholds. Confirm with an agronomist before chemical treatment.
