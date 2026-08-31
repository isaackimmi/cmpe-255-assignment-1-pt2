# Project 10: CRISP-DM Masters Curriculum

This is a lightweight, runnable end-to-end CRISP-DM demonstration for Assignment 1 Part 2. It uses the public, built-in `sklearn.datasets.load_iris` dataset so no download or credentials are needed.

## Run

From this directory:

```bash
python3 -m pip install -r requirements.txt
python3 src/crispdm_demo.py
pytest -q
```

The run writes `artifacts/crispdm_report.json` (phase-by-phase EDA, preparation, modeling, evaluation, and deployment notes) and `artifacts/iris_snapshot.csv`. Use `--output-dir path/to/output` to write elsewhere.

## Interactive curriculum dashboard

The project includes a responsive, JSON-backed dashboard in `index.html`. It turns the run report into six clickable CRISP-DM phase cards, a phase detail panel, dataset/model summary metrics, and a confusion-matrix evaluation view. The Iris teaching context and production limitations remain explicit in the UI.

After running the demo, serve this directory so the browser can fetch the report (opening `index.html` directly may block `fetch()` in some browsers):

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000> and select any phase card or the matching item in the left curriculum map. Use **View JSON** to inspect the source artifact. The **Run the studio** panel includes the demo/test commands and the local-server command.

## CRISP-DM walkthrough

1. **Business understanding:** define a flower-classification objective and a 0.90 holdout-accuracy success criterion.
2. **Data understanding / EDA:** load Iris, record dimensions, feature names, class balance, and missing-value count.
3. **Data preparation:** use a reproducible stratified 80/20 split. Scaling is fit only on training data through a pipeline.
4. **Modeling:** train `StandardScaler` plus `LogisticRegression`.
5. **Evaluation:** report accuracy, confusion matrix, and per-class precision/recall/F1 on the untouched holdout set.
6. **Deployment:** document a realistic next step and monitoring signals; the example deliberately stops before production deployment.

## Limitations

Iris is tiny, clean, and widely used for teaching, so this result does not establish production performance. The single holdout split has uncertainty, there is no external validation, drift analysis, cost-sensitive metric, model registry, or live API. A real project should confirm the business decision, collect representative data, use cross-validation and a final locked test set, review fairness and failure modes, and add operational monitoring.
## Integration verification

- **Prompt alignment:** Public Project 10 asks for a textbook CRISP-DM project with quizzes, EDA, clustering, anomaly detection, supervised learning, rules, LSH, and synthesis; the compact CRISP-DM walkthrough is implemented and extensions are documented.
- **Results/artifacts:** Iris holdout accuracy 0.9333 on 30 test rows; JSON/CSV regenerated; pytest passed 3/3.
- **Issue/resolution:** Built-in sklearn data avoided downloads; no claim is made that every listed advanced module is complete.
