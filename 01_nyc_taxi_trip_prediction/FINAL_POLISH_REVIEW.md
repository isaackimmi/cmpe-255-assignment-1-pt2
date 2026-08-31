# Final polish review — Project 01

Scope: static source, checked-in artifacts, tests, and validation scripts only. No source code was modified. Paths below are relative to this project root.

## Recommendation

**Conditional approve as an educational, reproducible synthetic-data demonstration. Do not present it as evidence of real NYC taxi performance or as a production prediction service yet.**

The core experiment is now coherent: `trip_duration` is explicit, request-time features are used, timestamps are normalized and sorted before splitting, train-only scaling and target-threshold fitting are used, three expanding chronological folds are reported, and final metrics can be recomputed from `outputs/predictions.csv`. The main remaining validity concern is that the observed test target is used to remove test rows before scoring. The UI is polished and has one real what-if interaction, but most of the analytical surface is still static and does not let a reviewer explore the folds, error segments, or checked-in artifacts.

## Prioritized actions

### [P1] Score the complete eligible test set; make target trimming a sensitivity analysis

Evidence:

- `run_experiment.py:181-190` learns the duration threshold from training targets, then filters both training and test records.
- `run_experiment.py:324-344` uses the filtered test records for the published predictions and metrics.
- `outputs/metrics.json:4-15` shows 6,000 input rows, 1,200 structural-clean test rows implicitly reduced to 1,187 scored rows, with 13 `test_duration_outlier` rows removed.
- `README.md:17-19` documents the policy accurately, but the result is still an inlier/trimmed-test estimate rather than performance over all eligible future trips.

Impact: a production system cannot know `trip_duration` at prediction time and therefore cannot remove a test request because its unseen target exceeds the threshold. The reported MAE/RMSE may be optimistic and the headline sample size is not the full future workload.

Action: retain all structurally valid test rows for the primary evaluation; use the training-derived threshold only for a separately labeled robust/inlier sensitivity metric. Report both denominators and the number of excluded targets. Apply the same distinction inside every temporal fold.

### [P1] Make the temporal contract strict for timezone mixing and tied timestamps

Evidence:

- `run_experiment.py:85-90` converts aware timestamps to UTC-naive values but leaves naive timestamps naive, without declaring the source timezone assumption.
- `run_experiment.py:193-201` sorts correctly, but the invariant is `train[-1].timestamp <= test[0].timestamp`; equal-time records may be split across train and test.
- `run_experiment.py:324-335` repeats the non-strict `>` check after target cleaning.

Impact: a CSV containing a mixture of local-naive and offset-aware timestamps can be ordered inconsistently. Splitting identical pickup times across the boundary also weakens the claimed strictly-forward evaluation.

Action: define one input timezone policy (for example, interpret NYC-naive timestamps as `America/New_York`, then store UTC); reject mixed/ambiguous inputs. Split on a timestamp/date group and require `max(train_time) < min(test_time)` unless tied timestamps are explicitly treated as one group. Record the policy and tie handling in `metrics.json`.

### [P1] Tighten the real-data contract beyond global coordinate ranges

Evidence:

- `run_experiment.py:75-82` checks required columns but does not enforce unique IDs, non-empty strings, or row-level source quality beyond later numeric parsing.
- `run_experiment.py:93-124` enforces global latitude/longitude ranges, passenger count `[1, 10]`, positive duration, and a `<100` mile route cap, but no NYC service-area/domain bounds, valid vendor set, integer passenger semantics, or pickup/drop-off plausibility policy.
- The current metadata records these broad rules at `outputs/metrics.json:146-151`.

Impact: globally valid coordinates can describe trips outside the intended service area, and unusual IDs/vendor values can pass as if they were valid NYC rows. The fallback remains useful as a smoke test, but the real-CSV path needs an explicit domain contract before its metrics are trusted.

Action: document and enforce the intended geographic/service-area policy, allowed vendor values, ID uniqueness, passenger integer rules, timestamp coverage, and duplicate handling. Keep the current drop-reason audit and fail/warn on high or domain-specific drop rates.

### [P2] Strengthen the evaluation summary and validation assertions

Evidence:

- The checked-in run is encouraging: the model reports MAE `81.732`, RMSE `102.373`, and R² `0.6630`, versus global-median MAE `143.727` and RMSE `176.635` (`outputs/metrics.json:20-39`).
- Three expanding folds are present and the model beats the global median on MAE/RMSE in each (`outputs/metrics.json:41-118`; construction in `run_experiment.py:247-277`).
- `validate.py:44-52` recomputes final metrics and checks both MAE/RMSE against the global median, but does not assert the model against the hour-conditioned baseline, summarize fold mean/variation, or verify fold boundary metadata.

Action: publish mean and dispersion across folds, add a recent/seasonal or route-time baseline if the task needs a stronger operational comparator, and assert all primary model-versus-baseline comparisons used in the README. Add segment metrics/calibration by distance, hour, weekday/weekend, and geography before making a deployment claim.

### [P2] Make artifacts self-explanatory and reproducible for inference

Evidence:

- `outputs/metrics.json:120-155` records features, model hyperparameters, cleaning rules, source metadata, and runtime information; this is a good audit foundation.
- `run_experiment.py:359-362` writes standardized absolute linear coefficients, correctly labeled as such. They are descriptive, not causal importance, and correlated coordinate/delta features can make rankings unstable.
- `run_experiment.py:413-415` writes metrics and plots but no serialized model weights or inference entry point. `run_experiment.py:414` generates the duration distribution from all structurally valid records, while scored metrics use post-target-cleaning records.
- `run_experiment.py:293-299` creates a scatter artifact with a reference line but no numeric axes, units, sample-size annotation, or error summary.

Action: export a model artifact or a documented coefficient/intercept bundle with an inference command; make output runs versioned or uniquely named. Label the duration plot as pre-trim structural-clean data or generate a separate scored-population plot. Add axes/units/counts and a residual/error plot. Keep signed coefficients plus a held-out permutation or grouped importance view if interpretation is required.

### [P1/UI] Upgrade the dashboard from a static report with one estimator to an analytical explorer

Evidence:

- `app.js:17-39` dynamically updates metric text and the single MAE comparison bar.
- `index.html:47-76` presents static metric cards and one checked-in `predicted_vs_actual.svg`; the documented `duration_distribution.svg` and `feature_importance.csv` are not surfaced in the UI (`README.md:34`).
- `index.html:111-119` is static CRISP-DM copy; there is no fold selector, baseline selector, error-segment control, table, or filter over `predictions.csv`.
- `app.js:100-101` does provide genuine reactive input behavior for the estimator, and `app.js:63-85` recalculates distance/time/passenger effects. This is meaningful as a teaching aid, but not model-backed exploration.

Action: add a fold/metric selector, an interactive prediction-vs-actual/residual view, filters or summaries by hour/distance/weekend, a feature-importance table, and a cleaning/source audit panel. Show fold sample sizes and uncertainty/variation. This would let a reviewer interrogate the evidence rather than only read the narrative.

### [P2/UI] Keep the illustrative estimator mathematically aligned or label it more prominently as qualitative

Evidence:

- Python fallback duration uses an approximate distance calculation, rush-hour/passenger effects, and Gaussian noise (`run_experiment.py:42-60`), with no weekend term.
- Browser estimation uses haversine distance and adds a weekend adjustment while omitting noise (`app.js:41-76`); it also does not load model weights.
- The limitation is disclosed at `README.md:47` and `index.html:80,106`, which is good practice.

Action: either expose a real inference endpoint/artifact, or name the browser formula as a separate illustrative simulator and share its exact equation/configuration. Do not let the large “ILLUSTRATIVE ESTIMATE” read like the published model result.

### [P2/UI] Add input validation and make fallback status unmistakable

Evidence:

- Numeric/date controls have no `required`, `min`, `max`, or domain validation (`index.html:82-96`).
- `app.js:65-84` converts values directly and does not guard invalid dates, missing coordinates, or non-finite distances before formatting the result.
- `app.js:88-97` falls back to embedded metrics on any fetch failure, while `index.html:25` always displays `run complete`; the footer status is the only explicit preview signal (`index.html:128`).

Action: validate the route/time fields with inline errors and a bounded NYC-domain policy; add an `aria-live` result/status region. Change the global status to “preview/fallback” until `metrics.json` is loaded, and display source hash/run timestamp so stale embedded values cannot look like a completed current run.

## Documentation hygiene

`DS_REVIEW.md` is stale relative to the current implementation. Its claims that CSV rows are unsorted, cleaning is unaudited, and temporal folds are absent (`DS_REVIEW.md:11-47`) conflict with `run_experiment.py:137-163,193-201,247-277` and `validate.py:13-18,44-52`. It also contains obsolete hard-coded UI/model findings (`DS_REVIEW.md:72-100`). Keep this final review as the authoritative current audit, or update/archive the older review before submission so evaluators do not see contradictory conclusions.

## Strengths worth preserving

- Explicit required-column contract and auditable structural drop reasons (`run_experiment.py:29-33,137-163`).
- Training-only feature scaling and training-only duration quantile fitting (`run_experiment.py:181-190,204-223`).
- Chronological ordering, split cutoff metadata, and expanding temporal folds (`run_experiment.py:193-201,247-277,387-396`).
- Recomputable final predictions and metric checks, including MAE, RMSE, and R² (`validate.py:21-52`).
- Clear labeling that the fallback is synthetic and that the browser estimator is illustrative (`README.md:11,47,51`; `index.html:80,106`).

## Final disposition

Ship the current project as a clearly labeled synthetic pipeline demonstration after adding the P1 clarifications/fixes above. For a real-data or production-facing submission, require complete-test scoring, an explicit timezone/tie policy, a tighter service-area contract, serialized inference, and an interactive evidence view before calling the result deployment-ready.

