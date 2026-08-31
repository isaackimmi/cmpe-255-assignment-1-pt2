"""Reproducible customer segmentation experiment (Project 03).

The data is intentionally synthetic, so the experiment reports internal
metrics as descriptive diagnostics and uses repeated train/validation splits
plus partition stability for exploratory model selection. Neither protocol
is a substitute for validation on observed customer outcomes.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, silhouette_score)
from sklearn.model_selection import ShuffleSplit
from sklearn.preprocessing import StandardScaler

SEED = 255
FEATURES = ["annual_income_k", "spend_score", "purchase_frequency", "avg_order_value"]
CANDIDATE_K_VALUES = tuple(range(2, 8))
VALIDATION_REPEATS = 12
TRAIN_FRACTION = 0.8
VARIANTS = ("standard", "log1p")
EXPLORER_COLUMNS = [
    "customer_id", *FEATURES, "cluster", "pca_x", "pca_y",
    "centroid_distance", "assignment_margin", "assignment_confidence",
    "uncertainty_label",
]
DOMAIN_BOUNDS = {
    "annual_income_k": (15, None),
    "spend_score": (1, 99),
    "purchase_frequency": (0.2, None),
    "avg_order_value": (5, None),
}


def make_dataset(n_per_segment: int = 40, seed: int = SEED) -> pd.DataFrame:
    """Create a documented, toy retail sample with three business segments."""
    if n_per_segment < 2:
        raise ValueError("n_per_segment must be at least 2")
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


def validate_dataset(df: pd.DataFrame) -> dict:
    """Validate the small data contract used by preprocessing and scoring."""
    errors: list[str] = []
    missing_columns = [feature for feature in FEATURES if feature not in df.columns]
    if missing_columns:
        errors.append(f"missing required columns: {missing_columns}")
    if df.empty:
        errors.append("dataset is empty")
    if not missing_columns:
        values = df[FEATURES]
        non_numeric = [feature for feature in FEATURES
                       if not pd.api.types.is_numeric_dtype(values[feature])]
        if non_numeric:
            errors.append(f"non-numeric features: {non_numeric}")
        else:
            missing_values = int(values.isna().sum().sum())
            nonfinite_values = int((~np.isfinite(values.to_numpy())).sum())
            if missing_values:
                errors.append(f"missing values: {missing_values}")
            if nonfinite_values:
                errors.append(f"non-finite values: {nonfinite_values}")
    range_violations = {}
    if not missing_columns and not errors:
        for feature, (lower, upper) in DOMAIN_BOUNDS.items():
            values = df[feature]
            invalid = (values < lower) if upper is None else ((values < lower) | (values > upper))
            range_violations[feature] = int(invalid.sum())
    return {
        "valid": not errors,
        "errors": errors,
        "n_rows": int(len(df)),
        "feature_schema": FEATURES,
        "missing_values": int(df[FEATURES].isna().sum().sum()) if not missing_columns else None,
        "duplicate_rows": int(df.duplicated().sum()),
        "range_violations": range_violations,
    }


def feature_audit(df: pd.DataFrame) -> dict:
    """Summarize scale, skew, IQR outliers, and redundancy for the toy input."""
    report = validate_dataset(df)
    if not report["valid"]:
        raise ValueError("Invalid dataset: " + "; ".join(report["errors"]))
    features = {}
    for feature in FEATURES:
        values = df[feature]
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        outliers = (values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)
        features[feature] = {
            "min": float(values.min()), "max": float(values.max()),
            "mean": float(values.mean()), "std": float(values.std(ddof=1)),
            "skew": float(values.skew()), "iqr_outliers": int(outliers.sum()),
        }
    return {"features": features, "correlation": df[FEATURES].corr().round(4).to_dict()}


def _raw_values(df: pd.DataFrame, preprocessing: str) -> np.ndarray:
    if preprocessing not in VARIANTS:
        raise ValueError(f"preprocessing must be one of {VARIANTS}, got {preprocessing!r}")
    values = df[FEATURES].to_numpy(dtype=float)
    if preprocessing == "log1p":
        if (values[:, [0, 3]] < 0).any():
            raise ValueError("log1p preprocessing requires non-negative monetary features")
        values = values.copy()
        values[:, [0, 3]] = np.log1p(values[:, [0, 3]])
    return values


def _transform(df: pd.DataFrame, improved: bool = False) -> np.ndarray:
    """Transform a complete frame; retained for the original teaching API."""
    preprocessing = "log1p" if improved else "standard"
    report = validate_dataset(df)
    if not report["valid"]:
        raise ValueError("Invalid dataset: " + "; ".join(report["errors"]))
    return StandardScaler().fit_transform(_raw_values(df, preprocessing))


def _fit_transformer(df: pd.DataFrame, preprocessing: str) -> StandardScaler:
    return StandardScaler().fit(_raw_values(df, preprocessing))


def _fit_kmeans(data: np.ndarray, k: int, random_state: int = SEED) -> KMeans:
    if k < 2 or k >= len(data):
        raise ValueError("k must be at least 2 and smaller than the number of rows")
    return KMeans(n_clusters=k, random_state=random_state, n_init=25).fit(data)


def _metrics(data: np.ndarray, labels: np.ndarray) -> dict:
    if len(np.unique(labels)) < 2:
        return {"silhouette": np.nan, "calinski_harabasz": np.nan, "davies_bouldin": np.nan}
    return {
        "silhouette": float(silhouette_score(data, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(data, labels)),
        "davies_bouldin": float(davies_bouldin_score(data, labels)),
    }


def evaluate_k(data: np.ndarray, k_values=CANDIDATE_K_VALUES) -> pd.DataFrame:
    """Compute descriptive full-sample metrics for each predeclared k."""
    rows = []
    for k in k_values:
        labels = _fit_kmeans(data, int(k)).labels_
        rows.append({"k": int(k), **_metrics(data, labels)})
    return pd.DataFrame(rows)


def evaluate_validation(df: pd.DataFrame, preprocessing: str = "standard",
                         k_values=CANDIDATE_K_VALUES, repeats: int = VALIDATION_REPEATS,
                         train_fraction: float = TRAIN_FRACTION, seed: int = SEED) -> pd.DataFrame:
    """Evaluate candidates on held-out rows and compare their partitions.

    Each repeat fits the scaler and K-Means on a training subset only. Metrics
    are calculated on the held-out rows. Stability is the pairwise adjusted
    Rand index of predictions for all rows from the repeated fitted models;
    ARI handles arbitrary cluster-label permutations.
    """
    report = validate_dataset(df)
    if not report["valid"]:
        raise ValueError("Invalid dataset: " + "; ".join(report["errors"]))
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    splitter = ShuffleSplit(n_splits=repeats, train_size=train_fraction, random_state=seed)
    values = _raw_values(df, preprocessing)
    metric_rows: list[dict] = []
    all_predictions: dict[int, list[np.ndarray]] = {int(k): [] for k in k_values}
    for repeat_index, (train_index, holdout_index) in enumerate(splitter.split(values)):
        scaler = StandardScaler().fit(values[train_index])
        train_values = scaler.transform(values[train_index])
        holdout_values = scaler.transform(values[holdout_index])
        all_values = scaler.transform(values)
        for k in k_values:
            model = _fit_kmeans(train_values, int(k), random_state=seed + repeat_index)
            holdout_labels = model.predict(holdout_values)
            all_predictions[int(k)].append(model.predict(all_values))
            metric_rows.append({
                "preprocessing": preprocessing,
                "k": int(k),
                "repeat": repeat_index + 1,
                **_metrics(holdout_values, holdout_labels),
            })
    metrics = pd.DataFrame(metric_rows)
    summary_rows = []
    for k in map(int, k_values):
        subset = metrics[metrics["k"] == k]
        aris = [adjusted_rand_score(left, right)
                for left, right in combinations(all_predictions[k], 2)]
        summary_rows.append({
            "preprocessing": preprocessing,
            "k": k,
            "validation_repeats": repeats,
            "train_fraction": train_fraction,
            "silhouette_mean": float(subset["silhouette"].mean()),
            "silhouette_std": float(subset["silhouette"].std(ddof=1)),
            "calinski_harabasz_mean": float(subset["calinski_harabasz"].mean()),
            "calinski_harabasz_std": float(subset["calinski_harabasz"].std(ddof=1)),
            "davies_bouldin_mean": float(subset["davies_bouldin"].mean()),
            "davies_bouldin_std": float(subset["davies_bouldin"].std(ddof=1)),
            "stability_ari_mean": float(np.mean(aris)),
            "stability_ari_std": float(np.std(aris, ddof=1)),
            "stability_ari_min": float(np.min(aris)),
        })
    return pd.DataFrame(summary_rows)


def fit_segmenter(df: pd.DataFrame, preprocessing: str, k: int,
                   random_state: int = SEED) -> dict:
    """Fit the preprocessing and K-Means model together for later scoring."""
    report = validate_dataset(df)
    if not report["valid"]:
        raise ValueError("Invalid dataset: " + "; ".join(report["errors"]))
    scaler = _fit_transformer(df, preprocessing)
    model = _fit_kmeans(scaler.transform(_raw_values(df, preprocessing)), k, random_state)
    return {"preprocessing": preprocessing, "scaler": scaler, "model": model}


def score_customers(df: pd.DataFrame, fitted: dict) -> pd.Series:
    """Assign new customers using the exact fitted preprocessing and model."""
    report = validate_dataset(df)
    if not report["valid"]:
        raise ValueError("Invalid dataset: " + "; ".join(report["errors"]))
    transformed = fitted["scaler"].transform(_raw_values(df, fitted["preprocessing"]))
    return pd.Series(fitted["model"].predict(transformed), index=df.index, name="cluster")


def _explorer_points(raw: pd.DataFrame, values: np.ndarray, model: KMeans,
                     embedding: np.ndarray) -> pd.DataFrame:
    """Create browser-safe point diagnostics for the selected fitted run.

    Distance and margin are unitless geometry diagnostics in the fitted,
    scaled feature space. They are not calibrated assignment probabilities.
    """
    distances = model.transform(values)
    nearest = distances.min(axis=1)
    runner_up = np.partition(distances, 1, axis=1)[:, 1]
    margin = runner_up - nearest
    confidence = np.clip(1 - nearest / np.maximum(runner_up, 1e-12), 0, 1)
    labels = np.where(confidence >= 0.55, "clear",
                      np.where(confidence >= 0.30, "moderate", "ambiguous"))
    points = raw.copy()
    points.insert(0, "customer_id", [f"C{index:03d}" for index in range(1, len(raw) + 1)])
    points["cluster"] = model.labels_.astype(int)
    points["pca_x"] = embedding[:, 0]
    points["pca_y"] = embedding[:, 1]
    points["centroid_distance"] = nearest
    points["assignment_margin"] = margin
    points["assignment_confidence"] = confidence
    points["uncertainty_label"] = labels
    return points[EXPLORER_COLUMNS]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def validate_artifacts(output_dir: str | Path = "artifacts", require_manifest: bool = True) -> dict:
    """Validate artifact schemas, metric agreement, and manifest hashes."""
    out = Path(output_dir)
    errors: list[str] = []
    required = ["summary.json", "baseline_scores.csv", "log1p_scores.csv",
                "validation_scores.csv", "customer_segments.csv", "explorer_points.csv",
                "segmentation.png"]
    missing = [name for name in required if not (out / name).exists()]
    if missing:
        errors.append(f"missing artifacts: {missing}")
        return {"valid": False, "errors": errors}
    try:
        summary = json.loads((out / "summary.json").read_text())
        assignments = pd.read_csv(out / "customer_segments.csv")
        explorer = pd.read_csv(out / "explorer_points.csv")
        validation = pd.read_csv(out / "validation_scores.csv")
        scores = {name: pd.read_csv(out / name) for name in ("baseline_scores.csv", "log1p_scores.csv")}
        expected_columns = FEATURES + ["cluster"]
        if assignments.columns.tolist() != expected_columns:
            errors.append(f"assignment schema mismatch: {assignments.columns.tolist()}")
        if len(assignments) != summary.get("n_customers"):
            errors.append("assignment row count disagrees with summary")
        if assignments[FEATURES].isna().any().any() or not np.isfinite(assignments[FEATURES].to_numpy()).all():
            errors.append("assignment features contain missing or non-finite values")
        if explorer.columns.tolist() != EXPLORER_COLUMNS:
            errors.append(f"explorer schema mismatch: {explorer.columns.tolist()}")
        if len(explorer) != len(assignments):
            errors.append("explorer row count disagrees with assignments")
        if len(explorer) and explorer["customer_id"].tolist() != [f"C{index:03d}" for index in range(1, len(explorer) + 1)]:
            errors.append("explorer customer IDs are not deterministic")
        numeric_explorer = [column for column in EXPLORER_COLUMNS if column not in {"customer_id", "uncertainty_label"}]
        if explorer[numeric_explorer].isna().any().any() or not np.isfinite(explorer[numeric_explorer].to_numpy()).all():
            errors.append("explorer diagnostics contain missing or non-finite values")
        if not set(explorer["uncertainty_label"].dropna()).issubset({"clear", "moderate", "ambiguous"}):
            errors.append("explorer uncertainty labels are invalid")
        if not assignments["cluster"].equals(explorer["cluster"]):
            errors.append("explorer clusters disagree with assignments")
        clusters = sorted(assignments["cluster"].dropna().unique().tolist())
        expected_clusters = list(range(int(summary["selected_k"])))
        if clusters != expected_clusters:
            errors.append(f"cluster labels mismatch: expected {expected_clusters}, got {clusters}")
        for name, frame in scores.items():
            if frame["k"].tolist() != list(CANDIDATE_K_VALUES):
                errors.append(f"{name} does not contain the predeclared candidate k values")
            if not np.isfinite(frame.drop(columns=["k"]).to_numpy()).all():
                errors.append(f"{name} contains non-finite metrics")
        if set(validation["preprocessing"]) != set(VARIANTS):
            errors.append("validation scores do not contain both preprocessing variants")
        selected = validation[(validation["preprocessing"] == summary["selected_preprocessing"])
                              & (validation["k"] == summary["selected_k"])]
        if len(selected) != 1:
            errors.append("summary selected model is absent from validation scores")
        else:
            selected_row = selected.iloc[0]
            for key in ("silhouette_mean", "stability_ari_mean", "stability_ari_min"):
                if not np.isclose(selected_row[key], summary["validation"][key]):
                    errors.append(f"summary validation.{key} disagrees with validation_scores.csv")
        transformed = _transform(assignments, summary["selected_preprocessing"] == "log1p")
        fit_metrics = _metrics(transformed, assignments["cluster"].to_numpy())
        for key, value in fit_metrics.items():
            if not np.isclose(value, summary["fit_metrics"][key]):
                errors.append(f"summary fit_metrics.{key} disagrees with assignments")
        manifest_path = out / "manifest.json"
        if require_manifest and not manifest_path.exists():
            errors.append("manifest.json is missing")
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            expected_hash_names = {"summary.json", "baseline_scores.csv", "log1p_scores.csv",
                                   "validation_scores.csv", "customer_segments.csv", "explorer_points.csv",
                                   "segmentation.png"}
            if (manifest.get("manifest_version") != 2
                    or manifest.get("selected_k") != summary.get("selected_k")
                    or manifest.get("n_customers") != summary.get("n_customers")
                    or manifest.get("selected_preprocessing") != summary.get("selected_preprocessing")
                    or manifest.get("features") != summary.get("features")
                    or set(manifest.get("hashes", {})) != expected_hash_names):
                errors.append("manifest metadata disagrees with summary")
            for name, expected_hash in manifest.get("hashes", {}).items():
                path = out / name
                if not path.exists() or _sha256(path) != expected_hash:
                    errors.append(f"manifest hash mismatch: {name}")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"artifact parse/consistency error: {exc}")
    return {"valid": not errors, "errors": errors}


def run(output_dir: str | Path = "artifacts") -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = make_dataset()
    data_quality = validate_dataset(raw)
    if not data_quality["valid"]:
        raise ValueError("Generated dataset failed validation")
    data_quality["feature_audit"] = feature_audit(raw)

    baseline = _transform(raw, improved=False)
    log1p = _transform(raw, improved=True)
    baseline_scores = evaluate_k(baseline)
    log1p_scores = evaluate_k(log1p)
    validation_scores = pd.concat([
        evaluate_validation(raw, variant) for variant in VARIANTS
    ], ignore_index=True)
    selected_row = validation_scores.sort_values(
        ["silhouette_mean", "stability_ari_mean", "stability_ari_min", "k"],
        ascending=[False, False, False, True],
    ).iloc[0]
    selected_preprocessing = str(selected_row["preprocessing"])
    selected_k = int(selected_row["k"])
    final_values = _transform(raw, improved=selected_preprocessing == "log1p")
    final_model = _fit_kmeans(final_values, selected_k)
    fit_metrics = _metrics(final_values, final_model.labels_)
    pca = PCA(n_components=2, random_state=SEED).fit(final_values)
    embedding = pca.transform(final_values)
    explorer_points = _explorer_points(raw, final_values, final_model, embedding)

    raw.assign(cluster=final_model.labels_).to_csv(out / "customer_segments.csv", index=False)
    explorer_points.to_csv(out / "explorer_points.csv", index=False)
    baseline_scores.to_csv(out / "baseline_scores.csv", index=False)
    log1p_scores.to_csv(out / "log1p_scores.csv", index=False)
    validation_scores.to_csv(out / "validation_scores.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for variant, label in (("standard", "StandardScaler"), ("log1p", "log1p + StandardScaler")):
        subset = validation_scores[validation_scores["preprocessing"] == variant]
        axes[0].errorbar(subset.k, subset.silhouette_mean, yerr=subset.silhouette_std,
                         marker="o", capsize=3, label=label)
    axes[0].set(xlabel="Number of clusters (k)", ylabel="Held-out silhouette",
                title="Exploratory validation")
    axes[0].legend()
    axes[1].scatter(embedding[:, 0], embedding[:, 1], c=final_model.labels_, cmap="viridis", s=24)
    axes[1].set(title=f"PCA projection only (k={selected_k})",
                xlabel="PC1 · visualization only", ylabel="PC2 · visualization only")
    fig.tight_layout()
    fig.savefig(out / "segmentation.png", dpi=160)
    plt.close(fig)

    selected_validation = selected_row.to_dict()
    for key, value in list(selected_validation.items()):
        if isinstance(value, (np.integer, np.floating)):
            selected_validation[key] = value.item()
    summary = {
        "seed": SEED,
        "n_customers": len(raw),
        "selected_k": selected_k,
        "selected_preprocessing": selected_preprocessing,
        "silhouette": fit_metrics["silhouette"],
        "calinski_harabasz": fit_metrics["calinski_harabasz"],
        "davies_bouldin": fit_metrics["davies_bouldin"],
        "fit_metrics": fit_metrics,
        "validation": selected_validation,
        "features": FEATURES,
        "preprocessing": "selected by repeated held-out validation; compare standard and log1p variants",
        "selection": {
            "candidate_k": list(CANDIDATE_K_VALUES),
            "criterion": "highest mean held-out silhouette; stability ARI and lower k are tie-breakers",
            "repeats": VALIDATION_REPEATS,
            "train_fraction": TRAIN_FRACTION,
            "note": "Exploratory internal validation on synthetic data; not evidence of future customer performance.",
        },
        "data_quality": data_quality,
        "generator": {"name": "three Gaussian prototype chunks", "n_per_segment": 40, "seed": SEED,
                      "interpretation": "prototype recovery teaching sample; not observed customer behavior"},
        "projection": {
            "method": "PCA",
            "components": ["pca_x", "pca_y"],
            "explained_variance_ratio": [float(value) for value in pca.explained_variance_ratio_],
            "use": "visualization-only projection of the four fitted feature dimensions",
        },
        "assignment_diagnostics": {
            "distance": "nearest centroid distance in fitted StandardScaler/log1p + StandardScaler space",
            "margin": "runner-up centroid distance minus nearest centroid distance",
            "confidence": "1 - nearest distance / runner-up distance; geometry proxy, not a probability",
            "labels": {"clear": ">= 0.55", "moderate": "0.30 to < 0.55", "ambiguous": "< 0.30"},
        },
        "provenance": {
            "source_sha256": _sha256(Path(__file__)),
            "python": sys.version.split()[0],
            "packages": {name: _version(name) for name in ("numpy", "pandas", "scikit-learn", "matplotlib")},
            "scoring_path": "src.experiment.fit_segmenter + score_customers",
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    hashed_names = ["summary.json", "baseline_scores.csv", "log1p_scores.csv",
                    "validation_scores.csv", "customer_segments.csv", "explorer_points.csv",
                    "segmentation.png"]
    manifest = {
        "manifest_version": 2,
        "n_customers": len(raw),
        "features": FEATURES,
        "selected_k": selected_k,
        "selected_preprocessing": selected_preprocessing,
        "hashes": {name: _sha256(out / name) for name in hashed_names},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    validation = validate_artifacts(out)
    if not validation["valid"]:
        raise RuntimeError("Generated artifacts failed validation: " + "; ".join(validation["errors"]))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
