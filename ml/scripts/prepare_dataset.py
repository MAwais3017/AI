"""
Prepare a simple wound dataset from folders into train/val CSV files.

Expected folder structure (you create it):
  ml/data/raw/
    healthy/
      img1.jpg, img2.jpg, ...
    infected/
      img3.jpg, img4.jpg, ...

This script will:
  - scan these folders
  - shuffle and split into train/val
  - write CSV files with paths and labels into ml/data/processed/

Run with:
  venv\Scripts\python.exe scripts/prepare_dataset.py
"""

import csv
import random
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
TRAIN_CSV = PROCESSED_DIR / "train.csv"
VAL_CSV = PROCESSED_DIR / "val.csv"

# train/val split ratio
VAL_RATIO = 0.2


def collect_samples():
    samples = []
    for label in ["healthy", "infected"]:
        class_dir = RAW_DIR / label
        if not class_dir.exists():
            print(f"WARNING: {class_dir} does not exist. Create it and add images.")
            continue
        for img_path in class_dir.glob("*.*"):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            samples.append((str(img_path), label))
    return samples


def split_dataset(samples):
    random.shuffle(samples)
    n_val = max(1, int(len(samples) * VAL_RATIO)) if samples else 0
    val_samples = samples[:n_val]
    train_samples = samples[n_val:]
    return train_samples, val_samples


def write_csv(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_path", "label"])
        for img_path, label in samples:
            writer.writerow([img_path, label])


def main():
    samples = collect_samples()
    if not samples:
        print("No images found. Please add images to ml/data/raw/healthy and ml/data/raw/infected.")
        return

    train_samples, val_samples = split_dataset(samples)
    write_csv(TRAIN_CSV, train_samples)
    write_csv(VAL_CSV, val_samples)
    print(f"Wrote {len(train_samples)} train and {len(val_samples)} val samples.")


if __name__ == "__main__":
    main()
