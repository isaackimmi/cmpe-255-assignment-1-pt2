import unittest
from pathlib import Path


CLIENT = Path(__file__).resolve().parents[1] / "client"


class ClientContractTests(unittest.TestCase):
    def test_vite_client_has_expected_runtime_files(self):
        self.assertTrue((CLIENT / "package.json").exists())
        self.assertTrue((CLIENT / "vite.config.js").exists())
        self.assertTrue((CLIENT / "index.html").exists())
        self.assertTrue((CLIENT / "src" / "main.jsx").exists())
        self.assertTrue((CLIENT / "src" / "App.jsx").exists())

    def test_client_calls_api_and_surfaces_failure_state(self):
        source = (CLIENT / "src" / "api" / "client.js").read_text(encoding="utf-8")
        for route in ("/api/metrics", "/api/behavior", "/api/generate", "/api/probabilities"):
            self.assertIn(route, source)
        self.assertIn("max_new_tokens", source)

    def test_client_uses_react_radix_and_feature_components(self):
        package = (CLIENT / "package.json").read_text(encoding="utf-8")
        self.assertIn('"react"', package)
        self.assertIn('"@radix-ui/themes"', package)
        components = list((CLIENT / "src" / "components").rglob("*.jsx"))
        self.assertGreaterEqual(len(components), 10)
        for folder in ("evidence", "layout", "method", "playground"):
            self.assertTrue((CLIENT / "src" / "components" / folder).is_dir(), folder)
        for component in (
            "layout/AppShell.jsx",
            "evidence/EvidenceMetrics.jsx",
            "playground/GenerationPlayground.jsx",
            "playground/ProbabilityPanel.jsx",
            "playground/TraceList.jsx",
            "ui/Panel.jsx",
            "ui/SectionHeader.jsx",
            "ui/StatusPill.jsx",
        ):
            self.assertTrue((CLIENT / "src" / "components" / component).exists(), component)
        self.assertTrue((CLIENT / "src" / "hooks" / "useModelEvidence.js").exists())
        self.assertTrue((CLIENT / "src" / "api" / "client.js").exists())
        self.assertFalse((CLIENT / "src" / "components" / "evidence" / "MetricGrid.jsx").exists())
        self.assertNotIn("export default", (CLIENT / "src" / "hooks" / "useModelEvidence.js").read_text())

    def test_ui_surfaces_connection_and_request_failures(self):
        hook = (CLIENT / "src" / "hooks" / "useModelEvidence.js").read_text(encoding="utf-8")
        form = (CLIENT / "src" / "components" / "playground" / "GenerationForm.jsx").read_text(encoding="utf-8")
        self.assertIn("unavailable", hook)
        self.assertIn("Request error", form)


if __name__ == "__main__":
    unittest.main()
