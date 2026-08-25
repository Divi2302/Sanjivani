from pydantic import BaseModel, Field
from typing import Optional, List, Any
import datetime

class AssessmentInputSchema(BaseModel):
    patient_id: Optional[int] = None
    patient_code: Optional[str] = "PAT-1001"
    age: int = Field(24, ge=12, le=60)
    height_cm: float = Field(158.0, ge=100.0, le=200.0)
    weight_kg: float = Field(58.0, ge=30.0, le=150.0)
    weight_gain: Any = False
    
    cycle_length: str = "21-35 days"
    cycle_regularity: str = "Regular"
    bleeding_duration_days: int = Field(..., ge=1, le=100, description="Menstrual bleeding / period duration in days")
    heavy_bleeding: bool = Field(..., description="Unusually heavy menstrual bleeding")
    symptom_duration: str = "1-3 months"
    
    facial_hair: Any = False
    acne: Any = False
    hair_loss: Any = False
    dark_skin: Any = False
    
    thyroid: str = "No"
    diabetes: str = "No"
    family_pcos: str = "No"
    existing_pcos_diagnosis: str = "Not diagnosed"
    
    fast_food: str = "Rarely"
    exercise: str = "Regularly"
    diet_quality: str = "Adequate daily meals"
    
    diarrhea: Any = False
    stomach_pain: Any = False
    vomiting: Any = False
    bloating: Any = False
    blood_in_stool: Any = False
    pain_severity: int = Field(1, ge=1, le=5)
    pain_location: str = "None"
    wellbeing: str = "Calm / Stable"
    
    submitted_by_role: str = "ASHA" # ASHA or Patient

class PredictionResultSchema(BaseModel):
    triage_level: str
    triage_code: int
    title: str
    title_hindi: str
    badge_color: str
    risk_probability: float
    risk_category: str
    calculated_bmi: float
    red_flag_triggered: bool
    recommended_action: str
    recommended_action_hindi: str
    reasons: List[Any]
    requires_referral: bool
    requires_followup: bool

class ReferralCreateSchema(BaseModel):
    patient_id: int
    assessment_id: int
    facility_name: str = "Ayushman Arogya Mandir - Rampur"
    facility_type: str = "Ayushman Arogya Mandir"
    notes: Optional[str] = None

class FollowUpCreateSchema(BaseModel):
    patient_id: int
    assessment_id: int
    scheduled_days: int = 7
    asha_notes: Optional[str] = None

class LocationQuerySchema(BaseModel):
    pincode: Optional[str] = "226001"
    village: Optional[str] = "Rampur"
