import json

import pandas as pd

import src.experiment as experiment
from src.experiment import SEED, load_data, run_experiment, split_data


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
    assert dataset["positive_class"] == {"label": 1, "name": "benign"}
    assert sum(dataset["target_class_counts"].values()) == dataset["n_samples"]
    assert dataset["dataset_hash_sha256"]
    assert metadata["environment"]["packages"]["scikit_learn"] is None or metadata["environment"]["packages"]["scikit_learn"]
    assert metadata["random_seed"] == SEED


def test_final_holdout_is_not_a_selection_metric(tmp_path):
    leaderboard = run_experiment(tmp_path, include_autogluon=False)
    final_metrics = json.loads((tmp_path / "final_metrics.json").read_text())
    assert "final_test_roc_auc" not in leaderboard.columns
    assert final_metrics["selection_metric"] == "cv_roc_auc_mean"
    assert final_metrics["final_test_samples"] == 114


def test_autogluon_disabled_and_unavailable_are_distinct(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, "_autogluon_available", lambda: False)
    run_experiment(tmp_path, include_autogluon=True)
    metadata = json.loads((tmp_path / "metrics.json").read_text())
    assert metadata["requested_backend"] == "autogluon_optional"
    assert metadata["attempted_backend"] == ["sklearn", "autogluon"]
    assert metadata["backend_status"]["autogluon"] == "unavailable"
    assert metadata["failure_type"]["autogluon"] == "missing_dependency"
    assert metadata["autogluon_note"] == "autogluon.tabular is not installed"
