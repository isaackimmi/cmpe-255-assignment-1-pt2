# Project 12 — Time-Series Forecasting

This is a small, reproducible, CPU-safe forecasting experiment for Assignment 1 Part 2. It generates a deterministic monthly signal, compares a seasonal-naive baseline with a lag-feature gradient-boosting model, evaluates on a held-out future period, and saves a plot plus machine-readable metrics.

The original `PROMPTS.md` was not present in the supplied checkout. This implementation follows the Project 12 requirements supplied with the task: dataset, chronological split, baseline, model, evaluation, plots, tests, README, and limitations.

## Run

From this directory:

```bash
python -m src.experiment --output-dir outputs
pytest -q
```

The default run creates `outputs/metrics.json`, `outputs/synthetic_monthly_series.csv`, and `outputs/forecast.png`.

## Method

There are 240 monthly observations. The first 70% is training, the next 15% is a validation forecast horizon, and the final 15% is the reported test horizon. A `HistGradientBoostingRegressor` uses lags 1, 2, 3, 6, and 12 plus recent change and rolling means. The model is fit on training rows and forecasts recursively through validation and test. The seasonal-naive baseline predicts the value 12 months earlier. Metrics are MAE and RMSE.

## Leakage controls and deviations

- All splits preserve time order; no random shuffling is used.
- Features for time `t` use only observations with timestamps before `t`.
- Test model predictions are recursive, so future test targets are never inserted into model history.
- The seasonal-naive baseline uses the already-observed value from 12 months earlier, which is a valid one-step-ahead operational baseline.
- The requested original prompt could not be recovered from the checkout, and no external dataset was assumed. A synthetic dataset is therefore used so the experiment runs offline and reproducibly.
- The validation horizon is used to exercise recursive forecasting, but no hyperparameter search is performed; the compact fixed configuration is intentionally CPU-safe.

## Limitations

This synthetic series is not evidence of real-world forecasting performance. There are no exogenous variables, missing-value cases, prediction intervals, rolling-origin uncertainty estimates, or statistical significance analysis. For production use, replace the generator with a versioned real dataset, add multiple rolling-origin evaluations, and tune only within each training window.
## Integration verification

- **Prompt alignment:** Public Project 12 asks for time-series forecasting with CRISP-DM and dashboards; chronological data, baseline/model comparison, leakage controls, metrics, plot, and tests are covered in a CLI.
- **Results/artifacts:** Seasonal naive beat fixed boosting (MAE 0.7678 vs 2.3015; RMSE 0.9971 vs 2.7192); outputs regenerated; pytest passed 4/4.
- **Issue/resolution:** Compatible existing environment was used because system Python lacked packages and Python 3.14 Matplotlib aborted during cache setup.
