const REQUIRED_FEATURES = ["annual_income_k", "spend_score", "purchase_frequency", "avg_order_value"];

function assert(condition, message) {
  if (!condition) throw new Error(`Invalid API evidence: ${message}`);
}

function finite(value, path) {
  assert(Number.isFinite(Number(value)), `${path} must be finite`);
}

export function validateDashboardPayload({ summary, profiles, points, validation }) {
  assert(summary && Number.isInteger(Number(summary.selected_k)), "summary.selected_k is required");
  assert(Array.isArray(summary.features), "summary.features must be an array");
  assert(REQUIRED_FEATURES.every((feature) => summary.features.includes(feature)), "summary.features is incomplete");
  finite(summary.validation?.silhouette_mean, "summary.validation.silhouette_mean");
  finite(summary.fit_metrics?.silhouette, "summary.fit_metrics.silhouette");
  assert(Array.isArray(profiles) && profiles.length > 0, "profiles must be a non-empty array");
  profiles.forEach((profile, index) => {
    assert(Number.isInteger(Number(profile.cluster)), `profiles[${index}].cluster is invalid`);
    REQUIRED_FEATURES.forEach((feature) => finite(profile.means?.[feature], `profiles[${index}].means.${feature}`));
  });
  assert(Array.isArray(points) && points.length > 0, "points must be a non-empty array");
  points.forEach((point, index) => {
    assert(typeof point.customer_id === "string", `points[${index}].customer_id is invalid`);
    REQUIRED_FEATURES.forEach((feature) => finite(point[feature], `points[${index}].${feature}`));
    ["cluster", "pca_x", "pca_y", "centroid_distance", "assignment_margin", "assignment_confidence"].forEach((key) => finite(point[key], `points[${index}].${key}`));
  });
  assert(Array.isArray(validation), "validation must be an array");
  validation.forEach((row, index) => {
    finite(row.k, `validation[${index}].k`);
    finite(row.silhouette_mean, `validation[${index}].silhouette_mean`);
  });
  return { summary, profiles, points, validation };
}
