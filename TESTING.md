# How to Test the App (including Image Quality & Preprocessing)

## 1. Start all three services

Use **3 terminals**. Run these from the project root `AI/` (or the folder that contains `backend`, `frontend`, `ml`).

### Terminal 1 – ML service (Python, port 8000)

```bash
cd ml
venv\Scripts\activate
python -m uvicorn scripts.inference_service:app --reload --host 0.0.0.0 --port 8000
```

*(On macOS/Linux use `source venv/bin/activate` and ensure the model exists at `ml/data/processed/model.joblib`.)*

### Terminal 2 – Backend (Node, port 3000)

```bash
cd backend
npm run dev
```

### Terminal 3 – Frontend (Expo)

```bash
cd frontend
npm start
```

Then choose:
- **w** – open in browser (web)
- **a** – Android emulator
- **i** – iOS simulator
- Or scan the QR code with Expo Go on your phone (same Wi‑Fi as your PC).

---

## 2. Test in the app

1. **Open the app** (web or Expo Go).
2. **Sign in or sign up** if your app has auth.
3. **Go to the main screen** (Wound Infection Detection).
4. **Pick or capture an image:**
   - **Gallery** – choose a wound photo (or any image).
   - **Camera** – take a new photo.
5. **Tap "Analyze Image".**
6. **Check the result:**
   - **Risk level** and **probabilities** (Healthy / Infected).
   - **Image quality note** (only if there are issues):
     - e.g. “Image may be too blurry”, “Image is too dark”, “Image has low contrast”.

To **see quality warnings**, use:
- A **blurry** image, or  
- A **very dark** or **very bright** image, or  
- A **tiny** image (e.g. under 64px).

Good-quality, well-lit images usually get no quality issues.

---

## 3. Test the quality-check endpoint alone (optional)

**Using curl** (replace `path/to/image.jpg` with a real file):

```bash
curl -X POST http://localhost:3000/image/quality-check -F "file=@path/to/image.jpg"
```

You should get JSON like:

```json
{
  "pass": true,
  "issues": [],
  "details": {
    "blur_score": 123.45,
    "brightness": 98.2,
    "contrast": 45.1,
    "resolution": { "width": 640, "height": 480, "min_side": 480 }
  }
}
```

If the image is blurry or dark, `pass` may be `false` and `issues` will list the problems.

---

## 4. Quick checklist

| Step                         | What to check                          |
|-----------------------------|----------------------------------------|
| ML service running          | `http://localhost:8000/health` → `{"status":"ok"}` |
| Backend running              | `http://localhost:3000/health` → `{"status":"ok"}` |
| Frontend running            | App opens in browser or device         |
| Analyze a good image        | Result + no quality note (or empty issues) |
| Analyze blurry/dark image   | Result + “Image quality note” with issues |

If the backend can’t reach the ML service, you’ll see “Failed to contact Python service”. Ensure the ML service is running on port 8000 and that `PYTHON_SERVICE_URL` (or default `http://localhost:8000`) is correct.
