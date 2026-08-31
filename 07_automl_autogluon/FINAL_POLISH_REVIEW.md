# Final polish review — Project 07

Reviewed 2026-08-30 from the current source, checked-in artifacts, tests, README, and the tracked Project 07 screenshot. No project source code was modified.

## Recommendation

Keep the current development-CV/final-holdout structure. It is a sound teaching-demo baseline and is materially stronger than a leaderboard built on the final test set. Before presenting this as an “auditable AutoML” result, make the reporting/UI changes below—especially the operating-point metrics, uncertainty, and artifact consistency work. The UI is genuinely interactive at the model-detail level, but it is currently a shallow inspector rather than an interactive exploration of leaderboard tradeoffs.

## What is already sound

- **Model-selection roles are correct.** `src/experiment.py:234-282` creates an 80/20 stratified development/final split, ranks candidates using only repeated CV on development rows, refits the selected model on all development rows, and scores the final holdout once. The current `artifacts/dataset_summary.json:8-27` records 455 development rows and 114 final-holdout rows.
- **Preprocessing is leakage-safe for the sklearn candidate that needs it.** `src/experiment.py:47-61` keeps `StandardScaler` inside the logistic-regression pipeline, and `src/experiment.py:111-128` clones/fits each pipeline inside each CV fold.
- **The fallback is honest.** `src/experiment.py:159-201` distinguishes missing AutoGluon from runtime failure, and `src/experiment.py:306-345` records requested/attempted backends and status. The current artifact is explicitly `sklearn_fallback` with AutoGluon disabled (`artifacts/metrics.json:11-23`), not mislabeled as an AutoGluon run.
- **Reproducibility metadata is unusually good for this size of demo.** The runner records a run ID, command, seed, dataset hash, platform, package versions, model parameters, and AutoGluon settings (`src/experiment.py:306-345`).
- **The UI is not static copy.** Cards are generated from `leaderboard.csv` and wired to `selectModel()` (`app.js:88-103`, `app.js:118-122`); the native model selector drives the same detail panel (`app.js:131-136`). A non-selected model is explicitly shown without an invented final-holdout score (`app.js:106-115`).

## Prioritized improvements

### P1 — Make the evaluation decision clinically/operationally meaningful

**Evidence:** Metrics are accuracy, balanced accuracy, F1, and ROC-AUC (`src/experiment.py:64-76`). F1 and probability-based ROC-AUC use label `1`/probability column `1`; the dataset manifest identifies that class as **benign** (`artifacts/dataset_summary.json:19-23`). The business-language copy instead discusses ranking malignant versus benign cases (`index.html:150`). The final artifact contains no sensitivity, specificity, precision/NPV, PR-AUC, calibration, confusion matrix, threshold, or class support (`artifacts/final_metrics.json:2-12`).

**Why it matters:** For a diagnostic-flavored example, optimizing/reporting benign-positive F1 while discussing malignant detection can invert the most important error. ROC-AUC alone does not specify an operating point, and the default classifier threshold is implicit in `model.predict()` (`src/experiment.py:73-76`).

**Action:** Declare the intended positive class and error costs in the manifest/UI. If malignant detection is the use case, either use malignant as the primary positive class or report both class perspectives. Select any threshold on development data only, then report threshold, sensitivity/recall, specificity, precision, NPV, PR-AUC, calibration, confusion-matrix counts, and final-holdout uncertainty. Show the complete selected-model holdout result in the UI instead of only final ROC-AUC (`app.js:69-87`).

### P1 — Report uncertainty and avoid implying a clearly superior winner

**Evidence:** The current leaderboard’s top three development-CV ROC-AUC means are 0.99603, 0.99422, and 0.99381, while their standard deviations are 0.00682, 0.00891, and 0.01015 (`artifacts/leaderboard.csv:2-4`). The runner computes mean/std but does not persist per-fold scores, confidence intervals, paired comparisons, or selection stability (`src/experiment.py:79-95`). The UI says standard deviation is a decision lens but does not render it (`index.html:131-136`; `app.js:94-115`).

**Why it matters:** The leader’s margin over Extra Trees is about 0.0018 ROC-AUC—small relative to fold variability. The current rank is a useful exploratory ordering, not evidence that Logistic Regression is reliably better.

**Action:** Persist fold/repeat-level metrics and add confidence intervals (or a clearly documented bootstrap/paired comparison). Render `mean ± std`/interval beside each primary metric and label close scores as practically tied. If hyperparameter tuning is added, use nested CV or a separately locked validation protocol so the reported uncertainty remains honest.

### P1 — Complete the interactive leaderboard/tradeoff surface

**Evidence:** The cards expose CV ROC-AUC, CV accuracy, and CV fit-time bars (`app.js:88-103`), and the detail panel exposes CV ROC-AUC, accuracy, F1, and fit time (`app.js:106-115`). However, there is no metric selector, sort control, filter, threshold control, uncertainty display, or Pareto/tradeoff view. `renderChart()` renders only ROC-AUC and accuracy bars (`app.js:124-129`), despite the legend advertising CV fit time (`index.html:104-107`); fit time is only indirectly available in the cards/detail panel. The “combined fit time” caption sums per-model CV means (`app.js:69-77`), which is not a measured end-to-end run time.

**Assessment:** This passes the “not static copy” bar, but only narrowly. Users can inspect each candidate, yet cannot change the decision lens or directly explore accuracy-versus-cost/variability tradeoffs.

**Action:** Add a primary-metric/sort control (ROC-AUC, balanced accuracy, F1, fit time), show mean ± std, and add a compact Pareto plot or table for quality versus training cost. Make the fit-time definition explicit and either remove “combined” or rename it to an illustrative sum of CV means. Keep the final holdout visually separate and unavailable as a sorting/selection control.

### P1 — Make AutoGluon runs auditable and comparable to the fallback

**Evidence:** AutoGluon is fit with `medium_quality`, a 60-second per-fit budget, one CPU, and a seed (`src/experiment.py:135-156`). Development CV repeats that fit across ten folds (`src/experiment.py:178-201`). Only the final AutoGluon path records `get_model_best()` (`src/experiment.py:159-173`); the CV row does not retain the internal AutoGluon leaderboard, model count, ensemble status, or fold-level search outputs. The metadata records settings but only serializes sklearn model parameters (`src/experiment.py:325-341`). Sklearn timings surround one estimator `.fit()`, whereas AutoGluon timings include search/ensemble work (`src/experiment.py:116-121`, `src/experiment.py:141-149`).

**Action:** Save AutoGluon’s version, fit summary/internal leaderboard, selected model/ensemble, model count, fold-level status, and total search time. Either use a documented common resource protocol or present backend-specific leaderboards; do not treat the mixed fit-time column as a fair efficiency ranking. In the UI, show when the result is fallback-only and when AutoGluon was actually evaluated.

### P2 — Pin the environment and make the evidence artifacts agree

**Evidence:** The checked-in metadata is rich, but `requirements.txt:1-6` uses open-ended minimum versions and comments AutoGluon out rather than pinning an installable optional environment. The README acknowledges version/environment variation (`README.md:43-48`). More importantly, the tracked `artifacts/run_evidence.svg:1` says “best ROC-AUC: 0.9947” and “tests: 2/2”; the current development leaderboard’s best CV ROC-AUC is 0.9960 (`artifacts/leaderboard.csv:2`), the current test suite has four tests, and the current command metadata says `--no-autogluon` (`artifacts/metrics.json:2-23`). The tracked screenshot `ui_screenshots/project-07.png` also shows older “TABULAR AUTOML”, “earns the handoff”, and “TEST-SET PROOF” wording that does not match the current source (`index.html:7`, `index.html:28-42`).

**Action:** Regenerate the SVG and screenshot from the current artifacts, distinguish development-CV versus final-holdout ROC-AUC, and report the actual test count/run command. Add a pinned lock file (including a documented optional AutoGluon environment) or state explicitly that the manifest is descriptive rather than sufficient for byte-for-byte recreation.

### P2 — Expand tests around the scientific contract

**Evidence:** The tests cover split repeatability, four-row fallback output, ranking fields, metadata, target mapping, and the absence of a final-test metric in the leaderboard (`tests/test_experiment.py:9-68`). They do not test metric direction/positive-class semantics, uncertainty artifact/UI fields, final-metric completeness, artifact drift, AutoGluon completed/failed branches, or the UI’s model-selection behavior.

**Action:** Add contract tests that assert: the holdout never contributes to ranking; selected model/metric names match across all artifacts; target mapping and threshold are explicit; CV uncertainty is present; backend status transitions are preserved; AutoGluon metadata is complete when available; and every checked-in evidence artifact reflects the current run schema.

## Verification performed

- `python3 -m py_compile src/experiment.py src/run_experiment.py tests/test_experiment.py` — passed.
- `node --check app.js` — passed.
- `/private/tmp/cmpe255-project07-venv/bin/python -m pytest -q` — **4 passed**, one environment warning about physical-core detection.
- AutoGluon execution — not run; the checked-in run is explicitly fallback-only and AutoGluon is optional.

## Final disposition

**Acceptable for a reproducible CPU-safe classroom model-comparison demo after evidence copy is refreshed.** Do not present the current output as a clinical operating-point study, production handoff, or statistically decisive AutoML benchmark until P1 items are addressed. The core split/selection protocol should be retained; the next polish pass should focus on uncertainty, class/error semantics, complete holdout reporting, backend auditability, and a richer interactive tradeoff view.
