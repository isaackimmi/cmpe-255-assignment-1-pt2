"""Reproducible, CPU-safe model comparison for Project 07.

The development data is used for model selection with repeated stratified CV.
The final holdout is reserved for one evaluation of the selected model.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.base import clone
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 255
TEST_SIZE = 0.20
CV_SPLITS = 5
CV_REPEATS = 2
AUTOGLOON_TIME_LIMIT = 60


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    data = load_breast_cancer(as_frame=True)
    return data.data, data.target


def split_data(X: pd.DataFrame, y: pd.Series):
    """Create the final, locked holdout and development data."""
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


def _metrics(y_true, predictions, probabilities) -> dict[str, float | None]:
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
        "f1": float(f1_score(y_true, predictions, pos_label=1)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)) if probabilities is not None else None,
    }


def _predict_metrics(model: Any, X_eval, y_eval) -> dict[str, float | None]:
    predictions = model.predict(X_eval)
    probabilities = model.predict_proba(X_eval)[:, 1] if hasattr(model, "predict_proba") else None
    return _metrics(y_eval, predictions, probabilities)


def _cv_summary(scores: list[dict[str, float | None]], fit_seconds: list[float]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for metric in ("accuracy", "balanced_accuracy", "f1", "roc_auc"):
        values = [float(score[metric]) for score in scores if score[metric] is not None]
        summary[f"cv_{metric}_mean"] = sum(values) / len(values)
        summary[f"cv_{metric}_std"] = pd.Series(values).std(ddof=1) if len(values) > 1 else 0.0
    summary["cv_fit_seconds_mean"] = sum(fit_seconds) / len(fit_seconds)
    summary["cv_fit_seconds_std"] = pd.Series(fit_seconds).std(ddof=1) if len(fit_seconds) > 1 else 0.0
    # These aliases keep the CSV convenient for existing dashboard/API users.
    summary.update({
        "accuracy": summary["cv_accuracy_mean"],
        "balanced_accuracy": summary["cv_balanced_accuracy_mean"],
        "f1": summary["cv_f1_mean"],
        "roc_auc": summary["cv_roc_auc_mean"],
        "fit_seconds": summary["cv_fit_seconds_mean"],
    })
    return {key: (float(value) if isinstance(value, (float, int)) else value) for key, value in summary.items()}


def score_model(name: str, model: Any, X_train, X_test, y_train, y_test) -> dict[str, Any]:
    """Fit and score a model on an explicitly supplied evaluation split."""
    started = time.perf_counter()
    model.fit(X_train, y_train)
    elapsed = time.perf_counter() - started
    return {
        "model": name,
        "backend": "sklearn",
        **_predict_metrics(model, X_test, y_test),
        "fit_seconds": round(elapsed, 4),
    }


def cross_validate_model(name: str, model: Any, X_dev, y_dev) -> dict[str, Any]:
    """Return repeated-CV metrics computed using development rows only."""
    splitter = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=CV_REPEATS, random_state=SEED)
    scores: list[dict[str, float | None]] = []
    fit_seconds: list[float] = []
    for train_indices, validation_indices in splitter.split(X_dev, y_dev):
        fold_model = clone(model)
        started = time.perf_counter()
        fold_model.fit(X_dev.iloc[train_indices], y_dev.iloc[train_indices])
        fit_seconds.append(time.perf_counter() - started)
        scores.append(_predict_metrics(fold_model, X_dev.iloc[validation_indices], y_dev.iloc[validation_indices]))
    return {
        "model": name,
        "backend": "sklearn",
        "evaluation_scope": "development_cv",
        "selection_protocol": f"{CV_REPEATS}x{CV_SPLITS}-fold repeated stratified CV",
        **_cv_summary(scores, fit_seconds),
    }


def _autogluon_available() -> bool:
    return importlib.util.find_spec("autogluon.tabular") is not None


def _autogluon_fit_and_score(X_train, X_eval, y_train, y_eval, path: Path) -> tuple[dict[str, float | None], float, Any]:
    from autogluon.tabular import TabularPredictor

    label = "target"
    train = X_train.copy()
    train[label] = y_train.to_numpy()
    started = time.perf_counter()
    predictor = TabularPredictor(label=label, path=str(path), verbosity=0).fit(
        train_data=train,
        presets="medium_quality",
        time_limit=AUTOGLOON_TIME_LIMIT,
        num_cpus=1,
        random_seed=SEED,
    )
    elapsed = time.perf_counter() - started
    predictions = predictor.predict(X_eval)
    probabilities = predictor.predict_proba(X_eval)
    if hasattr(probabilities, "columns"):
        probabilities = probabilities[1] if 1 in probabilities.columns else probabilities.iloc[:, -1]
    else:
        probabilities = probabilities[1]
    return _metrics(y_eval, predictions, probabilities), elapsed, predictor


def run_autogluon(X_train, X_test, y_train, y_test, output_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Run one explicitly scoped AutoGluon fit/evaluation."""
    if not _autogluon_available():
        return None, "autogluon.tabular is not installed"
    try:
        metrics, elapsed, predictor = _autogluon_fit_and_score(
            X_train, X_test, y_train, y_test, output_dir / "autogluon_model"
        )
        return {
            "model": "autogluon_medium_quality",
            "backend": "autogluon",
            **metrics,
            "fit_seconds": round(elapsed, 4),
            "autogluon_model": predictor.get_model_best() if hasattr(predictor, "get_model_best") else None,
        }, None
    except Exception as exc:  # optional dependency/version/runtime failures are recorded, not fatal
        return None, f"{type(exc).__name__}: {exc}"


def _cross_validate_autogluon(X_dev, y_dev, output_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not _autogluon_available():
        return None, "autogluon.tabular is not installed"
    splitter = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=CV_REPEATS, random_state=SEED)
    scores: list[dict[str, float | None]] = []
    fit_seconds: list[float] = []
    try:
        for fold_number, (train_indices, validation_indices) in enumerate(splitter.split(X_dev, y_dev), start=1):
            metrics, elapsed, _ = _autogluon_fit_and_score(
                X_dev.iloc[train_indices], X_dev.iloc[validation_indices],
                y_dev.iloc[train_indices], y_dev.iloc[validation_indices],
                output_dir / f"autogluon_cv_{fold_number}",
            )
            scores.append(metrics)
            fit_seconds.append(elapsed)
        return {
            "model": "autogluon_medium_quality",
            "backend": "autogluon",
            "evaluation_scope": "development_cv",
            "selection_protocol": f"{CV_REPEATS}x{CV_SPLITS}-fold repeated stratified CV",
            **_cv_summary(scores, fit_seconds),
        }, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _dataset_hash(X: pd.DataFrame, y: pd.Series) -> str:
    digest = hashlib.sha256()
    digest.update(pd.util.hash_pandas_object(X, index=True).to_numpy().tobytes())
    digest.update(pd.util.hash_pandas_object(y, index=True).to_numpy().tobytes())
    return digest.hexdigest()


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(_json_safe(value), indent=2) + "\n", encoding="utf-8")


def run_experiment(output_dir: str | Path = "artifacts", include_autogluon: bool = True) -> pd.DataFrame:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    X, y = load_data()
    X_dev, X_test, y_dev, y_test = split_data(X, y)

    rows = [cross_validate_model(name, model, X_dev, y_dev) for name, model in sklearn_models().items()]
    ag_note: str | None = "AutoGluon disabled by caller"
    ag_status = "disabled"
    ag_failure_type: str | None = None
    attempted_backend = ["sklearn"]
    if include_autogluon:
        attempted_backend.append("autogluon")
        ag_row, ag_note = _cross_validate_autogluon(X_dev, y_dev, output_path)
        if ag_row is not None:
            rows.append(ag_row)
            ag_status = "completed"
        else:
            ag_status = "unavailable" if ag_note == "autogluon.tabular is not installed" else "failed"
            ag_failure_type = "missing_dependency" if ag_status == "unavailable" else "runtime_error"

    leaderboard = pd.DataFrame(rows).sort_values(["cv_roc_auc_mean", "cv_accuracy_mean"], ascending=False, ignore_index=True)
    leaderboard.insert(0, "rank", range(1, len(leaderboard) + 1))
    leaderboard.to_csv(output_path / "leaderboard.csv", index=False)

    selected = leaderboard.iloc[0].to_dict()
    selected_name = str(selected["model"])
    final_started = time.perf_counter()
    if selected_name == "autogluon_medium_quality":
        final_row, final_note = run_autogluon(X_dev, X_test, y_dev, y_test, output_path)
        if final_row is None:
            raise RuntimeError(f"Selected AutoGluon model could not be evaluated on the final holdout: {final_note}")
        final_metrics = final_row
    else:
        final_model = sklearn_models()[selected_name]
        final_model.fit(X_dev, y_dev)
        final_metrics = {
            "model": selected_name,
            "backend": "sklearn",
            **_predict_metrics(final_model, X_test, y_test),
            "fit_seconds": round(time.perf_counter() - final_started, 4),
        }
    final_metrics.update({
        "evaluation_scope": "final_holdout",
        "selection_metric": "cv_roc_auc_mean",
        "selected_by": "development_cv",
        "final_test_samples": len(X_test),
    })
    _write_json(output_path / "final_metrics.json", final_metrics)

    data = load_breast_cancer(as_frame=True)
    summary = {
        "dataset": "sklearn breast cancer",
        "dataset_loader": "sklearn.datasets.load_breast_cancer",
        "dataset_hash_sha256": _dataset_hash(X, y),
        "n_samples": int(len(X)),
        "n_features": int(X.shape[1]),
        "development_samples": int(len(X_dev)),
        "final_test_samples": int(len(X_test)),
        "train_samples": int(len(X_dev)),
        "test_samples": int(len(X_test)),
        "random_seed": SEED,
        "test_size": TEST_SIZE,
        "target_name": "target",
        "target_names": {str(index): name for index, name in enumerate(data.target_names)},
        "target_class_counts": {str(index): int(count) for index, count in y.value_counts().sort_index().items()},
        "positive_class": {"label": 1, "name": str(data.target_names[1])},
        "selection_protocol": f"{CV_REPEATS}x{CV_SPLITS}-fold repeated stratified CV on development data",
        "final_evaluation_protocol": "Selected model refit on all development data; final holdout scored once",
    }
    _write_json(output_path / "dataset_summary.json", summary)

    metadata = {
        "schema_version": 2,
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "command": [sys.executable, *sys.argv],
        "backend": "autogluon_plus_sklearn" if ag_status == "completed" else "sklearn_fallback",
        "requested_backend": "autogluon_optional" if include_autogluon else "sklearn_only",
        "attempted_backend": attempted_backend,
        "backend_status": {"sklearn": "completed", "autogluon": ag_status},
        "failure_type": {"autogluon": ag_failure_type},
        "autogluon_note": ag_note,
        "random_seed": SEED,
        "ranking_metric": "cv_roc_auc_mean",
        "selection_scope": "development_cv",
        "final_evaluation_scope": "final_holdout",
        "models": leaderboard["model"].tolist(),
        "selected_model": selected_name,
        "final_metrics_artifact": "final_metrics.json",
        "cv_splits": CV_SPLITS,
        "cv_repeats": CV_REPEATS,
        "autogluon_settings": {
            "presets": "medium_quality",
            "time_limit_seconds": AUTOGLOON_TIME_LIMIT,
            "num_cpus": 1,
            "random_seed": SEED,
        },
        "model_parameters": {name: _json_safe(model.get_params()) for name, model in sklearn_models().items()},
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "packages": {
                "numpy": _package_version("numpy"),
                "pandas": _package_version("pandas"),
                "scikit_learn": _package_version("scikit-learn"),
                "autogluon_tabular": _package_version("autogluon.tabular"),
            },
            "fit_time_note": "Wall-clock training time is environment-specific; CV values are means across folds.",
        },
    }
    _write_json(output_path / "metrics.json", metadata)
    return leaderboard
