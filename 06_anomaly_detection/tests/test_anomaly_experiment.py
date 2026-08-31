import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from anomaly_experiment import evaluate, make_data, score_methods


def test_data_is_reproducible_and_has_expected_labels():
    x1, y1, c1 = make_data(7)
    x2, y2, c2 = make_data(7)
    assert np.array_equal(x1, x2)
    assert np.array_equal(y1, y2)
    assert np.array_equal(c1, c2)
    assert x1.shape == (900, 2)
    assert y1.sum() == 100


def test_detectors_return_finite_scores_and_ensemble():
    x, labels, _ = make_data()
    scores = score_methods(x, labels.mean())
    assert set(scores) == {"isolation_forest", "local_outlier_factor", "elliptic_envelope", "rank_ensemble"}
    assert all(np.isfinite(value).all() for value in scores.values())
    assert all(value.shape == (900,) for value in scores.values())


def test_metrics_are_valid_and_ensemble_beats_random_baseline():
    x, labels, _ = make_data()
    result = evaluate(score_methods(x, labels.mean()), labels, labels.mean())
    for values in result.values():
        assert 0 <= values["roc_auc"] <= 1
        assert 0 <= values["average_precision"] <= 1
        assert 0 <= values["f1"] <= 1
        assert values["flagged"] == 100
    assert result["rank_ensemble"]["average_precision"] > labels.mean()
