# Final polish review — Project 03 customer segmentation

> Follow-up status: the P0 dashboard and claim-framing findings from this review have been implemented. The current artifact contract and remaining limitations are summarized in [`DS_REVIEW.md`](DS_REVIEW.md); this document is retained as the pre-follow-up audit trail.

## Scope and recommendation

This is a review-only audit of the project state before the follow-up polish pass. It covers the Python experiment, committed artifacts, tests, README, and dashboard source by static inspection. No implementation code was changed during that audit.

**Recommendation: conditionally accept as a strong teaching/demo submission; do not present it as validated customer segmentation.** The current run is reproducible and materially stronger than a one-shot K-Means demo: it compares two preprocessing variants, evaluates predeclared `k=2…7` candidates over repeated 80/20 splits, reports uncertainty and ARI partition stability, provides a fitted scoring path, and validates artifact hashes. The main remaining gaps are that the synthetic generator encodes the expected three-cluster answer, the validation signal is still internal to one synthetic population, and the dashboard offers profile/filter interactions rather than genuine point-level segmentation exploration.

The committed selected run is `standard` preprocessing with `k=3` on 120 generated customers. Its mean held-out silhouette is `0.69097 ± 0.02897`, stability ARI mean/min are both `1.0`, and the full-sample silhouette is `0.69305` (`artifacts/summary.json:2-27`). These are coherent exploratory diagnostics, not evidence of future customer behavior, campaign lift, or segment validity.

## Prioritized findings

### P0 — Keep the claims explicitly exploratory and separate prototype recovery from customer discovery

**Evidence:** `make_dataset()` creates three Gaussian chunks with fixed centers, scales, exactly 40 rows per chunk, clipping, and rounding (`src/experiment.py:37-51`). The run records that generator directly as `three Gaussian prototype chunks` (`src/experiment.py:363-366`). The README correctly warns that the 120 customers are intentionally interpretable prototypes and “not a claim about real customer behavior” (`README.md:17`), and the summary selection note repeats that the result is not evidence of future performance (`artifacts/summary.json:36-48`).

**Why it matters:** A high silhouette and perfect ARI are expected when the experiment authors the three separated groups that K-Means is asked to recover. The output demonstrates pipeline mechanics and prototype recovery, but it does not test realistic sampling, imbalance, overlap, missingness, outliers, non-spherical structure, temporal drift, or whether the groups predict a business outcome. The equal 40-row cluster sizes in `artifacts/customer_segments.csv:1-121` reinforce that the final result mirrors the generator design.

**Action:** Keep the current project framed as a synthetic teaching lab. If the submission needs a business-facing conclusion, add a versioned observed dataset and an outcome-based validation plan. If it must remain offline, add a parameterized stress suite covering imbalanced, overlapping, non-spherical, contaminated, and missing-data cases, and report which preprocessing/model-selection conclusions survive. Avoid language such as “customer intelligence” or campaign guidance unless it is visibly qualified as a hypothesis.

### P0 — Upgrade the dashboard from interactive cards to interactive segmentation exploration

**Evidence:** The UI exposes a feature selector and segment filter (`index.html:63-77`), and `app.js` uses those controls only to re-render aggregate profile cards (`app.js:68-90`, `app.js:169-174`). The evaluation visualization is a single exported PNG (`index.html:97-100`), and the score table is rendered from the artifact without controls to choose candidate `k` or preprocessing (`app.js:93-95`, `app.js:173`). The CRISP-DM navigator changes explanatory copy only (`app.js:134-142`).

**Why it matters:** This is a polished static readout with lightweight cross-filtering, not an analyst-facing exploration surface. A user cannot inspect individual customers, click a point to see its raw features and cluster, compare cluster boundaries under another `k`, inspect an alternate preprocessing assignment, or examine overlap/uncertainty/outliers. The UI therefore cannot substantiate the README’s broader “explore” framing beyond profile summaries (`README.md:19-31`).

**Action:** Add a browser-native interactive scatter plot (or a small dependency-free SVG/canvas view) backed by the assignment CSV, with selectable x/y features, hover/click customer details, cluster toggles, and a visible “PCA projection only” label. Add a candidate `k`/preprocessing selector that switches among precomputed assignment artifacts, or clearly label the current view as the selected run only. Show cluster sizes, feature distributions, and low-confidence/outlier indicators where available. Preserve the current aggregate cards as a summary, not the only exploration mode.

### P1 — Make k selection and stability more defensible for a future observed-data path

**Evidence:** `evaluate_validation()` fits the scaler and K-Means on each training split, scores held-out rows, and computes ARI between predictions from repeated fitted models on all rows (`src/experiment.py:135-190`). The run selects the single row with the highest mean held-out silhouette, then uses ARI, minimum ARI, and lower `k` only as sort tie-breakers (`src/experiment.py:309-320`; selection metadata at `artifacts/summary.json:36-48`). The current validation rows are repeated random splits from the same 120-row synthetic population (`src/experiment.py:150-167`).

**Why it matters:** This is a reasonable exploratory protocol, and it avoids fitting the scaler on the held-out rows. However, repeated splits overlap heavily and do not represent a future time period or an independent customer population. ARI here is partition agreement across fitted models, not a per-customer probability of stable assignment under new data. The perfect `1.0` ARI for `k=2` and `k=3` in `artifacts/validation_scores.csv:2-3` is best interpreted as evidence of clean synthetic separation.

**Action:** For observed data, define a development/temporal holdout before model selection and report its assignment/segment-profile stability separately. Add bootstrap or subsample membership rates per customer, cluster-size ranges, and uncertainty near centroids. Predeclare an acceptance rule that combines geometry, stability, minimum segment size, and a business outcome; do not let the maximum internal silhouette alone choose the production segmentation. Compare K-Means with at least one non-spherical/robust alternative when the data shape warrants it.

### P1 — Add an explicit feature/data-quality audit instead of relying on synthetic clipping

**Evidence:** `validate_dataset()` checks required columns, numeric types, missing values, and finite values, while duplicates are only counted (`src/experiment.py:54-82`). The synthetic generator clips values to bounds before rounding (`src/experiment.py:46-51`). Preprocessing is either raw values or `log1p` on only income and AOV followed by `StandardScaler` (`src/experiment.py:85-107`). There is no domain-range, observation-window, duplicate policy, correlation/redundancy, outlier, or feature-weight audit.

**Why it matters:** Standardization puts the four features on comparable variance scales, but it does not establish that equal weighting is meaningful. Frequency, spend score, and AOV may encode overlapping behavior, and clipping a toy generator does not establish controls for real transactions. A future input with duplicates, impossible business values, or a changed aggregation window could produce a technically valid but substantively misleading partition.

**Action:** Define the customer grain and aggregation window; reject or explicitly handle duplicates; add domain checks and a data-quality report; measure skew/outliers rather than assuming a log transform; inspect correlation/redundancy; and sensitivity-test feature weights/scalers. Keep all learned transforms in one fitted pipeline and apply the same pipeline to new customers. Make the transform choice “standard vs log1p variant” rather than an implied improvement: the current selected standard run is better at `k=3` on held-out silhouette (`0.69097` vs `0.66461`) and full-sample silhouette (`0.69305` vs `0.66956`) (`artifacts/validation_scores.csv:2-9`, `artifacts/baseline_scores.csv:1-7`, `artifacts/log1p_scores.csv:1-7`).

### P1 — Refresh stale review documentation before delivery

**Evidence:** The current code selects from `validation_scores` (`src/experiment.py:309-320`), validates artifact schemas/metric agreement/hashes in Python (`src/experiment.py:228-294`), and includes a fitted scoring path (`src/experiment.py:193-210`). The current tests assert artifact existence, shape, cluster count, and `validate_artifacts()` success (`tests/test_experiment.py:41-49`). In contrast, `DS_REVIEW.md` still claims full-sample k selection and in-sample-only selection (`DS_REVIEW.md:11-17`), calls the log1p artifact `improved_scores.csv` (`DS_REVIEW.md:27-33`), says the dashboard does not validate metadata/hashes (`DS_REVIEW.md:51-57`), and says no scoring implementation exists (`DS_REVIEW.md:59-65`).

**Why it matters:** Those statements describe an earlier project state and would make a grader or collaborator distrust otherwise solid work. They also obscure the real remaining issues: synthetic-data limits, limited UI exploration, and the scope of ARI/held-out validation.

**Action:** Replace or archive the stale review and point readers to this final audit. Keep one authoritative statement of the current validation protocol, artifact list, and known limitations.

### P2 — Strengthen artifact and UI validation for maintainability

**Evidence:** Python artifact validation is a good baseline: it checks required files, schemas, row counts, contiguous labels, metric agreement, manifest metadata, and SHA-256 hashes (`src/experiment.py:228-294`). The manifest hashes the six runtime artifacts (`src/experiment.py:376-386`; `artifacts/manifest.json:12-18`). However, browser-side validation checks only row counts for the score files and selected-row consistency, and loops over whatever hashes are present in the manifest (`app.js:106-131`); it does not enforce score schemas/finite values or the complete expected hash set. The tests do not directly test malformed/stale artifact fixtures or JavaScript rendering behavior (`tests/test_experiment.py:41-49`).

**Action:** Share a single manifest/schema contract between Python and JavaScript; enforce the exact expected artifact/hash names in the browser; validate numeric finiteness and preprocessing/k coverage client-side; add a small fixture test for missing, stale, malformed, and mismatched artifacts; and add a smoke test for filter/feature-selection rendering. Consider exporting the fitted scaler/model or a tested command that scores a new CSV, since the current scoring functions are available in source but no model artifact is emitted (`src/experiment.py:193-210`, `src/experiment.py:371`).

### P2 — Improve provenance and interpretability for repeatable comparison

**Evidence:** The summary records seed, feature list, generator parameters, Python/package versions, and a source hash (`artifacts/summary.json:2-3`, `29-38`, `63-77`); requirements are pinned (`requirements.txt:1-5`). The exported PNG is a useful two-panel diagnostic but only shows a fixed PCA projection and the selected final partition (`src/experiment.py:327-340`).

**Action:** Record the exact run command/configuration, source revision when available, feature summary statistics, PCA explained-variance ratios, cluster centroids/profile intervals, and the selected model’s scoring parameters. Label PCA as visualization-only in the artifact metadata as well as in the UI. These additions will make later runs easier to compare without turning descriptive metrics into stronger claims than they support.

## Strengths to preserve

- The feature schema and finite-value checks fail early for missing/non-numeric/non-finite inputs (`src/experiment.py:54-82`).
- The validation loop fits preprocessing on training rows and uses `predict()` for held-out rows (`src/experiment.py:154-167`), which is a sound separation for this exploratory setup.
- K-Means uses a fixed seed and multiple initializations (`src/experiment.py:110-113`), and ARI is appropriate for comparing partitions with arbitrary label permutations (`src/experiment.py:173-187`).
- The selected run is cross-checked against assignments and validation artifacts, and the manifest makes accidental artifact drift detectable (`src/experiment.py:261-291`).
- The README and UI repeatedly disclose the synthetic-data and responsible-use limitations (`README.md:42-44`, `index.html:24`, `37`, `100`, `app.js:9-14`).

## Verification notes

- `./.venv/bin/python -m pytest -q`: **5 passed**; warnings only from the local Matplotlib/joblib environment.
- `./.venv/bin/python -m py_compile src/experiment.py tests/test_experiment.py`: passed.
- `node --check app.js`: passed.
- Static artifact consistency is represented by `validate_artifacts()` and the committed `manifest.json`; the selected summary values agree with the committed CSVs.
