# Surgical Wound Infection Detection (FYP)

This project implements your FYP idea:
- Mobile-oriented backend in **Node.js + Fastify**
- **Python ML service** (FastAPI) for wound infection prediction
- Simple, extendable **dataset pipeline** you can use even without a pre-made dataset.

## Folder structure

- `backend/` – Node.js Fastify REST API
- `ml/` – Python environment, dataset, training, and inference service
  - `data/raw/healthy` – put images of non-infected wounds here
  - `data/raw/infected` – put images of infected wounds here
  - `data/processed` – generated CSVs and trained model
  - `scripts/prepare_dataset.py` – builds train/val CSVs
  - `scripts/train_model.py` – trains a RandomForest classifier
  - `scripts/inference_service.py` – FastAPI prediction service

## 1. Setup Python ML environment

```bash
cd "C:\Users\M. Owais Dogar\OneDrive\Desktop\AI\ml"
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

## 2. Build your dataset (you have no dataset yet)

1. Collect wound images (from public datasets, hospitals, or synthetic examples) and manually put them into:
   - `ml/data/raw/healthy`
   - `ml/data/raw/infected`
2. Run the dataset preparation script:

```bash
cd "C:\Users\M. Owais Dogar\OneDrive\Desktop\AI\ml"
venv\Scripts\python.exe scripts/prepare_dataset.py
```

This will create `data/processed/train.csv` and `data/processed/val.csv`.

## 3. Train the ML model

```bash
cd "C:\Users\M. Owais Dogar\OneDrive\Desktop\AI\ml"
venv\Scripts\python.exe scripts/train_model.py
```

This trains a **RandomForest** classifier on simple grayscale image features and saves `data/processed/model.joblib`.

## 4. Run the Python inference API

```bash
cd "C:\Users\M. Owais Dogar\OneDrive\Desktop\AI\ml"
venv\Scripts\python.exe -m uvicorn scripts.inference_service:app --reload --host 0.0.0.0 --port 8000
```

Test quickly in browser/Postman:
- `GET http://localhost:8000/health`
- `POST http://localhost:8000/predict` with a `file` (form-data image)

## 5. Run the Node.js Fastify backend

```bash
cd "C:\Users\M. Owais Dogar\OneDrive\Desktop\AI\backend"
npm install   # first time only
npm run dev
```

Endpoints:
- `GET http://localhost:3000/health`
- `POST http://localhost:3000/image/quality-check` – placeholder quality check
- `POST http://localhost:3000/image/predict` – forwards the image to the Python `/predict` endpoint and returns its result

If your Python service runs on another URL, set:
```bash
set PYTHON_SERVICE_URL=http://localhost:8000
npm run dev
```

## 6. Connecting a mobile app (next step)

Your mobile app (Flutter / React Native) only needs to:
- Capture or select an image
- Send it as `multipart/form-data` to `POST http://<your-ip>:3000/image/predict`
- Show the returned `riskLevel` and probabilities.

From here you can:
- Replace the RandomForest with a deep CNN (e.g., PyTorch, TensorFlow)
- Improve image quality checks and add temporal analysis (multiple images over days).

## 6. React Native (Expo) frontend

A minimal Expo app is in `frontend/`.

### Install dependencies
```bash
cd "C:\Users\M. Owais Dogar\OneDrive\Desktop\AI\frontend"
npm install
```

### Run the app
```bash
npm start
```
This opens Expo DevTools. Use a real device (Expo Go app) or emulator. Make sure your device can reach the backend (use your machine IP instead of `localhost` in `App.js`: `BACKEND_URL = "http://<your-ip>:3000"`).

### What the app does
- Lets you pick or capture an image.
- Sends it as `multipart/form-data` to `POST /image/predict` on the Node backend.
- Displays the returned `riskLevel` and probabilities.

### File to edit
- `frontend/App.js` – set `BACKEND_URL` to your machine IP for device testing, and adjust UI if you like.
