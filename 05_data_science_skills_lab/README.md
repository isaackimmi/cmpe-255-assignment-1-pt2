# Project 05 — Data Science Skills Lab

This offline lab covers CSV ingestion, validation/cleaning, exploratory statistics, regression, binary classification, clustering, metrics, and plots using only Python’s standard library.

## Quick start

From this directory:

```bash
python3 run_lab.py
python3 -m unittest discover -s tests -v
```

The run writes `artifacts/metrics.json`, `artifacts/summary.json`, and an SVG scatter plot. SVG is viewable in any browser.

## Reproducibility

Python 3.9+ is recommended. The pipeline uses seed `255` for the split/clustering initialization and has no network dependency. Delete `artifacts/` and rerun for identical outputs.

## Deviations and scope

The original Project 05 prompt was not present in the supplied repository, so this follows the requested “data science skills lab” intent rather than claiming a verbatim reproduction. It uses a compact synthetic customer-health CSV instead of a remote/public dataset and standard-library implementations instead of pandas/scikit-learn/matplotlib. These choices keep the lab runnable offline; the algorithms are educational implementations, not production replacements for mature libraries.
## Integration verification

- **Prompt alignment:** Public Project 05 asks for data-science skills and CRISP-DM; the lab covers ingestion, cleaning, EDA, regression, classification, clustering, metrics, and plots.
- **Results/artifacts:** 23 cleaned rows, accuracy 0.8261, regression MAE 4.3804; unittest passed 4/4.
- **Issue/resolution:** External skill repositories and Kaggle data were replaced by safe offline fixtures and standard-library implementations.
