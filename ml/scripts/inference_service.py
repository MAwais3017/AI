r"""
FastAPI service for wound infection prediction.

Loads the trained model bundle from data/processed/model.joblib (Random Forest on extracted features).
  - POST /predict
    - body: multipart file "file" (image)
    - returns: riskLevel (healthy / infected) + probability estimate + quality
  - POST /quality-check
    - body: multipart file "file" (image)
    - returns: pass, issues, details

Run with:
  venv\Scripts\python.exe -m uvicorn scripts.inference_service:app --reload --host 0.0.0.0 --port 8000
"""

from pathlib import Path
from typing import Literal

import cv2
import joblib
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from scripts.extract_features import extract_features
from scripts.quality import check_quality
from scripts.relevance import RELEVANCE_MSG, check_relevance

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODEL_PATH = PROCESSED_DIR / "model.joblib"

# Reject only when blur is very extreme (e.g. bokeh); real wound photos often have moderate blur
RELEVANCE_MIN_BLUR = 15.0


def features_for_model(img: np.ndarray, bundle: dict) -> np.ndarray:
    """Extract and scale features using the saved training pipeline."""
    raw = extract_features(img).reshape(1, -1)
    scaler = bundle["scaler"]
    return scaler.transform(raw)

app = FastAPI(title="Wound Infection Classifier")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_model():
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model file not found at {MODEL_PATH}. Train the model first.")
    bundle = joblib.load(MODEL_PATH)
    if isinstance(bundle, dict) and bundle.get("type") == "rf_features":
        return bundle
    raise RuntimeError(
        "Old pixel-based model found. Retrain with: venv\\Scripts\\python.exe scripts/train_model.py"
    )


model = None


@app.on_event("startup")
async def startup_event():
    global model
    model = load_model()


@app.get("/health")
async def health():
    return {"status": "ok"}


def _decode_image(contents: bytes) -> np.ndarray:
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not decode image")
    return img


@app.post("/quality-check")
async def quality_check(file: UploadFile = File(...)):
    contents = await file.read()
    img = _decode_image(contents)
    result = check_quality(img)
    return {
        "pass": result["pass"],
        "issues": result["issues"],
        "details": result["details"],
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")

    contents = await file.read()
    img = _decode_image(contents)

    relevance_result = check_relevance(img)
    if not relevance_result["pass"]:
        raise HTTPException(
            status_code=400,
            detail=relevance_result.get("message") or RELEVANCE_MSG,
        )

    quality_result = check_quality(img)
    blur_score = quality_result.get("details", {}).get("blur_score", 999.0)
    if blur_score < RELEVANCE_MIN_BLUR:
        raise HTTPException(status_code=400, detail=RELEVANCE_MSG)

    features = features_for_model(img, model)
    clf = model["classifier"]
    probs = clf.predict_proba(features)[0]

    infected_prob = float(probs[1])
    healthy_prob = float(probs[0])
    max_prob = max(healthy_prob, infected_prob)

    # Reject only when model is very uncertain (likely not wound/skin); real wounds may score 60–75%
    if max_prob < 0.6:
        raise HTTPException(status_code=400, detail=RELEVANCE_MSG)

    # riskLevel must match the displayed probabilities (higher class wins). A fixed "infected
    # only if >= 75%" rule caused the badge to say Healthy while Infected had the higher %.
    if infected_prob > healthy_prob:
        risk_label: Literal["healthy", "infected"] = "infected"
    elif healthy_prob > infected_prob:
        risk_label = "healthy"
    else:
        risk_label = "infected"  # exact tie: cautious default
    
    # Generate recommendation based on risk level and probability
    if risk_label == "infected":
        if infected_prob >= 0.8:
            recommendation = "Urgent: Please visit a hospital or healthcare provider immediately for proper diagnosis and treatment."
        else:
            recommendation = "Recommended: Consult a healthcare provider soon. Monitor the wound closely for any worsening symptoms."
    else:
        recommendation = "Good: Wound appears healthy. Continue monitoring and maintain proper wound care. Consult a doctor if you notice any changes."

    return {
        "riskLevel": risk_label,
        "probabilities": {
            "healthy": float(probs[0]),
            "infected": float(probs[1]),
        },
        "recommendation": recommendation,
        "quality": {
            "pass": quality_result["pass"],
            "issues": quality_result["issues"],
        },
    }
