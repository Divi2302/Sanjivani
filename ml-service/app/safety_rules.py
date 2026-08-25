from typing import Dict, Any, List, Optional
from app.schemas import PCOSPredictionRequest, RedFlagItem

# Centralized threshold constants for menstrual duration
BLEEDING_NORMAL_MIN = 2
BLEEDING_NORMAL_MAX = 7
BLEEDING_PROLONGED_MIN = 8
BLEEDING_PROLONGED_MAX = 10
BLEEDING_SIGNIFICANT_MIN = 11
BLEEDING_SIGNIFICANT_MAX = 20
BLEEDING_EXTREME_MIN = 21

TRAINING_CYCLE_LENGTH_MIN = 0
TRAINING_CYCLE_LENGTH_MAX = 12

HIGH_ML_PROBABILITY_THRESHOLD = 0.70


def evaluate_safety_and_red_flags(
    data: PCOSPredictionRequest,
    existing_limitations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Lightweight deterministic safety guardrail evaluating only existing high-risk symptoms.
    Safety symptoms do NOT alter the Logistic Regression model's pure feature inputs or probability.
    """
    red_flags: List[RedFlagItem] = []
    clinical_reasons: List[str] = []
    model_limitations: List[str] = list(existing_limitations) if existing_limitations else []

    cycle_len = data.cycle_length

    # 1. Menstrual Bleeding Duration Evaluation (cycle_length represents duration in days)
    if cycle_len <= 1:
        clinical_reasons.append("Unusually short bleeding duration reported.")

    elif BLEEDING_PROLONGED_MIN <= cycle_len <= BLEEDING_PROLONGED_MAX:
        red_flags.append(RedFlagItem(
            severity="medium",
            category="bleeding_duration",
            message=f"Prolonged bleeding duration detected ({cycle_len} days)."
        ))
        clinical_reasons.append(f"Prolonged bleeding duration reported ({cycle_len} days).")

    elif BLEEDING_SIGNIFICANT_MIN <= cycle_len <= BLEEDING_SIGNIFICANT_MAX:
        red_flags.append(RedFlagItem(
            severity="high",
            category="bleeding_duration",
            message=f"Significantly prolonged bleeding duration detected ({cycle_len} days)."
        ))
        clinical_reasons.append(f"Prolonged bleeding duration reported ({cycle_len} days).")
        if cycle_len > TRAINING_CYCLE_LENGTH_MAX:
            limitation_msg = (
                f"Bleeding duration of {cycle_len} days is outside the model's observed training range "
                f"({TRAINING_CYCLE_LENGTH_MIN}–{TRAINING_CYCLE_LENGTH_MAX} days). "
                f"Model inference used the configured capped value ({TRAINING_CYCLE_LENGTH_MAX} days)."
            )
            if not any(f"{cycle_len} days" in lim and "outside" in lim for lim in model_limitations):
                model_limitations.append(limitation_msg)

    elif cycle_len >= BLEEDING_EXTREME_MIN:
        red_flags.append(RedFlagItem(
            severity="critical",
            category="bleeding_duration",
            message=f"Extremely prolonged bleeding duration detected ({cycle_len} days)."
        ))
        clinical_reasons.append(f"Extremely prolonged bleeding duration reported ({cycle_len} days).")
        limitation_msg = (
            f"Bleeding duration of {cycle_len} days is outside the model's observed training range "
            f"({TRAINING_CYCLE_LENGTH_MIN}–{TRAINING_CYCLE_LENGTH_MAX} days). "
            f"Model inference used the configured capped value ({TRAINING_CYCLE_LENGTH_MAX} days)."
        )
        if not any(f"{cycle_len} days" in lim and "outside" in lim for lim in model_limitations):
            model_limitations.append(limitation_msg)

    # 2. Bleeding Severity
    if data.heavy_bleeding:
        red_flags.append(RedFlagItem(
            severity="high",
            category="bleeding",
            message="Heavy menstrual bleeding reported."
        ))
        clinical_reasons.append("Heavy menstrual bleeding reported.")

    # 3. Pain Red Flags
    if data.severe_pain:
        red_flags.append(RedFlagItem(
            severity="high",
            category="pain",
            message="Severe pelvic or lower abdominal pain reported."
        ))
        clinical_reasons.append("Severe pain reported.")

    # 4. Gastrointestinal Red Flags
    if data.blood_in_stool:
        red_flags.append(RedFlagItem(
            severity="critical",
            category="gastrointestinal",
            message="Blood in stool observed — urgent clinical medical evaluation recommended."
        ))
        clinical_reasons.append("Blood in stool reported.")

    if data.vomiting:
        red_flags.append(RedFlagItem(
            severity="high",
            category="gastrointestinal",
            message="Persistent nausea or vomiting reported."
        ))
        clinical_reasons.append("Vomiting reported.")

    return {
        "red_flags": red_flags,
        "clinical_reasons": clinical_reasons,
        "model_limitations": model_limitations
    }


def evaluate_overall_triage(
    data: PCOSPredictionRequest,
    pcos_probability: float,
    model_prediction: int,
    base_warnings: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    ML-FIRST Triage Architecture with Lightweight Safety Guardrail.
    
    1. Primary Risk Engine: Logistic Regression Model (pcos_probability & model_prediction).
    2. Guardrail Layer: Checks existing acute symptoms (bleeding duration, heavy bleeding, severe pain, vomiting, blood in stool).
    3. Escalation-Only Guarantee: Guardrail can only ESCALATE triage (CRITICAL > HIGH > MODERATE > LOW).
    4. Zero-Fabrication Guarantee: Pure ML probability is NEVER altered or faked.
    """
    safety_result = evaluate_safety_and_red_flags(data, existing_limitations=base_warnings)
    red_flags: List[RedFlagItem] = safety_result["red_flags"]
    model_limitations: List[str] = safety_result["model_limitations"]

    cycle_len = data.cycle_length

    # Structured Prioritization of Legitimate User-Facing Clinical Reasons:
    # Priority 1: Critical/High Safety Findings
    safety_findings: List[str] = list(safety_result["clinical_reasons"])

    # Priority 2: Menstrual Abnormalities
    menstrual_findings: List[str] = []
    if data.cycle_type.lower() == "irregular":
        menstrual_findings.append("Irregular menstrual cycle pattern reported.")

    # Priority 3: Strong PCOS-Related Clinical Features
    pcos_findings: List[str] = []
    if data.weight_gain:
        pcos_findings.append("Recent weight gain reported.")
    if data.hair_growth:
        pcos_findings.append("Increased facial hair growth reported.")
    if data.pimples:
        pcos_findings.append("Acne/pimples reported.")
    if data.hair_loss:
        pcos_findings.append("Hair loss reported.")
    if data.skin_darkening:
        pcos_findings.append("Skin darkening reported.")

    # Priority 4: Lifestyle Context
    lifestyle_findings: List[str] = []
    if data.fast_food:
        lifestyle_findings.append("Frequent fast-food intake reported.")
    if not data.regular_exercise:
        lifestyle_findings.append("Limited regular exercise reported.")

    # Assemble prioritized clinical reasons (Deduplicated)
    overall_reasons = list(dict.fromkeys(
        safety_findings + menstrual_findings + pcos_findings + lifestyle_findings
    ))

    androgenic_symptoms_count = sum([
        data.weight_gain,
        data.hair_growth,
        data.skin_darkening,
        data.hair_loss,
        data.pimples
    ])
    if androgenic_symptoms_count >= 3:
        overall_reasons.append(f"Multiple androgenic/metabolic indicators present ({androgenic_symptoms_count} reported).")

    high_red_flags_count = sum(1 for rf in red_flags if rf.severity in ("high", "critical"))

    # =========================================================================
    # 1. CRITICAL Tier (Emergency / Immediate Evaluation)
    # =========================================================================
    is_critical = (
        # Bleeding duration >= 21 days
        cycle_len >= BLEEDING_EXTREME_MIN
        # Blood in stool (acute GI red flag)
        or data.blood_in_stool
        # Severe pain combined with heavy bleeding, persistent vomiting, or duration >= 11 days
        or (data.severe_pain and (data.heavy_bleeding or data.vomiting or cycle_len >= BLEEDING_SIGNIFICANT_MIN))
    )

    # =========================================================================
    # 2. HIGH Tier (Prompt Clinical Assessment)
    # =========================================================================
    is_high = (
        # Bleeding duration 11–20 days
        (BLEEDING_SIGNIFICANT_MIN <= cycle_len <= BLEEDING_SIGNIFICANT_MAX)
        # Heavy menstrual bleeding
        or data.heavy_bleeding
        # Severe pelvic/abdominal pain
        or data.severe_pain
        # Persistent vomiting
        or data.vomiting
        # Multiple acute safety red flags
        or (high_red_flags_count >= 2)
        # High statistical PCOS probability from ML model
        or (pcos_probability >= HIGH_ML_PROBABILITY_THRESHOLD)
    )

    # =========================================================================
    # 3. MODERATE Tier (Clinical Consultation Recommended)
    # =========================================================================
    is_moderate = (
        # Bleeding duration 8–10 days
        (BLEEDING_PROLONGED_MIN <= cycle_len <= BLEEDING_PROLONGED_MAX)
        # Primary ML prediction is positive (Higher PCOS risk)
        or (model_prediction == 1)
        # ML screening score elevated
        or (pcos_probability >= 0.40)
        # Clinical PCOS pattern indicators
        or (data.cycle_type.lower() == "irregular" and androgenic_symptoms_count >= 2)
        or (cycle_len <= 1 and androgenic_symptoms_count >= 2)
        or (androgenic_symptoms_count >= 3)
    )

    # =========================================================================
    # Deterministic Precedence Application: CRITICAL > HIGH > MODERATE > LOW
    # =========================================================================
    if is_critical:
        overall_prediction = "CRITICAL"
        recommendation = "Urgent emergency medical evaluation is strongly recommended due to critical clinical safety indicators."

    elif is_high:
        overall_prediction = "HIGH"
        recommendation = "Prompt clinical assessment by a healthcare professional (such as a gynecologist or physician) is recommended."

    elif is_moderate:
        overall_prediction = "MODERATE"
        recommendation = "Clinical consultation is recommended to evaluate your symptoms and menstrual patterns."

    else:
        overall_prediction = "LOW"
        if data.cycle_type.lower() == "irregular" or cycle_len <= 1:
            recommendation = (
                "Monitor menstrual patterns and consider consulting a healthcare professional "
                "if this pattern persists or additional symptoms develop."
            )
        else:
            recommendation = (
                "No immediate high-risk safety patterns detected. Continue routine health monitoring "
                "and consult a doctor if symptoms change."
            )

    return {
        "overall_prediction": overall_prediction,
        "overall_reasons": overall_reasons,
        "red_flags": red_flags,
        "model_limitations": model_limitations,
        "recommendation": recommendation
    }

