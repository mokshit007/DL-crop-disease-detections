"""Make the six-page IEEE version (paper_ieee.md) from the full draft (paper_source.md).

Each entry replaces one paragraph, identified by its opening words, with a shorter version.
No number or claim is added; only wording is shortened and table columns are dropped.
"""
import re
import sys
from pathlib import Path

SHORT = {
    "**Abstract.**": "**Abstract.** Convolutional networks exceed 99% accuracy on the PlantVillage leaf disease benchmark, yet fail on photographs taken outside the laboratory. Three practices contribute: augmented copies of a leaf leak across the train–test split, single-scale classifier heads average away small lesions, and models are judged by clean accuracy alone. A leaf-grouped split of 87,867 images (14 crops, 38 classes) removes the leakage of a random split, in which 67.5% of test images had a copy in training or validation. On this split, EfficientNetV2-MSAF, a head that applies convolutional block attention, generalised-mean pooling and scale-dropout at three backbone depths (+1.09% parameters), is compared with EfficientNetV2-S and a single-scale attention variant, each with and without field augmentation, using macro-F1, six corruptions, calibration error, selective prediction and McNemar tests. All models reach 99.51–99.62% clean accuracy with no significant difference. MSAF halves the raw expected calibration error (10.57% to 5.14%) and lowers selective risk by 20%, while field augmentation supplies most corruption robustness. The combined system raises mean corrupted accuracy from 82.20% to 94.84% and is deployed with a leaf gatekeeper, Grad-CAM explanations and treatment guidance.",
    "Plant pathogens and pests": "Plant pathogens and pests remove an estimated 17–30% of the global harvest of major staple crops \\[1\\]. Plant pathologists are scarce in rural areas, so a first diagnosis from a smartphone photograph is a low-cost alternative. The open PlantVillage collection \\[2\\] made such systems practical, and CNNs trained on it exceeded 99% accuracy in 2016 \\[3\\].",
    "Laboratory accuracy on PlantVillage": "Laboratory accuracy on PlantVillage has saturated between 99% and 100%, while accuracy on other photographs remains far lower: 31.4% on images from other sources in \\[3\\], and 68% for a 2025 vision transformer transferred to the in-the-wild PlantDoc images \\[4\\], \\[5\\]. A tool that is confident and wrong in the field can lead to the wrong treatment.",
    "Three weaknesses recur": "Three weaknesses recur. The augmented PlantVillage release stores rotated and flipped copies of each leaf as separate files, so a random file split places copies of one leaf in both training and test sets. Most classifiers decide from the coarsest feature map, where a small lesion is averaged away by global pooling. Models are compared by clean accuracy alone, although robustness and the reliability of confidence decide whether a prediction can be trusted \\[6\\].",
    "This work treats the evaluation": "This work treats the evaluation protocol and the classifier head as one problem. Its objectives are to (i) remove augmented-copy leakage, (ii) design a lightweight head that preserves small-lesion evidence on an EfficientNetV2 backbone \\[7\\], (iii) evaluate robustness, calibration and selective risk alongside accuracy, and (iv) deploy the result in a usable application.",
    "Clean accuracy is already saturated": "Because clean accuracy is saturated, gains must be shown on other measures without overstating small differences; training must fit a 4 GB GPU, and labelled field photographs are scarce.",
    "1. A leaf-disjoint split": "1. A leaf-disjoint split of the 38-class augmented PlantVillage release, showing that 67.5% of a random split's test images had a training or validation sibling.",
    "2. EfficientNetV2-MSAF, a head": "2. EfficientNetV2-MSAF, a head applying CBAM \\[8\\], generalised-mean pooling and scale-dropout at three backbone depths for +1.09% parameters.",
    "3. A controlled five-model": "3. A five-model comparison covering macro-F1, six corruptions, calibration before and after temperature scaling \\[9\\], \\[10\\], selective prediction and significance tests.",
    "4. A deployed system": "4. A deployed system with a leaf gatekeeper, Grad-CAM, severity estimate and treatment guidance.",
    "Section II reviews recent work": "Sections II–V cover related work, method, results and conclusions.",
    "Research from 2022 to 2026": "Work from 2022 to 2026 has pursued lighter CNNs, hybrids that add self-attention or state-space blocks, and, recently, evaluation beyond clean accuracy. Of sixteen original studies selected, five are analysed below, six are compared in Table I, and the five closest to this work are examined in Section III-C.",
    "Zhu et al. \\[11\\]": "Zhu et al. \\[11\\] fused multi-scale convolution with self-attention at shallow and deep levels (MSCVT), reaching 99.86% on PlantVillage and 97.50% on an apple leaf set. Combining shallow and deep features helps small lesions, but robustness and confidence were not examined; this work keeps the multi-scale premise with a pure CNN and tests it under corruption.",
    "Guan et al. \\[12\\]": "Guan et al. \\[12\\] built the 13.3 MB Dise-Efficient on EfficientNetV2; it reached 99.80% on PlantVillage but 64.40% on the field-captured IP102 pest set. This 35-point gap shows that laboratory accuracy does not transfer to the field even with a strong backbone, which motivates the corruption and field tests used here.",
    "Gole et al. \\[13\\]": "Gole et al. \[13\] (TrIncNet, a ViT with inception blocks) gained 5.38 points over a plain ViT on PlantVillage but only 2.87 points on in-field maize images, without calibration or robustness tests.",
    "Meng et al. \\[14\\]": "Meng et al. \[14\] fused convolutional and transformer branches, reaching 99.71% on PlantVillage with 4.9 M parameters, but did not describe how augmented copies of a leaf are kept out of the test split.",
    "Zhang and Liu \\[15\\]": "Zhang and Liu \\[15\\] fused shallow, medium and deep features with adaptive channel attention in a Vision Mamba network on field-acquired PlantDoc images, reaching 92.67% accuracy, 5.33 points above its baseline, with paired t-tests; calibration was not measured.",
    "Three trends emerge.": "PlantVillage accuracy has converged at 99.4–99.9% \\[11\\], \\[12\\], \\[14\\], \\[16\\], \\[17\\], so clean gains no longer discriminate between designs. Multi-scale fusion and attention are standard for small lesions \\[11\\], \\[15\\], \\[20\\], but are applied inside the backbone or at one output scale. Every study that tested harder data observed a large drop \\[12\\], \\[13\\], \\[17\\], \\[21\\], yet only \\[6\\] measures robustness and calibration. None (i) controls augmented-copy leakage, (ii) fuses attention-refined features from several depths at an EfficientNetV2 head, and (iii) reports calibration, selective risk and robustness together. The closest studies \\[4\\], \\[6\\], \\[22\\]–\\[24\\] inform Section III.",
    "The study uses the augmented release": "The study uses the augmented PlantVillage release on Kaggle \\[25\\], derived from \\[2\\]: 87,867 RGB images of single detached leaves on uniform backgrounds, covering 14 crops and 38 classes (26 diseased, 12 healthy). Rotated, flipped and pixel-shifted copies of each photograph are stored as separate files with suffixes such as `_90deg` and `_flipTB`. Table II gives the split.",
    "The dataset has three limitations": "The images are laboratory captures of one leaf each, and no labelled field photographs are included, so eight field photographs of supported classes were collected as a qualitative check.",
    "**Leakage audit and leaf-grouped split.**": "**Leakage audit and leaf-grouped split.** Each file is mapped to its source leaf ℓ(f) by stripping the augmentation suffix. Under a random file split, 67.5% of test images had a sibling in training or validation, so all files sharing ℓ(f) are assigned to the same subset (80/10/10 over leaf groups, seed 42):",
    "During training, a one-copy-per-leaf": "A one-copy-per-leaf sampler draws one copy of each leaf per epoch, so leaves with many stored copies are not over-weighted.",
    "**Standard augmentation and normalisation.**": "**Standard augmentation.** Training uses a random resized crop to 224 × 224, horizontal and vertical flips and colour jitter (0.2 brightness, contrast and saturation; 0.1 hue); evaluation resizes to 256 and centre-crops 224. Images are normalised with ImageNet channel statistics μ\\_c, σ\\_c:",
    "**Field augmentation (optional).**": "**Field augmentation (optional).** Gaussian blur (kernel 9, σ ∈ \\[0.5, 3\\]) and the sensor noise of Eq. (3) are each applied to 30% of training images. Motion blur, JPEG, low light and overexposure are never used in training, so they measure generalisation to unseen degradations.",
    "Fig. 1 shows the complete workflow.": "Fig. 1 shows the workflow: development (leakage audit, split, training of five models, evaluation under seven conditions) and deployment (gatekeeper, classifier, temperature scaling, Grad-CAM, severity, treatment lookup). Table III summarises the five studies that shaped the design.",
    "**Supporting research.**": "",
    "| EfficientNetV2-S | 20.23 | 2.85": "| Baseline | 20.23 | 2.85 | 14.63 | 56.0 | 37.8 |",
    "| EfficientNetV2-MSAF | 20.45 | 2.85": "| MSAF | 20.45 | 2.85 | 18.68 | 65.8 | 48.7 |",
    "| Model | Params (M) | GMACs": "| Model | Params (M) | GMACs | GPU (ms) | CPU, 4 thr. (ms) | Train (min) |",
    "| Training | 70,146": "| Training | 70,146 | 79.8% | Weight updates |",
    "| Validation | 8,832": "| Validation | 8,832 | 10.1% | Checkpoint, temperature |",
    "The proposed head combines": "The head keeps the EfficientNetV2 backbone validated in \\[22\\], applies CBAM as in \\[23\\] but at three depths, and fuses shallow and deep features as \\[24\\] does for detection. It targets the field gap of \\[4\\] with a 0.22 M-parameter head rather than an expert ensemble, and extends the evaluation view of \\[6\\] with temperature scaling, selective prediction and significance tests.",
    "**Multi-scale attention fusion (MSAF).**": "**Multi-scale attention fusion (MSAF).** As Fig. 2 shows, the ImageNet-pretrained EfficientNetV2-S \\[7\\] is tapped at stage 3 (64 channels, 28 × 28), stage 5 (160 channels, 14 × 14) and the final 1 × 1 projection (1,280 channels, 7 × 7). Each map F is refined by CBAM \\[8\\]: channel attention M\\_c (shared MLP, reduction 16) gives F′ = M\\_c ⊗ F, spatial attention M\\_s (7 × 7 convolution) is applied to F′, and the block returns F + M\\_s ⊗ F′ (residual):",
    "Global average pooling dilutes": "Global average pooling dilutes small, strong lesion activations, so each refined map is pooled by GeM \\[26\\] with learnable p (initialised to 3) over spatial positions Ω:",
    "The three descriptors (64, 160": "The three descriptors are layer-normalised so that the small fine-scale vectors are not dominated. During training, scale-dropout multiplies each by m\\_s ~ Bernoulli(0.9), keeping at least one scale. The fused 1,504-d vector z of Eq. (7) passes through dropout (0.3) and a linear layer, ŷ = W·Dropout(z) + b:",
    "The head adds 220,841 parameters": "The head adds 220,841 parameters (+1.09%, 20.45 M total) at an unchanged 2.85 GMACs. Two controls isolate its effect: the stock head (baseline) and one CBAM block on the 1,280-channel map (CBAM variant).",
    "All five models (baseline, CBAM": "All five models (baseline, CBAM, MSAF, and baseline and MSAF with field augmentation) share one recipe: 8 epochs, batch 32, AdamW \\[27\\] (learning rate 10⁻³, weight decay 10⁻⁴), a one-cycle schedule \\[28\\], mixed precision, seed 42 and cross-entropy with label smoothing \\[29\\] ε = 0.1 over K = 38 classes:",
    "The checkpoint with the best validation": "The best-validation checkpoint is kept, and a temperature T is fitted on the validation set by minimising NLL (Eq. 9). Training on an NVIDIA RTX 3050 (4 GB) took 37.8, 35.8 and 48.7 min for the baseline, CBAM and MSAF models.",
    "The deployed application uses the EfficientNetV2-S": "The application uses the EfficientNetV2-S checkpoint, because standard Grad-CAM gives noisy maps on MSAF, whose per-scale layer normalisation cancels much of the gradient weighting. The severity index is a heuristic, not a laboratory measurement.",
    "All results are measured on the 8,889": "All results use the 8,889-image leaf-disjoint test set under clean images and six fixed-severity corruptions in the style of \\[10\\] (Gaussian blur, motion blur, sensor noise, low light, JPEG quality 10, overexposure). Metrics are accuracy, macro-F1, mean corrupted accuracy (mCA), expected calibration error (ECE, 15 bins) before and after temperature scaling (TS), and selective prediction \\[31\\] on pooled corrupted images: area under the risk–coverage curve (AURC), error-detection AUROC and accuracy at 90% coverage. Paired differences use exact McNemar tests \\[32\\] and 95% bootstrap intervals. Latency is per image on the RTX 3050 and a 4-thread CPU.",
    "Table IV reports the main results.": "Table IV reports the main results. Clean accuracy spans 99.51–99.62% and no pairwise difference is significant (baseline vs. MSAF p = 0.143; vs. CBAM p = 0.164; field-augmented pair p = 0.86), so clean accuracy cannot separate the architectures.",
    "**Calibration.**": "**Calibration.** MSAF's raw ECE is 5.14% against 10.57% for the baseline (−5.43 points, 95% CI −5.55 to −5.26); single-scale CBAM lowers it by only 0.40 points, so the gain comes from the multi-scale head. TS brings clean ECE below 0.3% for all models, but without field augmentation it worsens corrupted-image ECE (baseline 8.81% to 12.23%); only the field-augmented models keep it low (2.49% and 2.77%).",
    "**Robustness.**": "**Robustness.** Without field augmentation, MSAF raises mCA by 0.79 points (95% CI 0.48 to 1.10): it is better under sensor noise (85.43% vs. 80.64%, p < 10⁻³⁷) and low light (94.35% vs. 90.04%, p < 10⁻⁴³) but worse under motion blur (50.11% vs. 54.48%, p < 10⁻¹⁸). Field augmentation lifts mCA by 12–13 points, and unseen motion blur rises to 86.32% (baseline) and 81.85% (MSAF); with it, MSAF trails the baseline by 0.83 points (95% CI −1.01 to −0.64), mainly on motion blur (Fig. 3).",
    "**Selective prediction.**": "**Selective prediction.** Without field augmentation, MSAF lowers AURC from 5.21% to 4.16% and raises error-detection AUROC from 85.49% to 87.27%. With field augmentation, both models reach AURC of about 0.5% and 98.5–99.0% accuracy at 90% coverage.",
    "**Efficiency.**": "**Efficiency.** MSAF adds 4.1 ms GPU and 9.8 ms CPU latency per image at unchanged GMACs (Table V).",
    "**Errors and gatekeeper.**": "**Errors and gatekeeper.** The most frequent clean error is corn gray leaf spot predicted as northern leaf blight (9–15 images), the baseline's two lowest per-class F1 scores (97.07%, 97.64%). The gatekeeper rejected five of six non-leaf images; without it, a text document was labelled healthy corn at 81.2%. The one that passed, random noise, received 18.3% confidence and triggered the warning.",
    "Fig. 3 summarises robustness": "Fig. 4 shows Grad-CAM explanations from the deployed model on test leaves and field photographs.",
    "Table VI places these results": "Table VI is indicative only: published models were not re-run, use random splits that may leak augmented copies, and report no robustness or calibration on PlantVillage.",
    "On clean images, the proposed system": "On clean images the system is on par with published models on a stricter test set; its distinguishing results are measured robustness, calibrated confidence and non-leaf rejection. The 8/8 field result is not comparable with the 31.4% or 68% figures, which come from hundreds of images.",
    "The calibration gain has a plausible": "The baseline concentrates confidence near 0.90 even on clean images (mean 89.08% at 99.62% accuracy), a sign of label-smoothing saturation; fusing layer-normalised descriptors from three depths spreads the logits and lowers NLL (0.069 vs. 0.123). Fine 28 × 28 features help when noise and darkness corrupt texture uniformly, but motion blur smears exactly those details. As in \[6\], robustness depends more on training data than on architecture.",
    "Several sources of error remain.": "Each model was trained once with one seed, so differences under about one point should not be over-read even when McNemar tests are significant. In practice, a deployed tool should be trained with capture-style augmentation and report calibrated confidence, and the MSAF head is worth its cost when trustworthy confidence matters more than motion-blur robustness.",
    "This study addressed the gap": "This study addressed the gap between near-perfect laboratory accuracy and unreliable field performance in crop disease diagnosis. A leaf-disjoint split of 87,867 PlantVillage images removed augmented-copy leakage that affected 67.5% of a random split's test images, and EfficientNetV2-MSAF fused attention-refined features from three backbone depths for 1.09% more parameters. All five models reached 99.51–99.62% clean accuracy with no significant difference, while the multi-scale head halved raw calibration error (10.57% to 5.14%) and reduced selective risk under unseen corruptions by 20%. Field augmentation supplied most robustness, and the deployed system, with a leaf gatekeeper, Grad-CAM and treatment guidance, raised mean corrupted accuracy from 82.20% to 94.84% and classified all eight field photographs correctly. Its main limitations are single-seed training, synthetic corruptions at one severity and only eight field images. Future work will evaluate on PlantDoc, repeat training over several seeds, add motion-blur and multi-severity augmentation, and validate severity against expert scoring.",
}

# Table columns to drop (by header name) to fit the page budget.
DROP_COLS = {"I": ["Research Title"], "III": ["Dataset"]}


def condense(src, dst):
    lines = Path(src).read_text(encoding="utf8").splitlines()
    out, used, table = [], set(), None
    for l in lines:
        m = re.match(r"\*\*TABLE ([IVX]+)\.", l)
        if m:
            table = m.group(1)
        if l.startswith("|") and table in DROP_COLS:
            cells = re.split(r"(?<!\\)\|", l)[1:-1]
            if l.startswith("| No.") or l.startswith("| Ref."):
                drop_idx = [i for i, c in enumerate(cells) if c.strip() in DROP_COLS[table]]
            cells = [c for i, c in enumerate(cells) if i not in drop_idx]
            out.append("|" + "|".join(cells) + "|")
            continue
        key = next((k for k in SHORT if l.startswith(k)), None)
        if key:
            used.add(key)
            out.append(SHORT[key])
        else:
            out.append(l)
    missing = set(SHORT) - used
    assert not missing, missing
    Path(dst).write_text("\n".join(out) + "\n", encoding="utf8")
    print("condensed", len(used), "paragraphs")


if __name__ == "__main__":
    condense(sys.argv[1], sys.argv[2])
