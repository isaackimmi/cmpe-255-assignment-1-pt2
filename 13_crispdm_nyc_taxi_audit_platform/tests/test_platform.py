import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.platform import (
    FEATURES,
    TARGET_POLICY,
    _features,
    _model,
    audit_data,
    infer_duration,
    make_sample_data,
    run_pipeline,
)


def test_sample_data_is_deterministic_and_auditable():
    first = make_sample_data(100, 7)
    second = make_sample_data(100, 7)
    assert first.equals(second)
    audit = audit_data(first)
    assert audit["rows"] == 100
    assert audit["null_counts"]["distance_miles"] > 0
    assert audit["invalid_duration_count"] > 0


def test_pipeline_writes_metrics_plots_and_report(tmp_path: Path):
    result = run_pipeline(tmp_path, rows=100, seed=2)
    metrics = json.loads((tmp_path / "metrics.json").read_text())
    manifest = json.loads((tmp_path / "run_manifest.json").read_text())
    assert metrics["test_rows"] > 0
    assert metrics["mae_minutes"] >= 0
    assert metrics["evaluation_type"] == "synthetic_smoke_test"
    assert metrics["retained_rows"] == metrics["train_rows"] + metrics["test_rows"]
    assert metrics["excluded_target_rows"] == 1
    assert metrics["target_policy"] == TARGET_POLICY
    assert manifest["configuration"]["seed"] == 2
    assert manifest["configuration"]["rows_argument"] == 100
    assert manifest["source"]["data_hash_sha256"]
    assert manifest["runtime"]["packages"]["scikit-learn"]
    assert {"eda.png", "actual_vs_predicted.png", "crispdm_report.md", "model.joblib", "run_manifest.json"}.issubset(result["artifacts"])


def test_inference_is_json_serializable(tmp_path: Path):
    run_pipeline(tmp_path, rows=100, seed=3)
    result = infer_duration(tmp_path, 17, 4, 3.2, 2, 1, 2)
    assert result["predicted_duration_minutes"] > 0
    assert result["run_id"]
    assert result["manifest_version"] == 1
    json.dumps(result)


def test_bad_inference_input_is_rejected(tmp_path: Path):
    run_pipeline(tmp_path, rows=100, seed=3)
    with pytest.raises(ValueError):
        infer_duration(tmp_path, 25, 4, 3.2, 2, 1, 2)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"distance_miles": 100.1},
        {"passengers": 7},
        {"passengers": 2.5},
        {"pickup_zone": 8},
        {"dropoff_zone": "2"},
    ],
)
def test_inference_enforces_training_feature_contract(tmp_path: Path, kwargs: dict):
    run_pipeline(tmp_path, rows=100, seed=3)
    inputs = {"pickup_hour": 17, "weekday": 4, "distance_miles": 3.2, "passengers": 2, "pickup_zone": 1, "dropoff_zone": 2}
    inputs.update(kwargs)
    with pytest.raises(ValueError, match="invalid inference input"):
        infer_duration(tmp_path, **inputs)


def test_audit_has_row_level_target_policy_and_all_categories():
    data = make_sample_data(60, 8)
    data["trip_duration_minutes"] = data["trip_duration_minutes"].astype(object)
    data.loc[0, "trip_duration_minutes"] = "not-a-number"
    data.loc[1, "trip_duration_minutes"] = np.inf
    data.loc[2, "trip_duration_minutes"] = None
    data.loc[3, "trip_duration_minutes"] = TARGET_POLICY["maximum_minutes"] + 1
    data.loc[4, "distance_miles"] = 0
    data.loc[5, "passenger_count"] = 7
    data["pickup_datetime"] = data["pickup_datetime"].astype(object)
    data.loc[6, "pickup_datetime"] = "not-a-timestamp"
    data.loc[7, "trip_id"] = data.loc[8, "trip_id"]

    audit = audit_data(data)
    quality = audit["target_quality"]
    assert quality["missing_count"] == 1
    assert quality["non_numeric_count"] == 1
    assert quality["non_finite_count"] == 1
    assert quality["above_maximum_count"] == 1
    assert quality["invalid_count"] == 4
    assert audit["invalid_pickup_datetime_count"] == 1
    assert audit["invalid_distance_count"] == 1
    assert audit["duplicate_trip_ids"] == 1
    assert {"category", "field", "row_index", "trip_id", "action", "status"}.issubset(audit["findings"][0])
    categories = {entry["category"] for entry in audit["finding_counts"]}
    assert "iqr_outlier_passenger_count" in categories
    assert "invalid_distance_non_positive" in categories
    assert "target_non_numeric" in categories
    duplicate = next(item for item in audit["findings"] if item["category"] == "duplicate_trip_id")
    assert duplicate["status"] == "excluded"
    assert duplicate["action"] == "exclude_duplicate_keep_first"
    assert next(item for item in audit["findings"] if item["category"] == "invalid_distance_non_positive")["action"] == "coerce_to_missing_and_impute"


def test_feature_timestamp_is_canonical_before_temporal_ordering():
    data = make_sample_data(60, 11)
    data.loc[data.index[0], "pickup_datetime"] = "2024-03-01T00:00:00"
    data.loc[data.index[1], "pickup_datetime"] = "2023-12-31T23:00:00"
    prepared = _features(data)
    assert str(prepared.loc[data.index[0], "pickup_datetime"]) == "2024-03-01 00:00:00"
    assert prepared.loc[data.index[1], "pickup_datetime"] < prepared.loc[data.index[0], "pickup_datetime"]


def test_train_only_imputation_statistics_do_not_depend_on_holdout_values():
    data = make_sample_data(100, 9).sort_values("pickup_datetime")
    prepared = _features(data[data["trip_duration_minutes"] > 0].copy())
    train = prepared.iloc[:75].copy()
    holdout = prepared.iloc[75:].copy()
    train.loc[train.index[0], "distance_miles"] = np.nan

    first_dataset = pd.concat([train, holdout])
    first = _model().fit(first_dataset.iloc[:75][FEATURES], first_dataset.iloc[:75]["trip_duration_minutes"])
    first_stats = first.named_steps["features"].named_transformers_["num"].named_steps["imputer"].statistics_.copy()

    changed_holdout = holdout.copy()
    changed_holdout["distance_miles"] = 999999.0
    second_dataset = pd.concat([train, changed_holdout])
    second = _model().fit(second_dataset.iloc[:75][FEATURES], second_dataset.iloc[:75]["trip_duration_minutes"])
    second_stats = second.named_steps["features"].named_transformers_["num"].named_steps["imputer"].statistics_.copy()

    assert np.array_equal(first_stats, second_stats)
    assert not changed_holdout.empty


def test_malformed_required_schema_is_reported_as_blocking():
    data = make_sample_data(50, 10).drop(columns=["dropoff_zone"])
    audit = audit_data(data)
    assert audit["missing_columns"] == ["dropoff_zone"]
    finding = next(item for item in audit["findings"] if item["category"] == "missing_required_column")
    assert finding["action"] == "fail_before_modeling"
    assert finding["status"] == "blocking"


def test_manifest_hashes_and_error_artifact_reconcile(tmp_path: Path):
    run_pipeline(tmp_path, rows=120, seed=12)
    manifest = json.loads((tmp_path / "run_manifest.json").read_text())
    metrics = json.loads((tmp_path / "metrics.json").read_text())
    errors = json.loads((tmp_path / "prediction_errors.json").read_text())
    assert set(manifest["artifact_hashes_sha256"]) == {
        "audit_report.json", "metrics.json", "model.joblib", "prediction_errors.json",
        "eda.png", "actual_vs_predicted.png", "crispdm_report.md",
    }
    for name, digest in manifest["artifact_hashes_sha256"].items():
        import hashlib
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest
    assert len(errors["rows"]) == metrics["test_rows"]
    assert metrics["raw_rows"] == metrics["retained_rows"] + metrics["excluded_rows"]
    assert metrics["train_rows"] + metrics["test_rows"] == metrics["retained_rows"]
    assert metrics["baselines"]["global_mean"]["rows"] == metrics["test_rows"]
