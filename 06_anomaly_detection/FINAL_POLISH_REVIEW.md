# Final polish review — Project 06: Anomaly Detection

**Review date:** 2026-08-30  
**Scope:** Current source, checked-in metrics/plot artifacts, tests, README, and the checked-in Project 06 UI screenshot. This review is read-only; no source code was modified.

## Recommendation

**Accept as a strong teaching/demo benchmark after a small release-hygiene pass; do not present it as deployment evidence.** The current implementation has corrected the major leakage problems documented in the older `DS_REVIEW.md`: clean training and calibration normals are separated from the labeled holdout, detector fitting does not receive labels, LOF is configured for novelty scoring, anomaly candidates are rejected against a declared tail-distance rule, and the dashboard replays precomputed score-backed operating points.

Before submission, replace or regenerate the stale screenshot and add one explicit disclosure that the 100-alert queue is an oracle-budget benchmark and that the slider is an offline holdout diagnostic, not a threshold-selection tool. For a stronger final polish, expose per-observation scores or a thresholded score plot, record runtime versions, and report repeated-seed uncertainty.

## What is solid in the current version

- `src/anomaly_experiment.py:94-111` creates 600 clean training normals, 200 clean calibration normals, and a 300-row labeled holdout; the test labels are not returned to the fitting functions.
- `src/anomaly_experiment.py:119-153` fits the scaler and detectors on `train_x` only, scores query data separately, uses LOF with `novelty=True`, and builds the ensemble against clean training score references.
- `src/anomaly_experiment.py:50-79` rejects generated anomaly candidates until their nearest declared normal-component squared Mahalanobis distance is at least 8. `tests/test_anomaly_experiment.py:19-36` protects that invariant and the category counts.
- `src/anomaly_experiment.py:156-160` calibrates thresholds from clean calibration scores, while `src/anomaly_experiment.py:189-205` computes final ranking and fixed-queue metrics on the holdout.
- `src/anomaly_experiment.py:208-222` generates threshold/budget operating points from actual test scores; `app.js:95-109` reads those saved points instead of inventing precision/recall with a client-side formula.
- The current artifact is internally informative: `artifacts/metrics.json:2-36` shows the rank ensemble leading ROC-AUC/AP (`0.983`/`0.968`) while LOF has the best F1@100 (`0.89`). The UI correctly labels its summary criterion as “TOP HOLDOUT ROC-AUC” in `index.html:58` rather than claiming a universal best method.

## Prioritized findings and actions

### [P1] Replace the stale checked-in screenshot before submission

**Evidence:** `ui_screenshots/project-06.png` visibly shows the previous dashboard state: “BEST OVERALL,” Elliptic Envelope at about `0.881` ROC-AUC, `11%`, “100 known anomalies / 900 points,” and “LAST RUN 42 SEC AGO.” Those values do not match the current artifact (`artifacts/metrics.json:2-36,249-269`), which reports rank ensemble ROC-AUC `0.982975`, a 300-point holdout, and a 33.3% synthetic holdout rate. The current source has also changed its labels and metadata handling (`index.html:43-61`, `app.js:20-43`).

**Why it matters:** A grader or reviewer can reasonably treat the screenshot as evidence of the delivered dashboard. It currently contradicts the code and metrics, making the artifact set look unreproducible even though the current implementation is substantially better.

**Action:** Regenerate the screenshot from the current `index.html` and `artifacts/metrics.json`, or remove the old screenshot from the submission set. Check that the visible winner, split sizes, prevalence, timestamp, and operating-point labels all come from the same run.

### [P2] Make the 100-alert queue’s oracle-budget status impossible to miss

**Evidence:** `DEFAULT_ALERT_BUDGET = 100` is fixed at `src/anomaly_experiment.py:26-29`; `evaluate` always selects exactly that many holdout rows at `src/anomaly_experiment.py:189-205`. The holdout itself contains 100 anomalies by construction at `src/anomaly_experiment.py:99-110`, and the artifact records both values at `artifacts/metrics.json:249-258`.

**Why it matters:** The methodology is label-safe for fitting and calibration, but `K=100` happens to equal the known number of holdout anomalies. This makes precision@K, recall@K, and F1@K a useful benchmark, not an unsupervised deployment operating point. A reader could overinterpret the attractive queue metrics as a calibrated production alert rate.

**Action:** Keep the fixed queue, but label it consistently as `precision@100 / recall@100 / F1@100 (oracle benchmark)`. Add a compact disclosure near `index.html:60` and `index.html:85-88`: “K is fixed for comparison; it is not inferred from holdout labels for deployment.” Keep threshold curves and several alert budgets as the decision-oriented view.

### [P2] Prevent post-hoc holdout tuning through the interactive replay

**Evidence:** The Python run computes every threshold/budget combination using holdout labels at `src/anomaly_experiment.py:208-222`. The browser then displays holdout precision/recall for the selected combination at `app.js:95-109`; the text says labels are used only in offline evaluation, but the UI does not explicitly say that the displayed curves must not be used to choose a deployment threshold (`index.html:85-88`).

**Why it matters:** The underlying experiment selects thresholds from clean calibration scores, which is correct. However, an analyst can move the sliders until holdout F1 looks best and silently turn the test set into a tuning set. The dashboard is therefore a valid diagnostic replay, but not a safe policy-selection interface.

**Action:** Add “Diagnostic only — do not select a production threshold from this labeled holdout” beside the queue readout. If a selection workflow is desired, export a separate labeled validation split for choosing the operating point and reserve the displayed holdout for one final report.

### [P2] Make “score exploration” more inspectable than a precomputed aggregate replay

**Evidence:** `app.js:70-76` looks up saved threshold and operating-point records, and `app.js:95-109` updates only flags, recall, precision, bar fill, and a textual threshold. The artifact contains aggregate operating points but no per-observation score/ID/category table. The score map is a static PNG at `index.html:79-80` and cannot show which points cross the selected threshold.

**Why it matters:** The current UI genuinely explores score-backed operating points, but it does not let a user inspect detector score distributions, the threshold boundary, or the actual alert queue. “Replay saved detector scores” is accurate in the provenance sense, but the user sees a lookup table rather than the scores themselves.

**Action:** Export a compact per-observation artifact containing an ID, split, category, each detector score, and selected alert state. Render at least one interactive score histogram/ranking plot with a threshold marker and a small table of flagged rows. Link the selected method and slider state to category recall so the failure-mode view updates at the same operating point.

### [P2] Tighten the anomaly-validity claim from component-tail validity to benchmark semantics

**Evidence:** `_normal_tail_distance` at `src/anomaly_experiment.py:41-47` measures distance to the nearest individual Gaussian component, and `_sample_valid_anomalies` enforces only that criterion at `src/anomaly_experiment.py:50-62`. The generators remain mechanism-specific at `src/anomaly_experiment.py:65-79`, including a compact “local” fringe group and a bounded uniform “global” mechanism.

**Why it matters:** The acceptance rule is a defensible improvement and is tested, but it does not establish that every point is semantically anomalous in a real domain, nor does it evaluate the full normal-mixture likelihood. “Global,” “local,” and “cluster” are generator mechanisms, not independently observed ground truth.

**Action:** Preserve the current rule, but use “accepted synthetic tail cases” or “injected mechanisms” in the dashboard copy. For a stronger benchmark, also record mixture log-density/separation diagnostics and report mechanism recall separately from anomaly-vs-normal performance. Keep the existing toy-benchmark caveat in `README.md:46-48`.

### [P2] Report stability and environment provenance before making method claims

**Evidence:** The checked-in artifact is one seed (`artifacts/metrics.json:249-269`), while `requirements.txt:1-4` has only lower bounds. The test suite covers reproducibility for a few generated seeds (`tests/test_anomaly_experiment.py:93-98`) but does not run a repeated-seed comparison, confidence interval, or serialized-artifact regeneration check.

**Why it matters:** The current seed-42 ranking is useful for instruction, but the relative ordering—especially the ensemble versus LOF—should not be treated as stable without repeated draws. Lower-bound dependencies can also change estimator behavior or numeric results.

**Action:** Run the full protocol across a predeclared seed list, report mean/median and dispersion for ROC-AUC, AP, F1@K, and category recall, and add the selected ranking metric to metadata. Pin a tested Python/dependency environment or commit a lock file, record versions in the artifact, and add a CI check that regenerates and schema-validates `metrics.json` and the PNG.

### [P3] Remove remaining hard-coded run state and improve navigation semantics

**Evidence:** The seed stamp is hard-coded as `42` in `index.html:54`, even though `app.js:36-42` dynamically renders the seed elsewhere. The “Methodology” navigation link targets `#methodology` at `index.html:25`, but that ID belongs to the operating-point explorer at `index.html:84`; the actual method-note strip at `index.html:92` has no ID.

**Why it matters:** A non-default seed can produce a dashboard with two different displayed seeds, and the navigation label does not land on the method note it promises.

**Action:** Give the stamp an ID and populate it from artifact metadata, and either rename the nav item to “Operating point” or move `id="methodology"` to the method-note strip and assign a separate ID to the explorer.

### [P3] Strengthen the static plot’s analytical affordances

**Evidence:** `src/anomaly_experiment.py:273-285` writes one static four-panel PNG. It scales marker sizes per method via `_normalise`, colors only holdout anomalies by raw score, and provides no score colorbar, threshold line, category encoding, or link to the selected UI operating point. The dashboard presents it as a saved image at `index.html:79-80`.

**Why it matters:** The image communicates broad spatial separation well, but comparisons of color intensity across panels are not calibrated visually, and users cannot connect the plot to the selected threshold or category-recall bars.

**Action:** Add a colorbar or a clearly stated common normalization, annotate the calibrated threshold/alert count, and use category markers or a companion legend. If keeping the PNG, describe it as a static overview and make the interactive score view the authoritative operating-point visualization.

## Verification performed

- Parsed `artifacts/metrics.json` and checked the current metadata, method metrics, category recall, threshold metrics, and operating-point structure.
- Static source review covered `src/anomaly_experiment.py`, `app.js`, `index.html`, `README.md`, `requirements.txt`, and both test files.
- `node --check app.js` passed.
- `python3 -m pytest -q` could not run in the available host environment because `pytest` is not installed; therefore this review does not claim a passing test run.
- No source code, checked-in artifact, or test file was modified.

## Final priority order

1. Replace the stale `ui_screenshots/project-06.png` or remove it from the deliverable.
2. Add the oracle-budget and holdout-diagnostic disclosures next to the queue controls.
3. Clarify that the current winner is metric-specific and single-seed; add repeated-seed uncertainty for any stronger claim.
4. Export/render per-observation scores so the dashboard explores actual score distributions and alert membership, not only precomputed aggregates.
5. Clean up the hard-coded seed stamp, navigation target, runtime pinning, and static plot annotations.
