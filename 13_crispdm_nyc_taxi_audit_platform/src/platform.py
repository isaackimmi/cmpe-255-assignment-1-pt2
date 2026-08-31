from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES = ["pickup_hour", "weekday", "is_rush_hour", "passenger_count", "distance_miles", "pickup_zone", "dropoff_zone"]
NUMERIC = ["pickup_hour", "weekday", "is_rush_hour", "passenger_count", "distance_miles"]
CATEGORICAL = ["pickup_zone", "dropoff_zone"]


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
    data = pd.DataFrame({"trip_id": np.arange(1, rows + 1), "pickup_datetime": pickup,
                         "passenger_count": passengers, "distance_miles": distance.round(3),
                         "pickup_zone": pickup_zone, "dropoff_zone": dropoff_zone,
                         "trip_duration_minutes": duration.round(2)})
    # A small, deterministic quality issue makes the audit meaningful; impute only feature values later.
    data.loc[data.index[::173], "distance_miles"] = np.nan
    data.loc[data.index[::211], "trip_duration_minutes"] = -3.0
    return data


def audit_data(data: pd.DataFrame) -> dict:
    required = ["trip_id", "pickup_datetime", "passenger_count", "distance_miles", "pickup_zone", "dropoff_zone", "trip_duration_minutes"]
    missing_columns = [c for c in required if c not in data.columns]
    numeric = [c for c in ["passenger_count", "distance_miles", "trip_duration_minutes"] if c in data]
    outliers = {}
    for col in numeric:
        values = pd.to_numeric(data[col], errors="coerce").dropna()
        q1, q3 = values.quantile([.25, .75])
        iqr = q3 - q1
        outliers[col] = int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum()) if iqr else 0
    return {"rows": int(len(data)), "columns": list(data.columns), "missing_columns": missing_columns,
            "null_counts": {k: int(v) for k, v in data.isna().sum().items()},
            "duplicate_trip_ids": int(data["trip_id"].duplicated().sum()) if "trip_id" in data else None,
            "invalid_duration_count": int((data["trip_duration_minutes"] <= 0).sum()) if "trip_duration_minutes" in data else None,
            "invalid_distance_count": int((data["distance_miles"] <= 0).sum()) if "distance_miles" in data else None,
            "iqr_outlier_counts": outliers}


def _features(data: pd.DataFrame) -> pd.DataFrame:
    frame = data.copy()
    frame["pickup_datetime"] = pd.to_datetime(frame["pickup_datetime"])
    frame["pickup_hour"] = frame.pickup_datetime.dt.hour
    frame["weekday"] = frame.pickup_datetime.dt.dayofweek
    frame["is_rush_hour"] = frame.pickup_hour.isin([7, 8, 9, 16, 17, 18, 19]).astype(int)
    for col in NUMERIC:
        frame[col] = frame[col].fillna(frame[col].median())
    return frame


def _model() -> Pipeline:
    prep = ColumnTransformer([("num", "passthrough", NUMERIC), ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
    return Pipeline([("features", prep), ("regressor", HistGradientBoostingRegressor(max_iter=120, max_leaf_nodes=15, learning_rate=.07, random_state=255))])


def run_pipeline(output: Path, rows: int = 1200, seed: int = 255) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    raw = make_sample_data(rows, seed)
    audit = audit_data(raw)
    clean = raw[raw.trip_duration_minutes > 0].copy().sort_values("pickup_datetime")
    prepared = _features(clean)
    split = int(len(prepared) * .8)
    train, test = prepared.iloc[:split], prepared.iloc[split:]
    model = _model()
    model.fit(train[FEATURES], train.trip_duration_minutes)
    prediction = model.predict(test[FEATURES])
    metrics = {"train_rows": len(train), "test_rows": len(test), "mae_minutes": round(float(mean_absolute_error(test.trip_duration_minutes, prediction)), 3),
               "rmse_minutes": round(float(np.sqrt(mean_squared_error(test.trip_duration_minutes, prediction))), 3),
               "r2": round(float(r2_score(test.trip_duration_minutes, prediction)), 3),
               "within_5_minutes_rate": round(float(np.mean(np.abs(test.trip_duration_minutes - prediction) <= 5)), 3), "split": "chronological 80/20"}
    joblib.dump(model, output / "model.joblib")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (output / "audit_report.json").write_text(json.dumps(audit, indent=2) + "\n")
    plt.figure(figsize=(8, 4)); plt.hist(clean.trip_duration_minutes, bins=30, color="#2673a8", alpha=.85); plt.xlabel("Trip duration (minutes)"); plt.ylabel("Trips"); plt.title("Sample duration distribution"); plt.tight_layout(); plt.savefig(output / "eda.png", dpi=130); plt.close()
    plt.figure(figsize=(5, 5)); plt.scatter(test.trip_duration_minutes, prediction, s=12, alpha=.55); lim=[0, max(test.trip_duration_minutes.max(), prediction.max())]; plt.plot(lim, lim, "k--"); plt.xlabel("Actual minutes"); plt.ylabel("Predicted minutes"); plt.title("Temporal holdout predictions"); plt.tight_layout(); plt.savefig(output / "actual_vs_predicted.png", dpi=130); plt.close()
    report = f"""# CRISP-DM report\n\n## Business understanding\nEstimate taxi trip duration to support planning and dispatch analysis.\n\n## Data understanding and audit\nGenerated {len(raw):,} deterministic NYC-like trips. The audit found {audit['null_counts']['distance_miles']} missing distances and {audit['invalid_duration_count']} non-positive durations; invalid target rows were excluded and numeric feature gaps were median-imputed.\n\n## Data preparation\nDerived pickup hour, weekday, and rush-hour indicator. Used distance, passenger count, pickup/dropoff zones, and temporal features.\n\n## Modeling\nA CPU-safe histogram gradient-boosting regressor was trained on the first 80% chronologically; the final 20% was held out.\n\n## Evaluation\n- MAE: **{metrics['mae_minutes']:.3f} minutes**\n- RMSE: **{metrics['rmse_minutes']:.3f} minutes**\n- R²: **{metrics['r2']:.3f}**\n- Within 5 minutes: **{metrics['within_5_minutes_rate']:.1%}**\n\n## Deployment and monitoring\n`run_platform.py --infer` loads the saved model. In production, monitor missingness, duration drift, error by zone/time, and prediction latency.\n\n## Limitations and deviations\nThis is a sample-data reproduction because the original prompt file and TLC data were unavailable. It omits coordinates, weather, fares, traffic feeds, privacy controls, model comparison, and a hosted API. Metrics are illustrative only.\n"""
    (output / "crispdm_report.md").write_text(report)
    return {"metrics": metrics, "audit": audit, "artifacts": sorted(p.name for p in output.iterdir())}


def infer_duration(output: Path, pickup_hour: int, weekday: int, distance_miles: float, passengers: int, pickup_zone: int, dropoff_zone: int) -> dict:
    if not 0 <= pickup_hour <= 23 or not 0 <= weekday <= 6 or distance_miles <= 0 or passengers < 1:
        raise ValueError("invalid inference input")
    model = joblib.load(output / "model.joblib")
    row = pd.DataFrame([{ "pickup_hour": pickup_hour, "weekday": weekday, "is_rush_hour": int(pickup_hour in [7,8,9,16,17,18,19]), "passenger_count": passengers, "distance_miles": distance_miles, "pickup_zone": pickup_zone, "dropoff_zone": dropoff_zone }])
    return {"predicted_duration_minutes": round(float(model.predict(row[FEATURES])[0]), 2), "inputs": row.iloc[0].to_dict()}
