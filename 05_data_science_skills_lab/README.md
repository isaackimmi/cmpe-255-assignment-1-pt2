# Project 05 — Data Science Skills Lab

This offline lab covers CSV ingestion, validation/cleaning, exploratory statistics, regression, binary classification, clustering, metrics, and plots using only Python’s standard library.

## Quick start

From this directory:

```bash
python3 run_lab.py
python3 -m unittest discover -s tests -v
```

The run writes `artifacts/metrics.json`, `artifacts/summary.json`, and an SVG scatter plot. SVG is viewable in any browser.

## Dashboard

The project includes a responsive browser dashboard in `index.html`. It reads `artifacts/metrics.json` and `artifacts/summary.json` at runtime, displays the generated SVG artifacts, and provides an interactive selector for the five lab modules.

From this directory, regenerate the artifacts and start a local static server:

```bash
python3 run_lab.py
python3 -m http.server 8000
```

Open <http://localhost:8000> in a browser. A static server is required because browsers block `fetch()` for local `file://` pages. Stop it with `Ctrl-C` when finished. No network request or third-party runtime is needed by the dashboard; it uses system font stacks and browser-native APIs.

The dashboard is intentionally labeled **offline-ready** and **synthetic fixture**. The CSV is a compact teaching dataset, not a public production dataset, and its metrics should be read as reproducibility evidence for the lab—not as business or forecasting claims.

### Dashboard checks

- Confirm the footer reports `ARTIFACT STATUS: READY`.
- Select all five module rows and confirm the detail panel changes.
- Switch between `01 / trend` and `02 / groups` to verify both existing SVG artifacts render.
- Resize the browser to a narrow viewport to check the responsive layout.

## Reproducibility

Python 3.9+ is recommended. The pipeline uses seed `255` for the split/clustering initialization and has no network dependency. Delete `artifacts/` and rerun for identical outputs.

## Deviations and scope

The original Project 05 prompt was not present in the supplied repository, so this follows the requested “data science skills lab” intent rather than claiming a verbatim reproduction. It uses a compact synthetic customer-health CSV instead of a remote/public dataset and standard-library implementations instead of pandas/scikit-learn/matplotlib. These choices keep the lab runnable offline; the algorithms are educational implementations, not production replacements for mature libraries.
## Integration verification

- **Prompt alignment:** Public Project 05 asks for data-science skills and CRISP-DM; the lab covers ingestion, cleaning, EDA, regression, classification, clustering, metrics, and plots.
- **Results/artifacts:** 23 cleaned rows, accuracy 0.8261, regression MAE 4.3804; unittest passed 4/4.
- **Issue/resolution:** External skill repositories and Kaggle data were replaced by safe offline fixtures and standard-library implementations.
