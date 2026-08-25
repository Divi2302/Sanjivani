# Sanjivani ML Prediction & Triage API

A clean, minimal, standalone **Machine Learning Prediction & Clinical Safety Triage Service** for PCOS screening and risk assessment.

---

## 1. Purpose

This service has a single responsibility:

**Receive patient assessment data → Validate input → Preprocess features & compute BMI → Run trained Logistic Regression model → Apply clinical red-flag & safety rules → Return structured prediction response.**

It does **not** contain databases, authentication, patient management, ASHA worker workflows, referrals, or frontend code. It is designed to be deployed as an independent ML microservice called by upstream backends or clients via `POST /predict`.

---

## 2. Architecture & Data Flow

```text
Client
  ↓
POST /predict
  ↓
Input Validation (Pydantic)
  ↓
Preprocessing + BMI Calculation (13 Features)
  ↓
Logistic Regression Model (StandardScaler + Inference)
  ↓
Red Flag / Safety Rules Engine
  ↓
Integrated Overall Prediction (Triage Priority)
  ↓
JSON Response
```

---

## 3. Project Structure

```
Sanjivani_Backend/
├── main.py                     # FastAPI application & POST /predict endpoint
├── requirements.txt            # Minimal runtime dependencies
├── pyproject.toml              # Project metadata & dependency specs
├── README.md                   # Complete service documentation
├── .gitignore                  # Git ignore rules
│
├── models/
│   ├── sanjivani_model.pkl     # Trained Logistic Regression model artifact
│   ├── scaler.pkl              # Fitted StandardScaler artifact (13 features)
│   └── model_metadata.json     # Feature list, scaling means & bounds
│
├── app/
│   ├── __init__.py
│   ├── schemas.py              # Pydantic request & response models
│   ├── preprocessing.py        # BMI calculation & 13-feature DataFrame vector
│   ├── prediction.py           # Model artifact loading & pure ML inference
│   └── safety_rules.py         # Acute red flags, limitations & overall triage
│
└── tests/
    └── test_predict.py         # Unit & integration test suite
```

---

## 4. Installation & Local Setup

### Prerequisites
- Python 3.11+
- `pip` or [uv](https://github.com/astral-sh/uv)

### Option A: Using `uv` (Recommended)
```bash
# Clone the repository
git clone <repo-url>
cd Sanjivani_Backend

# Run test suite
uv run python -m unittest discover tests

# Start development server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: Using standard `pip` & `venv`
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python3 -m unittest discover tests

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

## 5. API Endpoint Documentation

### Main Endpoint: `POST /predict`

Receives clinical screening inputs, validates data, runs machine learning inference, applies safety rules, and returns an integrated triage assessment.

#### Request JSON:
```json
{
  "age": 25,
  "weight": 75.0,
  "height": 160.0,
  "cycle_type": "regular",
  "cycle_length": 5,
  "weight_gain": true,
  "hair_growth": true,
  "skin_darkening": true,
  "hair_loss": true,
  "pimples": true,
  "fast_food": true,
  "regular_exercise": false,
  "heavy_bleeding": false,
  "severe_pain": false,
  "blood_in_stool": false,
  "vomiting": false
}
```

> **Note on `cycle_length`**: In this model and dataset, `cycle_length` represents the **menstrual bleeding duration in days** (normal range: 2–7 days, training dataset range: 0–12 days), **not** the menstrual cycle interval.

#### Response JSON:
```json
{
  "pcos_probability": 0.9045,
  "model_prediction": 1,
  "model_prediction_label": "Higher PCOS-related risk",
  "overall_prediction": "HIGH",
  "overall_reasons": [
    "Multiple androgenic/metabolic indicators present (5 reported).",
    "ML model detected elevated PCOS-related risk (probability: 90.5%)."
  ],
  "red_flags": [],
  "model_limitations": [],
  "recommendation": "Prompt consultation with a healthcare professional (such as a gynecologist or endocrinologist) is recommended.",
  "risk_probability": 0.9045,
  "bmi": 29.3,
  "triage_level": "high",
  "disclaimer": "This is an AI-assisted early screening and triage assessment and not a medical diagnosis.",
  "warnings": []
}
```

---

## 6. Key Concepts Explained

### 1. `pcos_probability` & `model_prediction` (Pure ML Layer)
- **`pcos_probability`**: The raw, unmanipulated positive-class probability directly produced by the trained `LogisticRegression` model after feature scaling via `StandardScaler`.
- **`model_prediction`**: Binary classification (`0` = Lower risk, `1` = Higher risk) using the calibrated decision threshold (`0.40`).
- **`model_prediction_label`**: `"Higher PCOS-related risk"` or `"Lower PCOS-related risk"`.

### 2. `overall_prediction` & `triage_level` (Integrated Decision Layer)
The overall clinical prediction is **decoupled** from the pure ML model prediction:
- **`overall_prediction`** (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`): Combines ML output with acute clinical symptoms, bleeding duration analysis, and red flags.
- **`triage_level`**: Lowercase representation of `overall_prediction` (`"low"`, `"moderate"`, `"high"`, `"critical"`).

**Example of Safety Escalation**:
If a patient has a very low ML risk probability (`0.05`), but reports `severe_pain: true` or `blood_in_stool: true`, the statistical ML probability remains untouched (`0.05`), but `overall_prediction` escalates immediately to `HIGH` or `CRITICAL` for patient safety.

### 3. `red_flags`
Structured clinical red flags detected from inputs:
```json
{
  "severity": "critical",
  "category": "gastrointestinal",
  "message": "Blood in stool observed — this is a serious general clinical red flag requiring urgent medical evaluation."
}
```
- Non-PCOS acute symptoms (such as `blood_in_stool` and `vomiting`) are evaluated as **general clinical red flags**, not as endocrine/PCOS indicators.

### 4. `model_limitations`
If inputs (e.g. bleeding duration $> 12$ days) fall outside the observed ML training range ($0–12$ days):
- The raw value is safely capped for the ML scaler.
- An explicit warning is returned in `model_limitations` explaining that the ML probability may be less reliable for out-of-distribution inputs.

---

## 7. How to Call `POST /predict` from External Backends

### cURL Example
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 25,
    "weight": 75.0,
    "height": 160.0,
    "cycle_type": "regular",
    "cycle_length": 5,
    "weight_gain": true,
    "hair_growth": true,
    "skin_darkening": true,
    "hair_loss": true,
    "pimples": true,
    "fast_food": true,
    "regular_exercise": false,
    "heavy_bleeding": false,
    "severe_pain": false,
    "blood_in_stool": false,
    "vomiting": false
  }'
```

### Python Example
```python
import requests

payload = {
    "age": 25,
    "weight": 75.0,
    "height": 160.0,
    "cycle_type": "regular",
    "cycle_length": 5,
    "weight_gain": True,
    "hair_growth": True,
    "skin_darkening": True,
    "hair_loss": True,
    "pimples": True,
    "fast_food": True,
    "regular_exercise": False,
    "heavy_bleeding": False,
    "severe_pain": False,
    "blood_in_stool": False,
    "vomiting": False
}

response = requests.post("http://localhost:8000/predict", json=payload)
data = response.json()
print("ML Probability:", data["pcos_probability"])
print("Overall Prediction:", data["overall_prediction"])
```

---

## 8. Medical & Legal Disclaimer

> **IMPORTANT**: This API is an AI-assisted early screening and risk stratification tool. The machine learning model prediction is a statistical estimate based on historical data, and the overall prediction incorporates deterministic safety rules. **This service does not provide a medical diagnosis or replace professional medical consultation, diagnosis, or treatment.**
