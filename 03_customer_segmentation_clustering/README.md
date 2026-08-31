# Project 03 — Customer Intelligence Clustering

An end-to-end, reproducible customer-segmentation experiment based on the original Project 03 prompt in [`PROMPTS.md`](https://github.com/dlmastery/data_science_examples/blob/main/PROMPTS.md): clustering, CRISP-DM, research-aware evaluation, and data-science reporting. This compact implementation intentionally uses a generated retail sample instead of requiring a Kaggle download, so it runs offline and is fully reproducible.

## Result

The experiment selects **k=3** using the maximum silhouette score over k=2…7. The selected model is K-Means with 25 initializations and seed 255. It compares a baseline `StandardScaler` pipeline with the improvement `log1p` on annual income and average order value followed by `StandardScaler`; this makes monetary skew less dominant. The selected run writes metrics, assignments, a PCA visualization, and a JSON model card to `artifacts/`.

## Reproduce

```bash
python3 -m pip install -r requirements.txt
python3 -m src.experiment
python3 -m pytest -q
```

Expected outputs include `artifacts/segmentation.png`, `summary.json`, and the three CSV reports. The data generator creates 120 customers across three intentionally interpretable prototypes (budget/infrequent, frequent/high-spend, and affluent/premium); it is not a claim about real customer behavior.

## Interactive dashboard

The project includes a dependency-free browser dashboard in `index.html`. It loads `artifacts/summary.json`, `artifacts/improved_scores.csv`, and `artifacts/customer_segments.csv` at runtime, so run the experiment first if the artifacts are missing or stale.

From this directory, run:

```bash
python3 -m src.experiment
python3 -m pytest -q
python3 -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000). Use the segment filter and feature selector to explore the profile cards, click through the CRISP-DM phase navigator, and review the exported segmentation image. Serving the directory over HTTP is required because browsers block `fetch()` requests for local files opened directly with `file://`.

## CRISP-DM trace

1. **Business understanding:** identify actionable customer groups for differentiated offers.
2. **Data understanding:** inspect four numeric behavioral/value features; the generator documents distributions and bounds.
3. **Data preparation:** clip impossible synthetic values, apply log1p to skew-prone monetary fields, then standardize. No target is used and no labels enter preprocessing.
4. **Modeling:** fit K-Means for k=2…7 with deterministic initialization.
5. **Evaluation:** use silhouette (primary), Calinski–Harabasz, Davies–Bouldin, a PCA projection, and a preprocessing comparison.
6. **Deployment/use:** export a segment assignment table for downstream campaign design; refit the scaler and K-Means together on production data.

## Limitations and responsible use

This is a teaching experiment, not a production segmentation. The synthetic clusters are clean and may overstate separability; K-Means assumes roughly spherical clusters and Euclidean geometry; PCA is only for visualization; internal metrics do not establish business value or fairness. Before deployment, validate on real longitudinal transactions, test segment stability over time, compare against hierarchical/DBSCAN alternatives, add business outcomes, and monitor drift. Do not use segments to deny service or infer sensitive traits.

## Project layout

- `src/experiment.py` — data generation, preprocessing, model selection, metrics, and plots.
- `tests/test_experiment.py` — reproducibility, selection, and artifact tests.
- `artifacts/` — generated outputs (created by the run command).
- `reports/` — reserved for a future full research report.
## Integration verification

- **Prompt alignment:** Public Project 03 asks for clustering with CRISP-DM and a dashboard; clustering, preprocessing comparison, evaluation, and reporting are implemented offline.
- **Results/artifacts:** k=3, silhouette 0.6696, Calinski–Harabasz 452.34, Davies–Bouldin 0.4672; run and pytest passed 3/3.
- **Issue/resolution:** Kaggle data/dashboard dependencies were replaced with deterministic synthetic data and compact artifacts.
