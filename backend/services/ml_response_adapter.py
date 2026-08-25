"""
ML Response Compatibility Adapter
Transforms the validated external ML service response into legacy platform structures
required by the current frontend, database schema, referral triggers, and follow-up schedulers.

DOES NOT perform any clinical decision-making. The external ML service is authoritative.
"""

from typing import Any, Dict, List, Union
from services.ml_client import MLServiceResponse
from database.schemas import PredictionResultSchema


# Explicit Mapping from Canonical ML Overall Prediction to Legacy Sanjivani Triage Levels
# NOTE: The canonical result remains 'LOW', 'MODERATE', 'HIGH', or 'CRITICAL'.
# 'LEVEL 1', 'LEVEL 2', 'LEVEL 3' are STRICTLY backward-compatibility representations
# for the current frontend badges, referral creation, and follow-up scheduling logic.
_TRIAGE_COMPATIBILITY_MAP = {
    "LOW": {
        "legacy_triage_level": "LEVEL 1",
        "triage_code": 1,
        "badge_color": "green",
        "title": "Low PCOS Indicator Risk",
        "title_hindi": "न्यूनतम जोखिम (Low Risk)",
        "risk_category": "Low Risk",
        "requires_referral": False,
        "requires_followup": False,
    },
    "MODERATE": {
        "legacy_triage_level": "LEVEL 2",
        "triage_code": 2,
        "badge_color": "yellow",
        "title": "Further Clinical Assessment Recommended",
        "title_hindi": "आगे की जांच एवं परामर्श आवश्यक",
        "risk_category": "Moderate Risk",
        "requires_referral": True,
        "requires_followup": True,
    },
    "HIGH": {
        "legacy_triage_level": "LEVEL 3",
        "triage_code": 3,
        "badge_color": "red",
        "title": "High Priority Clinical Referral Required",
        "title_hindi": "चिकित्सकीय परामर्श / अति आवश्यक रेफरल",
        "risk_category": "High Risk",
        "requires_referral": True,
        "requires_followup": True,
    },
    "CRITICAL": {
        "legacy_triage_level": "LEVEL 3",
        "triage_code": 3,
        "badge_color": "red",
        "title": "Critical Safety Escalation Required",
        "title_hindi": "अति आवश्यक आपातकालीन / विशेषज्ञ रेफरल",
        "risk_category": "Critical Risk",
        "requires_referral": True,
        "requires_followup": True,
    },
}


def adapt_ml_response_to_legacy(
    ml_response: Union[MLServiceResponse, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Normalizes a validated MLServiceResponse into the legacy dictionary structure
    expected by `PredictionResultSchema`, database persistence, and referral workflows.

    Args:
        ml_response: Validated response from MLClient.predict()

    Returns:
        Dictionary containing both canonical ML results and legacy compatibility fields.
    """
    if isinstance(ml_response, MLServiceResponse):
        raw = ml_response.model_dump()
    elif isinstance(ml_response, dict):
        raw = ml_response
    else:
        raise ValueError(f"Unsupported ML response type: {type(ml_response).__name__}")

    canonical_overall = raw.get("overall_prediction", "LOW").upper()
    compat = _TRIAGE_COMPATIBILITY_MAP.get(
        canonical_overall,
        _TRIAGE_COMPATIBILITY_MAP["LOW"]
    )

    # Convert raw string reasons into reason-card objects for UI compatibility
    # Do not invent Hindi translations; frontend falls back to title if title_hindi is empty
    reasons_list: List[Dict[str, str]] = [
        {
            "title": str(r),
            "title_hindi": "",
            "category": "Clinical Indicator"
        }
        for r in raw.get("overall_reasons", [])
    ]

    red_flags = raw.get("red_flags", [])
    red_flag_triggered = len(red_flags) > 0

    pcos_prob = float(raw.get("pcos_probability", raw.get("risk_probability", 0.0)))
    bmi = float(raw.get("bmi", 22.0))
    recommendation = raw.get("recommendation", "")

    # Build legacy PredictionResultSchema compatible dictionary
    return {
        "triage_level": compat["legacy_triage_level"],
        "triage_code": compat["triage_code"],
        "title": compat["title"],
        "title_hindi": compat["title_hindi"],
        "badge_color": compat["badge_color"],
        "risk_probability": round(pcos_prob, 4),
        "risk_category": compat["risk_category"],
        "calculated_bmi": round(bmi, 2),
        "red_flag_triggered": red_flag_triggered,
        "recommended_action": recommendation,
        "recommended_action_hindi": "",
        "reasons": reasons_list,
        "requires_referral": compat["requires_referral"],
        "requires_followup": compat["requires_followup"],
        # Extra canonical fields for forward compatibility
        "canonical_overall_prediction": canonical_overall,
        "model_prediction": raw.get("model_prediction", 0),
        "model_prediction_label": raw.get("model_prediction_label", ""),
        "model_limitations": raw.get("model_limitations", []),
        "red_flags": red_flags,
    }


def to_prediction_result_schema(adapted_dict: Dict[str, Any]) -> PredictionResultSchema:
    """Helper to instantiate PredictionResultSchema from adapted dictionary."""
    return PredictionResultSchema(
        triage_level=adapted_dict["triage_level"],
        triage_code=adapted_dict["triage_code"],
        title=adapted_dict["title"],
        title_hindi=adapted_dict["title_hindi"],
        badge_color=adapted_dict["badge_color"],
        risk_probability=adapted_dict["risk_probability"],
        risk_category=adapted_dict["risk_category"],
        calculated_bmi=adapted_dict["calculated_bmi"],
        red_flag_triggered=adapted_dict["red_flag_triggered"],
        recommended_action=adapted_dict["recommended_action"],
        recommended_action_hindi=adapted_dict["recommended_action_hindi"],
        reasons=adapted_dict["reasons"],
        requires_referral=adapted_dict["requires_referral"],
        requires_followup=adapted_dict["requires_followup"],
    )
