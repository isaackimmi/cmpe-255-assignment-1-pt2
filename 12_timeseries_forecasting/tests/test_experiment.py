import numpy as np
import pytest

from src.experiment import (
    HORIZONS,
    feature_matrix,
    make_dataset,
    make_features,
    metrics,
    run,
    seasonal_naive_forecast,
)


def test_dataset_is_reproducible_and_ordered():
    first, second = make_dataset(), make_dataset()
    assert first.equals(second)
    assert first.date.is_monotonic_increasing


def test_features_never_need_current_or_future_value():
    values = make_dataset()["value"].to_numpy()
    original = make_features(values, 24)
    changed_future = values.copy()
    changed_future[24:] += 10000
    assert np.allclose(original, make_features(changed_future, 24))


def test_feature_matrix_has_expected_shape():
    X, y = feature_matrix(make_dataset()["value"].to_numpy(), 12, 30)
    assert X.shape == (18, 8)
    assert y.shape == (18,)


def test_closed_loop_seasonal_naive_feeds_predictions_back():
    observed = np.arange(12, dtype=float)
    forecast = seasonal_naive_forecast(observed, 15)
    assert np.array_equal(forecast, np.r_[np.arange(12, dtype=float), [0.0, 1.0, 2.0]])


def test_metrics_reject_misaligned_or_non_finite_inputs():
    with pytest.raises(ValueError, match="same shape"):
        metrics(np.array([1.0, 2.0]), np.array([1.0]))
    with pytest.raises(ValueError, match="finite"):
        metrics(np.array([1.0, np.nan]), np.array([1.0, 2.0]))


def test_run_writes_artifacts(tmp_path):
    result = run(tmp_path)
    assert result["split"] == {
        "train_end": 168,
        "validation_end": 204,
        "test_start": 204,
        "train_rows": 168,
        "validation_rows": 36,
        "test_rows": 36,
    }
    assert result["forecast_protocol"] == {
        "name": "closed_loop_multi_step",
        "forecast_origin_index": 168,
        "forecast_origin": "2014-01-01",
        "history_through_index": 167,
        "history_through": "2013-12-01",
        "validation_horizon": 36,
        "test_horizon": 36,
        "actual_intermediate_observations_used": False,
        "predictions_feed_back_into_history": True,
        "test_targets_used_as_inputs": False,
    }
    assert result["available_horizons"] == list(HORIZONS)
    assert set(result["horizon_metrics"]) == {str(horizon) for horizon in HORIZONS}
    for horizon in HORIZONS:
        assert (tmp_path / f"forecast_horizon_{horizon}.png").exists()
        assert result["horizon_metrics"][str(horizon)]["baseline_seasonal_naive"]["mae"] >= 0
    predictions = np.genfromtxt(tmp_path / "forecast_predictions.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")
    assert len(predictions) == 72
    assert np.isfinite(predictions["baseline_seasonal_naive"]).all()
    assert np.isfinite(predictions["model_hist_gradient_boosting"]).all()
    assert result["forecast_protocol"]["actual_intermediate_observations_used"] is False
    assert (tmp_path / "metrics.json").exists()
    assert (tmp_path / "forecast.png").exists()
    assert metrics(np.array([1, 2]), np.array([1, 3]))["mae"] == 0.5


def test_run_is_deterministic_and_records_provenance(tmp_path):
    first = run(tmp_path / "first")
    second = run(tmp_path / "second")
    assert first == second
    assert first["provenance"]["data"]["seed"] == 7
    assert first["provenance"]["model"]["random_state"] == 7
    assert first["provenance"]["software"]["python"]
    assert first["provenance"]["source_revision"]
