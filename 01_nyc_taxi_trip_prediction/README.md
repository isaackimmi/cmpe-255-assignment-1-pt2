# Project 01 — NYC Taxi Trip Duration Prediction

This project is a small, reproducible data-science experiment for predicting the duration of a New York City taxi trip. It is designed to run without a Kaggle account or a multi-gigabyte download.

## Specification and scope

The local checkout did not contain `PROMPTS.md`, and its configured public remote had no readable branch content when this project was prepared. The implementation therefore follows the standard NYC Taxi Trip Duration task: predict `trip_duration` using pickup/drop-off coordinates, pickup time, passenger count, and vendor. The exact prompt should be reconciled here if the reference repository is restored.

## Data

`run_experiment.py` accepts a CSV with the common Kaggle columns (`id`, `vendor_id`, `pickup_datetime`, `passenger_count`, `pickup_longitude`, `pickup_latitude`, `dropoff_longitude`, `dropoff_latitude`, and `trip_duration`). With no input file, it creates a deterministic 6,000-row NYC-like sample. The fallback is useful for testing the pipeline, but its metrics are not evidence about real taxi performance. The core fallback uses only the Python standard library, so it runs in a minimal environment.

## Method

1. Parse pickup timestamps and derive hour, weekday, month, and rush-hour features.
2. Compute great-circle distance with the haversine formula and coordinate deltas.
3. Remove invalid coordinates, non-positive durations, and extreme duration outliers using training-set quantiles.
4. Use a chronological 80/20 split to avoid using future trips to predict earlier trips.
5. Compare a median-duration baseline with a regularized linear model on `log1p(trip_duration)`; report MAE, RMSE, and R² in seconds.

## Run

```bash
python3 run_experiment.py
python3 validate.py
```

To use a real CSV:

```bash
python3 run_experiment.py --input /path/to/train.csv --sample-size 50000
```

Outputs are written to `outputs/`: `metrics.json`, `feature_importance.csv`, `predictions.csv`, `duration_distribution.svg`, and `predicted_vs_actual.svg`.

## Results

The checked-in `outputs/metrics.json` records the result of the default deterministic fallback run. The model should beat the median baseline on MAE and RMSE, but the synthetic generator intentionally makes the task learnable and should not be interpreted as a real-world benchmark.

## Limitations and next steps

- The fallback data has no real traffic, weather, road-network, or event information.
- Random forests are a practical baseline, not a tuned production model.
- A real evaluation should use the official TLC/Kaggle data, geospatial sanity checks, a time-based validation design, and calibration/error analysis by borough, hour, and distance.
- The target is unavailable at prediction time in real deployment; only pickup-time and request attributes may be used.
## Integration verification

- **Prompt alignment:** Public Project 01 asks for end-to-end NYC taxi prediction with data, training, deployment, CRISP-DM, map, and estimation. This covers data, training, temporal evaluation, outputs, and CLI; hosted map UI is out of scope.
- **Results/artifacts:** 6,000 cleaned rows, 4,800/1,200 chronological split; MAE 82.045s, RMSE 102.688s, R² 0.6874. Outputs and validation passed.
- **Issue/resolution:** Full Kaggle/TLC data and frontend were not present; deterministic fallback is explicit.
