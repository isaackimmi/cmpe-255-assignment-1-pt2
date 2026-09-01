# Project 03 — Customer Segmentation Clustering

An end-to-end, reproducible customer-segmentation experiment based on the original Project 03 prompt in [`PROMPTS.md`](https://github.com/dlmastery/data_science_examples/blob/main/PROMPTS.md): clustering, CRISP-DM, research-aware evaluation, and data-science reporting. This compact implementation intentionally uses a generated retail sample instead of requiring a Kaggle download, so it runs offline and is fully reproducible.

## Result

The experiment predeclares candidate **k=2…7** and compares `StandardScaler` with a `log1p` monetary-feature variant. Each candidate is fit on 12 repeated 80/20 train/validation splits; the reported selection signal is mean held-out silhouette, with adjusted Rand index (ARI) stability as a tie-breaker. Full-sample silhouette, Calinski–Harabasz, and Davies–Bouldin values are retained as descriptive diagnostics, not performance estimates. The selected run writes validation distributions, assignments, a PCA visualization, a manifest, and a JSON model card to `artifacts/`.

## Reproduce

```bash
python3 -m pip install -r requirements.txt -r server/requirements.txt
python3 -m src.experiment
python3 -m pytest -q
```

For an isolated setup, use Python 3.11+ and create a virtual environment before installing the two requirement files:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r server/requirements.txt
```

Expected outputs include `artifacts/segmentation.png`, `summary.json`, `manifest.json`, and five CSV reports. The data generator creates 120 customers across three intentionally interpretable prototypes (budget/infrequent, frequent/high-spend, and affluent/premium); it is a prototype-recovery teaching sample, not a claim about real customer behavior.

## Interactive dashboard

The project includes a dependency-free browser dashboard in `index.html`. It loads the summary, both preprocessing score tables, validation scores, assignments, point-level explorer diagnostics, plot, and manifest at runtime. The UI checks exact schemas, finite numeric values, row counts, selected-model metadata, and the complete SHA-256 hash set before showing a verified status; run the experiment first if artifacts are missing or stale. The summary’s feature audit is descriptive for the generated sample, not a substitute for a real-data quality policy.

The polished E2E version is split into a React/Vite client built from reusable MUI components, a modular FastAPI evidence/scoring server, and an `ml/` adapter around the canonical reproducible experiment:

```text
client/   React + MUI component tree, data hook/API client, and SVG explorer
server/   FastAPI app factory, routers, schemas, artifact repository, profile service
ml/       Stable pipeline facade plus scoring, contracts, and preprocessing modules
```

From this directory, first regenerate the canonical artifacts and run the tests:

```bash
python3 -m src.experiment
python3 -m pytest -q
```

Run the API and client in separate terminals when doing a local demo (only one project server should be running at a time):

```bash
python3 -m uvicorn server.app:app --reload --port 8003
cd client
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The client calls the API for the manifest, summary, profiles, point-level explorer data, and new-customer scoring. Use the segment filter and feature selectors to explore profiles, then submit the estimator form to exercise the `/api/score` endpoint. The PCA map and geometry confidence are visualization/assignment diagnostics, not probabilities or outcome predictions.

The point explorer uses a roving keyboard focus model: Tab enters the selected point, arrow keys move between points, and Enter/Space selects. A synchronized semantic HTML table provides the same customer, segment, feature, and assignment evidence without relying on the SVG. Segment changes automatically reconcile the selected point so the inspector cannot display a customer outside the active filter.

Frontend verification is self-contained:

```bash
cd client
npm test       # Vitest + React Testing Library behavior contracts
npm run lint   # ESLint + React Hooks rules
npm run build  # production Vite bundle
```

## CRISP-DM trace

1. **Business understanding:** identify actionable customer groups for differentiated offers.
2. **Data understanding:** inspect four numeric behavioral/value features; the generator documents distributions and bounds. Point-level map data is exported to `artifacts/explorer_points.csv`.
3. **Data preparation:** validate the feature contract, optionally apply log1p to the two monetary fields, then fit `StandardScaler` on each training split. No target is used and no labels enter preprocessing.
4. **Modeling:** fit K-Means for the predeclared k=2…7 candidates with 25 initializations.
5. **Evaluation:** use repeated held-out silhouette means and uncertainty, partition stability via ARI, descriptive full-sample metrics, a PCA projection, and a measured preprocessing comparison.
6. **Deployment/use:** use the exported table only for hypothesis generation; `fit_segmenter()` and `score_customers()` provide a paired preprocessing/model scoring path for future observed data. The browser explorer is a selected-run inspection surface, not a production assignment tool.

## Limitations and responsible use

This is a teaching experiment, not a production segmentation. The synthetic clusters are clean and may overstate separability; K-Means assumes roughly spherical clusters and Euclidean geometry; PCA is only for visualization; internal metrics do not establish business value or fairness. Before deployment, validate on real longitudinal transactions, test segment stability over time, compare against hierarchical/DBSCAN alternatives, add business outcomes, and monitor drift. Do not use segments to deny service or infer sensitive traits.

## Project layout

- `src/experiment.py` — data contract, preprocessing, repeated validation, stability, scoring, and artifact checks.
- `client/src/components/` — composable React presentation and interaction components; MUI supplies accessible fields, cards, feedback, and buttons.
- `client/src/hooks/` and `client/src/api/` — data orchestration and HTTP boundaries kept out of presentation components.
- `server/application.py` and `server/routers/` — FastAPI app factory and route modules; `server/app.py` remains the stable ASGI entry point.
- `server/services/` — artifact validation/I/O and profile derivation, independent of HTTP routing.
- `ml/pipeline.py` — stable compatibility facade; focused scoring/contracts/preprocessing logic lives in sibling modules.
- `tests/test_experiment.py` — reproducibility, validation, scoring, and artifact-content tests.
- `artifacts/` — generated outputs (created by the run command), including the browser-ready `explorer_points.csv` diagnostics.
- `reports/` — reserved for a future full research report.
## Integration verification

- **Prompt alignment:** Public Project 03 asks for clustering with CRISP-DM and a dashboard; clustering, preprocessing comparison, evaluation, and reporting are implemented offline.
- **Results/artifacts:** the selected k and preprocessing are based on repeated held-out validation; the manifest and Python validator cross-check artifact schemas, hashes, and metric agreement.
- **Issue/resolution:** Kaggle data/dashboard dependencies were replaced with deterministic synthetic data and compact artifacts.
