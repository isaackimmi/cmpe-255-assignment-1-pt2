# Comparison Report

The portfolio is a faithful lightweight reproduction of the reference project themes, not a claim that every original production-scale feature is present. The public source is the reference PROMPTS.md; prompt-by-prompt mapping is in PROMPTS_USED.md.

## UI coverage

All 14 projects now have a browser-facing presentation layer. The dashboards read checked-in outputs and provide project-specific metric cards, charts, phase context, and analytical interactions. Controls that do not call the Python runtime are explicitly labeled artifact-backed or illustrative; the underlying experiments remain the source of truth.

Rendered evidence for each dashboard is checked into `ui_screenshots/project-00.png` through `project-13.png` and was refreshed during a sequential localhost smoke-review pass.

## Final polish review

The final pass reviewed every project twice: first for analytical soundness, then for UI usefulness. The highest-value upgrades added explicit evaluation populations, baselines, fold/holdout boundaries, uncertainty, provenance, artifact-backed explorers, synthetic-data framing, and functional filters/threshold/sort/detail controls. Project-level evidence and limitations are recorded in each `FINAL_POLISH_REVIEW.md`.

| Project | Reference intent | Implemented comparison | Result/artifact |
|---|---|---|---|
| 00 | Dynamic todo app | Local-first dependency-free task/workspace UI | HTML app; 4/4 tests |
| 01 | NYC taxi end-to-end prediction | Offline fallback, temporal split, regression, SVG outputs | MAE 82.045s; validation passed |
| 02 | Small LLM/chatbot | Character n-gram baseline plus optional causal Transformer | Perplexity 22.1789; 3/3 tests |
| 03 | Kaggle-style clustering | Deterministic customer sample, k search, preprocessing comparison | k=3, silhouette 0.6696 |
| 04 | Associative mining | Apriori and lift-ranked rules on checked-in baskets | 18 itemsets; SVG plot |
| 05 | Skills demonstration | Offline lab covering core DS methods | Accuracy 0.8261; SVGs/JSON |
| 06 | Anomaly detection | Isolation Forest, LOF, Elliptic Envelope, rank ensemble | Best F1 0.64; PNG/JSON |
| 07 | AutoML/AutoGluon | CPU-safe sklearn leaderboard with optional AutoGluon branch | Best ROC-AUC 0.9947 |
| 08 | Visual DS teaching page | Static GitHub Pages-ready interactive curriculum | 4 snapshots; 6/6 tests |
| 09 | Full-stack DAG demonstration | Dependency-free DAG core and multi-step example | Deterministic order; 6/6 tests |
| 10 | CRISP-DM curriculum | Iris-based CRISP-DM report and supervised baseline | Accuracy 0.9333 |
| 11 | Portfolio audit | Governance-defect fixture and audit report | 4 failures; CONDITIONAL |
| 12 | Forecasting website | Chronological series, baseline/model, recursive forecast | Naive MAE 0.7678 |
| 13 | Enterprise taxi audit platform | Integrated audit, model, report, inference CLI | MAE 2.794m; 4/4 tests |

## Cross-project observations

- Reproducibility is strongest where data are checked in or deterministically generated, seeds are fixed, and outputs are machine-readable.
- Temporal projects (01, 12, 13) preserve chronological evaluation; Project 06 explicitly documents that its compact scaling demonstration should be tightened for production.
- The portfolio's main gap against the public reference is breadth of UI/deployment and external-data integration, not missing test evidence in the compact implementations.
