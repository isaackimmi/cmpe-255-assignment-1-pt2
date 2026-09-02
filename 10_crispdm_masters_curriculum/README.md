# Project 10: Iris CRISP-DM walkthrough

This is a bounded, runnable teaching implementation of all six CRISP-DM phases for one supervised classification task. It uses scikit-learn's built-in Iris sample, so it needs no download or credentials. It is not a complete implementation of the broader “masters curriculum” topics such as clustering, anomaly detection, association rules, LSH, quizzes, or synthesis; those topics are separate portfolio projects.

## Run

From this directory:

```bash
python3 -m pip install -r requirements.txt
python3 src/crispdm_demo.py
pytest -q
```

The run writes:

- `artifacts/crispdm_report.json`: machine-readable phase notes, data-quality checks, CV/model comparison, uncertainty, runtime metadata, and hashes.
- `artifacts/iris_snapshot.csv`: the exact local data snapshot used by the run.
- `artifacts/model.joblib`: a versioned bundle containing the fitted pipeline and its inference contract.

Use `--output-dir path/to/output` to write to another directory. The fixed seed is `42`; model selection uses repeated stratified CV on training rows only, while the fixed 30-row holdout is used once for final evaluation.

## Local inference

After generating the artifacts, run a schema-validated prediction:

```bash
python3 src/inference.py \
  --model-path artifacts/model.joblib \
  --features 5.1 3.5 1.4 0.2
```

The contract requires the four positional features in this order: sepal length, sepal width, petal length, petal width. Values must be finite numeric centimeter measurements in the inclusive range `[0, 10]`. Invalid, missing, or out-of-range input is rejected; values are never silently reordered or imputed. Because a positional payload has no feature names with which to detect a plausible swap, callers with schema metadata should use named input, which canonicalises by exact feature name and rejects missing or extra keys:

```bash
python3 src/inference.py \
  --model-path artifacts/model.joblib \
  --named-features '{"sepal length (cm)":5.1,"sepal width (cm)":3.5,"petal length (cm)":1.4,"petal width (cm)":0.2}'
```

## Interactive dashboard

Serve this directory so the browser can fetch the report (opening `index.html` directly may block `fetch()` in some browsers):

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000>. The six cards are a visual guide to this one supervised walkthrough, and the JSON report remains the source of truth. The dashboard includes an artifact-backed candidate/baseline/metric explorer, repeated-CV score distribution, clickable confusion-matrix row details, artifact fingerprints, and a named-feature contract checker. Browser validation does not execute the model; use the local inference command for that.

## What the run demonstrates

1. **Business understanding:** define the classroom decision, stakeholders, constraints, and what the result cannot claim.
2. **Data understanding:** validate schema, finite values, labels, ranges, duplicates, class balance, provenance, and a content hash.
3. **Data preparation:** make a reproducible stratified split with a locked holdout and keep learned preprocessing inside each pipeline.
4. **Modeling:** compare a majority baseline, scaled logistic regression, scaled k-nearest neighbors, and a shallow decision tree with 3×5-fold CV on training data only.
5. **Evaluation:** report holdout accuracy, a 95% Wilson interval, baseline delta, confusion matrix, per-class scores/support, and failure cases.
6. **Deployment:** save the fitted bundle, enforce the input contract, and document monitoring windows, actions, rollback, and the boundary between local inference and production approval.

## Claim boundary and limitations

The model artifact supports local, schema-validated inference on Iris-like measurements only. A result such as `28/30` is split-specific evidence, not a production-performance claim. Iris is tiny, clean, and historically familiar; this project has no external validation, validated business cost matrix, fairness study, live service, or representative operational population. Before production use, replace the toy data with representative governed data and establish an externally validated acceptance rule.

## Reproducibility

The report records Python, NumPy, scikit-learn, and joblib versions, the data SHA-256, separate model configuration and fitted-artifact fingerprints, artifact hashes, random seed, split protocol, and CV scores. Dependencies are pinned in `requirements.txt`. Run `pytest -q` to verify deterministic splitting, data contracts, report schema, baseline comparison, artifact hashes, holdout row evidence, and inference behavior. The curriculum pass gate is strictly `modeling.beats_baseline_in_cv`; holdout accuracy and its baseline delta are separate, descriptive split-specific readouts.
