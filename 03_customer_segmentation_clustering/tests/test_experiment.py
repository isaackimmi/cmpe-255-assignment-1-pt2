import numpy as np
import pandas as pd
from src.experiment import (CANDIDATE_K_VALUES, FEATURES, SEED, evaluate_k,
                            evaluate_validation, fit_segmenter, make_dataset,
                            run, score_customers, validate_artifacts,
                            validate_dataset, _transform)


def test_dataset_is_reproducible_and_valid():
    left, right = make_dataset(), make_dataset()
    assert left.equals(right)
    assert left.shape == (120, len(FEATURES))
    assert np.isfinite(left.to_numpy()).all()


def test_k_selection_is_deterministic_and_has_expected_signal():
    scores = evaluate_k(_transform(make_dataset(), improved=True))
    assert scores.loc[scores.silhouette.idxmax(), "k"] == 3
    assert scores.silhouette.max() > 0.45


def test_validation_reports_uncertainty_and_stability():
    scores = evaluate_validation(make_dataset(), repeats=4)
    assert set(scores.preprocessing) == {"standard"}
    assert scores.k.tolist() == list(CANDIDATE_K_VALUES)
    assert scores.silhouette_std.notna().all()
    assert scores.stability_ari_mean.between(0, 1).all()


def test_data_contract_and_scoring_path():
    data = make_dataset()
    assert validate_dataset(data)["valid"]
    assert not validate_dataset(data.drop(columns=[FEATURES[0]]))["valid"]
    fitted = fit_segmenter(data, "standard", 3)
    assignments = score_customers(data.iloc[:3], fitted)
    assert len(assignments) == 3
    assert assignments.name == "cluster"
    assert set(assignments).issubset({0, 1, 2})


def test_run_writes_audit_artifacts(tmp_path):
    result = run(tmp_path)
    assert result["selected_k"] == 3
    for name in ["customer_segments.csv", "baseline_scores.csv", "log1p_scores.csv", "validation_scores.csv", "segmentation.png", "summary.json", "manifest.json"]:
        assert (tmp_path / name).exists()
    assignments = pd.read_csv(tmp_path / "customer_segments.csv")
    assert assignments.shape == (120, len(FEATURES) + 1)
    assert assignments.cluster.nunique() == result["selected_k"]
    assert validate_artifacts(tmp_path)["valid"]
