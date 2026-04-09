r"""
FastAPI service for wound infection prediction.

Loads the trained model from data/processed/model.joblib and exposes:
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

from scripts.quality import check_quality

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODEL_PATH = PROCESSED_DIR / "model.joblib"
IMG_SIZE = 64

# Reject only when blur is very extreme (e.g. bokeh); real wound photos often have moderate blur
RELEVANCE_MIN_BLUR = 15.0
RELEVANCE_MSG = "Image does not appear relevant for wound assessment. Please upload a clear image of a wound or affected skin area."


def preprocess_for_model(img: np.ndarray, denoise: bool = False) -> np.ndarray:
    """
    Preprocess image for the trained model: optional denoise, resize, grayscale, flatten.
    Must match training pipeline (train_model.py).
    """
    if img is None or img.size == 0:
        raise ValueError("Invalid image")
    if denoise and len(img.shape) == 3:
        img = cv2.fastNlMeansDenoisingColored(img, None, h=6, hForColorComponents=6, templateWindowSize=7, searchWindowSize=21)
    elif denoise and len(img.shape) == 2:
        img = cv2.fastNlMeansDenoising(img, None, h=10, templateWindowSize=7, searchWindowSize=21)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img.flatten().reshape(1, -1)

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
    return joblib.load(MODEL_PATH)


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

    quality_result = check_quality(img)
    blur_score = quality_result.get("details", {}).get("blur_score", 999.0)
    if blur_score < RELEVANCE_MIN_BLUR:
        raise HTTPException(status_code=400, detail=RELEVANCE_MSG)

    features = preprocess_for_model(img, denoise=False)
    probs = model.predict_proba(features)[0]
    labels: list[Literal["healthy", "infected"]] = ["healthy", "infected"]
    
    infected_prob = float(probs[1])
    healthy_prob = float(probs[0])
    max_prob = max(healthy_prob, infected_prob)

    # Reject only when model is very uncertain (likely not wound/skin); real wounds may score 60–75%
    if max_prob < 0.6:
        raise HTTPException(status_code=400, detail=RELEVANCE_MSG)

    # Use a higher threshold to reduce false positives (require 75% confidence for "infected")
    # Only predict "infected" if confidence is high enough, otherwise default to "healthy"
    if infected_prob >= 0.75:
        risk_label = "infected"
    else:
        risk_label = "healthy"
    
    # Generate recommendation based on risk level and probability
    if risk_label == "infected":
        if infected_prob >= 0.8:
            recommendation = "Urgent: Please visit a hospital or healthcare provider immediately for proper diagnosis and treatment."
        elif infected_prob >= 0.5:
            recommendation = "Recommended: Consult a healthcare provider soon. Monitor the wound closely for any worsening symptoms."
        else:
            recommendation = "Caution: Signs of possible infection detected. Consider consulting a healthcare provider if symptoms persist or worsen."
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
