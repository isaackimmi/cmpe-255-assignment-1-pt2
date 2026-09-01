"""Small artifact-backed inference layer shared by the FastAPI server.

The training experiment remains in ``run_experiment.py``. This module deliberately
loads its checked-in artifacts instead of inventing dashboard-only numbers, making
the client/server path reproducible and cheap to run locally.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
SERVICE_AREA = {"longitude": (-74.3, -73.65), "latitude": (40.45, 40.95)}
REQUIRED_PREDICTION_COLUMNS = {
    "pickup_datetime", "actual_seconds", "predicted_seconds", "global_median_seconds",
    "distance_miles", "hour", "weekday", "is_weekend", "robust_inlier",
}


def _number(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def _finite(value: object, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid_artifact_value:{field}") from error
    if not math.isfinite(number):
        raise ValueError(f"invalid_artifact_value:{field}")
    return number


def load_metrics() -> dict:
    return json.loads((OUTPUTS / "metrics.json").read_text())


def load_predictions() -> list[dict]:
    with (OUTPUTS / "predictions.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not REQUIRED_PREDICTION_COLUMNS.issubset(rows[0]):
        raise ValueError("prediction_artifact_schema_mismatch")
    for row in rows:
        for field in REQUIRED_PREDICTION_COLUMNS - {"pickup_datetime"}:
            _finite(row.get(field), field)
    return rows


def load_feature_importance() -> list[dict]:
    with (OUTPUTS / "feature_importance.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    coefficient_field = "absolute_coefficient" if rows and "absolute_coefficient" in rows[0] else "standardized_abs_coefficient"
    if not rows or "feature" not in rows[0] or coefficient_field not in rows[0]:
        raise ValueError("feature_importance_artifact_schema_mismatch")
    for row in rows:
        row["absolute_coefficient"] = _finite(row.get(coefficient_field), coefficient_field)
    return rows


def _matches(row: dict, slice_name: str, distance_median: float) -> bool:
    if slice_name in ("all", ""):
        return True
    if slice_name == "rush":
        if row.get("is_rush_hour") not in (None, ""):
            return row.get("is_rush_hour") in ("1", "1.0", "true", "True")
        hour = _finite(row.get("hour"), "hour")
        return 7 <= hour <= 9 or 16 <= hour <= 19
    if slice_name == "off_peak":
        return not _matches(row, "rush", distance_median)
    if slice_name == "weekend":
        if row.get("is_weekend") not in (None, ""):
            return row.get("is_weekend") in ("1", "1.0", "true", "True")
        weekday = _finite(row.get("weekday"), "weekday")
        return weekday >= 5
    if slice_name == "weekday":
        return not _matches(row, "weekend", distance_median)
    distance = _finite(row.get("distance_miles"), "distance_miles")
    if slice_name == "short":
        return distance < distance_median
    if slice_name == "long":
        return distance >= distance_median
    raise ValueError(f"unknown_slice:{slice_name}")


def _score(rows: list[dict], actual_key: str = "actual", prediction_key: str = "prediction") -> dict:
    actual = [_number(row.get(actual_key)) for row in rows]
    predicted = [_number(row.get(prediction_key)) for row in rows]
    if not rows:
        return {"rows": 0, "mae_seconds": None, "rmse_seconds": None, "r2": None}
    errors = [p - a for a, p in zip(actual, predicted)]
    mean_actual = sum(actual) / len(actual)
    ss_total = sum((a - mean_actual) ** 2 for a in actual)
    ss_residual = sum(error ** 2 for error in errors)
    return {
        "rows": len(rows),
        "mae_seconds": round(sum(abs(error) for error in errors) / len(errors), 3),
        "rmse_seconds": round(math.sqrt(ss_residual / len(errors)), 3),
        "r2": round(1 - ss_residual / ss_total, 4) if ss_total else None,
    }


def prediction_slice(slice_name: str = "all", population: str = "primary") -> dict:
    all_rows = load_predictions()
    distances = [_finite(row.get("distance_miles"), "distance_miles") for row in all_rows]
    distance_median = sorted(distances)[len(distances) // 2]
    rows = all_rows
    if population == "robust":
        rows = [row for row in rows if row.get("robust_inlier") in ("1", "1.0", "true", "True")]
    elif population != "primary":
        raise ValueError(f"unknown_population:{population}")
    rows = [row for row in rows if _matches(row, slice_name, distance_median)]
    for row in rows:
        row["actual"] = _finite(row.get("actual_seconds"), "actual_seconds")
        row["prediction"] = _finite(row.get("predicted_seconds"), "predicted_seconds")
        row["residual_seconds"] = round(row["prediction"] - row["actual"], 3)
    metrics = _score(rows)
    baseline_rows = [{"actual": row["actual"], "prediction": _finite(row.get("global_median_seconds"), "global_median_seconds")} for row in rows]
    metrics["baseline"] = _score(baseline_rows)
    return {"slice": slice_name, "population": population, "distance_boundary_miles": round(distance_median, 4), "metrics": metrics, "rows": rows}


def _haversine_miles(pickup_lat: float, pickup_lon: float, dropoff_lat: float, dropoff_lon: float) -> float:
    dlat = math.radians(dropoff_lat - pickup_lat)
    dlon = math.radians(dropoff_lon - pickup_lon)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(pickup_lat)) * math.cos(math.radians(dropoff_lat)) * math.sin(dlon / 2) ** 2
    return 3958.8 * 2 * math.asin(min(1, math.sqrt(max(0, a))))


def estimate(payload: dict) -> dict:
    try:
        pickup_lat = float(payload["pickup_latitude"])
        pickup_lon = float(payload["pickup_longitude"])
        dropoff_lat = float(payload["dropoff_latitude"])
        dropoff_lon = float(payload["dropoff_longitude"])
        passengers = int(payload.get("passenger_count", 1))
        raw_datetime = str(payload["pickup_datetime"])
        pickup_datetime = datetime.fromisoformat(raw_datetime.replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid_estimate_request") from error
    if not 1 <= passengers <= 10:
        raise ValueError("passenger_count_out_of_range")
    if not all(math.isfinite(value) for value in (pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)):
        raise ValueError("coordinates_must_be_finite")
    if not SERVICE_AREA["latitude"][0] <= pickup_lat <= SERVICE_AREA["latitude"][1] or not SERVICE_AREA["latitude"][0] <= dropoff_lat <= SERVICE_AREA["latitude"][1]:
        raise ValueError("coordinates_outside_service_area")
    if not SERVICE_AREA["longitude"][0] <= pickup_lon <= SERVICE_AREA["longitude"][1] or not SERVICE_AREA["longitude"][0] <= dropoff_lon <= SERVICE_AREA["longitude"][1]:
        raise ValueError("coordinates_outside_service_area")
    # The training contract interprets naive timestamps as NYC local time and
    # rejects ambiguous DST fall-back values. Mirror that contract for requests.
    from run_experiment import parse_timestamp
    try:
        pickup_datetime = parse_timestamp(raw_datetime)
    except ValueError as error:
        raise ValueError(str(error)) from error
    if not datetime(2010, 1, 1) <= pickup_datetime < datetime(2030, 1, 1):
        raise ValueError("timestamp_out_of_coverage")
    distance = _haversine_miles(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)
    if distance <= 0:
        raise ValueError("route_distance_must_be_positive")
    if distance >= 100:
        raise ValueError("route_exceeds_100_miles")
    rush = int(7 <= pickup_datetime.hour <= 9 or 16 <= pickup_datetime.hour <= 19)
    seconds = max(60, round(240 + 115 * distance + 90 * rush + 25 * (passengers - 1)))
    return {
        "estimated_duration_seconds": seconds,
        "estimated_duration_minutes": round(seconds / 60, 2),
        "distance_miles": round(distance, 3),
        "is_rush_hour": bool(rush),
        "mode": "deterministic synthetic teaching estimate",
        "disclaimer": "This is a deterministic synthetic teaching estimate that mirrors the fallback generator's directional relationships; it is not a production prediction service.",
    }
