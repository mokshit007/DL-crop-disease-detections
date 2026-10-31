"""
Pixel-level lesion map.

Grad-CAM shows which regions drove the classifier, at the resolution of its feature maps (14x14 / 7x7), so it
cannot outline individual spots. This module outlines the visible lesions themselves: the main leaf is
separated from the background with GrabCut (seeded at the image centre), then pixels are flagged where they
are redder / browner or markedly darker than the surrounding leaf tissue. Thin elongated detections (veins,
midribs) are discarded. It is a colour-contrast heuristic, not a trained segmentation model.
"""
import cv2
import numpy as np
from PIL import Image

WORK_SIZE = 448


def segment_leaf(img: np.ndarray) -> np.ndarray:
    """Boolean mask of the main leaf (the GrabCut foreground connected to the image centre, holes filled)."""
    H, W = img.shape[:2]
    gm = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
    cv2.ellipse(gm, (W // 2, H // 2), (int(W * 0.46), int(H * 0.46)), 0, 0, 360, cv2.GC_PR_FGD, -1)
    cv2.ellipse(gm, (W // 2, H // 2), (int(W * 0.08), int(H * 0.08)), 0, 0, 360, cv2.GC_FGD, -1)
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img[..., ::-1].copy(), gm, None, bg, fg, 5, cv2.GC_INIT_WITH_MASK)
    m = ((gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD)).astype(np.uint8) * 255

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(5, int(min(H, W) * 0.04)),) * 2)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        main = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        m = (labels == main).astype(np.uint8) * 255
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        m = np.zeros_like(m)
        cv2.drawContours(m, contours, -1, 255, -1)
    return m > 0


def detect_lesions(img: np.ndarray, leaf: np.ndarray) -> np.ndarray:
    """Boolean lesion mask inside `leaf`, from colour contrast against the local leaf tissue at two scales."""
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = [lab[..., i].astype(np.float32) for i in range(3)]

    # Fine scale: small spots against nearby tissue
    k = max(15, (min(img.shape[:2]) // 12) | 1)
    da = a - cv2.medianBlur(lab[..., 1], k).astype(np.float32)
    dl = l - cv2.medianBlur(lab[..., 0], k).astype(np.float32)
    db = b - cv2.medianBlur(lab[..., 2], k).astype(np.float32)
    les = (da > 7) | ((dl < -25) & (da > 2)) | ((da > 4) & (db > 6))

    # Coarse scale: large blotches that the fine reference would absorb
    k2 = min(3 * k, (min(img.shape[:2]) // 3) | 1)
    da2 = a - cv2.medianBlur(lab[..., 1], k2).astype(np.float32)
    dl2 = l - cv2.medianBlur(lab[..., 0], k2).astype(np.float32)
    les = (les | (da2 > 8) | ((dl2 < -25) & (da2 > 3))) & leaf

    les = cv2.morphologyEx(les.astype(np.uint8) * 255, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    # Ignore the leaf margin, where shadows and background bleed in
    interior = cv2.erode(leaf.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))) > 0
    les = ((les > 0) & interior).astype(np.uint8)

    # Drop thin elongated components (veins / midribs)
    n, labels, _, _ = cv2.connectedComponentsWithStats(les)
    keep = np.zeros(n, bool)
    for i in range(1, n):
        ys, xs = np.where(labels == i)
        if len(xs) < 4:
            continue
        (_, _), (w, h), _ = cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32))
        short, long_ = min(w, h) + 1, max(w, h) + 1
        keep[i] = not (long_ / short > 5 and short < 8)
    return keep[labels]


def lesion_map(pil_image: Image.Image):
    """
    Returns (leaf_mask, lesion_mask) at the original image size, plus the lesion share of the leaf in %.
    Work is done at WORK_SIZE px for speed.
    """
    rgb = pil_image.convert('RGB')
    W, H = rgb.size
    small = np.array(rgb.resize((WORK_SIZE, WORK_SIZE), Image.Resampling.BILINEAR))
    leaf = segment_leaf(small)
    les = detect_lesions(small, leaf)
    pct = 100.0 * les.sum() / max(1, leaf.sum())
    leaf_full = cv2.resize(leaf.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    les_full = cv2.resize(les.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    return leaf_full, les_full, round(float(pct), 1)

