import json
from pathlib import Path

import pandas as pd

import src.experiment as experiment
from src.experiment import (
    DEFAULT_THRESHOLD,
    SEED,
    _cross_validate_autogluon,
    _metrics,
    load_data,
    run_autogluon,
    run_experiment,
    split_data,
)


def test_dataset_and_split_are_reproducible():
    X, y = load_data()
    first = split_data(X, y)
    second = split_data(X, y)
    assert X.shape == (569, 30)
    assert y.nunique() == 2
    assert first[0].equals(second[0])
    assert first[3].equals(second[3])


def test_sklearn_fallback_writes_ranked_metrics(tmp_path):
    leaderboard = run_experiment(tmp_path, include_autogluon=False)
    assert isinstance(leaderboard, pd.DataFrame)
    assert len(leaderboard) == 4
    assert leaderboard["rank"].tolist() == [1, 2, 3, 4]
    assert leaderboard["evaluation_scope"].eq("development_cv").all()
    assert leaderboard["selection_protocol"].eq("2x5-fold repeated stratified CV").all()
    assert leaderboard["cv_roc_auc_mean"].between(0.5, 1.0).all()
    assert leaderboard["cv_roc_auc_std"].ge(0).all()
    assert leaderboard["backend"].eq("sklearn").all()
    assert (tmp_path / "leaderboard.csv").exists()
    assert (tmp_path / "final_metrics.json").exists()
    metadata = json.loads((tmp_path / "metrics.json").read_text())
    final_metrics = json.loads((tmp_path / "final_metrics.json").read_text())
    dataset = json.loads((tmp_path / "dataset_summary.json").read_text())
    assert metadata["backend"] == "sklearn_fallback"
    assert metadata["requested_backend"] == "sklearn_only"
    assert metadata["attempted_backend"] == ["sklearn"]
    assert metadata["backend_status"] == {"sklearn": "completed", "autogluon": "disabled"}
    assert metadata["selection_scope"] == "development_cv"
    assert metadata["final_evaluation_scope"] == "final_holdout"
    assert metadata["selected_model"] == leaderboard.iloc[0]["model"]
    assert final_metrics["evaluation_scope"] == "final_holdout"
    assert final_metrics["selected_by"] == "development_cv"
    assert final_metrics["model"] == metadata["selected_model"]
    assert dataset["development_samples"] + dataset["final_test_samples"] == dataset["n_samples"]
    assert dataset["positive_class"] == {"label": 0, "name": "malignant"}
    assert dataset["negative_class"] == {"label": 1, "name": "benign"}
    assert dataset["error_costs"]["false_negative_positive_class"] == "high"
    assert dataset["threshold_protocol"].startswith("Each candidate threshold")
    assert sum(dataset["target_class_counts"].values()) == dataset["n_samples"]
    assert dataset["dataset_hash_sha256"]
    assert metadata["environment"]["packages"]["scikit_learn"] is None or metadata["environment"]["packages"]["scikit_learn"]
    assert metadata["random_seed"] == SEED
    assert metadata["schema_version"] == 3
    assert metadata["selected_decision_threshold"] == final_metrics["decision_threshold"]
    assert metadata["cv_scores_artifact"] == "cv_scores.json"
    assert metadata["metric_semantics"]["practical_tie_tolerance"] > 0
    fold_scores = json.loads((tmp_path / "cv_scores.json").read_text())
    assert set(fold_scores["models"]) == set(leaderboard["model"])
    assert all(len(scores) == 10 for scores in fold_scores["models"].values())
    assert all("roc_auc" in score and "sensitivity" in score for scores in fold_scores["models"].values() for score in scores)
    assert all("final" not in str(score).lower() for scores in fold_scores["models"].values() for score in scores)
    assert final_metrics["positive_class"] == {"label": 0, "name": "malignant"}
    assert final_metrics["decision_threshold"] == leaderboard.iloc[0]["decision_threshold"]
    assert set(final_metrics["confusion_matrix"]) == {"tn", "fp", "fn", "tp"}


def test_final_holdout_is_not_a_selection_metric(tmp_path):
    leaderboard = run_experiment(tmp_path, include_autogluon=False)
    final_metrics = json.loads((tmp_path / "final_metrics.json").read_text())
    assert "final_test_roc_auc" not in leaderboard.columns
    assert final_metrics["selection_metric"] == "cv_roc_auc_mean"
    assert final_metrics["final_test_samples"] == 114
    assert "sensitivity" in final_metrics
    assert "specificity" in final_metrics
    assert "pr_auc" in final_metrics
    assert "brier_score" in final_metrics
    assert "decision_threshold" in final_metrics
    assert "final_test_roc_auc" not in leaderboard.columns


def test_metric_semantics_use_malignant_as_positive_class():
    metrics = _metrics([0, 0, 1, 1], [0, 1, 0, 1], [0.9, 0.4, 0.6, 0.1], DEFAULT_THRESHOLD)
    assert metrics["sensitivity"] == 0.5
    assert metrics["specificity"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["npv"] == 0.5
    assert metrics["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
    assert metrics["roc_auc"] == 0.75


def test_autogluon_disabled_and_unavailable_are_distinct(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, "_autogluon_available", lambda: False)
    run_experiment(tmp_path, include_autogluon=True)
    metadata = json.loads((tmp_path / "metrics.json").read_text())
    assert metadata["requested_backend"] == "autogluon_optional"
    assert metadata["attempted_backend"] == ["sklearn", "autogluon"]
    assert metadata["backend_status"]["autogluon"] == "unavailable"
    assert metadata["failure_type"]["autogluon"] == "missing_dependency"
    assert metadata["autogluon_note"] == "autogluon.tabular is not installed"


def test_autogluon_failed_cv_preserves_fold_audit(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, "_autogluon_available", lambda: True)

    def fail_fit(*args, **kwargs):
        raise RuntimeError("synthetic AutoGluon failure")

    monkeypatch.setattr(experiment, "_autogluon_fit_and_score", fail_fit)
    X, y = load_data()
    X_dev, _, y_dev, _ = split_data(X, y)
    row, note, audits, folds = _cross_validate_autogluon(X_dev, y_dev, tmp_path)
    assert row is None
    assert "synthetic AutoGluon failure" in note
    assert audits[-1]["status"] == "failed"
    assert folds == []


def test_autogluon_completed_result_keeps_search_audit(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, "_autogluon_available", lambda: True)
    audit = {"best_model": "WeightedEnsemble_L2", "model_count": 3, "model_names": ["CatBoost", "WeightedEnsemble_L2"], "ensemble_included": True, "internal_leaderboard_top20": [], "total_search_seconds": 1.2}
    metrics = _metrics([0, 0, 1, 1], [0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1])
    monkeypatch.setattr(experiment, "_autogluon_fit_and_score", lambda *args, **kwargs: (metrics, 1.2, object(), audit))
    X, y = load_data()
    X_dev, X_test, y_dev, y_test = split_data(X, y)
    row, note, returned_audit = run_autogluon(X_dev, X_test, y_dev, y_test, tmp_path, threshold=0.4)
    assert note is None
    assert row["backend"] == "autogluon"
    assert row["autogluon_model"] == "WeightedEnsemble_L2"
    assert row["decision_threshold"] == 0.4
    assert returned_audit["ensemble_included"] is True


def test_checked_in_artifacts_match_current_schema():
    root = Path(__file__).resolve().parents[1]
    metadata = json.loads((root / "artifacts/metrics.json").read_text())
    final_metrics = json.loads((root / "artifacts/final_metrics.json").read_text())
    cv_scores = json.loads((root / "artifacts/cv_scores.json").read_text())
    assert metadata["schema_version"] == 3
    assert metadata["selected_model"] == final_metrics["model"]
    assert metadata["selected_decision_threshold"] == final_metrics["decision_threshold"]
    assert set(metadata["models"]) == set(cv_scores["models"])
    assert "Development-CV ROC-AUC" in (root / "artifacts/run_evidence.svg").read_text()
