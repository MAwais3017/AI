"""
Image quality checks for wound images.

Evaluates blur (Laplacian variance), resolution, brightness, and contrast.
Returns pass/fail and a list of human-readable issues.
"""

from __future__ import annotations

import cv2
import numpy as np
from typing import Any

# Configurable thresholds (tune as needed)
# Blur: Laplacian variance below this = "may be too blurry" (higher = more sensitive to blur)
MIN_RESOLUTION = 64
MIN_BLUR_VARIANCE = 150.0
BRIGHTNESS_LOW = 30
BRIGHTNESS_HIGH = 225
MIN_CONTRAST_STD = 20.0


def check_quality(img: np.ndarray) -> dict[str, Any]:
    """
    Run quality checks on a BGR or grayscale image.
    Returns dict with: pass (bool), issues (list[str]), details (dict with scores).
    """
    if img is None or img.size == 0:
        return {
            "pass": False,
            "issues": ["Invalid or empty image"],
            "details": {},
        }

    h, w = img.shape[:2]
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    issues: list[str] = []
    details: dict[str, Any] = {}

    # Resolution
    min_side = min(h, w)
    details["resolution"] = {"width": w, "height": h, "min_side": min_side}
    if min_side < MIN_RESOLUTION:
        issues.append(f"Image resolution too low (min side {min_side}px, recommended at least {MIN_RESOLUTION}px)")

    # Blur (Laplacian variance)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    details["blur_score"] = round(float(laplacian_var), 2)
    if laplacian_var < MIN_BLUR_VARIANCE:
        issues.append(f"Image may be too blurry (sharpness score: {laplacian_var:.0f})")

    # Brightness
    mean_brightness = float(np.mean(gray))
    details["brightness"] = round(mean_brightness, 2)
    if mean_brightness < BRIGHTNESS_LOW:
        issues.append("Image is too dark")
    elif mean_brightness > BRIGHTNESS_HIGH:
        issues.append("Image is too bright")

    # Contrast (std of pixel values)
    contrast_std = float(np.std(gray))
    details["contrast"] = round(contrast_std, 2)
    if contrast_std < MIN_CONTRAST_STD:
        issues.append("Image has low contrast")

    return {
        "pass": len(issues) == 0,
        "issues": issues,
        "details": details,
    }
