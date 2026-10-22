import os
import json
import random

import torch
from PIL import Image
from torch.utils.data import Dataset, Sampler

from src.dataset import source_leaf_id

SPLIT_PATH = 'data/splits/leaf_disjoint.json'

def build_leaf_disjoint_split(root='data/processed', out_path=SPLIT_PATH, split_ratios=(0.8, 0.1, 0.1), seed=42):
    """
    Pools data/processed/{train,val,test} and re-splits it so that every augmented copy of a
    physical leaf lands in exactly one split. Stored as a manifest of relative paths, so no
    images are copied.
    """
    class_names = sorted(os.listdir(os.path.join(root, 'train')))
    groups = {}
    for split in ('train', 'val', 'test'):
        for cls in class_names:
            cls_dir = os.path.join(root, split, cls)
            for name in sorted(os.listdir(cls_dir)):
                groups.setdefault((cls, source_leaf_id(name)), []).append(f'{split}/{cls}/{name}')

    rng = random.Random(seed)
    manifest = {'class_names': class_names, 'train': [], 'val': [], 'test': []}
    for cls_idx, cls in enumerate(class_names):
        leaf_ids = sorted(k for k in groups if k[0] == cls)
        rng.shuffle(leaf_ids)
        n_train = int(len(leaf_ids) * split_ratios[0])
        n_val = int(len(leaf_ids) * split_ratios[1])
        parts = {
            'train': leaf_ids[:n_train],
            'val': leaf_ids[n_train:n_train + n_val],
            'test': leaf_ids[n_train + n_val:],
        }
        for split, ids in parts.items():
            for key in ids:
                manifest[split].extend([p, cls_idx] for p in groups[key])

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(manifest, f)
    print({s: len(manifest[s]) for s in ('train', 'val', 'test')}, f'-> {out_path}')
    return manifest

def load_split(path=SPLIT_PATH):
    if not os.path.exists(path):
        return build_leaf_disjoint_split(out_path=path)
    with open(path) as f:
        return json.load(f)

class ManifestDataset(Dataset):
    def __init__(self, samples, transform=None, root='data/processed'):
        self.samples = samples
        self.transform = transform
        self.root = root

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        rel_path, label = self.samples[idx]
        img = Image.open(os.path.join(self.root, rel_path)).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img, label

class OneCopyPerLeafSampler(Sampler):
    """
    Each epoch yields one randomly chosen augmented copy of every source leaf, so an epoch covers
    every physical leaf once (about half the files) while all copies are still seen across epochs.
    """
    def __init__(self, samples, seed=42):
        groups = {}
        for idx, (rel_path, label) in enumerate(samples):
            groups.setdefault((label, source_leaf_id(rel_path)), []).append(idx)
        self.groups = list(groups.values())
        self.generator = torch.Generator().manual_seed(seed)

    def __len__(self):
        return len(self.groups)

    def __iter__(self):
        order = torch.randperm(len(self.groups), generator=self.generator).tolist()
        for g in order:
            members = self.groups[g]
            yield members[torch.randint(len(members), (1,), generator=self.generator).item()]

if __name__ == '__main__':
    build_leaf_disjoint_split()
