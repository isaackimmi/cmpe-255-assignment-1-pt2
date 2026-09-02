# Implementation Plan — NYC Taxi Trip-Duration Prediction

## Retrospective scope

This plan documents the reproducible NYC-like taxi regression implementation: a dependency-light experiment with a deterministic fallback dataset, artifact-backed FastAPI evidence, and a React/MUI dashboard.

## Objectives

1. Predict `trip_duration` from pickup/drop-off coordinates, pickup time, passenger count, and vendor.
2. Preserve a production-realistic temporal boundary between training and future holdout data.
3. Compare an interpretable regularized model against meaningful median baselines.
4. Expose aggregate metrics, temporal slices, row-level predictions, feature importance, and an estimator through a browser UI.
5. Make synthetic fallback data and its limitations explicit.

## Data and preparation

1. Accept the common NYC Taxi Trip Duration CSV schema; generate a deterministic NYC-like sample when no CSV is supplied.
2. Validate IDs, timestamps, coordinates, passenger counts, vendor IDs, route distance, duration, finite values, service-area bounds, and drop-rate limits.
3. Normalize timestamps with an explicit America/New_York policy and reject mixed-awareness or ambiguous local times.
4. Engineer hour, weekday, month, rush-hour, coordinate-delta, and haversine-distance features.
5. Record structural drop reasons and data provenance in the metrics artifact.

## Modeling and evaluation

1. Split on whole pickup-timestamp groups so `max(train_time) < min(test_time)` is guaranteed.
2. Fit the 99th-percentile target trim on training data only; report the complete eligible holdout as primary and the trimmed inlier result as sensitivity analysis.
3. Train a regularized linear model on `log1p(trip_duration)` and convert predictions back to seconds.
4. Compare global-median, recent-median, and hour-conditioned median baselines.
5. Report MAE, RMSE, and R² in seconds on the final chronological holdout and across expanding chronological folds.
6. Preserve residuals, slice labels, robust-inlier flags, and row-level predictions for inspection.

## Application sequence

1. Keep `run_experiment.py` as the reproducible training/evaluation entrypoint.
2. Split ML responsibilities into validation, geospatial math, artifact loading, scoring, slice analysis, and estimator modules, with `ml/model.py` as a compatibility facade.
3. Split FastAPI configuration, schemas, routers, and application service so HTTP concerns remain separate from analytical logic.
4. Build React/MUI components for the dashboard shell, metric cards, evidence views, slice controls, prediction explorer, estimator form, and loading/error states.
5. Use API-backed artifacts for all displayed metrics; do not compute replacement values in the browser.

## Validation criteria

- Default fallback generation is deterministic and `validate.py` passes.
- Temporal leakage checks and timestamp policy tests pass.
- Model metrics are reported against the correct complete holdout population and baselines.
- Invalid estimator inputs are rejected with actionable responses.
- Client tests and the Vite production build pass; the rush-hour slice updates server-computed evidence.

## Limitations and next steps

The fallback data is synthetic and lacks real traffic, weather, road-network, and event features. A production version should use official TLC/Kaggle data, validate its service-area policy, add richer time-based validation, and monitor errors by borough, hour, distance, and drift.
