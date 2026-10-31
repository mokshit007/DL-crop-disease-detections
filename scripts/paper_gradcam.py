"""
Fig. 7 of the paper: Grad-CAM heatmaps and severity estimates of the leaf-disjoint
EfficientNetV2-S on unseen test leaves and on field photos.
Output: results/paper/figs/fig7_gradcam.png
Run from crop-disease-detection/:  python -m scripts.paper_gradcam
"""
import os

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from scripts.paper_figures import COL, save, plt
from src.gradcam import GradCAM
from src.model import get_model
from src.severity import SeverityEngine
from src.splits import load_split
from src.train import build_transforms

# (image, true class, short title); test leaves first, then two field photos
SAMPLES = [
    ('test', 'Apple___Apple_scab', 'Apple scab'),
    ('test', 'Tomato___Septoria_leaf_spot', 'Tomato Septoria'),
    ('test', 'Corn_(maize)___Common_rust_', 'Corn common rust'),
    ('field', 'Early-blight-potato.jpg', 'Potato early blight*'),
    ('field', 'GrayLeafSpot.jpg', 'Corn gray leaf spot*'),
]


def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    manifest = load_split()
    names = manifest['class_names']
    _, eval_tf = build_transforms()
    model = get_model(len(names), arch='baseline', pretrained=False).to(device)
    model.load_state_dict(torch.load('models/baseline.pth', map_location=device, weights_only=True))
    cam = GradCAM(model.eval())

    images = []
    for source, key, title in SAMPLES:
        if source == 'test':
            rel = next(p for p, l in manifest['test'] if names[l] == key)
            path = os.path.join('data/processed', rel)
        else:
            path = os.path.join('sample_images', key)
        images.append((Image.open(path).convert('RGB'), title))

    fig, axes = plt.subplots(2, len(images), figsize=(COL, 1.72))
    for j, (img, title) in enumerate(images):
        x = eval_tf(img).unsqueeze(0).to(device).requires_grad_(True)
        heat, idx, logits = cam.generate_heatmap(x)
        conf = 100 * F.softmax(logits.float(), dim=1)[0, idx].item()
        crop = img.resize((256, int(256 * img.height / img.width))) if img.width < img.height else img.resize((int(256 * img.width / img.height), 256))
        left, top = (crop.width - 224) // 2, (crop.height - 224) // 2
        crop = crop.crop((left, top, left + 224, top + 224))
        overlay = cam.overlay_heatmap(crop, heat, alpha=0.45)
        sev = SeverityEngine.calculate_severity(crop, heat, names[idx])
        axes[0, j].imshow(crop)
        axes[1, j].imshow(overlay)
        axes[0, j].set_title(title, fontsize=5.8, pad=2)
        short = names[idx].split('___')[1].replace('_', ' ').replace('Northern Leaf Blight', 'N. leaf blight').replace('Septoria leaf spot', 'Septoria spot')
        axes[1, j].set_xlabel(f'{short}\n{conf:.0f}% conf., sev. {sev["severity_pct"]:.0f}%', fontsize=5.3, labelpad=1.5)
        for ax in axes[:, j]:
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_linewidth(0.4)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.17, wspace=0.05, hspace=0.06)
    save(fig, 'fig7_gradcam')


if __name__ == '__main__':
    main()
