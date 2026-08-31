"""Smoke/quality checks for the experiment outputs."""
from pathlib import Path
import json
import csv

ROOT = Path(__file__).resolve().parent
out = ROOT / "outputs"
metrics = json.loads((out / "metrics.json").read_text())
assert metrics["rows_after_cleaning"] > 100
assert metrics["train_rows"] > metrics["test_rows"] > 0
assert metrics["linear_log_target"]["mae_seconds"] < metrics["baseline"]["mae_seconds"]
with open(out / "predictions.csv", newline="") as f:
    pred = list(csv.DictReader(f))
assert len(pred) == metrics["test_rows"]
assert all(row["actual_seconds"] and row["predicted_seconds"] for row in pred)
for name in ["duration_distribution.svg", "predicted_vs_actual.svg", "feature_importance.csv"]:
    assert (out / name).stat().st_size > 0
print("Validation passed: metrics, predictions, and plots are present and consistent.")
