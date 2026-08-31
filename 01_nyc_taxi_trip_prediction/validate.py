"""Independent quality checks for the experiment outputs."""
from datetime import datetime
from pathlib import Path
import csv
import json
import math
import statistics

ROOT = Path(__file__).resolve().parent
out = ROOT / "outputs"
metrics = json.loads((out / "metrics.json").read_text())

assert metrics["input_rows"] >= metrics["rows_after_structural_cleaning"] == metrics["rows_after_cleaning"] > 100
assert metrics["train_rows"] > metrics["test_rows"] > 0
assert metrics["train_rows"] < metrics["target_policy"]["train_rows_before_trim"]
assert metrics["target_policy"]["primary_test_rows_scored"] == metrics["test_rows"]
assert metrics["target_policy"]["robust_inlier_test_rows_scored"] == metrics["test_rows_robust_inlier"]
assert metrics["test_rows_robust_inlier"] <= metrics["test_rows"]
assert metrics["target_policy"]["test_duration_outlier_rows"] == metrics["test_rows"] - metrics["test_rows_robust_inlier"]
assert 0 <= metrics["drop_rate"] <= metrics["run_config"]["cleaning"]["maximum_allowed_drop_rate"]
assert metrics["split_cutoff"]["train_max_pickup_datetime"] < metrics["split_cutoff"]["test_min_pickup_datetime"]
assert metrics["run_config"]["timestamp_policy"]["mixed_awareness"] == "rejected"
assert metrics["run_config"]["timestamp_policy"]["split_tie_handling"]
assert len(metrics["temporal_validation"]["folds"]) == 3


def recompute(actual, predicted):
    mae = sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)
    rmse = math.sqrt(sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual))
    mean = statistics.mean(actual)
    ss_total = sum((a - mean) ** 2 for a in actual)
    r2 = 1 - sum((a - p) ** 2 for a, p in zip(actual, predicted)) / ss_total if ss_total else 0
    return {"mae_seconds": round(mae, 3), "rmse_seconds": round(rmse, 3), "r2": round(r2, 4)}


with open(out / "predictions.csv", newline="") as handle:
    predictions = list(csv.DictReader(handle))
assert len(predictions) == metrics["test_rows"]
assert all(row["pickup_datetime"] and row["actual_seconds"] and row["predicted_seconds"] for row in predictions)
timestamps = [datetime.fromisoformat(row["pickup_datetime"]) for row in predictions]
assert timestamps == sorted(timestamps)
assert all(row["robust_inlier"] in {"0", "1"} for row in predictions)
assert sum(row["robust_inlier"] == "1" for row in predictions) == metrics["test_rows_robust_inlier"]

actual = [float(row["actual_seconds"]) for row in predictions]
published_columns = {
    "baseline": "global_median_seconds",
    "recent_median_baseline": "recent_median_seconds",
    "hour_median_baseline": "hour_median_seconds",
    "linear_log_target": "predicted_seconds",
}
for metric_name, column in published_columns.items():
    recomputed = recompute(actual, [float(row[column]) for row in predictions])
    assert recomputed == metrics[metric_name], (metric_name, recomputed, metrics[metric_name])

assert metrics["linear_log_target"]["mae_seconds"] < metrics["baseline"]["mae_seconds"]
assert metrics["linear_log_target"]["rmse_seconds"] < metrics["baseline"]["rmse_seconds"]
assert metrics["linear_log_target"]["mae_seconds"] < metrics["recent_median_baseline"]["mae_seconds"]
assert metrics["linear_log_target"]["mae_seconds"] < metrics["hour_median_baseline"]["mae_seconds"]
assert metrics["robust_inlier_sensitivity"]["test_rows"] == metrics["test_rows_robust_inlier"]
for fold in metrics["temporal_validation"]["folds"]:
    assert fold["split_cutoff"]["train_max_pickup_datetime"] < fold["split_cutoff"]["test_min_pickup_datetime"]
    assert fold["linear_log_target"]["mae_seconds"] < fold["global_median"]["mae_seconds"]
    assert fold["linear_log_target"]["rmse_seconds"] < fold["global_median"]["rmse_seconds"]
assert metrics["temporal_validation"]["fold_summary"]["linear_log_target"]["stdev_mae_seconds"] >= 0

with open(out / "feature_importance.csv", newline="") as handle:
    importance = list(csv.DictReader(handle))
assert len(importance) == len(metrics["run_config"]["features"])
assert importance[0]["standardized_abs_coefficient"]

for name in ["duration_distribution.svg", "predicted_vs_actual.svg", "feature_importance.csv"]:
    assert (out / name).stat().st_size > 0
print("Validation passed: chronological split, cleaning audit, metrics, predictions, and plots are consistent.")
