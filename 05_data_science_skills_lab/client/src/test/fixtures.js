export const metrics = {
  data_quality: { raw_rows: 24, clean_rows: 23, duplicates_removed: 1, missing_values_imputed: 1, missing_values_by_column: { monthly_usage: 1 }, validation: "validated" },
  classification: { accuracy: 0.7, f1: 0.75, balanced_accuracy: 0.8, precision: 1, recall: 0.6, specificity: 1, threshold: 45, confusion_matrix: [[2, 0], [1, 3]], rule: "fixed", threshold_source: "domain" },
  regression: { mae: 2, mean_baseline_mae: 15, r2: 0.8, scored_rows: 6, missing_test_targets_excluded: 1 },
  clustering: { k: 2, silhouette: 0.55, centers: [[20, 1], [70, 3]] },
  reproducibility: { seed: 255 },
};

export const rows = [{ customer_id: "C001", plan: "pro", renewed: 1, cluster: 0, monthly_usage: 42 }];
export const summaryResponse = { metrics, summary: { analysis_rows: rows, regression_predictions: [{ customer_id: "C001", actual_usage: 42, predicted_usage: 40 }] }, source: { rows: 23 } };
export const rowsResponse = { count: 1, rows, filters: { plan: "all", renewal: "all", cluster: "all" } };
