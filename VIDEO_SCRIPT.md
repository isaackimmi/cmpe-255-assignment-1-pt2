# Assignment 1 Part 2 — Video Script

## 0:00–0:30 — Portfolio overview

Open the root README and show that Projects 00–13 are independent, offline-friendly reproductions. Point out PROMPTS_USED.md, REPRODUCTION_LOG.md, and COMPARISON_REPORT.md as the evidence trail.

Start the repository static server and open the dashboard pages one at a time. Show Projects 01, 03, 04, 06, 07, 08, 12, and 13, then briefly open the remaining UIs so every project has visual evidence. Demonstrate metric cards, artifact-backed charts, phase navigation, threshold/sort/filter controls, and a row- or point-level detail view.

## 0:30–1:20 — Applications and workflow

Open Project 00 and show the task/workspace UI. Run its Node tests. Then show Project 01's metrics.json and SVG outputs: the deterministic NYC-like fallback uses a chronological split and the log-target model improves over the median baseline.

## 1:20–2:10 — Modeling examples

Show Project 03's segmentation explorer and summary JSON, Project 04's rule/threshold explorer, and Project 06's anomaly score and operating-point views. Explain that synthetic data are intentionally labeled as teaching fixtures and metrics are not production claims.

## 2:10–2:55 — Skills and education

Show Project 05's metrics/plots and Project 08's visual lab. Demonstrate a chart focus/metric control, the threshold/learning-rate explorer, or a lesson quiz, then mention that numerical tests cover the same concepts.

## 2:55–3:40 — Pipelines, CRISP-DM, and audits

Run the Project 09 pipeline and show its deterministic execution order. Open Project 10's CRISP-DM JSON, Project 11's audit report with four intentional failures, and Project 12's forecast plot showing why the seasonal-naive baseline remains important.

## 3:40–4:30 — Capstone and verification

Run Project 13, call its inference CLI, and open metrics.json, audit_report.json, and the two PNGs. State the result: MAE 2.794 minutes, R² 0.892, and 4/4 tests. Close with the remaining blockers: no external Kaggle/TLC download, no AutoGluon install, and no hosted production dashboards.
