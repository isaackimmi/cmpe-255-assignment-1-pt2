"""Leakage-safe, reproducible anomaly-detection experiment."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler


NORMAL_MEANS = (np.array([0.0, 0.0]), np.array([5.0, 4.0]))
NORMAL_COVARIANCES = (
    np.array([[1.0, 0.25], [0.25, 0.7]]),
    np.array([[1.4, -0.4], [-0.4, 0.8]]),
)
ANOMALY_CATEGORIES = ("global", "local", "cluster")
METHOD_NAMES = ("isolation_forest", "local_outlier_factor", "elliptic_envelope", "rank_ensemble")
DEFAULT_MODEL_CONTAMINATION = 0.10
DEFAULT_ALERT_BUDGET = 100
THRESHOLD_PERCENTILES = tuple(range(50, 96))
ALERT_BUDGETS = tuple(range(25, 201, 5))
STABILITY_SEEDS = (0, 7, 21, 42, 84)


def _sample_normal(rng: np.random.Generator, n: int) -> np.ndarray:
    first = n // 2 + n % 2
    second = n // 2
    return np.vstack([
        rng.multivariate_normal(NORMAL_MEANS[0], NORMAL_COVARIANCES[0], first),
        rng.multivariate_normal(NORMAL_MEANS[1], NORMAL_COVARIANCES[1], second),
    ])


def _normal_tail_distance(points: np.ndarray) -> np.ndarray:
    """Return squared Mahalanobis distance to the nearest normal component."""
    distances = []
    for mean, covariance in zip(NORMAL_MEANS, NORMAL_COVARIANCES):
        delta = points - mean
        distances.append(np.einsum("ij,jk,ik->i", delta, np.linalg.inv(covariance), delta))
    return np.min(np.column_stack(distances), axis=1)


def _sample_valid_anomalies(rng, sampler, n: int, minimum_tail_distance: float = 8.0) -> np.ndarray:
    """Reject candidates plausible under either declared normal cluster."""
    accepted: list[np.ndarray] = []
    remaining = n
    for _ in range(200):
        candidates = sampler(max(remaining * 4, 64))
        candidates = candidates[_normal_tail_distance(candidates) >= minimum_tail_distance]
        if len(candidates):
            accepted.append(candidates[:remaining])
            remaining -= min(remaining, len(candidates))
        if remaining == 0:
            return np.vstack(accepted)
    raise RuntimeError("Could not generate enough valid anomalies for the protocol")


def _make_anomalies(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    global_outliers = _sample_valid_anomalies(
        rng, lambda size: rng.uniform([-5.0, -4.0], [10.0, 9.0], size=(size, 2)), 35
    )
    # This is a compact fringe group, not a dense group inside a normal mode.
    local_outliers = _sample_valid_anomalies(
        rng, lambda size: rng.multivariate_normal([3.0, 0.0], [[0.08, 0.0], [0.0, 0.08]], size), 30
    )
    cluster_outliers = _sample_valid_anomalies(
        rng, lambda size: rng.multivariate_normal([7.2, 1.5], [[0.18, 0.05], [0.05, 0.18]], size), 35
    )
    return (
        np.vstack([global_outliers, local_outliers, cluster_outliers]),
        np.repeat(ANOMALY_CATEGORIES, [35, 30, 35]),
    )


def make_data(seed: int = 42) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a complete labeled benchmark view for inspection only."""
    rng = np.random.default_rng(seed)
    normal = _sample_normal(rng, 800)
    anomalies, anomaly_categories = _make_anomalies(rng)
    x = np.vstack([normal, anomalies])
    labels = np.r_[np.zeros(len(normal), dtype=int), np.ones(len(anomalies), dtype=int)]
    categories = np.r_[np.repeat("normal", len(normal)), anomaly_categories]
    order = rng.permutation(len(x))
    return x[order], labels[order], categories[order]


def make_protocol_data(seed: int = 42) -> dict[str, np.ndarray]:
    """Create clean train/calibration data and an untouched labeled holdout."""
    rng = np.random.default_rng(seed)
    train = _sample_normal(rng, 600)
    calibration = _sample_normal(rng, 200)
    test_normal = _sample_normal(rng, 200)
    anomalies, anomaly_categories = _make_anomalies(rng)
    test = np.vstack([test_normal, anomalies])
    labels = np.r_[np.zeros(len(test_normal), dtype=int), np.ones(len(anomalies), dtype=int)]
    categories = np.r_[np.repeat("normal", len(test_normal)), anomaly_categories]
    order = rng.permutation(len(test))
    return {
        "train": train,
        "calibration": calibration,
        "test": test[order],
        "labels": labels[order],
        "categories": categories[order],
    }


def _normalise(scores: np.ndarray) -> np.ndarray:
    lo, hi = np.min(scores), np.max(scores)
    return (scores - lo) / (hi - lo) if hi > lo else np.zeros_like(scores)


def _detectors(seed: int, model_contamination: float) -> dict[str, object]:
    """Build detectors with fixed, label-independent configuration."""
    return {
        "isolation_forest": IsolationForest(n_estimators=250, contamination="auto", random_state=seed),
        "local_outlier_factor": LocalOutlierFactor(n_neighbors=25, contamination="auto", novelty=True),
        "elliptic_envelope": EllipticEnvelope(
            contamination=model_contamination, random_state=seed, support_fraction=0.8
        ),
    }


def score_methods(
    train_x: np.ndarray,
    query_x: np.ndarray | None = None,
    seed: int = 42,
    model_contamination: float = DEFAULT_MODEL_CONTAMINATION,
) -> dict[str, np.ndarray]:
    """Fit on ``train_x`` only and return larger-is-more-anomalous query scores."""
    query_x = train_x if query_x is None else query_x
    scaler = StandardScaler().fit(train_x)
    train_scaled = scaler.transform(train_x)
    query_scaled = scaler.transform(query_x)
    scores: dict[str, np.ndarray] = {}
    reference_scores: dict[str, np.ndarray] = {}
    for name, detector in _detectors(seed, model_contamination).items():
        detector.fit(train_scaled)
        reference_scores[name] = -detector.score_samples(train_scaled)
        scores[name] = -detector.score_samples(query_scaled)

    # Rank ensemble uses clean training scores as its reference distribution.
    ranks = []
    for name in ("isolation_forest", "local_outlier_factor", "elliptic_envelope"):
        ranks.append(np.searchsorted(np.sort(reference_scores[name]), scores[name], side="right") / len(train_x))
    scores["rank_ensemble"] = np.column_stack(ranks).mean(axis=1)
    return scores


def calibrate_thresholds(calibration_scores: dict[str, np.ndarray], percentile: float = 0.95) -> dict[str, float]:
    """Select score cutoffs from clean calibration scores only."""
    if not 0 < percentile < 1:
        raise ValueError("percentile must be between 0 and 1")
    return {name: float(np.quantile(score, percentile)) for name, score in calibration_scores.items()}


def _top_k_predictions(score: np.ndarray, k: int) -> np.ndarray:
    k = max(1, min(int(k), len(score)))
    prediction = np.zeros(len(score), dtype=int)
    prediction[np.argsort(score, kind="stable")[-k:]] = 1
    return prediction


def _threshold_predictions(score: np.ndarray, threshold: float, budget: int | None = None) -> np.ndarray:
    prediction = score >= threshold
    if budget is not None and prediction.sum() > budget:
        candidates = np.flatnonzero(prediction)
        keep = candidates[np.argsort(score[candidates], kind="stable")[-budget:]]
        prediction = np.zeros(len(score), dtype=bool)
        prediction[keep] = True
    return prediction.astype(int)


def _classification_metrics(labels: np.ndarray, prediction: np.ndarray) -> dict[str, float | int]:
    return {
        "precision": float(precision_score(labels, prediction, zero_division=0)),
        "recall": float(recall_score(labels, prediction, zero_division=0)),
        "f1": float(f1_score(labels, prediction, zero_division=0)),
        "flagged": int(prediction.sum()),
    }


def evaluate(scores: dict[str, np.ndarray], labels: np.ndarray, alert_budget: int) -> dict:
    """Evaluate ranking and an explicit fixed review-queue budget on a holdout."""
    if alert_budget < 1:
        raise ValueError("alert_budget must be positive")
    result = {}
    for name, score in scores.items():
        point = _classification_metrics(labels, _top_k_predictions(score, alert_budget))
        result[name] = {
            "roc_auc": float(roc_auc_score(labels, score)),
            "average_precision": float(average_precision_score(labels, score)),
            "precision_at_k": point["precision"],
            "recall_at_k": point["recall"],
            "f1_at_k": point["f1"],
            "alert_budget": int(alert_budget),
            "flagged": point["flagged"],
        }
    return result


def _threshold_grid(calibration_scores, test_scores, labels):
    thresholds_by_method = {}
    operating_points = {}
    for name, calibration_score in calibration_scores.items():
        thresholds_by_method[name] = []
        operating_points[name] = {}
        for percentile in THRESHOLD_PERCENTILES:
            threshold = float(np.quantile(calibration_score, percentile / 100))
            unbounded = _classification_metrics(labels, _threshold_predictions(test_scores[name], threshold))
            thresholds_by_method[name].append({"percentile": percentile, "threshold": threshold, **unbounded})
            operating_points[name][str(percentile)] = {}
            for budget in ALERT_BUDGETS:
                prediction = _threshold_predictions(test_scores[name], threshold, budget)
                operating_points[name][str(percentile)][str(budget)] = _classification_metrics(labels, prediction)
    return thresholds_by_method, operating_points


def _category_recall(scores, categories: np.ndarray, alert_budget: int):
    result = {}
    for name, score in scores.items():
        flagged = _top_k_predictions(score, alert_budget).astype(bool)
        result[name] = {
            category: float(flagged[categories == category].mean()) for category in ANOMALY_CATEGORIES
        }
    return result


def _runtime_versions() -> dict[str, str]:
    packages = {"numpy": "numpy", "scikit_learn": "scikit-learn", "matplotlib": "matplotlib"}
    versions = {"python": platform.python_version()}
    for name, package in packages.items():
        try:
            versions[name] = version(package)
        except PackageNotFoundError:
            versions[name] = "unavailable"
    return versions


def _build_metrics_once(seed: int = 42) -> tuple[dict, dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Run one protocol draw in memory and return metrics plus plot inputs."""
    data = make_protocol_data(seed)
    calibration_scores = score_methods(data["train"], data["calibration"], seed)
    test_scores = score_methods(data["train"], data["test"], seed)
    metrics = evaluate(test_scores, data["labels"], DEFAULT_ALERT_BUDGET)
    threshold_points, operating_points = _threshold_grid(calibration_scores, test_scores, data["labels"])
    metrics["category_recall"] = _category_recall(test_scores, data["categories"], DEFAULT_ALERT_BUDGET)
    metrics["threshold_metrics"] = {
        name: next(point for point in points if point["percentile"] == 95)
        for name, points in threshold_points.items()
    }
    metrics["threshold_points"] = threshold_points
    metrics["operating_points"] = operating_points
    metrics["metadata"] = {
        "seed": seed,
        "protocol": "clean_train_clean_calibration_holdout",
        "train_size": int(len(data["train"])),
        "calibration_size": int(len(data["calibration"])),
        "test_size": int(len(data["test"])),
        "test_normal_count": int((data["labels"] == 0).sum()),
        "test_anomaly_count": int((data["labels"] == 1).sum()),
        "test_anomaly_rate": float(data["labels"].mean()),
        "alert_budget": DEFAULT_ALERT_BUDGET,
        "alert_budget_semantics": "oracle_budget_benchmark",
        "model_contamination": DEFAULT_MODEL_CONTAMINATION,
        "threshold_selection": "clean calibration score percentile",
        "ranking_metric": "roc_auc",
        "holdout_use": "offline diagnostic evaluation only; do not tune deployment thresholds here",
        "anomaly_acceptance": "nearest normal-component Mahalanobis distance squared >= 8",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runtime_versions": _runtime_versions(),
    }
    metrics["data_quality"] = {
        "anomaly_categories": {
            category: int((data["categories"] == category).sum()) for category in ANOMALY_CATEGORIES
        },
        "minimum_anomaly_tail_distance": float(_normal_tail_distance(data["test"][data["labels"] == 1]).min()),
    }
    return metrics, data, test_scores


def _stability_summary(seed: int, metrics: dict) -> dict:
    rows = []
    for repeat_seed in STABILITY_SEEDS:
        if repeat_seed == seed:
            repeat_metrics = metrics
        else:
            repeat_metrics, _, _ = _build_metrics_once(repeat_seed)
        rows.append({
            "seed": repeat_seed,
            "methods": {
                name: {
                    "roc_auc": repeat_metrics[name]["roc_auc"],
                    "average_precision": repeat_metrics[name]["average_precision"],
                    "f1_at_k": repeat_metrics[name]["f1_at_k"],
                    "category_recall": repeat_metrics["category_recall"][name],
                }
                for name in METHOD_NAMES
            },
        })

    summary = {}
    for name in METHOD_NAMES:
        summary[name] = {}
        for metric_name in ("roc_auc", "average_precision", "f1_at_k"):
            values = np.array([row["methods"][name][metric_name] for row in rows])
            summary[name][metric_name] = {
                "mean": float(values.mean()),
                "std": float(values.std(ddof=1)),
                "min": float(values.min()),
                "max": float(values.max()),
            }
        summary[name]["category_recall"] = {}
        for category in ANOMALY_CATEGORIES:
            values = np.array([row["methods"][name]["category_recall"][category] for row in rows])
            summary[name]["category_recall"][category] = {
                "mean": float(values.mean()),
                "std": float(values.std(ddof=1)),
                "min": float(values.min()),
                "max": float(values.max()),
            }
    return {"seeds": list(STABILITY_SEEDS), "runs": rows, "summary": summary}


def build_metrics(seed: int = 42) -> tuple[dict, dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Run the protocol in memory; stability summaries are added when writing artifacts."""
    return _build_metrics_once(seed)


def build_observations(data: dict[str, np.ndarray], scores: dict[str, np.ndarray]) -> list[dict]:
    """Serialize the holdout rows so the dashboard can inspect actual scores."""
    observations = []
    for index in range(len(data["test"])):
        observations.append({
            "id": f"holdout-{index + 1:03d}",
            "split": "holdout",
            "feature_1": float(data["test"][index, 0]),
            "feature_2": float(data["test"][index, 1]),
            "label": int(data["labels"][index]),
            "category": str(data["categories"][index]),
            "scores": {name: float(score[index]) for name, score in scores.items()},
        })
    return observations


def plot_results(x, labels, scores, output: Path, threshold_metrics: dict | None = None) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True)
    for ax, (name, score) in zip(axes.flat, scores.items()):
        sizes = 18 + 80 * _normalise(score)
        ax.scatter(x[labels == 0, 0], x[labels == 0, 1], s=sizes[labels == 0], c="#b8c4d6", alpha=.55, label="normal")
        ax.scatter(x[labels == 1, 0], x[labels == 1, 1], s=sizes[labels == 1], c=score[labels == 1], cmap="Reds", alpha=.9, edgecolor="black", linewidth=.25, label="holdout anomaly")
        annotation = ""
        if threshold_metrics and name in threshold_metrics:
            threshold = threshold_metrics[name]["threshold"]
            flagged = int((score >= threshold).sum())
            annotation = f"\n95% calibration cut · {flagged} unbounded flags"
        ax.set_title(name.replace("_", " ").title() + annotation, fontsize=10)
        ax.set_xlabel("feature 1")
        ax.set_ylabel("feature 2")
        colorbar = fig.colorbar(ax.collections[-1], ax=ax, fraction=.046, pad=.04)
        colorbar.set_label("anomaly score", fontsize=8)
    handles, labels_text = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels_text, loc="lower center", ncol=2)
    fig.suptitle("Holdout anomaly scores: larger markers are more suspicious", fontsize=15)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def run(output_dir: Path, seed: int = 42) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics, data, test_scores = build_metrics(seed)
    plot_results(
        data["test"], data["labels"], test_scores, output_dir / "anomaly_scores.png", metrics["threshold_metrics"]
    )
    (output_dir / "observations.json").write_text(json.dumps(build_observations(data, test_scores), indent=2) + "\n")
    metrics["stability"] = _stability_summary(seed, metrics)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    metrics = run(args.output_dir, args.seed)
    for name, values in metrics.items():
        if isinstance(values, dict) and "f1_at_k" in values:
            print(f"{name:22s} F1@K={values['f1_at_k']:.3f} AP={values['average_precision']:.3f}")


if __name__ == "__main__":
    main()
