import os
from pathlib import Path
import joblib
import pandas as pd
from typing import Dict, Any, Union

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "sanjivani_model.pkl"
DEFAULT_SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"

MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))
SCALER_PATH = Path(os.getenv("SCALER_PATH", str(DEFAULT_SCALER_PATH)))


class PCOSPredictor:
    """
    Handles loading the trained Logistic Regression model and StandardScaler,
    and running pure inference to obtain PCOS risk probabilities.
    """

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        scaler_path: Path = SCALER_PATH,
        threshold: float = 0.40
    ):
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.threshold = threshold

        self._load_artifacts()

    def _load_artifacts(self):
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model artifact not found at: {self.model_path}")
        if not self.scaler_path.exists():
            raise FileNotFoundError(f"Scaler artifact not found at: {self.scaler_path}")

        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load ML artifacts: {e}") from e

    def predict(self, features: Union[pd.DataFrame, dict]) -> Dict[str, Any]:
        """
        Runs inference on 13 preprocessed features.

        Returns:
            dict with:
                - risk_probability (float, rounded to 4 decimals)
                - prediction (int: 0 or 1)
                - threshold (float: 0.40)
        """
        if isinstance(features, dict):
            features_df = pd.DataFrame([features])
        else:
            features_df = features

        # Scale features using the fitted StandardScaler
        scaled_features = self.scaler.transform(features_df)

        # Compute positive-class probability
        probabilities = self.model.predict_proba(scaled_features)
        positive_prob = float(probabilities[0][1])

        prediction = int(positive_prob >= self.threshold)

        return {
            "risk_probability": round(positive_prob, 4),
            "prediction": prediction,
            "threshold": self.threshold
        }


predictor = PCOSPredictor()
