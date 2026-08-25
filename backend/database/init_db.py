import json
import datetime
from sqlalchemy import text
from database.db import engine, Base, SessionLocal
from database.models import Patient, Assessment, Referral, FollowUp, HealthcareCenter, AshaUser

def migrate_db():
    """
    Safely adds new columns to existing SQLite tables if not already present.
    Non-destructive; does not delete, drop, or recreate tables.
    """
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(assessments);"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            if existing_columns:
                if "bleeding_duration_days" not in existing_columns:
                    conn.execute(text("ALTER TABLE assessments ADD COLUMN bleeding_duration_days INTEGER;"))
                    print("Schema migration: Added 'bleeding_duration_days' column to assessments table.")
                    
                if "heavy_bleeding" not in existing_columns:
                    conn.execute(text("ALTER TABLE assessments ADD COLUMN heavy_bleeding BOOLEAN;"))
                    print("Schema migration: Added 'heavy_bleeding' column to assessments table.")

                # Canonical Standalone ML Microservice Columns (Phase 4)
                new_canonical_cols = [
                    ("ml_available", "BOOLEAN"),
                    ("ml_error", "VARCHAR"),
                    ("pcos_probability", "FLOAT"),
                    ("model_prediction", "INTEGER"),
                    ("model_prediction_label", "VARCHAR"),
                    ("overall_prediction", "VARCHAR"),
                    ("overall_reasons_json", "TEXT"),
                    ("red_flags_json", "TEXT"),
                    ("recommendation", "TEXT"),
                    ("warnings_json", "TEXT"),
                    ("model_limitations_json", "TEXT"),
                    ("disclaimer", "TEXT"),
                    # Safety Triage V2 Columns
                    ("dizziness", "BOOLEAN"),
                    ("fainting", "BOOLEAN"),
                    ("shortness_of_breath", "BOOLEAN"),
                    ("rapid_pad_saturation", "BOOLEAN"),
                    ("flooding_gushing", "BOOLEAN"),
                    ("large_blood_clots", "BOOLEAN"),
                    ("pregnancy_possible", "BOOLEAN"),
                    ("sudden_severe_pelvic_pain", "BOOLEAN"),
                    ("one_sided_pelvic_pain", "BOOLEAN"),
                    ("shoulder_tip_pain", "BOOLEAN"),
                    ("fever_chills", "BOOLEAN"),
                    ("unable_to_keep_fluids", "BOOLEAN"),
                    ("bleeding_between_periods", "BOOLEAN"),
                    ("bleeding_after_sex", "BOOLEAN"),
                ]

                for col_name, col_type in new_canonical_cols:
                    if col_name not in existing_columns:
                        conn.execute(text(f"ALTER TABLE assessments ADD COLUMN {col_name} {col_type};"))
                        print(f"Schema migration: Added '{col_name}' ({col_type}) column to assessments table.")
        except Exception as e:
            print(f"Migration check exception: {e}")

def init_db():
    Base.metadata.create_all(bind=engine)
    migrate_db()
    db = SessionLocal()

    # 1. Seed Healthcare Centers (Ayushman Arogya Mandir, PHCs, CHCs)
    if db.query(HealthcareCenter).count() == 0:
        centers = [
            HealthcareCenter(
                name="Ayushman Arogya Mandir - Rampur",
                type="Ayushman Arogya Mandir",
                village="Rampur",
                district="Lucknow",
                pincode="226001",
                address="Near Panchayat Bhavan, Rampur Village",
                distance_km=1.2,
                contact_number="+91 94150 12345",
                assigned_asha_name="Sunita Devi",
                assigned_asha_phone="+91 98765 43210",
                latitude=26.8467,
                longitude=80.9462
            ),
            HealthcareCenter(
                name="Primary Health Centre (PHC) - Malihabad",
                type="PHC",
                village="Malihabad",
                district="Lucknow",
                pincode="226102",
                address="Main Highway Road, Malihabad",
                distance_km=4.5,
                contact_number="+91 522 284102",
                assigned_asha_name="Meena Verma",
                assigned_asha_phone="+91 98765 43211",
                latitude=26.9200,
                longitude=80.7100
            ),
            HealthcareCenter(
                name="Ayushman Arogya Mandir - Kakori",
                type="Ayushman Arogya Mandir",
                village="Kakori",
                district="Lucknow",
                pincode="226101",
                address="Sub-Centre Colony, Kakori",
                distance_km=3.8,
                contact_number="+91 94150 54321",
                assigned_asha_name="Pooja Kumari",
                assigned_asha_phone="+91 98765 43212",
                latitude=26.8800,
                longitude=80.8000
            ),
            HealthcareCenter(
                name="Community Health Centre (CHC) - Sarojini Nagar",
                type="CHC",
                village="Sarojini Nagar",
                district="Lucknow",
                pincode="226008",
                address="Near Block Development Office, Sarojini Nagar",
                distance_km=7.2,
                contact_number="+91 522 243501",
                assigned_asha_name="Radha Yadav",
                assigned_asha_phone="+91 98765 43213",
                latitude=26.7500,
                longitude=80.8700
            )
        ]
        db.add_all(centers)
        
    # 2. Seed Default ASHA User
    if db.query(AshaUser).count() == 0:
        asha = AshaUser(
            username="asha_sunita",
            name="Sunita Devi",
            center_name="Ayushman Arogya Mandir - Rampur",
            village="Rampur",
            phone="+91 98765 43210"
        )
        db.add(asha)

    # 3. Seed Initial Sample Patient Assessments for ASHA Dashboard Demo
    if db.query(Patient).count() == 0:
        sample_cases = [
            {
                "code": "PAT-1089",
                "name": "Priya Sharma",
                "age": 23,
                "triage": "LEVEL 2",
                "risk_prob": 0.58,
                "category": "Moderate Risk",
                "cycle_reg": "Irregular",
                "cycle_len": ">35 days",
                "facial_hair": True,
                "acne": True,
                "red_flag": False,
                "reasons": ["Persistent Menstrual Irregularity", "Reported Excess Facial Hair", "Extended Cycle Length (>35 Days)"],
                "status": "Referred"
            },
            {
                "code": "PAT-1090",
                "name": "Kavita Devi",
                "age": 28,
                "triage": "LEVEL 3",
                "risk_prob": 0.84,
                "category": "Elevated Risk",
                "cycle_reg": "Frequently missed",
                "cycle_len": ">35 days",
                "facial_hair": True,
                "acne": True,
                "red_flag": True,
                "reasons": ["Blood reported in stool (Safety Override)", "Severe Pelvic Pain (5/5)", "Persistent Menstrual Irregularity"],
                "status": "Follow-up Due"
            },
            {
                "code": "PAT-1091",
                "name": "Anita Kumari",
                "age": 19,
                "triage": "LEVEL 1",
                "risk_prob": 0.18,
                "category": "Low Risk",
                "cycle_reg": "Regular",
                "cycle_len": "21-35 days",
                "facial_hair": False,
                "acne": False,
                "red_flag": False,
                "reasons": ["No Significant Endocrine or Red-Flag Indicators Detected"],
                "status": "Completed"
            },
            {
                "code": "PAT-1092",
                "name": "Rekha Singh",
                "age": 31,
                "triage": "LEVEL 2",
                "risk_prob": 0.62,
                "category": "Elevated Risk",
                "cycle_reg": "Irregular",
                "cycle_len": "Varies significantly",
                "facial_hair": False,
                "acne": True,
                "red_flag": False,
                "reasons": ["Extended Cycle Length", "Unexplained Recent Weight Gain", "Elevated BMI"],
                "status": "Pending"
            }
        ]

        for sc in sample_cases:
            pt = Patient(
                patient_code=sc["code"],
                name=sc["name"],
                age=sc["age"],
                village="Rampur",
                district="Lucknow",
                pincode="226001"
            )
            db.add(pt)
            db.flush()

            ast = Assessment(
                patient_id=pt.id,
                age=sc["age"],
                height_cm=156.0,
                weight_kg=62.0,
                bmi=25.5,
                weight_gain=True,
                cycle_length=sc["cycle_len"],
                cycle_regularity=sc["cycle_reg"],
                symptom_duration="3-6 months",
                facial_hair=sc["facial_hair"],
                acne=sc["acne"],
                hair_loss=False,
                dark_skin=sc["red_flag"],
                thyroid="No",
                diabetes="No",
                family_pcos="Yes" if sc["triage"] != "LEVEL 1" else "No",
                existing_pcos_diagnosis="Not diagnosed",
                fast_food="Sometimes",
                exercise="Occasionally",
                diet_quality="Adequate daily meals",
                diarrhea=False,
                stomach_pain=sc["red_flag"],
                vomiting=False,
                bloating=False,
                blood_in_stool=sc["red_flag"],
                pain_severity=5 if sc["red_flag"] else 2,
                pain_location="Pelvic" if sc["triage"] != "LEVEL 1" else "None",
                wellbeing="Calm / Stable",
                risk_probability=sc["risk_prob"],
                risk_category=sc["category"],
                triage_level=sc["triage"],
                red_flag_triggered=sc["red_flag"],
                reasons_json=json.dumps(sc["reasons"]),
                submitted_by_role="ASHA"
            )
            db.add(ast)
            db.flush()

            if sc["triage"] in ["LEVEL 2", "LEVEL 3"]:
                ref = Referral(
                    patient_id=pt.id,
                    assessment_id=ast.id,
                    facility_name="Ayushman Arogya Mandir - Rampur",
                    facility_type="Ayushman Arogya Mandir",
                    status=sc["status"],
                    notes="Recommended clinical examination & ultrasound."
                )
                db.add(ref)
                db.flush()

                flw = FollowUp(
                    patient_id=pt.id,
                    assessment_id=ast.id,
                    scheduled_date=datetime.datetime.utcnow() + datetime.timedelta(days=3 if sc["triage"]=="LEVEL 3" else 7),
                    status="Pending" if sc["status"] != "Completed" else "Completed",
                    asha_notes="Followup scheduled for village visit."
                )
                db.add(flw)

    db.commit()
    db.close()
    print("SQLite database initialized and seeded successfully.")

if __name__ == "__main__":
    init_db()
