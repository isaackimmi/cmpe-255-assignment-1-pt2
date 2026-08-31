import numpy as np

from src.experiment import feature_matrix, make_dataset, make_features, metrics, run


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


def test_run_writes_artifacts(tmp_path):
    result = run(tmp_path)
    assert result["split"]["test_start"] > result["split"]["train_end"]
    assert (tmp_path / "metrics.json").exists()
    assert (tmp_path / "forecast.png").exists()
    assert metrics(np.array([1, 2]), np.array([1, 3]))["mae"] == 0.5
