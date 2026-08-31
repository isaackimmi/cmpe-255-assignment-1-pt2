# Data-science robustness review — Project 07

Reviewed 2026-08-30. Scope: the experiment runner, generated artifacts, tests, README, and browser dashboard in this project. This is a review-only artifact; source code was not modified.

## Overall assessment

The implementation is a clean, small exploratory sklearn comparison with an explicit optional AutoGluon branch. The stratified split is reproducible, and the sklearn scaler is inside a training-time pipeline, so there is no apparent feature-preprocessing leakage from the test rows. However, the experiment reuses the test split to rank/select models. That is evaluation leakage and invalidates the claim that the test set is untouched. The displayed leader and its 0.9947 ROC-AUC should therefore be treated as a selected holdout result, not an unbiased final estimate or production handoff decision.

The project is reasonable as a CPU-safe teaching demo after its claims are narrowed. It is not yet a statistically defensible AutoML benchmark or deployment-readiness evaluation.

## Findings

### [HIGH] The test set is used for model selection

Evidence:

- `src/experiment.py:102-108` creates one 80/20 train/test split and evaluates every candidate on `X_test`/`y_test`.
- `src/experiment.py:115-117` sorts the candidates by `roc_auc` and assigns the ranks before writing `leaderboard.csv`; that ROC-AUC is computed from the same test rows in `src/experiment.py:50-63`.
- The generated leaderboard confirms that four candidates were ranked on their test ROC-AUC (`artifacts/leaderboard.csv:1-5`).
- The AutoGluon candidate follows the same pattern: it is trained on `X_train` but scored on `X_test` and then appended to the same ranked table (`src/experiment.py:67-97`, `src/experiment.py:111-115`).

This is not feature leakage, but it is test-set reuse for model selection. Re-running or changing candidates based on this leaderboard causes the test set to influence the chosen model, so the winning test score is optimistically biased. It directly contradicts `README.md:40` and the dashboard’s “TEST-SET PROOF” and “Rank only on untouched test ROC-AUC” claims (`index.html:40-42`, `index.html:154`, `app.js:112-114`).

Concrete fix: split into development and final test data. Use repeated stratified cross-validation or a validation split inside the development data for model comparison, hyperparameter selection, and threshold selection. Fit the selected pipeline on all development data, evaluate the final locked model on the test set exactly once, and keep selection metrics separate from final test metrics in the artifacts/UI. If the leaderboard remains exploratory, label it explicitly as validation/CV performance rather than test performance.

### [HIGH] A single 114-row holdout is too unstable for a definitive winner

Evidence:

- `artifacts/dataset_summary.json:2-8` reports 569 total rows and only 114 test rows from one fixed split.
- The reported ROC-AUCs are close for the top candidates: 0.9947, 0.9868, and 0.9851 (`artifacts/leaderboard.csv:2-5`).
- There are no confidence intervals, repeated-split results, paired comparisons, or standard errors in `src/experiment.py:50-63` or the artifacts.

The fixed seed makes this particular split repeatable, but not representative. With four candidates and a small holdout, the rank order can be driven by sampling noise, and the displayed precision gives a false sense of certainty. This is especially consequential because the same holdout is already being used for selection.

Concrete fix: use repeated stratified CV for development comparisons and report mean, standard deviation, and confidence intervals for the primary metric. For a final locked test, report an interval (for example, bootstrap or an appropriate DeLong interval for ROC-AUC) and avoid declaring a winner when differences are not practically or statistically distinguishable.

### [MEDIUM] The sklearn path is a fixed comparison, not an auditable hyperparameter search

Evidence:

- All four sklearn configurations are hard-coded in `src/experiment.py:33-47`; there is no search space, trial loop, cross-validation, or selection protocol.
- The AutoGluon path specifies a preset and time budget (`src/experiment.py:80-85`) but does not persist its internal leaderboard, selected model configuration, trial count, or search history.
- `metrics.json` records only the backend, ranking metric, seed, and model names (`artifacts/metrics.json:2-11`).

The project can honestly call this a small model comparison, but “AutoML/model search” is stronger than what the fallback demonstrates. The fixed values may have been chosen before the run, but the repository does not make that provenance auditable; if they were adjusted after inspecting holdout results, the selection leakage is worse.

Concrete fix: predeclare candidate families and hyperparameter ranges, select them using inner CV or a validation set, and record the search budget, scoring protocol, all tried configurations, and selected configuration. For AutoGluon, persist the version, presets, time limit, model leaderboard, and whether an ensemble was selected.

### [MEDIUM] AutoGluon and sklearn results are not directly comparable, and failures collapse into the fallback label

Evidence:

- AutoGluon uses a 60-second `medium_quality` search and may ensemble models (`src/experiment.py:80-85`), while sklearn fit time is measured only around each estimator’s `.fit()` call (`src/experiment.py:50-53`).
- AutoGluon fit time therefore includes search/ensemble overhead, while the sklearn values do not use an equivalent budget or accounting boundary (`src/experiment.py:79-86`, `src/experiment.py:63`, `artifacts/leaderboard.csv:2-5`).
- Any AutoGluon exception is caught and converted into no AutoGluon row (`src/experiment.py:98-99`); `run_experiment()` then reports `sklearn_fallback` (`src/experiment.py:128-130`). The current artifact specifically says AutoGluon was disabled by the caller (`artifacts/metrics.json:2-3`).

The backend is labeled more honestly than pretending sklearn is AutoGluon, but a failed AutoGluon run and an intentionally disabled run are not the same experimental condition. The mixed leaderboard also does not support a fair fit-time comparison.

Concrete fix: record `requested_backend`, `attempted_backend`, `backend_status`, and failure type separately. Compare under a documented common resource protocol, or present AutoGluon and sklearn leaderboards separately. Report AutoGluon search time and model count independently from single-estimator fit time.

### [MEDIUM] Reproducibility metadata is insufficient, especially for AutoGluon

Evidence:

- The code records only seed and split fraction (`src/experiment.py:118-135`); the artifacts do not include Python/scikit-learn/AutoGluon versions, hardware, command line, dataset version/hash, or run identifier (`artifacts/dataset_summary.json:1-8`, `artifacts/metrics.json:2-11`).
- The AutoGluon call has no explicit run seed in `src/experiment.py:80-85`, and the README acknowledges that AutoGluon results can vary by version (`README.md:46`).
- Fit times are wall-clock measurements rounded to four decimals (`src/experiment.py:50-63`) and are inherently environment-dependent.

`random_state=255` makes the split and the configured sklearn estimators substantially more repeatable, but it does not make the full experiment reproducible across dependency versions or machines. The UI’s “REPRODUCIBLE / SEED 255” badge (`index.html:42`) overstates what is captured.

Concrete fix: record Python and package versions, OS/CPU information, exact command, dataset identity and hash, all effective model parameters, backend/search settings, explicit seeds where supported, and a run timestamp/ID. Treat fit time as hardware-specific and include a measurement protocol.

### [MEDIUM] Metrics do not define the clinical positive class or operating point

Evidence:

- `load_data()` returns the raw target without persisting target names or class semantics (`src/experiment.py:24-26`).
- F1 uses sklearn’s default positive label and ROC-AUC uses probability column 1 (`src/experiment.py:55-62`), while `dataset_summary.json` has no target mapping or class counts (`artifacts/dataset_summary.json:1-8`).
- The dashboard frames the use case as ranking “malignant vs. benign” (`index.html:150`) but shows only accuracy, balanced accuracy/F1 in artifacts, and ROC-AUC; it does not show sensitivity, specificity, precision, PR-AUC, confusion matrices, calibration, or a selected threshold (`src/experiment.py:59-63`, `index.html:112-114`).

For a diagnostic example, “which class is positive” and the cost of false negatives versus false positives must be explicit. ROC-AUC is threshold-free and does not establish safe operation at any clinical threshold; default 0.5 predictions and F1 alone do not answer that question.

Concrete fix: persist target names and the positive class, choose the operating threshold on development data, and report sensitivity/recall, specificity, precision/NPV, PR-AUC, calibration, confusion matrix, and uncertainty. Make the business metric reflect the stated error costs.

### [MEDIUM] Dashboard language presents exploratory output as proof or handoff evidence

Evidence:

- The page title/hero calls the page “AutoML leaderboard” and “TABULAR AUTOML” (`index.html:6-7`, `index.html:28-30`) even when the generated artifact is explicitly `sklearn_fallback` (`artifacts/metrics.json:2`).
- The hero says “TEST-SET PROOF” (`index.html:40-42`), the workflow says ranking is on an “untouched test” (`index.html:154`), and the detail panel says the leader is top-ranked on the untouched test split (`app.js:110-114`).
- The README calls the result a model handoff view (`README.md:5`, `README.md:23`) despite the selection and evaluation issue above.

These claims can cause a reader to interpret the 0.9947 result as a final unbiased performance estimate. The backend status card is transparent about fallback availability, but it does not correct the broader AutoML/proof/handoff framing.

Concrete fix: after correcting the evaluation protocol, reserve “final test” and “handoff” wording for the one-time locked evaluation. Until then, use “exploratory benchmark,” “development leaderboard,” and “holdout estimate after candidate selection.” Change the hero and workflow copy so the fallback is described as sklearn comparison rather than AutoML.

### [LOW] Tests do not guard the central evaluation contract

Evidence:

- `tests/test_experiment.py:8-16` checks dataset shape and repeatability of the split.
- `tests/test_experiment.py:18-28` checks that four rows, ranks, ROC-AUC ranges, backend labels, and a few metadata fields are written.
- No test asserts a development/validation/test protocol, prevents test-based ranking, validates target semantics, checks backend failure status, or verifies the reproducibility manifest.

The current tests can pass while the main scientific claim remains invalid. They are artifact smoke tests, not robustness tests.

Concrete fix: add tests for the corrected split roles, selection metric versus final-test metric, target mapping and class counts, metadata/artifact consistency, backend status transitions, and the documented CLI/reproducibility manifest.

### [LOW] Fit-time numbers are not a reliable cross-model efficiency metric

Evidence:

- Sklearn timing surrounds only `.fit()` (`src/experiment.py:50-53`), while AutoGluon timing surrounds the full predictor fit/search (`src/experiment.py:79-86`).
- The UI presents fit time as a directly comparable leaderboard metric (`index.html:104-107`, `app.js:93-97`) without hardware, warm-up, parallelism, or repeated-run context.

Concrete fix: define whether preprocessing, search, ensembling, and serialization are included; use a common resource budget; report median and variability over repeated runs; and avoid ranking efficiency from one wall-clock observation.

## Positive controls already present

- `train_test_split(..., stratify=y, random_state=SEED)` gives a deterministic stratified split (`src/experiment.py:20-30`).
- Standardization is inside a sklearn pipeline, so it is fitted as part of model fitting on training data rather than precomputed on all rows (`src/experiment.py:35-37`, `src/experiment.py:50-52`).
- The AutoGluon predictor receives training features/labels and test labels are dropped before prediction (`src/experiment.py:73-88`); the main problem is subsequent test-based ranking, not use of test labels as predictor inputs.
- The fallback is named explicitly in the current artifact (`artifacts/metrics.json:2-3`) and the README acknowledges that it does not reproduce AutoGluon’s ensembling/search space (`README.md:34-36`).

## Checks run

- PASS — `python3 -m py_compile src/experiment.py src/run_experiment.py tests/test_experiment.py`.
- PASS — `node --check app.js`.
- PASS — read-only artifact checks: required artifacts exist; train/test counts sum to 569; ranks are sequential; leaderboard ROC-AUC is descending; metric fields are populated; `metrics.json` model order matches the CSV.
- NOT RUN — `python3 -m pytest -q` could not start in the current environment: the active Python 3.14.7 installation has no `pytest` module (and no `scikit-learn` module). The README’s historical “pytest passed 2/2” statement was not independently reproduced in this environment.
- NOT RUN — AutoGluon execution: it is optional and the checked-in artifact was generated with `--no-autogluon`; the current environment also lacks the required sklearn dependency.

## Recommended order of remediation

1. Correct the evaluation roles and remove test-based ranking; update all test/proof/handoff wording.
2. Add repeated/nested development validation, uncertainty estimates, and an explicit operating threshold/positive class.
3. Add a reproducibility manifest and complete backend/search metadata.
4. Expand tests to enforce the evaluation contract, then run them in a clean environment installed from a pinned lock file.

