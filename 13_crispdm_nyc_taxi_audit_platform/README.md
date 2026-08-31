# Project 13 — CRISP-DM NYC Taxi Audit Platform

A small, CPU-safe capstone reproduction for NYC taxi trip-duration prediction. It combines a reproducible sample-data generator, exploratory/data-quality audit, temporal train/test evaluation, model metrics and plots, a CRISP-DM report, and a JSON-friendly inference CLI.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_platform.py --output artifacts
python run_platform.py --infer --pickup-hour 17 --weekday 4 --distance-miles 3.2 --passengers 2 --pickup-zone 1 --dropoff-zone 2
pytest -q
```

The default run creates `artifacts/metrics.json`, `artifacts/audit_report.json`, `artifacts/run_manifest.json`, `artifacts/prediction_errors.json`, `artifacts/eda.png`, `artifacts/actual_vs_predicted.png`, `artifacts/crispdm_report.md`, and a fitted `artifacts/model.joblib`. The data is generated deterministically and is intentionally not a download of the full NYC TLC corpus. Metrics are synthetic smoke-test metrics and are not evidence of real NYC taxi generalization.

## Dashboard UI

The project includes a dependency-free responsive dashboard in `dashboard/`. It reads the generated JSON/Markdown artifacts and displays the synthetic smoke-test scorecard, run identity, static evidence snapshots, row-level severity-filterable audit findings, holdout error/slice exploration, report notes, and a clearly labeled local/illustrative inference lab.

After generating the artifacts, serve the project root and open <http://localhost:8000/dashboard/>:

```bash
python -m http.server 8000
```

The dashboard's browser estimate is intentionally a separate toy calculator because the saved scikit-learn `model.joblib` is used by the Python CLI, not loaded into the browser. It omits zone inputs and must not be compared with the scorecard. Run the evaluated saved-model inference with:

```bash
python run_platform.py --infer --pickup-hour 17 --weekday 4 --distance-miles 3.2 --passengers 2 --pickup-zone 1 --dropoff-zone 2
```

Stop the local server with `Ctrl-C` when finished.

## What is implemented

- **Business understanding:** illustrate trip-duration estimation for an educational planning and audit demonstration.
- **Data understanding/preparation:** deterministic NYC-like records with pickup/dropoff zones, time, passenger count, distance, and duration; derived temporal and route features.
- **Audit:** schema, nulls, duplicate IDs, typed target-quality rules, field-specific validity checks, and IQR outlier observations are reported before modeling with row IDs, actions, and statuses.
- **Modeling:** a scikit-learn histogram gradient-boosting regressor with a chronological 80/20 split; imputation statistics are fitted only on training rows and serialized with the model.
- **Evaluation:** MAE, RMSE, R², a duration-within-5-minutes rate, and simple global-mean/distance-only baselines on one chronological holdout; row-level errors and slice metrics are saved as JSON. The scorecard explicitly labels this as a synthetic smoke test.
- **Reproducibility:** `run_manifest.json` records a run identity, command, seed, row argument, source/data hashes, git revision, runtime versions, feature contract, target policy, model parameters, split rule, population/time ranges, and artifact hashes.
- **Deployment:** `--infer` loads the saved model and returns a prediction for one trip as JSON.

## Explicit deviations

The original Project 13 prompt was not present in the provided checkout (nor was a `PROMPTS.md` file), so this reproduction follows the delegated brief. It uses synthetic sample data instead of downloading licensed TLC parquet/CSV files, a single lightweight model instead of a model benchmark, and a local CLI instead of a hosted web service. Zone IDs are categorical stand-ins, coordinates/weather/fare are omitted, and no claim is made that sample metrics represent production NYC performance.

## Reproducibility and limitations

The generator seed, feature list, model parameters, split rule, and audit thresholds are recorded in `artifacts/run_manifest.json`; the report summarizes the same run. This is an educational audit platform: synthetic distributions may be simpler than real traffic, random missingness is injected only to exercise audit handling, and predictions should not be used for dispatch, pricing, or safety decisions without real-data validation, monitoring, privacy review, and retraining.
## Integration verification

- **Prompt alignment:** Public Project 13 asks for enterprise CRISP-DM taxi auditing, EDA, explainability, model comparison, inference APIs, and MLOps; the compact audit/training/inference subset is implemented.
- **Results/artifacts:** The generated artifacts are traceable through `run_manifest.json`; reported scores are synthetic smoke-test results only.
- **Issue/resolution:** Full TLC data, hosted service, SHAP, load testing, and multi-model autoresearch were not run because this checkout is CPU-safe CLI scope.
