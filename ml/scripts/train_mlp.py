"""
Compare Random Forest (on extracted features) vs MLP (on normalized pixels).

Use this script for FYP evaluation / supervisor comparison.

Run with:
  venv\\Scripts\\python.exe scripts/train_mlp.py
"""

import csv
import sys
from pathlib import Path

_ML_ROOT = Path(__file__).resolve().parents[1]
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

import cv2
import numpy as np
from sklearn.metrics import accuracy_score, classification_report
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from scripts.extract_features import extract_features
from scripts.train_model import load_feature_dataset

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TRAIN_CSV = PROCESSED_DIR / "train.csv"
VAL_CSV = PROCESSED_DIR / "val.csv"
PIXEL_SIZE = 64


def load_pixel_dataset(csv_path: str):
    pixels, labels = [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img = cv2.imread(row["image_path"])
            if img is None:
                continue
            img = cv2.resize(img, (PIXEL_SIZE, PIXEL_SIZE))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            pixels.append(img.flatten() / 255.0)
            labels.append(0 if row["label"] == "healthy" else 1)
    return np.array(pixels), np.array(labels)


def main():
    if not TRAIN_CSV.exists() or not VAL_CSV.exists():
        print("Train/val CSV not found. Run prepare_dataset.py first.")
        return

    print("=" * 60)
    print("Model 1: Random Forest on extracted features")
    print("=" * 60)
    X_train_f, y_train = load_feature_dataset(TRAIN_CSV)
    X_val_f, y_val = load_feature_dataset(VAL_CSV)

    scaler_f = StandardScaler()
    X_train_f = scaler_f.fit_transform(X_train_f)
    X_val_f = scaler_f.transform(X_val_f)

    from sklearn.ensemble import RandomForestClassifier

    rf = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42)
    rf.fit(X_train_f, y_train)
    rf_pred = rf.predict(X_val_f)
    rf_acc = accuracy_score(y_val, rf_pred)
    print(f"Accuracy: {rf_acc:.4f}")
    print(classification_report(y_val, rf_pred, target_names=["healthy", "infected"]))

    print("\n" + "=" * 60)
    print("Model 2: MLP on normalized grayscale pixels")
    print("=" * 60)
    X_train_p, _ = load_pixel_dataset(TRAIN_CSV)
    X_val_p, y_val_p = load_pixel_dataset(VAL_CSV)

    mlp = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        max_iter=500,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1,
    )
    mlp.fit(X_train_p, y_train)
    mlp_pred = mlp.predict(X_val_p)
    mlp_acc = accuracy_score(y_val_p, mlp_pred)
    print(f"Accuracy: {mlp_acc:.4f}")
    print(classification_report(y_val_p, mlp_pred, target_names=["healthy", "infected"]))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Random Forest (features): {rf_acc:.4f}")
    print(f"MLP (pixels):             {mlp_acc:.4f}")
    winner = "Random Forest" if rf_acc >= mlp_acc else "MLP"
    print(f"Higher validation accuracy: {winner}")


if __name__ == "__main__":
    main()
