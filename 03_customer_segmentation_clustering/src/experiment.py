"""Reproducible customer segmentation experiment (Project 03)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

SEED = 255
FEATURES = ["annual_income_k", "spend_score", "purchase_frequency", "avg_order_value"]


def make_dataset(n_per_segment: int = 40, seed: int = SEED) -> pd.DataFrame:
    """Create a documented, toy retail sample with three business segments."""
    rng = np.random.default_rng(seed)
    centers = np.array([[35, 28, 2.2, 24], [72, 78, 7.0, 68], [105, 48, 3.8, 118]])
    scales = np.array([[7, 8, .65, 7], [10, 9, 1.0, 12], [13, 9, .8, 16]])
    chunks = [rng.normal(center, scale, size=(n_per_segment, 4))
              for center, scale in zip(centers, scales)]
    data = np.vstack(chunks)
    data[:, 0] = np.clip(data[:, 0], 15, None)
    data[:, 1] = np.clip(data[:, 1], 1, 99)
    data[:, 2] = np.clip(data[:, 2], .2, None)
    data[:, 3] = np.clip(data[:, 3], 5, None)
    return pd.DataFrame(data, columns=FEATURES).round(3)


def _transform(df: pd.DataFrame, improved: bool) -> np.ndarray:
    values = df[FEATURES].to_numpy()
    # The improvement reduces the influence of the right-skewed monetary fields.
    if improved:
        values = values.copy()
        values[:, [0, 3]] = np.log1p(values[:, [0, 3]])
    return StandardScaler().fit_transform(values)


def evaluate_k(data: np.ndarray, k_values=range(2, 8)) -> pd.DataFrame:
    rows = []
    for k in k_values:
        labels = KMeans(n_clusters=k, random_state=SEED, n_init=25).fit_predict(data)
        rows.append({"k": k, "silhouette": silhouette_score(data, labels),
                     "calinski_harabasz": calinski_harabasz_score(data, labels),
                     "davies_bouldin": davies_bouldin_score(data, labels)})
    return pd.DataFrame(rows)


def run(output_dir: str | Path = "artifacts") -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = make_dataset()
    baseline = _transform(raw, improved=False)
    improved = _transform(raw, improved=True)
    baseline_scores = evaluate_k(baseline)
    improved_scores = evaluate_k(improved)
    best_row = improved_scores.loc[improved_scores["silhouette"].idxmax()]
    k = int(best_row["k"])
    labels = KMeans(n_clusters=k, random_state=SEED, n_init=25).fit_predict(improved)
    raw.assign(cluster=labels).to_csv(out / "customer_segments.csv", index=False)
    baseline_scores.to_csv(out / "baseline_scores.csv", index=False)
    improved_scores.to_csv(out / "improved_scores.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(baseline_scores.k, baseline_scores.silhouette, marker="o", label="standard")
    axes[0].plot(improved_scores.k, improved_scores.silhouette, marker="o", label="log1p + standard")
    axes[0].set(xlabel="Number of clusters (k)", ylabel="Silhouette", title="Cluster selection")
    axes[0].legend()
    embedding = PCA(n_components=2, random_state=SEED).fit_transform(improved)
    axes[1].scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap="viridis", s=24)
    axes[1].set(title=f"Customer map (k={k})", xlabel="PC1", ylabel="PC2")
    fig.tight_layout()
    fig.savefig(out / "segmentation.png", dpi=160)
    plt.close(fig)
    summary = {"seed": SEED, "n_customers": len(raw), "selected_k": k,
               "silhouette": float(best_row["silhouette"]),
               "calinski_harabasz": float(best_row["calinski_harabasz"]),
               "davies_bouldin": float(best_row["davies_bouldin"]),
               "features": FEATURES, "preprocessing": "log1p income/AOV then StandardScaler"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
