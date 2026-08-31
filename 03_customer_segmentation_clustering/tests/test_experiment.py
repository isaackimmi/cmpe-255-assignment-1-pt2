import numpy as np
import pandas as pd
from src.experiment import (CANDIDATE_K_VALUES, FEATURES, SEED, evaluate_k,
                            evaluate_validation, fit_segmenter, make_dataset,
                            run, score_customers, validate_artifacts,
                            validate_dataset, feature_audit, _transform, EXPLORER_COLUMNS)


def test_dataset_is_reproducible_and_valid():
    left, right = make_dataset(), make_dataset()
    assert left.equals(right)
    assert left.shape == (120, len(FEATURES))
    assert np.isfinite(left.to_numpy()).all()
    audit = feature_audit(left)
    assert audit["features"][FEATURES[0]]["iqr_outliers"] >= 0
    assert set(audit["correlation"]) == set(FEATURES)


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
    for name in ["customer_segments.csv", "explorer_points.csv", "baseline_scores.csv", "log1p_scores.csv", "validation_scores.csv", "segmentation.png", "summary.json", "manifest.json"]:
        assert (tmp_path / name).exists()
    assignments = pd.read_csv(tmp_path / "customer_segments.csv")
    assert assignments.shape == (120, len(FEATURES) + 1)
    assert assignments.cluster.nunique() == result["selected_k"]
    explorer = pd.read_csv(tmp_path / "explorer_points.csv")
    assert explorer.columns.tolist() == EXPLORER_COLUMNS
    assert explorer.shape[0] == len(assignments)
    assert explorer.customer_id.iloc[0] == "C001"
    assert set(explorer.uncertainty_label).issubset({"clear", "moderate", "ambiguous"})
    assert explorer.assignment_confidence.between(0, 1).all()
    summary = pd.read_json(tmp_path / "summary.json", typ="series")
    assert "feature_audit" in summary["data_quality"]
    assert validate_artifacts(tmp_path)["valid"]


def test_artifact_manifest_rejects_stale_or_incomplete_hashes(tmp_path):
    run(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = manifest_path.read_text()
    manifest_path.write_text(manifest.replace('"explorer_points.csv":', '"stale.csv":', 1))
    result = validate_artifacts(tmp_path)
    assert not result["valid"]
    assert any("manifest" in error for error in result["errors"])
