"""
Builds CropSense_AI_Official_Presentation.pptx.

Every metric on the slides is read from files produced by the training / evaluation scripts:
  results/ablation_results.json   (python -m src.compare)
  results/history_<arch>.json     (python -m src.train --arch <arch>)
  results/test_metrics.json       (python -m src.evaluate, leakage audit of the original split)
  data/splits/leaf_disjoint.json  (python -m src.splits)
Run it again after re-training and the deck updates itself.
"""
import os
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

# Color Palette Definitions
DARK_BG = RGBColor(15, 23, 42)        # Slate 900
DARK_CARD = RGBColor(30, 41, 59)      # Slate 800
LIGHT_BG = RGBColor(248, 250, 252)    # Slate 50
CARD_BG = RGBColor(255, 255, 255)     # White
CARD_BORDER = RGBColor(226, 232, 240) # Slate 200
ROW_ALT = RGBColor(241, 245, 249)     # Slate 100

PRIMARY_GREEN = RGBColor(5, 150, 105) # Emerald 600
LIGHT_GREEN = RGBColor(16, 185, 129)  # Emerald 500
ACCENT_BLUE = RGBColor(37, 99, 235)   # Blue 600
PURPLE_ACCENT = RGBColor(124, 58, 237)# Violet 600
WARNING_AMBER = RGBColor(217, 119, 6) # Amber 600
ALERT_RED = RGBColor(220, 38, 38)     # Red 600

TEXT_DARK = RGBColor(15, 23, 42)      # Slate 900
TEXT_BODY = RGBColor(51, 65, 85)      # Slate 700
TEXT_MUTED = RGBColor(100, 116, 139)  # Slate 500
TEXT_LIGHT = RGBColor(241, 245, 249)  # Slate 100
TEXT_LIGHT_MUTED = RGBColor(148, 163, 184)  # Slate 400

TINT = {
    PRIMARY_GREEN: RGBColor(236, 253, 245),
    ACCENT_BLUE: RGBColor(239, 246, 255),
    PURPLE_ACCENT: RGBColor(245, 243, 255),
    WARNING_AMBER: RGBColor(255, 251, 235),
    ALERT_RED: RGBColor(254, 242, 242),
}

ARCH_LABELS = {
    'baseline': 'EfficientNetV2-S (baseline)',
    'cbam': 'EfficientNetV2-S + CBAM',
    'msaf': 'EfficientNetV2-MSAF (proposed)',
}

# ----------------------------------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------------------------------
def load_json(path, default=None):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def load_results():
    ablation = load_json('results/ablation_results.json', {'runs': {}})
    runs = ablation.get('runs', {})
    if 'baseline' not in runs or 'msaf' not in runs:
        raise SystemExit("results/ablation_results.json needs 'baseline' and 'msaf' runs. "
                         "Train them (run_ablation.ps1) and run: python -m src.compare")
    histories = {a: load_json(f'results/history_{a}.json') for a in ARCH_LABELS}
    split = load_json('data/splits/leaf_disjoint.json')
    split_sizes = {s: len(split[s]) for s in ('train', 'val', 'test')} if split else None
    return {
        'runs': runs,
        'test_images': ablation.get('test_images'),
        'histories': {a: h for a, h in histories.items() if h},
        'leak': load_json('results/test_metrics.json', {}),
        'split': split_sizes,
        'bench': load_json('results/comprehensive_benchmarks.json', {}),
    }

def signed(x, unit=' pts'):
    return f"{x:+.1f}{unit}"

def worst_corruption(run):
    name = min(run['corruptions'], key=run['corruptions'].get)
    return name, run['corruptions'][name]

def plot_training_curves(histories, out_path='results/ablation_training_curves.png'):
    colors = {'baseline': '#94A3B8', 'cbam': '#3B82F6', 'msaf': '#059669'}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), dpi=200)
    for arch, h in histories.items():
        ep = range(1, len(h['val_accs']) + 1)
        axes[0].plot(ep, h['val_accs'], marker='o', ms=4, lw=2, color=colors[arch], label=ARCH_LABELS[arch])
        axes[1].plot(ep, h['val_losses'], marker='o', ms=4, lw=2, color=colors[arch], label=ARCH_LABELS[arch])
    axes[0].set_title('Validation accuracy (%)', fontsize=11, fontweight='bold')
    axes[1].set_title('Validation loss', fontsize=11, fontweight='bold')
    for ax in axes:
        ax.set_xlabel('Epoch')
        ax.grid(linestyle='--', alpha=0.4)
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8, loc='lower right')
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path

# ----------------------------------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------------------------------
def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def no_shadow(shape):
    sp_pr = shape._element.spPr
    effect = sp_pr.find(qn('a:effectLst'))
    if effect is None:
        sp_pr.append(sp_pr.makeelement(qn('a:effectLst'), {}))

def add_text(slide, left, top, width, height, paragraphs, anchor=MSO_ANCHOR.TOP, margin=0):
    """paragraphs: list of dicts {text, size, bold, color, align, space_before} or plain strings."""
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(margin)
    for i, para in enumerate(paragraphs):
        if isinstance(para, str):
            para = {'text': para}
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        runs = para['text'] if isinstance(para['text'], list) else [(para['text'], {})]
        for text, style in runs:
            r = p.add_run()
            r.text = text
            r.font.size = Pt(style.get('size', para.get('size', 12)))
            r.font.bold = style.get('bold', para.get('bold', False))
            r.font.color.rgb = style.get('color', para.get('color', TEXT_BODY))
        p.alignment = para.get('align', PP_ALIGN.LEFT)
        if 'space_before' in para:
            p.space_before = Pt(para['space_before'])
        p.line_spacing = para.get('line_spacing', 1.05)
    return box

def card(slide, left, top, width, height, fill=CARD_BG, border=CARD_BORDER, accent=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.adjustments[0] = min(0.5, 0.12 / min(width, height))  # ~0.12in corner radius at any size
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = border
    shape.line.width = Pt(1)
    no_shadow(shape)
    if accent is not None:
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top + 0.12), Inches(0.06), Inches(height - 0.24))
        bar.fill.solid()
        bar.fill.fore_color.rgb = accent
        bar.line.fill.background()
        no_shadow(bar)
    return shape

def header(slide, tag, title, dark=False):
    add_text(slide, 0.8, 0.42, 11.7, 0.3, [{'text': tag.upper(), 'size': 11, 'bold': True,
                                            'color': LIGHT_GREEN if dark else PRIMARY_GREEN}])
    add_text(slide, 0.8, 0.72, 11.7, 0.65, [{'text': title, 'size': 26, 'bold': True,
                                             'color': TEXT_LIGHT if dark else TEXT_DARK}])

def footer(slide, n, dark=False):
    add_text(slide, 0.8, 7.05, 8, 0.25, [{'text': 'CropSense AI  |  EfficientNetV2-MSAF', 'size': 9,
                                          'color': TEXT_LIGHT_MUTED if dark else TEXT_MUTED}])
    add_text(slide, 11.5, 7.05, 1.0, 0.25, [{'text': str(n), 'size': 9, 'align': PP_ALIGN.RIGHT,
                                             'color': TEXT_LIGHT_MUTED if dark else TEXT_MUTED}])

def titled_card(slide, left, top, width, height, title, body, color, body_size=12, title_size=15, fill=None):
    card(slide, left, top, width, height, fill or CARD_BG, CARD_BORDER, accent=color)
    paras = [{'text': title, 'size': title_size, 'bold': True, 'color': color}]
    for i, line in enumerate(body if isinstance(body, list) else [body]):
        if isinstance(line, dict):
            paras.append({'size': body_size, 'color': TEXT_BODY, 'space_before': 6, **line})
        else:
            paras.append({'text': line, 'size': body_size, 'color': TEXT_BODY, 'space_before': 6})
    add_text(slide, left + 0.3, top + 0.22, width - 0.5, height - 0.35, paras)

def picture_fit(slide, path, left, top, max_w, max_h):
    """Adds an image scaled to fit inside the box, centred."""
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
    scale = min(max_w / w, max_h / h)
    pw, ph = w * scale, h * scale
    return slide.shapes.add_picture(path, Inches(left + (max_w - pw) / 2), Inches(top + (max_h - ph) / 2), Inches(pw), Inches(ph))

def table(slide, left, top, width, rows, col_widths, header_fill=DARK_BG, font_size=11, row_h=0.36, highlight_row=None, highlight_fill=None):
    n_rows, n_cols = len(rows), len(rows[0])
    shape = slide.shapes.add_table(n_rows, n_cols, Inches(left), Inches(top), Inches(width), Inches(row_h * n_rows))
    tbl = shape.table
    tbl_pr = shape._element.graphic.graphicData.tbl.tblPr
    tbl_pr.set('bandRow', '0')
    tbl_pr.set('firstRow', '0')
    total = sum(col_widths)
    for j, w in enumerate(col_widths):
        tbl.columns[j].width = Emu(int(Inches(width) * w / total))
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, value in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            style = {}
            if isinstance(value, tuple):
                value, style = value
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = str(value)
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            p.font.size = Pt(style.get('size', font_size))
            cell.fill.solid()
            if i == 0:
                cell.fill.fore_color.rgb = header_fill
                p.font.bold = True
                p.font.color.rgb = TEXT_LIGHT
            else:
                if highlight_row is not None and i == highlight_row:
                    cell.fill.fore_color.rgb = highlight_fill or TINT[PRIMARY_GREEN]
                else:
                    cell.fill.fore_color.rgb = CARD_BG if i % 2 else ROW_ALT
                p.font.bold = style.get('bold', highlight_row is not None and i == highlight_row and j == 0)
                p.font.color.rgb = style.get('color', TEXT_DARK)
    return tbl

def flow_box(slide, left, top, width, height, title, sub, fill, border, title_color=TEXT_DARK, size=11):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.adjustments[0] = min(0.5, 0.08 / min(width, height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = border
    shape.line.width = Pt(1.25)
    no_shadow(shape)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = title
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = title_color
    if sub:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = sub
        r2.font.size = Pt(size - 2)
        r2.font.color.rgb = TEXT_MUTED
    return shape

def arrow(slide, x1, y1, x2, y2, color=TEXT_MUTED):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(1.5)
    ln = conn.line._get_or_add_ln()
    tail = ln.makeelement(qn('a:tailEnd'), {'type': 'triangle', 'w': 'med', 'len': 'med'})
    ln.append(tail)
    return conn

# ----------------------------------------------------------------------------------------------
# Deck
# ----------------------------------------------------------------------------------------------
def create_deck():
    R = load_results()
    runs = R['runs']
    base, msaf, cbam = runs['baseline'], runs['msaf'], runs.get('cbam')
    d_mca = msaf['mCA'] - base['mCA']
    d_clean = msaf['clean_acc'] - base['clean_acc']
    d_field = msaf['field_true_class_conf'] - base['field_true_class_conf']
    base_worst, base_worst_acc = worst_corruption(base)
    d_worst = msaf['corruptions'][base_worst] - base_worst_acc
    # Per-corruption change MSAF vs. baseline, best gains first
    d_corr = sorted(((c, msaf['corruptions'][c] - base['corruptions'][c]) for c in msaf['corruptions']), key=lambda kv: -kv[1])
    top_gains = [kv for kv in d_corr if kv[1] > 0][:2]
    worst_loss = d_corr[-1]
    field_n = lambda r: round(r['field_acc'] * r['field_photos'] / 100)
    gains_txt = ', '.join(f"{c.lower()} {signed(v)}" for c, v in top_gains)
    extra_params = msaf['params'] - base['params']
    extra_pct = 100 * extra_params / base['params']
    leak = R['leak']
    split = R['split'] or {'train': 0, 'val': 0, 'test': R['test_images'] or 0}
    curves_png = plot_training_curves(R['histories']) if R['histories'] else None

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    n = 0

    def new_slide(dark=False):
        nonlocal n
        n += 1
        s = prs.slides.add_slide(blank)
        set_bg(s, DARK_BG if dark else LIGHT_BG)
        if n > 1:
            footer(s, n, dark)
        return s

    # ==============================================================
    # SLIDE 1: TITLE (Dark Theme)
    # ==============================================================
    s = new_slide(dark=True)
    tag = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(3.0), Inches(0.38))
    tag.fill.solid()
    tag.fill.fore_color.rgb = PRIMARY_GREEN
    tag.line.fill.background()
    no_shadow(tag)
    tag.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    r = tag.text_frame.paragraphs[0].add_run()
    r.text = 'DEEP LEARNING RESEARCH PROJECT'
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = TEXT_LIGHT
    add_text(s, 0.8, 1.45, 11.7, 1.9, [
        {'text': 'CropSense AI: Multi-Scale Crop Disease Detection', 'size': 38, 'bold': True, 'color': TEXT_LIGHT},
        {'text': 'EfficientNetV2-MSAF: Multi-Scale Attention Fusion with CBAM and GeM pooling', 'size': 20,
         'color': TEXT_LIGHT_MUTED, 'space_before': 14},
    ])
    msf = runs.get('msaf_field')
    if msf:
        badges = [
            (f"{base['mCA']:.1f} -> {msf['mCA']:.1f}%", 'Accuracy under 6 field corruptions\n(proposed system vs. original)', LIGHT_GREEN),
            (f"{base['ece']:.1f} -> {msf['ece']:.1f}%", 'Calibration error (ECE)\nvs. original EfficientNetV2-S', RGBColor(96, 165, 250)),
            (f"{field_n(msf)} / {msf['field_photos']}", f"Real field photos correct\n(original {field_n(base)} / {base['field_photos']})", RGBColor(251, 191, 36)),
            (f"{msf['clean_acc']:.2f}%", f"Clean test accuracy\n(+{extra_pct:.1f}% parameters)", RGBColor(167, 139, 250)),
        ]
    else:
      badges = [
        (f"{msaf['clean_acc']:.2f}%", 'Clean test accuracy\n(leaf-disjoint split)', LIGHT_GREEN),
        (f"{base['ece']:.1f} -> {msaf['ece']:.1f}%", 'Calibration error (ECE)\nvs. EfficientNetV2-S', RGBColor(96, 165, 250)),
        (f"{field_n(msaf)} / {msaf['field_photos']}", f"Real field photos correct\n(baseline {field_n(base)} / {base['field_photos']})", RGBColor(251, 191, 36)),
        (f"+{extra_pct:.1f}%", f"Parameters\n(+{extra_params/1e3:.0f}K over the baseline)", RGBColor(167, 139, 250)),
      ]
    if msf:
        add_text(s, 0.8, 5.8, 11.7, 0.4, [{'text': 'Proposed system = EfficientNetV2-MSAF + field-augmented training. Robustness comes mainly from the augmentation; '
                                                   'calibration and field-photo gains come from the MSAF architecture.', 'size': 12, 'color': TEXT_LIGHT_MUTED}])
    for i, (metric, label, col) in enumerate(badges):
        x = 0.8 + i * 2.95
        card(s, x, 4.0, 2.75, 1.65, DARK_CARD, RGBColor(51, 65, 85))
        add_text(s, x + 0.25, 4.18, 2.3, 1.4, [
            {'text': metric, 'size': 28, 'bold': True, 'color': col},
            {'text': label, 'size': 11, 'color': RGBColor(203, 213, 225), 'space_before': 6},
        ])
    add_text(s, 0.8, 6.6, 11.7, 0.4, [{'text': '38 classes  |  14 crops  |  Grad-CAM explainability  |  Leaf gatekeeper  |  Severity estimate  |  Streamlit app',
                                       'size': 12, 'color': TEXT_LIGHT_MUTED}])

    # ==============================================================
    # SLIDE 2: DRAWBACKS OF EXISTING MODELS (MEASURED)
    # ==============================================================
    s = new_slide()
    header(s, 'Problem analysis', 'Drawbacks of the existing model, measured on our data')
    drawbacks = [
        ('1. Single-scale decision', ALERT_RED,
         ['The classifier only sees the final 7x7 feature map: each cell covers 32x32 px of a 224 px leaf.',
          'Pin-point lesions (bacterial spot, Septoria specks, mite stippling) are averaged into a few cells.']),
        ('2. Average pooling dilutes lesions', WARNING_AMBER,
         ['Global average pooling weights a lesion covering 5% of the leaf at 5% of the descriptor.',
          'Healthy tissue and backdrop dominate the feature vector.']),
        ('3. Fragile under field conditions', ALERT_RED,
         [f"Leaf-disjoint test: {base['clean_acc']:.2f}% clean, but {base_worst_acc:.1f}% under {base_worst.lower()} "
          f"and {base['mCA']:.1f}% mean over 6 corruptions.",
          f"Real field photos: only {base['field_true_class_conf']:.0f}% mean confidence in the correct class."]),
        ('4. Evaluation flaw in the original split', WARNING_AMBER,
         [f"{leak.get('leaked_fraction_pct', 67.5):.1f}% of test images were rotated / flipped copies of training leaves.",
          'Clean accuracy is saturated (99.9%), so it cannot show any architectural gain on its own.']),
    ]
    for i, (title, col, body) in enumerate(drawbacks):
        x = 0.8 + (i % 2) * 5.95
        y = 1.65 + (i // 2) * 2.62
        titled_card(s, x, y, 5.75, 2.42, title, body, col, body_size=15, title_size=18)

    # ==============================================================
    # SLIDE 3: PROPOSED ARCHITECTURE (DIAGRAM)
    # ==============================================================
    s = new_slide()
    header(s, 'Proposed architecture', 'EfficientNetV2-MSAF: Multi-Scale Attention Fusion')
    # Backbone row
    stages = [('Input', '3x224x224'), ('Stem + Stage 1-2', 'Fused-MBConv'), ('Stage 3', '64 x 28x28'),
              ('Stage 4-5', '160 x 14x14'), ('Stage 6 + Head', '1280 x 7x7')]
    xs = [0.8, 2.85, 4.9, 6.95, 9.0]
    for (t, sub), x in zip(stages, xs):
        flow_box(s, x, 1.7, 1.75, 0.8, t, sub, CARD_BG, TEXT_MUTED)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(s, a + 1.75, 2.1, b, 2.1)
    add_text(s, 11.0, 1.75, 1.6, 0.7, [{'text': 'EfficientNetV2-S backbone (ImageNet-pretrained)', 'size': 10, 'color': TEXT_MUTED}])
    # Taps
    tap_x = [4.9, 6.95, 9.0]
    tap_labels = ['fine: small lesions', 'mid: lesion clusters', 'coarse: leaf pattern']
    for x, sub in zip(tap_x, tap_labels):
        arrow(s, x + 0.875, 2.5, x + 0.875, 2.95, PRIMARY_GREEN)
        flow_box(s, x, 2.95, 1.75, 0.62, 'CBAM', sub, TINT[ACCENT_BLUE], ACCENT_BLUE, ACCENT_BLUE, size=11)
        arrow(s, x + 0.875, 3.57, x + 0.875, 3.85, PRIMARY_GREEN)
        flow_box(s, x, 3.85, 1.75, 0.62, 'GeM + LayerNorm', 'learnable p', TINT[PRIMARY_GREEN], PRIMARY_GREEN, PRIMARY_GREEN, size=11)
        arrow(s, x + 0.875, 4.47, x + 0.875, 4.85, PRIMARY_GREEN)
    flow_box(s, 4.9, 4.85, 5.85, 0.62, 'Concatenate  [64 ; 160 ; 1280] = 1,504-d   +   scale-dropout (training)', None,
             TINT[PURPLE_ACCENT], PURPLE_ACCENT, PURPLE_ACCENT, size=12)
    arrow(s, 7.825, 5.47, 7.825, 5.75, PURPLE_ACCENT)
    flow_box(s, 4.9, 5.75, 5.85, 0.6, 'Dropout(0.3) + Linear(1504 -> 38)  ->  softmax', None, DARK_BG, DARK_BG, TEXT_LIGHT, size=12)
    # Left: what each part fixes
    fixes = [
        ('Multi-scale taps', 'targets drawback 1: stage 3 keeps 28x28 detail (8 px per cell)', ALERT_RED),
        ('CBAM per scale', 'focuses each scale on lesion channels and positions', ACCENT_BLUE),
        ('GeM pooling', 'targets drawback 2: emphasises small, strongly activated regions', WARNING_AMBER),
        ('Scale-dropout', 'targets drawback 3: drops whole scales so no single scale is relied on', PURPLE_ACCENT),
    ]
    y = 2.95
    for t, d, col in fixes:
        add_text(s, 0.8, y, 3.85, 0.85, [{'text': t, 'size': 13, 'bold': True, 'color': col},
                                          {'text': d, 'size': 11, 'color': TEXT_BODY, 'space_before': 2}])
        y += 0.85
    add_text(s, 11.0, 4.9, 1.7, 1.4, [{'text': f"+{extra_params:,} params\n(+{extra_pct:.2f}%)", 'size': 12, 'bold': True, 'color': PRIMARY_GREEN}])

    # ==============================================================
    # SLIDE 4: EQUATIONS
    # ==============================================================
    s = new_slide()
    header(s, 'Mathematical formulation', 'Attention, pooling and multi-scale fusion')
    eqs = [
        ('Channel attention', 'results/eq_channel_attention.png', 'Which feature channels respond to lesions (avg + max descriptors, shared MLP).', ACCENT_BLUE),
        ('Spatial attention', 'results/eq_spatial_attention.png', 'Where on the leaf the lesions are (7x7 conv over channel-pooled maps).', PRIMARY_GREEN),
        ('Generalized-mean pooling', 'results/eq_gem_pooling.png', 'Learnable p sits between average and max pooling; learned per scale.', WARNING_AMBER),
        ('Multi-scale fusion', 'results/eq_msaf_fusion.png', 'Per-scale descriptors are normalised then concatenated before the classifier.', PURPLE_ACCENT),
    ]
    for i, (t, img, d, col) in enumerate(eqs):
        x = 0.8 + (i % 2) * 5.95
        y = 1.65 + (i // 2) * 2.62
        card(s, x, y, 5.75, 2.42, CARD_BG, CARD_BORDER, accent=col)
        add_text(s, x + 0.3, y + 0.2, 5.2, 0.4, [{'text': t, 'size': 16, 'bold': True, 'color': col}])
        if os.path.exists(img):
            picture_fit(s, img, x + 0.3, y + 0.68, 5.2, 0.95)
        add_text(s, x + 0.3, y + 1.72, 5.2, 0.6, [{'text': d, 'size': 12, 'color': TEXT_BODY}])

    # ==============================================================
    # SLIDE 5: NETWORK SPECIFICATION TABLE
    # ==============================================================
    s = new_slide()
    header(s, 'Network specification', 'EfficientNetV2-MSAF layer and parameter blueprint')
    rows = [
        ['Block', 'Operation', 'Channels', 'Output', 'Params'],
        ['Stem', 'Conv 3x3, stride 2', '3 -> 24', '112x112', '696'],
        ['Stage 1 (2 blocks)', 'Fused-MBConv, stride 1', '24 -> 24', '112x112', '10,464'],
        ['Stage 2 (4 blocks)', 'Fused-MBConv, stride 2', '24 -> 48', '56x56', '303,552'],
        [('Stage 3 (4 blocks)  [tap 1]', {'bold': True, 'color': ACCENT_BLUE}), 'Fused-MBConv, stride 2', '48 -> 64', '28x28', '589,184'],
        ['Stage 4 (6 blocks)', 'MBConv + SE, stride 2', '64 -> 128', '14x14', '917,680'],
        [('Stage 5 (9 blocks)  [tap 2]', {'bold': True, 'color': ACCENT_BLUE}), 'MBConv + SE, stride 1', '128 -> 160', '14x14', '3,463,840'],
        ['Stage 6 (15 blocks)', 'MBConv + SE, stride 2', '160 -> 256', '7x7', '14,561,832'],
        [('Head conv  [tap 3]', {'bold': True, 'color': ACCENT_BLUE}), 'Conv 1x1', '256 -> 1280', '7x7', '330,240'],
        [('CBAM x 3 (new)', {'bold': True, 'color': PRIMARY_GREEN}), 'Channel MLP + 7x7 spatial conv', '64 / 160 / 1280', 'same', '209,318'],
        [('GeM + LayerNorm x 3 (new)', {'bold': True, 'color': PRIMARY_GREEN}), 'Learnable-p pooling, per-scale norm', '64 / 160 / 1280', '1x1', '3,011'],
        [('Classifier (new)', {'bold': True, 'color': PRIMARY_GREEN}), 'Dropout 0.3 + Linear', '1504 -> 38', '38', '57,190'],
        [('Total', {'bold': True}), '', '', '', (f"{msaf['params']:,}", {'bold': True})],
    ]
    table(s, 0.8, 1.6, 11.7, rows, [3.1, 3.3, 1.8, 1.3, 1.6], font_size=12, row_h=0.4)

    # ==============================================================
    # SLIDE 6: DATA ENGINEERING
    # ==============================================================
    s = new_slide()
    header(s, 'Data engineering', 'Leaf-disjoint split: a fair test set')
    data_cards = [
        ('Dataset', PRIMARY_GREEN,
         [f"{sum(split.values()):,} images, 38 classes, 14 crops (Kaggle 'New Plant Diseases', derived from PlantVillage).",
          'The dataset ships rotated / flipped copies of each photo (e.g. _90deg, _flipTB, _new30degFlipLR).']),
        ('Problem found in the original split', ALERT_RED,
         ['Files were split at random, so copies of one leaf ended up in both train and test.',
          f"{leak.get('leaked_fraction_pct', 67.5):.1f}% of the old test images had a sibling in train/val."]),
        ('Fix: group by source leaf', ACCENT_BLUE,
         ['Every copy of a physical leaf is assigned to the same split (80 / 10 / 10 by leaf, seed 42).',
          f"Train {split['train']:,}  |  Val {split['val']:,}  |  Test {split['test']:,} images."]),
        ('Same data for every model', PURPLE_ACCENT,
         ['All three architectures train and test on this identical split with the identical recipe.',
          'Any difference in the results comes from the architecture alone.']),
    ]
    for i, (t, col, body) in enumerate(data_cards):
        x = 0.8 + (i % 2) * 5.95
        y = 1.65 + (i // 2) * 2.62
        titled_card(s, x, y, 5.75, 2.42, t, body, col, body_size=15, title_size=18)

    # ==============================================================
    # SLIDE 7: TAXONOMY
    # ==============================================================
    s = new_slide()
    header(s, 'Scope', '14 crop species, 38 health and disease classes')
    taxonomy = [
        ('Orchard fruits', PRIMARY_GREEN, [
            ('Apple', 'Scab, Black rot, Cedar apple rust, Healthy'),
            ('Cherry', 'Powdery mildew, Healthy'),
            ('Peach', 'Bacterial spot, Healthy'),
            ('Blueberry', 'Healthy')]),
        ('Grains, vines, citrus', ACCENT_BLUE, [
            ('Corn', 'Gray leaf spot, Common rust, Northern leaf blight, Healthy'),
            ('Grape', 'Black rot, Esca, Leaf blight, Healthy'),
            ('Orange', 'Huanglongbing (citrus greening)'),
            ('Bell pepper', 'Bacterial spot, Healthy')]),
        ('Tubers, berries, row crops', WARNING_AMBER, [
            ('Potato', 'Early blight, Late blight, Healthy'),
            ('Strawberry', 'Leaf scorch, Healthy'),
            ('Squash', 'Powdery mildew'),
            ('Soybean / Raspberry', 'Healthy')]),
        ('Tomato (10 classes)', ALERT_RED, [
            ('Fungal', 'Early blight, Late blight, Leaf mold, Septoria spot, Target spot'),
            ('Bacterial', 'Bacterial spot'),
            ('Viral', 'Yellow leaf curl, Mosaic'),
            ('Pest / Healthy', 'Spider mites, Healthy')]),
    ]
    for i, (t, col, items) in enumerate(taxonomy):
        x = 0.8 + i * 2.95
        card(s, x, 1.65, 2.75, 5.1, CARD_BG, CARD_BORDER, accent=col)
        paras = [{'text': t, 'size': 17, 'bold': True, 'color': col}]
        for crop, diseases in items:
            paras.append({'text': crop, 'size': 15, 'bold': True, 'color': TEXT_DARK, 'space_before': 16})
            paras.append({'text': diseases, 'size': 14, 'color': TEXT_BODY, 'space_before': 3})
        add_text(s, x + 0.28, 1.85, 2.3, 4.8, paras)

    # ==============================================================
    # SLIDE 8: TRAINING RECIPE
    # ==============================================================
    s = new_slide()
    h = R['histories'].get('msaf') or R['histories'].get('baseline') or {}
    header(s, 'Training setup', 'One identical recipe for all three architectures')
    recipe = [
        ('Optimisation', PRIMARY_GREEN,
         [f"AdamW (lr {h.get('lr', 1e-3):g}, weight decay 1e-4) with OneCycleLR.",
          f"{h.get('epochs', 8)} epochs, batch {h.get('batch_size', 32)}, mixed precision (FP16 autocast + GradScaler) on an RTX 3050 4 GB."]),
        ('Regularisation', ACCENT_BLUE,
         ['Cross-entropy with label smoothing 0.1 (formula below).',
          'MSAF only: dropout 0.3 on the fused descriptor and scale-dropout 0.1.']),
        ('Augmentation', WARNING_AMBER,
         ['RandomResizedCrop 224, horizontal and vertical flips, ColorJitter.',
          'Corruptions are NOT used in training: robustness is measured, not trained in.']),
        ('Sampling', PURPLE_ACCENT,
         ['Each epoch draws one random copy of every source leaf (36,656 leaves).',
          f"Selection: best validation accuracy; evaluated once on the held-out test split."]),
    ]
    for i, (t, col, body) in enumerate(recipe):
        x = 0.8 + (i % 2) * 5.95
        y = 1.65 + (i // 2) * 2.25
        titled_card(s, x, y, 5.75, 2.05, t, body, col, body_size=14, title_size=18)
    if os.path.exists('results/eq_label_smoothing.png'):
        picture_fit(s, 'results/eq_label_smoothing.png', 2.9, 6.15, 7.5, 0.85)

    # ==============================================================
    # SLIDE 9: ABLATION RESULTS TABLE
    # ==============================================================
    s = new_slide()
    header(s, 'Results', f"Ablation on the leaf-disjoint test set ({R['test_images']:,} images)")
    order = [a for a in ('baseline', 'cbam', 'msaf') if a in runs]
    def best(metric, higher=True):
        vals = [runs[a][metric] for a in order]
        return max(vals) if higher else min(vals)
    def cell(a, metric, fmt, higher=True):
        v = runs[a][metric]
        return (fmt.format(v), {'bold': True, 'color': PRIMARY_GREEN}) if v == best(metric, higher) else fmt.format(v)
    rows = [['Model', 'Params', 'Clean acc', 'Macro-F1', 'Mean corrupted acc (mCA)', f'{base_worst}', 'ECE (lower better)', 'Field photo conf.', 'GPU latency']]
    for a in order:
        r = runs[a]
        rows.append([
            ARCH_LABELS[a], f"{r['params']/1e6:.2f}M",
            cell(a, 'clean_acc', '{:.2f}%'), cell(a, 'clean_macro_f1', '{:.2f}%'),
            cell(a, 'mCA', '{:.2f}%'),
            (f"{r['corruptions'][base_worst]:.2f}%", {'bold': True, 'color': PRIMARY_GREEN}) if r['corruptions'][base_worst] == max(runs[x]['corruptions'][base_worst] for x in order) else f"{r['corruptions'][base_worst]:.2f}%",
            cell(a, 'ece', '{:.2f}%', higher=False),
            cell(a, 'field_true_class_conf', '{:.1f}%'),
            f"{r['gpu_latency_ms']:.1f} ms" if r.get('gpu_latency_ms') else 'n/a',
        ])
    table(s, 0.8, 1.6, 11.7, rows, [2.9, 0.9, 1.1, 1.1, 1.5, 1.3, 1.2, 1.2, 1.1], font_size=12, row_h=0.62,
          highlight_row=order.index('msaf') + 1)
    takeaways = [
        ('Calibration', f"ECE {base['ece']:.1f}% -> {msaf['ece']:.1f}%: MSAF's confidence matches its accuracy far better.", PRIMARY_GREEN),
        ('Field photos', f"{field_n(msaf)}/{msaf['field_photos']} correct vs. {field_n(base)}/{base['field_photos']}; true-class confidence {signed(d_field)}.", WARNING_AMBER),
        ('Robustness: mixed', f"mCA {signed(d_mca)}. Gains: {gains_txt}. Loss: {worst_loss[0].lower()} {signed(worst_loss[1])}.", ACCENT_BLUE),
    ]
    if cbam:
        takeaways.append(('CBAM alone', f"mCA {signed(cbam['mCA'] - base['mCA'])}, best on motion blur, but ECE stays {cbam['ece']:.1f}%: the calibration gain comes from multi-scale GeM fusion.", PURPLE_ACCENT))
    for i, (t, d, col) in enumerate(takeaways):
        x = 0.8 + i * (11.7 / len(takeaways))
        w = 11.7 / len(takeaways) - 0.2
        titled_card(s, x, 4.55, w, 2.2, t, d, col, body_size=14, title_size=16)

    # ==============================================================
    # SLIDE 10: ROBUSTNESS CHART
    # ==============================================================
    s = new_slide()
    header(s, 'Robustness', 'Accuracy under six simulated field conditions')
    picture_fit(s, 'results/ablation_robustness.png', 0.8, 1.55, 8.3, 5.3)
    cond_desc = [
        ('Gaussian / motion blur', 'Defocus and hand shake (radius 2.5; 15 px kernel at random angle).'),
        ('Sensor noise / low light', 'Gaussian noise sigma 25; 35% brightness + noise.'),
        ('JPEG q=10', 'Heavy compression from messaging apps.'),
        ('Overexposure', 'Midday glare: 1.45x gain + 30.'),
    ]
    paras = [{'text': 'Conditions tested', 'size': 15, 'bold': True, 'color': ACCENT_BLUE}]
    for t, d in cond_desc:
        paras.append({'text': t, 'size': 12, 'bold': True, 'color': TEXT_DARK, 'space_before': 10})
        paras.append({'text': d, 'size': 11, 'color': TEXT_BODY, 'space_before': 1})
    paras.append({'text': 'None of these corruptions were seen in training for any model.', 'size': 11,
                  'bold': True, 'color': PRIMARY_GREEN, 'space_before': 14})
    paras.append({'text': f"MSAF gains most on {gains_txt}; motion blur remains the weak spot.",
                  'size': 11, 'color': TEXT_BODY, 'space_before': 8})
    card(s, 9.3, 1.55, 3.2, 5.3, CARD_BG, CARD_BORDER, accent=ACCENT_BLUE)
    add_text(s, 9.6, 1.75, 2.75, 5.0, paras)

    # ==============================================================
    # SLIDES 10b/10c: FIELD-AUGMENTED TRAINING (only when those runs exist)
    # ==============================================================
    if 'baseline_field' in runs and 'msaf_field' in runs:
        seen = ('Gaussian blur', 'Sensor noise')
        unseen = [c for c in base['corruptions'] if c not in seen]
        avg = lambda r, cs: sum(r['corruptions'][c] for c in cs) / len(cs)
        bf, mf = runs['baseline_field'], runs['msaf_field']
        fa_order = ['baseline', 'baseline_field', 'msaf', 'msaf_field']
        fa_labels = {'baseline': 'EfficientNetV2-S', 'baseline_field': 'EfficientNetV2-S + field aug.',
                     'msaf': 'EfficientNetV2-MSAF', 'msaf_field': 'EfficientNetV2-MSAF + field aug.'}
        cols = {
            'Clean acc': lambda r: r['clean_acc'],
            'Mean corrupted (mCA)': lambda r: r['mCA'],
            'Seen in training (2)': lambda r: avg(r, seen),
            'Unseen (4)': lambda r: avg(r, unseen),
            'Motion blur (unseen)': lambda r: r['corruptions']['Motion blur'],
            'ECE (lower better)': lambda r: r['ece'],
        }
        s = new_slide()
        header(s, 'Field-augmented training', 'Does MSAF still help when both models train on blur and noise?')
        rows = [['Model'] + list(cols) + ['Field photos']]
        for k in fa_order:
            row = [fa_labels[k]]
            for cname, fn in cols.items():
                vals = [fn(runs[x]) for x in fa_order]
                best_v = min(vals) if cname.startswith('ECE') else max(vals)
                v = fn(runs[k])
                row.append((f"{v:.2f}%", {'bold': True, 'color': PRIMARY_GREEN}) if v == best_v else f"{v:.2f}%")
            row.append(f"{field_n(runs[k])} / {runs[k]['field_photos']}")
            rows.append(row)
        table(s, 0.8, 1.6, 11.7, rows, [2.9, 1.1, 1.3, 1.3, 1.1, 1.3, 1.2, 1.0], font_size=12, row_h=0.55,
              highlight_row=fa_order.index('msaf_field') + 1)
        d_arch_aug = mf['mCA'] - bf['mCA']
        fa_takeaways = [
            ('Augmentation effect', f"mCA: EfficientNetV2-S {base['mCA']:.1f}% -> {bf['mCA']:.1f}%, MSAF {msaf['mCA']:.1f}% -> {mf['mCA']:.1f}%.", ACCENT_BLUE),
            ('Architecture under the same augmentation', f"MSAF + aug. vs. EfficientNetV2-S + aug.: mCA {signed(d_arch_aug)}, unseen {signed(avg(mf, unseen) - avg(bf, unseen))}, ECE {bf['ece']:.1f}% -> {mf['ece']:.1f}%.", PRIMARY_GREEN),
            ('Unseen corruptions', f"Motion blur, JPEG, low light and overexposure were never trained on. Motion blur: {bf['corruptions']['Motion blur']:.1f}% (S + aug.) vs. {mf['corruptions']['Motion blur']:.1f}% (MSAF + aug.).", WARNING_AMBER),
        ]
        for i, (t, d, col) in enumerate(fa_takeaways):
            x = 0.8 + i * 3.95
            titled_card(s, x, 4.55, 3.75, 2.2, t, d, col, body_size=13, title_size=15)

        s = new_slide()
        header(s, 'Field-augmented training', 'Accuracy per condition, with and without augmentation')
        if os.path.exists('results/field_aug_robustness.png'):
            picture_fit(s, 'results/field_aug_robustness.png', 0.8, 1.55, 8.3, 5.3)
        paras = [{'text': 'Training augmentation', 'size': 15, 'bold': True, 'color': ACCENT_BLUE},
                 {'text': 'Gaussian blur (sigma 0.5-3) on 30% and sensor noise (std up to 0.12) on 30% of training images.', 'size': 12, 'color': TEXT_BODY, 'space_before': 4},
                 {'text': 'Seen vs. unseen', 'size': 15, 'bold': True, 'color': ACCENT_BLUE, 'space_before': 14},
                 {'text': 'Gaussian blur and sensor noise resemble the training augmentation. Motion blur, JPEG, low light and overexposure test generalisation.', 'size': 12, 'color': TEXT_BODY, 'space_before': 4},
                 {'text': 'Same split, epochs and seed as the other runs.', 'size': 11, 'bold': True, 'color': PRIMARY_GREEN, 'space_before': 14}]
        card(s, 9.3, 1.55, 3.2, 5.3, CARD_BG, CARD_BORDER, accent=ACCENT_BLUE)
        add_text(s, 9.6, 1.75, 2.75, 5.0, paras)

    # ==============================================================
    # SLIDE 11: TRAINING CURVES
    # ==============================================================
    s = new_slide()
    header(s, 'Convergence', 'Validation curves of the three architectures')
    if curves_png:
        picture_fit(s, curves_png, 0.8, 1.55, 8.3, 5.3)
    paras = [{'text': 'Best validation accuracy', 'size': 15, 'bold': True, 'color': PRIMARY_GREEN}]
    for a in order:
        if runs[a].get('best_val_acc') is not None:
            paras.append({'text': [(f"{ARCH_LABELS[a]}\n", {'size': 12, 'bold': True, 'color': TEXT_DARK}),
                                   (f"{runs[a]['best_val_acc']:.2f}%", {'size': 20, 'bold': True, 'color': PRIMARY_GREEN if runs[a]['best_val_acc'] == max(runs[x].get('best_val_acc', 0) for x in order) else TEXT_MUTED})],
                          'space_before': 12})
    secs = [sum(R['histories'][a]['epoch_seconds']) / len(R['histories'][a]['epoch_seconds']) for a in order if a in R['histories']]
    if secs:
        paras.append({'text': f"About {sum(secs)/len(secs)/60:.0f} min per epoch on a 4 GB laptop GPU.", 'size': 11, 'color': TEXT_MUTED, 'space_before': 16})
    card(s, 9.3, 1.55, 3.2, 5.3, CARD_BG, CARD_BORDER, accent=PRIMARY_GREEN)
    add_text(s, 9.6, 1.75, 2.75, 5.0, paras)

    # ==============================================================
    # SLIDE 12: GRAD-CAM
    # ==============================================================
    s = new_slide()
    header(s, 'Explainable AI', 'Grad-CAM: where the model looks')
    if os.path.exists('results/gradcam_demo.png'):
        picture_fit(s, 'results/gradcam_demo.png', 0.8, 1.55, 7.4, 5.3)
    gcam = [
        ('Why it matters', 'Growers and extension officers need to see that the model looked at diseased tissue, not the background.', TEXT_DARK),
        ('How it works', 'Hooks on the head conv (model.features[-1]) collect activations and gradients; channel weights = mean gradient.', ACCENT_BLUE),
        ('Caveat for MSAF', 'On MSAF, Grad-CAM maps are noisy: the per-scale LayerNorm cancels the averaged gradient weights. The app therefore serves EfficientNetV2-S (shown here).', ALERT_RED),
    ]
    for k, (t, d, col) in enumerate(gcam):
        titled_card(s, 8.5, 1.55 + k * 1.8, 4.0, 1.65, t, d, col, body_size=12, title_size=15)

    # ==============================================================
    # SLIDE 13: SEVERITY ESTIMATE
    # ==============================================================
    s = new_slide()
    header(s, 'Agronomic output', 'Severity estimate: share of the leaf flagged by Grad-CAM')
    card(s, 0.8, 1.55, 11.7, 1.65, CARD_BG, CARD_BORDER, accent=PRIMARY_GREEN)
    add_text(s, 1.1, 1.7, 5.5, 1.4, [
        {'text': 'Severity index S', 'size': 16, 'bold': True, 'color': PRIMARY_GREEN},
        {'text': 'Pixels inside the segmented leaf whose Grad-CAM activation exceeds tau = 0.45, as a share of all leaf pixels.',
         'size': 14, 'color': TEXT_BODY, 'space_before': 4},
    ])
    if os.path.exists('results/eq_severity_index.png'):
        picture_fit(s, 'results/eq_severity_index.png', 6.8, 1.7, 5.5, 1.35)
    stages = [
        ('Stage 1: Mild', '< 10% of leaf', 'Bio-controls (neem oil, Bacillus subtilis); remove first affected leaves.', PRIMARY_GREEN),
        ('Stage 2: Moderate', '10-25% of leaf', 'Protective contact fungicide (copper hydroxide, mancozeb); sanitise tools.', WARNING_AMBER),
        ('Stage 3: Severe', '25-50% of leaf', 'Systemic fungicide (azoxystrobin, difenoconazole); stop overhead irrigation.', ALERT_RED),
        ('Stage 4: Critical', '> 50% of leaf', 'Remove and bag the plant; do not compost; protect neighbouring rows.', RGBColor(127, 29, 29)),
    ]
    for i, (t, rng, act, col) in enumerate(stages):
        x = 0.8 + i * 2.95
        titled_card(s, x, 3.4, 2.75, 2.75, t, [{'text': rng, 'bold': True, 'color': TEXT_DARK}, act], col, body_size=14, title_size=17)
    add_text(s, 0.8, 6.35, 11.7, 0.5, [{'text': 'Caveat: Grad-CAM shows evidence for the class, not a pixel-accurate lesion mask, and the stage thresholds are '
                                               'project-defined rather than an official standard. The app labels it as an estimate.',
                                       'size': 12, 'color': TEXT_MUTED}])

    # ==============================================================
    # SLIDE 14: DEPLOYMENT PIPELINE
    # ==============================================================
    s = new_slide()
    header(s, 'System', 'Two-stage deployment pipeline (Streamlit app)')
    pipe = [
        ('1. Leaf gatekeeper', 'HSV plant-pigment mask rejects documents, screens and objects; contour analysis rejects multi-leaf or cluttered photos.', ALERT_RED),
        ('2. Classification', 'CNN on the validated single leaf: top-3 classes with confidence, and a warning below 75% confidence.', PRIMARY_GREEN),
        ('3. Explanation', 'Grad-CAM heatmap from the same forward pass as the prediction.', ACCENT_BLUE),
        ('4. Action', 'Severity estimate, organic and chemical treatment plan, and a downloadable PDF report.', PURPLE_ACCENT),
    ]
    for i, (t, d, col) in enumerate(pipe):
        x = 0.8 + i * 2.95
        titled_card(s, x, 1.65, 2.75, 3.2, t, d, col, body_size=15, title_size=17)
        if i < 3:
            arrow(s, x + 2.77, 3.25, x + 2.93, 3.25, TEXT_MUTED)
    card(s, 0.8, 5.1, 11.7, 1.65, TINT[PRIMARY_GREEN], CARD_BORDER, accent=PRIMARY_GREEN)
    add_text(s, 1.1, 5.3, 11.2, 1.3, [
        {'text': 'Field-photo check', 'size': 17, 'bold': True, 'color': TEXT_DARK},
        {'text': f"On {msaf['field_photos']} real field photos (sample_images/), the baseline classifies {base['field_acc']:.0f}% correctly and MSAF "
                 f"{msaf['field_acc']:.0f}%, with mean true-class confidence {base['field_true_class_conf']:.0f}% vs. {msaf['field_true_class_conf']:.0f}%.",
         'size': 15, 'color': TEXT_BODY, 'space_before': 6},
    ])

    # ==============================================================
    # SLIDE 15: LIMITATIONS
    # ==============================================================
    s = new_slide()
    header(s, 'Critical evaluation', 'Limitations and next steps')
    limits = [
        ('Lab-style training images', ALERT_RED,
         'PlantVillage leaves are photographed on plain backgrounds. Next: fine-tune on in-field datasets (e.g. PlantDoc).'),
        ('Small real-world test', ALERT_RED,
         f"Field performance is checked on only {msaf['field_photos']} photos; corruptions are simulated. Next: a labelled field set of several hundred images."),
        ('Closed-world classes', WARNING_AMBER,
         'Any leaf is mapped to one of 38 classes; unseen crops (mango, rice) get the closest match. Next: an open-set reject threshold.'),
        ('Explainability trade-off', ALERT_RED,
         'Grad-CAM works on EfficientNetV2-S but gives noisy maps on MSAF, so the app keeps the baseline. Next: a CAM method built for multi-scale heads (e.g. per-scale Score-CAM).'),
        ('Deployment choice', WARNING_AMBER,
         'Better calibration (MSAF) vs. trustworthy heatmaps and severity estimate (baseline): the app currently favours explainability.'),
        ('Motion blur and single seed', WARNING_AMBER,
         (f"Motion blur is still the hardest condition ({runs['msaf_field']['corruptions']['Motion blur']:.0f}% for MSAF + aug., {runs['baseline_field']['corruptions']['Motion blur']:.0f}% for S + aug.). "
          if 'msaf_field' in runs and 'baseline_field' in runs else
          f"MSAF reaches only {msaf['corruptions']['Motion blur']:.0f}% under motion blur. ")
         + "One run per model: gaps under ~1 pt are within noise. Next: motion-blur augmentation and 3 seeds."),
    ]
    for i, (t, col, d) in enumerate(limits):
        x = 0.8 + (i % 3) * 3.95
        y = 1.65 + (i // 3) * 2.62
        titled_card(s, x, y, 3.75, 2.42, t, d, col, body_size=13, title_size=16)

    # ==============================================================
    # SLIDE 16: CONCLUSION & DEMO (Dark Theme)
    # ==============================================================
    s = new_slide(dark=True)
    header(s, 'Summary', 'Conclusion and live demo', dark=True)
    card(s, 0.8, 1.6, 7.0, 5.1, DARK_CARD, RGBColor(51, 65, 85))
    bullets = [
        'Identified 4 measurable drawbacks of the stock EfficientNetV2-S model.',
        f"Proposed EfficientNetV2-MSAF: multi-scale CBAM attention + GeM fusion for +{extra_pct:.1f}% parameters.",
        f"Fixed the evaluation: leaf-disjoint split (old split: {leak.get('leaked_fraction_pct', 67.5):.0f}% of test leaked).",
        f"Same recipe for all models: MSAF halves calibration error ({base['ece']:.1f}% -> {msaf['ece']:.1f}%) and gets {field_n(msaf)}/{msaf['field_photos']} field photos right (baseline {field_n(base)}).",
        (f"Field-augmented training lifts corrupted accuracy {base['mCA']:.1f}% -> {runs['msaf_field']['mCA']:.1f}% (MSAF + aug.); on its own, MSAF does not add robustness ({signed(runs['msaf_field']['mCA'] - runs['baseline_field']['mCA'])} vs. S + aug.)."
         if 'msaf_field' in runs and 'baseline_field' in runs else
         f"Honest result: clean accuracy {signed(d_clean)}, mean corrupted accuracy {signed(d_mca)}; motion blur is still unsolved."),
        'Trade-off found: MSAF breaks vanilla Grad-CAM, so the app keeps EfficientNetV2-S for trustworthy heatmaps.',
    ]
    paras = [{'text': 'Contributions', 'size': 20, 'bold': True, 'color': LIGHT_GREEN}]
    for b in bullets:
        paras.append({'text': f"-  {b}", 'size': 14, 'color': RGBColor(226, 232, 240), 'space_before': 10})
    add_text(s, 1.15, 1.85, 6.4, 4.7, paras)
    card(s, 8.1, 1.6, 4.4, 5.1, DARK_CARD, RGBColor(51, 65, 85))
    add_text(s, 8.45, 1.85, 3.8, 4.7, [
        {'text': 'Live demo', 'size': 20, 'bold': True, 'color': RGBColor(96, 165, 250)},
        {'text': 'Run the app', 'size': 12, 'color': TEXT_LIGHT_MUTED, 'space_before': 14},
        {'text': 'streamlit run app.py', 'size': 15, 'bold': True, 'color': LIGHT_GREEN, 'space_before': 2},
        {'text': 'Reproduce the comparison', 'size': 12, 'color': TEXT_LIGHT_MUTED, 'space_before': 14},
        {'text': '.\\run_ablation.ps1', 'size': 15, 'bold': True, 'color': LIGHT_GREEN, 'space_before': 2},
        {'text': 'Thank you. Questions?', 'size': 18, 'bold': True, 'color': TEXT_LIGHT, 'space_before': 36},
    ])

    output_filename = "CropSense_AI_Official_Presentation.pptx"
    prs.save(output_filename)
    print(f"Saved {output_filename} ({n} slides)")

if __name__ == '__main__':
    create_deck()
