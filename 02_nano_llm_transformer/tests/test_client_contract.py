import unittest
from pathlib import Path


CLIENT = Path(__file__).resolve().parents[1] / "client"


class ClientContractTests(unittest.TestCase):
    def test_vite_client_has_expected_runtime_files(self):
        self.assertTrue((CLIENT / "package.json").exists())
        self.assertTrue((CLIENT / "vite.config.js").exists())
        self.assertTrue((CLIENT / "index.html").exists())
        self.assertTrue((CLIENT / "src" / "main.js").exists())

    def test_client_calls_api_and_surfaces_failure_state(self):
        source = (CLIENT / "src" / "main.js").read_text(encoding="utf-8")
        for route in ("/api/metrics", "/api/behavior", "/api/generate", "/api/probabilities"):
            self.assertIn(route, source)
        self.assertIn("API unavailable", source)
        self.assertIn("Request error", source)
        self.assertIn("max_new_tokens", source)


if __name__ == "__main__":
    unittest.main()
