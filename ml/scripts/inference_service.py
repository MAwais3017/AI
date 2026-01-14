"""
FastAPI service for wound infection prediction.

Loads the trained model from data/processed/model.joblib and exposes:
  - POST /predict
    - body: multipart file "file" (image)
    - returns: riskLevel (healthy / infected) + probability estimate

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

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODEL_PATH = PROCESSED_DIR / "model.joblib"
IMG_SIZE = 64

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


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")

    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    features = img.flatten().reshape(1, -1)

    probs = model.predict_proba(features)[0]
    labels: list[Literal["healthy", "infected"]] = ["healthy", "infected"]
    
    # Use a higher threshold to reduce false positives (require 75% confidence for "infected")
    infected_prob = float(probs[1])
    healthy_prob = float(probs[0])
    
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
    }
