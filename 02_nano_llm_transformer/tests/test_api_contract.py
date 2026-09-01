import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
            from server import main
        except ModuleNotFoundError as exc:
            if exc.name in {"fastapi", "pydantic", "httpx", "starlette"}:
                raise unittest.SkipTest("FastAPI/httpx dependencies are required for HTTP contract tests")
            raise
        cls.main = main
        cls.client = TestClient(main.app)

    def test_health_route(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_metrics_and_behavior_routes_are_artifact_backed(self):
        metrics = self.client.get("/api/metrics")
        behavior = self.client.get("/api/behavior")
        self.assertEqual(metrics.status_code, 200)
        self.assertEqual(behavior.status_code, 200)
        payload = metrics.json()
        self.assertEqual(payload["split"]["train_chars"] + payload["split"]["validation_chars"] + payload["split"]["test_chars"], 360)
        self.assertEqual(behavior.json()["kind"], "deterministic_replay")
        self.assertEqual(payload["artifact_backend"], "stdlib_char_ngram")
        self.assertEqual(payload["inference_backend"], "stdlib_char_ngram")

    def test_generation_route_is_deterministic_and_bounded(self):
        body = {"prompt": "user:", "max_new_tokens": 4, "temperature": 0}
        first = self.client.post("/api/generate", json=body)
        second = self.client.post("/api/generate", json=body)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["text"], second.json()["text"])
        self.assertEqual(len(first.json()["trace"]), 4)

    def test_probability_route_returns_normalized_distribution(self):
        response = self.client.post("/api/probabilities", json={"context": "user:"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["context"], "user:")
        self.assertAlmostEqual(sum(item["probability"] for item in payload["candidates"]), 1.0, places=5)

    def test_request_validation_returns_422(self):
        for body in (
            {"prompt": "x", "max_new_tokens": 81},
            {"prompt": "x", "temperature": 2.1},
            {"prompt": "x", "max_new_tokens": "not-a-number"},
        ):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/api/generate", json=body).status_code, 422)

    def test_typed_artifact_errors_are_http_errors(self):
        from ml.model_adapter import ArtifactInvalid, ArtifactMissing, BackendUnsupported

        for error, expected_status, route in (
            (ArtifactMissing("metrics.json missing"), 503, "/api/metrics"),
            (ArtifactInvalid("metrics.json corrupt"), 500, "/api/metrics"),
            (BackendUnsupported("torch artifact unsupported"), 501, "/api/generate"),
        ):
            with self.subTest(code=error.code):
                target = "load_metrics" if route.endswith("metrics") else "generate"
                with patch.object(self.main, target, side_effect=error):
                    response = self.client.get(route) if route.endswith("metrics") else self.client.post(route, json={"prompt": "x"})
                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(response.json()["error"]["code"], error.code)


if __name__ == "__main__":
    unittest.main()
