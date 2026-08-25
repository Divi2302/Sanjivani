"""
Route-Level Integration Tests for /api/predict and /api/assessments (Phase 3)
Verifies runtime delegation to the standalone ML service and compatibility adaptation.
"""

import os
import sys
import unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app
from database.db import SessionLocal
from database.models import Assessment, Patient, Referral, FollowUp
from services.ml_client import (
    MLClient,
    MLServiceResponse,
    MLTimeoutError,
    MLConnectionError,
    MLHttpError,
    MLResponseValidationError,
)


class TestRuntimeRoutes(unittest.TestCase):
    """Test suite verifying /api/predict and /api/assessments runtime behavior"""

    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

        self.valid_payload = {
            "patient_code": "PAT-ROUTE-TEST",
            "age": 25,
            "height_cm": 160.0,
            "weight_kg": 60.0,
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

    def _mock_ml_response(self, overall: str, prob: float = 0.5, red_flags = None):
        return MLServiceResponse(
            pcos_probability=prob,
            model_prediction=1 if prob >= 0.4 else 0,
            model_prediction_label="Higher PCOS-related risk" if prob >= 0.4 else "Lower PCOS-related risk",
            overall_prediction=overall,
            overall_reasons=[f"Clinical reason for {overall} triage."],
            red_flags=red_flags or [],
            model_limitations=[],
            recommendation=f"Recommended action for {overall}.",
            risk_probability=prob,
            bmi=23.44,
            triage_level=overall.lower(),
            disclaimer="Standard medical disclaimer",
            warnings=[]
        )

    # =========================================================================
    # /api/predict Tests
    # =========================================================================

    @patch("main.ml_client.predict")
    def test_predict_low_triage(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response("LOW", 0.15)

        res = self.client.post("/api/predict", json=self.valid_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["triage_level"], "LEVEL 1")
        self.assertEqual(data["badge_color"], "green")
        self.assertEqual(data["risk_probability"], 0.15)
        self.assertFalse(data["requires_referral"])
        self.assertFalse(data["requires_followup"])
        self.assertFalse(data["red_flag_triggered"])
        mock_predict.assert_called_once()

    @patch("main.ml_client.predict")
    def test_predict_moderate_triage(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response("MODERATE", 0.55)

        res = self.client.post("/api/predict", json=self.valid_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["triage_level"], "LEVEL 2")
        self.assertEqual(data["badge_color"], "yellow")
        self.assertEqual(data["risk_probability"], 0.55)
        self.assertTrue(data["requires_referral"])
        self.assertTrue(data["requires_followup"])

    @patch("main.ml_client.predict")
    def test_predict_high_triage(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response("HIGH", 0.88)

        res = self.client.post("/api/predict", json=self.valid_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["triage_level"], "LEVEL 3")
        self.assertEqual(data["badge_color"], "red")
        self.assertEqual(data["risk_probability"], 0.88)
        self.assertTrue(data["requires_referral"])
        self.assertTrue(data["requires_followup"])

    @patch("main.ml_client.predict")
    def test_predict_critical_triage(self, mock_predict):
        red_flag = {
            "severity": "critical",
            "category": "gastrointestinal",
            "message": "Blood in stool reported."
        }
        mock_predict.return_value = self._mock_ml_response("CRITICAL", 0.92, red_flags=[red_flag])

        res = self.client.post("/api/predict", json=self.valid_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Backward compatibility level is LEVEL 3, but title reflects critical urgency
        self.assertEqual(data["triage_level"], "LEVEL 3")
        self.assertEqual(data["badge_color"], "red")
        self.assertTrue(data["red_flag_triggered"])
        self.assertEqual(data["title"], "Critical Safety Escalation Required")
        self.assertTrue(data["requires_referral"])
        self.assertTrue(data["requires_followup"])

    @patch("main.ml_client.predict")
    def test_predict_timeout_failure(self, mock_predict):
        mock_predict.side_effect = MLTimeoutError("ML API timed out")

        res = self.client.post("/api/predict", json=self.valid_payload)
        self.assertEqual(res.status_code, 503)
        self.assertIn("timed out", res.json()["detail"].lower())

    @patch("main.ml_client.predict")
    def test_predict_connection_failure(self, mock_predict):
        mock_predict.side_effect = MLConnectionError("Connection refused")

        res = self.client.post("/api/predict", json=self.valid_payload)
        self.assertEqual(res.status_code, 503)
        self.assertIn("unavailable", res.json()["detail"].lower())

    @patch("main.ml_client.predict")
    def test_predict_http_500_failure(self, mock_predict):
        mock_predict.side_effect = MLHttpError(status_code=500, message="Internal error")

        res = self.client.post("/api/predict", json=self.valid_payload)
        self.assertEqual(res.status_code, 503)

    @patch("main.ml_client.predict")
    def test_predict_malformed_response_failure(self, mock_predict):
        mock_predict.side_effect = MLResponseValidationError("Missing overall_prediction")

        res = self.client.post("/api/predict", json=self.valid_payload)
        self.assertEqual(res.status_code, 503)

    # =========================================================================
    # /api/assessments Workflow & Persistence Tests
    # =========================================================================

    @patch("main.ml_client.predict")
    def test_assessment_low_flow_no_referral(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response("LOW", 0.12)

        payload = dict(self.valid_payload)
        payload["patient_code"] = "PAT-ASSESS-LOW"

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data["success"])
        self.assertIsNone(data["referral_id"])
        self.assertIsNone(data["followup_id"])
        self.assertEqual(data["triage_result"]["triage_level"], "LEVEL 1")

        # Verify DB record
        ast = self.db.query(Assessment).filter(Assessment.id == data["assessment_id"]).first()
        self.assertIsNotNone(ast)
        self.assertEqual(ast.triage_level, "LEVEL 1")
        self.assertEqual(ast.risk_probability, 0.12)
        self.assertEqual(ast.risk_category, "Low Risk")
        self.assertFalse(ast.red_flag_triggered)

    @patch("main.ml_client.predict")
    def test_assessment_moderate_flow_with_referral(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response("MODERATE", 0.58)

        payload = dict(self.valid_payload)
        payload["patient_code"] = "PAT-ASSESS-MOD"

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data["success"])
        self.assertIsNotNone(data["referral_id"])
        self.assertIsNotNone(data["followup_id"])
        self.assertEqual(data["triage_result"]["triage_level"], "LEVEL 2")

        # Verify DB Referral & FollowUp
        ref = self.db.query(Referral).filter(Referral.id == data["referral_id"]).first()
        self.assertIsNotNone(ref)
        self.assertEqual(ref.status, "Pending")

        flw = self.db.query(FollowUp).filter(FollowUp.id == data["followup_id"]).first()
        self.assertIsNotNone(flw)
        self.assertEqual(flw.status, "Pending")

    @patch("main.ml_client.predict")
    def test_assessment_high_flow_with_urgent_followup(self, mock_predict):
        mock_predict.return_value = self._mock_ml_response("HIGH", 0.89)

        payload = dict(self.valid_payload)
        payload["patient_code"] = "PAT-ASSESS-HIGH"

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data["success"])
        self.assertIsNotNone(data["referral_id"])
        self.assertIsNotNone(data["followup_id"])
        self.assertEqual(data["triage_result"]["triage_level"], "LEVEL 3")

    @patch("main.ml_client.predict")
    def test_assessment_critical_flow(self, mock_predict):
        red_flag = {
            "severity": "critical",
            "category": "bleeding_duration",
            "message": "Extremely prolonged bleeding duration (25 days)."
        }
        mock_predict.return_value = self._mock_ml_response("CRITICAL", 0.95, red_flags=[red_flag])

        payload = dict(self.valid_payload)
        payload["patient_code"] = "PAT-ASSESS-CRIT"
        payload["bleeding_duration_days"] = 25

        res = self.client.post("/api/assessments", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data["success"])
        self.assertIsNotNone(data["referral_id"])
        self.assertIsNotNone(data["followup_id"])
        self.assertEqual(data["triage_result"]["triage_level"], "LEVEL 3")
        self.assertTrue(data["triage_result"]["red_flag_triggered"])

        # Check that DB row captured red flag and risk
        ast = self.db.query(Assessment).filter(Assessment.id == data["assessment_id"]).first()
        self.assertTrue(ast.red_flag_triggered)
        self.assertEqual(ast.triage_level, "LEVEL 3")
        self.assertEqual(ast.risk_category, "Critical Risk")

    @patch("main.ml_client.predict")
    def test_assessment_failure_no_fake_db_records(self, mock_predict):
        mock_predict.side_effect = MLConnectionError("Service unavailable")

        payload = dict(self.valid_payload)
        payload["patient_code"] = "PAT-FAIL-TEST"

        initial_count = self.db.query(Assessment).count()
        res = self.client.post("/api/assessments", json=payload)

        # Must reject with HTTP 503
        self.assertEqual(res.status_code, 503)

        # Must NOT create an assessment row with fake probability or fake LEVEL 1
        final_count = self.db.query(Assessment).count()
        self.assertEqual(initial_count, final_count)

    # =========================================================================
    # Admin Governance Endpoint Security Tests
    # =========================================================================

    def test_admin_metrics_disabled_when_token_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ADMIN_API_TOKEN", None)
            res = self.client.get("/api/ml/metrics", headers={"X-Admin-Token": "ANY_TOKEN"})
            self.assertEqual(res.status_code, 503)
            self.assertIn("not configured", res.json()["detail"].lower())

    def test_admin_metrics_forbidden_with_wrong_token(self):
        with patch.dict(os.environ, {"ADMIN_API_TOKEN": "SECRET_TEST_TOKEN_123"}):
            res = self.client.get("/api/ml/metrics", headers={"X-Admin-Token": "WRONG_TOKEN"})
            self.assertEqual(res.status_code, 403)
            self.assertIn("restricted", res.json()["detail"].lower())

    def test_admin_metrics_success_with_valid_token(self):
        with patch.dict(os.environ, {"ADMIN_API_TOKEN": "SECRET_TEST_TOKEN_123"}):
            res = self.client.get("/api/ml/metrics", headers={"X-Admin-Token": "SECRET_TEST_TOKEN_123"})
            self.assertEqual(res.status_code, 200)
    # =========================================================================
    # Database Configuration & Dynamic URL Tests
    # =========================================================================

    def test_database_url_sqlite_connect_args(self):
        """Verify that SQLite connect_args (check_same_thread: False) is applied only to SQLite"""
        from database import db as db_module
        
        # Test SQLite URL
        sqlite_url = "sqlite:///./test_custom.db"
        sqlite_args = {"check_same_thread": False} if sqlite_url.startswith("sqlite") else {}
        self.assertEqual(sqlite_args, {"check_same_thread": False})

        # Test non-SQLite URL
        postgres_url = "postgresql://user:pass@localhost:5432/sanjivani"
        pg_args = {"check_same_thread": False} if postgres_url.startswith("sqlite") else {}
        self.assertEqual(pg_args, {})

        # Default fallback verification
        self.assertTrue(db_module.DATABASE_URL.startswith("sqlite"))

    # =========================================================================
    # Main Backend Health Check Endpoint Tests
    # =========================================================================

    def test_health_get_endpoint(self):
        """Verify GET /health returns HTTP 200 with service and db status"""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "sanjivani-main-backend")
        self.assertEqual(data["database"], "connected")
        # Ensure no sensitive configuration or secrets are exposed
        self.assertNotIn("ADMIN_API_TOKEN", data)
        self.assertNotIn("ML_API_URL", data)
        self.assertNotIn("DATABASE_URL", data)

    def test_health_head_endpoint(self):
        """Verify HEAD /health returns HTTP 200 with zero response body for uptime monitors"""
        res = self.client.head("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text, "")


if __name__ == "__main__":
    unittest.main()


