"""Generate simple synthetic images for testing the pipeline.

This does NOT create real medical data. It only makes colored patterns so
that you can run `prepare_dataset.py` and `train_model.py` end-to-end.

- Healthy: greenish rectangles
- Infected: reddish/orange rectangles with random noise

Run with:
  venv\Scripts\python.exe scripts/generate_dummy_images.py
"""

from pathlib import Path
import random

import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
HEALTHY_DIR = RAW_DIR / "healthy"
INFECTED_DIR = RAW_DIR / "infected"

HEALTHY_COUNT = 40
INFECTED_COUNT = 40
IMG_SIZE = 256


def make_healthy_image() -> np.ndarray:
  img = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
  # soft green background
  img[:] = (40, 140, 60)
  # add some lighter patches
  for _ in range(5):
    x1, y1 = random.randint(0, IMG_SIZE - 60), random.randint(0, IMG_SIZE - 60)
    x2, y2 = x1 + random.randint(30, 80), y1 + random.randint(30, 80)
    cv2.rectangle(img, (x1, y1), (x2, y2), (70, 200, 100), thickness=-1)
  return img


def make_infected_image() -> np.ndarray:
  img = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
  # red/orange base
  img[:] = (40, 60, 180)  # BGR
  # irregular darker patches
  for _ in range(5):
    center = (random.randint(40, IMG_SIZE - 40), random.randint(40, IMG_SIZE - 40))
    axes = (random.randint(20, 60), random.randint(20, 60))
    color = (random.randint(0, 40), random.randint(0, 40), random.randint(130, 200))
    cv2.ellipse(img, center, axes, angle=random.random() * 180, startAngle=0, endAngle=360, color=color, thickness=-1)
  # add some noise
  noise = np.random.randint(0, 40, (IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
  img = cv2.add(img, noise)
  return img


def main():
  HEALTHY_DIR.mkdir(parents=True, exist_ok=True)
  INFECTED_DIR.mkdir(parents=True, exist_ok=True)

  print(f"Writing synthetic images to: {HEALTHY_DIR} and {INFECTED_DIR}")

  for i in range(HEALTHY_COUNT):
    img = make_healthy_image()
    out_path = HEALTHY_DIR / f"healthy_{i:03d}.png"
    cv2.imwrite(str(out_path), img)

  for i in range(INFECTED_COUNT):
    img = make_infected_image()
    out_path = INFECTED_DIR / f"infected_{i:03d}.png"
    cv2.imwrite(str(out_path), img)

  print("Done. Generated", HEALTHY_COUNT, "healthy and", INFECTED_COUNT, "infected images.")


if __name__ == "__main__":
  main()
