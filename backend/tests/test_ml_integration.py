"""
Unit and Integration Tests for ML Payload Mapper and ML Client Services
"""

import os
import sys
import unittest
from unittest.mock import patch
import httpx

# Ensure backend directory is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.ml_payload_mapper import build_ml_payload, MLPayloadMappingError
from services.ml_client import (
    MLClient,
    MLClientError,
    MLConnectionError,
    MLTimeoutError,
    MLHttpError,
    MLResponseValidationError,
    MLServiceResponse,
)
from database.schemas import AssessmentInputSchema


class TestMLPayloadMapper(unittest.TestCase):
    """Test suite for ml_payload_mapper.py"""

    def setUp(self):
        self.valid_sanjivani_dict = {
            "patient_code": "PAT-1089",
            "age": 25,
            "height_cm": 160.0,
            "weight_kg": 60.0,
            "weight_gain": True,
            "cycle_length": "21-35 days",           # Menstrual Interval (Must NOT be sent as ML cycle_length)
            "cycle_regularity": "Regular",
            "bleeding_duration_days": 5,           # Bleeding Duration (Must be sent as ML cycle_length)
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
            "pain_severity": 4,
            "pain_location": "Menstrual/pelvic",
            "wellbeing": "Calm / Stable",
            "submitted_by_role": "ASHA"
        }

    def test_normal_payload_mapping(self):
        ml_payload = build_ml_payload(self.valid_sanjivani_dict)

        # Verify exact 16 fields in ML request payload
        expected_keys = {
            "age", "weight", "height", "cycle_type", "cycle_length",
            "weight_gain", "hair_growth", "skin_darkening", "hair_loss", "pimples",
            "fast_food", "regular_exercise", "heavy_bleeding", "severe_pain",
            "blood_in_stool", "vomiting"
        }
        self.assertEqual(set(ml_payload.keys()), expected_keys)

        # Verify values
        self.assertEqual(ml_payload["age"], 25)
        self.assertEqual(ml_payload["weight"], 60.0)
        self.assertEqual(ml_payload["height"], 160.0)
        self.assertEqual(ml_payload["cycle_type"], "regular")
        self.assertEqual(ml_payload["cycle_length"], 5)  # From bleeding_duration_days
        self.assertTrue(ml_payload["weight_gain"])
        self.assertTrue(ml_payload["hair_growth"])
        self.assertFalse(ml_payload["skin_darkening"])
        self.assertFalse(ml_payload["hair_loss"])
        self.assertTrue(ml_payload["pimples"])
        self.assertTrue(ml_payload["fast_food"])
        self.assertTrue(ml_payload["regular_exercise"])
        self.assertFalse(ml_payload["heavy_bleeding"])
        self.assertTrue(ml_payload["severe_pain"])  # pain_severity = 4 >= 4
        self.assertFalse(ml_payload["blood_in_stool"])
        self.assertFalse(ml_payload["vomiting"])

        # CRITICAL ASSERTION: The cycle interval string "21-35 days" must NEVER appear as cycle_length
        self.assertNotEqual(ml_payload["cycle_length"], "21-35 days")
        self.assertIsInstance(ml_payload["cycle_length"], int)

        # Verify patient metadata is stripped
        self.assertNotIn("patient_code", ml_payload)
        self.assertNotIn("submitted_by_role", ml_payload)
        self.assertNotIn("thyroid", ml_payload)

    def test_mapping_from_pydantic_model(self):
        schema_obj = AssessmentInputSchema(**self.valid_sanjivani_dict)
        ml_payload = build_ml_payload(schema_obj)
        self.assertEqual(ml_payload["cycle_length"], 5)
        self.assertEqual(ml_payload["cycle_type"], "regular")
        self.assertEqual(ml_payload["weight"], 60.0)

    def test_cycle_regularity_mappings(self):
        cases = [
            ("Regular", "regular"),
            ("regular", "regular"),
            ("Irregular", "irregular"),
            ("irregular", "irregular"),
            ("Frequently missed", "irregular"),
            ("frequently missed", "irregular"),
        ]
        for input_val, expected_val in cases:
            d = dict(self.valid_sanjivani_dict)
            d["cycle_regularity"] = input_val
            mapped = build_ml_payload(d)
            self.assertEqual(mapped["cycle_type"], expected_val, f"Failed for {input_val}")

        # Unknown value must raise MLPayloadMappingError
        invalid_d = dict(self.valid_sanjivani_dict)
        invalid_d["cycle_regularity"] = "Not sure"
        with self.assertRaises(MLPayloadMappingError):
            build_ml_payload(invalid_d)

    def test_exercise_mappings(self):
        cases = [
            ("Regularly", True),
            ("Occasionally", False),
            ("Rarely/Never", False),
        ]
        for input_val, expected_val in cases:
            d = dict(self.valid_sanjivani_dict)
            d["exercise"] = input_val
            mapped = build_ml_payload(d)
            self.assertEqual(mapped["regular_exercise"], expected_val, f"Failed for {input_val}")

        # Unknown value must raise error
        invalid_d = dict(self.valid_sanjivani_dict)
        invalid_d["exercise"] = "Daily Gym"
        with self.assertRaises(MLPayloadMappingError):
            build_ml_payload(invalid_d)

    def test_fast_food_mappings(self):
        cases = [
            ("Rarely", False),
            ("Sometimes", False),
            ("Frequently", True),
        ]
        for input_val, expected_val in cases:
            d = dict(self.valid_sanjivani_dict)
            d["fast_food"] = input_val
            mapped = build_ml_payload(d)
            self.assertEqual(mapped["fast_food"], expected_val, f"Failed for {input_val}")

        # Unknown value must raise error
        invalid_d = dict(self.valid_sanjivani_dict)
        invalid_d["fast_food"] = "Every Meal"
        with self.assertRaises(MLPayloadMappingError):
            build_ml_payload(invalid_d)

    def test_pain_severity_thresholds(self):
        pain_cases = [
            (1, False),
            (2, False),
            (3, False),
            (4, True),
            (5, True),
        ]
        for severity, expected_severe in pain_cases:
            d = dict(self.valid_sanjivani_dict)
            d["pain_severity"] = severity
            mapped = build_ml_payload(d)
            self.assertEqual(mapped["severe_pain"], expected_severe, f"Failed for severity {severity}")

    def test_missing_required_fields(self):
        # Missing bleeding_duration_days
        d1 = dict(self.valid_sanjivani_dict)
        del d1["bleeding_duration_days"]
        with self.assertRaises(MLPayloadMappingError):
            build_ml_payload(d1)

        # Missing heavy_bleeding
        d2 = dict(self.valid_sanjivani_dict)
        del d2["heavy_bleeding"]
        with self.assertRaises(MLPayloadMappingError):
            build_ml_payload(d2)

        # Out-of-range bleeding_duration_days
        d3 = dict(self.valid_sanjivani_dict)
        d3["bleeding_duration_days"] = 0
        with self.assertRaises(MLPayloadMappingError):
            build_ml_payload(d3)


class TestMLClient(unittest.TestCase):
    """Test suite for ml_client.py with mock HTTP transports"""

    def setUp(self):
        self.sample_valid_response = {
            "pcos_probability": 0.8524,
            "model_prediction": 1,
            "model_prediction_label": "Higher PCOS-related risk",
            "overall_prediction": "HIGH",
            "overall_reasons": [
                "ML model detected elevated PCOS-related risk (probability: 85.2%).",
                "Severe pelvic or abdominal pain reported."
            ],
            "red_flags": [
                {
                    "severity": "high",
                    "category": "pain",
                    "message": "Severe pelvic or abdominal pain reported."
                }
            ],
            "model_limitations": [],
            "recommendation": "Prompt clinical consultation recommended.",
            "risk_probability": 0.8524,
            "bmi": 23.44,
            "triage_level": "high",
            "disclaimer": "AI-assisted screening tool, not a medical diagnosis.",
            "warnings": []
        }

    def test_client_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url, "http://test-ml.local/predict")
            return httpx.Response(200, json=self.sample_valid_response)

        transport = httpx.MockTransport(handler)
        client = MLClient(api_url="http://test-ml.local/predict", transport=transport)

        result = client.predict({"age": 25})
        self.assertIsInstance(result, MLServiceResponse)
        self.assertEqual(result.overall_prediction, "HIGH")
        self.assertEqual(result.pcos_probability, 0.8524)
        self.assertEqual(result.model_prediction, 1)
        self.assertEqual(result.bmi, 23.44)
        self.assertEqual(len(result.red_flags), 1)
        self.assertEqual(result.red_flags[0].category, "pain")

    def test_client_timeout(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Read timed out")

        transport = httpx.MockTransport(handler)
        client = MLClient(api_url="http://test-ml.local/predict", transport=transport)

        with self.assertRaises(MLTimeoutError):
            client.predict({"age": 25})

    def test_client_connection_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(handler)
        client = MLClient(api_url="http://test-ml.local/predict", transport=transport)

        with self.assertRaises(MLConnectionError):
            client.predict({"age": 25})

    def test_client_http_400(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"detail": "Invalid input format"})

        transport = httpx.MockTransport(handler)
        client = MLClient(api_url="http://test-ml.local/predict", transport=transport)

        with self.assertRaises(MLHttpError) as ctx:
            client.predict({"age": 25})
        self.assertEqual(ctx.exception.status_code, 400)

    def test_client_http_500(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="Internal Server Error")

        transport = httpx.MockTransport(handler)
        client = MLClient(api_url="http://test-ml.local/predict", transport=transport)

        with self.assertRaises(MLHttpError) as ctx:
            client.predict({"age": 25})
        self.assertEqual(ctx.exception.status_code, 500)

    def test_client_malformed_json(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="NOT_VALID_JSON{abc")

        transport = httpx.MockTransport(handler)
        client = MLClient(api_url="http://test-ml.local/predict", transport=transport)

        with self.assertRaises(MLResponseValidationError):
            client.predict({"age": 25})

    def test_client_missing_response_field(self):
        invalid_resp = dict(self.sample_valid_response)
        del invalid_resp["overall_prediction"]  # Required field missing

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=invalid_resp)

        transport = httpx.MockTransport(handler)
        client = MLClient(api_url="http://test-ml.local/predict", transport=transport)

        with self.assertRaises(MLResponseValidationError):
            client.predict({"age": 25})

    def test_client_invalid_overall_prediction(self):
        invalid_resp = dict(self.sample_valid_response)
        invalid_resp["overall_prediction"] = "UNKNOWN_LEVEL"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=invalid_resp)

        transport = httpx.MockTransport(handler)
        client = MLClient(api_url="http://test-ml.local/predict", transport=transport)

        with self.assertRaises(MLResponseValidationError):
            client.predict({"age": 25})

    def test_client_probability_out_of_bounds(self):
        for bad_prob in [1.5, -0.1]:
            invalid_resp = dict(self.sample_valid_response)
            invalid_resp["pcos_probability"] = bad_prob

            def handler(request: httpx.Request, p=bad_prob) -> httpx.Response:
                return httpx.Response(200, json=invalid_resp)

            transport = httpx.MockTransport(handler)
            client = MLClient(api_url="http://test-ml.local/predict", transport=transport)

            with self.assertRaises(MLResponseValidationError):
                client.predict({"age": 25})

    def test_production_env_requires_ml_api_url(self):
        # When running in production/staging and ML_API_URL is missing, it must raise ValueError
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            os.environ.pop("ML_API_URL", None)
            with self.assertRaises(ValueError) as ctx:
                MLClient()
            self.assertIn("CRITICAL CONFIG ERROR", str(ctx.exception))


class TestRealMLServiceIntegration(unittest.TestCase):
    """
    Direct integration test against the real standalone ML service application instance
    without relying on external network ports.
    """

    def test_real_ml_service_inference_with_mapped_payload(self):
        # Dynamically import standalone ML app for direct ASGI testing
        ML_SERVICE_DIR = os.path.join(os.path.dirname(BASE_DIR), "ml-service")
        if ML_SERVICE_DIR not in sys.path:
            sys.path.insert(0, ML_SERVICE_DIR)

        try:
            from app.main import app as ml_fastapi_app
        except ImportError as e:
            self.skipTest(f"ML service app could not be imported: {e}")

        # 1. Map a Sanjivani assessment into ML payload
        sanjivani_input = {
            "patient_code": "PAT-REAL-TEST",
            "age": 24,
            "height_cm": 158.0,
            "weight_kg": 58.0,
            "weight_gain": True,
            "cycle_length": "21-35 days",
            "cycle_regularity": "Irregular",
            "bleeding_duration_days": 6,
            "heavy_bleeding": True,
            "symptom_duration": "3-6 months",
            "facial_hair": True,
            "acne": True,
            "hair_loss": False,
            "dark_skin": True,
            "thyroid": "No",
            "diabetes": "No",
            "family_pcos": "Yes",
            "fast_food": "Frequently",
            "exercise": "Rarely/Never",
            "pain_severity": 4,
            "blood_in_stool": False,
            "vomiting": False
        }

        ml_payload = build_ml_payload(sanjivani_input)
        self.assertEqual(ml_payload["cycle_length"], 6)

        # 2. Invoke real ML service via FastAPI TestClient transport adapter
        from fastapi.testclient import TestClient as FastAPITestClient
        test_client = FastAPITestClient(ml_fastapi_app)

        def sync_app_handler(request: httpx.Request) -> httpx.Response:
            res = test_client.post("/predict", json=ml_payload)
            return httpx.Response(res.status_code, text=res.text)

        transport = httpx.MockTransport(sync_app_handler)
        client = MLClient(api_url="http://testserver/predict", transport=transport)

        response = client.predict(ml_payload)

        # 3. Verify ML response
        self.assertIsInstance(response, MLServiceResponse)
        self.assertIn(response.overall_prediction, ["LOW", "MODERATE", "HIGH", "CRITICAL"])
        self.assertGreaterEqual(response.pcos_probability, 0.0)
        self.assertLessEqual(response.pcos_probability, 1.0)
        self.assertGreater(response.bmi, 0.0)
        self.assertIsInstance(response.overall_reasons, list)
        self.assertIsInstance(response.recommendation, str)


if __name__ == "__main__":
    unittest.main()
