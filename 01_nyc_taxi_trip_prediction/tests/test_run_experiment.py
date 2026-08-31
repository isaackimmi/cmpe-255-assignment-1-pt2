import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_experiment", PROJECT / "run_experiment.py")
experiment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(experiment)


class ExperimentRegressionTests(unittest.TestCase):
    def test_reversed_input_is_sorted_before_split(self):
        rows = list(reversed(experiment.make_sample(200)))
        records, _ = experiment.featurize(rows, return_audit=True)
        train, test = experiment.split_records(records)
        self.assertLess(train[-1]["timestamp"], test[0]["timestamp"])
        self.assertEqual(records, sorted(records, key=lambda record: (record["timestamp"], str(record["id"]))))

    def test_reversed_csv_run_records_a_chronological_cutoff(self):
        rows = list(reversed(experiment.make_sample(120)))
        with tempfile.NamedTemporaryFile("w", newline="", suffix=".csv") as handle:
            writer = csv.DictWriter(handle, fieldnames=experiment.REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            with tempfile.TemporaryDirectory() as directory:
                metrics = experiment.run_experiment(input_path=handle.name, output_dir=Path(directory))
        self.assertLess(
            metrics["split_cutoff"]["train_max_pickup_datetime"],
            metrics["split_cutoff"]["test_min_pickup_datetime"],
        )
        self.assertEqual(metrics["source_sha256"] and len(metrics["source_sha256"]), 64)

    def test_cleaning_reports_invalid_rows(self):
        valid = experiment.make_sample(2)
        invalid_coordinate = dict(valid[0], id="invalid-coordinate", pickup_latitude="not-a-number")
        invalid_range = dict(valid[1], id="invalid-range", pickup_longitude=250)
        records, audit = experiment.featurize([valid[0], invalid_coordinate, invalid_range], return_audit=True)
        self.assertEqual(len(records), 1)
        self.assertEqual(audit["input_rows"], 3)
        self.assertEqual(audit["dropped_by_reason"]["parse_error"], 1)
        self.assertEqual(audit["dropped_by_reason"]["invalid_longitude"], 1)

    def test_duration_threshold_uses_training_only(self):
        rows = experiment.make_sample(20)
        records, _ = experiment.featurize(rows, return_audit=True)
        train, test = experiment.split_records(records, fraction=0.8)
        for record in train:
            record["target"] = 1000
        for record in test:
            record["target"] = 150
        test[-1]["target"] = 10_000_000
        filtered_train, filtered_test, upper, drops = experiment.apply_duration_policy(train, test)
        self.assertEqual(len(filtered_train), len(train))
        self.assertEqual(len(filtered_test), len(test) - 1)
        self.assertEqual(drops["train_duration_outlier"], 0)
        self.assertGreater(upper, 0)

    def test_primary_policy_keeps_test_targets_for_scoring(self):
        rows = experiment.make_sample(20)
        records, _ = experiment.featurize(rows, return_audit=True)
        train, test = experiment.split_records(records, fraction=0.8)
        test[-1]["target"] = 10_000_000
        kept_train, kept_test, upper, drops = experiment.apply_duration_policy(train, test, trim_test=False)
        self.assertEqual(len(kept_test), len(test))
        self.assertEqual(drops["test_duration_outlier"], 1)
        self.assertGreater(upper, 0)

    def test_run_writes_audited_metadata_and_recomputable_predictions(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            metrics = experiment.run_experiment(sample_size=300, output_dir=output_dir)
            self.assertEqual(metrics["input_rows"], 300)
            self.assertEqual(metrics["run_config"]["seed"], experiment.SEED)
            self.assertEqual(len(metrics["temporal_validation"]["folds"]), 3)
            self.assertEqual(metrics["test_rows"], metrics["target_policy"]["primary_test_rows_scored"])
            self.assertLessEqual(metrics["test_rows_robust_inlier"], metrics["test_rows"])
            with open(output_dir / "predictions.csv", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), metrics["test_rows"])
            self.assertIn("pickup_datetime", rows[0])
            self.assertIn("robust_inlier", rows[0])
            self.assertEqual(json.loads((output_dir / "metrics.json").read_text()), metrics)

    def test_mixed_timestamp_awareness_is_rejected(self):
        rows = experiment.make_sample(3)
        rows[1]["pickup_datetime"] = "2016-01-02T00:00:00+00:00"
        records, audit = experiment.featurize(rows, return_audit=True)
        self.assertEqual(len(records), 2)
        self.assertEqual(audit["dropped_by_reason"]["mixed_timestamp_timezone_awareness"], 1)

    def test_split_rejects_a_single_tied_timestamp_group(self):
        rows = experiment.make_sample(8)
        for row in rows:
            row["pickup_datetime"] = "2016-01-01 12:00:00"
        records, _ = experiment.featurize(rows, return_audit=True)
        with self.assertRaises(ValueError):
            experiment.split_records(records)

    def test_domain_contract_rejects_duplicate_and_out_of_area_rows(self):
        rows = experiment.make_sample(3)
        rows[1]["id"] = rows[0]["id"]
        rows[2]["pickup_longitude"] = -75
        _, audit = experiment.featurize(rows, return_audit=True)
        self.assertEqual(audit["dropped_by_reason"]["duplicate_id"], 1)
        self.assertEqual(audit["dropped_by_reason"]["outside_service_area_longitude"], 1)


if __name__ == "__main__":
    unittest.main()
