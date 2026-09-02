"""Run the reproducible Project 05 pipeline and write dashboard artifacts."""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from skills_lab import (  # noqa: E402
    classification_metrics,
    correlation,
    impute_numeric,
    kmeans,
    linear_regression,
    mean,
    regression_metrics,
    silhouette_score,
    standardize_points,
    svg_clusters,
    svg_scatter,
    train_test_split,
    unstandardize_points,
    load_clean,
)


ROOT = os.path.dirname(__file__)
SEED = 255
TEST_FRACTION = 0.30
CLUSTER_ITERATIONS = 100
CLUSTER_N_INIT = 20


def _r2(actual, predicted, baseline):
    total = sum((value - baseline) ** 2 for value in actual)
    residual = sum((value - guess) ** 2 for value, guess in zip(actual, predicted))
    return 1 - residual / total if total else 0.0


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_pipeline(root=ROOT):
    data_path = os.path.join(root, "data", "customer_health.csv")
    artifact_dir = os.path.join(root, "artifacts")
    os.makedirs(artifact_dir, exist_ok=True)

    # Validate and deduplicate first, while preserving missing values. No model
    # or imputer is allowed to see a future test partition at this point.
    raw_data, duplicates = load_clean(data_path, impute=False)
    analysis_data, full_imputation = impute_numeric(raw_data)

    # Regression: seeded shuffled holdout, feature imputer fit on train only,
    # and missing target rows excluded from the score rather than synthesized.
    regression_train_raw, regression_test_raw = train_test_split(raw_data, TEST_FRACTION, SEED)
    regression_train, train_feature_imputation = impute_numeric(regression_train_raw, regression_train_raw, ("tenure_months",))
    regression_test, test_feature_imputation = impute_numeric(regression_test_raw, regression_train_raw, ("tenure_months",))
    regression_fit = [row for row in regression_train if row["monthly_usage"] is not None]
    intercept, slope = linear_regression(
        [row["tenure_months"] for row in regression_fit],
        [row["monthly_usage"] for row in regression_fit],
    )
    scored_regression = [row for row in regression_test if row["monthly_usage"] is not None]
    regression_predictions = [
        {"customer_id": row["customer_id"], "tenure_months": row["tenure_months"], "actual_usage": row["monthly_usage"], "predicted_usage": round(intercept + slope * row["tenure_months"], 2)}
        for row in scored_regression
    ]
    regression_actual = [row["monthly_usage"] for row in scored_regression]
    regression_predicted = [intercept + slope * row["tenure_months"] for row in scored_regression]
    train_mean_usage = mean(row["monthly_usage"] for row in regression_fit)
    regression_result = {
        "feature": "tenure_months", "target": "monthly_usage", "evaluation": "single seeded shuffled holdout",
        "seed": SEED, "test_fraction": TEST_FRACTION, "train_rows": len(regression_fit),
        "train_candidate_rows": len(regression_train), "test_candidate_rows": len(regression_test), "scored_rows": len(scored_regression),
        "missing_train_targets_excluded": len(regression_train) - len(regression_fit),
        "missing_test_targets_excluded": len(regression_test) - len(scored_regression),
        "train_feature_imputed": train_feature_imputation["counts"],
        "test_feature_imputed": test_feature_imputation["counts"],
        **regression_metrics(regression_actual, regression_predicted),
        "r2": _r2(regression_actual, regression_predicted, train_mean_usage),
        "mean_baseline_mae": regression_metrics(regression_actual, [train_mean_usage] * len(regression_actual))["mae"],
        "mean_baseline_rmse": regression_metrics(regression_actual, [train_mean_usage] * len(regression_actual))["rmse"],
    }

    # Classification: fixed rule evaluated once on a stratified holdout. The
    # threshold is a domain rule, not a parameter tuned against this fixture.
    classification_train_raw, classification_test_raw = train_test_split(raw_data, TEST_FRACTION, SEED, stratify="renewed")
    classification_train, classification_train_imputation = impute_numeric(classification_train_raw, classification_train_raw, ("monthly_usage", "support_tickets"))
    classification_test, classification_test_imputation = impute_numeric(classification_test_raw, classification_train_raw, ("monthly_usage", "support_tickets"))
    threshold = 45
    predicted_test = [int(row["monthly_usage"] >= threshold and row["support_tickets"] <= 2) for row in classification_test]
    actual_test = [row["renewed"] for row in classification_test]
    majority_class = int(mean(row["renewed"] for row in classification_train) >= 0.5)
    classification_result = {
        "evaluation": "single seeded stratified holdout", "seed": SEED, "test_fraction": TEST_FRACTION,
        "train_rows": len(classification_train), "test_rows": len(classification_test),
        "rule": "usage >= 45 and support_tickets <= 2", "threshold": threshold,
        "threshold_source": "fixed domain rule; not tuned on this fixture",
        "train_feature_imputed": classification_train_imputation["counts"],
        "test_feature_imputed": classification_test_imputation["counts"],
        **classification_metrics(actual_test, predicted_test),
        "majority_baseline_class": majority_class,
        "majority_baseline_accuracy": classification_metrics(actual_test, [majority_class] * len(actual_test))["accuracy"],
    }

    # EDA is descriptive and uses only observed usage values for correlations.
    observed_usage = [row for row in raw_data if row["monthly_usage"] is not None]
    usage_values = [row["monthly_usage"] for row in observed_usage]
    renewal_values = [row["renewed"] for row in observed_usage]
    ticket_values = [row["support_tickets"] for row in observed_usage]

    # Clustering is descriptive, so its z-score parameters are fit on all
    # validated clean rows after explicit imputation. Multiple initializations
    # and candidate-k diagnostics make the chosen k inspectable.
    points = [[row["monthly_usage"], row["support_tickets"]] for row in analysis_data]
    scaled_points, scaling = standardize_points(points)
    candidate_k = list(range(1, min(4, len(scaled_points)) + 1))
    candidates = []
    for k in candidate_k:
        candidate_labels, _, candidate_meta = kmeans(scaled_points, k=k, seed=SEED, iterations=CLUSTER_ITERATIONS, n_init=CLUSTER_N_INIT, return_metadata=True)
        candidates.append({"k": k, "inertia": candidate_meta["inertia"], "silhouette": silhouette_score(scaled_points, candidate_labels), "n_init": CLUSTER_N_INIT, "converged": candidate_meta["converged"], "initialization_inertia_range": [min(candidate_meta["initialization_inertias"]), max(candidate_meta["initialization_inertias"])]})
    selected_k = max(candidates[1:], key=lambda candidate: (candidate["silhouette"], -candidate["k"]))["k"]
    labels, scaled_centers, cluster_meta = kmeans(scaled_points, k=selected_k, seed=SEED, iterations=CLUSTER_ITERATIONS, n_init=CLUSTER_N_INIT, return_metadata=True)
    centers = unstandardize_points(scaled_centers, scaling)

    raw_rows = len(raw_data) + duplicates
    missing_by_column = {column: sum(row[column] is None for row in raw_data) for column in ("tenure_months", "monthly_usage", "support_tickets")}
    metrics = {
        "data_quality": {
            "raw_rows": raw_rows, "clean_rows": len(raw_data), "duplicates_removed": duplicates,
            "missing_values_by_column": missing_by_column, "missing_values_imputed": sum(full_imputation["counts"].values()),
            "validation": "schema, finite numeric values, nonnegative domains, known plans, binary labels, and identical-duplicate policy",
        },
        "eda": {
            "usage_mean_observed": mean(usage_values), "observed_usage_rows": len(observed_usage),
            "usage_renewal_correlation": correlation(usage_values, renewal_values),
            "usage_ticket_correlation": correlation(usage_values, ticket_values),
            "interpretation": "descriptive association, not causal evidence",
        },
        "regression": regression_result,
        "classification": classification_result,
        "clustering": {
            "k": selected_k, "selection": "highest silhouette among candidate k values 1-4", "features": ["monthly_usage", "support_tickets"], "scaling": "z-score, fit on all clean rows for descriptive clustering",
            "cluster_sizes": [labels.count(index) for index in range(selected_k)], "centers": centers,
            "scaled_centers": scaled_centers, "inertia": cluster_meta["inertia"], "silhouette": silhouette_score(scaled_points, labels),
            "converged": cluster_meta["converged"], "iterations": cluster_meta["iterations"], "n_init": CLUSTER_N_INIT,
            "initialization_inertia_range": [min(cluster_meta["initialization_inertias"]), max(cluster_meta["initialization_inertias"])],
            "candidate_k": candidates,
        },
        "reproducibility": {"seed": SEED, "test_fraction": TEST_FRACTION, "cluster_iterations": CLUSTER_ITERATIONS, "cluster_n_init": CLUSTER_N_INIT, "input_sha256": _sha256(data_path)},
    }
    summary = {
        "rows": raw_data,
        "analysis_rows": [dict(row, cluster=labels[index]) for index, row in enumerate(analysis_data)],
        "imputation": {"scope": "all clean rows for descriptive outputs", "medians": full_imputation["medians"], "counts": full_imputation["counts"]},
        "regression_predictions": regression_predictions,
        "regression_excluded_test_targets": [{"customer_id": row["customer_id"], "reason": "monthly_usage is missing; target was not imputed for scoring"} for row in regression_test if row["monthly_usage"] is None],
    }
    with open(os.path.join(artifact_dir, "metrics.json"), "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    with open(os.path.join(artifact_dir, "summary.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    svg_scatter(analysis_data, os.path.join(artifact_dir, "tenure_usage.svg"))
    svg_clusters(points, labels, centers, os.path.join(artifact_dir, "customer_clusters.svg"))
    return metrics, summary


if __name__ == "__main__":
    metrics, _ = run_pipeline()
    print(json.dumps(metrics, indent=2))
