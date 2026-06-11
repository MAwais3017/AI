"""
Extract tabular features from wound images for Random Forest.

Random Forest expects structured feature vectors, not raw flattened pixels.
Features focus on color (inflammation, pus), texture, and edges relevant to wounds.
"""

from __future__ import annotations

import cv2
import numpy as np

# Slightly larger than old pixel model — better color/texture statistics
FEATURE_IMG_SIZE = 128
HIST_BINS = 8


def _ensure_bgr(img: np.ndarray) -> np.ndarray:
    if img is None or img.size == 0:
        raise ValueError("Invalid image")
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img


def _color_fraction(hsv: np.ndarray, lower: tuple[int, int, int], upper: tuple[int, int, int]) -> float:
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    return float(np.count_nonzero(mask)) / float(mask.size)


def _normalized_hist(channel: np.ndarray, bins: int = HIST_BINS) -> list[float]:
    hist, _ = np.histogram(channel.flatten(), bins=bins, range=(0, 256))
    total = hist.sum()
    if total == 0:
        return [0.0] * bins
    return (hist / total).astype(float).tolist()


FEATURE_NAMES: list[str] = [
    "b_mean",
    "g_mean",
    "r_mean",
    "b_std",
    "g_std",
    "r_std",
    "h_mean",
    "s_mean",
    "v_mean",
    "h_std",
    "s_std",
    "v_std",
    "gray_mean",
    "gray_std",
    "redness_mean",
    "redness_std",
    "yellow_brown_frac",
    "red_inflamed_frac",
    "pink_frac",
    "laplacian_var",
    "edge_density",
] + [f"h_hist_{i}" for i in range(HIST_BINS)] + [f"s_hist_{i}" for i in range(HIST_BINS)]


def extract_features(img: np.ndarray, resize: bool = True) -> np.ndarray:
    """
    Convert a BGR wound image into a 1D feature vector.
    Must match train_model.py and inference_service.py.
    """
    img = _ensure_bgr(img)
    if resize:
        img = cv2.resize(img, (FEATURE_IMG_SIZE, FEATURE_IMG_SIZE))

    b, g, r = cv2.split(img)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    redness = r.astype(np.float32) / (r.astype(np.float32) + g.astype(np.float32) + b.astype(np.float32) + 1.0)

    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.count_nonzero(edges)) / float(edges.size)

    yellow_brown_frac = _color_fraction(hsv, (8, 30, 60), (35, 220, 255))
    red_inflamed_frac = _color_fraction(hsv, (0, 40, 40), (12, 255, 255)) + _color_fraction(
        hsv, (165, 40, 40), (180, 255, 255)
    )
    pink_frac = _color_fraction(hsv, (0, 20, 80), (20, 180, 255))

    features = [
        float(np.mean(b)),
        float(np.mean(g)),
        float(np.mean(r)),
        float(np.std(b)),
        float(np.std(g)),
        float(np.std(r)),
        float(np.mean(h)),
        float(np.mean(s)),
        float(np.mean(v)),
        float(np.std(h)),
        float(np.std(s)),
        float(np.std(v)),
        float(np.mean(gray)),
        float(np.std(gray)),
        float(np.mean(redness)),
        float(np.std(redness)),
        yellow_brown_frac,
        min(red_inflamed_frac, 1.0),
        pink_frac,
        laplacian_var,
        edge_density,
    ]
    features.extend(_normalized_hist(h))
    features.extend(_normalized_hist(s))

    return np.array(features, dtype=np.float32)


def extract_features_batch(images: list[np.ndarray]) -> np.ndarray:
    return np.array([extract_features(img) for img in images])
