from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES = [
    "pickup_hour",
    "weekday",
    "is_rush_hour",
    "passenger_count",
    "distance_miles",
    "pickup_zone",
    "dropoff_zone",
]
NUMERIC = ["pickup_hour", "weekday", "is_rush_hour", "passenger_count", "distance_miles"]
CATEGORICAL = ["pickup_zone", "dropoff_zone"]
REQUIRED_COLUMNS = [
    "trip_id",
    "pickup_datetime",
    "passenger_count",
    "distance_miles",
    "pickup_zone",
    "dropoff_zone",
    "trip_duration_minutes",
]

TARGET_POLICY = {
    "field": "trip_duration_minutes",
    "missing": "exclude",
    "non_numeric": "exclude",
    "non_finite": "exclude",
    "non_positive": "exclude",
    "maximum_minutes": 180.0,
    "above_maximum": "exclude",
}
DISTANCE_MAX_MILES = 100.0
PASSENGER_MIN = 1
PASSENGER_MAX = 6
ZONE_MIN = 1
ZONE_MAX = 7
DUPLICATE_POLICY = "keep_first_exclude_later_rows"

FEATURE_POLICIES = {
    "pickup_datetime": {"invalid": "fail_before_modeling_or_inference"},
    "passenger_count": {
        "missing": "impute_in_train_pipeline",
        "invalid": "coerce_to_missing_and_impute",
        "range": [PASSENGER_MIN, PASSENGER_MAX],
        "integer_only": True,
    },
    "distance_miles": {
        "missing": "impute_in_train_pipeline",
        "invalid": "coerce_to_missing_and_impute",
        "range": [0, DISTANCE_MAX_MILES],
    },
    "pickup_zone": {
        "missing": "impute_in_train_pipeline",
        "invalid": "reject_before_inference",
        "range": [ZONE_MIN, ZONE_MAX],
        "integer_only": True,
    },
    "dropoff_zone": {
        "missing": "impute_in_train_pipeline",
        "invalid": "reject_before_inference",
        "range": [ZONE_MIN, ZONE_MAX],
        "integer_only": True,
    },
}

AUDIT_LABELS = {
    "missing_required_column": "Missing required columns",
    "missing_trip_id": "Missing values · trip ID",
    "missing_pickup_datetime": "Missing values · pickup time",
    "missing_passenger_count": "Missing values · passengers",
    "missing_distance_miles": "Missing values · distance",
    "missing_pickup_zone": "Missing values · pickup zone",
    "missing_dropoff_zone": "Missing values · dropoff zone",
    "missing_trip_duration_minutes": "Missing values · target",
    "invalid_pickup_datetime": "Invalid pickup timestamps",
    "duplicate_trip_id": "Duplicate trip IDs",
    "invalid_passenger_count": "Invalid passenger counts",
    "invalid_distance_non_numeric": "Non-numeric distances",
    "invalid_distance_non_finite": "Non-finite distances",
    "invalid_distance_non_positive": "Non-positive distances",
    "invalid_distance_above_maximum": "Implausible distances",
    "target_non_numeric": "Non-numeric targets",
    "target_non_finite": "Non-finite targets",
    "target_non_positive": "Non-positive targets",
    "target_above_maximum": "Targets above policy maximum",
    "iqr_outlier_passenger_count": "IQR passenger outliers",
    "iqr_outlier_distance_miles": "IQR distance outliers",
    "iqr_outlier_trip_duration_minutes": "IQR duration outliers",
}


def make_sample_data(rows: int = 1200, seed: int = 255) -> pd.DataFrame:
    if rows < 40:
        raise ValueError("rows must be at least 40")
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2024-01-01")
    pickup = start + pd.to_timedelta(rng.integers(0, 60 * 24 * 60, rows), unit="m")
    distance = np.clip(rng.gamma(2.2, 1.7, rows), 0.4, 18.0)
    hour = pickup.hour
    rush = (((hour >= 7) & (hour <= 9)) | ((hour >= 16) & (hour <= 19))).astype(int)
    passengers = rng.choice([1, 2, 3, 4, 5], rows, p=[.55, .25, .12, .06, .02])
    pickup_zone = rng.integers(1, 8, rows)
    dropoff_zone = rng.integers(1, 8, rows)
    traffic = rush * rng.normal(7, 2, rows) + (pickup.dayofweek >= 5) * rng.normal(-1, 1, rows)
    duration = np.clip(5.5 + 3.9 * distance + traffic + rng.normal(0, 3.0, rows), 2, 110)
    data = pd.DataFrame(
        {
            "trip_id": np.arange(1, rows + 1),
            "pickup_datetime": pickup,
            "passenger_count": passengers,
            "distance_miles": distance.round(3),
            "pickup_zone": pickup_zone,
            "dropoff_zone": dropoff_zone,
            "trip_duration_minutes": duration.round(2),
        }
    )
    # Deterministic quality issues exercise the audit and explicit target policy.
    data.loc[data.index[::173], "distance_miles"] = np.nan
    data.loc[data.index[::211], "trip_duration_minutes"] = -3.0
    return data


def _row_value(data: pd.DataFrame, position: int, column: str):
    if column not in data:
        return None
    value = data.iloc[position][column]
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value


def _numeric(data: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(data[column], errors="coerce")
    return values.where(np.isfinite(values))


def _coerced(data: pd.DataFrame, column: str) -> pd.Series:
    """Return numeric values before the finite-value check used by modeling."""
    return pd.to_numeric(data[column], errors="coerce")


def _add_findings(
    findings: list[dict],
    data: pd.DataFrame,
    mask: pd.Series | np.ndarray,
    category: str,
    field: str | None,
    severity: str,
    action: str,
    status: str,
) -> None:
    positions = np.flatnonzero(np.asarray(mask, dtype=bool))
    for position in positions:
        findings.append(
            {
                "finding_id": f"{category}:{position}",
                "category": category,
                "field": field,
                "row_index": int(position),
                "trip_id": _row_value(data, position, "trip_id"),
                "severity": severity,
                "action": action,
                "status": status,
            }
        )


def _iqr_mask(values: pd.Series) -> np.ndarray:
    finite = values.notna() & np.isfinite(values)
    if not finite.any():
        return np.zeros(len(values), dtype=bool)
    q1, q3 = values[finite].quantile([.25, .75])
    iqr = q3 - q1
    if not iqr:
        return np.zeros(len(values), dtype=bool)
    return (finite & ((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr))).to_numpy()


def audit_data(data: pd.DataFrame) -> dict:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    findings: list[dict] = []

    for column in missing_columns:
        findings.append(
            {
                "finding_id": f"missing_required_column:{column}",
                "category": "missing_required_column",
                "field": column,
                "row_index": None,
                "trip_id": None,
                "severity": "critical",
                "action": "fail_before_modeling",
                "status": "blocking",
            }
        )

    for column in REQUIRED_COLUMNS:
        if column in data:
            if column == "trip_id":
                severity, action, status = "critical", "fail_before_modeling", "blocking"
            elif column == "pickup_datetime":
                severity, action, status = "critical", "fail_before_modeling", "blocking"
            elif column in ("passenger_count", "distance_miles", "pickup_zone", "dropoff_zone"):
                severity, action, status = "warning", "impute_in_train_pipeline", "retained"
            else:
                severity, action, status = "critical", "exclude_from_model", "excluded"
            _add_findings(
                findings,
                data,
                data[column].isna(),
                f"missing_{column}",
                column,
                severity,
                action,
                status,
            )

    datetime_values = (
        pd.to_datetime(data["pickup_datetime"], errors="coerce")
        if "pickup_datetime" in data
        else pd.Series(dtype="datetime64[ns]")
    )
    if "pickup_datetime" in data:
        invalid_datetime = data["pickup_datetime"].notna() & datetime_values.isna()
        _add_findings(
            findings,
            data,
            invalid_datetime,
            "invalid_pickup_datetime",
            "pickup_datetime",
            "critical",
            "fail_before_modeling",
            "blocking",
        )

    if "trip_id" in data:
        duplicate_mask = data["trip_id"].duplicated(keep="first")
        _add_findings(
            findings,
            data,
            duplicate_mask,
            "duplicate_trip_id",
            "trip_id",
            "warning",
            "exclude_duplicate_keep_first",
            "excluded",
        )

    target_quality = {
        "policy": TARGET_POLICY,
        "missing_count": 0,
        "non_numeric_count": 0,
        "non_finite_count": 0,
        "non_positive_count": 0,
        "above_maximum_count": 0,
        "invalid_count": 0,
        "excluded_trip_ids": [],
    }
    invalid_target_mask = pd.Series(False, index=data.index)
    if "trip_duration_minutes" in data:
        raw_target = data["trip_duration_minutes"]
        target = _numeric(data, "trip_duration_minutes")
        missing = raw_target.isna()
        coerced_target = _coerced(data, "trip_duration_minutes")
        non_numeric = coerced_target.isna() & raw_target.notna()
        non_finite = coerced_target.map(lambda value: bool(np.isinf(value)) if pd.notna(value) else False)
        non_positive = target.notna() & (target <= 0)
        above_maximum = target.notna() & (target > TARGET_POLICY["maximum_minutes"])
        invalid_target = missing | non_numeric | non_finite | non_positive | above_maximum
        invalid_target_mask = invalid_target
        _add_findings(findings, data, non_numeric, "target_non_numeric", "trip_duration_minutes", "critical", "exclude_from_model", "excluded")
        _add_findings(findings, data, non_finite, "target_non_finite", "trip_duration_minutes", "critical", "exclude_from_model", "excluded")
        _add_findings(findings, data, non_positive, "target_non_positive", "trip_duration_minutes", "critical", "exclude_from_model", "excluded")
        _add_findings(findings, data, above_maximum, "target_above_maximum", "trip_duration_minutes", "critical", "exclude_from_model", "excluded")
        target_quality.update(
            {
                "missing_count": int(missing.sum()),
                "non_numeric_count": int(non_numeric.sum()),
                "non_finite_count": int(non_finite.sum()),
                "non_positive_count": int(non_positive.sum()),
                "above_maximum_count": int(above_maximum.sum()),
                "invalid_count": int(invalid_target.sum()),
                "excluded_trip_ids": [
                    _row_value(data, position, "trip_id")
                    for position in np.flatnonzero(invalid_target.to_numpy())
                ],
            }
        )

    distance_quality = {"missing_count": 0, "non_numeric_count": 0, "non_finite_count": 0, "non_positive_count": 0, "above_maximum_count": 0}
    if "distance_miles" in data:
        raw_distance = data["distance_miles"]
        distance = _numeric(data, "distance_miles")
        missing = raw_distance.isna()
        coerced_distance = _coerced(data, "distance_miles")
        non_numeric = coerced_distance.isna() & raw_distance.notna()
        non_finite = coerced_distance.map(lambda value: bool(np.isinf(value)) if pd.notna(value) else False)
        non_positive = distance.notna() & (distance <= 0)
        above_maximum = distance.notna() & (distance > DISTANCE_MAX_MILES)
        _add_findings(findings, data, non_numeric, "invalid_distance_non_numeric", "distance_miles", "warning", "coerce_to_missing_and_impute", "retained")
        _add_findings(findings, data, non_finite, "invalid_distance_non_finite", "distance_miles", "warning", "coerce_to_missing_and_impute", "retained")
        _add_findings(findings, data, non_positive, "invalid_distance_non_positive", "distance_miles", "warning", "coerce_to_missing_and_impute", "retained")
        _add_findings(findings, data, above_maximum, "invalid_distance_above_maximum", "distance_miles", "warning", "coerce_to_missing_and_impute", "retained")
        distance_quality = {
            "missing_count": int(missing.sum()),
            "non_numeric_count": int(non_numeric.sum()),
            "non_finite_count": int(non_finite.sum()),
            "non_positive_count": int(non_positive.sum()),
            "above_maximum_count": int(above_maximum.sum()),
        }

    if "passenger_count" in data:
        raw_passengers = data["passenger_count"]
        passengers = _numeric(data, "passenger_count")
        invalid_passengers = (
            (passengers.isna() & raw_passengers.notna())
            | (passengers.notna() & ((passengers < PASSENGER_MIN) | (passengers > PASSENGER_MAX)))
            | (passengers.notna() & (passengers % 1 != 0))
        )
        _add_findings(findings, data, invalid_passengers, "invalid_passenger_count", "passenger_count", "warning", "coerce_to_missing_and_impute", "retained")

    for column in ("passenger_count", "distance_miles", "trip_duration_minutes"):
        if column not in data:
            continue
        outlier_mask = _iqr_mask(_numeric(data, column))
        if column == "trip_duration_minutes":
            _add_findings(findings, data, outlier_mask & invalid_target_mask.to_numpy(), f"iqr_outlier_{column}", column, "info", "exclude_from_model", "excluded")
            _add_findings(findings, data, outlier_mask & ~invalid_target_mask.to_numpy(), f"iqr_outlier_{column}", column, "info", "review_domain_validity", "retained")
        else:
            _add_findings(findings, data, outlier_mask, f"iqr_outlier_{column}", column, "info", "review_domain_validity", "retained")

    category_counts = []
    for category, label in AUDIT_LABELS.items():
        category_counts.append(
            {
                "category": category,
                "label": label,
                "count": sum(finding["category"] == category for finding in findings),
            }
        )
    invalid_distance_count = sum(
        distance_quality[key]
        for key in ("non_numeric_count", "non_finite_count", "non_positive_count", "above_maximum_count")
    )
    invalid_datetime_count = sum(finding["category"] == "invalid_pickup_datetime" for finding in findings)
    return {
        "rows": int(len(data)),
        "columns": list(data.columns),
        "missing_columns": missing_columns,
        "null_counts": {key: int(value) for key, value in data.isna().sum().items()},
        "duplicate_trip_ids": int(data["trip_id"].duplicated().sum()) if "trip_id" in data else None,
        "invalid_duration_count": target_quality["invalid_count"],
        "non_positive_duration_count": target_quality["non_positive_count"],
        "invalid_distance_count": int(invalid_distance_count),
        "distance_quality": distance_quality,
        "target_quality": target_quality,
        "invalid_pickup_datetime_count": int(invalid_datetime_count),
        "iqr_outlier_counts": {
            column: sum(finding["category"] == f"iqr_outlier_{column}" for finding in findings)
            for column in ("passenger_count", "distance_miles", "trip_duration_minutes")
        },
        "finding_counts": category_counts,
        "findings": findings,
        "feature_policies": FEATURE_POLICIES,
        "duplicate_policy": DUPLICATE_POLICY,
        "blocking_finding_count": sum(finding["status"] == "blocking" for finding in findings),
    }


def _features(data: pd.DataFrame) -> pd.DataFrame:
    frame = data.copy()
    frame["pickup_datetime"] = pd.to_datetime(frame["pickup_datetime"], errors="coerce")
    frame["pickup_hour"] = frame.pickup_datetime.dt.hour
    frame["weekday"] = frame.pickup_datetime.dt.dayofweek
    frame["is_rush_hour"] = frame.pickup_hour.isin([7, 8, 9, 16, 17, 18, 19]).astype(int)
    for col in NUMERIC:
        values = pd.to_numeric(frame[col], errors="coerce")
        values = values.where(np.isfinite(values))
        if col == "distance_miles":
            values = values.where((values > 0) & (values <= DISTANCE_MAX_MILES))
        if col == "passenger_count":
            values = values.where((values >= PASSENGER_MIN) & (values <= PASSENGER_MAX) & (values % 1 == 0))
        frame[col] = values
    return frame


def _valid_target_mask(data: pd.DataFrame) -> pd.Series:
    """Apply the exact target policy used by audit, training, and reports."""
    if "trip_duration_minutes" not in data:
        return pd.Series(False, index=data.index)
    target = _numeric(data, "trip_duration_minutes")
    return target.notna() & (target > 0) & (target <= TARGET_POLICY["maximum_minutes"])


def _metric_summary(actual: pd.Series, prediction: np.ndarray) -> dict:
    score = r2_score(actual, prediction) if len(actual) > 1 else None
    return {
        "rows": int(len(actual)),
        "mae_minutes": round(float(mean_absolute_error(actual, prediction)), 3),
        "rmse_minutes": round(float(np.sqrt(mean_squared_error(actual, prediction))), 3),
        "r2": None if score is None or not np.isfinite(score) else round(float(score), 3),
        "within_5_minutes_rate": round(float(np.mean(np.abs(actual.to_numpy() - prediction) <= 5)), 3),
    }


def _slice_metrics(test: pd.DataFrame, prediction: np.ndarray) -> list[dict]:
    frame = test.copy()
    frame["prediction"] = prediction
    frame["abs_error"] = (frame["trip_duration_minutes"] - frame["prediction"]).abs()
    frame["duration_band"] = pd.cut(
        frame["trip_duration_minutes"],
        bins=[-np.inf, 10, 20, 40, np.inf],
        labels=["under_10", "10_to_20", "20_to_40", "over_40"],
        right=False,
    ).astype(str)
    frame["route"] = frame["pickup_zone"].astype(str) + " → " + frame["dropoff_zone"].astype(str)
    frame["missing_feature"] = frame[["passenger_count", "distance_miles"]].isna().any(axis=1)
    dimensions = {
        "pickup_hour": frame["pickup_datetime"].dt.hour.astype(str),
        "weekday": frame["pickup_datetime"].dt.dayofweek.astype(str),
        "duration_band": frame["duration_band"],
        "route": frame["route"],
        "missing_feature": frame["missing_feature"].map({True: "yes", False: "no"}),
    }
    slices = []
    actual = frame["trip_duration_minutes"]
    for dimension, values in dimensions.items():
        for value in sorted(values.dropna().unique()):
            mask = values == value
            summary = _metric_summary(actual[mask], frame.loc[mask, "prediction"].to_numpy())
            slices.append({"dimension": dimension, "value": value, **summary})
    return slices


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _model() -> Pipeline:
    numeric_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median", add_indicator=True))])
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    prep = ColumnTransformer(
        [("num", numeric_pipeline, NUMERIC), ("cat", categorical_pipeline, CATEGORICAL)],
        sparse_threshold=0,
    )
    return Pipeline(
        [
            ("features", prep),
            (
                "regressor",
                HistGradientBoostingRegressor(
                    max_iter=120,
                    max_leaf_nodes=15,
                    learning_rate=.07,
                    random_state=255,
                ),
            ),
        ]
    )


def _git_revision() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else "unavailable"
    except OSError:
        return "unavailable"


def _package_versions() -> dict:
    packages = {"joblib": "joblib", "matplotlib": "matplotlib", "numpy": "numpy", "pandas": "pandas", "scikit-learn": "scikit-learn"}
    result = {}
    for label, package in packages.items():
        try:
            result[label] = version(package)
        except PackageNotFoundError:
            result[label] = "unavailable"
    return result


def _data_hash(data: pd.DataFrame) -> str:
    encoded = pd.util.hash_pandas_object(data, index=True).values.tobytes()
    return hashlib.sha256(encoded).hexdigest()


def run_pipeline(output: Path, rows: int = 1200, seed: int = 255, command: list[str] | None = None) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    raw = make_sample_data(rows, seed)
    audit = audit_data(raw)
    (output / "audit_report.json").write_text(json.dumps(audit, indent=2, default=str) + "\n")
    if audit["missing_columns"]:
        raise ValueError(f"Missing required columns: {', '.join(audit['missing_columns'])}")
    if audit["blocking_finding_count"]:
        raise ValueError("Blocking audit findings must be corrected before modeling")

    valid_target = _valid_target_mask(raw)
    valid_duplicate = ~raw["trip_id"].duplicated(keep="first")
    retained_mask = valid_target & valid_duplicate
    clean = raw.loc[retained_mask].copy()
    clean["pickup_datetime"] = pd.to_datetime(clean["pickup_datetime"], errors="coerce")
    clean["trip_duration_minutes"] = _numeric(clean, "trip_duration_minutes").to_numpy()
    # Canonicalize first, then sort, so mixed timestamp representations cannot
    # change the temporal boundary through lexicographic ordering.
    clean = clean.sort_values("pickup_datetime", kind="mergesort")
    prepared = _features(clean)
    split = int(len(prepared) * .8)
    if split <= 0 or split >= len(prepared):
        raise ValueError("target policy left too few rows for a chronological train/test split")
    train, test = prepared.iloc[:split], prepared.iloc[split:]
    model = _model()
    model.fit(train[FEATURES], train.trip_duration_minutes)
    prediction = model.predict(test[FEATURES])
    global_mean_prediction = np.full(len(test), train.trip_duration_minutes.mean())
    distance_baseline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("regressor", LinearRegression()),
        ]
    )
    distance_baseline.fit(train[["distance_miles"]], train.trip_duration_minutes)
    distance_prediction = distance_baseline.predict(test[["distance_miles"]])
    error_rows = []
    for position, (_, row) in enumerate(test.iterrows()):
        actual = float(row["trip_duration_minutes"])
        estimate = float(prediction[position])
        error_rows.append(
            {
                "trip_id": _row_value(test, position, "trip_id"),
                "row_index": int(row.name),
                "pickup_datetime": row["pickup_datetime"].isoformat(),
                "pickup_hour": int(row["pickup_datetime"].hour),
                "weekday": int(row["pickup_datetime"].dayofweek),
                "passenger_count": None if pd.isna(row["passenger_count"]) else int(row["passenger_count"]),
                "distance_miles": None if pd.isna(row["distance_miles"]) else float(row["distance_miles"]),
                "pickup_zone": _row_value(test, position, "pickup_zone"),
                "dropoff_zone": _row_value(test, position, "dropoff_zone"),
                "actual_minutes": round(actual, 3),
                "predicted_minutes": round(estimate, 3),
                "error_minutes": round(estimate - actual, 3),
                "absolute_error_minutes": round(abs(estimate - actual), 3),
                "missing_feature": bool(row[["passenger_count", "distance_miles"]].isna().any()),
            }
        )
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    data_hash = _data_hash(raw)
    run_id = hashlib.sha256(f"{data_hash}:{source_hash}:{rows}:{seed}".encode()).hexdigest()[:16]
    metrics = {
        "evaluation_type": "synthetic_smoke_test",
        "data_source": "deterministic in-memory NYC-like generator",
        "run_id": run_id,
        "raw_rows": int(len(raw)),
        "retained_rows": int(len(clean)),
        "excluded_target_rows": int((~valid_target).sum()),
        "excluded_duplicate_rows": int((valid_target & ~valid_duplicate).sum()),
        "excluded_rows": int((~retained_mask).sum()),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "test_fraction": round(float(len(test) / len(clean)), 4),
        "mae_minutes": round(float(mean_absolute_error(test.trip_duration_minutes, prediction)), 3),
        "rmse_minutes": round(float(np.sqrt(mean_squared_error(test.trip_duration_minutes, prediction))), 3),
        "r2": round(float(r2_score(test.trip_duration_minutes, prediction)), 3),
        "within_5_minutes_rate": round(float(np.mean(np.abs(test.trip_duration_minutes - prediction) <= 5)), 3),
        "split": "chronological 80/20; preprocessing fitted on training rows only",
        "time_ranges": {
            "train_start": train["pickup_datetime"].min().isoformat(),
            "train_end": train["pickup_datetime"].max().isoformat(),
            "holdout_start": test["pickup_datetime"].min().isoformat(),
            "holdout_end": test["pickup_datetime"].max().isoformat(),
        },
        "baselines": {
            "global_mean": _metric_summary(test.trip_duration_minutes, global_mean_prediction),
            "distance_only_linear": _metric_summary(test.trip_duration_minutes, distance_prediction),
        },
        "error_slices_artifact": "prediction_errors.json",
        "error_slices": _slice_metrics(test, prediction),
        "target_policy": TARGET_POLICY,
    }
    joblib.dump(model, output / "model.joblib")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    prediction_errors = {
        "run_id": run_id,
        "evaluation_type": "synthetic_smoke_test",
        "model": "HistGradientBoostingRegressor",
        "rows": error_rows,
        "slice_metrics": metrics["error_slices"],
    }
    (output / "prediction_errors.json").write_text(json.dumps(prediction_errors, indent=2) + "\n")
    plt.figure(figsize=(8, 4))
    plt.hist(clean.trip_duration_minutes, bins=30, color="#2673a8", alpha=.85)
    plt.xlabel("Trip duration (minutes)")
    plt.ylabel("Trips")
    plt.title("Synthetic sample duration distribution")
    plt.tight_layout()
    plt.savefig(output / "eda.png", dpi=130)
    plt.close()
    plt.figure(figsize=(5, 5))
    plt.scatter(test.trip_duration_minutes, prediction, s=12, alpha=.55)
    lim = [0, max(test.trip_duration_minutes.max(), prediction.max())]
    plt.plot(lim, lim, "k--")
    plt.xlabel("Actual minutes")
    plt.ylabel("Predicted minutes")
    plt.title("Synthetic temporal holdout predictions")
    plt.tight_layout()
    plt.savefig(output / "actual_vs_predicted.png", dpi=130)
    plt.close()

    manifest = {
        "manifest_version": 1,
        "command": command or ["run_pipeline", f"rows={rows}", f"seed={seed}"],
        "source": {
            "data_source": "synthetic",
            "description": "Deterministic NYC-like fixture; not downloaded TLC data",
            "data_hash_sha256": data_hash,
            "source_hash_sha256": source_hash,
            "git_revision": _git_revision(),
        },
        "runtime": {"python": sys.version.split()[0], "packages": _package_versions()},
        "configuration": {
            "rows_argument": rows,
            "seed": seed,
            "features": FEATURES,
            "numeric_features": NUMERIC,
            "categorical_features": CATEGORICAL,
            "model": {
                "type": "HistGradientBoostingRegressor",
                "max_iter": 120,
                "max_leaf_nodes": 15,
                "learning_rate": .07,
                "random_state": 255,
            },
            "split": "sort by pickup_datetime; first 80% train; final 20% holdout",
            "target_policy": TARGET_POLICY,
            "feature_policies": FEATURE_POLICIES,
            "duplicate_policy": DUPLICATE_POLICY,
            "distance_policy": {"maximum_miles": DISTANCE_MAX_MILES, "invalid_values": "coerce to missing and impute in fitted training pipeline"},
        },
        "population": {
            "raw_rows": int(len(raw)),
            "retained_rows": int(len(clean)),
            "excluded_target_rows": int((~valid_target).sum()),
            "excluded_duplicate_rows": int((valid_target & ~valid_duplicate).sum()),
            "excluded_rows": int((~retained_mask).sum()),
            "excluded_target_trip_ids": audit["target_quality"]["excluded_trip_ids"],
            "train_rows": int(len(train)),
            "holdout_rows": int(len(test)),
            "time_ranges": metrics["time_ranges"],
        },
        "run_id": run_id,
    }
    report = f"""# Synthetic CRISP-DM report

## Business understanding
Estimate taxi trip duration for an educational planning and audit demonstration. This project does not make dispatch, pricing, safety, or NYC traffic-performance claims.

## Data understanding and audit
Generated {len(raw):,} deterministic NYC-like trips in memory. This is a synthetic fixture, not a download of the NYC TLC corpus. The complete audit is saved in `audit_report.json` with row-level findings, severity, action, and status. It recorded {len(audit['findings']):,} findings across all audit categories.

## Target-quality policy
`trip_duration_minutes` must be numeric, finite, greater than 0, and at most {TARGET_POLICY['maximum_minutes']:.0f} minutes. Rows failing any rule are excluded before the chronological split. Raw, retained, and excluded populations plus excluded IDs are recorded in the audit and `run_manifest.json`.

## Data preparation
Pickup hour, weekday, and rush-hour indicators are derived before splitting. Invalid feature values are coerced to missing. Numeric medians and missingness indicators are fitted inside the model pipeline on training rows only, then applied unchanged to the holdout and inference rows.

## Modeling and evaluation
A CPU-safe histogram gradient-boosting regressor was trained on the first 80% chronologically; the final 20% was held out. These are synthetic smoke-test metrics, not evidence of generalization to real taxi trips. The holdout spans {metrics['time_ranges']['holdout_start']} through {metrics['time_ranges']['holdout_end']}.

- Retained rows: **{len(clean):,}** ({len(train):,} train / {len(test):,} holdout)
- MAE: **{metrics['mae_minutes']:.3f} minutes**
- RMSE: **{metrics['rmse_minutes']:.3f} minutes**
- R²: **{metrics['r2']:.3f}** (coefficient of determination, not accuracy)
- Within 5 minutes: **{metrics['within_5_minutes_rate']:.1%}** (application threshold, not generic accuracy)

The global-mean baseline scores MAE **{metrics['baselines']['global_mean']['mae_minutes']:.3f}** minutes and the distance-only linear baseline scores **{metrics['baselines']['distance_only_linear']['mae_minutes']:.3f}** minutes on the same holdout. These single-window baselines are calibration references, not proof of temporal generalization. Row-level model errors and slice metrics are saved in `prediction_errors.json`.

## Deployment and monitoring
`run_platform.py --infer` loads the saved model and uses the same serialized preprocessing pipeline. In production, validate licensed real TLC data, monitor missingness, drift, error slices, and prediction latency before considering operational use.

## Reproducibility
`run_manifest.json` records the run identity, command, seed, row argument, source/data hashes, git revision, Python and package versions, feature contract, model parameters, split rule, target policy, artifact hashes, and population/time-range counts.

## Limitations and deviations
The original prompt and licensed TLC data were unavailable. The generated data uses a deliberately simple mechanism, so the reported score measures recovery of this toy mechanism. The browser inference lab is a separate hand-written directional calculator; it is not the evaluated saved-model inference. Real-data ingestion, rolling-origin validation, uncertainty intervals, route geometry, weather, traffic feeds, privacy controls, and a hosted API remain future work.
"""
    (output / "crispdm_report.md").write_text(report)
    artifact_names = [
        "audit_report.json",
        "metrics.json",
        "model.joblib",
        "prediction_errors.json",
        "eda.png",
        "actual_vs_predicted.png",
        "crispdm_report.md",
    ]
    manifest["artifact_hashes_sha256"] = {name: _sha256_file(output / name) for name in artifact_names}
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    return {"metrics": metrics, "audit": audit, "manifest": manifest, "artifacts": sorted(p.name for p in output.iterdir())}


def _validate_inference_inputs(
    pickup_hour: int,
    weekday: int,
    distance_miles: float,
    passengers: int,
    pickup_zone: int,
    dropoff_zone: int,
) -> None:
    integer_inputs = {
        "pickup_hour": (pickup_hour, 0, 23),
        "weekday": (weekday, 0, 6),
        "passengers": (passengers, PASSENGER_MIN, PASSENGER_MAX),
        "pickup_zone": (pickup_zone, ZONE_MIN, ZONE_MAX),
        "dropoff_zone": (dropoff_zone, ZONE_MIN, ZONE_MAX),
    }
    for name, (value, lower, upper) in integer_inputs.items():
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not lower <= int(value) <= upper:
            raise ValueError(f"invalid inference input: {name} must be an integer in [{lower}, {upper}]")
    if isinstance(distance_miles, (bool, np.bool_)) or not isinstance(distance_miles, (int, float, np.integer, np.floating)):
        raise ValueError("invalid inference input: distance_miles must be numeric")
    if not np.isfinite(distance_miles) or not 0 < float(distance_miles) <= DISTANCE_MAX_MILES:
        raise ValueError(f"invalid inference input: distance_miles must be in (0, {DISTANCE_MAX_MILES}]")


def infer_duration(output: Path, pickup_hour: int, weekday: int, distance_miles: float, passengers: int, pickup_zone: int, dropoff_zone: int) -> dict:
    _validate_inference_inputs(pickup_hour, weekday, distance_miles, passengers, pickup_zone, dropoff_zone)
    model = joblib.load(output / "model.joblib")
    manifest_path = output / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    expected_model_hash = manifest.get("artifact_hashes_sha256", {}).get("model.joblib")
    actual_model_hash = _sha256_file(output / "model.joblib")
    if expected_model_hash and expected_model_hash != actual_model_hash:
        raise ValueError("model artifact hash does not match run manifest")
    row = pd.DataFrame(
        [
            {
                "pickup_hour": pickup_hour,
                "weekday": weekday,
                "is_rush_hour": int(pickup_hour in [7, 8, 9, 16, 17, 18, 19]),
                "passenger_count": passengers,
                "distance_miles": distance_miles,
                "pickup_zone": pickup_zone,
                "dropoff_zone": dropoff_zone,
            }
        ]
    )
    return {
        "predicted_duration_minutes": round(float(model.predict(row[FEATURES])[0]), 2),
        "inputs": row.iloc[0].to_dict(),
        "run_id": manifest.get("run_id"),
        "manifest_version": manifest.get("manifest_version"),
        "model_artifact_sha256": actual_model_hash,
    }
