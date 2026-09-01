# CMPE 255 Assignment 1 — Part 2

This repository documents my reproduction of the data-science projects from the instructor's reference repository using an agentic coding assistant.

Reference: [dlmastery/data_science_examples](https://github.com/dlmastery/data_science_examples)

## Projects

Each numbered directory contains an independent reproduction, its own README, runnable code, tests, and generated artifacts where practical.

## UI layer

Every project includes a browser-facing UI in addition to its data-science experiment. Projects 0–5 also provide a professor-style end-to-end layout: a Vite client calls a FastAPI server, and Projects 1–5 expose a small `ml/` adapter where model/evaluation logic belongs. Project 00 is intentionally planning-only and therefore has no `ml/` directory. Projects 6–14 remain unchanged.

For the polished E2E demos, follow each project README and run only one project at a time. The common pattern is:

```bash
cd <project>
python3 -m uvicorn <server module>:app --host 127.0.0.1 --port <port>
# in a second terminal
cd client && npm install && npm run dev
```

The exact modules/ports are documented per project (00: 8000/5173, 01: 8001/5173, 02: 8002/5175, 03: 8003/5173, 04: 8004/5173, 05: 8005/5175). The client proxies `/api` to the local server, and the API reads checked-in artifacts or deterministic fixtures. A root static server is still available for the original artifact galleries:

### First-six demo runbook

Run one project at a time. In one terminal, start the server from the project directory; in a second terminal, start its React client from the project’s `client/` directory. Open the printed Vite URL in a browser.

| Project | Server command | Client command |
| --- | --- | --- |
| 00 Dynamic Todo | `python3 -m uvicorn main:app --reload --port 8000` | `cd client && npm ci && npm run dev` |
| 01 NYC Taxi | `python3 -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8001` | `cd client && npm install && npm run dev` |
| 02 Nano LLM | `cd server && python3 -m uvicorn main:app --host 127.0.0.1 --port 8002` | `cd client && npm install && npm run dev -- --port 5175` |
| 03 Customer Segmentation | `python3 -m uvicorn server.app:app --reload --port 8003` | `cd client && npm install && npm run dev` |
| 04 Pattern Mining | `python3 -m uvicorn server.main:app --reload --port 8004` | `cd client && npm install && npm run dev` |
| 05 Skills Lab | `python3 -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8005` | `cd client && npm install && npm run dev -- --port 5175` |

Each project README contains the same instructions with project-specific prerequisites and API details. A ready-to-read narration for the six screenshots is in [DEMO_SCRIPTS_00_05.md](DEMO_SCRIPTS_00_05.md).

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

Each UI includes metric cards, visualizations or artifact previews, explanatory CRISP-DM context, responsive styling, and project-specific analytical controls. Where the browser is reading checked-in artifacts rather than running Python, that boundary is labeled explicitly.

Rendered UI screenshots are stored in [`ui_screenshots/`](ui_screenshots/). `e2e-project-00.png` through `e2e-project-05.png` are the fresh sequential Vite/FastAPI smoke-test captures; the older `project-00.png` through `project-13.png` gallery captures remain for the full portfolio.

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

## Data-science robustness review

Each project includes a reviewer-authored [`DS_REVIEW.md`](00_dynamic_todo_workspace/DS_REVIEW.md) with evidence-backed findings. The review pass was implemented on this same branch: leakage boundaries, held-out evaluation, input validation, reproducibility metadata, artifact contracts, and dashboard claims were strengthened where applicable. Review reports remain alongside each project so the reasoning and limitations are auditable.

## Final polish

The final polish pass added a second review record, [`FINAL_POLISH_REPORT.md`](FINAL_POLISH_REPORT.md), for all 14 projects. It prioritized data-science integrity—evaluation populations, baselines, leakage boundaries, uncertainty, provenance, and artifact contracts—before improving the dashboards. The resulting UIs are exploratory evidence viewers, not static marketing pages.

## Reproducibility

Each project README contains its own setup and execution instructions. Projects use small or synthetic datasets when the original data, hardware, or external service is impractical; those deviations are documented explicitly.

## E2E verification

Projects 0–5 were started one at a time locally, with API-connected browser checks and a meaningful UI interaction per project. The checks exercised task mutation (00), a repaired rush-hour slice (01), generation/probability traces (02), point inspection (03), rule sorting (04), and server-side row filtering (05). The live screenshots and per-project reviewer reports provide the submission/demo evidence.

## Frontend and service architecture

Projects 0–5 use React entrypoints mounted by Vite. Each client keeps reusable UI under `client/src/components/`, transport and server state under `client/src/api`, `client/src/services`, or `client/src/hooks`, and project styling/theme concerns in dedicated files. Radix UI is used where appropriate for lightweight primitives; MUI is used where appropriate for richer controls and feedback. The Python side follows the same separation: FastAPI routers/schemas/services form the server boundary, while `ml/` contains focused artifact, preprocessing, scoring, and domain modules behind compatibility facades where needed. Each project includes a `FINAL_FE_REVIEW.md` documenting the independent composability/accessibility review and applied fixes.

## Video

YouTube walkthrough: _To be added after recording._
## Integration status

All 14 projects have a real README, runnable entry point, test or validation command, documented prompt alignment, results/artifacts, and explicit deviations. The final local verification is summarized in [REPRODUCTION_LOG.md](REPRODUCTION_LOG.md): all 14 project checks passed, with Project 11 intentionally returning a CONDITIONAL release recommendation because its fixture contains four governance defects.

The portfolio is intentionally offline-friendly. Synthetic or built-in datasets replace external Kaggle/TLC downloads where needed, AutoGluon and PyTorch remain optional, and hosted dashboards/browser tours are not claimed unless present in the project README.
