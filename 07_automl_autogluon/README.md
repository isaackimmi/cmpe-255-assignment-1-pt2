# Project 07 — AutoML / Model Comparison

The source Project 07 prompt is: “Now lets do another project - illustrate automl with autogluon on various data science tasks - make sure you follow crisp-dm framework and also include nice data science admin dashboard. you can research the papers and implement autoresearch to do hill climbing and match the dashboard details with research paper. include all details a data scientist and ai engineer will care.”

This implementation reproduces the core AutoML/model-comparison experiment as a lightweight, CPU-safe tabular classification run. It compares several scikit-learn models on the reproducible breast-cancer dataset bundled with scikit-learn and writes a development-validation leaderboard plus a separately locked final holdout result. A dependency-free browser dashboard turns those artifacts into an auditable benchmark view. The intended operating point treats malignant (label `0`) as the positive class because false negatives are the higher-cost error.

## Run

From this directory:

```bash
python3 -m pip install -r requirements.txt
python3 src/run_experiment.py --output-dir artifacts
python3 -m pytest -q
```

To view the dashboard after generating the artifacts, start a local HTTP server from this directory (the browser fetches the JSON and CSV files, so opening `index.html` directly may be blocked by browser file-access rules):

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000> and use the leaderboard cards or model selector to inspect each run. The UI loads the leaderboard, metadata, dataset summary, final holdout, and fold-level `cv_scores.json` artifacts at runtime. It includes ranked model cards, uncertainty-aware quality/operating-point/fit-time comparisons, backend status, model details, a CRISP-DM workflow, and reproduction instructions.

The experiment uses a fixed random seed, a stratified 80/20 final holdout, and 2x5-fold repeated stratified CV on the remaining development data. It does not download data. The generated files are:

- `artifacts/leaderboard.csv` — ranked development-CV model comparison (the selection signal)
- `artifacts/final_metrics.json` — one final holdout evaluation for the selected model
- `artifacts/metrics.json` — run metadata, backend status, effective settings, and environment
- `artifacts/dataset_summary.json` — dataset and split summary
- `artifacts/cv_scores.json` — all development fold/repeat scores and backend audit-compatible records
- `index.html`, `styles.css`, `app.js` — responsive, dependency-free leaderboard UI

The leaderboard’s selection metric is development-CV ROC-AUC for malignant probability. Each model also gets a threshold selected from its development-only out-of-fold probabilities by malignant F1. The selected threshold is locked before the final holdout is scored. Final metrics include sensitivity, specificity, precision, NPV, PR-AUC, Brier score, and confusion-matrix counts. CV rows include mean, sample standard deviation, and a documented normal-approximation 95% interval; the final holdout is a single evaluation and has no confidence interval.

The dashboard supports sorting by ROC-AUC, balanced accuracy, malignant F1, sensitivity, PR-AUC, or fit time; filtering by backend; and isolating the practical-tie set. These controls change the exploration lens only. They cannot use the final holdout to reorder or select models. Fit time is environment-specific and is not a cross-backend efficiency claim.

## AutoGluon behavior

If `autogluon.tabular` is installed, the runner evaluates an additional AutoGluon candidate on each development-CV fold using `presets="medium_quality"`, `time_limit=60`, `num_cpus=1`, and the recorded seed/settings. It then refits AutoGluon on all development rows only if it wins development CV, before the one final holdout evaluation. AutoGluon is optional because it is a large dependency and may not be available in a CPU-only teaching environment.

The sklearn fallback is intentionally explicit rather than pretending to be AutoGluon. `metrics.json` distinguishes the requested backend, attempted backends, completion/disabled/unavailable/failed status, and failure type. When AutoGluon is evaluated, the run also records per-fit best model, model count, ensemble presence, total search time, and a top-20 internal leaderboard; failed or unavailable runs retain their status and partial audit records. The fallback provides a small deterministic model comparison, but it does not reproduce AutoGluon's ensembling or search space.

## Dataset and evaluation

The dataset is `sklearn.datasets.load_breast_cancer`, with 569 rows, 30 numeric features, and a binary target. Target `0` (`malignant`) is the explicit positive class used for thresholded metrics and probability ranking; benign recall is reported as specificity and benign F1 is retained as `f1_negative_class`. The final holdout is never used for model selection: candidates are ranked by mean development-CV ROC-AUC, then the selected model is refit on all development rows and evaluated on the final holdout once. The leaderboard reports CV means, standard deviations, and intervals; `final_metrics.json` reports the locked holdout metrics. This is a compact demonstration dataset, not a production benchmark.

## Limitations and deviations

- The checkout supplied for this task initially did not contain a Project 07 directory. The local `PROMPTS_USED.md` points to the referenced `PROMPTS.md`; the source Project 07 prompt is preserved above. This implementation follows the delegated requirements and narrows the original broad brief to a reproducible CPU-safe experiment with a local static dashboard.
- Research-paper and autoresearch/hill-climbing deliverables from the broad source prompt are intentionally out of scope for this delegated reproduction. The dashboard covers the requested CRISP-DM workflow and model-comparison/admin view without implying that a research-grade search process was run.
- AutoGluon results can vary slightly by version and environment. The run records package versions, platform, command, dataset hash, model parameters, backend settings, internal search audit, and seed to make that variation auditable.
- Wall-clock fit times are environment-specific; CV fit-time values are means across folds and are not an efficiency ranking under a common resource budget.
- The dataset is small and clean, so results should not be interpreted as evidence for deployment performance.
- `requirements.txt` is a portable minimum manifest. `requirements.lock` pins the fallback verification environment represented by the checked-in artifacts; AutoGluon remains an optional, separately managed environment because its platform-specific dependency set is substantially larger.
## Integration verification

- **Prompt alignment:** Public Project 07 asks for AutoML, CRISP-DM, research, autoresearch, and dashboard details; CPU-safe model comparison and explicit backend reporting are implemented.
- **Results/artifacts:** The development leaderboard ranks candidates using repeated CV; only the selected candidate receives a final holdout result. Artifacts include the protocol and reproducibility manifest.
- **Issue/resolution:** AutoGluon may be skipped with `--no-autogluon` because it is heavyweight; fallback and failure states are labeled honestly.
