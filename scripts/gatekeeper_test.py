"""
Open-world check: feeds non-leaf images to the full pipeline (gatekeeper + classifier) and to the bare
classifier, and records what each one answers. Writes results/gatekeeper_test.json.
Run from the project root:  python scripts/gatekeeper_test.py
"""
import os
import sys
import json

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.predict import CropDiseasePredictor

def test_images():
    rng = np.random.default_rng(0)
    tests = {}
    doc = Image.new('RGB', (800, 1000), 'white')
    d = ImageDraw.Draw(doc)
    for y in range(40, 960, 28):
        d.text((40, y), 'Lorem ipsum dolor sit amet, consectetur adipiscing elit ' * 2, fill='black')
    tests['Text document'] = doc

    sc = Image.new('RGB', (1280, 720), (245, 245, 245))
    d = ImageDraw.Draw(sc)
    d.rectangle([0, 0, 1280, 60], fill=(30, 41, 59))
    d.rectangle([40, 100, 600, 400], fill=(255, 255, 255), outline=(200, 200, 200))
    d.rectangle([660, 100, 1240, 400], fill=(59, 130, 246))
    d.rectangle([40, 440, 1240, 680], fill=(255, 255, 255))
    tests['App screenshot'] = sc

    tests['Blank grey surface'] = Image.fromarray(np.full((600, 600, 3), 128, np.uint8))
    tests['Random noise'] = Image.fromarray(rng.integers(0, 255, (600, 600, 3), dtype=np.uint8))

    sky = np.zeros((600, 600, 3), np.uint8)
    sky[..., 2] = np.linspace(255, 180, 600)[:, None]
    sky[..., 1] = 160
    sky[..., 0] = 90
    tests['Blue sky'] = Image.fromarray(sky)

    leaf = Image.open('sample_images/corn healthy.jpg').convert('RGB').resize((300, 300))
    leaf2 = Image.open('sample_images/healthy apple.png').convert('RGB').resize((300, 300))
    col = Image.new('RGB', (640, 640), (20, 20, 20))
    for pos, im in (((10, 10), leaf), ((330, 330), leaf2), ((330, 10), leaf2), ((10, 330), leaf)):
        col.paste(im, pos)
    tests['Four-leaf collage'] = col
    return tests

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = CropDiseasePredictor()
    rows = []
    for name, img in test_images().items():
        r = p.predict(img)
        t = p.transform(img.convert('RGB')).unsqueeze(0).to(p.device)
        with torch.no_grad():
            probs = F.softmax(p.model(t), 1)[0]
        conf, idx = probs.max(0)
        top = r['top_predictions'][0] if r['top_predictions'] else None
        rows.append({
            'image': name,
            'pipeline_valid': bool(r['is_valid_leaf']),
            'pipeline_code': r['error_code'],
            'pipeline_prediction': top['class'] if top else None,
            'pipeline_confidence': round(top['confidence'], 1) if top else None,
            'bare_classifier_prediction': p.class_names[idx],
            'bare_classifier_confidence': round(100 * conf.item(), 1),
        })
        print(rows[-1])
    os.makedirs('results', exist_ok=True)
    with open('results/gatekeeper_test.json', 'w') as f:
        json.dump({'model': 'models/best_model.pth (EfficientNetV2-S, deployed)', 'tests': rows}, f, indent=2)
    print('Saved results/gatekeeper_test.json')
