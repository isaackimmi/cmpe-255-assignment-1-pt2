# Data-science robustness review — Project 03

## Scope and overall assessment

Review-only assessment of preprocessing, clustering assumptions, k selection, leakage, stability, scaling, metrics, interpretation, reproducibility, and dashboard claims. No source code was changed. The implementation is a clear, reproducible teaching demo, but its quantitative results should not be treated as evidence that real customers form these segments or that the recommended actions will work.

No target/label leakage is present in the current toy generator: the clustering code uses only the four feature columns (`src/experiment.py:18`, `36-42`). However, the evaluation design has substantial in-sample selection optimism, and the absence of real or temporal data prevents a meaningful generalization claim.

## Findings

### [HIGH] k selection and reported metrics are optimized and measured on the same rows

**Evidence:** `src/experiment.py:45-52` fits K-Means and computes all three metrics on the same `data` for every candidate k. `src/experiment.py:58-65` selects the maximum silhouette from the full 120-row dataset and fits the final model on those same rows. `artifacts/summary.json:5-7` reports those selected in-sample metrics.

**Risk:** The reported silhouette/CH/DB values are descriptive training-set values, not estimates of performance on future customers. Selecting k from the same scores compounds optimism; the hard-coded range `2..7` is also not justified by a business or statistical constraint. This is the main leakage/generalization concern, even though there is no target leakage.

**Concrete fix:** Predeclare candidate k values and evaluate them with repeated subsampling/bootstrap stability, or fit preprocessing and K-Means on a development period and assign a later holdout with `transform`/`predict`. Report the distribution of metrics and cluster membership stability rather than one selected score. Add business outcomes or future behavior for external validation.

### [HIGH] The data-generating process hard-codes the expected answer

**Evidence:** `src/experiment.py:21-33` creates exactly three Gaussian prototype chunks, exactly 40 rows per chunk, stacks them in order, clips them to clean bounds, and rounds them. `tests/test_experiment.py:12-15` asserts that k=3 and silhouette > 0.45 are the expected result. `README.md:3`, `17`, and `44` acknowledges that this is synthetic and unusually clean; `PROMPT.md:5` identifies the original request as a popular Kaggle-data clustering project.

**Risk:** The strong separation and equal cluster sizes primarily demonstrate recovery of the authored prototypes. They do not test sampling bias, missingness, duplicates, temporal drift, transaction aggregation, imbalance, contamination, or ambiguous customers. Persona and campaign conclusions therefore have no empirical customer-behavior support.

**Concrete fix:** Use a versioned, documented real dataset when making behavioral claims, or label the project consistently as a toy demonstration. If offline execution is required, add stress scenarios with imbalanced/overlapping/non-spherical clusters, outliers, missing values, and varying prototype parameters, and report which conclusions survive those scenarios.

### [MEDIUM] The log-transform variant is called “improved” despite worse primary results

**Evidence:** `src/experiment.py:36-42` applies `log1p` to income and AOV based on a comment about right skew. The raw generated data has only mild skew in the audit (`annual_income_k=0.047`, `avg_order_value=0.207`). At k=3, `artifacts/baseline_scores.csv:4` has silhouette 0.6931, CH 460.43, DB 0.4656, while `artifacts/improved_scores.csv:4` has silhouette 0.6696, CH 452.34, DB 0.4672. The README and UI label this as an improvement (`README.md:7`; `index.html:93-95`).

**Risk:** The wording implies an improvement that is not supported by the displayed internal metrics. More importantly, applying a transformation because a feature is assumed to be skewed is not a substitute for measuring skew, domain scale, outlier sensitivity, or business usefulness.

**Concrete fix:** Rename this to a preprocessing variant unless a predeclared criterion supports “improved.” Add feature-distribution diagnostics and a repeated stability/business comparison. Keep transformations in a fitted pipeline and document why the chosen distance geometry is appropriate.

### [MEDIUM] Fixed seed and `n_init=25` provide determinism, not clustering stability

**Evidence:** `src/experiment.py:17`, `48`, and `65` use one global seed and 25 K-Means initializations. The tests check repeated identical generation and exact k selection (`tests/test_experiment.py:5-15`), but do not perturb rows, seeds, time windows, or features. `README.md:44` lists stability as future work rather than reporting it.

**Risk:** A repeatable answer for one synthetic sample does not show that customer memberships or segment profiles are robust to resampling, new periods, outliers, or initialization. The audit found identical assignments for several seeds on this unusually separated sample, but that is not a substitute for a reported stability protocol.

**Concrete fix:** Run repeated seeds plus bootstrap/subsample and temporal evaluations. Compare partitions using ARI/AMI or variation of information after handling arbitrary cluster-label permutations; report per-customer membership rates and cluster-size ranges.

### [MEDIUM] Data-quality and feature-design controls are not implemented for a real input path

**Evidence:** The only preparation is synthetic clipping and rounding (`src/experiment.py:29-33`) followed by `StandardScaler` (`src/experiment.py:36-42`). There is no schema, missing-value, duplicate, outlier, aggregation-window, or feature-correlation validation. The tests only assert finiteness and shape (`tests/test_experiment.py:5-10`).

**Risk:** If the generator is replaced with transaction/customer data, missing or malformed values can flow into scaling/metrics, and arbitrary equal weighting after standardization may over- or under-weight correlated measures such as frequency, spend score, and AOV. Clipping synthetic values does not establish production data quality.

**Concrete fix:** Add an explicit data contract and validation report; define the customer observation window and aggregation rules; handle missingness and outliers deliberately; inspect correlation/redundancy; and justify or sensitivity-test feature weights and alternative scalers. Fit all learned preprocessing only on the development data.

### [MEDIUM] Dashboard personas and “run verified” status overstate what is validated

**Evidence:** `app.js:30-35` assigns “Power shoppers,” “Premium occasionals,” and “Value starters” from only the frequency and AOV leaders, then `app.js:79-84` attaches campaign guidance. `index.html:61` hard-codes “Three profiles.” `app.js:103-120` treats successful HTTP responses as verification and sets `Artifacts loaded · run verified`; it does not validate row counts, schema, selected k, metric consistency, or artifact freshness.

**Risk:** The names and actions can be read as validated behavioral personas even though they are heuristic labels over a toy sample. A stale or mismatched artifact set can also be presented as verified. The hard-coded “three” framing can become inconsistent if the experiment output changes.

**Concrete fix:** Use “heuristic profile label” language and show uncertainty/overlap, outlier handling, and the fact that guidance is a hypothesis. Change the status to “artifact files loaded” unless a manifest check passes. Generate and validate a manifest containing code/data parameters, row count, feature schema, selected k, metric values, and hashes; render the actual number of clusters dynamically. Provide a fitted pipeline/scoring path and an explicit policy for new or low-confidence customers before deployment.

### [LOW] Reproducibility is good for this toy run but provenance is incomplete

**Evidence:** Dependencies are pinned in `requirements.txt:1-5`, and the seed is recorded in `artifacts/summary.json:2`. But `run()` has fixed generation/model defaults (`src/experiment.py:55-65`), emits CSV/PNG/JSON only, and does not record Python/package versions, code revision, generation parameters, or a model/scaler artifact. The README says production data should refit the scaler and K-Means (`README.md:40`), but no scoring implementation is included.

**Risk:** A future artifact cannot be independently tied to an exact environment or source revision, and the exported assignment table cannot safely assign segments to new customers.

**Concrete fix:** Record environment versions, source revision, generator parameters, feature statistics, and an artifact manifest. Serialize the fitted preprocessing/model or provide a tested scoring command that applies the same transformations and handles unknown/low-confidence cases.

### [LOW] Tests do not assert semantic correctness of generated artifacts

**Evidence:** `tests/test_experiment.py:18-23` checks only that five output files exist. It does not check CSV row count, feature schema, finite metric values, nonempty/contiguous clusters, agreement between `summary.json` and CSV scores, or assignment reproducibility after an isolated run.

**Concrete fix:** Add artifact-content tests and a dashboard fixture test: validate 120 rows and four numeric features, exactly the selected k nonempty clusters, metric recomputation, summary/artifact consistency, and schema/error handling for missing or stale files.

## Checks run

- `./.venv/bin/python -m pytest -q` — **3 passed**; 15 third-party warnings (Matplotlib deprecations and a joblib CPU-detection warning).
- `./.venv/bin/python -m py_compile src/experiment.py tests/test_experiment.py` — **passed**.
- `node --check app.js` — **passed**.
- Isolated `run()` to a temporary output directory — **passed**, selecting k=3 and reproducing the committed summary values.
- Visual inspection of `artifacts/segmentation.png` — plot rendered and matches the documented two-panel silhouette/PCA diagnostic; it remains an in-sample visual diagnostic, not validation evidence.
