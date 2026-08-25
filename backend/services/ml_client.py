"""
ML Service Client
Communicates with the standalone Sanjivani ML Prediction & Triage Microservice.
Validates outgoing requests and strictly validates incoming prediction/triage responses.
"""

import os
import logging
from typing import Any, Dict, List, Literal, Optional
import httpx
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("sanjivani_ml_client")


# ==============================================================================
# Custom Client Exceptions (No Fake Fallbacks)
# ==============================================================================
class MLClientError(Exception):
    """Base exception for all ML client communication and validation errors."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class MLConnectionError(MLClientError):
    """Raised when the standalone ML service cannot be reached or connection is refused."""
    pass


class MLTimeoutError(MLClientError):
    """Raised when a request to the standalone ML service times out."""
    pass


class MLHttpError(MLClientError):
    """Raised when the standalone ML service returns a non-2xx HTTP status code."""
    def __init__(self, status_code: int, message: str, body: Optional[str] = None):
        super().__init__(f"ML API HTTP {status_code}: {message}")
        self.status_code = status_code
        self.body = body


class MLResponseValidationError(MLClientError):
    """Raised when the standalone ML service response fails schema or boundary validation."""
    pass


# ==============================================================================
# Response Schema Validation Models
# ==============================================================================
class RedFlagItemSchema(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    category: str
    message: str


class MLServiceResponse(BaseModel):
    """
    Validated response schema returned by the standalone ML Prediction API.
    Guarantees that probabilities, classifications, and triage levels are strictly valid.
    """
    # 1. Machine Learning Inference
    pcos_probability: float = Field(..., ge=0.0, le=1.0)
    model_prediction: int = Field(..., ge=0, le=1)
    model_prediction_label: str

    # 2. Safety & Overall Clinical Triage
    overall_prediction: Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]
    overall_reasons: List[str] = Field(default_factory=list)
    red_flags: List[RedFlagItemSchema] = Field(default_factory=list)
    model_limitations: List[str] = Field(default_factory=list)
    recommendation: str

    # 3. Calculated Metrics & Compatibility
    risk_probability: float = Field(..., ge=0.0, le=1.0)
    bmi: float = Field(..., gt=0.0)
    triage_level: str
    disclaimer: str
    warnings: List[str] = Field(default_factory=list)

    @field_validator("overall_prediction")
    @classmethod
    def validate_overall_prediction(cls, v: str) -> str:
        valid_levels = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid overall_prediction '{v}'. Expected one of: {valid_levels}")
        return v.upper()


# ==============================================================================
# Client Implementation
# ==============================================================================
class MLClient:
    """
    HTTP client for the standalone Sanjivani ML service.
    
    Environment configuration:
        - ML_API_URL: Endpoint URL for prediction (default: http://127.0.0.1:8001/predict)
        - ML_API_TIMEOUT: Request timeout in seconds (default: 5.0)
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ):
        raw_url = api_url or os.getenv("ML_API_URL", "http://127.0.0.1:8001/predict")
        self.api_url = raw_url.strip()

        env_mode = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
        if not api_url and "ML_API_URL" not in os.environ:
            if env_mode in ["production", "prod", "staging"]:
                raise ValueError(
                    "CRITICAL CONFIG ERROR: 'ML_API_URL' environment variable must be explicitly configured in production/staging environments. "
                    "Localhost fallback is disabled for deployed environments."
                )

        raw_timeout = timeout if timeout is not None else float(os.getenv("ML_API_TIMEOUT", "5.0"))
        self.timeout = float(raw_timeout)
        self._transport = transport

    def _get_client(self) -> httpx.Client:
        return httpx.Client(
            timeout=httpx.Timeout(self.timeout),
            transport=self._transport,
        )

    def predict(self, payload: Dict[str, Any]) -> MLServiceResponse:
        """
        Sends a mapped prediction request payload to the ML service POST /predict endpoint,
        validates the response, and returns an `MLServiceResponse`.

        Raises:
            MLTimeoutError: If the request times out.
            MLConnectionError: If connection to the ML service fails.
            MLHttpError: If the server returns a non-2xx status code.
            MLResponseValidationError: If the response is malformed or invalid.
        """
        try:
            with self._get_client() as client:
                response = client.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json", "Accept": "application/json"}
                )
        except httpx.TimeoutException as e:
            logger.error(f"ML service request timed out after {self.timeout}s to {self.api_url}: {e}")
            raise MLTimeoutError(
                f"Prediction service timed out after {self.timeout} seconds."
            ) from e
        except (httpx.ConnectError, httpx.NetworkError) as e:
            logger.error(f"Failed to connect to ML service at {self.api_url}: {e}")
            raise MLConnectionError(
                f"Could not connect to standalone ML prediction service at {self.api_url}."
            ) from e
        except httpx.RequestError as e:
            logger.error(f"HTTP request error when calling ML service: {e}")
            raise MLConnectionError(
                f"ML service communication error: {e}"
            ) from e

        # Handle HTTP Status Codes
        if response.status_code != 200:
            error_body = response.text
            logger.error(f"ML service returned status {response.status_code}: {error_body}")
            raise MLHttpError(
                status_code=response.status_code,
                message=f"ML service returned error HTTP {response.status_code}",
                body=error_body
            )

        # Parse and validate JSON Response
        try:
            raw_data = response.json()
        except Exception as e:
            logger.error(f"Malformed JSON received from ML service: {e}")
            raise MLResponseValidationError(
                f"ML service returned malformed non-JSON response: {e}"
            ) from e

        if not isinstance(raw_data, dict):
            raise MLResponseValidationError(
                f"ML service response must be a JSON object, got {type(raw_data).__name__}"
            )

        try:
            validated = MLServiceResponse(**raw_data)
            return validated
        except Exception as e:
            logger.error(f"ML service response schema validation failed: {e}")
            raise MLResponseValidationError(
                f"Invalid response schema from ML service: {e}"
            ) from e


# Default client instance
ml_client = MLClient()
