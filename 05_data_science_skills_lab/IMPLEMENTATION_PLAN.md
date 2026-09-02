# Implementation Plan — Data Science Skills Lab

## Retrospective scope

This plan documents the compact offline lab and its artifact-backed dashboard. One synthetic customer-health fixture is used to demonstrate ingestion, validation, cleaning, EDA, regression, classification, clustering, metrics, and plots with standard-library implementations.

## Objectives

1. Demonstrate a complete DS workflow across several common analytical tasks.
2. Make validation, missingness, imputation, baselines, holdout populations, and configuration visible.
3. Keep the lab deterministic, offline-ready, and easy to rerun.
4. Provide a React/MUI evidence dashboard rather than exposing only Python output.
5. Prevent global filters from being mistaken for new model evaluations.

## Data and preparation

1. Validate the CSV schema, finite numeric values, nonnegative domains, known plans, binary labels, and duplicate IDs.
2. Preserve missing values during raw loading so cleaning boundaries remain explicit.
3. Fit numeric feature medians on training rows only, then apply them to validation/holdout rows.
4. Exclude rows with missing regression targets instead of imputing the target and scoring against a fabricated value.
5. Record missingness, imputation counts, source SHA-256, seed, configuration, and generated artifact metadata.

## Modeling and evaluation

1. Regression: use a seeded 70/30 shuffled holdout, train-only imputation, a simple model, and a train-mean baseline; report MAE, RMSE, and R² on observed targets.
2. Classification: use a seeded stratified holdout, a fixed domain rule, confusion matrix, F1, specificity, balanced accuracy, and a training-derived majority-class baseline.
3. Clustering: impute descriptive inputs explicitly, standardize usage/support-ticket features, evaluate candidate `k` with silhouette/inertia, and use multiple seeded initializations for the selected solution.
4. EDA: report correlations as descriptive observed-data associations, not causal claims.
5. Generate JSON summaries and SVG plots as the stable evidence contract.

## Application sequence

1. Keep `run_lab.py` and `src/skills_lab.py` responsible for validation, analytical computation, and artifact generation.
2. Split the ML layer into artifact repository, contracts, and read-only evidence assembly; retain `pipeline.py` as a compatibility facade.
3. Split FastAPI composition, routers, schemas, and evidence services, with explicit missing-artifact error handling.
4. Build React/Vite/MUI components for the shell, module navigation, metric grid/cards, filters, evidence container, cleaning/classification/regression/clustering panels, and semantic chart alternatives.
5. Use cancellable latest-request-wins hooks, response validators, section-level retry states, and an evidence error boundary.
6. Filter row evidence server-side by plan, renewal, and cluster while keeping fixed holdout metrics unchanged and visibly labeled.

## Validation criteria

- Re-running after deleting artifacts produces identical outputs.
- Tests cover validation failures, fold-local imputation, holdout integrity, numerical edge cases, and deterministic clustering.
- API routes return typed evidence and actionable missing-artifact errors.
- Client tests cover navigation/retry, query composition, nested contracts, out-of-order responses, and accessibility.
- Lint, Vite build, Python tests, and the dashboard’s API-connected smoke path pass.

## Limitations and next steps

The fixture is synthetic and the algorithms are educational rather than production replacements for mature libraries. A stronger follow-up would use a documented public dataset, richer feature engineering, repeated/time-based evaluation where appropriate, calibrated models, fairness analysis, and drift monitoring.
