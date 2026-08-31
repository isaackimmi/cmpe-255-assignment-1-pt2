# Project 13 final polish review

## Recommendation

**Conditional approve for an educational, deterministic demo; do not present it as a validated NYC taxi model or production audit platform.** The current pipeline is materially stronger than the older `DS_REVIEW.md` describes: preprocessing is leakage-safe, target-quality handling is typed and explicit, audit counts reconcile, and the checked-in run is reproducible. The main remaining work is to make the evaluation scientifically meaningful on real data, enforce the feature/data-quality contract consistently, and turn the dashboard from an artifact viewer into a genuinely explorable audit/model workspace.

The synthetic framing is unusually clear and should be preserved. If the assignment only requires a CPU-safe reproducible prototype, this is a credible submission with the caveats below. If it requires evidence of NYC generalization, model comparison, explainability, or MLOps readiness, it is not ready without the P1 work.

## What is solid

- The generator is explicitly synthetic: `src/platform.py:84-112` creates deterministic in-memory records, and the target is deliberately generated from distance, rush/weekend effects, and noise at `src/platform.py:96-97`. `README.md:15` and `README.md:45-51` clearly state that the metrics are smoke-test metrics, not NYC generalization evidence.
- The current split/preprocessing order is sound for the synthetic run. Target filtering and chronological sorting occur before the split at `src/platform.py:436-445`; the imputer and categorical encoder are fitted within the model pipeline at `src/platform.py:368-393`, and fitting occurs on `train` only at `src/platform.py:446-447`.
- Target policy is now explicit and typed. `_numeric`/`_coerced` and the policy checks at `src/platform.py:233-271` distinguish missing, nonnumeric, non-finite, non-positive, and over-maximum targets; the run excludes the same six target rows recorded in the manifest.
- The checked-in artifacts are internally consistent: 1,200 raw rows, 1,194 retained rows, and 955/239 train/holdout rows; 187 finding records equal the sum of category counts; the manifest data and source hashes match the current generator and `src/platform.py`.
- The dashboard does load live JSON/Markdown artifacts rather than hard-coding the scorecard and audit counts (`dashboard/app.js:80-93`). It also labels the browser calculator as separate from the evaluated model (`dashboard/index.html:127-140`), which is an important honesty improvement.

## Prioritized improvements

### P1 — Keep the headline conclusion explicitly synthetic, or add a real-data evaluation

**Evidence:** All rows come from the deterministic generator (`src/platform.py:84-112`), and the target uses the same main signals that appear in `FEATURES` (`src/platform.py:24-32`, `src/platform.py:96-97`). The scorecard reports `synthetic_smoke_test` and the source is described as an in-memory NYC-like generator (`src/platform.py:449-463`; `artifacts/metrics.json:2-14`).

**Risk:** The 2.790-minute MAE, 3.624-minute RMSE, 0.892 R², and 84.1% within-five-minute rate demonstrate recovery of a controlled toy mechanism, not traffic variability, route coverage, or NYC operational accuracy. The disclosure prevents a hidden substitution, but surrounding language such as “model health” (`dashboard/index.html:52-55`) and “dispatch analysis” (`dashboard/index.html:96-100`) can still encourage over-interpretation.

**Action:** Retain the synthetic label in every scorecard/report view, rename “model health” to “synthetic smoke-test scorecard,” and change dispatch wording to planning/audit demonstration. For a substantive NYC claim, add a pinned/licensed TLC input mode with schema/unit/provenance checks and run the headline results on a held-out real calendar period. Keep synthetic data as a fast fixture, not as the evidence set.

### P1 — Establish evaluation strength before using the metrics to compare models or support decisions

**Evidence:** Evaluation is one chronological 80/20 block (`src/platform.py:440-464`) with one histogram booster (`src/platform.py:380-391`). There are no baseline metrics, rolling-origin windows, uncertainty intervals, or error slices; the report itself lists these as future work (`artifacts/crispdm_report.md:536-552`).

**Risk:** A single 239-row holdout cannot establish stability across weeks, seasons, holidays, traffic regimes, or sparse routes. R² and within-five-minute rate have no operational reference point or uncertainty estimate.

**Action:** Add at least a global-mean and distance/route baseline, then use multiple rolling future windows with a documented gap policy. Report mean and dispersion/confidence intervals and slice MAE/RMSE/within-five by hour, weekday, duration band, route/zone, and missingness. Keep the current split as a smoke test, but do not call it model health until these comparisons exist.

### P1 — Make feature-quality actions and the temporal boundary enforceable and reproducible

**Evidence:** `audit_data` records invalid distances/passengers as retained with actions such as `coerce_to_missing_and_impute` or `review_or_exclude` (`src/platform.py:274-304`), while `_features` silently converts invalid numeric values to missing and the pipeline continues (`src/platform.py:351-365`, `src/platform.py:441-447`). Duplicate IDs are reported but retained (`src/platform.py:220-231`). Timestamp validity is checked, but the raw timestamp column is sorted before `_features` canonicalizes it (`src/platform.py:433-441`, `src/platform.py:351-355`).

**Risk:** The audit can say “review or exclude” while modeling has already chosen imputation. Duplicate records can overweight trips. With real string/mixed-format timestamps, sorting before canonicalization can produce a different temporal boundary than intended. These are manageable in the fixture but unsafe as an ingestion contract.

**Action:** Define one explicit feature policy per field: reject, deduplicate, impute, or retain-with-warning. Apply the same policy in audit, modeling, inference, and the manifest. Canonicalize validated timestamps before sorting; record the cutoff timestamp and train/holdout time ranges. Make duplicate handling and invalid-feature row IDs/counts visible in the retained/excluded population summary.

### P2 — Make audit exploration genuinely row-level and severity-aware

**Evidence:** The dashboard now renders every category in `audit.finding_counts` (`dashboard/app.js:28-34`), so the earlier “missing categories” concern is resolved. However, it only displays aggregate counts; it does not render the underlying `audit.findings` records containing row IDs, actions, and statuses. It also maps every nonzero category to the same generic “Review” signal via `signalFor` (`dashboard/app.js:23-25`). The HTML labels the area “Complete data audit” (`dashboard/index.html:112`) and the summary says “complete row-level audit” (`dashboard/app.js:34`) without offering row-level navigation.

**Risk:** A user cannot inspect which trips triggered a critical target exclusion versus an informational IQR observation, or see what action was taken. The 187 findings are technically present in JSON but not interactively usable in the UI.

**Action:** Add expandable/filterable finding details by severity, category, status, field, and trip ID, with a direct link/download to the raw audit JSON. Distinguish blocking/critical, warning, and informational signals. Either expose all row-level findings or change “complete row-level audit” to “complete category summary.”

### P2 — Align browser inference with the evaluated model, or separate it more forcefully

**Evidence:** The Python path loads `model.joblib` and accepts pickup/dropoff zones (`src/platform.py:558-575`). The browser path computes an independent hand-written formula from hour, weekday, distance, and passengers (`dashboard/app.js:59-77`) and omits zones; the HTML does disclose this (`dashboard/index.html:127-140`).

**Risk:** The disclosure is good, but the interactive control is visually adjacent to the scorecard and cannot test the saved model or expose learned zone effects. A user can still compare two numbers that come from different systems.

**Action:** Prefer a small local inference endpoint or a browser-compatible export using the exact serialized pipeline and all feature inputs. If the toy calculator must remain, title it “toy directional calculator,” place it under a separate exploratory section, show its formula/input limitations in the output, and provide a clearly separate command/result area for saved-model inference.

### P2 — Replace static evidence display with artifact-backed exploration

**Evidence:** EDA and prediction evidence are fixed PNGs (`dashboard/index.html:73-83`), the CRISP-DM timeline is hard-coded copy (`dashboard/index.html:87-100`), and the app fetches only metrics, audit JSON, and the Markdown report (`dashboard/app.js:80-89`). `run_manifest.json` is not loaded into the UI even though it contains run identity, feature contract, versions, and hashes (`src/platform.py:486-521`).

**Risk:** The UI is partially dynamic but mostly a polished report: users cannot filter EDA by time/route/missingness, inspect prediction errors, explore audit findings, or verify that the displayed images and numbers belong to the same run. The static timeline also says “monitored signal” although no monitoring artifact is displayed.

**Action:** Add a manifest/run-identity panel showing git revision, seed, data/source hashes, runtime, population counts, and artifact freshness. Add at least interactive metric/slice controls and a prediction-error view; if browser charting is intentionally out of scope, provide labeled raw-artifact links and describe the current plots as static snapshots. Change monitoring language to “monitoring plan” until monitoring data exists.

### P2 — Tighten the inference input contract

**Evidence:** `infer_duration` rejects invalid hour, weekday, non-finite/non-positive distance, and passengers below one, but does not enforce the configured passenger maximum, integer passenger semantics, distance maximum, or zone value/type contract (`src/platform.py:558-571`). The training feature rules do enforce distance and passenger ranges (`src/platform.py:357-364`).

**Risk:** Inference can accept values outside the training policy and return extrapolated predictions, creating train/serve contract drift.

**Action:** Reuse the same feature validation/policy for CLI/API inference, reject or explicitly flag out-of-contract inputs, and add parity tests for boundary and invalid cases. Include the model/manifest identity in inference output so a prediction can be traced to the artifact used.

### P2 — Supersede stale review/documentation claims

**Evidence:** `DS_REVIEW.md:7`, `DS_REVIEW.md:21-27`, and `DS_REVIEW.md:29-35` still claim holdout imputation leakage and incomplete UI audit categories. Those claims conflict with the current pipeline (`src/platform.py:368-378`, `src/platform.py:441-447`) and current dashboard category rendering (`dashboard/app.js:28-34`). The old review also reports four tests and older metric values (`DS_REVIEW.md:85-100`), while the current suite has seven tests and the checked-in metrics are `artifacts/metrics.json:4-13`.

**Risk:** A grader or maintainer reading the project root can receive contradictory conclusions and mistake fixed findings for current defects.

**Action:** Mark the old review as superseded or update it to the current implementation. Keep this final review as the authoritative remaining-risk assessment.

### P3 — Expand regression coverage around the remaining invariants

**Evidence:** The current tests cover deterministic generation, artifact creation, inference serialization, target audit categories, train-only imputation statistics, and missing-schema blocking (`tests/test_platform.py:20-117`). They do not test timestamp canonicalization/order, duplicate policy, feature-policy/action parity, inference upper bounds, manifest artifact integrity, or dashboard rendering/label semantics.

**Action:** Add focused tests for chronological cutoff/time ranges, invalid feature policy, duplicate handling, inference boundary rejection, manifest-to-artifact hashes, and metric/row-count reconciliation. Add a lightweight JavaScript/browser smoke test that verifies artifact load, complete category rendering, and the toy-calculator labeling.

## Verification performed

- `./.venv/bin/pytest -q`: **7 passed**; the run emitted dependency deprecation warnings from the prepared Python/NumPy/joblib environment.
- `node --check dashboard/app.js`: **passed**.
- Manifest data hash and source hash were recomputed and matched `artifacts/run_manifest.json`.
- Audit reconciliation: **187** finding records equals the sum of category counts; statuses are **181 retained / 6 excluded** across **5 nonzero categories**.
- Population reconciliation: **1,194 retained = 955 train + 239 holdout**; the report and metrics agree on the checked-in scorecard.
- No source code, generated artifacts, or existing documentation were modified by this audit; this file is the review deliverable.

## Final decision

Ship as a transparent synthetic demonstration if the scope is educational and the synthetic disclaimer remains prominent. Before calling it a robust NYC taxi audit/modeling platform, complete the real-data evaluation and multi-window baselines, enforce one auditable feature/target policy end to end, align inference with the saved model, and add row-level/artifact-backed UI exploration. The current implementation is honest and reproducible enough for a demo, but its metrics should remain smoke-test evidence only.
