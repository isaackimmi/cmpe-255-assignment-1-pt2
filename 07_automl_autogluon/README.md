# Project 07 — AutoML / Model Comparison

The source Project 07 prompt is: “Now lets do another project - illustrate automl with autogluon on various data science tasks - make sure you follow crisp-dm framework and also include nice data science admin dashboard. you can research the papers and implement autoresearch to do hill climbing and match the dashboard details with research paper. include all details a data scientist and ai engineer will care.”

This implementation reproduces the core AutoML/model-comparison experiment as a lightweight, CPU-safe tabular classification run. It compares several scikit-learn models on the reproducible breast-cancer dataset bundled with scikit-learn and writes a ranked leaderboard plus test-set metrics. A dependency-free browser dashboard turns those artifacts into a model handoff view.

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

Open <http://localhost:8000> and use the leaderboard cards or model selector to inspect each run. The UI loads `artifacts/leaderboard.csv`, `artifacts/metrics.json`, and `artifacts/dataset_summary.json` at runtime. It includes ranked model cards, ROC-AUC/accuracy/fit-time comparisons, backend status, model details, a CRISP-DM workflow, and reproduction instructions.

The experiment uses a fixed random seed, a stratified 80/20 holdout, and CPU-safe model settings. It does not download data. The generated files are:

- `artifacts/leaderboard.csv` — ranked test-set model comparison
- `artifacts/metrics.json` — run metadata and metrics
- `artifacts/dataset_summary.json` — dataset and split summary
- `index.html`, `styles.css`, `app.js` — responsive, dependency-free leaderboard UI

## AutoGluon behavior

If `autogluon.tabular` is installed, the runner executes an additional AutoGluon model using `presets="medium_quality"`, `time_limit=60`, `num_cpus=1`, and `verbosity=0`. AutoGluon is optional because it is a large dependency and may not be available in a CPU-only teaching environment. When it is unavailable, the runner continues with the sklearn comparison and records `backend: sklearn_fallback` plus the reason in `metrics.json`.

The sklearn fallback is intentionally explicit rather than pretending to be AutoGluon: it provides a small model-comparison/leaderboard experiment with equivalent reproducibility and evaluation outputs, but it does not reproduce AutoGluon's ensembling or search space.

## Dataset and evaluation

The dataset is `sklearn.datasets.load_breast_cancer`, with 569 rows, 30 numeric features, and a binary target. The holdout test set is never used for model selection. Models are fit on the training split and ranked by test ROC-AUC (with accuracy, balanced accuracy, F1, and fit time also reported). This is a compact demonstration dataset, not a production benchmark.

## Limitations and deviations

- The checkout supplied for this task initially did not contain a Project 07 directory. The local `PROMPTS_USED.md` points to the referenced `PROMPTS.md`; the source Project 07 prompt is preserved above. This implementation follows the delegated requirements and narrows the original broad brief to a reproducible CPU-safe experiment with a local static dashboard.
- Research-paper and autoresearch/hill-climbing deliverables from the broad source prompt are intentionally out of scope for this delegated reproduction. The dashboard covers the requested CRISP-DM workflow and model-comparison/admin view without implying that a research-grade search process was run.
- AutoGluon results can vary slightly by version and are not asserted by the tests. The sklearn path is deterministic for the configured seed.
- A single fixed holdout is appropriate for a quick assignment reproduction but is weaker than repeated cross-validation.
- The dataset is small and clean, so results should not be interpreted as evidence for deployment performance.
## Integration verification

- **Prompt alignment:** Public Project 07 asks for AutoML, CRISP-DM, research, autoresearch, and dashboard details; CPU-safe model comparison and explicit backend reporting are implemented.
- **Results/artifacts:** Sklearn fallback ranked logistic regression first (ROC-AUC 0.9947, accuracy 0.9561); artifacts regenerated; pytest passed 2/2.
- **Issue/resolution:** AutoGluon was skipped with `--no-autogluon` because it is heavyweight; fallback is labeled honestly.
