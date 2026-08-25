from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, List


class RedFlagItem(BaseModel):
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Severity level: low, medium, high, or critical"
    )
    category: str = Field(
        ...,
        description="Category: bleeding_duration, bleeding, pain, gastrointestinal, etc."
    )
    message: str = Field(
        ...,
        description="Clinical description of the identified red flag"
    )


class PCOSPredictionRequest(BaseModel):
    age: int = Field(
        ...,
        ge=10,
        le=100,
        description="Age in years"
    )
    weight: float = Field(
        ...,
        gt=0,
        le=300,
        description="Weight in kg"
    )
    height: float = Field(
        ...,
        gt=0,
        le=250,
        description="Height in cm"
    )

    cycle_type: Literal["regular", "irregular"] = Field(
        ...,
        description="Menstrual cycle regularity ('regular' or 'irregular')"
    )
    cycle_length: int = Field(
        ...,
        gt=0,
        le=100,
        description="Menstrual bleeding / period duration in days"
    )

    weight_gain: bool = Field(
        ...,
        description="Recent unexplained weight gain"
    )
    hair_growth: bool = Field(
        ...,
        description="Excessive hair growth (hirsutism)"
    )
    skin_darkening: bool = Field(
        ...,
        description="Skin darkening (acanthosis nigricans)"
    )
    hair_loss: bool = Field(
        ...,
        description="Hair thinning or loss"
    )
    pimples: bool = Field(
        ...,
        description="Acne or pimples"
    )
    fast_food: bool = Field(
        ...,
        description="Regular fast food consumption"
    )
    regular_exercise: bool = Field(
        ...,
        description="Engages in regular exercise"
    )

    heavy_bleeding: bool = Field(
        default=False,
        description="Heavy menstrual bleeding"
    )
    severe_pain: bool = Field(
        default=False,
        description="Severe pelvic or abdominal pain"
    )
    blood_in_stool: bool = Field(
        default=False,
        description="Blood observed in stool"
    )
    vomiting: bool = Field(
        default=False,
        description="Persistent nausea or vomiting"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )


class PCOSPredictionResponse(BaseModel):
    # 1. Pure ML Model Outputs
    pcos_probability: float = Field(
        ...,
        description="ML Logistic Regression positive-class probability (0.0 to 1.0)"
    )
    model_prediction: int = Field(
        ...,
        description="Binary ML classification (0 for lower risk, 1 for higher risk) based on 0.40 threshold"
    )
    model_prediction_label: str = Field(
        ...,
        description="Human-readable label for pure ML prediction"
    )

    # 2. Hybrid Rule Engine & Overall Triage Outputs
    overall_prediction: Literal["LOW", "MODERATE", "HIGH", "CRITICAL"] = Field(
        ...,
        description="Integrated clinical triage level: LOW, MODERATE, HIGH, or CRITICAL"
    )
    overall_reasons: List[str] = Field(
        default_factory=list,
        description="Deterministic reasons justifying the overall triage level"
    )
    red_flags: List[RedFlagItem] = Field(
        default_factory=list,
        description="Structured clinical red flags detected from symptoms"
    )
    model_limitations: List[str] = Field(
        default_factory=list,
        description="Warnings if inputs fall outside the ML training range/distribution"
    )
    recommendation: str = Field(
        ...,
        description="Guidance and recommendation for the patient"
    )

    # 3. Compatibility & Calculated Health Metrics
    risk_probability: float = Field(
        ...,
        description="Alias for pcos_probability for frontend compatibility"
    )
    bmi: float = Field(
        ...,
        description="Calculated Body Mass Index (BMI) in kg/m^2"
    )
    triage_level: str = Field(
        ...,
        description="Lowercase alias of overall_prediction (low, moderate, high, critical)"
    )
    disclaimer: str = Field(
        default="This is an AI-assisted early screening and triage assessment and not a medical diagnosis.",
        description="Standard medical disclaimer"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Alias for model_limitations"
    )


class HealthCheckResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    model_loaded: bool = Field(..., json_schema_extra={"example": True})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})