"""
Heuristic relevance check: image should look like skin / wound tissue, not random scenes.

Used before running the infection classifier so objects (vehicles, landscapes, etc.)
return a clear error instead of a bogus prediction.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

RELEVANCE_MSG = (
    "Image does not appear relevant for wound assessment. "
    "Please upload a clear photo of a wound or affected skin area."
)

# Minimum share of pixels that look like skin or wound tissue (flesh, red, pink, yellow crust)
MIN_BODY_TISSUE_FRACTION = 0.06

# If blue/green (sky, water, vehicles) dominates and tissue is scarce, reject
MAX_SCENE_COLOR_FRACTION = 0.45
SCENE_COLOR_REQUIRES_TISSUE_BELOW = 0.12

# Reject when scene colors outweigh tissue-like colors (random / outdoor photos)
MAX_SCENE_TO_TISSUE_RATIO = 1.6
SCENE_RATIO_REQUIRES_TISSUE_BELOW = 0.32


def _skin_mask(ycrcb: np.ndarray, hsv: np.ndarray) -> np.ndarray:
    y_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
    h_mask1 = cv2.inRange(hsv, np.array([0, 30, 60]), np.array([25, 150, 255]))
    h_mask2 = cv2.inRange(hsv, np.array([0, 15, 50]), np.array([20, 255, 255]))
    return cv2.bitwise_or(y_mask, cv2.bitwise_or(h_mask1, h_mask2))


def _wound_tissue_mask(hsv: np.ndarray) -> np.ndarray:
    """Red / pink / inflamed / yellow-brown crust tones common in wound photos."""
    red_low = cv2.inRange(hsv, np.array([0, 40, 40]), np.array([12, 255, 255]))
    red_high = cv2.inRange(hsv, np.array([165, 40, 40]), np.array([180, 255, 255]))
    pink = cv2.inRange(hsv, np.array([0, 20, 80]), np.array([20, 180, 255]))
    yellow_brown = cv2.inRange(hsv, np.array([8, 30, 60]), np.array([35, 220, 255]))
    return cv2.bitwise_or(cv2.bitwise_or(red_low, red_high), cv2.bitwise_or(pink, yellow_brown))


def _scene_mask(hsv: np.ndarray) -> np.ndarray:
    """Strong blue/green — typical of sky, grass, water, many non-skin objects."""
    blue = cv2.inRange(hsv, np.array([85, 40, 40]), np.array([135, 255, 255]))
    green = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
    return cv2.bitwise_or(blue, green)


def tissue_fraction(img: np.ndarray) -> float:
    if img is None or img.size == 0:
        return 0.0
    h, w = img.shape[:2]
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    body = cv2.bitwise_or(_skin_mask(ycrcb, hsv), _wound_tissue_mask(hsv))
    return float(np.count_nonzero(body)) / float(h * w)


def scene_fraction(img: np.ndarray) -> float:
    if img is None or img.size == 0:
        return 0.0
    h, w = img.shape[:2]
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    scene = _scene_mask(hsv)
    return float(np.count_nonzero(scene)) / float(h * w)


def check_relevance(img: np.ndarray) -> dict[str, Any]:
    """
    Return { "pass": bool, "message": str | None, "details": dict }.
  """
    if img is None or img.size == 0:
        return {
            "pass": False,
            "message": RELEVANCE_MSG,
            "details": {},
        }

    tissue = tissue_fraction(img)
    scene = scene_fraction(img)
    details = {
        "tissue_fraction": round(tissue, 4),
        "scene_fraction": round(scene, 4),
    }

    if tissue < MIN_BODY_TISSUE_FRACTION:
        return {"pass": False, "message": RELEVANCE_MSG, "details": details}

    if scene >= MAX_SCENE_COLOR_FRACTION and tissue < SCENE_COLOR_REQUIRES_TISSUE_BELOW:
        return {"pass": False, "message": RELEVANCE_MSG, "details": details}

    if tissue > 0 and scene / tissue >= MAX_SCENE_TO_TISSUE_RATIO and tissue < SCENE_RATIO_REQUIRES_TISSUE_BELOW:
        return {"pass": False, "message": RELEVANCE_MSG, "details": details}

    return {"pass": True, "message": None, "details": details}
