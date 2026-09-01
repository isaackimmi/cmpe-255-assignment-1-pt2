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

The project includes a responsive React dashboard in `client/`. Vite builds the application, Material UI supplies accessible interaction primitives, and the client calls FastAPI for artifact-backed evidence rather than inventing metrics in the browser.

For a demo, one command handles dependencies, starts FastAPI and React, opens <http://127.0.0.1:5175>, and stops both with one `Ctrl-C`:

```bash
./run_demo.sh
```

The commands below remain available for artifact regeneration and manual development.

The end-to-end layout mirrors the reference repository:

```text
client/   React + Vite + Material UI dashboard
server/   FastAPI composition root, routers, schemas, and evidence services
ml/       artifact contracts, repository, and read-only analytical service
```

From this directory, regenerate the artifacts and start the API and client in separate terminals:

```bash
python3 run_lab.py
python3 -m pip install -r server/requirements.txt
python3 -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8005
# second terminal
cd client
npm install
npm run dev
```

Open <http://localhost:5175>. Stop both processes with `Ctrl-C` when finished. The available API routes are `/api/health`, `/api/summary`, `/api/cleaning`, `/api/classification`, `/api/regression`, `/api/clustering`, and `/api/rows`. The client calls the module-specific route as you navigate and calls `/api/rows?plan=...&renewal=...&cluster=...` when filters change. Vite proxies `/api` to port 8005 through `client/vite.config.js`; set `VITE_API_URL=http://127.0.0.1:8005` when the API is hosted on another origin.

The dashboard is intentionally labeled **offline-ready** and **synthetic fixture**. The CSV is a compact teaching dataset, not a public production dataset. Its metrics are reproducibility evidence for the lab—not business, causal, or production forecasting claims. The client does not silently replace failed API requests with browser-only model results.

The DS remains the main character: `run_lab.py` and `src/skills_lab.py` own validation, fold-local imputation, baselines, regression, classification, clustering, and artifact generation. FastAPI exposes those results with explicit missing-artifact errors; the client is an evidence exploration layer.

### Code organization

The frontend is composed rather than assembled in one entry file. `client/src/components/` contains the `AppShell`, `ModuleNav`, metric grid/cards, filters, evidence container, and one focused panel per analytical module. `client/src/hooks/useLabData.js` owns request state while `client/src/api/labApi.js` owns HTTP details. Theme tokens live in `theme.js`; presentation remains in scoped CSS files.

Global plan, renewal, and cluster controls filter the reusable row-evidence panel shown alongside every module. They do **not** recompute the fixed checked-in model metrics; that boundary is stated next to the count and active filter chips. Abort controllers plus request identities guarantee latest-request-wins behavior for rapid navigation and filtering. Client response validators and an evidence error boundary prevent malformed nested artifacts from crashing the full shell.

Frontend quality checks are available from `client/`:

```bash
npm run lint
npm test
npm run build
```

Vitest and React Testing Library cover navigation/retry behavior, query composition, nested contracts, and out-of-order module/filter responses. Evidence rows and confusion matrices use semantic tables, while visual charts include textual figure alternatives.

The backend follows the same boundary discipline. `server/main.py` only composes the application, `server/routers/` defines HTTP routes, `server/schemas.py` validates filter domains, and `server/services/evidence.py` translates analytical errors into API behavior. In `ml/`, artifact I/O, contracts, and source-evidence assembly are separate modules; `pipeline.py` remains a small compatibility facade for existing imports.

### Dashboard checks

- Confirm the header reports `API CONNECTED`.
- Select the five module views and confirm the detail panel changes.
- Filter by plan, renewal outcome, and cluster group; inspect the returned row table.
- Compare the model to the baseline, then inspect the classification confusion matrix and cluster profiles.
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
