"""
Evaluation pass for the research paper.

Caches the logits of every trained checkpoint on
  - the leaf-disjoint validation set (clean),
  - the leaf-disjoint test set, clean and under the six corruptions of src/compare.py
    (same functions, same per-image seeds, so accuracies match results/ablation_results.json),
  - the eight field photos in sample_images/,
and measures parameters, MACs and single-image latency of each architecture in one session.

Outputs: results/paper/logits.npz, results/paper/efficiency.json
Run from crop-disease-detection/:  python -m scripts.paper_eval
"""
import os
import json
import time

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torch.utils.flop_counter import FlopCounterMode

from src.model import get_model
from src.splits import load_split
from src.train import build_transforms
from src.compare import CORRUPTIONS, CorruptedDataset, FIELD_PHOTOS, latency_ms

RUNS = ('baseline', 'cbam', 'msaf', 'baseline_field', 'msaf_field')
CONDITIONS = ('Clean',) + tuple(CORRUPTIONS)
OUT_DIR = 'results/paper'


class AllConditions(Dataset):
    """Returns the clean image and its six corrupted versions, stacked: [7, 3, 224, 224]."""
    def __init__(self, samples, transform, root='data/processed'):
        self.samples, self.transform, self.root = samples, transform, root

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        rel_path, label = self.samples[idx]
        img = Image.open(os.path.join(self.root, rel_path)).convert('RGB')
        views = [self.transform(img)]
        for fn in CORRUPTIONS.values():
            views.append(self.transform(fn(img, np.random.default_rng(idx))))
        return torch.stack(views), label


def load(run, num_classes, device):
    model = get_model(num_classes, arch=run.split('_')[0], pretrained=False).to(device)
    model.load_state_dict(torch.load(f'models/{run}.pth', map_location=device, weights_only=True))
    return model.eval()


@torch.no_grad()
def forward(model, x, device):
    with torch.amp.autocast('cuda', enabled=device.type == 'cuda'):
        return model(x).float().cpu().numpy()


def main(batch_size=32, workers=8):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    manifest = load_split()
    class_names = manifest['class_names']
    _, eval_tf = build_transforms()
    test, val = manifest['test'], manifest['val']
    models = {run: load(run, len(class_names), device) for run in RUNS}
    os.makedirs(OUT_DIR, exist_ok=True)

    # Test set: clean + six corruptions, every model on the same batch
    test_logits = {run: np.zeros((len(CONDITIONS), len(test), len(class_names)), np.float32) for run in RUNS}
    loader = DataLoader(AllConditions(test, eval_tf), batch_size=batch_size, num_workers=workers, pin_memory=True)
    start, i = time.time(), 0
    for step, (xb, _) in enumerate(loader):
        xb = xb.to(device, non_blocking=True)
        for c in range(len(CONDITIONS)):
            for run, model in models.items():
                test_logits[run][c, i:i + len(xb)] = forward(model, xb[:, c], device)
        i += len(xb)
        if step % 25 == 0:
            print(f'test {i}/{len(test)}  {time.time() - start:.0f}s', flush=True)

    # Validation set: clean only (used to fit temperature scaling)
    val_logits = {run: np.zeros((len(val), len(class_names)), np.float32) for run in RUNS}
    loader = DataLoader(CorruptedDataset(val, eval_tf), batch_size=64, num_workers=workers, pin_memory=True)
    i = 0
    for xb, _ in loader:
        xb = xb.to(device, non_blocking=True)
        for run, model in models.items():
            val_logits[run][i:i + len(xb)] = forward(model, xb, device)
        i += len(xb)
    print(f'val done  {time.time() - start:.0f}s', flush=True)

    # Field photos
    field_x = torch.stack([eval_tf(Image.open(os.path.join('sample_images', f)).convert('RGB')) for f in FIELD_PHOTOS]).to(device)
    field_labels = np.array([class_names.index(c) for c in FIELD_PHOTOS.values()])

    arrays = {'labels_test': np.array([l for _, l in test]), 'labels_val': np.array([l for _, l in val]),
              'labels_field': field_labels, 'conditions': np.array(CONDITIONS), 'class_names': np.array(class_names),
              'field_files': np.array(list(FIELD_PHOTOS))}
    for run, model in models.items():
        arrays[f'{run}_test'] = test_logits[run]
        arrays[f'{run}_val'] = val_logits[run]
        arrays[f'{run}_field'] = forward(model, field_x, device)
    np.savez_compressed(os.path.join(OUT_DIR, 'logits.npz'), **arrays)

    # Sanity check against results/ablation_results.json
    with open('results/ablation_results.json') as f:
        reported = json.load(f)['runs']
    for run in RUNS:
        acc = 100 * (test_logits[run][0].argmax(1) == arrays['labels_test']).mean()
        print(f'{run:15s} clean acc {acc:.2f}% (reported {reported[run]["clean_acc"]}%)')
    del models
    torch.cuda.empty_cache()

    # Efficiency: one session, same conditions for every architecture
    eff = {}
    for arch in ('baseline', 'cbam', 'msaf'):
        model = get_model(len(class_names), arch=arch, pretrained=False).eval()
        with FlopCounterMode(display=False) as counter, torch.no_grad():
            model(torch.randn(1, 3, 224, 224))
        eff[arch] = {
            'params': sum(p.numel() for p in model.parameters()),
            'gmacs': round(counter.get_total_flops() / 2e9, 3),
            'cpu_latency_ms': round(latency_ms(model, torch.device('cpu'), runs=20), 1),
        }
        if device.type == 'cuda':
            eff[arch]['gpu_latency_ms'] = round(latency_ms(model.to(device), device, runs=100), 2)
        print(arch, eff[arch], flush=True)
    with open(os.path.join(OUT_DIR, 'efficiency.json'), 'w') as f:
        json.dump(eff, f, indent=2)
    print(f'done in {time.time() - start:.0f}s')


if __name__ == '__main__':
    main()
