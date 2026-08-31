import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from skills_lab import *
from run_lab import run_pipeline


PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "customer_health.csv")


class SkillsLabTests(unittest.TestCase):
    def test_cleaning_deduplicates_and_imputes(self):
        rows, removed = load_clean(DATA_PATH)
        self.assertEqual((len(rows), removed), (23, 1))
        self.assertTrue(all(row["monthly_usage"] is not None for row in rows))

    def test_validation_rejects_bad_domains_and_conflicting_duplicates(self):
        header = ["customer_id", "tenure_months", "monthly_usage", "support_tickets", "plan", "renewed"]
        cases = [
            ["C001", "-1", "20", "1", "basic", "0"],
            ["C001", "1", "20", "1", "basic", "2"],
            ["C001", "1", "nan", "1", "basic", "0"],
        ]
        for values in cases:
            with self.subTest(values=values), tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as handle:
                csv.writer(handle).writerows([header, values])
                path = handle.name
            try:
                with self.assertRaises(ValueError):
                    load_clean(path, impute=False)
            finally:
                os.unlink(path)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as handle:
            csv.writer(handle).writerows([header, ["C001", "1", "20", "1", "basic", "0"], ["C001", "1", "21", "1", "basic", "0"]])
            path = handle.name
        try:
            with self.assertRaisesRegex(ValueError, "conflicting duplicate"):
                load_clean(path, impute=False)
        finally:
            os.unlink(path)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as handle:
            csv.writer(handle).writerows([header, ["C001", "1", "", "1", "basic", "0"]])
            path = handle.name
        try:
            with self.assertRaisesRegex(ValueError, "all values are missing"):
                load_clean(path)
        finally:
            os.unlink(path)

    def test_split_local_imputation_does_not_use_test_values(self):
        rows, _ = load_clean(DATA_PATH, impute=False)
        train, test = train_test_split(rows, test_fraction=0.30, seed=255)
        train_filled, train_info = impute_numeric(train, train, ("monthly_usage",))
        test_filled, test_info = impute_numeric(test, train, ("monthly_usage",))
        self.assertEqual(train_info["medians"]["monthly_usage"], median(row["monthly_usage"] for row in train if row["monthly_usage"] is not None))
        self.assertEqual(test_info["medians"], train_info["medians"])
        self.assertEqual(sum(row["monthly_usage"] is None for row in test), test_info["counts"]["monthly_usage"])
        self.assertTrue(all(row["monthly_usage"] is not None for row in train_filled + test_filled if row["monthly_usage"] is not None))

    def test_regression_and_metrics(self):
        self.assertEqual(linear_regression([1, 2, 3], [2, 4, 6]), (0.0, 2.0))
        self.assertEqual(regression_metrics([2, 4], [2, 5])["mae"], 0.5)
        with self.assertRaisesRegex(ValueError, "equal lengths"):
            correlation([1, 2, 3], [1, 2])
        with self.assertRaisesRegex(ValueError, "distinct x"):
            linear_regression([1, 1], [2, 3])
        with self.assertRaises(ValueError):
            regression_metrics([], [])
        with self.assertRaisesRegex(ValueError, "non-empty"):
            mean([])

    def test_classification_counts_and_edge_validation(self):
        metrics = classification_metrics([0, 0, 1, 1], [0, 1, 1, 0])
        self.assertEqual(metrics["confusion_matrix"], [[1, 1], [1, 1]])
        self.assertEqual(metrics["accuracy"], 0.5)
        self.assertEqual(metrics["f1"], 0.5)
        with self.assertRaisesRegex(ValueError, "0/1"):
            classification_metrics([0, 2], [0, 1])
        with self.assertRaisesRegex(ValueError, "equal lengths"):
            classification_metrics([0], [0, 1])

    def test_scaled_kmeans_is_deterministic_and_validated(self):
        points = [[0, 0], [0.1, 0.1], [10, 10], [10.1, 10.1]]
        self.assertEqual(kmeans(points, seed=255), kmeans(points, seed=255))
        labels, centers, metadata = kmeans(points, k=2, seed=255, n_init=5, return_metadata=True)
        self.assertTrue(metadata["converged"])
        self.assertEqual(len(metadata["initialization_inertias"]), 5)
        for point, label in zip(points, labels):
            distances = [sum((point[d] - center[d]) ** 2 for d in range(2)) for center in centers]
            self.assertEqual(label, distances.index(min(distances)))
        with self.assertRaisesRegex(ValueError, "between 1 and"):
            kmeans(points, k=0)
        with self.assertRaisesRegex(ValueError, "non-empty"):
            kmeans([])
        with self.assertRaisesRegex(ValueError, "dimension"):
            kmeans([[1, 2], [3]])

    def test_degenerate_svg_inputs_produce_valid_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            scatter = os.path.join(directory, "scatter.svg")
            clusters = os.path.join(directory, "clusters.svg")
            svg_scatter([], scatter)
            svg_scatter([{"tenure_months": 1.0, "monthly_usage": 2.0, "renewed": 1}], scatter)
            svg_clusters([], [], [], clusters)
            svg_clusters([[1.0, 2.0]], [0], [[1.0, 2.0]], clusters)
            for path in (scatter, clusters):
                with open(path, encoding="utf-8") as handle:
                    contents = handle.read()
                self.assertIn("<svg", contents)
                self.assertIn("0.0", contents)
                self.assertIn("cluster 0", contents) if path == clusters else self.assertIn("renewed", contents)

    def test_pipeline_artifacts_use_observed_held_out_targets(self):
        metrics, summary = run_pipeline(PROJECT_ROOT)
        regression = metrics["regression"]
        classification = metrics["classification"]
        self.assertEqual(regression["scored_rows"], len(summary["regression_predictions"]))
        self.assertEqual(regression["missing_train_targets_excluded"], 1)
        self.assertTrue(all(item["actual_usage"] is not None for item in summary["regression_predictions"]))
        self.assertEqual(classification["evaluation"], "single seeded stratified holdout")
        self.assertIn("f1", classification)
        self.assertIn("majority_baseline_accuracy", classification)
        self.assertEqual(metrics["data_quality"]["raw_rows"], 24)
        self.assertEqual(metrics["data_quality"]["missing_values_imputed"], 1)
        self.assertEqual(metrics["clustering"]["k"], 2)
        self.assertGreater(metrics["clustering"]["silhouette"], 0)


if __name__ == "__main__":
    unittest.main()
