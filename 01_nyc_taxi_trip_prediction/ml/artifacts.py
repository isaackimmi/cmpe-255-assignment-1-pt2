import csv
import json

from .config import OUTPUTS, REQUIRED_PREDICTION_COLUMNS
from .numeric import finite


def load_metrics() -> dict:
    return json.loads((OUTPUTS / "metrics.json").read_text())


def load_predictions() -> list[dict]:
    with (OUTPUTS / "predictions.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not REQUIRED_PREDICTION_COLUMNS.issubset(rows[0]):
        raise ValueError("prediction_artifact_schema_mismatch")
    for row in rows:
        for field in REQUIRED_PREDICTION_COLUMNS - {"pickup_datetime"}:
            finite(row.get(field), field)
    return rows


def load_feature_importance() -> list[dict]:
    with (OUTPUTS / "feature_importance.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    coefficient_field = "absolute_coefficient" if rows and "absolute_coefficient" in rows[0] else "standardized_abs_coefficient"
    if not rows or "feature" not in rows[0] or coefficient_field not in rows[0]:
        raise ValueError("feature_importance_artifact_schema_mismatch")
    for row in rows:
        row["absolute_coefficient"] = finite(row.get(coefficient_field), coefficient_field)
    return rows
