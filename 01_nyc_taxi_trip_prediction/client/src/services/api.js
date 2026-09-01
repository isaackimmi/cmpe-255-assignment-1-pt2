const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

/** @typedef {{mae_seconds: number|null, rmse_seconds: number|null, r2: number|null, rows?: number}} ScoreMetrics */
/** @typedef {{linear_log_target: ScoreMetrics, baseline: ScoreMetrics, train_rows: number, test_rows: number, split_cutoff: {train_max_pickup_datetime: string, test_min_pickup_datetime: string}, source?: string}} ExperimentResponse */
/** @typedef {{feature: string, absolute_coefficient: number}} FeatureImportanceRow */
/** @typedef {{pickup_datetime: string, actual: number, prediction: number, residual_seconds: number}} PredictionRow */
/** @typedef {{slice: string, population: string, distance_boundary_miles: number, metrics: ScoreMetrics & {baseline: ScoreMetrics}, rows: PredictionRow[]}} PredictionSliceResponse */
/** @typedef {{estimated_duration_seconds: number, distance_miles: number, is_rush_hour: boolean, disclaimer: string}} EstimateResponse */

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const isObject = (value) =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const finite = (value) => Number.isFinite(Number(value));

function invalidResponse(resource) {
  throw new ApiError(`invalid_${resource}_response`, 502);
}

/** @returns {ExperimentResponse} */
function normalizeExperiment(payload) {
  if (
    !isObject(payload) ||
    !isObject(payload.linear_log_target) ||
    !isObject(payload.baseline) ||
    !isObject(payload.split_cutoff) ||
    !finite(payload.train_rows) ||
    !finite(payload.test_rows)
  )
    invalidResponse("experiment");
  return payload;
}

/** @returns {FeatureImportanceRow[]} */
function normalizeImportance(payload) {
  if (
    !Array.isArray(payload) ||
    payload.some(
      (row) =>
        !isObject(row) ||
        typeof row.feature !== "string" ||
        !finite(row.absolute_coefficient),
    )
  )
    invalidResponse("feature_importance");
  return payload.map((row) => ({
    ...row,
    absolute_coefficient: Number(row.absolute_coefficient),
  }));
}

/** @returns {PredictionSliceResponse} */
function normalizePredictionSlice(payload) {
  if (
    !isObject(payload) ||
    typeof payload.slice !== "string" ||
    typeof payload.population !== "string" ||
    !finite(payload.distance_boundary_miles) ||
    !isObject(payload.metrics) ||
    !isObject(payload.metrics.baseline) ||
    !Array.isArray(payload.rows)
  )
    invalidResponse("predictions");
  if (
    payload.rows.some(
      (row) =>
        !isObject(row) ||
        typeof row.pickup_datetime !== "string" ||
        !finite(row.actual) ||
        !finite(row.prediction) ||
        !finite(row.residual_seconds),
    )
  )
    invalidResponse("predictions");
  return payload;
}

/** @returns {EstimateResponse} */
function normalizeEstimate(payload) {
  if (
    !isObject(payload) ||
    !finite(payload.estimated_duration_seconds) ||
    !finite(payload.distance_miles) ||
    typeof payload.is_rush_hour !== "boolean" ||
    typeof payload.disclaimer !== "string"
  )
    invalidResponse("estimate");
  return payload;
}

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    throw new ApiError(error?.message || "network_request_failed", 0);
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail =
      typeof payload.detail === "string"
        ? payload.detail
        : JSON.stringify(payload.detail || {});
    throw new ApiError(
      detail || `request_failed:${response.status}`,
      response.status,
    );
  }
  return response.json();
}

export const taxiApi = {
  experiment: ({ signal } = {}) =>
    request("/experiment", { signal }).then(normalizeExperiment),
  featureImportance: ({ signal } = {}) =>
    request("/feature-importance", { signal }).then(normalizeImportance),
  predictions: ({ slice, population, signal } = {}) =>
    request(
      `/predictions?slice=${encodeURIComponent(slice || "all")}&population=${encodeURIComponent(population || "primary")}`,
      { signal },
    ).then(normalizePredictionSlice),
  estimate: (payload, { signal } = {}) =>
    request("/estimate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    }).then(normalizeEstimate),
};
