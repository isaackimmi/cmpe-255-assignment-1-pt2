# Project 12 data-science robustness review

## Scope

Reviewed the forecasting implementation, tests, generated metrics, README, and browser dashboard in this project. The review covers chronological splitting, leakage controls, lag and rolling features, the seasonal baseline, recursive forecasting, metric validity, horizon handling, reproducibility, and UI claims. No source files were modified.

## Executive summary

The model feature construction is properly causal, the data is chronologically ordered, and the model forecast path is recursive. The main issue is evaluation comparability: the HistGradientBoosting model is evaluated as a closed-loop recursive forecast from the training origin, while the seasonal-naive baseline is evaluated as a rolling one-step forecast that uses actual lagged observations. In the reported 36 test points, 24 baseline predictions read values whose timestamps are themselves inside the test window. That protocol can be operationally valid for one-step-ahead forecasting, but it is not a like-for-like comparison with the model's recursive path, so the headline result that the seasonal naive "beat" the model is not a valid model comparison as currently implemented.

The remaining concerns are moderate: the validation split is not scored or used for selection/refitting, the dashboard's horizon selector is intentionally only a presentation lens, and reproducibility is deterministic at the code level but not environment-pinned or provenance-rich.

## Findings

### [HIGH] Baseline and model are evaluated under different information sets

Evidence:

- `src/experiment.py:55-63` implements recursive forecasting by appending each prediction to history.
- `src/experiment.py:94-97` forecasts validation from `values[:train_end]`, then forecasts the reported test window from the training values plus the *predicted* validation values. No actual validation/test target is inserted into the model history.
- `src/experiment.py:66-68` defines the seasonal baseline as `values[t - SEASONAL_PERIOD]`, and `src/experiment.py:98-104` scores that baseline on the same test slice.
- With `n=240`, `train_end=168`, `validation_end/test_start=204`, the baseline accesses indices `192..227` for test timestamps `204..239`. Indices `204..227` are test targets, so 24 of 36 baseline predictions use actual values from inside the test window. This is valid only if the stated protocol is rolling one-step-ahead forecasting where each prior observation becomes available before the next prediction; it is not valid as a 36-step closed-loop comparison against the model path.
- `README.md:32`, `README.md:38-39`, and `README.md:49` present the model as recursive and the resulting baseline-vs-model numbers as a comparison, while the baseline is explicitly described as one-step operational at `README.md:39`.

Impact: the reported baseline MAE/RMSE (`0.7678`/`0.9971`) and the UI claim that the baseline leads (`index.html:42-49`) do not compare equivalent forecast scenarios. The result is not evidence that the baseline is better than the model under the same deployment horizon.

Concrete fix: choose and state one evaluation protocol, then apply it to both forecasters:

1. For a rolling one-step evaluation, score both the model and seasonal naive at each test timestamp using only observations available at that timestamp; or
2. For a closed-loop multi-step evaluation, start both forecasts from the same origin and append each forecaster's own prediction to its history. A recursive seasonal-naive implementation should replace the current direct lookup for this case.

Report the protocol and forecast origin in `metrics.json`, and add a regression test that prevents accidental mixing of actual test targets into a closed-loop baseline.

### [MEDIUM] Validation/test semantics and forecast origin are ambiguous

Evidence:

- `src/experiment.py:84-87` creates 70% train, 15% validation, and 15% test rows.
- `src/experiment.py:96-97` uses the validation period only as an unscored recursive warm-through period and carries its predictions into the test forecast. The model remains fitted only on the training rows (`src/experiment.py:87-92`); actual validation observations are not used to update or refit it.
- `metrics.json` contains only test metrics (`baseline_seasonal_naive` and `model_hist_gradient_boosting`) and no validation metrics or forecast-origin metadata (`outputs/metrics.json:2-16`).
- `README.md:32` calls the middle period a validation forecast horizon, but `README.md:41` says no hyperparameter search is performed.

Impact: a reader may interpret the final 36 points as a normal test forecast issued at the validation boundary, but the model is actually producing the last 36 points of a 72-step forecast issued at the training boundary. The validation block is neither a conventional tuning set nor a separately reported evaluation.

Concrete fix: either (a) score validation separately and, after all choices are frozen, fit/update using the allowed history through `validation_end` before forecasting the 36-point test horizon, or (b) retain the frozen 72-step experiment but label it explicitly as a 72-step forecast from `train_end` and report metrics by horizon block. In either case, store `forecast_origin`, `validation_horizon`, `test_horizon`, and whether actual intermediate observations were used.

### [MEDIUM] Horizon selector does not produce horizon-specific forecasts or metrics

Evidence:

- `app.js:3-20` maps 6/12/24/36 to labels and moves a visual marker only.
- `app.js:42-45` wires button clicks only to `setHorizon`; no forecast, slice, or metric request is made.
- `index.html:64-68` and `README.md:28` correctly disclose that this is illustrative and does not create new predictions.

Impact: the disclosure avoids a direct false forecasting claim, but the dashboard cannot answer a horizon-specific question. Selecting 6, 12, or 24 months leaves the displayed test metrics and full-window plot unchanged; the control is a review lens, not horizon handling.

Concrete fix: either remove the control until it is connected, or emit horizon-indexed predictions/metrics from Python and have the UI select the corresponding forecast slice and metric. Keep the illustrative label until real inference is connected.

### [MEDIUM] Reproducibility is deterministic in-code but not environment- or provenance-reproducible

Evidence:

- `src/experiment.py:24-36` fixes the synthetic-data seed default at 7, and `src/experiment.py:88-91` fixes the estimator `random_state` at 7.
- `requirements.txt:1-5` uses open-ended lower bounds (`>=`) rather than a lock/constraints file.
- `outputs/metrics.json:2-16` records row counts, split indices, metrics, and a prose leakage note, but not the data seed, model parameters, Python/library versions, or source revision.
- `tests/test_experiment.py:6-9` checks dataset equality across two calls, but does not verify regenerated metrics/predictions or the environment/configuration used to create committed artifacts.
- In this host, the documented `python` and `pytest` commands are not on `PATH`; the run succeeded with the bundled Python 3.12 runtime. The run also emitted Matplotlib cache and joblib core-detection warnings.

Impact: results should be stable in the supplied compatible environment, but dependency upgrades or a different runtime can change estimator behavior, warnings, or artifact bytes while the dashboard continues to show an apparently verified run.

Concrete fix: add a pinned `requirements-lock.txt` or constraints file; record Python, NumPy, pandas, scikit-learn, and Matplotlib versions plus the data/model configuration in `metrics.json`; and add a deterministic regression check for key numeric outputs (or a documented artifact hash with an explicit tolerance policy). Make the README's interpreter command match the supported environment.

### [LOW] Tests do not cover the high-risk forecasting invariants

Evidence:

- `tests/test_experiment.py:12-17` verifies that a single feature vector is unaffected by changing values at/after its timestamp, which is a useful causal-feature check.
- `tests/test_experiment.py:20-23` checks only feature shape, and `tests/test_experiment.py:26-31` checks artifact existence and one metric calculation.
- There is no test for exact split boundaries, recursive history contents, equal baseline/model forecast protocol, baseline horizon alignment, finite/non-empty predictions, or validation/test metric lengths.

Impact: the current 4-test suite can pass while the main comparison protocol is methodologically invalid.

Concrete fix: add tests for (1) exact `train_end`, `validation_end`, and test length; (2) recursive forecast history never containing actual future targets; (3) a closed-loop seasonal-naive baseline; (4) equal prediction/actual lengths and finite values; and (5) per-horizon metrics or forecast-origin metadata.

## Verified strengths

- Chronological ordering and split arithmetic are explicit (`src/experiment.py:27`, `src/experiment.py:84-87`); no random row shuffle is used.
- Model lag, change, and rolling features use only values before `t` (`src/experiment.py:39-52`). The existing future-mutation test supports this invariant (`tests/test_experiment.py:12-17`).
- The HistGradientBoosting model's validation/test path is recursive (`src/experiment.py:55-63`, `src/experiment.py:94-97`).
- MAE and RMSE are computed correctly for equal-length arrays (`src/experiment.py:71-75`).
- The synthetic-data limitation is disclosed in `README.md:43-45`; the project does not present this single synthetic series as real-world performance evidence.
- The dashboard is unusually candid about its planning-horizon limitation (`index.html:64-68`, `README.md:28`). The main UI correction needed is to qualify the baseline comparison with its information-set/protocol distinction.

## Checks run

All checks below were run without modifying source files:

- Bundled Python 3.12 runtime: `python3 -m pytest -q` → **4 passed**, 1 environment warning about physical-core detection.
- Bundled Python 3.12 runtime: isolated `python3 -m src.experiment --output-dir <temporary directory>` → **passed**; `metrics.json`, `forecast.png`, and `synthetic_monthly_series.csv` were created.
- Bundled Node runtime: `node --check app.js` → **passed**.
- Diagnostic protocol audit: confirmed the current seasonal-naive test lookup uses **24/36 actual test targets** as lag inputs under a closed-loop interpretation.

