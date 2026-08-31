# Data-science robustness review — Project 06

Scope: anomaly-generation validity, contamination assumptions, preprocessing, train/test separation, model comparison, thresholding, metric interpretation, reproducibility, and dashboard claims. This is a review only; no source code was modified.

Severity tags:

- **[P1 — High]** materially invalidates the stated unsupervised evaluation or can produce misleading performance conclusions.
- **[P2 — Medium]** weakens scientific validity, reproducibility, or interpretation but is bounded by the teaching/demo scope.
- **[P3 — Low]** limited-risk quality or maintainability issue.

## Executive summary

The implementation is a clear, deterministic teaching example with sensible detector diversity, category-level diagnostics, and a useful warning that the dashboard simulation does not rerun Python. The largest robustness issue is that the experiment uses the full labeled, contaminated data set for fitting, scaling, contamination configuration, and evaluation. Consequently, the reported fixed-budget results are transductive/oracle-budget benchmark results, not an estimate of deployment performance from an unsupervised detector.

The synthetic labels also describe injection mechanisms rather than guaranteed semantic anomalies: some points generated as “global” or “local” anomalies fall inside approximate normal-cluster 95% ellipses. In the checked-in seed-42 artifact, the rank ensemble is not an improvement over the individual detectors, and the dashboard’s threshold explorer displays formula-based illustrative numbers rather than predictions from actual detector scores.

## Findings

### [P1 — High] Label-derived contamination leaks the oracle anomaly prevalence into model fitting and alert selection

**Evidence**

- `src/anomaly_experiment.py:117-122` computes `contamination = labels.mean()` and passes it into both model scoring and evaluation.
- `src/anomaly_experiment.py:58-66` configures Isolation Forest, LOF, and Elliptic Envelope with that contamination value.
- `src/anomaly_experiment.py:85-98` then selects exactly `round(contamination * n)` highest-scoring points.
- `README.md:12` and `index.html:59-60` describe this as the known 100/900 rate or fixed alert budget.

**Why it matters**

Although the label array is not passed directly to `fit`, the true prevalence is derived from labels and used to configure training and the operating point. This is not a genuinely unsupervised deployment setting. It guarantees a 100-point queue for this data set and gives every detector an oracle budget that would normally be unknown.

**Concrete fix**

Separate two explicitly named experiments: (1) an oracle-budget benchmark, where the known synthetic prevalence is allowed but clearly labeled as such, and (2) an unsupervised operating-point experiment, where contamination is estimated from a clean calibration set or selected from an explicit alert-cost policy without using test labels. Report performance over several budgets or thresholds rather than only the label-derived budget.

### [P1 — High] There is no train/test separation; the scaler and every detector are fit and scored on the same contaminated observations

**Evidence**

- `src/anomaly_experiment.py:119-122` creates one `x` matrix, fits scores on it, and evaluates those scores against labels from the same matrix.
- `src/anomaly_experiment.py:54-56` calls `StandardScaler().fit_transform(x)` on all observations, including injected anomalies and observations later treated as evaluation data.
- `src/anomaly_experiment.py:69-77` calls `detector.fit(x_scaled)` and obtains scores from the fitted training data; LOF uses its training `negative_outlier_factor_`.
- `tests/test_anomaly_experiment.py:20-35` checks shapes and metric ranges but does not enforce a holdout or leakage-safe preprocessing path.

**Why it matters**

The reported ROC-AUC, AP, and fixed-budget scores measure how well each model ranks the points it was fit on. The contamination also influences the fitted support/threshold. In addition, full-data scaling and full-data local neighborhoods allow the injected anomalies to affect the representation and neighborhoods used to judge them. This can be useful for a transductive toy benchmark, but it is not evidence of generalization to future observations.

**Concrete fix**

Create a train/calibration/test protocol. Fit preprocessing on training data only, fit each detector on training data only, and score an untouched test set. For LOF, use a novelty-detection configuration for scoring new samples. Keep synthetic anomaly labels out of all fitting and operating-point selection; use them only for final test evaluation.

### [P1 — High] The anomaly generators do not guarantee that generated points are anomalous relative to the declared normal population

**Evidence**

- `src/anomaly_experiment.py:32-36` defines the normal clusters and the three anomaly mechanisms; `src/anomaly_experiment.py:37-46` assigns mechanism labels and shuffles rows.
- The “global” mechanism is uniform over `[-5,-4]` to `[10,9]`, a box that overlaps the normal-cluster support.
- The “local” mechanism is a dense Gaussian at `[2.4, 0.0]` with small variance, so it is a compact group near the tail/fringe of the first normal cluster rather than necessarily a low-density point.
- A diagnostic using the generator’s normal means/covariances and an approximate chi-square 95% ellipse threshold of 6.0 found, at seed 42, **4/35 global** and **12/30 local** generated points inside at least one approximate normal ellipse. The cluster mechanism had 0/35 inside that ellipse, but its nearest normal-ellipse distance was only about 6.804 for the closest point.

**Why it matters**

The labels are mechanism labels, not necessarily ground-truth anomaly labels. Some “anomalies” are plausible normal observations under the stated normal model, so low recall can reflect ambiguous labels rather than detector failure. The benchmark therefore supports failure-mode illustration, but not a strong claim that one method detects real anomalies better.

**Concrete fix**

Define and test an anomaly acceptance rule before labeling points—for example, a minimum likelihood-tail distance from the complete normal mixture, a minimum separation from the normal manifold, or a domain-specific semantic rule. Reject/resample generated points that violate the rule. Also report results separately for mechanism detection and for a validated anomaly-vs-normal task.

### [P2 — Medium] The model comparison is single-seed and lacks hyperparameter or uncertainty analysis; the ensemble “improvement” claim is unsupported by the artifact

**Evidence**

- `src/anomaly_experiment.py:58-66` uses one fixed configuration: 250 Isolation Forest trees, LOF `n_neighbors=25`, and Elliptic Envelope `support_fraction=0.8`.
- `README.md:10` calls the rank ensemble a “meaningful improvement,” but seed-42 `artifacts/metrics.json:2-32` shows it below the individual leaders: rank ensemble ROC-AUC/AP/F1 are **0.7886/0.4613/0.37**, versus Elliptic Envelope **0.8808/0.6883/0.64** and Isolation Forest **0.8585/0.5333/0.48**.
- A seed sweep over 0–9 produced ranges of ROC-AUC/AP/F1 of **0.8415–0.9224 / 0.6364–0.7481 / 0.54–0.62** for Elliptic Envelope and **0.7654–0.8376 / 0.3956–0.5033 / 0.32–0.39** for the rank ensemble.
- `tests/test_anomaly_experiment.py:28-36` tests only the default seed and asserts that this one rank-ensemble AP exceeds prevalence; it does not test robustness across seeds or configurations.

**Why it matters**

The dashboard’s “best overall” conclusion is a one-draw conclusion from a synthetic distribution that was designed around these methods. The ensemble is a valid scale-normalization idea, but the current result does not show improvement, and no uncertainty interval establishes whether the ranking is stable.

**Concrete fix**

Pre-specify a small, fair hyperparameter grid (especially multiple LOF neighborhood sizes), repeat the complete experiment across many seeds, and report mean/median plus dispersion or confidence intervals. Describe the ensemble as a candidate combination unless it consistently improves a preselected metric on held-out data.

### [P2 — Medium] Fixed-budget F1, precision, and recall are presented as if they were threshold metrics, but they collapse to the same quantity at this budget

**Evidence**

- `src/anomaly_experiment.py:88-98` predicts exactly `n_anomalies` points by rank and computes precision, recall, and F1.
- For seed 42, `artifacts/metrics.json:2-32` reports equal precision, recall, and F1 for every method, with `flagged: 100` for every method.
- Since there are 100 true anomalies and 100 predicted positives, precision and recall are both `TP/100`; F1 is therefore identical as well.
- A contamination sweep confirmed that the operating point changes the result materially: at 5% the models flag 45 points, while at 20% they flag 180 points, with the expected precision/recall trade-off.

**Why it matters**

These values are useful as precision@100 / recall@100, but they are not threshold-calibrated F1 results and F1 was not optimized. A reader may incorrectly infer that the detector has an intrinsically balanced precision/recall operating point.

**Concrete fix**

Name the metrics explicitly as precision@k, recall@k, and F1@k when using a fixed queue. Also report PR curves or a threshold sweep on held-out data, and select a threshold using an operational cost or validation objective rather than the test labels.

### [P2 — Medium] The dashboard operating-point explorer generates invented metrics rather than applying a detector threshold to detector scores

**Evidence**

- `app.js:73-92` computes `thresholdFactor`, `budgetFactor`, `projectedRecall`, and `projectedPrecision` from hand-written formulas based on the saved point estimate.
- No score arrays or thresholded predictions are loaded by `app.js`; the only fetch is `artifacts/metrics.json` at `app.js:95-100`.
- `index.html:84-88` labels the result “Projected queue,” “LIVE PREVIEW,” and “Directional estimate,” while `README.md:36` says the behavior is illustrative and does not rerun Python.

**Why it matters**

The disclaimer substantially reduces the risk of a hidden claim, but the displayed recall/precision values are still not empirically derived. The threshold slider is not a decision threshold for any of the detector score distributions, and changing the flag budget cannot reproduce a real ranked queue except at the single saved point.

**Concrete fix**

Either export per-observation scores and compute actual threshold/quantile predictions in the browser, or rename the outputs to clearly hypothetical scenario estimates and remove quantitative “recall”/“precision” language. If using actual thresholds, preserve the score direction and calibration semantics for each detector.

### [P2 — Medium] Several dashboard claims are hard-coded or over-broad for a single artifact

**Evidence**

- `app.js:22-27` labels the ROC-AUC winner “BEST OVERALL” and computes prevalence as `flagged / 900`; `app.js:31-38` sorts the entire scoreboard by ROC-AUC only.
- `index.html:43-44` hard-codes `RUN 042` and “LAST RUN 42 sec ago.”
- `index.html:58-60` presents “BEST OVERALL” and “ANOMALY PREVALENCE” as run facts, while the experiment is one synthetic seed and the prevalence is an oracle setup rather than a deployment estimate.

**Why it matters**

“Best overall” is ambiguous when ROC-AUC, AP, and fixed-budget F1 are all shown, and a static “42 sec ago” value becomes false immediately. Hard-coding 900 also makes the UI stale if the generator’s sample size changes.

**Concrete fix**

Store dataset size, seed, generation timestamp, contamination mode, and the ranking criterion in `metrics.json`. Render “best ROC-AUC on seed 42” (or a multi-seed aggregate) and use the artifact metadata for all counts/timestamps. Avoid presenting synthetic prevalence as an observed production prevalence.

### [P2 — Medium] Reproducibility is not environment-complete and the documented end-to-end command is not portable on the reviewed host

**Evidence**

- `requirements.txt:1-4` uses unpinned lower bounds, so future NumPy, scikit-learn, Matplotlib, and pytest versions can change results or behavior.
- `README.md:18-24` documents `python -m ...`, but the reviewed host exposes `python3` and no `python` command; the default Python 3.14 environment also lacked the declared packages.
- In an isolated temporary environment with the declared requirements installed, `python -m pytest -q` passed **3/3** and `node --check app.js` passed.
- The full experiment command exited with code 134 while Matplotlib was building its font cache, including after retrying with a writable temporary `MPLCONFIGDIR`; consequently, end-to-end regeneration of `metrics.json`/PNG was not verified in this environment.

**Why it matters**

The seed controls the explicit NumPy and estimator RNGs, but it does not pin library behavior or make the artifact pipeline reproducible across environments. The checked-in metrics remain inspectable, but a fresh run could not be independently regenerated here.

**Concrete fix**

Pin a tested Python version and exact dependency versions (or commit a lock file), record versions in the artifact, and run the full experiment in CI. Use `python3`/`python` consistently in the README and configure/test Matplotlib in a supported environment with a writable cache directory.

### [P3 — Low] The test suite does not protect the critical scientific invariants

**Evidence**

- `tests/test_anomaly_experiment.py:10-18` verifies only deterministic generation and counts.
- `tests/test_anomaly_experiment.py:20-26` verifies finite score arrays and method names.
- `tests/test_anomaly_experiment.py:28-36` checks metric ranges, exactly 100 flags, and one seed-42 AP comparison.

**Why it matters**

The tests would still pass if preprocessing leaked across a future split, if category recall disappeared, if artifact metadata became inconsistent, or if the ensemble claim stopped holding outside seed 42. They validate plumbing more than the scientific protocol.

**Concrete fix**

Add tests for: train-only preprocessing and holdout scoring; no label access in fitting/threshold selection; category counts and category-recall output; multiple seeds; explicit fixed-budget semantics; artifact regeneration; and dashboard handling of metadata-driven sample counts.

## Checks run

- `python3 -m pytest -q` in the host environment: could not start because `pytest` was not installed.
- Isolated temporary environment installed from `requirements.txt`: `python -m pytest -q` — **3 passed**.
- `node --check app.js` — **passed**.
- Full `src/anomaly_experiment.py --output-dir <temporary-dir> --seed 42`: **not completed**; exited 134 during Matplotlib font-cache construction under Python 3.14, including with a writable temporary Matplotlib cache. No project source or checked-in artifact was modified.
- Static source inspection and seed/contamination diagnostics were run against the implementation and checked-in `artifacts/metrics.json`.

## Recommended priority order

1. Make the evaluation protocol leakage-safe: separate train/calibration/test data and stop deriving training contamination or operating points from test labels.
2. Validate or redesign the synthetic anomaly generators so the labels correspond to declared anomaly criteria.
3. Replace the single-seed “best overall” and ensemble-improvement claims with repeated-seed, held-out comparisons and uncertainty.
4. Make the dashboard either score-backed or explicitly hypothetical, and move run metadata out of hard-coded UI text.
5. Pin the runtime/dependencies and add an end-to-end CI check for artifacts.
