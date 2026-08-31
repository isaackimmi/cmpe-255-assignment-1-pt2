"""Reproducible NYC taxi trip-duration experiment using only the Python standard library."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import random
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SEED = 255
DEFAULT_SAMPLE_SIZE = 6000
TRAIN_DURATION_QUANTILE = 0.99
MAX_DROP_RATE = 0.25
INPUT_TIMEZONE = "America/New_York"
UTC = timezone.utc
NYC_TIMEZONE = ZoneInfo(INPUT_TIMEZONE)
SERVICE_AREA = {
    "longitude": [-74.3, -73.65],
    "latitude": [40.45, 40.95],
}
ALLOWED_VENDOR_IDS = {1, 2}
TIMESTAMP_COVERAGE = {"min": "2010-01-01 00:00:00", "max": "2030-01-01 00:00:00"}
MODEL_CONFIG = {
    "type": "regularized_linear_regression",
    "target_transform": "log1p",
    "learning_rate": 0.04,
    "iterations": 1800,
    "l2": 0.002,
}
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
REQUIRED_COLUMNS = [
    "id", "vendor_id", "pickup_datetime", "passenger_count",
    "pickup_longitude", "pickup_latitude", "dropoff_longitude",
    "dropoff_latitude", "trip_duration",
]
FEATURE_NAMES = [
    "vendor_id", "passenger_count", "pickup_longitude", "pickup_latitude",
    "dropoff_longitude", "dropoff_latitude", "hour", "weekday", "month",
    "is_weekend", "is_rush_hour", "distance_miles", "delta_longitude",
    "delta_latitude",
]


def make_sample(n: int) -> list[dict]:
    rng = random.Random(SEED)
    start = datetime(2016, 1, 1)
    rows = []
    for i in range(n):
        pickup = start + timedelta(minutes=rng.randrange(90 * 24 * 60))
        plon, plat = rng.gauss(-73.975, .035), rng.gauss(40.755, .030)
        dlon, dlat = plon + rng.gauss(0, .035), plat + rng.gauss(0, .030)
        passenger = rng.randint(1, 4)
        hour = pickup.hour
        rush = int(7 <= hour <= 9 or 16 <= hour <= 19)
        dist = 69 * math.sqrt(
            ((plon - dlon) * math.cos(math.radians(plat))) ** 2
            + (plat - dlat) ** 2
        )
        duration = max(
            60,
            round(240 + 115 * dist + 90 * rush + 25 * (passenger - 1) + rng.gauss(0, 100)),
        )
        rows.append({
            "id": i,
            "vendor_id": rng.randint(1, 2),
            "pickup_datetime": pickup.isoformat(sep=" "),
            "passenger_count": passenger,
            "pickup_longitude": plon,
            "pickup_latitude": plat,
            "dropoff_longitude": dlon,
            "dropoff_latitude": dlat,
            "trip_duration": duration,
        })
    return rows


def read_csv(path: str | Path) -> list[dict]:
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in columns]
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
        return list(reader)


def parse_timestamp(value: object, expect_aware: bool | None = None) -> datetime:
    """Parse one timestamp under the declared NYC-naive/UTC-aware contract."""
    raw = str(value).strip()
    if not raw:
        raise ValueError("missing_timestamp")
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    is_aware = parsed.tzinfo is not None and parsed.utcoffset() is not None
    if expect_aware is not None and is_aware != expect_aware:
        raise ValueError("mixed_timestamp_timezone_awareness")
    if is_aware:
        return parsed.astimezone(UTC).replace(tzinfo=None)

    # Naive values are explicitly NYC local time. Reject DST fall-back values
    # that have two possible UTC interpretations instead of silently guessing.
    local = parsed.replace(tzinfo=NYC_TIMEZONE, fold=0)
    alternate = parsed.replace(tzinfo=NYC_TIMEZONE, fold=1)
    if local.utcoffset() != alternate.utcoffset():
        raise ValueError("ambiguous_local_timestamp")
    return local.astimezone(UTC).replace(tzinfo=None)


def _feature_row(row: dict, timestamp: datetime) -> tuple[list[float], float, datetime]:
    keys = [
        "vendor_id", "passenger_count", "pickup_longitude", "pickup_latitude",
        "dropoff_longitude", "dropoff_latitude",
    ]
    values = {key: float(row[key]) for key in keys}
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("non_finite_numeric")
    if values["vendor_id"] not in ALLOWED_VENDOR_IDS or not values["vendor_id"].is_integer():
        raise ValueError("invalid_vendor_id")
    if not values["passenger_count"].is_integer() or not 1 <= values["passenger_count"] <= 10:
        raise ValueError("invalid_passenger_count")
    if not -180 <= values["pickup_longitude"] <= 180 or not -180 <= values["dropoff_longitude"] <= 180:
        raise ValueError("invalid_longitude")
    if not -90 <= values["pickup_latitude"] <= 90 or not -90 <= values["dropoff_latitude"] <= 90:
        raise ValueError("invalid_latitude")
    if not SERVICE_AREA["longitude"][0] <= values["pickup_longitude"] <= SERVICE_AREA["longitude"][1] \
            or not SERVICE_AREA["longitude"][0] <= values["dropoff_longitude"] <= SERVICE_AREA["longitude"][1]:
        raise ValueError("outside_service_area_longitude")
    if not SERVICE_AREA["latitude"][0] <= values["pickup_latitude"] <= SERVICE_AREA["latitude"][1] \
            or not SERVICE_AREA["latitude"][0] <= values["dropoff_latitude"] <= SERVICE_AREA["latitude"][1]:
        raise ValueError("outside_service_area_latitude")
    if not datetime(2010, 1, 1) <= timestamp < datetime(2030, 1, 1):
        raise ValueError("timestamp_out_of_coverage")

    dlat = math.radians(values["dropoff_latitude"] - values["pickup_latitude"])
    dlon = math.radians(values["dropoff_longitude"] - values["pickup_longitude"])
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(values["pickup_latitude"]))
        * math.cos(math.radians(values["dropoff_latitude"]))
        * math.sin(dlon / 2) ** 2
    )
    distance = 3958.8 * 2 * math.asin(min(1, math.sqrt(max(0, a))))
    if not math.isfinite(distance) or distance >= 100:
        raise ValueError("distance_outlier")

    target = float(row["trip_duration"])
    if not math.isfinite(target):
        raise ValueError("non_finite_duration")
    if target <= 0:
        raise ValueError("non_positive_duration")

    hour, weekday, month = timestamp.hour, timestamp.weekday(), timestamp.month
    features = [
        values["vendor_id"], values["passenger_count"], values["pickup_longitude"],
        values["pickup_latitude"], values["dropoff_longitude"], values["dropoff_latitude"],
        hour, weekday, month, int(weekday >= 5), int(hour in [7, 8, 9, 16, 17, 18, 19]),
        distance, values["dropoff_longitude"] - values["pickup_longitude"],
        values["dropoff_latitude"] - values["pickup_latitude"],
    ]
    return features, target, timestamp


def featurize(rows: list[dict], return_audit: bool = False):
    """Validate and featurize rows, retaining timestamps for chronological splitting.

    Structural cleaning is deliberately independent of the target quantile policy. The
    latter is fitted after the chronological split so no test targets influence cleaning.
    """
    audit = {"input_rows": len(rows), "dropped_by_reason": {}}
    result = []
    seen_ids = set()
    awareness = None
    for row in rows:
        try:
            row_id = str(row.get("id", "")).strip()
            if not row_id:
                raise ValueError("missing_id")
            if row_id in seen_ids:
                raise ValueError("duplicate_id")
            seen_ids.add(row_id)
            raw_timestamp = str(row["pickup_datetime"]).strip()
            parsed_raw = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
            row_awareness = parsed_raw.tzinfo is not None and parsed_raw.utcoffset() is not None
            if awareness is None:
                awareness = row_awareness
            elif row_awareness != awareness:
                raise ValueError("mixed_timestamp_timezone_awareness")
            timestamp = parse_timestamp(raw_timestamp, expect_aware=awareness)
            features, target, timestamp = _feature_row(row, timestamp)
            result.append({"features": features, "target": target, "timestamp": timestamp, "id": row_id})
        except KeyError:
            reason = "missing_value"
        except (ValueError, TypeError, OverflowError) as error:
            reason = str(error) if str(error) in {
                "non_finite_numeric", "invalid_longitude", "invalid_latitude",
                "invalid_passenger_count", "distance_outlier", "non_finite_duration",
                "non_positive_duration", "invalid_vendor_id", "outside_service_area_longitude",
                "outside_service_area_latitude", "timestamp_out_of_coverage", "missing_id",
                "duplicate_id", "missing_timestamp", "ambiguous_local_timestamp",
                "mixed_timestamp_timezone_awareness",
            } else "parse_error"
        else:
            continue
        audit["dropped_by_reason"][reason] = audit["dropped_by_reason"].get(reason, 0) + 1

    result.sort(key=lambda record: (record["timestamp"], str(record["id"])))
    audit["rows_after_structural_cleaning"] = len(result)
    if return_audit:
        return result, audit
    return [(record["features"], record["target"]) for record in result]


def quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a quantile from no values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def apply_duration_policy(
    train: list[dict],
    test: list[dict],
    q: float = TRAIN_DURATION_QUANTILE,
    trim_test: bool = True,
):
    """Fit a train-only target threshold; optionally trim the test sensitivity set.

    The primary evaluation never trims test rows because their targets would be
    unavailable at prediction time. ``trim_test=True`` remains available for
    callers that explicitly need the historical inlier-only sensitivity view.
    """
    upper = quantile([record["target"] for record in train], q)
    train_kept = [record for record in train if record["target"] <= upper]
    test_kept = [record for record in test if record["target"] <= upper] if trim_test else list(test)
    dropped = {
        "train_duration_outlier": len(train) - len(train_kept),
        "test_duration_outlier": sum(record["target"] > upper for record in test),
    }
    return train_kept, test_kept, upper, dropped


def split_records(records: list[dict], fraction: float = 0.8):
    if len(records) < 2:
        raise ValueError("At least two valid rows are required for a train/test split")
    ordered = sorted(records, key=lambda record: (record["timestamp"], str(record["id"])))
    groups = []
    for record in ordered:
        if not groups or groups[-1][0]["timestamp"] != record["timestamp"]:
            groups.append([record])
        else:
            groups[-1].append(record)
    target_cut = len(ordered) * fraction
    cut = min(range(1, len(groups)), key=lambda index: abs(sum(len(group) for group in groups[:index]) - target_cut))
    train = [record for group in groups[:cut] for record in group]
    test = [record for group in groups[cut:] for record in group]
    if train[-1]["timestamp"] >= test[0]["timestamp"]:
        raise AssertionError("Chronological split invariant violated: tied timestamps cross the boundary")
    return train, test


def fit_predict(train_x, train_y, test_x):
    means = [statistics.mean(column) for column in zip(*train_x)]
    scales = [statistics.pstdev(column) or 1 for column in zip(*train_x)]
    z = [[(value - mean) / scale for value, mean, scale in zip(row, means, scales)] for row in train_x]
    test_z = [[(value - mean) / scale for value, mean, scale in zip(row, means, scales)] for row in test_x]
    target = [math.log1p(value) for value in train_y]
    weights = [0.0] * len(FEATURE_NAMES)
    intercept = statistics.mean(target)
    for _ in range(MODEL_CONFIG["iterations"]):
        errors = [intercept + sum(weight * value for weight, value in zip(weights, row)) - actual for row, actual in zip(z, target)]
        intercept -= MODEL_CONFIG["learning_rate"] * statistics.mean(errors)
        for j in range(len(weights)):
            gradient = sum(error * row[j] for error, row in zip(errors, z)) / len(z)
            weights[j] -= MODEL_CONFIG["learning_rate"] * (gradient + MODEL_CONFIG["l2"] * weights[j])
    predictions = [
        max(1, math.expm1(intercept + sum(weight * value for weight, value in zip(weights, row))))
        for row in test_z
    ]
    # Standardized absolute coefficients are comparable across the mixed feature units.
    return predictions, [abs(weight) for weight in weights]


def score(actual, predicted):
    mae = sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)
    rmse = math.sqrt(sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual))
    mean = statistics.mean(actual)
    ss = sum((a - mean) ** 2 for a in actual)
    return {
        "mae_seconds": round(mae, 3),
        "rmse_seconds": round(rmse, 3),
        "r2": round(1 - sum((a - p) ** 2 for a, p in zip(actual, predicted)) / ss, 4) if ss else 0,
    }


def hour_median_predictions(train_records: list[dict], test_records: list[dict], fallback: float) -> list[float]:
    by_hour = {}
    for record in train_records:
        hour = record["timestamp"].hour
        by_hour.setdefault(hour, []).append(record["target"])
    medians = {hour: statistics.median(values) for hour, values in by_hour.items()}
    return [medians.get(record["timestamp"].hour, fallback) for record in test_records]


def temporal_folds(records: list[dict], count: int = 3):
    """Return expanding chronological folds ending at the final holdout boundary."""
    ordered = sorted(records, key=lambda record: (record["timestamp"], str(record["id"])))
    groups = []
    for record in ordered:
        if not groups or groups[-1][0]["timestamp"] != record["timestamp"]:
            groups.append([record])
        else:
            groups[-1].append(record)
    group_offsets = [sum(len(group) for group in groups[:index]) for index in range(1, len(groups))]
    boundaries = [min(group_offsets, key=lambda offset: abs(offset - len(ordered) * fraction)) for fraction in (0.5, 0.65, 0.8)]
    folds = []
    selected = boundaries[-count:]
    for index, train_end in enumerate(selected):
        test_end = selected[index + 1] if index + 1 < len(selected) else len(ordered)
        if test_end <= train_end:
            continue
        train, test = ordered[:train_end], ordered[train_end:test_end]
        train, _, _, _ = apply_duration_policy(train, test, trim_test=False)
        if train and test:
            folds.append((train, test))
    return folds


def evaluate_fold(train, test):
    train_x = [record["features"] for record in train]
    train_y = [record["target"] for record in train]
    test_x = [record["features"] for record in test]
    test_y = [record["target"] for record in test]
    global_median = statistics.median(train_y)
    recent = train_y[max(0, int(len(train_y) * 0.8)):]
    recent_median = statistics.median(recent)
    model_predictions, _ = fit_predict(train_x, train_y, test_x)
    hour_predictions = hour_median_predictions(train, test, global_median)
    predictions = {
        "global_median": [global_median] * len(test_y),
        "recent_median": [recent_median] * len(test_y),
        "hour_median": hour_predictions,
        "linear_log_target": model_predictions,
    }
    result = {name: score(test_y, values) for name, values in predictions.items()}
    upper = quantile(train_y, TRAIN_DURATION_QUANTILE)
    robust_indexes = [index for index, value in enumerate(test_y) if value <= upper]
    result["robust_inlier"] = {
        name: score([test_y[index] for index in robust_indexes], [values[index] for index in robust_indexes])
        for name, values in predictions.items()
    } if robust_indexes else {}
    result["test_rows"] = len(test_y)
    result["robust_test_rows"] = len(robust_indexes)
    result["train_rows"] = len(train)
    return result


def svg_hist(values, path):
    lo, hi = min(values), max(values)
    bins = [0] * 30
    for value in values:
        bins[min(29, int((value - lo) / (hi - lo + 1e-9) * 30))] += 1
    peak = max(bins) or 1
    bars = "".join(
        f'<rect x="{20 + i * 15}" y="{180 - count / peak * 150:.1f}" width="12" height="{count / peak * 150:.1f}" fill="#2c7fb8"/>'
        for i, count in enumerate(bins)
    )
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="500" height="220"><text x="20" y="15">Trip duration distribution</text>{bars}<line x1="20" y1="180" x2="470" y2="180" stroke="black"/></svg>')


def svg_scatter(actual, predicted, path):
    high = max(max(actual), max(predicted))
    points = "".join(
        f'<circle cx="{20 + 440 * actual_value / high:.1f}" cy="{200 - 180 * predicted_value / high:.1f}" r="1.5" fill="#2c7fb8" opacity=".35"/>'
        for actual_value, predicted_value in zip(actual, predicted)
    )
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="500" height="220"><text x="20" y="15">Predicted vs actual duration</text><line x1="20" y1="200" x2="460" y2="20" stroke="red" stroke-dasharray="4"/>{points}</svg>')


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_experiment(input_path: str | None = None, sample_size: int = DEFAULT_SAMPLE_SIZE, output_dir: Path = OUT):
    if input_path:
        rows = read_csv(input_path)
        source = f"csv:{Path(input_path).resolve()}"
        source_hash = file_sha256(input_path)
        requested_sample_size = None
    else:
        if sample_size < 2:
            raise ValueError("--sample-size must be at least 2")
        rows = make_sample(sample_size)
        source = "deterministic synthetic NYC-like fallback"
        source_hash = None
        requested_sample_size = sample_size

    records, audit = featurize(rows, return_audit=True)
    train_structural, test_structural = split_records(records)
    train, test, duration_upper, target_drops = apply_duration_policy(
        train_structural, test_structural, trim_test=False
    )
    robust_test = [record for record in test if record["target"] <= duration_upper]
    drop_rate = 1 - len(records) / len(rows) if rows else 1
    if drop_rate > MAX_DROP_RATE:
        raise ValueError(f"Cleaning dropped {drop_rate:.1%} of input rows, above the {MAX_DROP_RATE:.1%} limit")
    if len(train) < 2 or not test:
        raise ValueError("Duration cleaning left too few rows for evaluation")
    train_timestamp = train_structural[-1]["timestamp"]
    test_timestamp = test_structural[0]["timestamp"]
    if train_timestamp >= test_timestamp:
        raise AssertionError("Chronological split invariant violated after structural cleaning")

    train_x = [record["features"] for record in train]
    train_y = [record["target"] for record in train]
    test_x = [record["features"] for record in test]
    test_y = [record["target"] for record in test]
    model_predictions, importance = fit_predict(train_x, train_y, test_x)
    global_median = statistics.median(train_y)
    recent_median = statistics.median(train_y[max(0, int(len(train_y) * 0.8)):])
    hour_predictions = hour_median_predictions(train, test, global_median)
    robust_indexes = {id(record) for record in robust_test}

    output_dir.mkdir(exist_ok=True)
    predictions_path = output_dir / "predictions.csv"
    with open(predictions_path, "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            "pickup_datetime", "actual_seconds", "predicted_seconds", "global_median_seconds",
            "recent_median_seconds", "hour_median_seconds", "distance_miles", "hour", "weekday",
            "is_weekend", "absolute_error_seconds", "residual_seconds", "robust_inlier",
        ])
        writer.writerows([
            [
                record["timestamp"].isoformat(sep=" "), actual, predicted, global_median, recent_median,
                hour_prediction, record["features"][11], record["timestamp"].hour,
                record["timestamp"].weekday(), int(record["timestamp"].weekday() >= 5),
                abs(actual - predicted), predicted - actual, int(id(record) in robust_indexes),
            ]
            for record, actual, predicted, hour_prediction in zip(test, test_y, model_predictions, hour_predictions)
        ])

    with open(output_dir / "feature_importance.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["feature", "standardized_abs_coefficient"])
        writer.writerows(sorted(zip(FEATURE_NAMES, importance), key=lambda item: item[1], reverse=True))

    folds = []
    for fold_number, (fold_train, fold_test) in enumerate(temporal_folds(records), start=1):
        result = evaluate_fold(fold_train, fold_test)
        result["fold"] = fold_number
        result["split_cutoff"] = {
            "train_max_pickup_datetime": fold_train[-1]["timestamp"].isoformat(sep=" "),
            "test_min_pickup_datetime": fold_test[0]["timestamp"].isoformat(sep=" "),
        }
        folds.append(result)

    fold_summary = {}
    for method in ("global_median", "recent_median", "hour_median", "linear_log_target"):
        values = [fold[method]["mae_seconds"] for fold in folds]
        fold_summary[method] = {
            "mean_mae_seconds": round(statistics.mean(values), 3),
            "stdev_mae_seconds": round(statistics.pstdev(values), 3),
            "min_mae_seconds": min(values),
            "max_mae_seconds": max(values),
        }

    metrics = {
        "run_timestamp_utc": datetime.now(UTC).isoformat(),
        "source": source,
        "source_sha256": source_hash,
        "input_rows": audit["input_rows"],
        "rows_after_structural_cleaning": audit["rows_after_structural_cleaning"],
        "rows_after_cleaning": len(records),
        "drop_rate": round(drop_rate, 6),
        "dropped_by_reason": audit["dropped_by_reason"],
        "target_policy": {
            "quantile": TRAIN_DURATION_QUANTILE,
            "upper_bound_seconds": round(duration_upper, 3),
            "train_rows_before_trim": len(train_structural),
            "train_rows_used_for_fit": len(train),
            "train_duration_outlier_rows": target_drops["train_duration_outlier"],
            "test_duration_outlier_rows": target_drops["test_duration_outlier"],
            "primary_test_rows_scored": len(test),
            "robust_inlier_test_rows_scored": len(robust_test),
            "robust_inlier_exclusion_is_sensitivity_only": True,
        },
        "duration_upper_bound_seconds": round(duration_upper, 3),
        "duration_quantile": TRAIN_DURATION_QUANTILE,
        "train_rows": len(train),
        "test_rows": len(test),
        "test_rows_robust_inlier": len(robust_test),
        "split_cutoff": {
            "train_max_pickup_datetime": train_timestamp.isoformat(sep=" "),
            "test_min_pickup_datetime": test_timestamp.isoformat(sep=" "),
        },
        "observed_timestamp_range": {
            "min_pickup_datetime": records[0]["timestamp"].isoformat(sep=" "),
            "max_pickup_datetime": records[-1]["timestamp"].isoformat(sep=" "),
        },
        "baseline_median_seconds": global_median,
        "baseline": score(test_y, [global_median] * len(test_y)),
        "recent_median_baseline": score(test_y, [recent_median] * len(test_y)),
        "hour_median_baseline": score(test_y, hour_predictions),
        "linear_log_target": score(test_y, model_predictions),
        "robust_inlier_sensitivity": {
            "baseline": score([record["target"] for record in robust_test], [global_median] * len(robust_test)),
            "recent_median_baseline": score([record["target"] for record in robust_test], [recent_median] * len(robust_test)),
            "hour_median_baseline": score(
                [record["target"] for record in robust_test],
                [hour_predictions[index] for index, record in enumerate(test) if id(record) in robust_indexes],
            ),
            "linear_log_target": score(
                [record["target"] for record in robust_test],
                [prediction for record, prediction in zip(test, model_predictions) if id(record) in robust_indexes],
            ),
            "test_rows": len(robust_test),
        },
        "temporal_validation": {"folds": folds, "fold_summary": fold_summary},
        "run_config": {
            "seed": None if input_path else SEED,
            "sample_size": requested_sample_size,
            "features": FEATURE_NAMES,
            "model": MODEL_CONFIG,
            "cleaning": {
                "coordinate_ranges": "latitude [-90, 90], longitude [-180, 180]",
                "service_area": SERVICE_AREA,
                "passenger_count_range": "integer [1, 10]",
                "allowed_vendor_ids": sorted(ALLOWED_VENDOR_IDS),
                "maximum_route_distance_miles": 100,
                "duration": "positive values; upper bound is fit on training only and used for sensitivity scoring",
                "duplicate_handling": "duplicate non-empty ids are dropped after the first occurrence",
                "timestamp_coverage": TIMESTAMP_COVERAGE,
                "maximum_allowed_drop_rate": MAX_DROP_RATE,
            },
            "timestamp_policy": {
                "naive_input_timezone": INPUT_TIMEZONE,
                "aware_input_normalization": "UTC",
                "mixed_awareness": "rejected",
                "ambiguous_local_times": "rejected",
                "split_tie_handling": "pickup timestamp groups stay wholly in train or test",
                "strict_forward_invariant": "train_max_pickup_datetime < test_min_pickup_datetime",
            },
            "python_version": platform.python_version(),
            "platform": sys.platform,
        },
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    svg_hist([record["target"] for record in records], output_dir / "duration_distribution.svg")
    svg_scatter(test_y, model_predictions, output_dir / "predicted_vs_actual.svg")
    print(json.dumps(metrics, indent=2))
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--sample-size", type=int, default=None, help="fallback rows; not applicable with --input")
    args = parser.parse_args()
    if args.input and args.sample_size is not None:
        parser.error("--sample-size applies only to the synthetic fallback; omit it with --input")
    run_experiment(args.input, args.sample_size or DEFAULT_SAMPLE_SIZE)


if __name__ == "__main__":
    main()
