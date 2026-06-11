"""
Train Random Forest on extracted wound image features (tabular data).

Pipeline:
  1. Load images from train/val CSVs
  2. Extract color, texture, and edge features (extract_features.py)
  3. Scale features with StandardScaler
  4. Train RandomForest classifier
  5. Save model bundle to data/processed/model.joblib

Run with:
  venv\\Scripts\\python.exe scripts/train_model.py
"""

import csv
import sys
from pathlib import Path

_ML_ROOT = Path(__file__).resolve().parents[1]
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

import cv2
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler

from scripts.extract_features import FEATURE_NAMES, extract_features

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TRAIN_CSV = PROCESSED_DIR / "train.csv"
VAL_CSV = PROCESSED_DIR / "val.csv"
MODEL_PATH = PROCESSED_DIR / "model.joblib"
MODEL_TYPE = "rf_features"


def load_feature_dataset(csv_path: str):
    features, labels = [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img_path = row["image_path"]
            label = row["label"]
            img = cv2.imread(img_path)
            if img is None:
                print(f"WARNING: Could not read {img_path}")
                continue
            features.append(extract_features(img))
            labels.append(0 if label == "healthy" else 1)
    return np.array(features), np.array(labels)


def main():
    if not TRAIN_CSV.exists() or not VAL_CSV.exists():
        print("Train/val CSV not found. Run prepare_dataset.py first.")
        return

    print("Extracting features from train set...")
    X_train, y_train = load_feature_dataset(TRAIN_CSV)
    print("Extracting features from val set...")
    X_val, y_val = load_feature_dataset(VAL_CSV)

    if X_train.size == 0 or X_val.size == 0:
        print("Dataset is empty. Please add more images.")
        return

    print(f"Feature vector size: {X_train.shape[1]} ({len(FEATURE_NAMES)} features)")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    print("Training RandomForest on extracted features...")
    clf = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42)
    clf.fit(X_train_scaled, y_train)

    print("\nValidation results:")
    y_pred = clf.predict(X_val_scaled)
    print(classification_report(y_val, y_pred, target_names=["healthy", "infected"]))

    bundle = {
        "type": MODEL_TYPE,
        "classifier": clf,
        "scaler": scaler,
        "feature_names": FEATURE_NAMES,
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_PATH)
    print(f"\nSaved model bundle to {MODEL_PATH}")


if __name__ == "__main__":
    main()
