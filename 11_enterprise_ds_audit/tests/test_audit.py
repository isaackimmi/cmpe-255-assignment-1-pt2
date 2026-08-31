import csv, json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from enterprise_audit import audit_dataset, generate_sample


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sample.csv"
        generate_sample(self.path)

    def tearDown(self): self.tmp.cleanup()

    def test_finds_expected_governance_defects(self):
        result = audit_dataset(self.path)
        statuses = {c["name"]: c["status"] for c in result["checks"]}
        self.assertEqual(statuses["schema"], "FAIL")
        self.assertEqual(statuses["missingness"], "FAIL")
        self.assertEqual(statuses["duplicate_identifiers"], "FAIL")
        self.assertEqual(statuses["leakage_risk"], "FAIL")
        self.assertEqual(result["release_recommendation"], "CONDITIONAL")

    def test_generation_is_reproducible(self):
        other = Path(self.tmp.name) / "other.csv"
        generate_sample(other)
        self.assertEqual(self.path.read_bytes(), other.read_bytes())

    def test_model_quality_is_reported(self):
        result = audit_dataset(self.path)
        quality = result["model_quality"]
        self.assertGreater(quality["test_rows"], 0)
        for key in ("accuracy", "precision", "recall", "f1", "balanced_accuracy"):
            self.assertIn(key, quality["model"])


if __name__ == "__main__": unittest.main()
