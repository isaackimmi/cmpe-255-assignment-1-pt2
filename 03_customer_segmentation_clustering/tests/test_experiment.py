import numpy as np
from src.experiment import FEATURES, SEED, evaluate_k, make_dataset, run, _transform


def test_dataset_is_reproducible_and_valid():
    left, right = make_dataset(), make_dataset()
    assert left.equals(right)
    assert left.shape == (120, len(FEATURES))
    assert np.isfinite(left.to_numpy()).all()


def test_k_selection_is_deterministic_and_has_expected_signal():
    scores = evaluate_k(_transform(make_dataset(), improved=True))
    assert scores.loc[scores.silhouette.idxmax(), "k"] == 3
    assert scores.silhouette.max() > 0.45


def test_run_writes_audit_artifacts(tmp_path):
    result = run(tmp_path)
    assert result["selected_k"] == 3
    for name in ["customer_segments.csv", "baseline_scores.csv", "improved_scores.csv", "segmentation.png", "summary.json"]:
        assert (tmp_path / name).exists()
