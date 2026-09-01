"""Dependency-free checks for the E2E seam when FastAPI is not installed."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
MODEL_SPEC = importlib.util.spec_from_file_location("project01_model", PROJECT / "ml" / "model.py")
model = importlib.util.module_from_spec(MODEL_SPEC)
MODEL_SPEC.loader.exec_module(model)


class StaticE2EContractTests(unittest.TestCase):
    def test_client_is_react_vite_mui_and_references_all_api_resources(self):
        package = json.loads((PROJECT / "client" / "package.json").read_text())
        self.assertIn("vite", package["devDependencies"])
        self.assertIn("react", package["dependencies"])
        self.assertIn("@mui/material", package["dependencies"])
        self.assertTrue((PROJECT / "client" / "src" / "components").is_dir())
        for component in (
            "layout/AppShell.jsx", "sections/HeroSection.jsx", "evidence/EvidenceSection.jsx",
            "common/MetricCard.jsx", "common/MetricGrid.jsx", "explorer/SliceExplorer.jsx",
            "estimator/TripEstimator.jsx",
        ):
            self.assertTrue((PROJECT / "client" / "src" / "components" / component).exists(), component)
        app_source = (PROJECT / "client" / "src" / "App.jsx").read_text()
        for component_name in ("AppShell", "HeroSection", "EvidenceSection", "SliceExplorer", "TripEstimator"):
            self.assertIn(component_name, app_source)
        client = (PROJECT / "client" / "src" / "services" / "api.js").read_text()
        for endpoint in ("/experiment", "/feature-importance", "/predictions", "/estimate"):
            self.assertIn(endpoint, client)

    def test_server_declares_fastapi_routes_and_vite_proxy(self):
        server = (PROJECT / "server" / "routers" / "experiment.py").read_text()
        for route in ("/api/health", "/api/experiment", "/api/feature-importance", "/api/predictions", "/api/estimate"):
            self.assertIn(route.removeprefix("/api"), server)
        self.assertTrue((PROJECT / "server" / "services" / "experiment_service.py").exists())
        self.assertTrue((PROJECT / "ml" / "artifacts.py").exists())
        self.assertTrue((PROJECT / "ml" / "slicing.py").exists())
        vite = (PROJECT / "client" / "vite.config.js").read_text()
        self.assertIn("127.0.0.1:8001", vite)

    def test_artifact_slice_is_finite_and_boundary_is_population_invariant(self):
        primary = model.prediction_slice("short", "primary")
        robust = model.prediction_slice("short", "robust")
        self.assertEqual(primary["distance_boundary_miles"], robust["distance_boundary_miles"])
        self.assertGreater(primary["metrics"]["rows"], 0)
        for row in primary["rows"][:25]:
            self.assertTrue(all(isinstance(row[key], (int, float)) for key in ("actual", "prediction", "residual_seconds")))

    def test_time_and_weekday_slices_derive_from_available_columns(self):
        rush = model.prediction_slice("rush", "primary")
        off_peak = model.prediction_slice("off_peak", "primary")
        weekend = model.prediction_slice("weekend", "primary")
        weekday = model.prediction_slice("weekday", "primary")
        self.assertGreater(rush["metrics"]["rows"], 0)
        self.assertGreater(off_peak["metrics"]["rows"], 0)
        self.assertGreater(weekend["metrics"]["rows"], 0)
        self.assertGreater(weekday["metrics"]["rows"], 0)
        self.assertEqual(rush["metrics"]["rows"] + off_peak["metrics"]["rows"], model.prediction_slice("all", "primary")["metrics"]["rows"])
        for row in rush["rows"][:10]:
            hour = float(row["hour"])
            self.assertTrue(7 <= hour <= 9 or 16 <= hour <= 19)

    def test_estimator_mirrors_service_area_and_timestamp_contract(self):
        valid = {
            "pickup_latitude": 40.748, "pickup_longitude": -73.985,
            "dropoff_latitude": 40.765, "dropoff_longitude": -73.955,
            "pickup_datetime": "2016-03-18T17:30", "passenger_count": 2,
        }
        result = model.estimate(valid)
        self.assertIn("is_rush_hour", result)
        for payload, message in (
            ({**valid, "pickup_latitude": 35}, "coordinates_outside_service_area"),
            ({**valid, "pickup_datetime": "2016-11-06T01:30"}, "ambiguous_local_timestamp"),
            ({**valid, "pickup_latitude": 40.748, "dropoff_latitude": 40.748, "pickup_longitude": -73.985, "dropoff_longitude": -73.985}, "route_distance_must_be_positive"),
        ):
            with self.assertRaisesRegex(ValueError, message):
                model.estimate(payload)


if __name__ == "__main__":
    unittest.main()
