# CMPE 255 Assignment 1 — Part 2

This repository documents my reproduction of the data-science projects from the instructor's reference repository using an agentic coding assistant.

Reference: [dlmastery/data_science_examples](https://github.com/dlmastery/data_science_examples)

## Projects

Each numbered directory contains an independent reproduction, its own README, runnable code, tests, and generated artifacts where practical.

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
