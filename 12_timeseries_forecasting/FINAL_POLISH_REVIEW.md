# Project 12 — Final Polish Review

## Scope and verdict

This is a final static audit of the forecasting implementation, committed outputs, tests, README, and browser UI. No source code was modified; the only intended change is this review file.

**Recommendation: conditionally ready for a coursework/demo submission, not yet ready to present as a production forecasting evaluation.** The core chronology and leakage controls are sound, and the previous baseline/model information-set mismatch is resolved: both forecasters now start at the same training origin and run closed-loop through validation and test. The remaining work is mostly about making the evaluation protocol unambiguous, making horizon/error exploration genuinely analytical, and tightening the meaning of “verified” and provenance claims.

There is no critical leakage defect in the current implementation. The highest-priority polish is to choose whether the middle 36 months are a true validation stage or part of a single 72-step forecast, then use that language consistently in the metrics, README, plot labels, and UI.

## Prioritized action list

| Priority | Area | Finding | Recommended action |
| --- | --- | --- | --- |
| **P1** | Forecast protocol | The model is fitted only through the training boundary and produces one 72-step forecast through the nominal validation and test blocks. This is valid as a long-horizon stress test, but the “validation” block is not used for tuning, selection, refitting, or test-origin updating. | Either use validation for frozen-model selection followed by a documented refit/update before a test-origin forecast, or rename the current design as a **72-step closed-loop forecast from the training origin** with validation/test reporting slices. Store the chosen interpretation as a first-class protocol field. |
| **P1** | UI errors | The horizon selector changes precomputed PNGs and aggregated cards, but does not expose date-level residuals, error trajectories, or the underlying forecast rows. | Load `forecast_predictions.csv` and render a data-backed interactive chart/table with actual, baseline, model, residual, absolute error, and selected horizon. Add a residual/error view so users can inspect *why* a horizon wins. |
| **P1** | UI verification claims | `VERIFIED` and `suite verified` are presentation literals, while the runtime only confirms that `metrics.json` fetched successfully. There is no output hash or test-result artifact check. | Change the badge to “artifact loaded” unless verification is actually performed. Add generation timestamp, artifact hashes, source dirty/clean state, and a machine-readable test/reproduction status before displaying “verified.” |
| **P2** | Horizon semantics | Horizon metrics are cumulative prefix scores for test months 1 through `h`, not error at the exact `h`-month lead. The UI mostly discloses this, but “TEST WINDOW · 12 MONTHS” can be read as a new 12-month test window. | Label these values **cumulative test prefix, months 1–h**. Add exact-lead metrics and/or rolling-origin lead metrics if the product question is “how accurate is a forecast h months ahead?” |
| **P2** | Baselines and generalization | A seasonal-naive baseline is appropriate for the synthetic annual seasonality, but one baseline is weak evidence for a trending signal and one generated series is not evidence of real-world performance. | Add last-value, drift/trend, and seasonal-naive references; report normalized metrics such as MASE; evaluate multiple rolling origins and multiple data seeds before drawing model conclusions. |
| **P2** | Provenance | Provenance is substantially improved and includes seed, model configuration, software versions, and source revision, but it does not identify the exact emitted artifact bytes or whether the checkout was dirty. The README also shows the loose install command rather than the pinned environment command. | Record config values such as lags and split fractions, generation time, output hashes, repository dirty state, and the lockfile/environment used. Make the reproduction command explicitly use `requirements-lock.txt` or a constraints workflow. |
| **P3** | Regression coverage | The tests cover causality, split metadata, closed-loop seasonal naive behavior, finite metrics, artifacts, determinism, and provenance. They do not directly test the CSV row semantics, the model’s recursive history, prefix-vs-lead metric meaning, or the UI’s artifact switching. | Add focused tests for forecast dates/split labels, no actual future values entering either history, exact horizon slicing, and the UI’s selected artifact/metric consistency. |

## Evidence and detailed findings

### 1. Forecasting soundness: chronology and leakage are strong

**Verified strengths:**

- `src/experiment.py:36-48` generates an ordered monthly series; `src/experiment.py:39` uses monthly-start frequency and `src/experiment.py:185-188` derives the 70/15/15 chronological boundaries.
- `src/experiment.py:51-56` builds every lag, change, and rolling feature from `values[:t]`; the feature for time `t` never reads the current or a future target.
- `src/experiment.py:191-193` fits the estimator only on rows before `train_end`.
- `src/experiment.py:195-205` forecasts both methods from `values[:train_end]` through the complete 72-step continuation, retaining validation/test actuals only for post-hoc scoring.
- `src/experiment.py:81-105` implements the seasonal-naive baseline as closed-loop: after the available observed history is exhausted, prior predictions are fed back rather than actual future targets.
- `src/experiment.py:108-120` rejects empty, misaligned, or non-finite metric inputs before calculating MAE/RMSE.
- `outputs/metrics.json:11-21` explicitly records the common origin (`2014-01-01`), no actual intermediate observations, prediction feedback, and no test targets as inputs.

This is a meaningful improvement over a mixed-information-set comparison. The reported 36-month test result is now a like-for-like closed-loop comparison: model MAE 2.301 versus baseline MAE 2.722, and model RMSE 2.719 versus baseline RMSE 2.941 (`outputs/metrics.json:33-49`).

### 2. P1 — “Validation” is a reporting slice, not a conventional validation stage

**Evidence:**

- `src/experiment.py:185-188` creates separate train, validation, and test indices.
- `src/experiment.py:191-200` fits once on training rows and then issues one 72-step forecast from the training boundary; it does not use the validation observations to tune or refit.
- `src/experiment.py:201-213` scores the first 36 forecast steps as validation and the next 36 as test.
- `README.md:32` calls the middle block a validation forecast block, while `README.md:39` correctly says it is not used to tune or refit.
- `outputs/metrics.json:11-21` calls the protocol `closed_loop_multi_step` and records the origin at the beginning of the nominal validation block.

**Impact:** A reader familiar with train/validation/test workflows may assume the test forecast begins at `test_start` with actual validation history available. That is not what this run measures. It measures the last 36 steps of a forecast issued at the training origin, after 36 predicted intermediate values have been fed back. This is not leakage, but it is a different operational question and is likely to be misunderstood from the current “validation/test” vocabulary.

**Action:** Pick one explicit contract:

1. **Forecast-origin protocol:** preserve the current run, rename the middle block to something like `warm_through` or `origin_to_test`, and state that the reported test is forecast lead 37–72 from the training origin; or
2. **Conventional holdout protocol:** freeze decisions using validation, then fit/update with the permitted history through `validation_end` and issue a fresh 36-step test forecast from `test_start`.

Whichever contract is selected, expose `forecast_origin`, `forecast_lead_start`, `forecast_lead_end`, `actual_intermediate_observations_used`, and `refit_after_validation` in `metrics.json` and mirror those terms in the UI.

### 3. P1 — The UI is interactively selecting artifacts, but not exploring errors

**What works:**

- `app.js:15-37` responds to each horizon button, updates the selected label and test-slice text, selects the matching `horizon_metrics` record, and swaps in the matching `forecast_horizon_*.png` artifact.
- `app.js:40-60` recomputes the displayed winner and relative MAE difference for the selected stored horizon. This is why the UI can correctly show different winners: the six-month prefix favors the baseline (`outputs/metrics.json:51-60`), while the 12-, 24-, and 36-month prefixes favor the model (`outputs/metrics.json:62-90`).
- `index.html:64-68` candidly labels the control as an illustrative artifact lens and says it does not run new inference. That disclosure should be retained.

**Gap:** `app.js:62-70` fetches only `outputs/metrics.json`; it never reads the emitted `forecast_predictions.csv` (`outputs/metrics.json:105`). The chart is an image element at `index.html:58`, and the selector only changes its `src` at `app.js:31-36`. There is no residual series, hover value, date-level comparison, error distribution, or downloadable selected slice. The current experience is therefore an interactive artifact gallery and metric switcher—not an interactive error analysis surface.

**Action:** Use the CSV as the UI’s source of truth for an SVG/canvas chart and a compact accessible table. At minimum expose:

- selected horizon and exact date range;
- actual, seasonal-naive, and model values for each displayed date;
- signed residual and absolute error for both forecasters;
- cumulative MAE/RMSE plus exact-lead or rolling-origin error where available;
- a clear marker distinguishing the forecast origin, nominal validation boundary, and test boundary.

### 4. P1 — “Verified” is not yet an evidence-backed UI state

**Evidence:**

- `index.html:31` hard-codes the hero state as `VERIFIED`.
- `index.html:92` hard-codes `suite verified` beside the reproduction command.
- `app.js:64-70` sets `Metrics + forecast slice connected` after a successful JSON fetch, but does not verify that all referenced images, CSV rows, source revision, or test results match.
- `outputs/metrics.json:106-129` records useful provenance but no generation timestamp, output hashes, test report, or repository dirty state.

**Impact:** The UI can look fully verified even if a PNG is missing, an artifact is stale relative to `metrics.json`, or the committed output was generated from uncommitted code. This weakens trust precisely where the design emphasizes evidence.

**Action:** Use separate states such as `artifact loaded`, `artifact/provenance matched`, and `reproduction checks passed`. Make the final state data-backed from a manifest containing hashes for `metrics.json`, the prediction CSV, and each plot, plus the source revision and clean/dirty status.

### 5. P2 — Horizon metrics need clearer semantics and richer lead analysis

**Evidence:**

- `src/experiment.py:208-213` calculates each horizon from `test_actual[:horizon]`, `test_baseline[:horizon]`, and `test_model[:horizon]`.
- `outputs/metrics.json:51-91` stores four prefix metrics, and `README.md:32` describes them as the “first 6/12/24/36 test months.”
- `app.js:3-7` and `index.html:64-68` also describe a selected slice, which is directionally correct.
- `index.html:57` labels the selected value as `TEST WINDOW · N MONTHS`, which can imply that the entire test window was regenerated for each choice.

**Impact:** A 12-month MAE currently means average error over forecast leads 1–12 for the one fixed origin, not performance at lead 12. It is also not an independent 12-month test set; the prefixes are nested and share observations.

**Action:** Rename the UI label to `TEST PREFIX · MONTHS 1–N` and the metric label to `cumulative prefix MAE/RMSE`. If horizon decisions matter, emit `lead_metrics` for each lead and, preferably, rolling-origin metrics with uncertainty intervals. Keep the existing prefix cards as a useful planning summary, but do not present them as exact-lead accuracy.

### 6. P2 — Baseline coverage and external validity are intentionally narrow

**Evidence:**

- `src/experiment.py:23-33` defines a trending, deterministic seasonal synthetic process with fixed noise seed and a fixed HistGBR configuration.
- `src/experiment.py:81-105` supplies one seasonal-naive reference.
- `README.md:41-46` explicitly discloses the synthetic-data choice and the absence of exogenous variables, missing-value cases, intervals, rolling-origin uncertainty, and significance analysis.

**Assessment:** The disclosures are responsible, and the synthetic generator is appropriate for an offline CPU-safe demonstration. However, the data-generating process is close to the seasonal-naive/model assumptions and the single series does not establish robustness. A model win on this artifact should be described as an implementation demonstration, not evidence of general forecasting superiority.

**Action:** Add last-value, drift/trend, and seasonal-naive baselines; report MASE or another scale-normalized metric; run multiple seeds and rolling origins; and add at least one realistic versioned dataset before making a deployment recommendation. Add prediction intervals or calibrated empirical error bands if the UI will use the word “planning.”

### 7. P2 — Provenance is good, but artifact identity can be stronger

**Verified strengths:**

- `requirements-lock.txt:1-5` pins the main runtime dependencies.
- `src/experiment.py:275-285` records the data seed, estimator and parameters, Python/library versions, and source revision.
- `tests/test_experiment.py:85-92` checks deterministic results and the presence of provenance.

**Remaining gap:** `requirements.txt:1-5` remains open-ended, while `README.md:11-16` shows generic run commands and `README.md:49-51` only later mentions the lockfile. `src/experiment.py:130-142` records only the short HEAD revision; it does not say whether the checkout was dirty. There is also no hash of the generated CSV/JSON/PNG outputs.

**Action:** Record the exact configuration (`LAGS`, seasonal period, split fractions, dataset length), a UTC generation timestamp, output SHA-256 hashes, and repository dirty state. Put the pinned environment command first in the README. This would make the “refresh and inspect” workflow auditable rather than merely repeatable in a compatible environment.

### 8. P3 — Tests protect important invariants but not the full contract

**Evidence:**

- `tests/test_experiment.py:15-18` checks deterministic ordered data.
- `tests/test_experiment.py:21-26` checks that future mutations cannot affect a feature vector.
- `tests/test_experiment.py:35-38` checks closed-loop seasonal-naive feedback.
- `tests/test_experiment.py:41-46` checks metric input validation.
- `tests/test_experiment.py:48-82` checks split metadata, horizons, finite prediction values, and artifact creation.
- `tests/test_experiment.py:85-92` checks deterministic run output and provenance.

**Missing coverage:** no direct assertion ties each CSV date and `split` label to the intended forecast index; no spy/mock test proves the model recursive path never sees actual validation/test values; no test distinguishes prefix metrics from exact-lead metrics; and no browser-level test verifies that each selected horizon updates both the metric data and image artifact consistently.

**Action:** Add those focused regression tests before further UI or protocol changes. They are small tests with high value because a future refactor could preserve the metadata while silently changing the information set or slice alignment.

## Final recommendation

Keep the current forecasting implementation as the baseline for the submission: its chronology, causal features, common closed-loop information set, finite metric checks, and provenance are credible for a compact synthetic demonstration. Before calling the project “final,” make the P1 changes:

1. declare whether the current 72-step origin-to-test continuation is intentional, and align all validation/test labels with that decision;
2. make the UI’s horizon view say “stored artifact slice” and add row-level residual/error exploration; and
3. replace hard-coded verification language with a data-backed artifact/reproduction status.

After those changes, the project should be considered strong for the stated CPU-safe coursework scope. It should still be presented as a reproducible forecasting workflow demonstration—not a production model—until rolling-origin evaluation, stronger baselines, realistic data, uncertainty, and deployment-backed inference are added.
