import pandas as pd
from typing import Dict, Any, List
from app.schemas import PCOSPredictionRequest

# Exact 13 features in the exact column order expected by the fitted StandardScaler and LogisticRegression model.
# NOTE: Leading/trailing whitespaces in ' Age (yrs)' and 'Height(Cm) ' are intentional to match the training dataset headers.
EXPECTED_FEATURES = [
    ' Age (yrs)',
    'Weight (Kg)',
    'Height(Cm) ',
    'BMI',
    'Cycle(R/I)',
    'Cycle length(days)',
    'Weight gain(Y/N)',
    'hair growth(Y/N)',
    'Skin darkening (Y/N)',
    'Hair loss(Y/N)',
    'Pimples(Y/N)',
    'Fast food (Y/N)',
    'Reg.Exercise(Y/N)'
]

CYCLE_LENGTH_MIN_TRAINING = 0
CYCLE_LENGTH_MAX_TRAINING = 12


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """
    Calculate Body Mass Index (BMI) in kg/m^2.
    """
    height_m = height_cm / 100.0
    return weight_kg / (height_m ** 2)


def encode_cycle_type(cycle_type: str) -> int:
    """
    Encode menstrual cycle regularity to numerical model representation:
    2 = Regular
    4 = Irregular
    """
    normalized = cycle_type.strip().lower()
    if normalized == "regular":
        return 2
    elif normalized == "irregular":
        return 4
    else:
        raise ValueError(f"Invalid cycle_type '{cycle_type}'. Expected 'regular' or 'irregular'.")


def preprocess_input(data: PCOSPredictionRequest) -> Dict[str, Any]:
    """
    Validates, preprocesses, and structures request input into the 13-feature format
    expected by the scaler and ML model.

    Handles out-of-distribution cycle lengths (dataset training range: 0–12 days)
    by generating an explicit warning and safely capping the model-fed value.
    """
    warnings: List[str] = []

    # 1. Calculate BMI
    bmi = calculate_bmi(data.weight, data.height)

    # 2. Map cycle regularity
    cycle_encoded = encode_cycle_type(data.cycle_type)

    # 3. Validate cycle length against training distribution (0–12 days)
    original_cycle_length = data.cycle_length
    model_cycle_length = original_cycle_length

    if original_cycle_length < CYCLE_LENGTH_MIN_TRAINING or original_cycle_length > CYCLE_LENGTH_MAX_TRAINING:
        warnings.append(
            f"Bleeding duration of {original_cycle_length} days is outside the model's observed training range "
            f"({CYCLE_LENGTH_MIN_TRAINING}–{CYCLE_LENGTH_MAX_TRAINING} days). "
            f"Model inference used the configured capped value ({CYCLE_LENGTH_MAX_TRAINING} days)."
        )
        model_cycle_length = min(max(original_cycle_length, CYCLE_LENGTH_MIN_TRAINING), CYCLE_LENGTH_MAX_TRAINING)

    # 4. Construct raw feature mapping with exact feature names
    feature_dict = {
        ' Age (yrs)': data.age,
        'Weight (Kg)': data.weight,
        'Height(Cm) ': data.height,
        'BMI': bmi,
        'Cycle(R/I)': cycle_encoded,
        'Cycle length(days)': model_cycle_length,
        'Weight gain(Y/N)': int(data.weight_gain),
        'hair growth(Y/N)': int(data.hair_growth),
        'Skin darkening (Y/N)': int(data.skin_darkening),
        'Hair loss(Y/N)': int(data.hair_loss),
        'Pimples(Y/N)': int(data.pimples),
        'Fast food (Y/N)': int(data.fast_food),
        'Reg.Exercise(Y/N)': int(data.regular_exercise)
    }

    # 5. Create DataFrame with exact column ordering
    features_df = pd.DataFrame([feature_dict])[EXPECTED_FEATURES]

    return {
        "features_df": features_df,
        "bmi": bmi,
        "warnings": warnings,
        "model_cycle_length": model_cycle_length,
        "original_cycle_length": original_cycle_length
    }
