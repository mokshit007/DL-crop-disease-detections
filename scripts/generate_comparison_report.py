"""
Builds Advantages_vs_Published_Models.pdf: what CropSense (EfficientNetV2-MSAF) offers over
published, online-available plant-disease models.

Our numbers are read from results/ (ablation_results.json, test_metrics.json, gatekeeper_test.json).
Published numbers are quoted from the cited papers (see REFERENCES) and are NOT re-measured here.
Run from the project root:  python scripts/generate_comparison_report.py
"""
import os
import sys
import json
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_improvement_report import (P, bullets, callout, data_table, figure, ss, INK, GREEN, GREEN_T, BLUE_T, BLUE,
                                         AMBER, AMBER_T, RED, RED_T, MUTED, RULE)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Spacer, KeepTogether, NextPageTemplate, PageBreak

OUT = 'Advantages_vs_Published_Models.pdf'

# Published results quoted from the papers' abstracts (see REFERENCES); not re-measured here.
PUBLISHED = [
    ('Mohanty et al., 2016', 'AlexNet / GoogLeNet', 'PlantVillage, 38 classes, 54,306 images', '99.35%',
     '31.4% on images from other online sources', '[1]'),
    ('Ferentinos, 2018', 'VGG and others', '87,848 images, 58 classes', '99.53%', 'Not reported', '[2]'),
    ('Too et al., 2019', 'DenseNet-121 (best of VGG16, Inception-V4, ResNet-50/101/152)', 'PlantVillage, 38 classes', '99.75%', 'Not reported', '[3]'),
    ('Atila et al., 2021', 'EfficientNet-B4 / B5', 'PlantVillage (55,448 / 61,486 images)', '99.91% / 99.97%', 'Not reported', '[4]'),
    ('Andrew et al., 2022', 'DenseNet-121', 'PlantVillage', '99.81%', 'Not reported', '[5]'),
]

# Approximate parameter counts of the reference architectures (standard ImageNet versions)
ARCH_PARAMS = [
    ('VGG-16', 138.4), ('AlexNet', 61.1), ('Inception-V4', 42.7), ('EfficientNet-B5', 30.4), ('ResNet-50', 25.6),
    ('EfficientNet-B4', 19.3), ('DenseNet-121', 8.0), ('GoogLeNet', 6.8),
]

REFERENCES = [
    '[1] Mohanty, S. P., Hughes, D. P. &amp; Salathé, M. (2016). Using Deep Learning for Image-Based Plant Disease Detection. <i>Frontiers in Plant Science</i> 7:1419. arxiv.org/abs/1604.03169',
    '[2] Ferentinos, K. P. (2018). Deep learning models for plant disease detection and diagnosis. <i>Computers and Electronics in Agriculture</i> 145, 311–318.',
    '[3] Too, E. C., Li, Y., Njuki, S. &amp; Liu, Y. (2019). A comparative study of fine-tuning deep learning models for plant disease identification. <i>Computers and Electronics in Agriculture</i> 161, 272–279.',
    '[4] Atila, Ü., Uçar, M., Akyol, K. &amp; Uçar, E. (2021). Plant leaf disease classification using EfficientNet deep learning model. <i>Ecological Informatics</i> 61, 101182.',
    '[5] Andrew, J., Eunice, J., Popescu, D. E., Chowdary, M. K. &amp; Hemanth, J. (2022). Deep Learning-Based Leaf Disease Detection in Crops Using Images for Agricultural Applications. <i>Agronomy</i> 12(10), 2395.',
    '[6] Noyan, M. A. (2022). Uncovering bias in the PlantVillage dataset. arxiv.org/abs/2206.04374',
    '[7] Singh, D. et al. (2020). PlantDoc: A Dataset for Visual Plant Disease Detection. <i>CoDS-COMAD</i>. arxiv.org/abs/1911.10317',
    '[8] Hendrycks, D. &amp; Dietterich, T. (2019). Benchmarking Neural Network Robustness to Common Corruptions and Perturbations. <i>ICLR</i>.',
    '[9] Guo, C., Pleiss, G., Sun, Y. &amp; Weinberger, K. Q. (2017). On Calibration of Modern Neural Networks. <i>ICML</i>.',
]

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont('Calibri', 8.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 1.2 * cm, 'CropSense AI  |  Advantages over published plant-disease models')
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f'Page {doc.page}')
    canvas.setStrokeColor(RULE)
    canvas.line(2 * cm, 1.55 * cm, A4[0] - 2 * cm, 1.55 * cm)
    canvas.restoreState()

def on_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(INK)
    canvas.rect(0, A4[1] - 7.2 * cm, A4[0], 7.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(GREEN)
    canvas.rect(2 * cm, A4[1] - 2.3 * cm, 6.4 * cm, 0.6 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Calibri-Bold', 9)
    canvas.drawString(2.25 * cm, A4[1] - 2.1 * cm, 'COMPARISON WITH PUBLISHED MODELS')
    canvas.setFont('Calibri-Bold', 25)
    canvas.drawString(2 * cm, A4[1] - 3.75 * cm, 'Advantages over Published Models')
    canvas.setFont('Calibri', 14)
    canvas.setFillColor(colors.HexColor('#CBD5E1'))
    canvas.drawString(2 * cm, A4[1] - 4.65 * cm, 'From lab accuracy to a field-ready, trustworthy diagnosis system')
    canvas.setFont('Calibri', 10.5)
    canvas.setFillColor(colors.HexColor('#94A3B8'))
    canvas.drawString(2 * cm, A4[1] - 5.6 * cm, f'CropSense AI project  |  Technical report  |  {date.today():%d %B %Y}')
    canvas.restoreState()
    on_page(canvas, doc)

def build():
    A = json.load(open('results/ablation_results.json'))
    runs = A['runs']
    base, msaf, mf = runs['baseline'], runs['msaf'], runs.get('msaf_field')
    if not mf:
        raise SystemExit('results/ablation_results.json has no msaf_field run; run run_ablation.ps1 first.')
    leak = json.load(open('results/test_metrics.json'))
    gate = json.load(open('results/gatekeeper_test.json'))['tests']
    fcount = lambda r: round(r['field_acc'] * r['field_photos'] / 100)
    n_test = A['test_images']
    n_rejected = sum(not t['pipeline_valid'] for t in gate)
    doc_row = next(t for t in gate if t['image'] == 'Text document')
    clean_name = lambda c: c.replace('___', ': ').replace('_', ' ').replace(',', '')

    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2.2 * cm,
                          title='CropSense: Advantages over Published Plant-Disease Models', author='CropSense AI project',
                          subject='Advantages of CropSense / EfficientNetV2-MSAF over published plant-disease models')
    doc.addPageTemplates([
        PageTemplate(id='cover', frames=Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - 6.2 * cm), onPage=on_cover),
        PageTemplate(id='normal', frames=Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height), onPage=on_page),
    ])
    W = doc.width
    story = [NextPageTemplate('normal')]

    # ------------------------------------------------------------------ 1. Summary
    story.append(P('1. Summary', 'h1'))
    story.append(P('<b>Question.</b> Does our model have any advantage over existing plant-disease models available online and in the literature?'))
    story.append(callout(
        '<b>Answer: yes, one major difference and several supporting ones.</b> Published PlantVillage models are evaluated almost exclusively '
        'on <b>clean laboratory images</b> and report 99.35–99.97% accuracy there. Our model matches that level '
        f'({mf["clean_acc"]:.2f}%) under a stricter, leakage-free protocol, and in addition is <b>measured and engineered for the field</b>: '
        'robust to blur, noise and poor light, with calibrated confidence and a filter that refuses to diagnose non-leaf images. '
        'The cited papers report none of these properties.'))
    story.append(Spacer(1, 8))
    story.append(P('<b>The major difference in one sentence:</b> published models answer "which of 38 classes is this lab photo?"; CropSense answers '
                   '"is this a single real leaf, what disease does it have, how sure are we, and where is the evidence?", and it stays accurate when '
                   'the photo is blurred, noisy or dark.'))
    adv = [
        ['Criterion', 'Published models (as reported)', 'CropSense: EfficientNetV2-MSAF + field aug.'],
        ['Clean accuracy', '99.35–99.97% (random file splits)', f'{mf["clean_acc"]:.2f}% on a leaf-disjoint split: on par'],
        ['Test-set leakage controlled', 'Not described in the papers', f'Yes: every copy of a leaf in one split ({leak["leaked_fraction_pct"]:.1f}% of a random split leaks)'],
        ['Robustness to field corruptions', 'Not reported', f'{mf["mCA"]:.1f}% mean over 6 corruptions; {mf["corruptions"]["Motion blur"]:.1f}% under unseen motion blur'],
        ['Calibrated confidence (ECE)', 'Not reported', f'{mf["ece"]:.1f}% (a stock EfficientNetV2-S trained identically: {base["ece"]:.1f}%)'],
        ['Rejects non-leaf / multi-leaf images', 'No: always outputs a class', f'Yes: {n_rejected} of {len(gate)} non-leaf test images rejected'],
        ['Real field photos', 'Mohanty et al.: 31.4% on other-source images', f'{fcount(mf)}/{mf["field_photos"]} correct (small sample)'],
        ['Explanation and action', 'Class label', 'Grad-CAM heatmap, severity estimate, treatment plan, PDF report'],
    ]
    story.append(data_table(adv, [4.2 * cm, 5.4 * cm, 7.4 * cm]))
    story.append(P('Published figures are quoted from the papers\' abstracts and were not re-measured by us; "not reported" means the cited abstracts '
                   'give no such result. Section 9 lists what this comparison cannot claim.', 'caption'))

    # ------------------------------------------------------------------ 2. What published models report
    story.append(P('2. What published models report', 'h1'))
    story.append(P('The table below collects widely cited results for PlantVillage-style data, from the 2016 paper that introduced deep learning on '
                   'PlantVillage to recent EfficientNet and DenseNet studies.'))
    rows = [['Study', 'Model', 'Data', 'Reported accuracy', 'Real-world test', 'Ref.']] + [list(r) for r in PUBLISHED]
    story.append(data_table(rows, [2.9 * cm, 3.6 * cm, 3.4 * cm, 2.2 * cm, 3.7 * cm, 1.2 * cm]))
    story.append(Spacer(1, 6))
    story.append(P('Two observations from the literature matter for everything that follows:'))
    story += bullets([
        '<b>Clean accuracy is saturated.</b> Every study is between 99.35% and 99.97%. A new model cannot show a meaningful gain there, '
        'so a real improvement has to be shown on other criteria.',
        '<b>Lab accuracy does not transfer to the field.</b> The only study in the table that tested on outside images, Mohanty et al. [1], '
        'reports a drop from 99.35% to <b>31.4%</b>. Noyan [6] later showed that a model using only <b>8 background pixels</b> of PlantVillage '
        'images reaches 49.0% accuracy (chance: 2.6%), so part of the high lab accuracy comes from background bias, not from the disease.',
    ])

    # ------------------------------------------------------------------ 3. Advantage 1: honest evaluation
    story.append(P('3. Advantage 1: a leakage-free evaluation', 'h1'))
    story.append(P('The Kaggle dataset used by many online implementations ships several rotated / flipped copies of each photo. If files are split at random, '
                   'copies of the same physical leaf appear in both training and test sets, so the test partly measures memorisation.'))
    story += bullets([
        f'Our audit of a random file split: <b>{leak["leaked_fraction_pct"]:.1f}%</b> of test images had a rotated or flipped sibling in train/val.',
        'Our evaluation groups every copy of a leaf into one split (80/10/10 by leaf). The papers in Section 2 do not describe such grouping in their abstracts, '
        'so we cannot say whether their numbers are affected; ours are not.',
        f'Under this stricter protocol our model still reaches <b>{mf["clean_acc"]:.2f}%</b> on {n_test:,} test images, the same level as the published results.',
    ])

    # ------------------------------------------------------------------ 4. Advantage 2: robustness
    story.append(P('4. Advantage 2: measured robustness to field conditions (the major difference)', 'h1'))
    story.append(P('Phone photos taken in a field are blurred by hand shake, noisy at dusk, dark in shade and compressed by messaging apps. '
                   'We test six such corruptions, following the ImageNet-C methodology [8]. Four of them (motion blur, low light, JPEG, overexposure) '
                   'were <b>never used in training</b>, so they measure genuine generalisation.'))
    crow = [['Condition', 'Stock EfficientNetV2-S*', 'CropSense (MSAF + field aug.)', 'Seen in training?']]
    seen = ('Gaussian blur', 'Sensor noise')
    for c in base['corruptions']:
        crow.append([c, f'{base["corruptions"][c]:.1f}%', f'{mf["corruptions"][c]:.1f}%', 'Similar' if c in seen else 'No'])
    crow.append(['Mean (mCA)', f'{base["mCA"]:.1f}%', f'{mf["mCA"]:.1f}%', ''])
    bold = {(i, 2) for i in range(1, len(crow)) if crow[i][2] > crow[i][1]}
    story.append(KeepTogether([
        data_table(crow, [4.2 * cm, 4.2 * cm, 4.9 * cm, 3.7 * cm], highlight_rows={len(crow) - 1}, bold_cells=bold),
        P('*A standard EfficientNetV2-S, the same family as the EfficientNet models in [4], trained by us under the identical recipe and split. '
          'It stands in for a typical published model, because the cited papers give no corruption results.', 'caption')]))
    story += bullets([
        f'Mean accuracy under corruption rises from <b>{base["mCA"]:.1f}% to {mf["mCA"]:.1f}%</b>; motion blur, never trained on, from '
        f'{base["corruptions"]["Motion blur"]:.1f}% to {mf["corruptions"]["Motion blur"]:.1f}%.',
        'This is the property the literature identifies as missing: lab accuracy that collapses outside the lab [1].',
    ])
    if os.path.exists('results/field_aug_robustness.png'):
        story.append(figure('results/field_aug_robustness.png', W, 'Figure 1. Accuracy per condition. The stock model collapses under motion blur and noise; '
                            'the field-trained models do not.'))

    # ------------------------------------------------------------------ 5. Advantage 3: calibration
    story.append(P('5. Advantage 3: confidence you can trust', 'h1'))
    story.append(P('A diagnosis tool shows its confidence to farmers, and our app warns below 75%. That only works if a reported 90% is right about 90% of the time. '
                   'This is measured by the Expected Calibration Error (ECE) [9]: lower is better.'))
    story.append(data_table([
        ['Model (same split and recipe)', 'ECE', 'Field photos correct', 'Mean true-class confidence on field photos'],
        ['Stock EfficientNetV2-S', f'{base["ece"]:.2f}%', f'{fcount(base)}/8', f'{base["field_true_class_conf"]:.0f}%'],
        ['EfficientNetV2-MSAF', f'{msaf["ece"]:.2f}%', f'{fcount(msaf)}/8', f'{msaf["field_true_class_conf"]:.0f}%'],
        ['EfficientNetV2-MSAF + field aug. (CropSense)', f'{mf["ece"]:.2f}%', f'{fcount(mf)}/8', f'{mf["field_true_class_conf"]:.0f}%'],
    ], [6.2 * cm, 2.2 * cm, 3.4 * cm, 5.2 * cm], highlight_rows={3}))
    story.append(Spacer(1, 4))
    story.append(P(f'The MSAF architecture roughly <b>halves the calibration error</b> of a standard EfficientNetV2-S. None of the papers in Section 2 report calibration.'))

    # ------------------------------------------------------------------ 6. Advantage 4: open-world
    story.append(P('6. Advantage 4: it refuses to diagnose what is not a leaf', 'h1'))
    story.append(P('A standard classifier is "closed-world": whatever it receives, it outputs one of its 38 classes. CropSense first runs a leaf gatekeeper '
                   '(plant-pigment colour analysis plus contour analysis) and rejects non-plant or multi-leaf photos.'))
    grow = [['Input image', 'Bare classifier (what a closed-world model says)', 'CropSense pipeline']]
    for t in gate:
        verdict = ('Rejected: not a plant' if t['pipeline_code'] == 'non_plant' else
                   'Rejected: multiple leaves' if t['pipeline_code'] == 'multiple_leaves' else
                   f"Passed, {t['pipeline_confidence']:.0f}% confidence -> low-confidence warning")
        grow.append([t['image'], f"{clean_name(t['bare_classifier_prediction'])} ({t['bare_classifier_confidence']:.0f}%)", verdict])
    gbold = {(i, 2) for i, t in enumerate(gate, start=1) if not t['pipeline_valid']}
    story.append(KeepTogether([P('We tested it on six non-leaf images:'), data_table(grow, [3.6 * cm, 6.9 * cm, 6.5 * cm], bold_cells=gbold)]))
    story.append(Spacer(1, 4))
    story.append(P(f'Without the gatekeeper the classifier calls a <b>text document "{clean_name(doc_row["bare_classifier_prediction"])}" with '
                   f'{doc_row["bare_classifier_confidence"]:.0f}% confidence</b>. CropSense rejects {n_rejected} of {len(gate)}; the remaining one (random noise) '
                   'passes the colour filter but gets a low confidence that triggers the app\'s warning. The test images are synthetic or composed by us, so this is '
                   'a functional check rather than a benchmark (<font name="Consolas">scripts/gatekeeper_test.py</font>).'))

    # ------------------------------------------------------------------ 7. Advantage 5: explanation and action
    story.append(P('7. Advantage 5: explanation and action, not just a label', 'h1'))
    feat = [
        ['Output', 'Typical published model', 'CropSense'],
        ['Disease class', 'Yes', 'Yes, top-3 with confidence'],
        ['Visual evidence', 'No', 'Grad-CAM heatmap over the leaf'],
        ['How badly is the leaf affected?', 'No', 'Severity estimate (share of leaf flagged, 4 stages)'],
        ['What should the farmer do?', 'No', 'Pathogen, symptoms, organic and chemical control, prevention'],
        ['Shareable record', 'No', 'One-click PDF diagnostic report'],
        ['Field input', 'Offline images', 'Upload or live phone / webcam camera'],
    ]
    story.append(data_table(feat, [5.0 * cm, 4.2 * cm, 7.8 * cm]))
    story.append(P('Severity is a heuristic estimate from Grad-CAM, not a laboratory measurement; the app labels it as such.', 'caption'))

    # ------------------------------------------------------------------ 8. Efficiency
    story.append(P('8. Model size compared with published architectures', 'h1'))
    prow = [['Architecture', 'Parameters (approx.)', 'Used in']]
    used = {'VGG-16': '[2], [3]', 'AlexNet': '[1]', 'Inception-V4': '[3]', 'EfficientNet-B5': '[4]', 'ResNet-50': '[3]',
            'EfficientNet-B4': '[4]', 'DenseNet-121': '[3], [5]', 'GoogLeNet': '[1]'}
    for name, pm in ARCH_PARAMS:
        prow.append([name, f'{pm:.1f}M', used[name]])
    prow.append(['EfficientNetV2-MSAF (ours)', f'{msaf["params"] / 1e6:.1f}M', f'GPU latency {msaf["gpu_latency_ms"]:.0f} ms / image (RTX 3050 Laptop)'])
    prow[1:] = sorted(prow[1:], key=lambda r: -float(r[1].rstrip('M')))
    story.append(data_table(prow, [5.4 * cm, 3.6 * cm, 8.0 * cm], highlight_rows={next(i for i, r in enumerate(prow) if 'ours' in r[0])}))
    story.append(P(f'At {msaf["params"] / 1e6:.1f}M parameters our model is about 7× smaller than VGG-16 and smaller than ResNet-50 and EfficientNet-B5, '
                   'but larger than DenseNet-121 and GoogLeNet. Size is not our main advantage; it is competitive, not leading.'))

    # ------------------------------------------------------------------ 9. Limits of this comparison
    story.append(P('9. What this comparison does not claim', 'h1'))
    story.append(callout('Stating the limits keeps the advantages defensible in a viva.', AMBER_T, AMBER))
    story.append(Spacer(1, 4))
    story += bullets([
        '<b>No head-to-head re-run of published models.</b> Their numbers are quoted, not re-measured. The robustness and calibration comparison uses a '
        'stock EfficientNetV2-S trained by us as a representative standard model.',
        f'<b>Clean accuracy is not an advantage.</b> Ours ({mf["clean_acc"]:.2f}%) is on par with, and slightly below, the best reported results '
        '(99.75–99.97%), which were measured on random splits.',
        f'<b>The field-photo test is small</b> ({mf["field_photos"]} photos) and different from Mohanty et al.\'s set, so {fcount(mf)}/{mf["field_photos"]} vs. 31.4% is an '
        'indication, not a controlled comparison. A larger field benchmark (e.g. PlantDoc [7]) is the natural next step.',
        '<b>Background bias</b> [6] is not specifically removed by our model; field augmentation and the gatekeeper reduce, but do not eliminate, reliance on '
        'lab-style backgrounds.',
        '<b>One training run per model</b>; differences under about 1 point are within noise.',
    ])

    # ------------------------------------------------------------------ 10. How to present it
    story.append(P('10. How to present this to the faculty', 'h1'))
    story.append(callout(
        '"Published PlantVillage models reach 99.35–99.97% on clean lab images, but the original study shows accuracy falling to 31.4% on outside images, '
        'and none of these papers measure robustness, calibration or non-leaf inputs. Our system reaches the same clean accuracy '
        f'({mf["clean_acc"]:.2f}%) on a stricter, leakage-free split, keeps {mf["mCA"]:.1f}% accuracy across six field corruptions '
        f'(motion blur {mf["corruptions"]["Motion blur"]:.1f}% without ever training on it), halves the calibration error of a standard EfficientNetV2-S, '
        'rejects non-leaf images that a closed-world classifier would confidently mislabel, and explains every diagnosis. '
        'Our major difference is field readiness and trustworthiness, not lab accuracy."', BLUE_T, BLUE))

    story.append(P('References', 'h1'))
    story += bullets(REFERENCES)

    doc.build(story)
    print(f'Saved {OUT}')

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    build()
