import json
from pathlib import Path

import pytest

from src.platform import audit_data, infer_duration, make_sample_data, run_pipeline


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
    assert metrics["test_rows"] > 0
    assert metrics["mae_minutes"] >= 0
    assert {"eda.png", "actual_vs_predicted.png", "crispdm_report.md", "model.joblib"}.issubset(result["artifacts"])


def test_inference_is_json_serializable(tmp_path: Path):
    run_pipeline(tmp_path, rows=100, seed=3)
    result = infer_duration(tmp_path, 17, 4, 3.2, 2, 1, 2)
    assert result["predicted_duration_minutes"] > 0
    json.dumps(result)


def test_bad_inference_input_is_rejected(tmp_path: Path):
    run_pipeline(tmp_path, rows=100, seed=3)
    with pytest.raises(ValueError):
        infer_duration(tmp_path, 25, 4, 3.2, 2, 1, 2)
