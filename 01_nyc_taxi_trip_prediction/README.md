# Project 01 — NYC Taxi Trip Duration Prediction

This project is a small, reproducible data-science experiment for predicting the duration of a New York City taxi trip. It is designed to run without a Kaggle account or a multi-gigabyte download.

## Specification and scope

The local checkout did not contain `PROMPTS.md`, and its configured public remote had no readable branch content when this project was prepared. The implementation therefore follows the standard NYC Taxi Trip Duration task: predict `trip_duration` using pickup/drop-off coordinates, pickup time, passenger count, and vendor. The exact prompt should be reconciled here if the reference repository is restored.

## Data

`run_experiment.py` accepts a CSV with the common Kaggle columns (`id`, `vendor_id`, `pickup_datetime`, `passenger_count`, `pickup_longitude`, `pickup_latitude`, `dropoff_longitude`, `dropoff_latitude`, and `trip_duration`). With no input file, it creates a deterministic 6,000-row NYC-like sample. The fallback is useful for testing the pipeline, but its metrics are not evidence about real taxi performance. The core fallback uses only the Python standard library, so it runs in a minimal environment.

## Method

1. Parse pickup timestamps and derive hour, weekday, month, and rush-hour features.
2. Compute great-circle distance with the haversine formula and coordinate deltas.
3. Validate finite numeric values, integer passenger counts, allowed vendor IDs, NYC-like service-area bounds, positive durations, timestamp coverage, unique IDs, and a maximum 100-mile route distance. Structural drop reasons are recorded in `metrics.json`, and the run fails if more than 25% of rows are dropped.
4. Interpret naive timestamps as `America/New_York`, normalize aware timestamps to UTC, reject mixed-awareness and ambiguous local times, and split on whole pickup-timestamp groups. The strict chronological contract requires `max(train_time) < min(test_time)`.
5. Fit the 99th-percentile duration threshold on training targets only. The primary holdout score includes every structurally eligible future row; the thresholded inlier score is reported separately as a sensitivity analysis because test targets are unavailable at prediction time.
6. Compare global-median, recent-median, and hour-conditioned median baselines with a regularized linear model on `log1p(trip_duration)`; report MAE, RMSE, and R² in seconds on the complete final holdout and across three expanding chronological folds.

## Run

```bash
python3 run_experiment.py
python3 validate.py
```

To use a real CSV:

```bash
python3 run_experiment.py --input /path/to/train.csv
```

Outputs are written to `outputs/`: `metrics.json`, `feature_importance.csv`, `predictions.csv`, `duration_distribution.svg`, and `predicted_vs_actual.svg`. `predictions.csv` contains primary all-row scores plus distance/time slice fields, residuals, and a `robust_inlier` sensitivity flag.

## Browser UI

The project includes a dependency-light standalone browser UI in `index.html`, `styles.css`, and `app.js`. It reads the checked-in `outputs/metrics.json`, `outputs/predictions.csv`, and `outputs/feature_importance.csv` at runtime and presents the model metrics, baseline comparison, residual/slice explorer, fold evidence, cleaning audit, SVG evidence, CRISP-DM workflow, and run instructions in a screenshot-friendly layout.

Because browsers block `fetch()` for local JSON files opened with `file://`, serve this directory locally:

```bash
cd 01_nyc_taxi_trip_prediction
python3 -m http.server 8000
```

Then open <http://localhost:8000>. The route/time controls provide a deterministic, no-noise client-side illustrative estimate based on the synthetic generator's directional relationships. They do not load model weights and should not be described as a production prediction. The UI falls back to the checked-in metric values when opened without a local server, but serving the folder enables the live `metrics.json` status. Hero and callout percentages are populated from the loaded metrics, so they remain honest for alternate CSV runs.

## Results

The checked-in `outputs/metrics.json` records the result of the default deterministic fallback run: 5,996 structurally eligible rows, a 4,749-row training fit after training-only target trimming, and a complete 1,199-row chronological holdout. Primary model MAE is 84.592s, RMSE 106.976s, and R² 0.6617 versus global-median MAE 148.243s and RMSE 184.684s. The 1,186-row inlier result is labeled separately as sensitivity analysis, and fold means/dispersion are included in the artifact. The synthetic generator intentionally makes the task learnable and should not be interpreted as a real-world benchmark.

## Limitations and next steps

- The fallback data has no real traffic, weather, road-network, or event information.
- The linear model and median baselines are intentionally small, interpretable benchmarks, not tuned production models. `feature_importance.csv` reports absolute standardized linear coefficients; correlated coordinate features can make individual rankings unstable.
- A real evaluation should use the official TLC/Kaggle data, verify the service-area policy against the source, use a time-based validation design, and perform calibration/error analysis by borough, hour, and distance.
- The target is unavailable at prediction time in real deployment; only pickup-time and request attributes may be used.
## Integration verification

- **Prompt alignment:** Public Project 01 asks for end-to-end NYC taxi prediction with data, training, deployment, CRISP-DM, map, and estimation. This covers data, training, temporal evaluation, outputs, and CLI; hosted map UI is out of scope.
- **Results/artifacts:** 6,000 input rows, 5,996 structurally eligible rows, 4,749/1,199 fit/holdout split; primary MAE 84.592s, RMSE 106.976s, R² 0.6617. Outputs, temporal folds, artifact-backed explorer, and validation passed.
- **Issue/resolution:** Full Kaggle/TLC data and frontend were not present; deterministic fallback is explicit.
