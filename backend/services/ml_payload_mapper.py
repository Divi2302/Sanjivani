"""
ML Payload Mapper Service
Translates Sanjivani Assessment inputs into the exact schema required
by the standalone ML Prediction & Clinical Triage Service (PCOSPredictionRequest).
"""

from typing import Any, Dict, Union


class MLPayloadMappingError(ValueError):
    """Raised when an assessment payload cannot be mapped into the ML request schema."""
    pass


# Deterministic categorical mappings
_CYCLE_REGULARITY_MAP = {
    "regular": "regular",
    "irregular": "irregular",
    "frequently missed": "irregular",
}

_EXERCISE_MAP = {
    "regularly": True,
    "occasionally": False,
    "rarely/never": False,
}

# The ML service schema defines `fast_food` as a boolean indicating regular/frequent fast-food consumption.
# "Frequently" indicates regular consumption (True), whereas "Rarely" and "Sometimes" indicate non-regular (False).
_FAST_FOOD_MAP = {
    "rarely": False,
    "sometimes": False,
    "frequently": True,
}


def build_ml_payload(assessment: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """
    Transforms a Sanjivani Assessment (dict or Pydantic model) into the exact dictionary
    accepted by the standalone ML service `PCOSPredictionRequest`.

    IMPORTANT SEMANTIC DISTINCTION:
    - In Sanjivani Main Backend: `cycle_length` represents the menstrual cycle INTERVAL (e.g. '21-35 days').
    - In the Standalone ML Service: `cycle_length` represents the MENSTRUAL BLEEDING DURATION in days (e.g. 5).
    - Therefore, the ML `cycle_length` field is mapped STRICTLY from `bleeding_duration_days` and NEVER
      from the Sanjivani `cycle_length` interval string.

    Raises:
        MLPayloadMappingError: If any required field is missing, invalid, or cannot be mapped.
    """
    if hasattr(assessment, "model_dump"):
        data = assessment.model_dump()
    elif hasattr(assessment, "dict"):
        data = assessment.dict()
    elif isinstance(assessment, dict):
        data = assessment
    else:
        raise MLPayloadMappingError(
            f"Unsupported assessment input type '{type(assessment).__name__}'. Expected dict or Pydantic model."
        )

    # 1. Demographics & Body Metrics
    try:
        if "age" not in data or data["age"] is None:
            raise MLPayloadMappingError("Missing required field 'age'.")
        age = int(data["age"])
        if not (10 <= age <= 100):
            raise MLPayloadMappingError(f"Invalid age: {age}. Must be between 10 and 100.")
    except (ValueError, TypeError) as e:
        raise MLPayloadMappingError(f"Invalid 'age' value: {e}") from e

    try:
        raw_weight = data.get("weight_kg") if "weight_kg" in data else data.get("weight")
        if raw_weight is None:
            raise MLPayloadMappingError("Missing required field 'weight_kg' / 'weight'.")
        weight = float(raw_weight)
        if not (0 < weight <= 300):
            raise MLPayloadMappingError(f"Invalid weight: {weight} kg. Must be between 0 and 300 kg.")
    except (ValueError, TypeError) as e:
        raise MLPayloadMappingError(f"Invalid weight value: {e}") from e

    try:
        raw_height = data.get("height_cm") if "height_cm" in data else data.get("height")
        if raw_height is None:
            raise MLPayloadMappingError("Missing required field 'height_cm' / 'height'.")
        height = float(raw_height)
        if not (0 < height <= 250):
            raise MLPayloadMappingError(f"Invalid height: {height} cm. Must be between 0 and 250 cm.")
    except (ValueError, TypeError) as e:
        raise MLPayloadMappingError(f"Invalid height value: {e}") from e

    # 2. Menstrual Pattern & Duration
    # Cycle regularity mapping (Regular -> 'regular', Irregular/Frequently missed -> 'irregular')
    raw_reg = data.get("cycle_regularity") if "cycle_regularity" in data else data.get("cycle_type")
    if not raw_reg or not isinstance(raw_reg, str):
        raise MLPayloadMappingError("Missing or invalid 'cycle_regularity'.")
    normalized_reg = raw_reg.strip().lower()
    if normalized_reg not in _CYCLE_REGULARITY_MAP:
        raise MLPayloadMappingError(
            f"Unknown cycle regularity '{raw_reg}'. Expected one of: Regular, Irregular, Frequently missed."
        )
    cycle_type = _CYCLE_REGULARITY_MAP[normalized_reg]

    # Bleeding duration mapping (CRITICAL: Must receive bleeding_duration_days, NOT cycle_length interval)
    raw_duration = data.get("bleeding_duration_days")
    if raw_duration is None:
        raise MLPayloadMappingError(
            "Missing required field 'bleeding_duration_days'. Menstrual bleeding duration must be explicitly provided."
        )
    try:
        bleeding_duration = int(raw_duration)
        if not (1 <= bleeding_duration <= 100):
            raise MLPayloadMappingError(
                f"Invalid bleeding duration: {bleeding_duration} days. Must be between 1 and 100 days."
            )
    except (ValueError, TypeError) as e:
        raise MLPayloadMappingError(f"Invalid 'bleeding_duration_days' value: {e}") from e

    # 3. Androgenic / PCOS Symptoms
    def _parse_bool(field_name: str, val: Any) -> bool:
        if val is None:
            raise MLPayloadMappingError(f"Missing required clinical boolean field '{field_name}'.")
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)) and val in (0, 1):
            return bool(val)
        s = str(val).strip().lower()
        if s in ("true", "1", "yes"):
            return True
        if s in ("false", "0", "no"):
            return False
        raise MLPayloadMappingError(f"Invalid boolean value '{val}' for field '{field_name}'.")

    weight_gain = _parse_bool("weight_gain", data.get("weight_gain"))
    hair_growth = _parse_bool("facial_hair", data.get("facial_hair") if "facial_hair" in data else data.get("hair_growth"))
    skin_darkening = _parse_bool("dark_skin", data.get("dark_skin") if "dark_skin" in data else data.get("skin_darkening"))
    hair_loss = _parse_bool("hair_loss", data.get("hair_loss"))
    pimples = _parse_bool("acne", data.get("acne") if "acne" in data else data.get("pimples"))

    # 4. Lifestyle & Nutrition Mappings
    raw_fast_food = data.get("fast_food")
    if raw_fast_food is None:
        raise MLPayloadMappingError("Missing required field 'fast_food'.")
    if isinstance(raw_fast_food, bool):
        fast_food = raw_fast_food
    else:
        norm_ff = str(raw_fast_food).strip().lower()
        if norm_ff not in _FAST_FOOD_MAP:
            raise MLPayloadMappingError(
                f"Unknown fast food value '{raw_fast_food}'. Expected one of: Rarely, Sometimes, Frequently."
            )
        fast_food = _FAST_FOOD_MAP[norm_ff]

    raw_exercise = data.get("exercise") if "exercise" in data else data.get("regular_exercise")
    if raw_exercise is None:
        raise MLPayloadMappingError("Missing required field 'exercise'.")
    if isinstance(raw_exercise, bool):
        regular_exercise = raw_exercise
    else:
        norm_ex = str(raw_exercise).strip().lower()
        if norm_ex not in _EXERCISE_MAP:
            raise MLPayloadMappingError(
                f"Unknown exercise value '{raw_exercise}'. Expected one of: Regularly, Occasionally, Rarely/Never."
            )
        regular_exercise = _EXERCISE_MAP[norm_ex]

    # 5. Acute Symptoms & Safety Red Flags
    heavy_bleeding = _parse_bool("heavy_bleeding", data.get("heavy_bleeding"))

    # Pain Mapping: In Sanjivani frontend, scale 1-5 is used where 4 is labeled 'Severe' and 5 is 'Very Severe'.
    # Severe pelvic/abdominal pain (severe_pain) is True if pain_severity >= 4, else False.
    if "severe_pain" in data and isinstance(data["severe_pain"], bool):
        severe_pain = data["severe_pain"]
    elif "pain_severity" in data and data["pain_severity"] is not None:
        try:
            pain_level = int(data["pain_severity"])
            severe_pain = pain_level >= 4
        except (ValueError, TypeError) as e:
            raise MLPayloadMappingError(f"Invalid 'pain_severity' value: {e}") from e
    else:
        severe_pain = False

    blood_in_stool = _parse_bool("blood_in_stool", data.get("blood_in_stool"))
    vomiting = _parse_bool("vomiting", data.get("vomiting"))

    # 6. Construct exact PCOSPredictionRequest dictionary (16 features)
    return {
        "age": age,
        "weight": weight,
        "height": height,
        "cycle_type": cycle_type,
        "cycle_length": bleeding_duration,
        "weight_gain": weight_gain,
        "hair_growth": hair_growth,
        "skin_darkening": skin_darkening,
        "hair_loss": hair_loss,
        "pimples": pimples,
        "fast_food": fast_food,
        "regular_exercise": regular_exercise,
        "heavy_bleeding": heavy_bleeding,
        "severe_pain": severe_pain,
        "blood_in_stool": blood_in_stool,
        "vomiting": vomiting,
    }
