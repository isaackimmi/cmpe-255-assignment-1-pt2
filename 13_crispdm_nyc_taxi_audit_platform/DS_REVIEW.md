# Project 13 data-science robustness review

## Scope and overall assessment

Reviewed the target/data generator, cleaning and feature construction, chronological split, model and metrics, audit report, inference path, dashboard claims, fallback/sample-data behavior, reproducibility documentation, tests, and generated artifacts. Source code was not modified.

The implementation is a useful deterministic smoke-test/demo, and the checked-in pipeline reproduces its reported numbers. It is not yet evidence that a model generalizes to NYC taxi trips: the entire evaluation is generated from a simple formula that uses the same variables supplied to the model, preprocessing leaks holdout information, audit results are incompletely surfaced by the UI, and evaluation has only one small holdout with no baseline or uncertainty interval.

Severity uses the following convention: **P1** materially limits validity or could mislead a model/data consumer; **P2** is an important robustness or reproducibility gap; **P3** is a lower-risk quality improvement.

## Findings

### [P1] The reported performance is synthetic-DGP performance, not NYC taxi performance

**Evidence:** `src/platform.py:23-44` creates every row in memory. In particular, `src/platform.py:35-36` constructs the target from distance, rush-hour status, weekend status, and independent noise, then clips it. Those same variables are included in `FEATURES` at `src/platform.py:18-20`. The pipeline always calls `make_sample_data` at `src/platform.py:81-84`; there is no real TLC ingestion path. The README discloses this at `README.md:15` and `README.md:44-50`, and the generated report repeats it at `artifacts/crispdm_report.md:24-25`.

**Impact:** The model is being evaluated on data generated from a known, stable mechanism with the main signal deliberately exposed as input. The 2.794-minute MAE, 3.622-minute RMSE, 0.892 R², and 84.5% within-five-minute rate (`artifacts/metrics.json:1-8`) therefore measure recovery of this toy mechanism. They do not support conclusions about NYC traffic, dispatch use, route coverage, seasonal drift, or operational accuracy, even though the product name and narrative use “NYC taxi.” The disclosure prevents this from being a hidden substitution, but it does not make the resulting metrics production evidence.

**Concrete fix:** Keep the generator as a fast test fixture, but add an explicit TLC input mode with a pinned dataset/version, schema and unit checks, a data hash, and documented licensing/provenance. Run all headline metrics on a held-out real-data time period and label synthetic results as smoke-test metrics. If real data is unavailable, rename the result as a synthetic demonstration and avoid model-health or dispatch conclusions.

### [P1] Holdout information is used to fit feature imputation

**Evidence:** `_features` fills every numeric feature with `frame[col].median()` at `src/platform.py:65-73`. It is called on the complete cleaned dataset before splitting at `src/platform.py:85-88`; the split and model fit happen only afterward at `src/platform.py:87-90`. Thus the median includes future/holdout rows. The dashboard and README claim “no future leakage” at `dashboard/index.html:45` and `README.md:40`, but that claim is too strong.

**Impact:** This is preprocessing leakage. For the default seed, the full-data distance median is 3.2565 versus 3.2510 using training rows only; the observed metric difference is small because only seven missing distances are injected and only one is in the holdout. The methodology is nevertheless invalid for a real missingness pattern and can become materially optimistic if future distributions or missing values differ.

**Concrete fix:** Perform only deterministic timestamp derivations before the split. Put `SimpleImputer` (preferably with a missingness indicator) inside the fitted training pipeline, or fit imputation statistics on `train` and apply them unchanged to `test` and inference. Add a regression test that changes holdout feature values and verifies training preprocessing statistics do not change.

### [P1] Audit observations are not consistently represented or acted upon

**Evidence:** `audit_data` reports IQR observations for passenger count, distance, and target at `src/platform.py:50-62`; the checked-in report contains 94 passenger-count, 43 distance, and 37 duration IQR observations at `artifacts/audit_report.json:25-29`. The dashboard only renders missing distances, non-positive durations, duplicate IDs, duration IQR outliers, and missing columns at `dashboard/app.js:27-42`. It omits `invalid_distance_count`, passenger-count IQR observations, and distance IQR observations. Consequently, its “50 findings to review” summary is a count of selected UI rows, not all audit observations. Also, the modeling path only drops non-positive targets at `src/platform.py:85`; it neither resolves the other IQR findings nor records whether each one was retained, corrected, or excluded.

**Impact:** A user can reasonably read the dashboard as a complete audit and miss substantial reported observations. IQR is also applied mechanically to low-cardinality `passenger_count`; values of 4 or 5 can be valid passengers rather than data errors. Treating every IQR observation as a generic “Review” signal without domain rules creates both false positives and incomplete review coverage.

**Concrete fix:** Define field-specific validity rules and severity thresholds (for example, passenger range, distance range, and target range) separately from descriptive distribution flags. Emit row IDs and an action/status for each finding. Display every audit category or explicitly label the UI as a subset, and reconcile the summary count with a documented unique-row/finding definition. Make the pipeline fail or require an explicit policy decision when critical schema/range checks fail.

### [P2] The temporal split is directionally correct but does not establish temporal generalization

**Evidence:** The data is sorted by pickup time and split into one first-80%/last-20% block at `src/platform.py:81-95`; the artifact calls it `chronological 80/20` at `artifacts/metrics.json:8`. For the default run this is 955 train and 239 test rows, with the holdout spanning only 2024-02-18 18:28 through 2024-02-29 23:50. No rolling-origin folds, gap/embargo, repeated periods, baseline, or subgroup metrics are implemented. The report acknowledges a single model and illustrative metrics at `artifacts/crispdm_report.md:12-25`.

**Impact:** One 239-row block cannot show stability across weeks, seasons, holidays, changing traffic regimes, or rare routes. The headline score has no uncertainty interval and no comparison against a simple baseline, so “model health” is not calibrated against a meaningful operational reference.

**Concrete fix:** Add rolling-origin validation over multiple future windows, with an explicit gap if labels or aggregates could overlap the boundary. Report mean and dispersion or confidence intervals, plus baselines such as global mean, route-distance regression, and last-period median. Stratify error by pickup hour, weekday, duration band, route/zone, and missingness; report holdout feature/target drift.

### [P2] Target quality handling is incomplete and can silently change the evaluation population

**Evidence:** The synthetic generator intentionally injects six `-3.0` durations at `src/platform.py:41-44`. The audit counts only direct `<= 0` values at `src/platform.py:59-62`, while the training population is silently filtered with `trip_duration_minutes > 0` at `src/platform.py:85`. There is no explicit target-missing, finite-value, unit, or upper-plausibility check. `audit_data` uses coercion only for IQR calculation (`src/platform.py:52-56`), but direct comparisons for invalid values can fail on nonnumeric input.

**Impact:** The report’s raw-row audit count and model metric denominator describe different populations, and future real-data records with missing, infinite, malformed, or implausibly long targets are not governed by a documented policy. A change in invalid rows can alter the chronological boundary and make metrics incomparable across runs.

**Concrete fix:** Validate and type-coerce the target once, count missing/non-finite/non-positive/implausible values separately, record raw/retained/excluded counts and exclusion IDs, and make the inclusion policy explicit. Reject malformed input with a structured audit result before model fitting rather than relying on a later comparison or `KeyError`.

### [P2] Feature engineering is tightly coupled to the toy target and under-specifies real taxi behavior

**Evidence:** The feature list is limited to hour, weekday, a hard-coded rush flag, passenger count, distance, and categorical pickup/dropoff zones at `src/platform.py:18-20` and `src/platform.py:65-73`. The generated target uses the same rush/weekend/distance signals at `src/platform.py:31-36`. Hour and weekday are passed as ordinary numeric variables, not cyclic or otherwise structured time features. Missing numeric values are silently median-filled, with no missingness indicator, at `src/platform.py:71-73`; there are no route geometry, calendar/holiday, weather, traffic, or pickup/dropoff-time features.

**Impact:** The synthetic benchmark rewards matching the generator’s formula but says little about congestion, route topology, or regime changes in actual trips. Numeric hour/weekday distances impose arbitrary ordering, and silent imputation can hide a production data-quality signal. The feature set is therefore appropriate for the stated demo but insufficient to support the broader NYC/dispatch framing.

**Concrete fix:** For real data, define a point-in-time feature contract and add validated route/geospatial, calendar, and traffic features available at prediction time. Encode cyclical time or use an appropriate categorical representation, add missingness indicators, and measure performance separately for missing versus complete inputs. Verify that any historical/aggregate feature is computed without future rows.

### [P2] The browser inference experience cannot substantiate the saved-model conclusions

**Evidence:** The Python inference path loads `model.joblib` and requires pickup/dropoff zones at `src/platform.py:106-111`. The dashboard instead computes a hand-written formula in `dashboard/app.js:67-85`, omitting zones and the fitted model. The HTML does disclose this clearly at `dashboard/index.html:123-140`, and the README repeats the CLI requirement at `README.md:27-31`.

**Impact:** The disclosure is good, but the interactive estimate is not a prediction from the evaluated pipeline. Its outputs cannot be used to validate the model metrics or infer route effects. Users may still conflate the visually adjacent local estimate with the scorecard model.

**Concrete fix:** Prefer a local API or a browser-compatible exported model with the exact same feature contract. If the formula remains, make it visually and semantically a separate toy calculator, show that it is not the evaluated model, and include all required model inputs or explain their omission in the output.

### [P2] Dashboard KPI wording overstates what the metrics mean

**Evidence:** `dashboard/app.js:13-19` labels R² as “Model accuracy” and calls the holdout count “Test coverage,” displaying test rows as “of” train rows. The artifact actually has 239 test rows and 955 train rows (`artifacts/metrics.json:2-8`), while the cleaned evaluation population is 1,194 rows, so the holdout fraction is approximately 20%, not 239/955 coverage.

**Impact:** R² is not classification accuracy and is not an operational accuracy percentage. The denominator wording makes the data split harder to interpret and can imply 25% test coverage. These labels weaken otherwise useful caveats about the synthetic, illustrative nature of the result.

**Concrete fix:** Label the KPI “R²” and include the value’s definition; label the row statistic “Holdout rows” and show “239 of 1,194 retained rows (20.0%)” alongside train rows. Add MAE units and, if retained, explain that within-five-minutes is an application threshold rather than generic accuracy.

### [P2] Reproducibility metadata is incomplete and the documented test command is environment-sensitive

**Evidence:** The run is seedable through `run_platform.py:14-16` and deterministic model settings are present at `src/platform.py:76-78`, but the generated report at `artifacts/crispdm_report.md:6-25` does not record the actual seed, row argument, package versions, git revision, or data hash. `README.md:48-50` says the seed, feature list, model parameters, split rule, and thresholds are recorded in the report, which is not true for the checked-in report. Dependencies are only lower-bounded in `requirements.txt:1-6`.

**Impact:** A future environment can produce materially different artifacts, and an artifact cannot be traced to an exact command/environment from its own metadata. In this checkout, the documented `pytest -q` console entrypoint failed collection with `ModuleNotFoundError: No module named 'src'`; `PYTHONPATH=. .venv/bin/python -m pytest -q` passed. This indicates the project is not packaged or test invocation is not robust across environments.

**Concrete fix:** Write a run manifest containing command arguments, source/data hash, row counts before and after filtering, library/Python versions, and git revision; pin or lock dependencies and test supported Python versions. Add package metadata or a pytest configuration so the README command works from the project root without manually setting `PYTHONPATH`.

### [P3] Tests verify happy-path plumbing but not data-science invariants

**Evidence:** `tests/test_platform.py:9-37` has four tests covering deterministic generation, artifact existence, JSON serialization, and one invalid CLI input. There is no assertion for chronological ordering/boundary, train-only preprocessing, complete audit/UI category coverage, baseline or slice metrics, malformed schema/type handling, or stable artifact metadata.

**Impact:** The current suite can pass while the leakage, audit omission, metric-label, and generalization issues above remain undetected.

**Concrete fix:** Add focused tests for split ordering and row counts, train-only imputation, schema/range failures, all audit fields, inference feature parity, and metric calculations against a small frozen fixture. Add a smoke test that regenerates artifacts in a temporary directory and compares the manifest and metrics within defined tolerances.

## Checks performed

- `PYTHONPATH=. MPLCONFIGDIR=/private/tmp/project13-mpl LOKY_MAX_CPU_COUNT=1 .venv/bin/python -m pytest -q`: **4 passed** (387 dependency deprecation warnings from joblib/NumPy).
- Regenerated the pipeline into `/private/tmp/project13-review-artifacts` with `rows=1200, seed=255`: headline metrics reproduced exactly (955/239; MAE 2.794; RMSE 3.622; R² 0.892; within-five 0.845), and the model artifact loaded successfully.
- Ran the saved-model inference CLI successfully; it returned a JSON prediction of 26.37 minutes for the documented example inputs.
- `node --check dashboard/app.js`: passed.
- Seed sensitivity check over seeds `1, 2, 3, 4, 5, 7, 42, 255, 999` produced MAE 2.664–2.995, RMSE 3.347–4.285, R² 0.843–0.901, and within-five rates 0.820–0.879. This is descriptive, not a replacement for proper repeated temporal validation.
- The attempted plain `.venv/bin/pytest -q` invocation failed at collection because the repository is not importable as `src` through that entrypoint; the module invocation above passed. No source files were changed during review; this review file is the only file added for this task.

## Bottom line

The project is credible as a transparent, deterministic educational demo with appropriately prominent synthetic-data caveats. The reported numbers and local artifact flow are reproducible under the prepared environment. Before presenting it as a robust taxi audit/modeling platform, fix the preprocessing leakage, make audit findings and target policy complete and enforceable, establish real-data and multi-window evaluation with baselines and uncertainty, align UI language with metric semantics, and record exact run provenance.
