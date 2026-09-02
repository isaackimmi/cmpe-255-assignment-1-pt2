function requireObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`Invalid ${label}: expected object`);
  return value;
}

function requireNumber(value, label) {
  if (!Number.isFinite(Number(value))) throw new Error(`Invalid ${label}: expected finite number`);
}

function validateClassification(value) {
  const result = requireObject(value, "classification metrics");
  ["accuracy", "f1", "balanced_accuracy", "precision", "recall", "specificity"].forEach((key) => requireNumber(result[key], `classification.${key}`));
  if (!Array.isArray(result.confusion_matrix) || result.confusion_matrix.length !== 2 || result.confusion_matrix.some((row) => !Array.isArray(row) || row.length !== 2)) throw new Error("Invalid classification.confusion_matrix");
  return result;
}

function validateRegression(value) {
  const result = requireObject(value, "regression metrics");
  ["mae", "mean_baseline_mae", "r2", "scored_rows"].forEach((key) => requireNumber(result[key], `regression.${key}`));
  return result;
}

function validateClustering(value) {
  const result = requireObject(value, "clustering metrics");
  requireNumber(result.k, "clustering.k");
  requireNumber(result.silhouette, "clustering.silhouette");
  if (!Array.isArray(result.centers)) throw new Error("Invalid clustering.centers");
  return result;
}

function validateQuality(value) {
  const result = requireObject(value, "data quality metrics");
  ["raw_rows", "clean_rows", "duplicates_removed", "missing_values_imputed"].forEach((key) => requireNumber(result[key], `data_quality.${key}`));
  requireObject(result.missing_values_by_column, "data_quality.missing_values_by_column");
  return result;
}

export function validateSummary(payload) {
  const value = requireObject(payload, "summary response");
  const metrics = requireObject(value.metrics, "metrics");
  validateQuality(metrics.data_quality);
  validateClassification(metrics.classification);
  validateRegression(metrics.regression);
  validateClustering(metrics.clustering);
  requireObject(metrics.reproducibility, "reproducibility metrics");
  const summary = requireObject(value.summary, "summary evidence");
  if (!Array.isArray(summary.analysis_rows) || !Array.isArray(summary.regression_predictions)) throw new Error("Invalid summary row collections");
  return value;
}

export function validateModule(module, payload) {
  if (module === "cleaning") return validateQuality(payload);
  if (module === "classification") return validateClassification(payload);
  if (module === "regression") {
    const value = requireObject(payload, "regression response");
    validateRegression(value.metrics);
    if (!Array.isArray(value.predictions)) throw new Error("Invalid regression predictions");
    return value;
  }
  if (module === "clustering") {
    const value = requireObject(payload, "clustering response");
    validateClustering(value.metrics);
    if (!Array.isArray(value.rows)) throw new Error("Invalid clustering rows");
    return value;
  }
  throw new Error(`Unknown module contract: ${module}`);
}

export function validateRows(payload) {
  const value = requireObject(payload, "rows response");
  requireNumber(value.count, "rows.count");
  if (!Array.isArray(value.rows)) throw new Error("Invalid rows collection");
  requireObject(value.filters, "rows.filters");
  return value;
}
