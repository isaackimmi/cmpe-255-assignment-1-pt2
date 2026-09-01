"""No-server API contract tests for Project 01."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None


@unittest.skipUnless(HAS_FASTAPI, "install server/requirements.txt to run API contracts")
class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from server import main
        cls.api = main

    def test_health_contract(self):
        payload = self.api.health()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["project"], "01_nyc_taxi_trip_prediction")

    def test_experiment_and_feature_contracts(self):
        metrics = self.api.experiment()
        self.assertIn("linear_log_target", metrics)
        self.assertLess(metrics["split_cutoff"]["train_max_pickup_datetime"], metrics["split_cutoff"]["test_min_pickup_datetime"])
        features = self.api.feature_importance()
        self.assertTrue(features)
        self.assertIn("feature", features[0])

    def test_prediction_slice_contract_uses_stable_boundary(self):
        primary = self.api.predictions(slice="short", population="primary")
        robust = self.api.predictions(slice="short", population="robust")
        self.assertEqual(primary["distance_boundary_miles"], robust["distance_boundary_miles"])
        self.assertGreater(primary["metrics"]["rows"], 0)
        self.assertIn("baseline", primary["metrics"])

    def test_invalid_slice_and_population_are_http_400(self):
        with self.assertRaises(self.api.HTTPException) as slice_error:
            self.api.predictions(slice="not-a-slice", population="primary")
        self.assertEqual(slice_error.exception.status_code, 400)
        with self.assertRaises(self.api.HTTPException) as population_error:
            self.api.predictions(slice="all", population="not-a-population")
        self.assertEqual(population_error.exception.status_code, 400)

    def test_estimator_contract(self):
        request = self.api.EstimateRequest(
            pickup_latitude=40.748, pickup_longitude=-73.985,
            dropoff_latitude=40.765, dropoff_longitude=-73.955,
            pickup_datetime="2016-03-18T17:30", passenger_count=2,
        )
        result = self.api.estimate_trip(request)
        self.assertGreater(result["estimated_duration_seconds"], 0)
        self.assertIn("is_rush_hour", result)
        self.assertIn("teaching estimate", result["disclaimer"])

    def test_estimator_rejects_out_of_area_and_ambiguous_timestamp(self):
        base = {
            "pickup_latitude": 40.748, "pickup_longitude": -73.985,
            "dropoff_latitude": 40.765, "dropoff_longitude": -73.955,
            "pickup_datetime": "2016-03-18T17:30", "passenger_count": 2,
        }
        with self.assertRaises(self.api.HTTPException) as area_error:
            self.api.estimate_trip(self.api.EstimateRequest(**{**base, "pickup_latitude": 35}))
        self.assertEqual(area_error.exception.status_code, 422)
        with self.assertRaises(self.api.HTTPException) as timestamp_error:
            self.api.estimate_trip(self.api.EstimateRequest(**{**base, "pickup_datetime": "2016-11-06T01:30"}))
        self.assertEqual(timestamp_error.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
