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

## E2E application layout

The project now follows the reference repository's client/server/ml split while
keeping the data-science code dependency-light:

- `ml/` is organized by responsibility: artifact loading, numerical validation,
  scoring, slice analysis, geospatial math, and teaching estimation.
  `ml/model.py` remains a compatibility facade, while `run_experiment.py`
  remains the reproducible training/evaluation entry point.
- `server/` separates app construction, configuration, Pydantic schemas,
  routers, and an application service. `server/main.py` is a deliberately thin
  ASGI/compatibility entry point.
- `client/` is a React + Vite application using Material UI. Reusable layout,
  evidence, explorer, estimator, loading/error, and metric components live
  under `client/src/components`; API transport, async hooks, formatting, and
  the shared MUI theme live in their own modules.

### One-command demo

From this project directory, one command handles dependencies, starts FastAPI and React, opens <http://127.0.0.1:5173>, and stops both with one `Ctrl-C`:

```bash
./run_demo.sh
```

The separate commands below remain available for experiment regeneration and development.

### Run the ML experiment

```bash
cd 01_nyc_taxi_trip_prediction
python3 run_experiment.py
python3 validate.py
```

### Run FastAPI

In a second terminal from this project directory:

```bash
python3 -m venv .venv-server
source .venv-server/bin/activate
python -m pip install -r server/requirements.txt
uvicorn server.main:app --reload --host 127.0.0.1 --port 8001
```

The API docs are available at <http://127.0.0.1:8001/docs>.

### Run the Vite client

In a third terminal:

```bash
cd client
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` to FastAPI on port 8001.
For a production-like local preview, use `npm run build` followed by
`npm run preview` while FastAPI remains running.

## Legacy artifact viewer

The top-level `index.html`, `styles.css`, and `app.js` remain as a standalone
artifact viewer for GitHub Pages and offline inspection. The Vite client is the
preferred demo path because it exercises the actual FastAPI boundary.

Because browsers block `fetch()` for local JSON files opened with `file://`, the
legacy viewer can be served directly:

```bash
python3 -m http.server 8000
```

The legacy route/time controls are a deterministic browser-only teaching aid.
The E2E Vite client sends estimator requests to FastAPI, which applies the same
service-area, timestamp, distance, and passenger validation contract.

## Results

The checked-in `outputs/metrics.json` records the result of the default deterministic fallback run: 5,996 structurally eligible rows, a 4,749-row training fit after training-only target trimming, and a complete 1,199-row chronological holdout. Primary model MAE is 84.592s, RMSE 106.976s, and R² 0.6617 versus global-median MAE 148.243s and RMSE 184.684s. The 1,186-row inlier result is labeled separately as sensitivity analysis, and fold means/dispersion are included in the artifact. The synthetic generator intentionally makes the task learnable and should not be interpreted as a real-world benchmark.

## Limitations and next steps

- The fallback data has no real traffic, weather, road-network, or event information.
- The linear model and median baselines are intentionally small, interpretable benchmarks, not tuned production models. `feature_importance.csv` reports absolute standardized linear coefficients; correlated coordinate features can make individual rankings unstable.
- A real evaluation should use the official TLC/Kaggle data, verify the service-area policy against the source, use a time-based validation design, and perform calibration/error analysis by borough, hour, and distance.
- The target is unavailable at prediction time in real deployment; only pickup-time and request attributes may be used.

## Tests

Run the experiment and API contracts without starting either server:

```bash
python3 -m unittest discover -v
```

The API tests call route functions directly. They cover health and artifact
response shapes, stable slice boundaries, invalid query values, valid estimator
responses, out-of-area coordinates, and ambiguous timestamps.

The static E2E contracts also verify the React/Vite/MUI dependency boundary,
the component directory, modular API service, FastAPI router/service split, and
focused ML modules. Run `npm run build` from `client/` to verify the production
frontend bundle.
## Integration verification

- **Prompt alignment:** Public Project 01 asks for end-to-end NYC taxi prediction with data, training, deployment, CRISP-DM, map, and estimation. This covers data, training, temporal evaluation, outputs, and CLI; hosted map UI is out of scope.
- **Results/artifacts:** 6,000 input rows, 5,996 structurally eligible rows, 4,749/1,199 fit/holdout split; primary MAE 84.592s, RMSE 106.976s, R² 0.6617. Outputs, temporal folds, artifact-backed explorer, and validation passed.
- **Issue/resolution:** Full Kaggle/TLC data and frontend were not present; deterministic fallback is explicit.
