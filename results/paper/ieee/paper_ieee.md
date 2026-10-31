# IEEE Research Paper — Draft

Oct 30, 2026 · @Divyesh

## Phase 1: Project understanding and gaps

The project is CropSense AI: 38-class crop leaf disease diagnosis with a proposed EfficientNetV2-MSAF head. Real experimental results exist (Path A), so no numbers need to be invented. A complete 6-page IEEE draft already exists in the folder; this paper rebuilds it from scratch to this prompt's structure.

### What the project folder supports

| Item | Evidence in folder | Value |
| --- | --- | --- |
| Working title | Research\_Paper\_CropSense\_IEEE\_Final.pdf | EfficientNetV2-MSAF: Multi-Scale Attention Fusion for Leakage-Free, Calibrated and Field-Robust Crop Leaf Disease Diagnosis |
| Dataset | README, data/splits/leaf\_disjoint.json | PlantVillage (augmented Kaggle copy), 14 crops, 38 classes, 87,867 images; leaf-disjoint split 70,146 / 8,832 / 8,889 |
| Leakage finding | results/test\_metrics.json | 67.5% of the original random-split test images had a copy of the same leaf in train/val |
| Proposed model | src/model.py, src/attention.py | CBAM on 3 backbone scales + GeM pooling + LayerNorm + scale-dropout; +220,841 params (20.45M total) |
| Models compared | models/\*.pth | Baseline, CBAM, MSAF, Baseline + field aug., MSAF + field aug. (8 epochs, AdamW + OneCycleLR, label smoothing 0.1, AMP, 1 seed) |
| Clean accuracy | results/ablation\_results.json | 99.51 to 99.62% for all models, no significant difference |
| Calibration (ECE) | results/ablation\_results.json | Baseline 10.57%, MSAF 5.14% |
| Robustness (mean of 6 corruptions) | results/ablation\_results.json | Baseline 82.20%, MSAF + field aug. 94.83% |
| Extra analyses | results/paper/metrics.json, efficiency.json | Bootstrap CIs, McNemar tests, temperature scaling, risk-coverage (AURC), MACs, GPU/CPU latency |
| System features | app.py, src/predict.py | Leaf gatekeeper (5 of 6 non-leaf images rejected), Grad-CAM, severity heuristic, treatment advice, PDF report |
| Hardware | README | RTX 3050, 4 GB |
| Figures | scripts/paper\_figures.py, results/ | Methodology and architecture diagrams, corruption chart, reliability diagram, risk-coverage curves, Grad-CAM panel |

### Gaps against the master prompt

- **Literature structure:** the existing draft has 35 references and an 11-paper table. The prompt wants 15 to 17 original 2022 to 2026 papers, top 5 discussed in Methodology, 5 analytical paragraphs, the rest in a table. The draft also cites two review papers (\[5\], \[6\]), which the prompt excludes from the survey set.
- **Author block:** names, university, emails and guide are still placeholders.
- **Field evaluation:** only 8 field photographs. No cross-dataset test (for example PlantDoc) has been run.
- **Statistical strength:** every model was trained with one seed, so small robustness differences (under 1 point) are within noise.
- **Explainability:** Grad-CAM maps are noisy on MSAF; the app deploys the baseline for this reason. This must be stated as a limitation.
- **Unrelated file:** 24BCE7021.docx is a Computer Networks lab report and is not used.

### Decisions taken

- Rebuilt from scratch (author's choice).
- Author block left as placeholders until details are supplied.
- PlantDoc test and extra seeds listed as limitations, not run, given the 31 October 2026 deadline.
- Output is this doc; an IEEE two-column .docx/.pdf can follow.

## Paper title and abstract

**EfficientNetV2-MSAF: Multi-Scale Attention Fusion for Leakage-Free, Calibrated and Field-Robust Crop Leaf Disease Diagnosis**

&#91;Author 1\], \[Author 2\], \[Author 3\]; \[Department\], \[University\], \[City\], India; \[emails\]. Guide: \[Name, Designation\].

**Abstract.** Convolutional networks exceed 99% accuracy on the PlantVillage leaf disease benchmark, yet fail on photographs taken outside the laboratory. Three practices contribute: augmented copies of a leaf leak across the train–test split, single-scale classifier heads average away small lesions, and models are judged by clean accuracy alone. A leaf-grouped split of 87,867 images (14 crops, 38 classes) removes the leakage of a random split, in which 67.5% of test images had a copy in training or validation. On this split, EfficientNetV2-MSAF, a head that applies convolutional block attention, generalised-mean pooling and scale-dropout at three backbone depths (+1.09% parameters), is compared with EfficientNetV2-S and a single-scale attention variant, each with and without field augmentation, using macro-F1, six corruptions, calibration error, selective prediction and McNemar tests. All models reach 99.51–99.62% clean accuracy with no significant difference. MSAF halves the raw expected calibration error (10.57% to 5.14%) and lowers selective risk by 20%, while field augmentation supplies most corruption robustness. The combined system raises mean corrupted accuracy from 82.20% to 94.84% and is deployed with a leaf gatekeeper, Grad-CAM explanations and treatment guidance.

**Index Terms:** plant disease classification, EfficientNetV2, attention, multi-scale feature fusion, data leakage, calibration, corruption robustness, explainable AI.

## I. Introduction

### A. Background and Research Context

Plant pathogens and pests remove an estimated 17–30% of the global harvest of major staple crops \[1\]. Plant pathologists are scarce in rural areas, so a first diagnosis from a smartphone photograph is a low-cost alternative. The open PlantVillage collection \[2\] made such systems practical, and CNNs trained on it exceeded 99% accuracy in 2016 \[3\].

### B. Research Problem and Its Significance

Laboratory accuracy on PlantVillage has saturated between 99% and 100%, while accuracy on other photographs remains far lower: 31.4% on images from other sources in \[3\], and 68% for a 2025 vision transformer transferred to the in-the-wild PlantDoc images \[4\], \[5\]. A tool that is confident and wrong in the field can lead to the wrong treatment.

### C. Limitations of Conventional Approaches

Three weaknesses recur. The augmented PlantVillage release stores rotated and flipped copies of each leaf as separate files, so a random file split places copies of one leaf in both training and test sets. Most classifiers decide from the coarsest feature map, where a small lesion is averaged away by global pooling. Models are compared by clean accuracy alone, although robustness and the reliability of confidence decide whether a prediction can be trusted \[6\].

### D. Motivation and Objectives

This work treats the evaluation protocol and the classifier head as one problem. Its objectives are to (i) remove augmented-copy leakage, (ii) design a lightweight head that preserves small-lesion evidence on an EfficientNetV2 backbone \[7\], (iii) evaluate robustness, calibration and selective risk alongside accuracy, and (iv) deploy the result in a usable application.

### E. Research Challenges

Because clean accuracy is saturated, gains must be shown on other measures without overstating small differences; training must fit a 4 GB GPU, and labelled field photographs are scarce.

### F. Contributions

1. A leaf-disjoint split of the 38-class augmented PlantVillage release, showing that 67.5% of a random split's test images had a training or validation sibling.
2. EfficientNetV2-MSAF, a head applying CBAM \[8\], generalised-mean pooling and scale-dropout at three backbone depths for +1.09% parameters.
3. A five-model comparison covering macro-F1, six corruptions, calibration before and after temperature scaling \[9\], \[10\], selective prediction and significance tests.
4. A deployed system with a leaf gatekeeper, Grad-CAM, severity estimate and treatment guidance.

### G. Organization of the Paper

Sections II–V cover related work, method, results and conclusions.

## II. Literature Review

Work from 2022 to 2026 has pursued lighter CNNs, hybrids that add self-attention or state-space blocks, and, recently, evaluation beyond clean accuracy. Of sixteen original studies selected, five are analysed below, six are compared in Table I, and the five closest to this work are examined in Section III-C.

### A. Multi-Scale and Hybrid Architectures

Zhu et al. \[11\] fused multi-scale convolution with self-attention at shallow and deep levels (MSCVT), reaching 99.86% on PlantVillage and 97.50% on an apple leaf set. Combining shallow and deep features helps small lesions, but robustness and confidence were not examined; this work keeps the multi-scale premise with a pure CNN and tests it under corruption.

Guan et al. \[12\] built the 13.3 MB Dise-Efficient on EfficientNetV2; it reached 99.80% on PlantVillage but 64.40% on the field-captured IP102 pest set. This 35-point gap shows that laboratory accuracy does not transfer to the field even with a strong backbone, which motivates the corruption and field tests used here.

Gole et al. \[13\] (TrIncNet, a ViT with inception blocks) gained 5.38 points over a plain ViT on PlantVillage but only 2.87 points on in-field maize images, without calibration or robustness tests.

Meng et al. \[14\] fused convolutional and transformer branches, reaching 99.71% on PlantVillage with 4.9 M parameters, but did not describe how augmented copies of a leaf are kept out of the test split.

Zhang and Liu \[15\] fused shallow, medium and deep features with adaptive channel attention in a Vision Mamba network on field-acquired PlantDoc images, reaching 92.67% accuracy, 5.33 points above its baseline, with paired t-tests; calibration was not measured.

### B. Comparative Survey of Further Studies

Table I summarises six further original studies.

**TABLE I. Comparative survey of related studies**

| No. | Authors and Year | Dataset | Methodology | Reported Results | Limitations |
| --- | --- | --- | --- | --- | --- |
| \[16\] | Andrew et al., 2022 | PlantVillage, 54,305 images, 38 classes | Fine-tuned DenseNet-121, ResNet-50, VGG-16, Inception V4 | DenseNet-121: 99.81% accuracy | Single curated dataset; no field, corruption or calibration tests |
| \[17\] | Hassan and Maji, 2022 | PlantVillage, rice, cassava | Inception layers, residual links, depthwise separable convolution | 99.39%, 99.66%, 76.59% | Large drop on the harder cassava set |
| \[18\] | Borhani et al., 2022 | Multiple leaf datasets | ViT, CNN and CNN–ViT hybrids | Attention raised accuracy but slowed prediction; hybrids recovered speed | Accuracy–speed trade-off only; no robustness analysis |
| \[19\] | Li and Li, 2022 | Self-built apple leaf set with complex backgrounds | ConvViT: convolution plus linear-complexity attention | 96.85%, comparable to Swin-Tiny at 32.7% of its parameters | One crop; self-built data limit comparison |
| \[20\] | Lin et al., 2022 | PlantVillage-based few-shot tasks, intra- and cross-domain | Meta-Baseline with cascaded multi-scale features and channel attention | 5-shot: 77.43% single-plant, 92.83% multi-plant | Few-shot setting; accuracy still modest |
| \[21\] | De Silva and Brown, 2023 | Self-collected multispectral set, six filters | CNNs, ViT-B16 and hybrids | ViT-B16: 83.3% accuracy, 89.5% F1 (average) | Specialised optics; moderate accuracy |

### C. Research Trends and Gap

PlantVillage accuracy has converged at 99.4–99.9% \[11\], \[12\], \[14\], \[16\], \[17\], so clean gains no longer discriminate between designs. Multi-scale fusion and attention are standard for small lesions \[11\], \[15\], \[20\], but are applied inside the backbone or at one output scale. Every study that tested harder data observed a large drop \[12\], \[13\], \[17\], \[21\], yet only \[6\] measures robustness and calibration. None (i) controls augmented-copy leakage, (ii) fuses attention-refined features from several depths at an EfficientNetV2 head, and (iii) reports calibration, selective risk and robustness together. The closest studies \[4\], \[6\], \[22\]–\[24\] inform Section III.

## III. Methodology

### A. Dataset Overview

The study uses the augmented PlantVillage release on Kaggle \[25\], derived from \[2\]: 87,867 RGB images of single detached leaves on uniform backgrounds, covering 14 crops and 38 classes (26 diseased, 12 healthy). Rotated, flipped and pixel-shifted copies of each photograph are stored as separate files with suffixes such as `_90deg` and `_flipTB`. Table II gives the split.

**TABLE II. Leaf-disjoint data split**

| Subset | Images | Share | Role |
| --- | --- | --- | --- |
| Training | 70,146 | 79.8% | Weight updates |
| Validation | 8,832 | 10.1% | Checkpoint, temperature |
| Test | 8,889 | 10.1% | All reported results |
| Total | 87,867 | 100% | 14 crops, 38 classes |

The images are laboratory captures of one leaf each, and no labelled field photographs are included, so eight field photographs of supported classes were collected as a qualitative check.

### B. Dataset Preprocessing

**Leakage audit and leaf-grouped split.** Each file is mapped to its source leaf ℓ(f) by stripping the augmentation suffix. Under a random file split, 67.5% of test images had a sibling in training or validation, so all files sharing ℓ(f) are assigned to the same subset (80/10/10 over leaf groups, seed 42):

```latex
\ell(f_i)=\ell(f_j)\;\Rightarrow\;\mathrm{split}(f_i)=\mathrm{split}(f_j) \qquad (1)
```

A one-copy-per-leaf sampler draws one copy of each leaf per epoch, so leaves with many stored copies are not over-weighted.

**Standard augmentation.** Training uses a random resized crop to 224 × 224, horizontal and vertical flips and colour jitter (0.2 brightness, contrast and saturation; 0.1 hue); evaluation resizes to 256 and centre-crops 224. Images are normalised with ImageNet channel statistics μ\_c, σ\_c:

```latex
\hat{x}_c=\frac{x_c-\mu_c}{\sigma_c} \qquad (2)
```

**Field augmentation (optional).** Gaussian blur (kernel 9, σ ∈ \[0.5, 3\]) and the sensor noise of Eq. (3) are each applied to 30% of training images. Motion blur, JPEG, low light and overexposure are never used in training, so they measure generalisation to unseen degradations.

```latex
x'=\mathrm{clip}_{[0,1]}\left(x+0.12\,u\,\varepsilon\right),\quad u\sim\mathcal{U}(0,1),\;\varepsilon\sim\mathcal{N}(0,I) \qquad (3)
```

### C. Methodology Overview

Fig. 1 shows the workflow: development (leakage audit, split, training of five models, evaluation under seven conditions) and deployment (gatekeeper, classifier, temperature scaling, Grad-CAM, severity, treatment lookup). Table III summarises the five studies that shaped the design.

&#91;embedded content: Fig. 1. Proposed methodology and system workflow\]

**Fig. 1.** Proposed methodology and system workflow. The leaf-disjoint split (highlighted) is the basis of every reported result; the trained weights and temperature T feed the deployed classifier.



**TABLE III. The five most relevant studies and their influence on this work**

| Ref. | Study | Method | Reported results | Limitation | Use in this work |
| --- | --- | --- | --- | --- | --- |
| \[22\] | Albattah et al., 2022, Frontiers in Plant Science | EfficientNetV2-B4 with added dense layers | Precision 99.63%, recall 99.93%, accuracy 99.99% | Clean test only; leakage control not described | Confirms EfficientNetV2 as backbone family |
| \[23\] | Zhao et al., 2022, Computers and Electronics in Agriculture | Inception-residual CNN with embedded modified CBAM; web deployment | 99.55% overall; 98.44%, 99.43%, 95.20% per crop | Attention at one stage; three crops | CBAM for lesion focus; deployed web system |
| \[24\] | Wang et al., 2024, Frontiers in Plant Science | CBAM in backbone, shallow features fused through BiRepGFPN in YOLOv6 | Tomato mAP 93.8%, F1 94.0%; mAP +2.6 to +11.8 points over YOLO variants on PlantDoc | Detection task; no calibration analysis | Shallow-feature fusion for small lesions |
| \[4\] | Salman et al., 2025, Frontiers in Plant Science | ViT with mixture of experts, entropy and orthogonal regularisation | +20% over ViT; 68% PlantVillage to PlantDoc | Large model; field accuracy still low | Defines the field-generalisation problem |
| \[6\] | Das et al., 2025, IEEE ICCCMLA | ResNet-18, EfficientNet-B0, ConvNeXt-Tiny under 8 corruptions at 3 severities | Similar clean accuracy, divergent mCE and ECE; ConvNeXt-Tiny most robust | Existing models only; no new design | Robustness and calibration protocol |

The head keeps the EfficientNetV2 backbone validated in \[22\], applies CBAM as in \[23\] but at three depths, and fuses shallow and deep features as \[24\] does for detection. It targets the field gap of \[4\] with a 0.22 M-parameter head rather than an expert ensemble, and extends the evaluation view of \[6\] with temperature scaling, selective prediction and significance tests.

**Multi-scale attention fusion (MSAF).** As Fig. 2 shows, the ImageNet-pretrained EfficientNetV2-S \[7\] is tapped at stage 3 (64 channels, 28 × 28), stage 5 (160 channels, 14 × 14) and the final 1 × 1 projection (1,280 channels, 7 × 7). Each map F is refined by CBAM \[8\]: channel attention M\_c (shared MLP, reduction 16) gives F′ = M\_c ⊗ F, spatial attention M\_s (7 × 7 convolution) is applied to F′, and the block returns F + M\_s ⊗ F′ (residual):

```latex
M_c(F)=\sigma\big(\mathrm{MLP}(\mathrm{AvgPool}(F))+\mathrm{MLP}(\mathrm{MaxPool}(F))\big) \qquad (4)
```

```latex
M_s(F')=\sigma\big(f^{7\times7}([\mathrm{AvgPool}_c(F');\mathrm{MaxPool}_c(F')])\big),\quad F'=M_c\otimes F,\; F''=M_s\otimes F' \qquad (5)
```

Global average pooling dilutes small, strong lesion activations, so each refined map is pooled by GeM \[26\] with learnable p (initialised to 3) over spatial positions Ω:

```latex
d_k=\Big(\frac{1}{|\Omega|}\sum_{(i,j)\in\Omega}x_{k,i,j}^{\,p}\Big)^{1/p} \qquad (6)
```

The three descriptors are layer-normalised so that the small fine-scale vectors are not dominated. During training, scale-dropout multiplies each by m\_s ~ Bernoulli(0.9), keeping at least one scale. The fused 1,504-d vector z of Eq. (7) passes through dropout (0.3) and a linear layer, ŷ = W·Dropout(z) + b:

```latex
z=[\,m_1\,\mathrm{LN}(d^{(1)});\;m_2\,\mathrm{LN}(d^{(2)});\;m_3\,\mathrm{LN}(d^{(3)})\,],\qquad \hat{y}=W\,\mathrm{Dropout}_{0.3}(z)+b \qquad (7)
```

&#91;embedded content: Fig. 2. EfficientNetV2-MSAF architecture\]

**Fig. 2.** EfficientNetV2-MSAF architecture. Three backbone depths are each refined by CBAM, pooled by GeM and layer-normalised, then concatenated with scale-dropout before a single linear classifier.

The head adds 220,841 parameters (+1.09%, 20.45 M total) at an unchanged 2.85 GMACs. Two controls isolate its effect: the stock head (baseline) and one CBAM block on the 1,280-channel map (CBAM variant).

### D. Model Training and Implementation

All five models (baseline, CBAM, MSAF, and baseline and MSAF with field augmentation) share one recipe: 8 epochs, batch 32, AdamW \[27\] (learning rate 10⁻³, weight decay 10⁻⁴), a one-cycle schedule \[28\], mixed precision, seed 42 and cross-entropy with label smoothing \[29\] ε = 0.1 over K = 38 classes:

```latex
\mathcal{L}=-\sum_{k=1}^{K}\Big[(1-\varepsilon)\,y_k+\frac{\varepsilon}{K}\Big]\log\hat{y}_k \qquad (8)
```

The best-validation checkpoint is kept, and a temperature T is fitted on the validation set by minimising NLL (Eq. 9). Training on an NVIDIA RTX 3050 (4 GB) took 37.8, 35.8 and 48.7 min for the baseline, CBAM and MSAF models.

```latex
\hat{p}_k=\frac{\exp(z_k/T)}{\sum_{j=1}^{K}\exp(z_j/T)} \qquad (9)
```

The deployed Streamlit application follows Algorithm 1.

**Algorithm 1. Diagnosis pipeline**

1. Input: photograph I. Output: diagnosis report or rejection.
2. Run the leaf gatekeeper; if I is not a plant image or shows several leaves, reject it with a reason and stop.
3. Resize and normalise I (Eq. 2) and compute logits z with the classifier.
4. Calibrate the probabilities with temperature T (Eq. 9); flag low-confidence predictions.
5. Compute the Grad-CAM map \[30\] for the predicted class.
6. Segment the leaf and compute the severity index as the share of leaf pixels flagged by Grad-CAM; map it to one of four stages.
7. Look up the pathogen, symptoms, organic and chemical controls and prevention for the class, and return the report (optionally as PDF).

The application uses the EfficientNetV2-S checkpoint, because standard Grad-CAM gives noisy maps on MSAF, whose per-scale layer normalisation cancels much of the gradient weighting. The severity index is a heuristic, not a laboratory measurement.

## IV. Results and Discussion

### A. Experimental Setup

All results use the 8,889-image leaf-disjoint test set under clean images and six fixed-severity corruptions in the style of \[10\] (Gaussian blur, motion blur, sensor noise, low light, JPEG quality 10, overexposure). Metrics are accuracy, macro-F1, mean corrupted accuracy (mCA), expected calibration error (ECE, 15 bins) before and after temperature scaling (TS), and selective prediction \[31\] on pooled corrupted images: area under the risk–coverage curve (AURC), error-detection AUROC and accuracy at 90% coverage. Paired differences use exact McNemar tests \[32\] and 95% bootstrap intervals. Latency is per image on the RTX 3050 and a 4-thread CPU.

### B. Quantitative Results

Table IV reports the main results. Clean accuracy spans 99.51–99.62% and no pairwise difference is significant (baseline vs. MSAF p = 0.143; vs. CBAM p = 0.164; field-augmented pair p = 0.86), so clean accuracy cannot separate the architectures.

**TABLE IV. Main results on the leaf-disjoint test set (8,889 images)**

| Model | Params (M) | Clean acc. (%) | Macro-F1 (%) | mCA (%) | ECE raw (%) | ECE after TS (%) | Corrupted ECE after TS (%) | AURC (%) | Error-detection AUROC (%) | Field photos |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EfficientNetV2-S (baseline) | 20.23 | 99.62 | 99.61 | 82.20 | 10.57 | 0.17 | 12.23 | 5.21 | 85.49 | 6/8 |
| + CBAM | 20.43 | 99.51 | 99.51 | 83.08 | 10.17 | 0.29 | 11.65 | 5.16 | 85.29 | 8/8 |
| EfficientNetV2-MSAF | 20.45 | 99.51 | 99.51 | 82.99 | **5.14** | 0.29 | 10.83 | 4.16 | 87.27 | 8/8 |
| Baseline + field aug. | 20.23 | 99.58 | 99.57 | **95.67** | 10.56 | 0.19 | **2.49** | **0.45** | 93.82 | 6/8 |
| MSAF + field aug. (proposed system) | 20.45 | 99.56 | 99.55 | 94.84 | 5.44 | 0.21 | 2.77 | 0.50 | **93.98** | 8/8 |

**Calibration.** MSAF's raw ECE is 5.14% against 10.57% for the baseline (−5.43 points, 95% CI −5.55 to −5.26); single-scale CBAM lowers it by only 0.40 points, so the gain comes from the multi-scale head. TS brings clean ECE below 0.3% for all models, but without field augmentation it worsens corrupted-image ECE (baseline 8.81% to 12.23%); only the field-augmented models keep it low (2.49% and 2.77%).

**Robustness.** Without field augmentation, MSAF raises mCA by 0.79 points (95% CI 0.48 to 1.10): it is better under sensor noise (85.43% vs. 80.64%, p < 10⁻³⁷) and low light (94.35% vs. 90.04%, p < 10⁻⁴³) but worse under motion blur (50.11% vs. 54.48%, p < 10⁻¹⁸). Field augmentation lifts mCA by 12–13 points, and unseen motion blur rises to 86.32% (baseline) and 81.85% (MSAF); with it, MSAF trails the baseline by 0.83 points (95% CI −1.01 to −0.64), mainly on motion blur (Fig. 3).

&#91;embedded content: Fig. 3. Source: results/paper/metrics.json · 5 models × 7 conditions\]

**Fig. 3.** Test accuracy of the five models under clean and six corrupted conditions. Blue markers (field augmentation) sit far right of grey markers under blur and noise; the head type changes the result mainly under motion blur, sensor noise and low light.

**Selective prediction.** Without field augmentation, MSAF lowers AURC from 5.21% to 4.16% and raises error-detection AUROC from 85.49% to 87.27%. With field augmentation, both models reach AURC of about 0.5% and 98.5–99.0% accuracy at 90% coverage.

**Efficiency.** MSAF adds 4.1 ms GPU and 9.8 ms CPU latency per image at unchanged GMACs (Table V).

**TABLE V. Computational cost (224 × 224 input, batch 1)**

| Model | Params (M) | GMACs | GPU (ms) | CPU, 4 thr. (ms) | Train (min) |
| --- | --- | --- | --- | --- | --- |
| Baseline | 20.23 | 2.85 | 14.63 | 56.0 | 37.8 |
| + CBAM | 20.43 | 2.85 | 15.02 | 58.0 | 35.8 |
| MSAF | 20.45 | 2.85 | 18.68 | 65.8 | 48.7 |

**Errors and gatekeeper.** The most frequent clean error is corn gray leaf spot predicted as northern leaf blight (9–15 images), the baseline's two lowest per-class F1 scores (97.07%, 97.64%). The gatekeeper rejected five of six non-leaf images; without it, a text document was labelled healthy corn at 81.2%. The one that passed, random noise, received 18.3% confidence and triggered the warning.

### C. Graphical Results

Fig. 4 shows Grad-CAM explanations from the deployed model on test leaves and field photographs.

&#91;image: Grad-CAM explanations from the deployed EfficientNetV2-S model\]

**Fig. 4.** Grad-CAM explanations from the deployed EfficientNetV2-S model (top: input; bottom: heatmap; below: prediction, calibrated confidence and severity). Columns marked \* are field photographs. Heat concentrates on lesions in the test leaves. The corn gray leaf spot field photo is misclassified as northern leaf blight at 46% confidence, the same confusion that dominates the test-set errors, and its low confidence would trigger the app's warning.

### D. Comparison With Existing Research

Table VI is indicative only: published models were not re-run, use random splits that may leak augmented copies, and report no robustness or calibration on PlantVillage.

**TABLE VI. Comparison with published results (as reported by each study)**

| Study | Model | Test data and split | Clean accuracy | Harder or field data | Calibration reported |
| --- | --- | --- | --- | --- | --- |
| Mohanty et al. \[3\] | GoogLeNet | PlantVillage, random split | 99.35% | 31.4% on images from other sources | No |
| Andrew et al. \[16\] | DenseNet-121 | PlantVillage, 38 classes | 99.81% | Not tested | No |
| Albattah et al. \[22\] | EfficientNetV2-B4 + dense | PlantVillage (Kaggle) + drone | 99.99% | Drone images included in test | No |
| Guan et al. \[12\] | Dise-Efficient (EfficientNetV2) | PlantVillage; IP102 | 99.80% | 64.40% on IP102 | No |
| Meng et al. \[14\] | CNN–ViT dual branch, 4.9 M | PlantVillage | 99.71% | Not tested | No |
| Salman et al. \[4\] | ViT + mixture of experts | PlantVillage to PlantDoc | Not compared here | 68% cross-domain | No |
| This work | EfficientNetV2-MSAF + field aug. | Augmented PlantVillage, leaf-disjoint | 99.56% | mCA 94.84% over 6 corruptions; 8/8 field photos | Yes: ECE 5.44% raw |

On clean images the system is on par with published models on a stricter test set; its distinguishing results are measured robustness, calibrated confidence and non-leaf rejection. The 8/8 field result is not comparable with the 31.4% or 68% figures, which come from hundreds of images.

### E. Critical Result Analysis

The baseline concentrates confidence near 0.90 even on clean images (mean 89.08% at 99.62% accuracy), a sign of label-smoothing saturation; fusing layer-normalised descriptors from three depths spreads the logits and lowers NLL (0.069 vs. 0.123). Fine 28 × 28 features help when noise and darkness corrupt texture uniformly, but motion blur smears exactly those details. As in \[6\], robustness depends more on training data than on architecture.

Each model was trained once with one seed, so differences under about one point should not be over-read even when McNemar tests are significant. In practice, a deployed tool should be trained with capture-style augmentation and report calibrated confidence, and the MSAF head is worth its cost when trustworthy confidence matters more than motion-blur robustness.

## V. Conclusion and Future Work

This study addressed the gap between near-perfect laboratory accuracy and unreliable field performance in crop disease diagnosis. A leaf-disjoint split of 87,867 PlantVillage images removed augmented-copy leakage that affected 67.5% of a random split's test images, and EfficientNetV2-MSAF fused attention-refined features from three backbone depths for 1.09% more parameters. All five models reached 99.51–99.62% clean accuracy with no significant difference, while the multi-scale head halved raw calibration error (10.57% to 5.14%) and reduced selective risk under unseen corruptions by 20%. Field augmentation supplied most robustness, and the deployed system, with a leaf gatekeeper, Grad-CAM and treatment guidance, raised mean corrupted accuracy from 82.20% to 94.84% and classified all eight field photographs correctly. Its main limitations are single-seed training, synthetic corruptions at one severity and only eight field images. Future work will evaluate on PlantDoc, repeat training over several seeds, add motion-blur and multi-severity augmentation, and validate severity against expert scoring.

## References

The 16 surveyed 2022–2026 studies are \[4\], \[6\] and \[11\]–\[24\]; each was checked against its Crossref DOI record (title, authors, venue, volume, year). The remaining references support methods and background.

&#91;1\] S. Savary, L. Willocquet, S. J. Pethybridge, P. Esker, N. McRoberts, and A. Nelson, “The global burden of pathogens and pests on major food crops,” *Nature Ecology & Evolution*, vol. 3, no. 3, pp. 430–439, 2019, doi: 10.1038/s41559-018-0793-y.

&#91;2\] D. P. Hughes and M. Salathé, “An open access repository of images on plant health to enable the development of mobile disease diagnostics,” arXiv:1511.08060, 2015.

&#91;3\] S. P. Mohanty, D. P. Hughes, and M. Salathé, “Using deep learning for image-based plant disease detection,” *Frontiers in Plant Science*, vol. 7, Art. no. 1419, 2016, doi: 10.3389/fpls.2016.01419.

&#91;4\] Z. Salman, A. Muhammad, and D. Han, “Plant disease classification in the wild using vision transformers and mixture of experts,” *Frontiers in Plant Science*, vol. 16, Art. no. 1522985, 2025, doi: 10.3389/fpls.2025.1522985.

&#91;5\] D. Singh, N. Jain, P. Jain, P. Kayal, S. Kumawat, and N. Batra, “PlantDoc: A dataset for visual plant disease detection,” in *Proc. 7th ACM IKDD CoDS and 25th COMAD*, 2020, pp. 249–253.

&#91;6\] J. Das, Y. Panjwani, and E. Uchoi, “Beyond accuracy: Robustness and calibration evaluation of deep learning models for plant disease detection,” in *Proc. IEEE 7th Int. Conf. Cybernetics, Cognition and Machine Learning Applications (ICCCMLA)*, 2025, pp. 1–6, doi: 10.1109/ICCCMLA66092.2025.11581126.

&#91;7\] M. Tan and Q. V. Le, “EfficientNetV2: Smaller models and faster training,” in *Proc. 38th Int. Conf. Machine Learning (ICML)*, 2021, pp. 10096–10106.

&#91;8\] S. Woo, J. Park, J.-Y. Lee, and I. S. Kweon, “CBAM: Convolutional block attention module,” in *Proc. European Conf. Computer Vision (ECCV)*, 2018, pp. 3–19.

&#91;9\] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, “On calibration of modern neural networks,” in *Proc. 34th Int. Conf. Machine Learning (ICML)*, 2017, pp. 1321–1330.

&#91;10\] D. Hendrycks and T. Dietterich, “Benchmarking neural network robustness to common corruptions and perturbations,” in *Proc. Int. Conf. Learning Representations (ICLR)*, 2019.

&#91;11\] D. Zhu, J. Tan, C. Wu, K. Yung, and A. W. H. Ip, “Crop disease identification by fusing multiscale convolution and vision transformer,” *Sensors*, vol. 23, no. 13, Art. no. 6015, 2023, doi: 10.3390/s23136015.

&#91;12\] H. Guan, C. Fu, G. Zhang, K. Li, P. Wang, and Z. Zhu, “A lightweight model for efficient identification of plant diseases and pests based on deep learning,” *Frontiers in Plant Science*, vol. 14, Art. no. 1227011, 2023, doi: 10.3389/fpls.2023.1227011.

&#91;13\] P. Gole, P. Bedi, S. Marwaha, M. A. Haque, and C. K. Deb, “TrIncNet: A lightweight vision transformer network for identification of plant diseases,” *Frontiers in Plant Science*, vol. 14, Art. no. 1221557, 2023, doi: 10.3389/fpls.2023.1221557.

&#91;14\] Q. Meng, J. Guo, H. Zhang, Y. Zhou, and X. Zhang, “A dual-branch model combining convolution and vision transformer for crop disease classification,” *PLOS ONE*, vol. 20, no. 4, Art. no. e0321753, 2025, doi: 10.1371/journal.pone.0321753.

&#91;15\] S. Zhang and R. Liu, “Multi-scale feature fusion-based vision Mamba for robust plant disease image classification on field-acquired PlantDoc data,” *Frontiers in Plant Science*, vol. 17, Art. no. 1842426, 2026, doi: 10.3389/fpls.2026.1842426.

&#91;16\] J. Andrew, J. Eunice, D. E. Popescu, M. K. Chowdary, and J. Hemanth, “Deep learning-based leaf disease detection in crops using images for agricultural applications,” *Agronomy*, vol. 12, no. 10, Art. no. 2395, 2022, doi: 10.3390/agronomy12102395.

&#91;17\] S. M. Hassan and A. K. Maji, “Plant disease identification using a novel convolutional neural network,” *IEEE Access*, vol. 10, pp. 5390–5401, 2022, doi: 10.1109/ACCESS.2022.3141371.

&#91;18\] Y. Borhani, J. Khoramdel, and E. Najafi, “A deep learning based approach for automated plant disease classification using vision transformer,” *Scientific Reports*, vol. 12, Art. no. 11554, 2022, doi: 10.1038/s41598-022-15163-0.

&#91;19\] X. Li and S. Li, “Transformer help CNN see better: A lightweight hybrid apple disease identification model based on transformers,” *Agriculture*, vol. 12, no. 6, Art. no. 884, 2022, doi: 10.3390/agriculture12060884.

&#91;20\] H. Lin, R. Tse, S.-K. Tang, Z.-P. Qiang, and G. Pau, “Few-shot learning approach with multi-scale feature fusion and attention for plant disease recognition,” *Frontiers in Plant Science*, vol. 13, Art. no. 907916, 2022, doi: 10.3389/fpls.2022.907916.

&#91;21\] M. De Silva and D. Brown, “Multispectral plant disease detection with vision transformer–convolutional neural network hybrid approaches,” *Sensors*, vol. 23, no. 20, Art. no. 8531, 2023, doi: 10.3390/s23208531.

&#91;22\] W. Albattah, A. Javed, M. Nawaz, M. Masood, and S. Albahli, “Artificial intelligence-based drone system for multiclass plant disease detection using an improved efficient convolutional neural network,” *Frontiers in Plant Science*, vol. 13, Art. no. 808380, 2022, doi: 10.3389/fpls.2022.808380.

&#91;23\] Y. Zhao, C. Sun, X. Xu, and J. Chen, “RIC-Net: A plant disease classification model based on the fusion of Inception and residual structure and embedded attention mechanism,” *Computers and Electronics in Agriculture*, vol. 193, Art. no. 106644, 2022, doi: 10.1016/j.compag.2021.106644.

&#91;24\] Y. Wang, P. Zhang, and S. Tian, “Tomato leaf disease detection based on attention mechanism and multi-scale feature fusion,” *Frontiers in Plant Science*, vol. 15, Art. no. 1382802, 2024, doi: 10.3389/fpls.2024.1382802.

&#91;25\] “New Plant Diseases Dataset (Augmented),” Kaggle, 2018. \[Online\]. Available: https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset

&#91;26\] F. Radenović, G. Tolias, and O. Chum, “Fine-tuning CNN image retrieval with no human annotation,” *IEEE Trans. Pattern Analysis and Machine Intelligence*, vol. 41, no. 7, pp. 1655–1668, 2019.

&#91;27\] I. Loshchilov and F. Hutter, “Decoupled weight decay regularization,” in *Proc. Int. Conf. Learning Representations (ICLR)*, 2019.

&#91;28\] L. N. Smith and N. Topin, “Super-convergence: Very fast training of neural networks using large learning rates,” in *Proc. SPIE Artificial Intelligence and Machine Learning for Multi-Domain Operations Applications*, vol. 11006, 2019, Art. no. 1100612.

&#91;29\] C. Szegedy, V. Vanhoucke, S. Ioffe, J. Shlens, and Z. Wojna, “Rethinking the Inception architecture for computer vision,” in *Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 2818–2826.

&#91;30\] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, “Grad-CAM: Visual explanations from deep networks via gradient-based localization,” in *Proc. IEEE Int. Conf. Computer Vision (ICCV)*, 2017, pp. 618–626.

&#91;31\] Y. Geifman and R. El-Yaniv, “Selective classification for deep neural networks,” in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 30, 2017, pp. 4878–4887.

&#91;32\] T. G. Dietterich, “Approximate statistical tests for comparing supervised classification learning algorithms,” *Neural Computation*, vol. 10, no. 7, pp. 1895–1923, 1998.

## Open items: missing experiments, unsupported claims and limitations

The paper uses only numbers found in the project's result files (`results/paper/metrics.json`, `efficiency.json`, `gatekeeper_test.json`, `data/splits/leaf_disjoint.json`) and in the abstracts of the cited studies. The items below are still open; none of them has been presented as a result.

| Item | Type | Status | What closes it |
| --- | --- | --- | --- |
| Author names, affiliation, emails, guide | Missing information | Placeholders in the title block | Author to supply |
| PlantDoc or other field-dataset test | Missing experiment | Not run; listed as future work | Map PlantDoc classes to the 38 classes and test all five models (about 2 h) |
| Multiple training seeds | Missing experiment | Single seed (42); stated as limitation | Retrain with 3 seeds (about 40–55 min per model per seed) and report mean ± std |
| Field photographs | Weak evidence | Only 8 images; reported as qualitative | Larger labelled field set |
| Corruption severity | Scope limit | One fixed severity per corruption | Multi-severity sweep |
| Severity index | Unvalidated heuristic | Described as heuristic, not as measured | Comparison against expert severity scores |
| Grad-CAM on MSAF | Known weakness | Deployed app uses baseline for explanations | Explanation method for multi-scale heads |
| Details of \[6\], \[24\], \[4\], \[15\] | Source depth | Taken from abstracts verified via Crossref | Read full texts before final submission |
| Google Scholar as discovery platform | Process deviation | Papers found and verified through Crossref/DOI records, because Scholar blocks automated queries | Optionally re-check each title on Google Scholar |
| Six-page IEEE limit | Formatting check | Not yet measurable in this doc | Transfer to the IEEE two-column template and check page count |
| Figures 1–2 | Formatting | Drawn in this doc | Export as vector/600 dpi for the template; `scripts/paper_figures.py` regenerates the result plots |

The completion checklist in the project folder says the faculty checks AI-generated content. Rewrite the prose in your own words before submission; the facts, numbers and references can stay.
