# Project 10 data-science robustness review

Review date: 2026-08-30  
Scope: CRISP-DM completeness, data handling, preprocessing, split strategy, model selection, evaluation, leakage, reproducibility, and support for conclusions. This is a review only; source code was not modified.

## Executive assessment

This is a clean, runnable teaching demo for one Iris classification baseline, not a complete “CRISP-DM masters curriculum” or a production-ready data-science project. The reported `0.9333` is reproducible for the checked 30-row stratified holdout, and the current code shows no direct preprocessing leakage: the scaler is inside the model pipeline and is fit after the split. The result does not support a generalization or production-performance claim because the evaluation is one small holdout with no locked final test protocol, uncertainty interval, model comparison, or external validation.

## Findings

### [HIGH] F1 — The implemented curriculum is materially narrower than the requested Project 10 scope

Evidence:

- `../PROMPTS_USED.md:17` describes the requested textbook project and explicitly lists quizzes, EDA/preprocessing, clustering, anomaly detection, supervised learning, association rules, LSH, and synthesis.
- `README.md:41-45` calls the implementation a compact walkthrough and acknowledges that it does not claim every advanced module is complete.
- The project contains one executable supervised classifier (`src/crispdm_demo.py:14-20, 63-78`) and its tests/dashboard; there are no implemented clustering, anomaly-detection, association-rule, LSH, quiz, or synthesis modules.

Impact: a learner cannot follow the requested breadth of CRISP-DM analysis, and the six-card UI can give the impression of full phase coverage while showing only one modeling task.

Fix: either re-scope the project title/README to “Iris CRISP-DM baseline” or add the missing modules as reproducible, tested sections with shared data contracts, method-specific evaluation, quizzes, and a synthesis that compares what each method can and cannot answer.

### [HIGH] F2 — A single 30-row holdout is used as the success gate

Evidence:

- `src/crispdm_demo.py:57-60` performs one 80/20 split with 30 test rows and a fixed seed.
- `src/crispdm_demo.py:70-77` evaluates only that holdout; `src/crispdm_demo.py:96-106` records its accuracy as the project evaluation.
- `README.md:31-40` defines success as holdout accuracy `>= 0.90` and separately acknowledges uncertainty and the lack of cross-validation/external validation.
- The artifact has only 10 examples per class in the test set (`artifacts/crispdm_report.json:34-44, 62-93`).

Impact: the pass/fail conclusion is highly sensitive to a few observations and does not estimate expected performance on new samples. As an independent check, the exact 95% binomial interval for 28/30 correct is approximately 0.779–0.992; repeated 5-fold stratified CV (10 repeats, seed 42) varied from 0.900 to 1.000 (mean 0.953, SD 0.035). These checks do not prove production performance, but they show why `0.9333` should be presented as split-specific.

Fix: pre-specify a training-only repeated/nested stratified CV protocol for model selection, retain a final locked test set used once, report uncertainty intervals and per-class support, and validate the threshold against a decision or cost rather than treating a generic fixed threshold as a business requirement.

### [HIGH] F3 — Business understanding is not decision-grade

Evidence: `src/crispdm_demo.py:34-40` defines a generic flower-classification objective, names only “student analyst” and “course reviewer” as stakeholders, and uses “holdout accuracy >= 0.90” as the success criterion. No user decision, action, error costs, operational constraints, target population, or acceptance rule for class-specific failures is specified.

Impact: the metric pass does not establish that the model solves a meaningful business problem. The threshold is an educational assertion, not a validated requirement.

Fix: state who would act on each prediction, the consequence of each error, data-collection constraints, acceptable latency and coverage, and class-specific/cost-weighted acceptance criteria. Tie model selection and monitoring to those decisions.

### [MEDIUM] F4 — Data understanding and quality checks are too shallow for a robust workflow

Evidence:

- `src/crispdm_demo.py:43-53` records only the loader name, row/feature/class counts, missing-value count, and class counts. It does not inspect distributions, ranges, outliers, duplicates, label quality, units, provenance, or representativeness.
- `README.md:3` identifies the built-in loader but records no dataset/version/license/hash metadata.
- `artifacts/iris_snapshot.csv:1-151` is a useful snapshot, but the pipeline has no schema or value validation against it.

An additional read-only check found one duplicate feature vector in the 150-row Iris data (`[5.8, 2.7, 5.1, 1.9]`, both class 2); no exact feature-row overlap crossed the fixed train/test split. The current result is therefore not shown to be contaminated by that duplicate, but duplicate handling is undocumented.

Impact: data-quality assumptions are implicit, and future replacement data could silently violate the model’s schema or evaluation assumptions.

Fix: add a data-quality report and assertions for schema, units, ranges, duplicates, missingness, label validity, class balance, and train/test overlap; record source/version/license and a content hash; document why the data represents the intended population.

### [MEDIUM] F5 — There is no empirical model selection or meaningful baseline comparison

Evidence:

- `src/crispdm_demo.py:63-67` constructs exactly one `StandardScaler` + `LogisticRegression` pipeline.
- `artifacts/crispdm_report.json:40-42` records only that algorithm, and `README.md:33-35` presents it as the modeling choice.
- The tests (`tests/test_crispdm_demo.py:14-18, 28`) check that the model runs and clears the threshold, not that it beats a baseline or is selected by a predeclared procedure.

Impact: the rationale that the model is “strong enough” is qualitative; the project cannot show whether scaling, regularization, or another simple classifier changes the result.

Fix: include a majority-class baseline and a small, justified candidate set (for example, linear, tree, and nearest-neighbor models), compare them with training-only CV, tune only inside the training procedure, and record the selection metric and tie-breaking rule.

### [MEDIUM] F6 — Preprocessing is leakage-safe for this clean dataset but not a complete input contract

Evidence:

- The positive control is correct: `src/crispdm_demo.py:63-67` places `StandardScaler` in a `Pipeline`, and `src/crispdm_demo.py:89-95` fits it only on `x_train` before holdout prediction.
- `src/crispdm_demo.py:49` reports zero missing values, but there is no imputation, schema validation, range/unit check, or handling policy for invalid future inputs.

Impact: the notebook-free demo is safe for the bundled clean Iris matrix, but a production caller could send missing, reordered, nonnumeric, or out-of-range features and receive an exception or an unexamined prediction.

Fix: define and enforce the feature schema at fit and inference time; add an explicit missing/invalid-value policy; keep every learned transformation inside the pipeline; and add tests for malformed inputs and train-only fitting.

### [MEDIUM] F7 — “Deployment” is documentation only; no deployable model or inference contract is produced

Evidence: `src/crispdm_demo.py:107-110` writes a next-step sentence and monitoring labels but does not serialize the fitted pipeline, expose inference, record model/data versions, or implement monitoring. `README.md:17-27, 38-40` describes a static dashboard and explicitly says the example stops before production deployment. The project artifact list has JSON/CSV evidence but no model file or API.

Impact: the deployment phase cannot be tested end to end, and the proposed signals (“input ranges”, “class distribution”, and “accuracy on reviewed labels”) have no collection cadence, thresholds, ownership, or alert action.

Fix: save a versioned pipeline plus metadata, provide a typed inference entry point/API, add contract and smoke tests, and specify monitoring windows, drift/performance thresholds, alert owners, retraining criteria, and rollback behavior.

### [MEDIUM] F8 — Reproducibility depends on an unpinned environment and underpowered tests

Evidence:

- `requirements.txt:1-3` contains only lower bounds (`numpy>=1.24`, `scikit-learn>=1.2`, `pytest>=7.0`), so future resolver choices can change numerical behavior or APIs.
- `src/crispdm_demo.py:23, 58-60, 66` fixes the split/model seed, which is good, but the report does not record Python, NumPy, scikit-learn, or BLAS versions, the data hash, or the full estimator configuration.
- `tests/test_crispdm_demo.py:6-27` has only three tests: split repeatability/size, threshold/artifact existence, and top-level phase keys.

Impact: the current artifacts were reproducible in the supplied `.venv` (Python 3.14.7, NumPy 2.5.2, scikit-learn 1.9.0), but a fresh environment is not guaranteed to reproduce them, and tests would not catch metric/schema drift.

Fix: commit a lock/constraints file or supported-version matrix, record runtime/dependency/data/model metadata in the report, and test artifact schema, class supports, metric determinism, pipeline behavior, and a known prediction fixture.

### [MEDIUM] F9 — Evaluation coverage is insufficient for the stated “nuances” and for operational conclusions

Evidence:

- `src/crispdm_demo.py:70-78` reports accuracy, a confusion matrix, and a classification report only.
- `artifacts/crispdm_report.json:43-94` contains no confidence interval, calibration/probability assessment, ROC/PR analysis, cost-sensitive metric, subgroup/slice analysis, or failure-case review.
- `index.html:76-81` labels the card “PASS” from the single accuracy threshold, while `README.md:38-40` lists the missing uncertainty, cost-sensitive, fairness, and external-validation work as limitations.

Impact: the artifact supports the narrow claim “this fixed split produced 28/30 correct with the listed per-class scores.” It does not support “the model is reliable,” “ready to deploy,” or that the 0.90 threshold corresponds to acceptable risk.

Fix: report confidence intervals, repeated-CV distributions, calibrated probabilities where used, class- and slice-level errors, cost/utility metrics, and representative failure cases. Make the UI conclusion explicitly split-specific until a locked external evaluation exists.

## Positive controls observed

- `src/crispdm_demo.py:57-60` uses a stratified split with a fixed seed.
- `src/crispdm_demo.py:63-67, 89-95` correctly prevents scaler fitting on holdout data.
- `README.md:38-40` does disclose that Iris is tiny and that the single holdout is not a production claim.
- The generated JSON and CSV are inspectable, and the fixed-seed rerun reproduced both artifacts byte-for-byte.

## Checks run

All checks below were read-only with respect to source; the rerun wrote only to `/private/tmp/cmpe255_project10_review_run`.

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | **3 passed** in 1.48s |
| `.venv/bin/python src/crispdm_demo.py --output-dir /private/tmp/cmpe255_project10_review_run` | **Passed**, reported accuracy 0.933 |
| Compare regenerated JSON/CSV with checked-in artifacts | **Byte-identical** |
| `python3 -m compileall -q src tests` | **Passed** |
| `node --check src/app.js` | **Passed** |
| `python3 -m json.tool artifacts/crispdm_report.json` | **Passed** |
| Explicit fixed-split exact-row overlap check | **No train/test overlap**; one duplicate exists within the full data |
| Independent repeated 5-fold stratified CV, 10 repeats, seed 42 | Accuracy mean **0.953**, SD **0.035**, range **0.900–1.000** |

The system Python initially could not run the README commands because NumPy and pytest were not installed; the project’s local `.venv` supplied the declared dependencies and was used for the successful checks.
