import unittest
from pydantic import ValidationError

from app.schemas import (
    PCOSPredictionRequest,
    PCOSPredictionResponse,
    HealthCheckResponse
)
from app.preprocessing import (
    preprocess_input,
    calculate_bmi,
    encode_cycle_type,
    EXPECTED_FEATURES
)
from app.prediction import predictor
from app.safety_rules import evaluate_safety_and_red_flags, evaluate_overall_triage
try:
    from app.main import predict, health_check, root
except ImportError:
    from main import predict, health_check, root


class TestSanjivaniPredictionService(unittest.TestCase):

    # ---------------- Preprocessing & Feature Tests ----------------

    def test_bmi_calculation(self):
        bmi = calculate_bmi(60.0, 165.0)
        expected = 60.0 / ((165.0 / 100.0) ** 2)
        self.assertAlmostEqual(bmi, expected, places=4)

    def test_cycle_encoding(self):
        self.assertEqual(encode_cycle_type("regular"), 2)
        self.assertEqual(encode_cycle_type("Regular"), 2)
        self.assertEqual(encode_cycle_type("irregular"), 4)
        self.assertEqual(encode_cycle_type("Irregular"), 4)
        with self.assertRaises(ValueError):
            encode_cycle_type("unknown")

    def test_feature_names_and_exact_order(self):
        req = PCOSPredictionRequest(
            age=25,
            weight=60.0,
            height=165.0,
            cycle_type="regular",
            cycle_length=5,
            weight_gain=False,
            hair_growth=False,
            skin_darkening=False,
            hair_loss=False,
            pimples=False,
            fast_food=False,
            regular_exercise=True,
            heavy_bleeding=False,
            severe_pain=False,
            blood_in_stool=False,
            vomiting=False
        )
        preprocessed = preprocess_input(req)
        features_df = preprocessed["features_df"]
        self.assertEqual(list(features_df.columns), EXPECTED_FEATURES)
        self.assertEqual(features_df['Cycle(R/I)'].iloc[0], 2)
        self.assertEqual(features_df['Cycle length(days)'].iloc[0], 5)

    # ---------------- ML Predictor Inference Tests ----------------

    def test_ml_predictor_inference(self):
        req = PCOSPredictionRequest(
            age=25,
            weight=60.0,
            height=165.0,
            cycle_type="regular",
            cycle_length=5,
            weight_gain=False,
            hair_growth=False,
            skin_darkening=False,
            hair_loss=False,
            pimples=False,
            fast_food=False,
            regular_exercise=True
        )
        preprocessed = preprocess_input(req)
        ml_res = predictor.predict(preprocessed["features_df"])
        self.assertIn("risk_probability", ml_res)
        self.assertIn("prediction", ml_res)
        self.assertIsInstance(ml_res["risk_probability"], float)
        self.assertIn(ml_res["prediction"], [0, 1])

    # ---------------- Endpoint & Status Tests ----------------

    def test_root_endpoint(self):
        res = root()
        self.assertEqual(res["service"], "Sanjivani ML Prediction API")
        self.assertEqual(res["status"], "online")

    def test_health_endpoint(self):
        res = health_check()
        self.assertIsInstance(res, HealthCheckResponse)
        self.assertEqual(res.status, "healthy")
        self.assertTrue(res.model_loaded)

    # ---------------- Simplified ML-First Guardrail Tests (Section 10) ----------------

    def _base_req(self, **overrides):
        data = {
            "age": 25,
            "weight": 55.0,
            "height": 165.0,
            "cycle_type": "regular",
            "cycle_length": 5,
            "weight_gain": False,
            "hair_growth": False,
            "skin_darkening": False,
            "hair_loss": False,
            "pimples": False,
            "fast_food": False,
            "regular_exercise": True,
            "heavy_bleeding": False,
            "severe_pain": False,
            "blood_in_stool": False,
            "vomiting": False
        }
        data.update(overrides)
        return PCOSPredictionRequest(**data)

    def test_1_normal_assessment_ml_determines_result(self):
        """1. Normal assessment -> ML model determines result -> no unnecessary safety override"""
        req = self._base_req(cycle_length=5)
        res = predict(req)
        self.assertEqual(res.overall_prediction, "LOW")
        self.assertEqual(res.model_prediction, 0)
        self.assertLess(res.pcos_probability, 0.40)
        self.assertEqual(len(res.red_flags), 0)

    def test_2_bleeding_duration_9_days_moderate(self):
        """2. bleeding_duration_days = 9 -> at least MODERATE"""
        req = self._base_req(cycle_length=9)
        res = predict(req)
        self.assertIn(res.overall_prediction, ["MODERATE", "HIGH", "CRITICAL"])
        self.assertEqual(res.overall_prediction, "MODERATE")

    def test_3_bleeding_duration_12_days_high_prob_unchanged(self):
        """3. bleeding_duration_days = 12 -> at least HIGH -> model probability unchanged"""
        req = self._base_req(cycle_length=12)
        res = predict(req)
        self.assertIn(res.overall_prediction, ["HIGH", "CRITICAL"])
        self.assertEqual(res.overall_prediction, "HIGH")
        # Probability must remain the legitimate ML model output (< 0.4 for this negative profile)
        self.assertNotEqual(res.pcos_probability, 1.0)
        self.assertLess(res.pcos_probability, 0.40)
        self.assertEqual(res.model_prediction, 0)

    def test_4_bleeding_duration_21_days_critical(self):
        """4. bleeding_duration_days = 21 -> CRITICAL -> model probability unchanged"""
        req = self._base_req(cycle_length=21)
        res = predict(req)
        self.assertEqual(res.overall_prediction, "CRITICAL")
        self.assertNotEqual(res.pcos_probability, 1.0)
        self.assertLess(res.pcos_probability, 0.40)

    def test_5_heavy_bleeding_at_least_high(self):
        """5. heavy_bleeding = true -> at least HIGH"""
        req = self._base_req(heavy_bleeding=True)
        res = predict(req)
        self.assertIn(res.overall_prediction, ["HIGH", "CRITICAL"])
        self.assertEqual(res.overall_prediction, "HIGH")

    def test_6_severe_pain_guardrail(self):
        """6. pain_severity >= 4 (severe_pain = true) -> existing severe pain guardrail works (at least HIGH)"""
        req = self._base_req(severe_pain=True)
        res = predict(req)
        self.assertIn(res.overall_prediction, ["HIGH", "CRITICAL"])
        self.assertEqual(res.overall_prediction, "HIGH")

    def test_7_vomiting_rule(self):
        """7. vomiting = true -> existing vomiting rule works (at least HIGH)"""
        req = self._base_req(vomiting=True)
        res = predict(req)
        self.assertIn(res.overall_prediction, ["HIGH", "CRITICAL"])
        self.assertEqual(res.overall_prediction, "HIGH")

    def test_8_blood_in_stool_rule(self):
        """8. blood_in_stool = true -> existing safety rule works (CRITICAL)"""
        req = self._base_req(blood_in_stool=True)
        res = predict(req)
        self.assertEqual(res.overall_prediction, "CRITICAL")

    def test_9_ml_high_no_safety_rule_remains_high(self):
        """9. ML says HIGH and no safety rule triggers -> final remains HIGH"""
        req = self._base_req(
            age=28,
            weight=85.0,
            height=152.0,
            cycle_type="irregular",
            cycle_length=5,
            weight_gain=True,
            hair_growth=True,
            skin_darkening=True,
            hair_loss=True,
            pimples=True,
            fast_food=True,
            regular_exercise=False
        )
        res = predict(req)
        self.assertEqual(res.model_prediction, 1)
        self.assertGreater(res.pcos_probability, 0.40)
        self.assertIn(res.overall_prediction, ["HIGH", "MODERATE"])

    def test_10_ml_low_critical_guardrail_unfaked_probability(self):
        """10. ML says LOW and CRITICAL guardrail triggers -> overall becomes CRITICAL -> raw ML result remains LOW / original probability"""
        req = self._base_req(
            cycle_length=5,
            severe_pain=True,
            heavy_bleeding=True
        )
        res = predict(req)
        self.assertEqual(res.overall_prediction, "CRITICAL")
        self.assertEqual(res.model_prediction, 0)
        self.assertLess(res.pcos_probability, 0.40)
        self.assertNotEqual(res.pcos_probability, 1.0)

    def test_11_critical_never_downgraded(self):
        """11. CRITICAL can never be downgraded"""
        req = self._base_req(
            cycle_length=25,
            heavy_bleeding=False,
            severe_pain=False,
            blood_in_stool=False
        )
        res = predict(req)
        self.assertEqual(res.overall_prediction, "CRITICAL")

    def test_no_model_jargon_in_reasons(self):
        """Verify that overall_reasons does not contain algorithmic text like 'ML model detected'"""
        req = self._base_req(heavy_bleeding=True, cycle_length=9)
        res = predict(req)
        for reason in res.overall_reasons:
            self.assertNotIn("ML model", reason)
            self.assertNotIn("probability:", reason)
            self.assertNotIn("model predicted", reason.lower())


if __name__ == "__main__":
    unittest.main()
