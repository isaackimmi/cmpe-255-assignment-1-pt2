"""Reproducible anomaly-detection experiment on a labeled synthetic data set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler


def make_data(seed: int = 42) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return features, binary anomaly labels, and anomaly categories.

    The normal population has two unequal clusters. Anomalies include points far
    from both clusters (global), points in a dense cluster's fringe (local), and
    a compact shifted group (cluster). Categories make failure modes inspectable.
    """
    rng = np.random.default_rng(seed)
    normal_a = rng.multivariate_normal([0.0, 0.0], [[1.0, 0.25], [0.25, 0.7]], 500)
    normal_b = rng.multivariate_normal([5.0, 4.0], [[1.4, -0.4], [-0.4, 0.8]], 300)
    global_outliers = rng.uniform([-5.0, -4.0], [10.0, 9.0], size=(35, 2))
    local_outliers = rng.multivariate_normal([2.4, 0.0], [[0.08, 0.0], [0.0, 0.08]], 30)
    cluster_outliers = rng.multivariate_normal([7.2, 1.5], [[0.18, 0.05], [0.05, 0.18]], 35)
    x = np.vstack([normal_a, normal_b, global_outliers, local_outliers, cluster_outliers])
    labels = np.r_[np.zeros(800, dtype=int), np.ones(100, dtype=int)]
    categories = np.r_[
        np.repeat("normal", 800),
        np.repeat("global", 35),
        np.repeat("local", 30),
        np.repeat("cluster", 35),
    ]
    order = rng.permutation(len(x))
    return x[order], labels[order], categories[order]


def _normalise(scores: np.ndarray) -> np.ndarray:
    lo, hi = np.min(scores), np.max(scores)
    return (scores - lo) / (hi - lo) if hi > lo else np.zeros_like(scores)


def score_methods(x: np.ndarray, contamination: float = 100 / 900, seed: int = 42) -> dict[str, np.ndarray]:
    """Fit several detectors and return larger-is-more-anomalous scores."""
    x_scaled = StandardScaler().fit_transform(x)
    detectors = {
        "isolation_forest": IsolationForest(
            n_estimators=250, contamination=contamination, random_state=seed
        ),
        "local_outlier_factor": LocalOutlierFactor(
            n_neighbors=25, contamination=contamination
        ),
        "elliptic_envelope": EllipticEnvelope(
            contamination=contamination, random_state=seed, support_fraction=0.8
        ),
    }
    scores = {}
    for name, detector in detectors.items():
        detector.fit(x_scaled)
        # LOF deliberately has no score_samples method in training mode;
        # its fitted training scores are exposed as negative_outlier_factor_.
        raw_scores = (
            detector.negative_outlier_factor_
            if name == "local_outlier_factor"
            else detector.score_samples(x_scaled)
        )
        scores[name] = -raw_scores
    # Improvement: rank ensemble is less sensitive to detector score scales.
    ranks = np.column_stack([np.argsort(np.argsort(scores[name])) for name in detectors])
    scores["rank_ensemble"] = ranks.mean(axis=1) / (len(x) - 1)
    return scores


def evaluate(scores: dict[str, np.ndarray], labels: np.ndarray, contamination: float) -> dict:
    n_anomalies = max(1, int(round(contamination * len(labels))))
    result = {}
    for name, score in scores.items():
        pred = np.zeros(len(score), dtype=int)
        pred[np.argsort(score)[-n_anomalies:]] = 1
        result[name] = {
            "roc_auc": float(roc_auc_score(labels, score)),
            "average_precision": float(average_precision_score(labels, score)),
            "precision": float(precision_score(labels, pred, zero_division=0)),
            "recall": float(recall_score(labels, pred, zero_division=0)),
            "f1": float(f1_score(labels, pred, zero_division=0)),
            "flagged": int(pred.sum()),
        }
    return result


def plot_results(x: np.ndarray, labels: np.ndarray, scores: dict[str, np.ndarray], output: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True)
    for ax, (name, score) in zip(axes.flat, scores.items()):
        sizes = 18 + 80 * _normalise(score)
        ax.scatter(x[labels == 0, 0], x[labels == 0, 1], s=sizes[labels == 0], c="#b8c4d6", alpha=.55, label="normal")
        ax.scatter(x[labels == 1, 0], x[labels == 1, 1], s=sizes[labels == 1], c=score[labels == 1], cmap="Reds", alpha=.9, edgecolor="black", linewidth=.25, label="known anomaly")
        ax.set_title(name.replace("_", " ").title())
        ax.set_xlabel("feature 1"); ax.set_ylabel("feature 2")
    handles, labels_text = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels_text, loc="lower center", ncol=2)
    fig.suptitle("Anomaly scores: larger markers are more suspicious", fontsize=15)
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def run(output_dir: Path, seed: int = 42) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    x, labels, categories = make_data(seed)
    contamination = labels.mean()
    scores = score_methods(x, contamination, seed)
    metrics = evaluate(scores, labels, contamination)
    category_recall = {}
    for name, score in scores.items():
        flagged = np.zeros(len(score), dtype=bool)
        flagged[np.argsort(score)[-int(labels.sum()):]] = True
        category_recall[name] = {
            category: float(flagged[categories == category].mean())
            for category in ("global", "local", "cluster")
        }
    metrics["category_recall"] = category_recall
    plot_results(x, labels, scores, output_dir / "anomaly_scores.png")
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    metrics = run(args.output_dir, args.seed)
    for name, values in metrics.items():
        if isinstance(values, dict) and "f1" in values:
            print(f"{name:22s} F1={values['f1']:.3f} AP={values['average_precision']:.3f}")


if __name__ == "__main__":
    main()
