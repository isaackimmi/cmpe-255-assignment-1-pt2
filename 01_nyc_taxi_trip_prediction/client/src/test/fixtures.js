export const metricsFixture = {
  linear_log_target: { mae_seconds: 84.6, rmse_seconds: 106.9, r2: 0.6617 },
  baseline: { mae_seconds: 148.2, rmse_seconds: 184.6, r2: -0.01 },
  train_rows: 4749,
  test_rows: 1199,
  source: "test artifacts",
  split_cutoff: {
    train_max_pickup_datetime: "2016-03-12 23:37:00",
    test_min_pickup_datetime: "2016-03-12 23:46:00",
  },
};

export const importanceFixture = [
  { feature: "distance_miles", absolute_coefficient: 0.25 },
  { feature: "passenger_count", absolute_coefficient: 0.05 },
];

export function sliceFixture(slice = "all", population = "primary", rows = 2) {
  return {
    slice,
    population,
    distance_boundary_miles: 2.38,
    metrics: {
      rows,
      mae_seconds: 81.8,
      rmse_seconds: 105,
      r2: 0.681,
      baseline: { rows, mae_seconds: 147.4, rmse_seconds: 180, r2: -0.01 },
    },
    rows: Array.from({ length: rows }, (_, index) => ({
      pickup_datetime: `2016-03-13 0${index + 7}:04:00`,
      actual: 383 + index,
      prediction: 425.5 + index,
      residual_seconds: 42.5,
    })),
  };
}

export function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}
