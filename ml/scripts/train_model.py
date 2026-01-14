"""
Simple image classifier training using scikit-learn on basic image features.

Because we are avoiding heavy deep-learning libraries here, this script:
  - reads train/val CSVs from data/processed
  - loads images with OpenCV
  - resizes to 64x64 and flattens pixels
  - trains a RandomForest classifier
  - saves the model to data/processed/model.joblib

Run with:
  venv\Scripts\python.exe scripts/train_model.py
"""

import csv
from pathlib import Path

import cv2
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TRAIN_CSV = PROCESSED_DIR / "train.csv"
VAL_CSV = PROCESSED_DIR / "val.csv"
MODEL_PATH = PROCESSED_DIR / "model.joblib"

IMG_SIZE = 64


def load_dataset(csv_path):
    paths, labels = [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img_path = row["image_path"]
            label = row["label"]
            img = cv2.imread(img_path)
            if img is None:
                print(f"WARNING: Could not read {img_path}")
                continue
            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            paths.append(img.flatten())
            labels.append(0 if label == "healthy" else 1)
    return np.array(paths), np.array(labels)


def main():
    if not TRAIN_CSV.exists() or not VAL_CSV.exists():
        print("Train/val CSV not found. Run prepare_dataset.py first.")
        return

    print("Loading train dataset...")
    X_train, y_train = load_dataset(TRAIN_CSV)
    print("Loading val dataset...")
    X_val, y_val = load_dataset(VAL_CSV)

    if X_train.size == 0 or X_val.size == 0:
        print("Dataset is empty. Please add more images.")
        return

    print("Training RandomForest classifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    print("Evaluating on validation set...")
    y_pred = clf.predict(X_val)
    print(classification_report(y_val, y_pred, target_names=["healthy", "infected"]))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
