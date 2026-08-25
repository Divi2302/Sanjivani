import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    PCOSPredictionRequest,
    PCOSPredictionResponse,
    HealthCheckResponse
)
from app.preprocessing import preprocess_input
from app.prediction import predictor
from app.safety_rules import evaluate_overall_triage

# Configure logger
logger = logging.getLogger("sanjivani_ml_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="Sanjivani ML Prediction API",
    description="Standalone ML Prediction and Hybrid Clinical Safety Triage API for PCOS Screening",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["Service Status"],
    summary="Root Service Information"
)
def root():
    """
    Root probe providing service status and links to documentation.
    """
    return {
        "service": "Sanjivani ML Prediction API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Service Status"],
    summary="Health & Readiness Probe"
)
def health_check():
    """
    Liveness & readiness probe verifying that ML model and scaler artifacts are loaded.
    """
    is_ready = predictor.model is not None and predictor.scaler is not None
    return HealthCheckResponse(
        status="healthy" if is_ready else "unhealthy",
        model_loaded=is_ready,
        version="1.0.0"
    )


@app.post(
    "/predict",
    response_model=PCOSPredictionResponse,
    tags=["Prediction & Triage"],
    summary="Predict PCOS Risk & Perform Integrated Clinical Triage"
)
def predict(data: PCOSPredictionRequest):
    """
    Standalone prediction and triage pipeline:
    1. Preprocesses health assessment input into 13 standardized features and calculates BMI.
    2. Executes inference using the trained Logistic Regression model and fitted StandardScaler.
    3. Evaluates clinical safety red flags and menstrual bleeding duration bounds.
    4. Computes deterministic overall triage level (LOW, MODERATE, HIGH, CRITICAL).
    5. Returns structured JSON output with separate ML and triage results.
    """
    try:
        # 1. Feature Preprocessing & Scaling Input Preparation
        preprocessed = preprocess_input(data)
        features_df = preprocessed["features_df"]
        bmi = preprocessed["bmi"]
        base_warnings = preprocessed["warnings"]

        # 2. Pure Machine Learning Inference
        ml_result = predictor.predict(features_df)
        pcos_probability = ml_result["risk_probability"]
        model_pred = ml_result["prediction"]
        model_prediction_label = (
            "Higher PCOS-related risk" if model_pred == 1 else "Lower PCOS-related risk"
        )

        # 3. Deterministic Safety & Overall Triage Rule Engine
        triage_result = evaluate_overall_triage(
            data=data,
            pcos_probability=pcos_probability,
            model_prediction=model_pred,
            base_warnings=base_warnings
        )

        # Deduplicate model limitations and warnings
        deduped_limitations = list(dict.fromkeys(triage_result["model_limitations"]))
        deduped_warnings = list(dict.fromkeys(base_warnings + deduped_limitations))

        # 4. Assemble Structured API Response
        return PCOSPredictionResponse(
            # ML Model outputs
            pcos_probability=pcos_probability,
            model_prediction=model_pred,
            model_prediction_label=model_prediction_label,

            # Hybrid triage outputs
            overall_prediction=triage_result["overall_prediction"],
            overall_reasons=triage_result["overall_reasons"],
            red_flags=triage_result["red_flags"],
            model_limitations=deduped_limitations,
            recommendation=triage_result["recommendation"],

            # Compatibility & calculated metrics
            risk_probability=pcos_probability,
            bmi=round(bmi, 2),
            triage_level=triage_result["overall_prediction"].lower(),
            disclaimer="This is an AI-assisted early screening and triage assessment and not a medical diagnosis.",
            warnings=deduped_warnings
        )

    except Exception as e:
        logger.error(f"Inference error in /predict: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the prediction request."
        )
