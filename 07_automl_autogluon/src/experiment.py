"""Reproducible, CPU-safe model comparison for Project 07."""

from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 255
TEST_SIZE = 0.20


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    data = load_breast_cancer(as_frame=True)
    return data.data, data.target


def split_data(X: pd.DataFrame, y: pd.Series):
    return train_test_split(X, y, test_size=TEST_SIZE, random_state=SEED, stratify=y)


def sklearn_models() -> dict[str, Any]:
    return {
        "logistic_regression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=1000, random_state=SEED)
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=120, max_depth=8, n_jobs=1, random_state=SEED
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=120, max_depth=10, n_jobs=1, random_state=SEED
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=100, max_leaf_nodes=15, random_state=SEED
        ),
    }


def score_model(name: str, model: Any, X_train, X_test, y_train, y_test) -> dict[str, Any]:
    started = time.perf_counter()
    model.fit(X_train, y_train)
    elapsed = time.perf_counter() - started
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
    return {
        "model": name,
        "backend": "sklearn",
        "accuracy": float(accuracy_score(y_test, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, predictions)),
        "f1": float(f1_score(y_test, predictions)),
        "roc_auc": float(roc_auc_score(y_test, probabilities)) if probabilities is not None else None,
        "fit_seconds": round(elapsed, 4),
    }


def run_autogluon(X_train, X_test, y_train, y_test, output_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    if importlib.util.find_spec("autogluon.tabular") is None:
        return None, "autogluon.tabular is not installed"
    try:
        from autogluon.tabular import TabularPredictor

        label = "target"
        train = X_train.copy()
        test = X_test.copy()
        train[label] = y_train.to_numpy()
        test[label] = y_test.to_numpy()
        path = output_dir / "autogluon_model"
        started = time.perf_counter()
        predictor = TabularPredictor(label=label, path=str(path), verbosity=0).fit(
            train_data=train,
            presets="medium_quality",
            time_limit=60,
            num_cpus=1,
        )
        elapsed = time.perf_counter() - started
        predictions = predictor.predict(test.drop(columns=[label]))
        probabilities = predictor.predict_proba(test.drop(columns=[label]))[1]
        return {
            "model": "autogluon_medium_quality",
            "backend": "autogluon",
            "accuracy": float(accuracy_score(y_test, predictions)),
            "balanced_accuracy": float(balanced_accuracy_score(y_test, predictions)),
            "f1": float(f1_score(y_test, predictions)),
            "roc_auc": float(roc_auc_score(y_test, probabilities)),
            "fit_seconds": round(elapsed, 4),
        }, None
    except Exception as exc:  # optional dependency/version/runtime failures are recorded, not fatal
        return None, f"AutoGluon run failed: {type(exc).__name__}: {exc}"


def run_experiment(output_dir: str | Path = "artifacts", include_autogluon: bool = True) -> pd.DataFrame:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y)

    rows = [score_model(name, model, X_train, X_test, y_train, y_test) for name, model in sklearn_models().items()]
    ag_row = None
    ag_note = "AutoGluon disabled by caller"
    if include_autogluon:
        ag_row, ag_note = run_autogluon(X_train, X_test, y_train, y_test, output_path)
        if ag_row is not None:
            rows.append(ag_row)
    leaderboard = pd.DataFrame(rows).sort_values(["roc_auc", "accuracy"], ascending=False, ignore_index=True)
    leaderboard.insert(0, "rank", range(1, len(leaderboard) + 1))
    leaderboard.to_csv(output_path / "leaderboard.csv", index=False)
    summary = {
        "dataset": "sklearn breast cancer",
        "n_samples": int(len(X)),
        "n_features": int(X.shape[1]),
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "random_seed": SEED,
        "test_size": TEST_SIZE,
    }
    (output_path / "dataset_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    metadata = {
        "backend": "autogluon_plus_sklearn" if ag_row else "sklearn_fallback",
        "autogluon_note": ag_note,
        "random_seed": SEED,
        "ranking_metric": "roc_auc",
        "models": leaderboard["model"].tolist(),
    }
    (output_path / "metrics.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return leaderboard
