# CMPE 255 Assignment 1 — Part 2

This repository documents my reproduction of the data-science projects from the instructor's reference repository using an agentic coding assistant.

Reference: [dlmastery/data_science_examples](https://github.com/dlmastery/data_science_examples)

## Projects

Each numbered directory contains an independent reproduction, its own README, runnable code, tests, and generated artifacts where practical.

## UI layer

Every project now includes a browser-facing UI in addition to its data-science experiment. The dashboards are dependency-light and read checked-in metrics, CSVs, and visual artifacts. Start a static server from this repository root:

```bash
python3 -m http.server 8766
```

Then open the corresponding path:

| Project | UI path |
|---|---|
| 00 | `/00_dynamic_todo_workspace/` |
| 01 | `/01_nyc_taxi_trip_prediction/` |
| 02 | `/02_nano_llm_transformer/` |
| 03 | `/03_customer_segmentation_clustering/` |
| 04 | `/04_associative_pattern_mining/` |
| 05 | `/05_data_science_skills_lab/` |
| 06 | `/06_anomaly_detection/` |
| 07 | `/07_automl_autogluon/` |
| 08 | `/08_datascience_visual_mastery/` |
| 09 | `/09_flowforge_dag_engine/ui/` |
| 10 | `/10_crispdm_masters_curriculum/` |
| 11 | `/11_enterprise_ds_audit/` |
| 12 | `/12_timeseries_forecasting/` |
| 13 | `/13_crispdm_nyc_taxi_audit_platform/dashboard/` |

Each UI includes metric cards, visualizations or artifact previews, explanatory CRISP-DM context, responsive styling, and clear labeling for browser interactions that are illustrative rather than direct Python inference.

Rendered UI screenshots are stored in [`ui_screenshots/`](ui_screenshots/). They were captured from the public GitHub Pages deployment after loading each project dashboard.

| Directory | Focus |
|---|---|
| `00_dynamic_todo_workspace` | Agent-oriented task workspace |
| `01_nyc_taxi_trip_prediction` | Regression and trip prediction |
| `02_nano_llm_transformer` | Small transformer/LLM experiment |
| `03_customer_segmentation_clustering` | Customer clustering |
| `04_associative_pattern_mining` | Market-basket association rules |
| `05_data_science_skills_lab` | Representative data-science skills |
| `06_anomaly_detection` | Anomaly detection and evaluation |
| `07_automl_autogluon` | Automated model comparison |
| `08_datascience_visual_mastery` | Interactive/statistical visualization |
| `09_flowforge_dag_engine` | Data-pipeline DAG concepts |
| `10_crispdm_masters_curriculum` | CRISP-DM workflow demonstration |
| `11_enterprise_ds_audit` | Data-quality and governance auditing |
| `12_timeseries_forecasting` | Chronological forecasting |
| `13_crispdm_nyc_taxi_audit_platform` | Integrated CRISP-DM/taxi audit platform |

## Assignment artifacts

- [Prompt record](PROMPTS_USED.md)
- [Reproduction log](REPRODUCTION_LOG.md)
- [Comparison report](COMPARISON_REPORT.md)
- [Video script](VIDEO_SCRIPT.md)

## Reproducibility

Each project README contains its own setup and execution instructions. Projects use small or synthetic datasets when the original data, hardware, or external service is impractical; those deviations are documented explicitly.

## Video

YouTube walkthrough: _To be added after recording._
## Integration status

All 14 projects have a real README, runnable entry point, test or validation command, documented prompt alignment, results/artifacts, and explicit deviations. The final local verification is summarized in [REPRODUCTION_LOG.md](REPRODUCTION_LOG.md): all 14 project checks passed, with Project 11 intentionally returning a CONDITIONAL release recommendation because its fixture contains four governance defects.

The portfolio is intentionally offline-friendly. Synthetic or built-in datasets replace external Kaggle/TLC downloads where needed, AutoGluon and PyTorch remain optional, and hosted dashboards/browser tours are not claimed unless present in the project README.
