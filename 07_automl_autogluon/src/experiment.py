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

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 255
TEST_SIZE = 0.20
CV_SPLITS = 5
CV_REPEATS = 2
AUTOGLOON_TIME_LIMIT = 60
POSITIVE_LABEL = 0
NEGATIVE_LABEL = 1
DEFAULT_THRESHOLD = 0.5
PRACTICAL_TIE_TOLERANCE = 0.005


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


def _metrics(y_true, predictions, probabilities, threshold: float = DEFAULT_THRESHOLD) -> dict[str, Any]:
    """Return metrics with malignant (label 0) as the declared positive class."""
    y_array = np.asarray(y_true)
    if probabilities is not None:
        probabilities = np.asarray(probabilities, dtype=float)
        predictions = np.where(probabilities >= threshold, POSITIVE_LABEL, NEGATIVE_LABEL)
    binary_true = (y_array == POSITIVE_LABEL).astype(int)
    binary_predictions = (np.asarray(predictions) == POSITIVE_LABEL).astype(int)
    tn, fp, fn, tp = confusion_matrix(binary_true, binary_predictions, labels=[0, 1]).ravel()
    sensitivity = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    npv = tn / (tn + fn) if tn + fn else 0.0
    result: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_array, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_array, predictions)),
        "f1": float(f1_score(binary_true, binary_predictions, pos_label=1, zero_division=0)),
        "f1_negative_class": float(f1_score(binary_true, binary_predictions, pos_label=0, zero_division=0)),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "precision": float(precision),
        "npv": float(npv),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "threshold": float(threshold),
    }
    if probabilities is not None:
        result["roc_auc"] = float(roc_auc_score(binary_true, probabilities))
        result["pr_auc"] = float(average_precision_score(binary_true, probabilities))
        result["brier_score"] = float(brier_score_loss(binary_true, probabilities))
    else:
        result.update({"roc_auc": None, "pr_auc": None, "brier_score": None})
    return result


def _predict_metrics(model: Any, X_eval, y_eval, threshold: float = DEFAULT_THRESHOLD) -> dict[str, Any]:
    predictions = model.predict(X_eval)
    probabilities = None
    if hasattr(model, "predict_proba"):
        raw_probabilities = model.predict_proba(X_eval)
        classes = list(getattr(model, "classes_", [NEGATIVE_LABEL, POSITIVE_LABEL]))
        probabilities = np.asarray(raw_probabilities)[:, classes.index(POSITIVE_LABEL)]
    return _metrics(y_eval, predictions, probabilities, threshold=threshold)


def _mean_std_ci(values: list[float]) -> tuple[float, float, tuple[float, float]]:
    if not values:
        return 0.0, 0.0, (0.0, 0.0)
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    margin = 1.96 * std / np.sqrt(len(values)) if values else 0.0
    return mean, std, (max(0.0, mean - margin), min(1.0, mean + margin))


def _cv_summary(scores: list[dict[str, Any]], fit_seconds: list[float]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for metric in ("accuracy", "balanced_accuracy", "f1", "f1_negative_class", "sensitivity", "specificity", "precision", "npv", "roc_auc", "pr_auc", "brier_score"):
        values = [float(score[metric]) for score in scores if score[metric] is not None]
        mean, std, (ci_low, ci_high) = _mean_std_ci(values)
        summary[f"cv_{metric}_mean"] = mean
        summary[f"cv_{metric}_std"] = std
        summary[f"cv_{metric}_ci_low"] = ci_low
        summary[f"cv_{metric}_ci_high"] = ci_high
    fit_mean, fit_std, _ = _mean_std_ci(fit_seconds)
    summary["cv_fit_seconds_mean"] = fit_mean
    summary["cv_fit_seconds_std"] = fit_std
    summary["cv_fold_count"] = len(scores)
    # These aliases keep the CSV convenient for existing dashboard/API users.
    summary.update({
        "accuracy": summary["cv_accuracy_mean"],
        "balanced_accuracy": summary["cv_balanced_accuracy_mean"],
        "f1": summary["cv_f1_mean"],
        "roc_auc": summary["cv_roc_auc_mean"],
        "fit_seconds": summary["cv_fit_seconds_mean"],
    })
    return {key: (float(value) if isinstance(value, (float, int)) else value) for key, value in summary.items()}


def _select_threshold(y_true, probabilities) -> float:
    """Select an operating threshold from development-only out-of-fold predictions."""
    y_binary = (np.asarray(y_true) == POSITIVE_LABEL).astype(int)
    candidates = np.unique(np.concatenate(([DEFAULT_THRESHOLD], np.asarray(probabilities, dtype=float))))
    best = (float("-inf"), float("-inf"), float("-inf"), DEFAULT_THRESHOLD)
    for candidate in candidates:
        predicted = (np.asarray(probabilities) >= candidate).astype(int)
        f1 = f1_score(y_binary, predicted, zero_division=0)
        sensitivity = recall = (np.sum((y_binary == 1) & (predicted == 1)) / np.sum(y_binary == 1))
        tie_break = -abs(float(candidate) - DEFAULT_THRESHOLD)
        score = (float(f1), float(recall), float(tie_break), float(candidate))
        if score[:3] > best[:3]:
            best = score
    return round(float(best[3]), 6)


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


def cross_validate_model(name: str, model: Any, X_dev, y_dev) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return repeated-CV metrics computed using development rows only."""
    splitter = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=CV_REPEATS, random_state=SEED)
    scores: list[dict[str, Any]] = []
    fold_records: list[dict[str, Any]] = []
    fit_seconds: list[float] = []
    oof_probabilities: list[float] = []
    oof_labels: list[int] = []
    for split_number, (train_indices, validation_indices) in enumerate(splitter.split(X_dev, y_dev), start=1):
        fold_model = clone(model)
        started = time.perf_counter()
        fold_model.fit(X_dev.iloc[train_indices], y_dev.iloc[train_indices])
        elapsed = time.perf_counter() - started
        fit_seconds.append(elapsed)
        fold_score = _predict_metrics(fold_model, X_dev.iloc[validation_indices], y_dev.iloc[validation_indices])
        scores.append(fold_score)
        fold_records.append({
            "repeat": ((split_number - 1) // CV_SPLITS) + 1,
            "fold": ((split_number - 1) % CV_SPLITS) + 1,
            "fit_seconds": round(elapsed, 6),
            **fold_score,
        })
        raw_probabilities = fold_model.predict_proba(X_dev.iloc[validation_indices])
        classes = list(getattr(fold_model, "classes_", [NEGATIVE_LABEL, POSITIVE_LABEL]))
        oof_probabilities.extend(np.asarray(raw_probabilities)[:, classes.index(POSITIVE_LABEL)])
        oof_labels.extend(y_dev.iloc[validation_indices].tolist())
    threshold = _select_threshold(oof_labels, oof_probabilities)
    row = {
        "model": name,
        "backend": "sklearn",
        "evaluation_scope": "development_cv",
        "selection_protocol": f"{CV_REPEATS}x{CV_SPLITS}-fold repeated stratified CV",
        **_cv_summary(scores, fit_seconds),
        "decision_threshold": threshold,
        "threshold_selection_scope": "development_cv_oof",
    }
    return row, fold_records


def _autogluon_available() -> bool:
    return importlib.util.find_spec("autogluon.tabular") is not None


def _autogluon_fit_and_score(X_train, X_eval, y_train, y_eval, path: Path, threshold: float = DEFAULT_THRESHOLD) -> tuple[dict[str, Any], float, Any, dict[str, Any]]:
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
        probabilities = probabilities[POSITIVE_LABEL] if POSITIVE_LABEL in probabilities.columns else probabilities.iloc[:, 0]
    else:
        probabilities = np.asarray(probabilities)[:, POSITIVE_LABEL]
    model_names = []
    try:
        model_names = list(predictor.get_model_names())
    except Exception:
        pass
    internal_leaderboard: list[dict[str, Any]] = []
    try:
        internal = predictor.leaderboard(silent=True)
        internal_leaderboard = internal.head(20).to_dict(orient="records")
    except Exception:
        pass
    audit = {
        "best_model": predictor.get_model_best() if hasattr(predictor, "get_model_best") else None,
        "model_count": len(model_names),
        "model_names": model_names,
        "internal_leaderboard_top20": internal_leaderboard,
        "ensemble_included": any("weightedensemble" in str(name).lower() for name in model_names),
        "time_limit_seconds": AUTOGLOON_TIME_LIMIT,
        "total_search_seconds": round(elapsed, 4),
    }
    return _metrics(y_eval, predictions, probabilities, threshold=threshold), elapsed, predictor, audit


def run_autogluon(X_train, X_test, y_train, y_test, output_dir: Path, threshold: float = DEFAULT_THRESHOLD) -> tuple[dict[str, Any] | None, str | None, dict[str, Any] | None]:
    """Run one explicitly scoped AutoGluon fit/evaluation."""
    if not _autogluon_available():
        return None, "autogluon.tabular is not installed", None
    try:
        metrics, elapsed, predictor, audit = _autogluon_fit_and_score(
            X_train, X_test, y_train, y_test, output_dir / "autogluon_model", threshold=threshold
        )
        return {
            "model": "autogluon_medium_quality",
            "backend": "autogluon",
            **metrics,
            "fit_seconds": round(elapsed, 4),
            "autogluon_model": audit["best_model"],
            "decision_threshold": threshold,
            "threshold_selection_scope": "development_cv_oof",
        }, None, audit
    except Exception as exc:  # optional dependency/version/runtime failures are recorded, not fatal
        return None, f"{type(exc).__name__}: {exc}", None


def _cross_validate_autogluon(X_dev, y_dev, output_dir: Path) -> tuple[dict[str, Any] | None, str | None, list[dict[str, Any]], list[dict[str, Any]]]:
    if not _autogluon_available():
        return None, "autogluon.tabular is not installed", [], []
    splitter = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=CV_REPEATS, random_state=SEED)
    scores: list[dict[str, Any]] = []
    fold_records: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    fit_seconds: list[float] = []
    oof_probabilities: list[float] = []
    oof_labels: list[int] = []
    try:
        for fold_number, (train_indices, validation_indices) in enumerate(splitter.split(X_dev, y_dev), start=1):
            metrics, elapsed, predictor, audit = _autogluon_fit_and_score(
                X_dev.iloc[train_indices], X_dev.iloc[validation_indices],
                y_dev.iloc[train_indices], y_dev.iloc[validation_indices],
                output_dir / f"autogluon_cv_{fold_number}",
            )
            scores.append(metrics)
            fit_seconds.append(elapsed)
            fold_records.append({"repeat": ((fold_number - 1) // CV_SPLITS) + 1, "fold": ((fold_number - 1) % CV_SPLITS) + 1, "fit_seconds": round(elapsed, 6), **metrics})
            audits.append({"repeat": ((fold_number - 1) // CV_SPLITS) + 1, "fold": ((fold_number - 1) % CV_SPLITS) + 1, "status": "completed", **audit})
            raw_probabilities = predictor.predict_proba(X_dev.iloc[validation_indices])
            if hasattr(raw_probabilities, "columns"):
                raw_probabilities = raw_probabilities[POSITIVE_LABEL] if POSITIVE_LABEL in raw_probabilities.columns else raw_probabilities.iloc[:, 0]
            else:
                raw_probabilities = raw_probabilities[:, POSITIVE_LABEL]
            oof_probabilities.extend(np.asarray(raw_probabilities, dtype=float))
            oof_labels.extend(y_dev.iloc[validation_indices].tolist())
        return {
            "model": "autogluon_medium_quality",
            "backend": "autogluon",
            "evaluation_scope": "development_cv",
            "selection_protocol": f"{CV_REPEATS}x{CV_SPLITS}-fold repeated stratified CV",
            **_cv_summary(scores, fit_seconds),
            "decision_threshold": _select_threshold(oof_labels, oof_probabilities),
            "threshold_selection_scope": "development_cv_oof",
        }, None, audits, fold_records
    except Exception as exc:
        audits.append({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        return None, f"{type(exc).__name__}: {exc}", audits, fold_records


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

    cv_records: dict[str, list[dict[str, Any]]] = {}
    rows = []
    for name, model in sklearn_models().items():
        row, fold_records = cross_validate_model(name, model, X_dev, y_dev)
        rows.append(row)
        cv_records[name] = fold_records
    ag_note: str | None = "AutoGluon disabled by caller"
    ag_status = "disabled"
    ag_failure_type: str | None = None
    ag_audits: list[dict[str, Any]] = []
    ag_fold_records: list[dict[str, Any]] = []
    attempted_backend = ["sklearn"]
    if include_autogluon:
        attempted_backend.append("autogluon")
        ag_row, ag_note, ag_audits, ag_fold_records = _cross_validate_autogluon(X_dev, y_dev, output_path)
        if ag_row is not None:
            rows.append(ag_row)
            cv_records[ag_row["model"]] = ag_fold_records
            ag_status = "completed"
        else:
            ag_status = "unavailable" if ag_note == "autogluon.tabular is not installed" else "failed"
            ag_failure_type = "missing_dependency" if ag_status == "unavailable" else "runtime_error"

    leaderboard = pd.DataFrame(rows).sort_values(["cv_roc_auc_mean", "cv_accuracy_mean"], ascending=False, ignore_index=True)
    leaderboard.insert(0, "rank", range(1, len(leaderboard) + 1))
    leader_auc = float(leaderboard.iloc[0]["cv_roc_auc_mean"])
    leaderboard["cv_roc_auc_margin_to_leader"] = leader_auc - leaderboard["cv_roc_auc_mean"].astype(float)
    leaderboard["practically_tied"] = leaderboard["cv_roc_auc_margin_to_leader"] <= PRACTICAL_TIE_TOLERANCE
    leaderboard.to_csv(output_path / "leaderboard.csv", index=False)
    _write_json(output_path / "cv_scores.json", {
        "schema_version": 1,
        "evaluation_scope": "development_cv",
        "protocol": f"{CV_REPEATS}x{CV_SPLITS}-fold repeated stratified CV",
        "uncertainty": "Mean, sample standard deviation, and normal-approximation 95% CI across fold/repeat scores; final holdout is excluded.",
        "models": cv_records,
    })

    selected = leaderboard.iloc[0].to_dict()
    selected_name = str(selected["model"])
    selected_threshold = float(selected.get("decision_threshold", DEFAULT_THRESHOLD))
    final_started = time.perf_counter()
    if selected_name == "autogluon_medium_quality":
        final_row, final_note, final_audit = run_autogluon(
            X_dev, X_test, y_dev, y_test, output_path, threshold=selected_threshold
        )
        if final_row is None:
            raise RuntimeError(f"Selected AutoGluon model could not be evaluated on the final holdout: {final_note}")
        final_metrics = final_row
        ag_audits.append({"scope": "final_holdout_fit", "status": "completed", **(final_audit or {})})
    else:
        final_model = sklearn_models()[selected_name]
        final_model.fit(X_dev, y_dev)
        final_metrics = {
            "model": selected_name,
            "backend": "sklearn",
            **_predict_metrics(final_model, X_test, y_test, threshold=selected_threshold),
            "fit_seconds": round(time.perf_counter() - final_started, 4),
        }
    final_metrics.update({
        "evaluation_scope": "final_holdout",
        "selection_metric": "cv_roc_auc_mean",
        "selected_by": "development_cv",
        "final_test_samples": len(X_test),
        "decision_threshold": selected_threshold,
        "threshold_selection_scope": "development_cv_oof",
        "positive_class": {"label": POSITIVE_LABEL, "name": "malignant"},
        "uncertainty": "No confidence interval is reported for this single locked holdout evaluation.",
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
        "positive_class": {"label": POSITIVE_LABEL, "name": str(data.target_names[POSITIVE_LABEL])},
        "negative_class": {"label": NEGATIVE_LABEL, "name": str(data.target_names[NEGATIVE_LABEL])},
        "intended_use": "Prioritize detection of malignant cases; false negatives are the higher-cost error.",
        "error_costs": {"false_negative_positive_class": "high", "false_positive_positive_class": "moderate"},
        "selection_protocol": f"{CV_REPEATS}x{CV_SPLITS}-fold repeated stratified CV on development data",
        "final_evaluation_protocol": "Selected model refit on all development data; final holdout scored once",
        "threshold_protocol": "Each candidate threshold is selected from its development-only out-of-fold probabilities by malignant-class F1; the selected threshold is then locked for the final holdout.",
        "metric_semantics": {
            "roc_auc": "Probability ranking for malignant (label 0).",
            "pr_auc": "Average precision for malignant (label 0).",
            "sensitivity": "Recall of malignant cases at the reported threshold.",
            "specificity": "Recall of benign cases at the reported threshold.",
            "brier_score": "Mean squared probability error for malignant probability; lower is better.",
        },
    }
    _write_json(output_path / "dataset_summary.json", summary)

    metadata = {
        "schema_version": 3,
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "command": [sys.executable, *sys.argv],
        "backend": "autogluon_plus_sklearn" if ag_status == "completed" else "sklearn_fallback",
        "requested_backend": "autogluon_optional" if include_autogluon else "sklearn_only",
        "attempted_backend": attempted_backend,
        "backend_status": {"sklearn": "completed", "autogluon": ag_status},
        "failure_type": {"autogluon": ag_failure_type},
        "autogluon_note": ag_note,
        "autogluon_audit": ag_audits,
        "random_seed": SEED,
        "ranking_metric": "cv_roc_auc_mean",
        "selection_scope": "development_cv",
        "final_evaluation_scope": "final_holdout",
        "models": leaderboard["model"].tolist(),
        "selected_model": selected_name,
        "selected_decision_threshold": selected_threshold,
        "final_metrics_artifact": "final_metrics.json",
        "cv_scores_artifact": "cv_scores.json",
        "positive_class": {"label": POSITIVE_LABEL, "name": "malignant"},
        "negative_class": {"label": NEGATIVE_LABEL, "name": "benign"},
        "metric_semantics": {
            "ranking": "Development-CV ROC-AUC; higher is better.",
            "operating_point": "Malignant-positive thresholded metrics; threshold selected on development OOF predictions only.",
            "uncertainty": "Mean ± sample SD and normal-approximation 95% CI across the 10 development CV fold/repeat scores.",
            "practical_tie_tolerance": PRACTICAL_TIE_TOLERANCE,
        },
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
            "fit_time_note": "Wall-clock training time is environment-specific. sklearn values measure estimator fit; AutoGluon values include search and ensemble work, so fit time is not a cross-backend efficiency ranking.",
        },
    }
    _write_json(output_path / "metrics.json", metadata)
    return leaderboard
