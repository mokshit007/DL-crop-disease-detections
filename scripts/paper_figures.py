"""
Figures for the research paper (IEEE two-column: one column = 3.5 in, full width = 7.16 in).

Diagrams (Fig. 1, Fig. 2) are drawn from the project's real configuration; result plots read
results/paper/metrics.json (scripts/paper_analysis.py) and results/history_*.json.
Output: results/paper/figs/*.png at 600 dpi.
Run from crop-disease-detection/:  python -m scripts.paper_figures
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

FIG_DIR = 'results/paper/figs'
DPI = 600
COL, FULL = 3.5, 7.16

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'mathtext.fontset': 'stix',
    'font.size': 7.5, 'axes.titlesize': 7.5, 'axes.labelsize': 7.5, 'xtick.labelsize': 6.8, 'ytick.labelsize': 6.8,
    'legend.fontsize': 6.6, 'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'lines.linewidth': 1.2, 'savefig.dpi': DPI, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.02,
})

# One colour per run, kept identical in every figure (Okabe-Ito based, colour-blind safe)
RUN_STYLE = {
    'baseline':       {'label': 'EfficientNetV2-S',              'color': '#7F7F7F', 'marker': 'o'},
    'cbam':           {'label': 'EfficientNetV2-S + CBAM',        'color': '#0072B2', 'marker': 's'},
    'msaf':           {'label': 'EfficientNetV2-MSAF',            'color': '#009E73', 'marker': '^'},
    'baseline_field': {'label': 'EfficientNetV2-S + FA',          'color': '#E69F00', 'marker': 'D'},
    'msaf_field':     {'label': 'EfficientNetV2-MSAF + FA (ours)', 'color': '#D55E00', 'marker': 'v'},
}
RUNS = tuple(RUN_STYLE)

INK = '#1A1A1A'
FILL = {'data': '#E8F1FA', 'proc': '#F2F2F2', 'model': '#E6F4EE', 'out': '#FDF0E6', 'reject': '#FBE9E9', 'attn': '#FFF6D9'}


def box(ax, x, y, w, h, text, kind='proc', size=6.6, bold_first=True, ls='-'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.06', linewidth=0.7,
                                edgecolor=INK, facecolor=FILL[kind], linestyle=ls))
    # Axes units are inches, so a line of `size` pt is size * 1.25 / 72 in tall; the first line is the bold title
    lines = text.split('\n')
    step = size * 1.25 / 72
    top = y + h / 2 + (len(lines) - 1) * step / 2
    for i, line in enumerate(lines):
        ax.text(x + w / 2, top - i * step, line, ha='center', va='center', fontsize=size, color=INK,
                fontweight='bold' if (i == 0 and bold_first) else 'normal')


def arrow(ax, x0, y0, x1, y1, text=None, rad=0.0, ls='-', tx=0, ty=0.05, size=6.0):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>', mutation_scale=7, linewidth=0.7, color=INK,
                                 connectionstyle=f'arc3,rad={rad}', linestyle=ls, shrinkA=0, shrinkB=0))
    if text:
        ax.text((x0 + x1) / 2 + tx, (y0 + y1) / 2 + ty, text, ha='center', va='bottom', fontsize=size, color=INK,
                style='italic')


def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis('off')
    return fig, ax


def lane_label(ax, x, y, h, text):
    ax.text(x, y + h / 2, text, rotation=90, ha='center', va='center', fontsize=6.8, fontweight='bold', color='#404040')


def fig_methodology():
    """Fig. 1: model development (top lane) and deployed diagnosis pipeline (bottom lane)."""
    fig, ax = canvas(FULL, 2.25)
    h = 0.62
    # Lane A: model development
    ya = 1.45
    ax.add_patch(FancyBboxPatch((0.02, ya - 0.12), FULL - 0.04, h + 0.24, boxstyle='round,pad=0,rounding_size=0.05',
                                linewidth=0.5, edgecolor='#9A9A9A', facecolor='none', linestyle=(0, (3, 2))))
    lane_label(ax, 0.16, ya, h, '(a) Development')
    w = 1.5
    xs = [0.32, 2.07, 3.82, 5.57]
    box(ax, xs[0], ya, w, h, 'PlantVillage (Kaggle, augmented)\n87,867 images, 14 crops\n38 classes', 'data')
    box(ax, xs[1], ya, w, h, 'Leakage audit + leaf-grouped split\n70,146 / 8,832 / 8,889 images\nzero leaf overlap', 'proc')
    box(ax, xs[2], ya, w, h, 'Training (identical recipe)\nV2-S | V2-S+CBAM | V2-MSAF\n± field augmentation (FA)', 'model')
    box(ax, xs[3], ya, w, h, 'Evaluation\nclean, 6 corruptions, ECE,\nselective risk, field photos', 'out')
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, a + w, ya + h / 2, b, ya + h / 2)

    # Lane B: deployed pipeline
    yb = 0.2
    ax.add_patch(FancyBboxPatch((0.02, yb - 0.12), FULL - 0.04, h + 0.47, boxstyle='round,pad=0,rounding_size=0.05',
                                linewidth=0.5, edgecolor='#9A9A9A', facecolor='none', linestyle=(0, (3, 2))))
    lane_label(ax, 0.16, yb + 0.1, h + 0.1, '(b) Diagnosis')
    w2 = 1.08
    box(ax, 0.32, yb + 0.12, w2, h, 'Leaf photo\nupload or\nlive camera', 'data')
    box(ax, 1.62, yb + 0.12, w2, h, 'Leaf gatekeeper\nHSV plant-pixel\nratio, leaf count', 'proc')
    box(ax, 1.62, yb + 0.12 + h + 0.12, w2, 0.3, 'Reject: non-leaf /\nmulti-leaf image', 'reject', size=5.8, bold_first=False)
    box(ax, 2.92, yb + 0.12, w2, h, 'Classifier\nEfficientNetV2\n38-way softmax', 'model')
    box(ax, 4.22, yb + 0.47, w2, 0.4, 'Grad-CAM\nlesion heatmap', 'proc', size=6.2)
    box(ax, 4.22, yb - 0.02, w2, 0.4, 'Treatment KB\n38 classes', 'proc', size=6.2)
    box(ax, 5.52, yb + 0.47, 0.75, 0.4, 'Severity\nstage 0–4', 'proc', size=6.2)
    box(ax, 6.42, yb + 0.12, 0.66, h, 'Report\nclass, conf.,\nheatmap,\nadvice', 'out', size=6.0)
    arrow(ax, 0.32 + w2, yb + 0.12 + h / 2, 1.62, yb + 0.12 + h / 2)
    arrow(ax, 1.62 + w2, yb + 0.12 + h / 2, 2.92, yb + 0.12 + h / 2, 'valid', ty=0.02)
    arrow(ax, 1.62 + w2 / 2, yb + 0.12 + h, 1.62 + w2 / 2, yb + 0.12 + h + 0.12)
    arrow(ax, 2.92 + w2, yb + 0.12 + h / 2 + 0.1, 4.22, yb + 0.67)
    arrow(ax, 2.92 + w2, yb + 0.12 + h / 2 - 0.1, 4.22, yb + 0.18)
    arrow(ax, 4.22 + w2, yb + 0.67, 5.52, yb + 0.67)
    arrow(ax, 5.52 + 0.75, yb + 0.67, 6.42, yb + 0.12 + h / 2 + 0.12)
    arrow(ax, 4.22 + w2, yb + 0.18, 6.42, yb + 0.12 + h / 2 - 0.12)
    save(fig, 'fig1_methodology')


def fig_architecture():
    """Fig. 2: EfficientNetV2-MSAF."""
    fig, ax = canvas(FULL, 2.45)
    # Backbone row
    yb, hb = 1.72, 0.52
    stages = [('Input', '224×224×3'), ('Stem', '112²×24'), ('Stage 1\nF-MBConv', '112²×24'),
              ('Stage 2\nF-MBConv', '56²×48'), ('Stage 3\nF-MBConv', '28²×64'), ('Stage 4\nMBConv', '14²×128'),
              ('Stage 5\nMBConv', '14²×160'), ('Stage 6\nMBConv', '7²×256'), ('Head\n1×1 conv', '7²×1280')]
    w, gap, x0 = 0.64, 0.14, 0.08
    centers = []
    for i, (name, size) in enumerate(stages):
        x = x0 + i * (w + gap)
        kind = 'data' if i == 0 else ('model' if i in (4, 6, 8) else 'proc')
        box(ax, x, yb, w, hb, name, kind, size=6.2, bold_first=True)
        ax.text(x + w / 2, yb - 0.075, size, ha='center', va='top', fontsize=5.9, color='#333333')
        centers.append(x + w / 2)
        if i:
            arrow(ax, x - gap, yb + hb / 2, x, yb + hb / 2)
    ax.text(x0 + 4 * (w + gap) - 0.05, yb + hb + 0.1, 'EfficientNetV2-S backbone (ImageNet-pretrained)', fontsize=6.6,
            fontweight='bold', color='#404040', ha='center')

    # Three branches
    yr = 0.98
    taps = [(4, '64'), (6, '160'), (8, '1280')]
    bw, bh, st = 0.46, 0.3, 0.58
    branch_x = [1.05, 3.05, 5.05]
    for (si, dim), bx in zip(taps, branch_x):
        cx = centers[si]
        ax.add_patch(FancyArrowPatch((cx, yb - 0.2), (bx + bw / 2, yr + bh), arrowstyle='-|>', mutation_scale=7,
                                     linewidth=0.7, color=INK, connectionstyle='arc3,rad=0'))
        box(ax, bx, yr, bw, bh, 'CBAM', 'attn', size=6.0)
        box(ax, bx + st, yr, bw, bh, 'GeM', 'proc', size=6.0)
        box(ax, bx + 2 * st, yr, bw, bh, 'LN', 'proc', size=6.0)
        arrow(ax, bx + bw, yr + bh / 2, bx + st, yr + bh / 2)
        arrow(ax, bx + st + bw, yr + bh / 2, bx + 2 * st, yr + bh / 2)
        ax.text(bx + 2 * st + bw + 0.05, yr + bh / 2, f'{dim}-d', ha='left', va='center', fontsize=6.0)
        arrow(ax, bx + 2 * st + bw / 2, yr, 3.6, 0.53)
    box(ax, 3.0, 0.2, 1.2, 0.33, 'Scale-dropout + concat\n1504-d descriptor', 'model', size=6.0, bold_first=False)
    box(ax, 4.45, 0.2, 1.05, 0.33, 'Dropout 0.3\nFC 1504→38', 'proc', size=6.0, bold_first=False)
    box(ax, 5.75, 0.2, 0.75, 0.33, 'Softmax\n38 classes', 'out', size=6.0, bold_first=False)
    arrow(ax, 4.2, 0.365, 4.45, 0.365)
    arrow(ax, 5.5, 0.365, 5.75, 0.365)

    # CBAM inset (left)
    ix, iy = 0.08, 0.06
    ax.add_patch(FancyBboxPatch((ix, iy), 2.75, 0.62, boxstyle='round,pad=0,rounding_size=0.05', linewidth=0.5,
                                edgecolor='#9A9A9A', facecolor='#FFFCF2', linestyle=(0, (3, 2))))
    ax.text(ix + 0.06, iy + 0.53, 'CBAM block (residual)', fontsize=6.2, fontweight='bold', va='center')
    ax.text(ix + 0.06, iy + 0.37, r'$M_c$: AvgPool, MaxPool $\rightarrow$ shared MLP $\rightarrow \sigma$', fontsize=5.9, va='center')
    ax.text(ix + 0.06, iy + 0.22, r'$M_s$: [mean$_c$; max$_c$] $\rightarrow$ 7$\times$7 conv $\rightarrow \sigma$', fontsize=5.9, va='center')
    ax.text(ix + 0.06, iy + 0.03, r'out $= F + M_s(F^{\prime}) \otimes F^{\prime}$,  $F^{\prime} = M_c(F) \otimes F$', fontsize=5.9, va='bottom')
    save(fig, 'fig2_architecture')


def load_metrics():
    with open('results/paper/metrics.json') as f:
        return json.load(f)


def style_axes(ax):
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', linestyle=':', linewidth=0.5, color='#B0B0B0')
    ax.set_axisbelow(True)


def fig_training(m):
    """Fig. 3: validation accuracy and training loss per epoch."""
    fig, axes = plt.subplots(1, 2, figsize=(COL, 1.45))
    for run in RUNS:
        t, s = m['training'][run], RUN_STYLE[run]
        ep = np.arange(1, len(t['val_acc']) + 1)
        axes[0].plot(ep, t['val_acc'], color=s['color'], marker=s['marker'], markersize=2.6, linewidth=0.9)
        axes[1].plot(ep, t['train_loss'], color=s['color'], marker=s['marker'], markersize=2.6, linewidth=0.9, label=s['label'])
    axes[0].set_ylabel('Val. accuracy (%)')
    axes[1].set_ylabel('Training loss')
    for ax, tag in zip(axes, '(a)(b)'.replace(')(', ') (').split()):
        ax.set_xlabel('Epoch')
        ax.set_xticks(range(1, 9))
        style_axes(ax)
        ax.text(0.03 if tag == '(a)' else 0.86, 0.04 if tag == '(a)' else 0.86, tag, transform=ax.transAxes, fontsize=7, fontweight='bold')
    axes[0].set_ylim(88, 100.3)
    fig.tight_layout(w_pad=1.0, rect=(0, 0, 1, 0.8))
    fig.legend(*axes[1].get_legend_handles_labels(), loc='upper center', ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 1.01), handlelength=1.6, columnspacing=0.9, fontsize=6.0)
    save(fig, 'fig3_training')


def fig_robustness(m):
    """Fig. 4: test accuracy per corruption for the five models."""
    conds = m['conditions']
    fig, ax = plt.subplots(figsize=(FULL, 1.75))
    x = np.arange(len(conds))
    width = 0.16
    for i, run in enumerate(RUNS):
        s = RUN_STYLE[run]
        vals = [m['runs'][run]['acc'][c] for c in conds]
        bars = ax.bar(x + (i - 2) * width, vals, width * 0.92, color=s['color'], label=s['label'], linewidth=0)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.6, f'{v:.0f}', ha='center', va='bottom', fontsize=5.2, color='#333333')
    ax.set_xticks(x)
    ax.set_xticklabels(['Clean'] + [c.replace(' (q=10)', ' (q = 10)') for c in conds[1:]])
    ax.set_ylabel('Test accuracy (%)')
    ax.set_ylim(40, 104)
    style_axes(ax)
    ax.axvline(0.5, color='#9A9A9A', linewidth=0.6, linestyle='--')
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=5, frameon=False, handlelength=1.2, columnspacing=1.2)
    fig.tight_layout()
    save(fig, 'fig4_robustness')


def fig_calibration(m):
    """Fig. 5: (a) reliability diagram on clean test images, (b) ECE before / after temperature scaling."""
    fig, axes = plt.subplots(1, 2, figsize=(COL, 1.65), gridspec_kw={'width_ratios': [1, 1.25]})
    ax = axes[0]
    ax.plot([0, 1], [0, 1], color='#9A9A9A', linewidth=0.7, linestyle='--', label='Perfect')
    for run in ('baseline', 'msaf', 'msaf_field'):
        s = RUN_STYLE[run]
        rows = [r for r in m['runs'][run]['reliability_clean'] if r['count'] >= 20]
        ax.plot([r['conf'] for r in rows], [r['acc'] for r in rows], color=s['color'], marker=s['marker'], markersize=2.8,
                linewidth=0.9, label=s['label'].replace('EfficientNetV2-', 'V2-').replace(' (ours)', ''))
    ax.set_xlim(0.3, 1.0)
    ax.set_ylim(0.3, 1.02)
    ax.set_xlabel('Confidence')
    ax.set_ylabel('Accuracy')
    ax.legend(loc='lower right', bbox_to_anchor=(1.02, 0.0), frameon=True, framealpha=0.9, edgecolor='none', fontsize=5.4, handlelength=1.2)
    style_axes(ax)
    ax.text(0.04, 0.9, '(a)', transform=ax.transAxes, fontsize=7, fontweight='bold')

    ax = axes[1]
    x = np.arange(len(RUNS))
    raw_c = [m['runs'][r]['ece']['Clean'] for r in RUNS]
    ts_c = [m['runs'][r]['ece_ts']['Clean'] for r in RUNS]
    raw_s = [m['runs'][r]['ece_corrupted_mean'] for r in RUNS]
    ts_s = [m['runs'][r]['ece_ts_corrupted_mean'] for r in RUNS]
    w = 0.2
    ax.bar(x - 1.5 * w, raw_c, w, color='#4D4D4D', label='Clean, raw')
    ax.bar(x - 0.5 * w, ts_c, w, color='#BDBDBD', label='Clean, TS')
    ax.bar(x + 0.5 * w, raw_s, w, color='#0072B2', label='Corrupted, raw')
    ax.bar(x + 1.5 * w, ts_s, w, color='#9CC9E6', label='Corrupted, TS')
    ax.set_xticks(x)
    ax.set_xticklabels(['V2-S', 'CBAM', 'MSAF', 'V2-S\n+FA', 'MSAF\n+FA'], fontsize=5.6)
    ax.set_ylabel('ECE (%)')
    style_axes(ax)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=5.4, handlelength=0.9, ncol=2, columnspacing=0.7)
    ax.set_ylim(0, 13)
    ax.text(0.85, 0.9, '(b)', transform=ax.transAxes, fontsize=7, fontweight='bold')
    fig.tight_layout(w_pad=0.6)
    save(fig, 'fig5_calibration')


def fig_selective(m):
    """Fig. 6: risk-coverage on the pooled corrupted test set."""
    fig, ax = plt.subplots(figsize=(COL, 1.6))
    for run in RUNS:
        s = RUN_STYLE[run]
        curve = np.array(m['runs'][run]['selective']['curve'])
        keep = curve[:, 0] >= 0.02
        ax.plot(100 * curve[keep, 0], 100 * curve[keep, 1], color=s['color'], linewidth=1.0,
                label=f"{s['label']} ({m['runs'][run]['selective']['aurc']:.2f})")
    ax.set_xlabel('Coverage (% of predictions kept, most confident first)')
    ax.set_ylabel('Error rate (%)')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 20)
    style_axes(ax)
    ax.legend(title='Model (AURC, %)', title_fontsize=5.8, loc='upper left', frameon=False, fontsize=5.6, handlelength=1.4)
    fig.tight_layout()
    save(fig, 'fig6_selective')


def save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    fig.savefig(os.path.join(FIG_DIR, name + '.png'))
    plt.close(fig)
    print('saved', name)


if __name__ == '__main__':
    fig_methodology()
    fig_architecture()
    if os.path.exists('results/paper/metrics.json'):
        metrics = load_metrics()
        fig_training(metrics)
        fig_robustness(metrics)
        fig_calibration(metrics)
        fig_selective(metrics)
