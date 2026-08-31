import csv
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from enterprise_audit import LABEL_COLUMN, PREDICTION_TIME_COLUMN, SAFE_FEATURES, _metric, audit_dataset, generate_sample


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sample.csv"
        generate_sample(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def _rows(self):
        with self.path.open(newline="") as handle:
            return list(csv.DictReader(handle))

    def _write(self, path, rows, fields=None):
        fields = fields or list(rows[0])
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _clean_path(self):
        rows = self._rows()
        rows[6]["monthly_spend"] = "123.45"
        rows.pop()
        clean = Path(self.tmp.name) / "clean.csv"
        self._write(clean, rows)
        return clean

    def _audit(self, path, **kwargs):
        return audit_dataset(path, prediction_time_column=PREDICTION_TIME_COLUMN, label_column=LABEL_COLUMN, feature_manifest=SAFE_FEATURES, **kwargs)

    def test_seeded_defects_are_reported_and_model_is_blocked(self):
        result = self._audit(self.path)
        statuses = {check["name"]: check["status"] for check in result["checks"]}
        self.assertEqual(statuses["schema"], "FAIL")
        self.assertEqual(statuses["missingness"], "FAIL")
        self.assertEqual(statuses["duplicate_identifiers"], "FAIL")
        self.assertEqual(statuses["leakage_risk"], "PASS")
        self.assertEqual(statuses["model_quality"], "INCONCLUSIVE")
        self.assertEqual(result["release_recommendation"], "CONDITIONAL")
        self.assertEqual(result["decision_state"], "BLOCKED")

    def test_clean_fixture_can_pass_real_leakage_check(self):
        result = self._audit(self._clean_path())
        checks = {check["name"]: check for check in result["checks"]}
        self.assertEqual(checks["schema"]["status"], "PASS")
        self.assertEqual(checks["domain_validity"]["status"], "PASS")
        self.assertEqual(checks["leakage_risk"]["status"], "PASS")
        self.assertEqual(checks["leakage_risk"]["evidence"]["offending_features"], [])
        self.assertIn(result["model_quality"]["status"], {"PASS", "WARN"})
        self.assertEqual(result["release_recommendation"], "APPROVE")

    def test_warning_only_model_result_is_conditional(self):
        rows = self._rows()
        rows[6]["monthly_spend"] = "123.45"
        rows.pop()
        for row in rows:
            row["support_tickets_90d"] = "0"
        path = Path(self.tmp.name) / "warning.csv"
        self._write(path, rows)
        result = self._audit(path)
        self.assertEqual(result["model_quality"]["status"], "WARN")
        self.assertEqual(result["release_recommendation"], "CONDITIONAL")
        self.assertEqual(result["decision_state"], "CONDITIONAL")

    def test_unsafe_feature_manifest_is_detected(self):
        result = audit_dataset(self._clean_path(), prediction_time_column=PREDICTION_TIME_COLUMN, label_column=LABEL_COLUMN, feature_manifest=["churned", "churn_confirmed_at"])
        leakage = next(check for check in result["checks"] if check["name"] == "leakage_risk")
        self.assertEqual(leakage["status"], "FAIL")
        offending = leakage["evidence"]["offending_features"]
        self.assertEqual({item["column"] for item in offending}, {"churned", "churn_confirmed_at"})

    def test_missing_prediction_contract_does_not_fall_back_silently(self):
        result = audit_dataset(self._clean_path())
        leakage = next(check for check in result["checks"] if check["name"] == "leakage_risk")
        self.assertEqual(leakage["status"], "INCONCLUSIVE")
        self.assertTrue(leakage["evidence"]["invalid_contract"])
        self.assertEqual(result["release_recommendation"], "CONDITIONAL")

    def test_later_row_shape_error_fails_closed(self):
        rows = self._rows()
        malformed = Path(self.tmp.name) / "later_row_extra.csv"
        fields = list(rows[0])
        with malformed.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields)
            writer.writerow([rows[0][field] for field in fields])
            writer.writerow([rows[1][field] for field in fields] + ["undeclared"])
        result = self._audit(malformed)
        checks = {check["name"]: check for check in result["checks"]}
        self.assertEqual(checks["schema"]["status"], "FAIL")
        self.assertEqual(checks["model_quality"]["status"], "INCONCLUSIVE")
        self.assertEqual(checks["schema"]["evidence"]["row_errors"][0]["reason"], "field_count")

    def test_malformed_holdout_value_is_inconclusive_not_an_exception(self):
        rows = self._rows()
        rows[6]["monthly_spend"] = "123.45"
        rows.pop()
        rows[-1]["support_tickets_90d"] = "not-an-int"
        path = Path(self.tmp.name) / "bad_holdout.csv"
        self._write(path, rows)
        result = self._audit(path)
        checks = {check["name"]: check for check in result["checks"]}
        self.assertEqual(checks["schema"]["status"], "FAIL")
        self.assertEqual(checks["model_quality"]["status"], "INCONCLUSIVE")

    def test_missing_sentinels_and_non_finite_values_are_normalized_or_rejected(self):
        rows = self._rows()[:]
        rows[0]["monthly_spend"] = "  N/A "
        rows[1]["monthly_spend"] = "NaN"
        result = Path(self.tmp.name) / "sentinels.csv"
        self._write(result, rows[:-1])
        audit = self._audit(result)
        missing = next(check for check in audit["checks"] if check["name"] == "missingness")
        schema = next(check for check in audit["checks"] if check["name"] == "schema")
        self.assertEqual(missing["evidence"]["null_counts"]["monthly_spend"], 3)
        self.assertEqual(schema["status"], "FAIL")

    def test_duplicate_headers_and_domain_ranges_are_controlled(self):
        rows = self._rows()[:1]
        rows[0]["customer_id"] = ""
        rows[0]["tenure_months"] = "-1"
        malformed = Path(self.tmp.name) / "duplicate_header.csv"
        fields = list(rows[0])
        with malformed.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields + ["plan"])
            writer.writerow([rows[0][field] for field in fields] + [rows[0]["plan"]])
        result = self._audit(malformed)
        checks = {check["name"]: check for check in result["checks"]}
        self.assertEqual(checks["schema"]["status"], "FAIL")
        self.assertEqual(checks["domain_validity"]["status"], "INCONCLUSIVE")
        self.assertTrue(checks["schema"]["evidence"]["duplicate_headers"])
        self.assertTrue(any(item["column"] == "customer_id" for item in checks["domain_validity"]["evidence"]["violations"]))
        self.assertTrue(any(item["column"] == "tenure_months" for item in checks["domain_validity"]["evidence"]["violations"]))

    def test_reproducibility_hash_is_stable_across_audit_runs(self):
        first = self._audit(self._clean_path())
        second = self._audit(self._clean_path())
        self.assertTrue(first["reproducibility"]["rerun_match"])
        self.assertEqual(first["reproducibility"]["canonical_result_sha256"], second["reproducibility"]["canonical_result_sha256"])
        self.assertTrue(first["reproducibility"]["split"].startswith("time-ordered"))
        self.assertTrue(first["reproducibility"]["split_manifest"]["test_row_ids"])

    def test_metric_rejects_mismatched_arrays(self):
        with self.assertRaises(ValueError):
            _metric([0, 1], [0])


if __name__ == "__main__":
    unittest.main()
