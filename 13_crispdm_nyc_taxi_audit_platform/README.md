# Project 13 — CRISP-DM NYC Taxi Audit Platform

A small, CPU-safe capstone reproduction for NYC taxi trip-duration prediction. It combines a reproducible sample-data generator, exploratory/data-quality audit, temporal train/test evaluation, model metrics and plots, a CRISP-DM report, and a JSON-friendly inference CLI.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_platform.py --output artifacts
python run_platform.py --infer --pickup-hour 17 --weekday 4 --distance-miles 3.2 --passengers 2
pytest -q
```

The default run creates `artifacts/metrics.json`, `artifacts/audit_report.json`, `artifacts/eda.png`, `artifacts/actual_vs_predicted.png`, `artifacts/crispdm_report.md`, and a fitted `artifacts/model.joblib`. The data is generated deterministically and is intentionally not a download of the full NYC TLC corpus.

## What is implemented

- **Business understanding:** estimate trip duration in minutes for planning and dispatch analysis.
- **Data understanding/preparation:** deterministic NYC-like records with pickup/dropoff zones, time, passenger count, distance, and duration; derived temporal and route features.
- **Audit:** schema, nulls, duplicate IDs, invalid values, and robust IQR outlier counts are reported before modeling.
- **Modeling:** a scikit-learn histogram gradient-boosting regressor with a chronological 80/20 split, avoiding leakage from future trips.
- **Evaluation:** MAE, RMSE, R², and a duration-within-5-minutes rate; plots make data shape and prediction quality inspectable.
- **Deployment:** `--infer` loads the saved model and returns a prediction for one trip as JSON.

## Explicit deviations

The original Project 13 prompt was not present in the provided checkout (nor was a `PROMPTS.md` file), so this reproduction follows the delegated brief. It uses synthetic sample data instead of downloading licensed TLC parquet/CSV files, a single lightweight model instead of a model benchmark, and a local CLI instead of a hosted web service. Zone IDs are categorical stand-ins, coordinates/weather/fare are omitted, and no claim is made that sample metrics represent production NYC performance.

## Reproducibility and limitations

The generator seed, feature list, model parameters, split rule, and audit thresholds are recorded in the report. This is an educational audit platform: synthetic distributions may be simpler than real traffic, random missingness is injected only to exercise audit handling, and predictions should not be used for dispatch, pricing, or safety decisions without real-data validation, monitoring, privacy review, and retraining.
## Integration verification

- **Prompt alignment:** Public Project 13 asks for enterprise CRISP-DM taxi auditing, EDA, explainability, model comparison, inference APIs, and MLOps; the compact audit/training/inference subset is implemented.
- **Results/artifacts:** 955/239 chronological split; MAE 2.794 minutes, RMSE 3.622, R² 0.892, 84.5% within five minutes; pipeline/inference/pytest passed 4/4.
- **Issue/resolution:** Full TLC data, hosted service, SHAP, load testing, and multi-model autoresearch were not run because this checkout is CPU-safe CLI scope.
