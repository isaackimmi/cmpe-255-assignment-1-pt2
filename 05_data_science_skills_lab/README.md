# Project 05 — Data Science Skills Lab

This offline lab covers CSV ingestion, validation/cleaning, exploratory statistics, regression, binary classification, clustering, metrics, and plots using only Python’s standard library.

## Quick start

From this directory:

```bash
python3 run_lab.py
python3 -m unittest discover -s tests -v
```

The run writes `artifacts/metrics.json`, `artifacts/summary.json`, and two SVG scatter plots. SVG is viewable in any browser.

## Dashboard

The project includes a responsive browser dashboard in `index.html`. It reads `artifacts/metrics.json` and `artifacts/summary.json` at runtime, renders an inline evidence explorer from those artifacts, and provides an interactive selector for the five lab modules.

From this directory, regenerate the artifacts and start a local static server:

```bash
python3 run_lab.py
python3 -m http.server 8000
```

Open <http://localhost:8000> in a browser. A static server is required because browsers block `fetch()` for local `file://` pages. Stop it with `Ctrl-C` when finished. No network request or third-party runtime is needed by the dashboard; it uses system font stacks and browser-native APIs.

The dashboard is intentionally labeled **offline-ready** and **synthetic fixture**. The CSV is a compact teaching dataset, not a public production dataset. Its metrics are reproducibility evidence for the lab—not business, causal, or production forecasting claims.

### Dashboard checks

- Confirm the footer reports `ARTIFACT STATUS: READY`.
- Select all five module rows and confirm the detail panel changes.
- Switch between `01 / trend` and `02 / groups`; filter by plan, renewal outcome, and cluster group; and inspect the plotted-row table.
- Hover or keyboard-focus a point to inspect its customer-level values and verify the evidence count changes with filters.
- Resize the browser to a narrow viewport to check the responsive layout.

## Evaluation and reproducibility

Python 3.9+ is recommended. The pipeline has no network dependency and validates the required schema, finite numeric values, nonnegative domains, known plans, binary labels, and duplicate-ID consistency before analysis. `load_clean(..., impute=False)` preserves missing values so the model boundaries are explicit.

- Regression uses a seeded (`255`) shuffled 70/30 holdout. Numeric feature medians are fit on training rows only. Rows with a missing `monthly_usage` target are excluded from training/scoring rather than scored against an imputed target. The artifact reports observed scored rows, excluded targets, MAE/RMSE/R², and a train-mean baseline.
- Classification evaluates the fixed domain rule on a seeded stratified holdout and reports F1, specificity, balanced accuracy, sample count, and a training-derived majority-class baseline. The threshold is not tuned on this fixture.
- Clustering imputes descriptive inputs explicitly, z-score scales usage and support tickets, evaluates candidate `k` values 1–4 with silhouette scores and inertia, and uses 20 seeded initializations for the selected two-cluster result. Centers in the artifact are converted back to the original units for interpretation.
- Correlations use observed usage values and are labeled descriptive associations. Missingness, imputation counts, configuration, and the input SHA-256 are recorded in the generated artifacts.

Delete `artifacts/` and rerun for identical outputs.

## Deviations and scope

The original Project 05 prompt was not present in the supplied repository, so this follows the requested “data science skills lab” intent rather than claiming a verbatim reproduction. It uses a compact synthetic customer-health CSV instead of a remote/public dataset and standard-library implementations instead of pandas/scikit-learn/matplotlib. These choices keep the lab runnable offline; the algorithms are educational implementations, not production replacements for mature libraries.
## Integration verification

- **Prompt alignment:** Public Project 05 asks for data-science skills and CRISP-DM; the lab covers ingestion, cleaning, EDA, regression, classification, clustering, metrics, and plots.
- **Results/artifacts:** generated metrics include validation counts, observed held-out scores, baselines, scaled-clustering diagnostics, and configuration metadata; run `python3 run_lab.py` to regenerate the current snapshot.
- **Tests:** 8 regression tests cover validation failures, fold-local imputation, held-out artifact integrity, degenerate SVG inputs, numerical edge cases, and deterministic multi-initialized k-means. The generated `summary.json` also carries each descriptive clustering row’s selected cluster label for the dashboard explorer.
- **Issue/resolution:** External skill repositories and Kaggle data were replaced by safe offline fixtures and standard-library implementations.
