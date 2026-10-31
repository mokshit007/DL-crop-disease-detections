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

**Abstract.** Convolutional networks routinely exceed 99% accuracy on the PlantVillage leaf disease benchmark, yet their accuracy falls sharply on photographs taken outside the laboratory. Three practices contribute to this gap: rotated and flipped copies of the same leaf leak across the train–test split, single-scale classifier heads average away small lesions, and models are judged by clean accuracy alone. This study rebuilds the evaluation and the classifier head together. A leaf-grouped split of 87,867 images covering 14 crops and 38 classes removes the leakage of a random split, in which 67.5% of test images had a copy in training or validation. On this split, EfficientNetV2-MSAF, a multi-scale attention fusion head that applies convolutional block attention, generalised-mean pooling and scale-dropout at three backbone depths (+0.22 M parameters, +1.09%), is compared with EfficientNetV2-S and a single-scale attention variant, each trained with and without field augmentation. Evaluation covers accuracy and macro-F1, six image corruptions, expected calibration error (ECE), selective prediction and paired McNemar tests. All models reach 99.51–99.62% clean accuracy with no significant difference. MSAF halves the raw ECE from 10.57% to 5.14% and lowers the area under the risk–coverage curve by 20%, whereas field augmentation supplies most of the corruption robustness. The combined system raises mean corrupted accuracy from 82.20% to 94.84% and classifies all eight available field photographs correctly. It is deployed with a leaf gatekeeper, Grad-CAM explanations, a severity estimate and treatment guidance.

**Index Terms:** plant disease classification, EfficientNetV2, attention, multi-scale feature fusion, data leakage, calibration, corruption robustness, explainable AI.

## I. Introduction

### A. Background and Research Context

Plant pathogens and pests are estimated to remove 17–30% of the global harvest of wheat, rice, maize, potato and soybean, with the heaviest losses in food-deficit regions \[1\]. Plant pathologists are scarce in rural areas, so an image-based first diagnosis from a smartphone photograph offers a low-cost alternative. The open PlantVillage collection \[2\] made such systems practical, and convolutional neural networks (CNNs) trained on it exceeded 99% accuracy as early as 2016 \[3\].

### B. Research Problem and Its Significance

Laboratory accuracy on PlantVillage has since saturated between 99% and 100%, while accuracy on photographs from other sources remains far lower. Mohanty et al. reported a fall from 99.35% to 31.4% on images collected outside the dataset \[3\]. A 2025 vision transformer with a mixture of experts reached only 68% when transferred from PlantVillage to the in-the-wild PlantDoc images \[4\], \[5\]. A diagnosis tool that is confident and wrong under field conditions can lead to the wrong treatment being applied.

### C. Limitations of Conventional Approaches

Three weaknesses recur in current practice. First, the widely used augmented PlantVillage release stores rotated and flipped copies of each leaf as separate files, so a random file-level split places copies of one leaf in both training and test sets and inflates test accuracy. Second, most classifiers decide from the final, coarsest feature map, where a small lesion occupies a fraction of one cell and is averaged away by global pooling. Third, models are compared by clean accuracy alone, although robustness to corruption and the reliability of confidence scores determine whether a prediction can be trusted in the field \[6\].

### D. Motivation and Objectives

This work treats the evaluation protocol and the classifier head as a single problem. Its objectives are to (i) measure and remove augmented-copy leakage, (ii) design a lightweight head that preserves small-lesion evidence on an EfficientNetV2 backbone \[7\], (iii) evaluate accuracy together with corruption robustness, calibration and selective risk, and (iv) deploy the result in a usable diagnostic application.

### E. Research Challenges

Clean accuracy is already saturated, so architectural gains must be shown on other measures without overstating small differences. Training must fit a 4 GB consumer GPU, the added head must not noticeably raise inference cost, and real field photographs with verified labels are scarce.

### F. Contributions

1. A leaf-disjoint split of the 38-class augmented PlantVillage release that groups every copy of a leaf, showing that 67.5% of a random split's test images had a training or validation sibling.
2. EfficientNetV2-MSAF, a head that applies convolutional block attention (CBAM) \[8\], generalised-mean pooling and scale-dropout at three backbone depths for +1.09% parameters.
3. A controlled five-model comparison reporting macro-F1, six corruptions, expected calibration error before and after temperature scaling \[9\], \[10\], selective prediction and paired significance tests.
4. A deployed system adding a leaf gatekeeper, Grad-CAM explanations, a severity estimate and treatment guidance.

### G. Organization of the Paper

Section II reviews recent work and identifies the research gap. Section III describes the dataset, preprocessing, architecture and training. Section IV reports and discusses the results, and Section V concludes with limitations and future directions.

## II. Literature Review

Research from 2022 to 2026 has moved along three lines: lighter or better-tuned CNNs, hybrids that add self-attention or state-space blocks to capture global context, and, more recently, evaluation beyond clean accuracy. Sixteen original studies were selected; five are analysed below, six are compared in Table I, and the five most closely related to this work are examined in Section III-C.

### A. Multi-Scale and Hybrid Architectures

Zhu et al. \[11\] argued that CNNs model local lesion texture well but miss global context, and proposed MSCVT, which fuses multi-scale convolution with self-attention at both shallow and deep levels and uses inverted residual blocks to limit parameters. MSCVT reached 99.86% on PlantVillage and 97.50% on an apple leaf pathology set. The study shows that combining shallow and deep features helps small-lesion recognition, but both evaluations use curated images, and robustness and confidence reliability are not examined. The present work adopts the same multi-scale premise while keeping a pure CNN backbone and testing it under corruption.

Guan et al. \[12\] built Dise-Efficient on EfficientNetV2 and trained it with a dynamic learning-rate decay and transfer learning. The 13.3 MB model reached 99.80% on PlantVillage but 64.40% on IP102, a pest dataset captured in real environments. The 35-point gap between the two datasets is direct evidence that laboratory accuracy does not transfer to field conditions, even with a strong EfficientNetV2 backbone. This finding motivates the corruption and field tests used here.

Gole et al. \[13\] replaced the multilayer perceptron of a vision transformer (ViT) encoder with an inception block to form TrIncNet, a lighter network suited to IoT devices. On PlantVillage and an in-field maize dataset, it outperformed six CNNs and improved on a plain ViT by 5.38 and 2.87 points respectively. The smaller gain on in-field images again indicates that field data are harder, although calibration and corruption robustness are not reported.

Meng et al. \[14\] combined a convolutional branch for local features and a transformer branch for global features through a learnable weighted fusion, and added a locality-aware feed-forward layer with linear self-attention. With 4.9 M parameters and 0.62 GFLOPs, the model reached 99.71% on PlantVillage and 98.78% on a potato leaf set. It demonstrates that feature fusion can be both accurate and cheap. Like most PlantVillage studies, however, it does not describe how augmented copies of a leaf are kept out of the test split.

Zhang and Liu \[15\] addressed field-acquired images directly with an improved Vision Mamba network on PlantDoc. A multi-scale feature fusion module combines shallow, medium and deep features, and an adaptive channel attention module suppresses background. The model reached 92.67% accuracy and 91.70% macro-F1, 5.33 points above its baseline, with five-fold cross-validation and paired t-tests. This is one of few studies to report statistical significance; confidence calibration is still not measured.

### B. Comparative Survey of Further Studies

Table I summarises six further original studies.

**TABLE I. Comparative survey of related studies**

| No. | Authors and Year | Research Title | Dataset | Methodology | Reported Results | Limitations |
| --- | --- | --- | --- | --- | --- | --- |
| \[16\] | Andrew et al., 2022 | Deep learning-based leaf disease detection in crops using images for agricultural applications | PlantVillage, 54,305 images, 38 classes | Fine-tuned DenseNet-121, ResNet-50, VGG-16, Inception V4 | DenseNet-121: 99.81% accuracy | Single curated dataset; no field, corruption or calibration tests |
| \[17\] | Hassan and Maji, 2022 | Plant disease identification using a novel convolutional neural network | PlantVillage, rice, cassava | Inception layers, residual links, depthwise separable convolution | 99.39%, 99.66%, 76.59% | Large drop on the harder cassava set |
| \[18\] | Borhani et al., 2022 | A deep learning based approach for automated plant disease classification using vision transformer | Multiple leaf datasets | ViT, CNN and CNN–ViT hybrids | Attention raised accuracy but slowed prediction; hybrids recovered speed | Accuracy–speed trade-off only; no robustness analysis |
| \[19\] | Li and Li, 2022 | Transformer help CNN see better: A lightweight hybrid apple disease identification model based on transformers | Self-built apple leaf set with complex backgrounds | ConvViT: convolution plus linear-complexity attention | 96.85%, comparable to Swin-Tiny at 32.7% of its parameters | One crop; self-built data limit comparison |
| \[20\] | Lin et al., 2022 | Few-shot learning approach with multi-scale feature fusion and attention for plant disease recognition | PlantVillage-based few-shot tasks, intra- and cross-domain | Meta-Baseline with cascaded multi-scale features and channel attention | 5-shot: 77.43% single-plant, 92.83% multi-plant | Few-shot setting; accuracy still modest |
| \[21\] | De Silva and Brown, 2023 | Multispectral plant disease detection with vision transformer–convolutional neural network hybrid approaches | Self-collected multispectral set, six filters | CNNs, ViT-B16 and hybrids | ViT-B16: 83.3% accuracy, 89.5% F1 (average) | Specialised optics; moderate accuracy |

### C. Research Trends and Gap

Three trends emerge. Reported PlantVillage accuracy has converged between 99.4% and 99.9% \[11\], \[12\], \[14\], \[16\], \[17\], so further gains on clean images no longer discriminate between designs. Multi-scale fusion and attention are now standard tools for small lesions \[11\], \[15\], \[20\], but they are applied inside the backbone or at a single output scale. Every study that tested harder data observed a large drop \[12\], \[13\], \[17\], \[21\], yet only isolated recent work measures robustness and calibration \[6\]. None of the surveyed studies (i) controls augmented-copy leakage, (ii) fuses attention-refined features from several depths at the classifier head of an EfficientNetV2 backbone, and (iii) reports calibration, selective risk and corruption robustness alongside accuracy. The five studies closest to these aims \[4\], \[6\], \[22\]–\[24\] inform the method in Section III.

## III. Methodology

### A. Dataset Overview

The study uses the augmented release of PlantVillage distributed on Kaggle \[25\], derived from the original collection \[2\]. It contains 87,867 RGB leaf images of 14 crops in 38 classes (26 disease classes and 12 healthy classes), each showing a single detached leaf on a uniform background. The release enlarges PlantVillage by storing rotated, flipped and pixel-shifted copies of each photograph as separate files, identifiable by filename suffixes such as `_90deg`, `_flipTB`, `_new30degFlipLR` and `_newPixel25`. Table II gives the split used in this work.

**TABLE II. Leaf-disjoint data split**

| Subset | Images | Share | Role |
| --- | --- | --- | --- |
| Training | 70,146 | 79.8% | Weight updates |
| Validation | 8,832 | 10.1% | Checkpoint selection, temperature fitting |
| Test | 8,889 | 10.1% | All reported results |
| Total | 87,867 | 100% | 14 crops, 38 classes |

The dataset has three limitations: images are captured under controlled lighting with plain backgrounds, each image shows one leaf, and field photographs with verified labels are not included. Eight field photographs of supported classes were therefore collected separately as a small qualitative check.

### B. Dataset Preprocessing

**Leakage audit and leaf-grouped split.** Each file is mapped to its source leaf by stripping the augmentation suffix, giving a leaf identifier ℓ(f). Under the original random file split, 67.5% of test images had a sibling copy in training or validation. All files that share ℓ(f) are therefore assigned to the same subset, with an 80/10/10 ratio over leaf groups and a fixed seed of 42:

```latex
\ell(f_i)=\ell(f_j)\;\Rightarrow\;\mathrm{split}(f_i)=\mathrm{split}(f_j) \qquad (1)
```

During training, a one-copy-per-leaf sampler draws one copy of each physical leaf per epoch, so that leaves with many stored copies are not over-weighted while all copies are still seen across epochs.

**Standard augmentation and normalisation.** Training images receive a random resized crop to 224 × 224 pixels, horizontal and vertical flips, and colour jitter (brightness, contrast and saturation 0.2; hue 0.1). Evaluation images are resized to 256 pixels and centre-cropped to 224. All images are normalised with ImageNet statistics, where x is a pixel value and μ\_c, σ\_c are the channel mean and standard deviation:

```latex
\hat{x}_c=\frac{x_c-\mu_c}{\sigma_c} \qquad (2)
```

**Field augmentation (optional).** To model handheld capture, Gaussian blur (kernel 9, σ drawn from \[0.5, 3\]) and additive sensor noise are each applied to 30% of training images. Noise follows Eq. (3), with u drawn uniformly from \[0, 1\] and ε a standard normal tensor. Motion blur, JPEG compression, low light and overexposure are never used in training, so they measure generalisation to unseen degradations.

```latex
x'=\mathrm{clip}_{[0,1]}\left(x+0.12\,u\,\varepsilon\right),\quad u\sim\mathcal{U}(0,1),\;\varepsilon\sim\mathcal{N}(0,I) \qquad (3)
```

### C. Methodology Overview

Fig. 1 shows the complete workflow. The development path audits leakage, builds the leaf-disjoint split, trains five models under one recipe and evaluates them under seven conditions. The deployment path passes each uploaded photograph through a leaf gatekeeper, the classifier, temperature scaling, Grad-CAM, the severity estimate and the treatment lookup.

&#91;embedded content: Fig. 1. Proposed methodology and system workflow\]

**Fig. 1.** Proposed methodology and system workflow. The leaf-disjoint split (highlighted) is the basis of every reported result; the trained weights and temperature T feed the deployed classifier.

**Supporting research.** Five studies shaped the design; Table III summarises them.

**TABLE III. The five most relevant studies and their influence on this work**

| Ref. | Study | Dataset | Method | Reported results | Limitation | Use in this work |
| --- | --- | --- | --- | --- | --- | --- |
| \[22\] | Albattah et al., 2022, Frontiers in Plant Science | PlantVillage (Kaggle) plus drone images | EfficientNetV2-B4 with added dense layers | Precision 99.63%, recall 99.93%, accuracy 99.99% | Clean test only; leakage control not described | Confirms EfficientNetV2 as backbone family |
| \[23\] | Zhao et al., 2022, Computers and Electronics in Agriculture | Corn, potato and tomato leaves | Inception-residual CNN with embedded modified CBAM; web deployment | 99.55% overall; 98.44%, 99.43%, 95.20% per crop | Attention at one stage; three crops | CBAM for lesion focus; deployed web system |
| \[24\] | Wang et al., 2024, Frontiers in Plant Science | PlantDoc; tomato leaf set | CBAM in backbone, shallow features fused through BiRepGFPN in YOLOv6 | Tomato mAP 93.8%, F1 94.0%; mAP +2.6 to +11.8 points over YOLO variants on PlantDoc | Detection task; no calibration analysis | Shallow-feature fusion for small lesions |
| \[4\] | Salman et al., 2025, Frontiers in Plant Science | PlantVillage, PlantDoc, cross-domain sets | ViT with mixture of experts, entropy and orthogonal regularisation | +20% over ViT; 68% PlantVillage to PlantDoc | Large model; field accuracy still low | Defines the field-generalisation problem |
| \[6\] | Das et al., 2025, IEEE ICCCMLA | Benchmark plant disease set | ResNet-18, EfficientNet-B0, ConvNeXt-Tiny under 8 corruptions at 3 severities | Similar clean accuracy, divergent mCE and ECE; ConvNeXt-Tiny most robust | Existing models only; no new design | Robustness and calibration protocol |

The proposed head combines the lessons of these studies. It keeps the EfficientNetV2 backbone validated in \[22\], applies CBAM as in \[23\] but at three depths rather than one, and fuses shallow and deep features as \[24\] does for detection, here at the classification head. It targets the field gap described in \[4\] with a 0.22 M-parameter head instead of a large expert ensemble, and adopts the evaluation view of \[6\], extended with temperature scaling, selective prediction and significance tests.

**Multi-scale attention fusion (MSAF).** Fig. 2 shows the architecture. The ImageNet-pretrained EfficientNetV2-S backbone \[7\] is tapped at three depths: stage 3 (64 channels, 28 × 28, one cell covers 8 × 8 pixels), stage 5 (160 channels, 14 × 14) and the final 1 × 1 projection (1,280 channels, 7 × 7, one cell covers 32 × 32 pixels). Each tapped map F is refined by CBAM \[8\], which applies channel attention M\_c and then spatial attention M\_s, where σ is the sigmoid, MLP a shared two-layer perceptron with reduction ratio 16, and f^{7×7} a 7 × 7 convolution:

```latex
M_c(F)=\sigma\big(\mathrm{MLP}(\mathrm{AvgPool}(F))+\mathrm{MLP}(\mathrm{MaxPool}(F))\big) \qquad (4)
```

```latex
M_s(F')=\sigma\big(f^{7\times7}([\mathrm{AvgPool}_c(F');\mathrm{MaxPool}_c(F')])\big),\quad F'=M_c\otimes F,\; F''=M_s\otimes F' \qquad (5)
```

Global average pooling dilutes small, strong lesion activations, so each refined map is pooled by generalised-mean (GeM) pooling \[26\] with a learnable exponent p initialised to 3, where Ω is the set of spatial positions:

```latex
d_k=\Big(\frac{1}{|\Omega|}\sum_{(i,j)\in\Omega}x_{k,i,j}^{\,p}\Big)^{1/p} \qquad (6)
```

The three descriptors (64, 160 and 1,280 values) are each layer-normalised so that the small fine-scale vectors are not dominated by the head. During training, scale-dropout multiplies each descriptor by a mask m\_s drawn from Bernoulli(0.9), keeping at least one scale per sample, which forces redundancy across scales. The 1,504-dimensional fused vector passes through dropout (0.3) and a linear layer:

```latex
z=[\,m_1\,\mathrm{LN}(d^{(1)});\;m_2\,\mathrm{LN}(d^{(2)});\;m_3\,\mathrm{LN}(d^{(3)})\,],\qquad \hat{y}=W\,\mathrm{Dropout}_{0.3}(z)+b \qquad (7)
```

&#91;embedded content: Fig. 2. EfficientNetV2-MSAF architecture\]

**Fig. 2.** EfficientNetV2-MSAF architecture. Three backbone depths are each refined by CBAM, pooled by GeM and layer-normalised, then concatenated with scale-dropout before a single linear classifier.

The head adds 220,841 parameters (+1.09%, 20.45 M in total) and leaves the backbone cost unchanged at 2.85 GMACs. Two controls isolate its effect: the stock EfficientNetV2-S head (baseline) and a single CBAM block on the final 1,280-channel map (CBAM variant).

### D. Model Training and Implementation

All five models (baseline, CBAM, MSAF, baseline with field augmentation, MSAF with field augmentation) share one recipe: 8 epochs, batch size 32, AdamW \[27\] with learning rate 10⁻³ and weight decay 10⁻⁴, a one-cycle schedule \[28\], automatic mixed precision and seed 42. The loss is cross-entropy with label smoothing \[29\], ε = 0.1, over K = 38 classes, where y is the one-hot label and ŷ the softmax output:

```latex
\mathcal{L}=-\sum_{k=1}^{K}\Big[(1-\varepsilon)\,y_k+\frac{\varepsilon}{K}\Big]\log\hat{y}_k \qquad (8)
```

The checkpoint with the best validation accuracy is kept. After training, a single temperature T is fitted on the validation set by minimising negative log-likelihood, and calibrated probabilities are computed from the logits z as in Eq. (9). Training used PyTorch and torchvision on an NVIDIA RTX 3050 laptop GPU with 4 GB of memory and took 37.8 min (baseline), 35.8 min (CBAM) and 48.7 min (MSAF).

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

The deployed application uses the EfficientNetV2-S checkpoint, because standard Grad-CAM produces noisy maps on MSAF: its per-scale layer normalisation cancels much of the averaged gradient weighting. The severity index is a heuristic based on explanation maps, not a laboratory measurement.

## IV. Results and Discussion

### A. Experimental Setup

All results are measured on the 8,889-image leaf-disjoint test set under seven conditions: clean images and six fixed-severity corruptions (Gaussian blur, motion blur, sensor noise, low light, JPEG compression at quality 10 and overexposure) in the style of \[10\]. Reported metrics are accuracy, macro precision, recall and F1, mean corrupted accuracy (mCA, the mean over the six corruptions), expected calibration error (ECE, 15 bins) before and after temperature scaling, and selective prediction \[31\] on the pooled corrupted images: area under the risk–coverage curve (AURC, lower is better), the AUROC of confidence for detecting errors, and accuracy at 90% coverage. Paired differences use exact McNemar tests \[32\] and 95% bootstrap confidence intervals. Latency is the mean single-image time on the RTX 3050 GPU and on a 4-thread CPU. Hardware and software are as in Section III-D.

### B. Quantitative Results

Table IV reports the main results. Clean accuracy lies between 99.51% and 99.62% for all five models, and no pairwise clean difference is significant (baseline vs. MSAF, p = 0.143; baseline vs. CBAM, p = 0.164; the two field-augmented models, p = 0.86). Clean accuracy therefore cannot separate the architectures on this benchmark.

**TABLE IV. Main results on the leaf-disjoint test set (8,889 images)**

| Model | Params (M) | Clean acc. (%) | Macro-F1 (%) | mCA (%) | ECE raw (%) | ECE after TS (%) | Corrupted ECE after TS (%) | AURC (%) | Error-detection AUROC (%) | Field photos |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EfficientNetV2-S (baseline) | 20.23 | 99.62 | 99.61 | 82.20 | 10.57 | 0.17 | 12.23 | 5.21 | 85.49 | 6/8 |
| + CBAM | 20.43 | 99.51 | 99.51 | 83.08 | 10.17 | 0.29 | 11.65 | 5.16 | 85.29 | 8/8 |
| EfficientNetV2-MSAF | 20.45 | 99.51 | 99.51 | 82.99 | **5.14** | 0.29 | 10.83 | 4.16 | 87.27 | 8/8 |
| Baseline + field aug. | 20.23 | 99.58 | 99.57 | **95.67** | 10.56 | 0.19 | **2.49** | **0.45** | 93.82 | 6/8 |
| MSAF + field aug. (proposed system) | 20.45 | 99.56 | 99.55 | 94.84 | 5.44 | 0.21 | 2.77 | 0.50 | **93.98** | 8/8 |

**Calibration.** The raw ECE of MSAF is 5.14% against 10.57% for the baseline, a difference of −5.43 points (95% CI −5.55 to −5.26). The single-scale CBAM variant lowers it by only 0.40 points, so the improvement comes from the multi-scale head rather than from attention alone. Temperature scaling reduces clean ECE below 0.3% for every model, but it fits clean validation data: for the models trained without field augmentation it worsens corrupted-image ECE (baseline 8.81% raw to 12.23% scaled). Only the field-augmented models transfer the calibration to corrupted images (2.49% and 2.77%).

**Robustness.** Without field augmentation, MSAF raises mCA by 0.79 points over the baseline (95% CI 0.48 to 1.10). The effect is condition-dependent: MSAF is better under sensor noise (85.43% vs. 80.64%, p < 10⁻³⁷) and low light (94.35% vs. 90.04%, p < 10⁻⁴³), but worse under motion blur (50.11% vs. 54.48%, p < 10⁻¹⁸). Field augmentation dominates: it lifts mCA by about 12–13 points, and motion blur, never seen in training, rises to 86.32% (baseline) and 81.85% (MSAF). Under the same augmentation, MSAF trails the baseline by 0.83 points of mCA (95% CI −1.01 to −0.64), mainly because of motion blur. Fig. 3 shows accuracy under each condition.

&#91;embedded content: Fig. 3. Source: results/paper/metrics.json · 5 models × 7 conditions\]

**Fig. 3.** Test accuracy of the five models under clean and six corrupted conditions. Blue markers (field augmentation) sit far right of grey markers under blur and noise; the head type changes the result mainly under motion blur, sensor noise and low light.

**Selective prediction.** Without field augmentation, MSAF lowers AURC from 5.21% to 4.16% (20%) and raises the error-detection AUROC from 85.49% to 87.27%, so its confidence ranks correct and incorrect predictions better. With field augmentation, both models reach AURC of about 0.5% and accuracy at 90% coverage of 98.5–99.0%.

**Efficiency.** Table V shows that the MSAF head leaves the multiply–accumulate count unchanged and adds 4.1 ms of GPU latency and 9.8 ms of CPU latency per image, which remains acceptable for interactive use.

**TABLE V. Computational cost (224 × 224 input, batch 1)**

| Model | Params (M) | GMACs | GPU latency (ms) | CPU latency, 4 threads (ms) | Training time, 8 epochs (min) |
| --- | --- | --- | --- | --- | --- |
| EfficientNetV2-S | 20.23 | 2.85 | 14.63 | 56.0 | 37.8 |
| + CBAM | 20.43 | 2.85 | 15.02 | 58.0 | 35.8 |
| EfficientNetV2-MSAF | 20.45 | 2.85 | 18.68 | 65.8 | 48.7 |

**Errors and gatekeeper.** The most frequent clean-image error in every model is corn Cercospora (gray) leaf spot predicted as northern leaf blight (9–15 test images); these are the two lowest per-class F1 scores of the baseline (97.07% and 97.64%). In a separate test of six non-leaf images, the gatekeeper rejected five (a text document, an app screenshot, a blank surface, a sky photograph and a four-leaf collage). Without it, the classifier labelled the text document as healthy corn with 81.2% confidence. The one image that passed, random noise, received 18.3% confidence and triggered the low-confidence warning.

### C. Graphical Results

Fig. 3 summarises robustness across conditions, and Fig. 4 shows Grad-CAM explanations from the deployed model on test leaves and field photographs.

&#91;image: Grad-CAM explanations from the deployed EfficientNetV2-S model\]

**Fig. 4.** Grad-CAM explanations from the deployed EfficientNetV2-S model (top: input; bottom: heatmap; below: prediction, calibrated confidence and severity). Columns marked \* are field photographs. Heat concentrates on lesions in the test leaves. The corn gray leaf spot field photo is misclassified as northern leaf blight at 46% confidence, the same confusion that dominates the test-set errors, and its low confidence would trigger the app's warning.

### D. Comparison With Existing Research

Table VI places these results beside published work. The comparison is indicative only: published models were not re-run, they use random file splits that may include augmented-copy leakage, and none reports corruption robustness or calibration on PlantVillage.

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

On clean images, the proposed system is on par with published models, not better, and its test set is stricter. Its distinguishing results are the measured robustness, the calibrated confidence and the rejection of non-leaf inputs, none of which the compared studies report. The 8/8 field result cannot be compared with the 31.4% or 68% figures, because those come from hundreds of PlantDoc-style images, whereas only eight photographs were available here.

### E. Critical Result Analysis

The calibration gain has a plausible cause. The baseline concentrates confidence near 0.90 even on clean images (mean confidence 89.08% at 99.62% accuracy), a sign of label-smoothing saturation, whereas fusing layer-normalised descriptors from three depths spreads the logits and yields lower NLL (0.069 vs. 0.123). The mixed robustness pattern is also consistent with the design: fine-scale features at 28 × 28 help when noise and darkness corrupt texture uniformly, but motion blur smears exactly those fine details, so a head that relies on them suffers more. Field augmentation, not architecture, is the main robustness lever, which agrees with the observation in \[6\] that clean accuracy hides large differences under corruption.

Several sources of error remain. Each model was trained once with one seed, so differences under about one point should not be over-read even when McNemar tests are significant, because those tests capture test-set variance but not training variance. The corruptions are synthetic and applied at one severity. The field set has eight images. Standard Grad-CAM is unreliable on MSAF, so the deployed explanations come from the baseline model. Practically, the results suggest that a deployed diagnostic tool should be trained with capture-style augmentation and should report calibrated confidence, and that the MSAF head is worth its small cost when trustworthy confidence matters more than motion-blur robustness.

## V. Conclusion and Future Work

This study addressed the gap between near-perfect laboratory accuracy and unreliable field performance in image-based crop disease diagnosis. A leaf-disjoint split of 87,867 PlantVillage images removed augmented-copy leakage that affected 67.5% of a random split's test images, and EfficientNetV2-MSAF fused CBAM-refined, GeM-pooled features from three backbone depths at a cost of 1.09% more parameters. Under a controlled five-model comparison, all models reached 99.51–99.62% clean accuracy with no significant difference, which shows that clean accuracy no longer discriminates between designs. The multi-scale head halved the raw calibration error (10.57% to 5.14%) and reduced selective risk under unseen corruptions by 20%, while field augmentation supplied most of the corruption robustness. Combined, the proposed system raised mean corrupted accuracy from 82.20% to 94.84% and classified all eight available field photographs correctly. Deployed with a leaf gatekeeper, Grad-CAM explanations, a severity estimate and treatment guidance, it offers farmers and extension workers a first diagnosis whose confidence can be interpreted. The main limitations are single-seed training, synthetic corruptions at one severity, a field set of only eight images, weaker motion-blur robustness of MSAF, and Grad-CAM maps that are unreliable on the multi-scale head. Future work will evaluate the system on PlantDoc and other field datasets, repeat training over several seeds, add motion-blur and multi-severity augmentation, develop an explanation method suited to multi-scale heads, and validate the severity estimate against expert scoring.

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
