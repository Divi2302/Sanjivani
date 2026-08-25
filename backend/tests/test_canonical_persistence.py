"""
Phase 4 Verification Tests: Canonical ML Result Persistence & Backward Compatibility
"""

import os
import sys
import json
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app
from database.db import SessionLocal, engine
from database.models import Assessment, Patient, Referral, FollowUp
from database.init_db import init_db
from services.ml_client import MLServiceResponse, MLTimeoutError, RedFlagItemSchema


class TestCanonicalPersistence(unittest.TestCase):
    """Test suite verifying canonical ML result persistence and backward compatibility."""

    def setUp(self):
        init_db()
        self.client = TestClient(app)
        self.db = SessionLocal()

        self.sample_payload = {
            "patient_code": "PAT-PHASE4-TEST",
            "age": 24,
            "height_cm": 158.0,
            "weight_kg": 58.0,
            "weight_gain": True,
            "cycle_length": "21-35 days",
            "cycle_regularity": "Regular",
            "bleeding_duration_days": 5,
            "heavy_bleeding": False,
            "symptom_duration": "1-3 months",
            "facial_hair": True,
            "acne": True,
            "hair_loss": False,
            "dark_skin": False,
            "thyroid": "No",
            "diabetes": "No",
            "family_pcos": "No",
            "existing_pcos_diagnosis": "Not diagnosed",
            "fast_food": "Frequently",
            "exercise": "Regularly",
            "diet_quality": "Adequate daily meals",
            "diarrhea": False,
            "stomach_pain": False,
            "vomiting": False,
            "bloating": False,
            "blood_in_stool": False,
            "pain_severity": 1,
            "pain_location": "None",
            "wellbeing": "Calm / Stable",
            "submitted_by_role": "ASHA"
        }

    def tearDown(self):
        self.db.close()

    def _mock_ml_response(
        self,
        overall: str,
        prob: float,
        model_pred: int,
        label: str,
        reasons: list = None,
        red_flags: list = None,
        recommendation: str = "Consult healthcare provider.",
        warnings: list = None,
        limitations: list = None,
        disclaimer: str = "AI-assisted screening tool."
    ):
        rf_objs = []
        if red_flags:
            for rf in red_flags:
                if isinstance(rf, dict):
                    rf_objs.append(RedFlagItemSchema(**rf))
                else:
                    rf_objs.append(rf)

        return MLServiceResponse(
            pcos_probability=prob,
            model_prediction=model_pred,
            model_prediction_label=label,
            overall_prediction=overall,
            overall_reasons=reasons or [f"Reason for {overall}."],
            red_flags=rf_objs,
            model_limitations=limitations or [],
            recommendation=recommendation,
            risk_probability=prob,
            bmi=23.23,
            triage_level=overall.lower(),
            disclaimer=disclaimer,
            warnings=warnings or []
        )

    # 1. LOW Assessment Persistence Test
    @patch("main.ml_client.predict")
    def test_low_assessment_canonical_persistence(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response(
            overall="LOW",
            prob=0.1425,
            model_pred=0,
            label="Lower PCOS-related risk",
            reasons=["ML model detected lower PCOS-related probability (14.2%)."],
            red_flags=[],
            recommendation="Continue healthy lifestyle habits.",
            warnings=[],
            limitations=[],
            disclaimer="AI-assisted early screening assessment."
        )

        payload = dict(self.sample_payload)
        payload["patient_code"] = "PAT-CANONICAL-LOW"

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Query persisted row
        ast = self.db.query(Assessment).filter(Assessment.id == data["assessment_id"]).first()
        self.assertIsNotNone(ast)

        # Assert Canonical ML Fields
        self.assertTrue(ast.ml_available)
        self.assertIsNone(ast.ml_error)
        self.assertEqual(ast.pcos_probability, 0.1425)
        self.assertEqual(ast.model_prediction, 0)
        self.assertEqual(ast.model_prediction_label, "Lower PCOS-related risk")
        self.assertEqual(ast.overall_prediction, "LOW")
        self.assertEqual(json.loads(ast.overall_reasons_json), ["ML model detected lower PCOS-related probability (14.2%)."])
        self.assertEqual(json.loads(ast.red_flags_json), [])
        self.assertEqual(ast.recommendation, "Continue healthy lifestyle habits.")
        self.assertEqual(json.loads(ast.warnings_json), [])
        self.assertEqual(json.loads(ast.model_limitations_json), [])
        self.assertEqual(ast.disclaimer, "AI-assisted early screening assessment.")

        # Assert Legacy Compatibility Fields
        self.assertEqual(ast.triage_level, "LEVEL 1")
        self.assertEqual(ast.risk_category, "Low Risk")
        self.assertFalse(ast.red_flag_triggered)
        self.assertIsNone(data["referral_id"])
        self.assertIsNone(data["followup_id"])

    # 2. MODERATE Assessment Persistence Test
    @patch("main.ml_client.predict")
    def test_moderate_assessment_canonical_persistence(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response(
            overall="MODERATE",
            prob=0.5230,
            model_pred=1,
            label="Higher PCOS-related risk",
            reasons=["ML model detected elevated risk.", "Irregular menstrual cycle reported."],
            red_flags=[],
            recommendation="Schedule consultation at Ayushman Arogya Mandir."
        )

        payload = dict(self.sample_payload)
        payload["patient_code"] = "PAT-CANONICAL-MOD"

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        ast = self.db.query(Assessment).filter(Assessment.id == data["assessment_id"]).first()
        self.assertEqual(ast.overall_prediction, "MODERATE")
        self.assertEqual(ast.triage_level, "LEVEL 2")
        self.assertEqual(ast.model_prediction, 1)
        self.assertEqual(ast.pcos_probability, 0.5230)
        self.assertIsNotNone(data["referral_id"])
        self.assertIsNotNone(data["followup_id"])

    # 3. HIGH Assessment Persistence Test
    @patch("main.ml_client.predict")
    def test_high_assessment_canonical_persistence(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response(
            overall="HIGH",
            prob=0.8650,
            model_pred=1,
            label="Higher PCOS-related risk",
            reasons=["High ML probability", "Multiple androgenic symptoms"],
            red_flags=[],
            recommendation="Prompt consultation with specialist."
        )

        payload = dict(self.sample_payload)
        payload["patient_code"] = "PAT-CANONICAL-HIGH"

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        ast = self.db.query(Assessment).filter(Assessment.id == data["assessment_id"]).first()
        self.assertEqual(ast.overall_prediction, "HIGH")
        self.assertEqual(ast.triage_level, "LEVEL 3")
        self.assertEqual(ast.model_prediction, 1)
        self.assertEqual(ast.pcos_probability, 0.8650)
        self.assertIsNotNone(data["referral_id"])
        self.assertIsNotNone(data["followup_id"])

    # 4. CRITICAL Assessment & Coexistence with LEVEL 3 Test (CRITICAL must NOT be lost)
    @patch("main.ml_client.predict")
    def test_critical_assessment_coexistence(self, mock_predict):
        critical_rf = {
            "severity": "critical",
            "category": "bleeding_duration",
            "message": "Extremely prolonged bleeding duration (28 days)."
        }
        mock_predict.return_value = self._mock_ml_response(
            overall="CRITICAL",
            prob=0.9120,
            model_pred=1,
            label="Higher PCOS-related risk",
            reasons=["Extremely prolonged bleeding duration.", "Critical clinical concern."],
            red_flags=[critical_rf],
            recommendation="Immediate emergency medical evaluation strongly advised."
        )

        payload = dict(self.sample_payload)
        payload["patient_code"] = "PAT-CANONICAL-CRIT"
        payload["bleeding_duration_days"] = 28

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        ast = self.db.query(Assessment).filter(Assessment.id == data["assessment_id"]).first()

        # CRITICAL ASSERTIONS:
        # 1. Canonical overall_prediction is CRITICAL (never replaced by HIGH)
        self.assertEqual(ast.overall_prediction, "CRITICAL")
        # 2. Legacy triage_level is LEVEL 3 (for workflow escalation)
        self.assertEqual(ast.triage_level, "LEVEL 3")
        # 3. Both coexist simultaneously in the same record
        self.assertTrue(ast.red_flag_triggered)
        saved_rf = json.loads(ast.red_flags_json)
        self.assertEqual(len(saved_rf), 1)
        self.assertEqual(saved_rf[0]["severity"], "critical")
        self.assertEqual(saved_rf[0]["category"], "bleeding_duration")

    # 5. Empty Arrays Serialization
    @patch("main.ml_client.predict")
    def test_empty_arrays_serialization(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response(
            overall="LOW",
            prob=0.10,
            model_pred=0,
            label="Lower PCOS-related risk",
            reasons=["No symptoms reported."],
            red_flags=[],
            warnings=[],
            limitations=[]
        )

        payload = dict(self.sample_payload)
        payload["patient_code"] = "PAT-CANONICAL-EMPTY-ARRAYS"

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)

        ast = self.db.query(Assessment).filter(Assessment.patient_id == res.json()["patient_id"]).first()
        self.assertEqual(json.loads(ast.red_flags_json), [])
        self.assertEqual(json.loads(ast.warnings_json), [])
        self.assertEqual(json.loads(ast.model_limitations_json), [])

    # 6. Historical Records with NULL Canonical Fields
    def test_historical_record_null_canonical_handling(self):
        # Query or create a historical patient and assessment with NULL canonical fields
        hist_p = self.db.query(Patient).filter(Patient.patient_code == "PAT-OLD-HISTORICAL-NULL").first()
        if not hist_p:
            hist_p = Patient(
                patient_code="PAT-OLD-HISTORICAL-NULL",
                name="Old Patient",
                age=28,
                village="Rampur"
            )
            self.db.add(hist_p)
            self.db.flush()

        hist_ast = self.db.query(Assessment).filter(Assessment.patient_id == hist_p.id).first()
        if not hist_ast:
            hist_ast = Assessment(
                patient_id=hist_p.id,
                age=28,
                height_cm=155.0,
                weight_kg=54.0,
                bmi=22.48,
                cycle_length="21-35 days",
                cycle_regularity="Regular",
                bleeding_duration_days=None,
                heavy_bleeding=None,
                risk_probability=0.20,
                risk_category="Low Risk",
                triage_level="LEVEL 1",
                red_flag_triggered=False,
                reasons_json=json.dumps(["Legacy historical reason."]),
                # Canonical ML fields explicitly NULL
                ml_available=None,
                ml_error=None,
                pcos_probability=None,
                model_prediction=None,
                model_prediction_label=None,
                overall_prediction=None,
                overall_reasons_json=None,
                red_flags_json=None,
                recommendation=None,
                warnings_json=None,
                model_limitations_json=None,
                disclaimer=None
            )
            self.db.add(hist_ast)
            self.db.commit()

        # Lookup patient
        lookup_res = self.client.get("/api/patients/lookup?patient_code=PAT-OLD-HISTORICAL-NULL")
        self.assertEqual(lookup_res.status_code, 200)
        data = lookup_res.json()

        self.assertTrue(data["success"])
        self.assertEqual(data["assessment_overview"]["triage_level"], "LEVEL 1")
        self.assertIsNone(data["canonical_ml_result"])

    # 7. Patient Lookup with Canonical ML Fields
    @patch("main.ml_client.predict")
    def test_patient_lookup_returns_canonical_ml(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response(
            overall="HIGH",
            prob=0.82,
            model_pred=1,
            label="Higher PCOS-related risk",
            reasons=["High probability."],
            red_flags=[{"severity": "high", "category": "pain", "message": "Severe pain"}],
            recommendation="Specialist review required."
        )

        payload = dict(self.sample_payload)
        payload["patient_code"] = "PAT-LOOKUP-CANONICAL"

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)

        lookup_res = self.client.get("/api/patients/lookup?patient_code=PAT-LOOKUP-CANONICAL")
        self.assertEqual(lookup_res.status_code, 200)
        data = lookup_res.json()

        canonical_ml = data["canonical_ml_result"]
        self.assertIsNotNone(canonical_ml)
        self.assertEqual(canonical_ml["overall_prediction"], "HIGH")
        self.assertEqual(canonical_ml["pcos_probability"], 0.82)
        self.assertEqual(canonical_ml["model_prediction"], 1)
        self.assertEqual(len(canonical_ml["red_flags"]), 1)
        self.assertEqual(canonical_ml["red_flags"][0]["category"], "pain")
        self.assertEqual(canonical_ml["recommendation"], "Specialist review required.")

    # 8. ML Failure Regression (No Assessment Row Persisted)
    @patch("main.ml_client.predict")
    def test_ml_failure_no_assessment_persisted(self, mock_predict):
        mock_predict.side_effect = MLTimeoutError("ML API timed out")

        payload = dict(self.sample_payload)
        payload["patient_code"] = "PAT-FAIL-PERSIST-TEST"

        initial_ast_count = self.db.query(Assessment).count()
        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 503)

        final_ast_count = self.db.query(Assessment).count()
        self.assertEqual(initial_ast_count, final_ast_count)


if __name__ == "__main__":
    unittest.main()
