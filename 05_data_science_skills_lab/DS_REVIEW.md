# Project 05 Data-Science Robustness Review (historical)

> **Historical document.** This review captures the pre-polish implementation and is retained for traceability. Its earlier findings about imputed regression targets, in-sample classification, raw clustering, and weak validation were addressed in the current pipeline. Use [README.md](README.md) and `artifacts/metrics.json` as the current source of truth for evaluation design, results, and verification.

## Scope and overall assessment

Reviewed the ingestion/cleaning, EDA, regression, classification, clustering, plotting, artifact generation, dashboard-facing outputs, tests, and reproducibility notes in an earlier revision of this project. The implementation was a useful offline teaching fixture, but that revision had methodological and validation gaps; those findings are superseded by the current implementation and artifacts.

Severity tags below use `HIGH` for issues that can make a reported result materially misleading or make ordinary inputs unsafe, `MEDIUM` for important methodological or robustness gaps, and `LOW` for documentation/interpretability improvements.

## Findings

### [HIGH] Regression evaluation includes a synthetic test target and leaks preprocessing across the split

Evidence:

- `src/skills_lab.py:12-16` computes each median over all cleaned rows before any train/test split and writes the median into the data in place.
- `run_lab.py:4-6` calls `load_clean` first, then takes the first 16 rows as training data and scores the remaining rows.
- `data/customer_health.csv:24-25` contains the retained `C023` record with missing `monthly_usage` (the duplicate is removed, leaving one missing target in the test tail).
- The generated `artifacts/summary.json` reports `C023` with `actual_usage: 56.5`, although 56.5 is an imputation rather than an observation. Including that row produces MAE 4.3804/RMSE 7.8707; excluding it from the six observed test targets produces MAE 1.7270/RMSE 1.8924.

Why it matters: an evaluation target must be an observed outcome. In addition, fitting an imputer using rows from the eventual test set allows test-distribution information into preprocessing. The current error is therefore not a valid estimate of performance on observed future usage.

Concrete fix: split after schema/domain validation but before fitting preprocessing. Fit numeric imputers on training features only, apply them to validation/test features, and exclude rows with missing regression targets from scoring (or use a clearly labeled missing-target strategy). Report imputation counts separately for train and test and retain a missingness indicator where appropriate.

### [HIGH] Classification accuracy, precision, and recall are resubstitution metrics, not held-out performance

Evidence:

- `run_lab.py:7-8` creates `cls` for every cleaned row from the fixed rule and immediately passes the same rows and labels to `classification_metrics`.
- `artifacts/metrics.json` reports accuracy 0.8261, precision 1.0, and recall 0.7778 from the full 23-row dataset; there is no classification train/test split or cross-validation.
- The class distribution is 18 renewed versus 5 not renewed, so the majority-class accuracy baseline is already 0.7826. The reported rule improves this fixture by only about 4.35 percentage points in-sample.

Why it matters: even if the rule was fixed a priori, scoring it on the same rows cannot establish generalization; if its threshold was chosen after looking at these labels, the estimate is additionally optimistic. Accuracy is also incomplete for this imbalanced sample; the perfect precision should not be read as evidence of a reliable production classifier.

Concrete fix: define the rule and threshold from domain knowledge before evaluation, or tune them on a training fold only, then report held-out or repeated stratified cross-validation results with sample counts. Add F1, specificity/balanced accuracy, and confidence intervals or fold variability, and compare against the majority baseline.

### [HIGH] Cleaning is conversion, not validation; malformed and out-of-domain records can enter the analysis

Evidence:

- `src/skills_lab.py:4-11` assumes every required column exists, converts with `float`/`int`, and never validates finite values, ranges, categorical values, or the binary label domain.
- `float("nan")` is accepted as a numeric value; it can contaminate sorted medians and downstream statistics. Negative tenure/tickets and `renewed=2` are also accepted.
- Empty or all-missing numeric columns reach `vals[len(vals)//2]` at `src/skills_lab.py:14` and fail with an index error; an empty label fails at `src/skills_lab.py:11`.
- Duplicate IDs are removed at `src/skills_lab.py:7-9` before the duplicate record is compared with the retained record, so conflicting duplicates are silently resolved by “first row wins.”

Why it matters: a data-quality step that silently accepts `NaN`, impossible values, invalid labels, or conflicting customer records can produce plausible but invalid statistics and model inputs. Failures are also not reported with row/column context.

Concrete fix: validate the required schema and uniqueness policy explicitly; reject or quarantine non-finite values; enforce nonnegative/domain bounds and `renewed in {0,1}`; validate `plan`; and emit a row-level validation report. For duplicate IDs, either require identical records or resolve them with a documented aggregation/business rule rather than silently retaining the first row.

### [MEDIUM] Regression split is arbitrary, order-dependent, and weakly documented

Evidence:

- `run_lab.py:6` hardcodes `split=16` and uses `xs[:split]`/`usage[:split]` versus the remaining rows. No shuffle, fold generation, or temporal meaning for CSV order is established.
- The test tail is mostly longer-tenure customers than the training prefix, while the final `C023` row has tenure 11 and imputed usage 56.5; reordering the CSV changes the estimate without changing the records.
- `src/skills_lab.py:22-23` fits an unconstrained least-squares line but the pipeline reports only MAE/RMSE and no baseline, R², residual inspection, or uncertainty.

Why it matters: a single seven-row, order-dependent split gives high-variance and potentially distribution-shifted results. A line can be a useful baseline, but the current output does not show whether it beats a simple baseline or whether residuals support the linear form.

Concrete fix: choose and document a real validation design (time split only when row order represents time; otherwise a seeded shuffle or repeated K-fold split), keep preprocessing inside each fold, and report fold variability. Add a baseline such as train-mean prediction, R² with its limitations, residual plots/checks, and prediction uncertainty. Preserve a final untouched test set if a generalization claim is needed.

### [MEDIUM] K-means is dominated by feature scale and has no k-selection or stability evidence

Evidence:

- `run_lab.py:7-8` clusters raw `monthly_usage` and `support_tickets`.
- `src/skills_lab.py:31` uses unweighted squared Euclidean distance. In this fixture, usage spans 61 units (18–79) while tickets spans 6 units (0–6); the corresponding squared ranges differ by roughly two orders of magnitude, so usage largely determines assignment.
- `run_lab.py:8` fixes `k=2` and reports only cluster sizes/centers. There is no inertia, silhouette-like separation check, repeated initialization, or cluster stability assessment.

Why it matters: the resulting “groups” are primarily usage bands, not a balanced joint segmentation of usage and support burden. A single random initialization and arbitrary k do not establish that two meaningful groups exist.

Concrete fix: scale features (with a documented choice and fit scope), then run multiple seeded initializations. Report inertia plus a separation/stability diagnostic across candidate k values, and explain the business/analytical interpretation of each cluster. If raw units are intentionally weighted, state and justify those weights instead of presenting the result as neutral k-means.

### [MEDIUM] Numerical helpers silently accept mismatched inputs and have undefined edge-case behavior

Evidence:

- `src/skills_lab.py:20-27` uses `zip(xs, ys)` without checking equal lengths. For example, `correlation([1,2,3], [1,2])` returns `0.5` rather than rejecting the invalid input; the means are computed from full inputs while the numerator uses only paired prefixes.
- `mean`, `regression_metrics`, and `classification_metrics` divide by zero on empty inputs (`src/skills_lab.py:18-27`). `linear_regression` divides by zero for constant x (`src/skills_lab.py:22-23`).
- `src/skills_lab.py:28-36` does not validate dimensions, finite values, `k`, or iteration count: empty points, `k > n`, and `k=0` fail with low-level errors, while `iterations=0` raises `UnboundLocalError`.
- When `kmeans` reaches its iteration limit, `labels` were computed before the final center update but the returned centers are after that update (`src/skills_lab.py:31-36`), so labels and centers can be inconsistent.

Concrete fix: add shared input validation for non-empty, equal-length, finite vectors and explicit policies for constant variance. Raise clear `ValueError`s with the offending shape/field. Validate `1 <= k <= n`, positive iterations, and equal point dimensions; recompute labels after the final center update and return convergence/inertia metadata.

### [MEDIUM] Plot generation fails on constant ranges and omits scale/legend information needed to interpret the result

Evidence:

- `src/skills_lab.py:38` and `src/skills_lab.py:44` divide by `max(values)-min(values)` without a zero-range guard. Constant x or y values therefore raise `ZeroDivisionError` instead of producing a valid plot.
- `src/skills_lab.py:40` and `src/skills_lab.py:47` draw axes and titles but no tick labels, numeric ranges, units, or legends. The cluster plot uses two hardcoded colors and does not identify which color maps to which cluster.
- The dashboard captions in `app.js:61-64` describe trends/groups, but the SVG itself does not provide enough scale information to independently verify those claims.

Concrete fix: use a safe scale for constant dimensions (center the points or add a small display padding), emit numeric tick labels and units, and add legends for renewal/cluster colors. Test SVG generation with empty, singleton, and constant-range inputs and verify the rendered artifacts visually.

### [MEDIUM] Existing tests cover only happy-path helper examples, not pipeline integrity or robustness

Evidence:

- `tests/test_skills_lab.py:5-12` contains four tests: one fixture cleaning assertion, one regression assertion, one confusion-matrix assertion, and deterministic k-means. There are no tests for `run_lab.py`, generated JSON/SVG consistency, split leakage, invalid schemas, invalid domains, missing targets, mismatched vector lengths, degenerate plots, or k-means convergence.

Concrete fix: add fixture-driven tests for each validation rule and failure mode, a pipeline test that regenerates artifacts and checks counts/keys, tests proving test targets are observed and preprocessing is fold-local, and SVG smoke tests for degenerate ranges. Add a small integration check for the dashboard’s expected artifact paths if the UI is part of the deliverable.

### [LOW] Artifact metadata is partly hardcoded and the reproducibility note overstates what seed 255 controls

Evidence:

- `run_lab.py:8` hardcodes `"raw_rows":24` and `"missing_values_imputed":1` instead of deriving both from the input and the cleaning report.
- `README.md:40` says seed 255 is used for “the split/clustering initialization,” but `run_lab.py:6` uses a deterministic positional split with no random seed; seed 255 is passed only indirectly through the default `kmeans` argument at `src/skills_lab.py:28`.
- `README.md:48` records result values manually, so changing the CSV or pipeline can leave the integration-verification prose stale.

Concrete fix: derive all quality counts from `load_clean`, record the input file hash and configuration (split strategy, seed, k, iterations, scaling), and generate result summaries from the same run. Update the README from generated metadata or clearly label it as a snapshot.

### [LOW] Feature timing and causal interpretation are not defined

Evidence:

- `run_lab.py:7` uses current `monthly_usage` and `support_tickets` to classify `renewed`, while `data/customer_health.csv:1` provides no observation-window or event-timing fields.
- `src/skills_lab.py:20-21` computes ordinary Pearson correlation for the EDA outputs, including the binary renewal indicator. This is a valid descriptive point-biserial-equivalent calculation for finite paired data, but no uncertainty, outlier sensitivity, or adjustment for tenure/plan is reported.
- `app.js:3-6` presents usage/renewal relationships and customer groups, and `README.md:29` appropriately calls the data synthetic, but the feature timing needed for a pre-renewal prediction task is not stated.

Concrete fix: report sample size and uncertainty/robustness checks for correlations, inspect influential points, and consider stratified or adjusted analyses for tenure/plan. Document when each feature is measured relative to renewal, ensure all prediction features precede the label, and explicitly describe the correlations as association rather than causal evidence. If this is only an educational retrospective rule, label it that way in the artifacts/dashboard.

## Checks run during the historical review

All checks were run from the project root, and no source code was modified.

- `python3 -m unittest discover -s tests -v` — passed, 4/4 at that time; the current suite is 8/8.
- `python3 run_lab.py` — completed successfully and reproduced the existing metrics/artifacts.
- `python3 -m compileall -q src run_lab.py` — passed.
- Targeted edge-case probes confirmed the failure modes above: mismatched correlation returned `0.5`; empty/constant inputs raised `ZeroDivisionError` or low-level `ValueError`/`UnboundLocalError`; constant-range SVGs raised `ZeroDivisionError`.

## Recommended remediation order

1. Make validation explicit and make the split/imputation/evaluation boundaries correct, especially excluding imputed regression targets from scoring.
2. Replace in-sample classification metrics with a documented held-out/CV evaluation and appropriate imbalance-aware metrics.
3. Scale and validate clustering, then add k-selection/stability evidence.
4. Harden numerical and plotting helpers with clear shape/domain checks and degenerate-input tests.
5. Derive artifact metadata and document the actual reproducibility controls and feature timing.
