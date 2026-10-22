"""
Architecture comparison on the leaf-disjoint test split.

For every trained checkpoint in models/{baseline,cbam,msaf}.pth this measures:
  - clean test accuracy and macro-F1
  - accuracy under six field corruptions (mean = "mCA", mean Corruption Accuracy)
  - calibration (Expected Calibration Error, 15 bins)
  - accuracy and true-class confidence on the real field photos in sample_images/
  - parameters and single-image latency
Writes results/ablation_results.json and results/ablation_robustness.png.
"""
import os
import io
import json
import time

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.model import get_model
from src.splits import load_split
from src.train import build_transforms

# Run name -> label. The architecture is the part before "_" ("msaf_field" = MSAF trained with --field-aug).
RUNS = [
    ('baseline', 'EfficientNetV2-S (baseline)'),
    ('cbam', 'EfficientNetV2-S + CBAM'),
    ('msaf', 'EfficientNetV2-MSAF (proposed)'),
    ('baseline_field', 'EfficientNetV2-S + field aug.'),
    ('msaf_field', 'EfficientNetV2-MSAF + field aug.'),
]

# Corruptions also used as training augmentation by --field-aug (the rest stay unseen for every model)
SEEN_IN_FIELD_AUG = ('Gaussian blur', 'Sensor noise')

RUN_COLORS = {'baseline': '#94A3B8', 'cbam': '#3B82F6', 'msaf': '#059669',
              'baseline_field': '#475569', 'msaf_field': '#065F46'}

FIELD_PHOTOS = {
    'Apple Scab.jpg': 'Apple___Apple_scab',
    'Early-blight-potato.jpg': 'Potato___Early_blight',
    'GrayLeafSpot.jpg': 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
    'Powdery mildew_1.png': 'Squash___Powdery_mildew',
    'bell pepper bactiral.jpg': 'Pepper,_bell___Bacterial_spot',
    'bell-pepper healthy.png': 'Pepper,_bell___healthy',
    'corn healthy.jpg': 'Corn_(maize)___healthy',
    'healthy apple.png': 'Apple___healthy',
}

# ---- Field corruptions (deterministic per image via the seed argument) ----
def gaussian_blur(img, rng):
    return img.filter(ImageFilter.GaussianBlur(radius=2.5))

def motion_blur(img, rng):
    k = np.zeros((15, 15), np.float32)
    k[7, :] = 1.0 / 15
    angle = rng.uniform(0, 180)
    rot = cv2.getRotationMatrix2D((7, 7), angle, 1.0)
    k = cv2.warpAffine(k, rot, (15, 15))
    k /= max(k.sum(), 1e-6)
    return Image.fromarray(cv2.filter2D(np.array(img), -1, k))

def sensor_noise(img, rng):
    arr = np.array(img).astype(np.float32)
    return Image.fromarray(np.clip(arr + rng.normal(0, 25, arr.shape), 0, 255).astype(np.uint8))

def low_light(img, rng):
    arr = np.array(img).astype(np.float32) * 0.35
    return Image.fromarray(np.clip(arr + rng.normal(0, 8, arr.shape), 0, 255).astype(np.uint8))

def jpeg_artifacts(img, rng):
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=10)
    return Image.open(io.BytesIO(buf.getvalue())).convert('RGB')

def overexposure(img, rng):
    arr = np.array(img).astype(np.float32)
    return Image.fromarray(np.clip(arr * 1.45 + 30, 0, 255).astype(np.uint8))

CORRUPTIONS = {
    'Gaussian blur': gaussian_blur,
    'Motion blur': motion_blur,
    'Sensor noise': sensor_noise,
    'Low light': low_light,
    'JPEG (q=10)': jpeg_artifacts,
    'Overexposure': overexposure,
}

class CorruptedDataset(Dataset):
    def __init__(self, samples, transform, corruption=None, root='data/processed'):
        self.samples, self.transform, self.corruption, self.root = samples, transform, corruption, root

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        rel_path, label = self.samples[idx]
        img = Image.open(os.path.join(self.root, rel_path)).convert('RGB')
        if self.corruption is not None:
            img = self.corruption(img, np.random.default_rng(idx))
        return self.transform(img), label

@torch.no_grad()
def predict_probs(model, loader, device):
    probs, labels = [], []
    for x, y in loader:
        with torch.amp.autocast('cuda', enabled=device.type == 'cuda'):
            out = model(x.to(device, non_blocking=True))
        probs.append(F.softmax(out.float(), dim=1).cpu())
        labels.append(y)
    return torch.cat(probs).numpy(), torch.cat(labels).numpy()

def expected_calibration_error(probs, labels, bins=15):
    conf, pred = probs.max(1), probs.argmax(1)
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            ece += m.mean() * abs((pred[m] == labels[m]).mean() - conf[m].mean())
    return ece

def latency_ms(model, device, runs=30):
    x = torch.randn(1, 3, 224, 224, device=device)
    with torch.no_grad():
        for _ in range(5):
            model(x)
        if device.type == 'cuda':
            torch.cuda.synchronize()
        t = time.perf_counter()
        for _ in range(runs):
            model(x)
        if device.type == 'cuda':
            torch.cuda.synchronize()
    return (time.perf_counter() - t) / runs * 1000

def compare(batch_size=64, num_workers=3, runs=RUNS, ckpt_fmt='models/{}.pth', limit=None, out_dir='results', reuse=True):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    manifest = load_split()
    class_names = manifest['class_names']
    _, eval_tf = build_transforms()
    test = manifest['test'][::max(1, len(manifest['test']) // limit)] if limit else manifest['test']

    results = {'test_images': len(test), 'runs': {}}
    out_json = os.path.join(out_dir, 'ablation_results.json')
    previous = {}
    if reuse and os.path.exists(out_json):
        with open(out_json) as f:
            prev = json.load(f)
        if prev.get('test_images') == len(test):
            previous = prev['runs']
    for name, label in runs:
        arch = name.split('_')[0]
        ckpt = ckpt_fmt.format(name)
        if not os.path.exists(ckpt):
            print(f"Skipping {name}: {ckpt} not found")
            continue
        if name in previous and os.path.getmtime(ckpt) < os.path.getmtime(out_json):
            print(f"Reusing earlier results for {name}")
            results['runs'][name] = {**previous[name], 'label': label}
            continue
        model = get_model(len(class_names), arch=arch, pretrained=False).to(device)
        model.load_state_dict(torch.load(ckpt, map_location=device, weights_only=True))
        model.eval()
        r = {'label': label, 'params': sum(p.numel() for p in model.parameters())}

        def loader(corruption=None):
            return DataLoader(CorruptedDataset(test, eval_tf, corruption), batch_size=batch_size,
                              num_workers=num_workers, pin_memory=True)

        probs, labels = predict_probs(model, loader(), device)
        r['clean_acc'] = round(100 * (probs.argmax(1) == labels).mean(), 2)
        r['clean_macro_f1'] = round(100 * f1_score(labels, probs.argmax(1), average='macro'), 2)
        r['ece'] = round(100 * expected_calibration_error(probs, labels), 2)
        print(f"[{name}] clean acc {r['clean_acc']}%  macro-F1 {r['clean_macro_f1']}%  ECE {r['ece']}%", flush=True)

        r['corruptions'] = {}
        for cname, fn in CORRUPTIONS.items():
            p, l = predict_probs(model, loader(fn), device)
            r['corruptions'][cname] = round(100 * (p.argmax(1) == l).mean(), 2)
            print(f"[{name}]   {cname:14s} {r['corruptions'][cname]}%", flush=True)
        r['mCA'] = round(float(np.mean(list(r['corruptions'].values()))), 2)

        field_correct, field_conf = [], []
        for fname, cls in FIELD_PHOTOS.items():
            img = Image.open(os.path.join('sample_images', fname)).convert('RGB')
            with torch.no_grad():
                p = F.softmax(model(eval_tf(img).unsqueeze(0).to(device)).float(), dim=1)[0].cpu().numpy()
            idx = class_names.index(cls)
            field_correct.append(int(p.argmax() == idx))
            field_conf.append(float(p[idx]))
        r['field_acc'] = round(100 * np.mean(field_correct), 1)
        r['field_true_class_conf'] = round(100 * np.mean(field_conf), 1)
        r['field_photos'] = len(FIELD_PHOTOS)

        r['gpu_latency_ms'] = round(latency_ms(model, device), 2) if device.type == 'cuda' else None
        r['cpu_latency_ms'] = round(latency_ms(model.cpu(), torch.device('cpu'), runs=10), 1)

        hist_path = f'results/history_{name}.json'
        if os.path.exists(hist_path):
            with open(hist_path) as f:
                r['best_val_acc'] = round(json.load(f)['best_val_acc'], 2)
        print(f"[{name}] mCA {r['mCA']}%  field {r['field_acc']}% (true-class conf {r['field_true_class_conf']}%)", flush=True)
        results['runs'][name] = r
        del model
        if device.type == 'cuda':
            torch.cuda.empty_cache()

    os.makedirs(out_dir, exist_ok=True)
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=4)
    plot(results, os.path.join(out_dir, 'ablation_robustness.png'), keys=('baseline', 'cbam', 'msaf'))
    plot(results, os.path.join(out_dir, 'field_aug_robustness.png'), keys=('baseline', 'baseline_field', 'msaf', 'msaf_field'),
         title='Effect of field-augmented training (Gaussian blur + sensor noise seen in training)')
    return results

def plot(results, out_path='results/ablation_robustness.png', keys=None, title='Leaf-disjoint test accuracy under field corruptions'):
    runs = {k: results['runs'][k] for k in (keys or results['runs']) if k in results['runs']}
    if not runs:
        return
    conds = ['Clean'] + list(CORRUPTIONS)
    colors = RUN_COLORS
    x = np.arange(len(conds))
    width = 0.8 / max(1, len(runs))
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=200)
    for i, (arch, r) in enumerate(runs.items()):
        vals = [r['clean_acc']] + [r['corruptions'][c] for c in CORRUPTIONS]
        bars = ax.bar(x + (i - (len(runs) - 1) / 2) * width, vals, width, label=r['label'], color=colors.get(arch, '#64748B'))
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.0f}", ha='center', va='bottom', fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(conds, fontsize=9)
    ax.set_ylabel('Test accuracy (%)')
    lo = min(min([r['clean_acc']] + list(r['corruptions'].values())) for r in runs.values())
    ax.set_ylim(max(0, lo - 10), 104)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=min(len(runs), 4))
    ax.set_title(title, fontsize=12, fontweight='bold', pad=28)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=3)
    compare(num_workers=parser.parse_args().workers)
