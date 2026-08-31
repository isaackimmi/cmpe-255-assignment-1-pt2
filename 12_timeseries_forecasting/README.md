# Project 12 — Time-Series Forecasting

This is a small, reproducible, CPU-safe forecasting experiment for Assignment 1 Part 2. It generates a deterministic monthly signal, compares a seasonal-naive baseline with a lag-feature gradient-boosting model, evaluates aligned closed-loop forecasts on held-out future periods, and saves plots plus machine-readable metrics and predictions.

The original `PROMPTS.md` was not present in the supplied checkout. This implementation follows the Project 12 requirements supplied with the task: dataset, chronological split, baseline, model, evaluation, plots, tests, README, and limitations.

## Run

From this directory:

```bash
python -m src.experiment --output-dir outputs
pytest -q
```

The default run creates `outputs/metrics.json`, `outputs/synthetic_monthly_series.csv`, `outputs/forecast_predictions.csv`, `outputs/forecast.png`, and horizon-specific plot artifacts.

## Forecasting Studio UI

Open `index.html` through a small local HTTP server from this directory so the browser can load the generated JSON artifact:

```bash
python -m http.server 8000
```

Then visit <http://localhost:8000>. The studio loads `outputs/metrics.json` and displays the emitted forecast artifact, with baseline/model metric cards, the chronological split, leakage controls, a CRISP-DM workflow trace, and reproduction commands. Refresh the page after regenerating the experiment outputs.

The planning-horizon selector is intentionally labeled **illustrative**: it selects a horizon-specific slice and metrics already emitted by the offline run; it does not call the Python experiment or create new predictions. A production version should connect that control to a backend inference endpoint before presenting newly generated values as forecasts.

## Method

There are 240 monthly observations. The first 70% is training, the next 15% is a validation forecast block, and the final 15% is the reported test block. A `HistGradientBoostingRegressor` uses lags 1, 2, 3, 6, and 12 plus recent change and rolling means. Both forecasters start at the training boundary and forecast recursively through validation and test; actual validation/test targets are used only after forecasting for scoring. The model is fit on training rows. The seasonal-naive baseline predicts the value 12 months earlier, feeding its own predictions back after the first forecast. Metrics are MAE and RMSE, reported for validation, full test, and the first 6/12/24/36 test months.

## Leakage controls and deviations

- All splits preserve time order; no random shuffling is used.
- Features for time `t` use only observations with timestamps before `t`.
- Both baseline and model use the same forecast origin (`train_end`) and closed-loop multi-step information set; future validation/test targets are never inserted into either history.
- The validation block is not used to tune or refit the fixed model; it is a scored forecast block that makes the 72-step origin-to-test protocol explicit.
- `metrics.json` records split boundaries, forecast origin, horizons, prediction-history semantics, configuration, software versions, source revision, and the emitted horizon metrics.
- The requested original prompt could not be recovered from the checkout, and no external dataset was assumed. A synthetic dataset is therefore used so the experiment runs offline and reproducibly.
- The validation horizon is used to exercise recursive forecasting, but no hyperparameter search is performed; the compact fixed configuration is intentionally CPU-safe.

## Limitations

This synthetic series is not evidence of real-world forecasting performance. There are no exogenous variables, missing-value cases, prediction intervals, rolling-origin uncertainty estimates, or statistical significance analysis. For production use, replace the generator with a versioned real dataset, add multiple rolling-origin evaluations, and tune only within each training window.
## Integration verification

- **Prompt alignment:** Public Project 12 asks for time-series forecasting with CRISP-DM and dashboards; chronological data, baseline/model comparison, leakage controls, metrics, plot, and tests are covered in a CLI.
- **Results/artifacts:** The committed metrics compare aligned closed-loop forecasts and include validation/test plus 6/12/24/36-month slices; outputs can be regenerated with the commands above.
- **Issue/resolution:** Use the pinned versions in `requirements-lock.txt` when reproducing the supplied artifacts; the looser `requirements.txt` remains suitable for compatible installs.
