import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from anomaly_experiment import (  # noqa: E402
    ANOMALY_CATEGORIES,
    DEFAULT_ALERT_BUDGET,
    build_metrics,
    calibrate_thresholds,
    evaluate,
    make_data,
    make_protocol_data,
    score_methods,
)


def test_data_is_reproducible_and_anomalies_pass_acceptance_rule():
    x1, y1, c1 = make_data(7)
    x2, y2, c2 = make_data(7)
    assert np.array_equal(x1, x2)
    assert np.array_equal(y1, y2)
    assert np.array_equal(c1, c2)
    assert x1.shape == (900, 2)
    assert y1.sum() == 100

    anomaly_x = x1[y1 == 1]
    from anomaly_experiment import _normal_tail_distance

    assert np.all(_normal_tail_distance(anomaly_x) >= 8.0)
    assert {category: int((c1 == category).sum()) for category in ANOMALY_CATEGORIES} == {
        "global": 35,
        "local": 30,
        "cluster": 35,
    }


def test_protocol_has_clean_train_calibration_and_untouched_holdout():
    data = make_protocol_data(42)
    assert data["train"].shape == (600, 2)
    assert data["calibration"].shape == (200, 2)
    assert data["test"].shape == (300, 2)
    assert data["labels"].sum() == 100
    assert np.isfinite(data["train"]).all()
    assert np.isfinite(data["calibration"]).all()
    assert np.isfinite(data["test"]).all()


def test_detectors_fit_on_train_and_score_query_without_labels():
    data = make_protocol_data()
    calibration_scores = score_methods(data["train"], data["calibration"])
    test_scores = score_methods(data["train"], data["test"])
    assert set(test_scores) == {"isolation_forest", "local_outlier_factor", "elliptic_envelope", "rank_ensemble"}
    assert all(np.isfinite(value).all() for value in calibration_scores.values())
    assert all(np.isfinite(value).all() for value in test_scores.values())
    assert all(value.shape == (200,) for value in calibration_scores.values())
    assert all(value.shape == (300,) for value in test_scores.values())


def test_threshold_calibration_uses_only_clean_scores():
    scores = {"method": np.array([0.0, 1.0, 2.0, 3.0])}
    assert calibrate_thresholds(scores, 0.75)["method"] == 2.25


def test_fixed_budget_metrics_are_named_and_have_explicit_queue_size():
    data = make_protocol_data()
    result = evaluate(score_methods(data["train"], data["test"]), data["labels"], DEFAULT_ALERT_BUDGET)
    for values in result.values():
        assert 0 <= values["roc_auc"] <= 1
        assert 0 <= values["average_precision"] <= 1
        assert 0 <= values["f1_at_k"] <= 1
        assert values["alert_budget"] == DEFAULT_ALERT_BUDGET
        assert values["flagged"] == DEFAULT_ALERT_BUDGET
        assert values["precision_at_k"] == values["recall_at_k"] == values["f1_at_k"]


def test_metrics_include_holdout_protocol_and_score_backed_operating_points():
    metrics, _, _ = build_metrics(42)
    metadata = metrics["metadata"]
    assert metadata["protocol"] == "clean_train_clean_calibration_holdout"
    assert metadata["train_size"] == 600
    assert metadata["calibration_size"] == 200
    assert metadata["test_size"] == 300
    assert metadata["test_anomaly_count"] == 100
    assert metadata["alert_budget"] == DEFAULT_ALERT_BUDGET
    assert metadata["anomaly_acceptance"].endswith(">= 8")
    for name in ("isolation_forest", "local_outlier_factor", "elliptic_envelope", "rank_ensemble"):
        assert len(metrics["threshold_points"][name]) == 46
        assert metrics["operating_points"][name]["95"]["100"]["flagged"] <= 100


def test_protocol_remains_finite_and_reproducible_for_multiple_seeds():
    for seed in (0, 7):
        first = make_protocol_data(seed)
        second = make_protocol_data(seed)
        assert np.array_equal(first["test"], second["test"])
        assert np.isfinite(score_methods(first["train"], first["test"])["rank_ensemble"]).all()
