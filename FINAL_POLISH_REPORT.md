# Final polish report

Date: 2026-08-31  
Scope: Projects 00–13 on `assignment-1-part-2-reproduction`

## Review method

Each project received a final static review focused on whether the data-science claims were supported by the code and checked-in artifacts. A separate implementation pass addressed the highest-value findings. The UI review was performed sequentially with one local static server and one browser page at a time; no concurrent localhost servers were used.

## Portfolio-level outcomes

- Evaluation boundaries and denominators were made explicit in the predictive projects.
- Baselines, fold-level variation, operating points, residuals, error slices, and uncertainty were surfaced where they materially improve interpretation.
- Artifact manifests and run evidence now connect browser views to reproducible outputs rather than invented page-only numbers.
- Synthetic, illustrative, optional-backend, and planning-only boundaries are labeled where applicable.
- Dashboards gained functional filters, threshold controls, sorting, point/row detail, or evidence panels appropriate to each project.
- All 14 project test suites passed in the final verification pass. Optional PyTorch branches remain skipped when PyTorch is unavailable.
- JavaScript syntax checks and `git diff --check` passed.

## Project checklist

| Project | Final analytical/UI focus |
|---|---|
| 00 | Honest planning-only evidence, dataset readiness, workflow-stage detail, accessible task controls |
| 01 | Complete eligible holdout scoring, strict timestamp/data contracts, artifact-backed residual and slice exploration |
| 02 | Three-way split behavior, OOV/probability evidence, deterministic generation traces, backend/config disclosure |
| 03 | Feature-quality audit, deterministic clustering artifacts, point-level feature/PCA explorer |
| 04 | Rule-driven basket exploration with support, confidence, count, and itemset-size controls |
| 05 | Artifact-backed skill evidence, baselines, sample sizes, confusion matrices, and chart/table exploration |
| 06 | Saved score observations, threshold/operating-point explorer, detector comparison and diagnostics |
| 07 | Holdout-safe metrics, fold uncertainty, practical tie semantics, backend status, leaderboard controls |
| 08 | Visible reverse-gradient branches, learning-rate behavior, cost/threshold endpoints, numerical checks |
| 09 | Successful/failed run manifests, lineage, quality-gate state, and artifact-backed DAG explorer |
| 10 | Reproducible CRISP-DM/model bundle evidence, schema/fingerprint contract, inference safeguards |
| 11 | Finding-level severity/category/status drill-down, structured release decision evidence |
| 12 | CSV-backed forecast/error explorer, baseline comparison, horizon/provenance semantics |
| 13 | Explicit synthetic framing, run identity, holdout/error/slice evidence, row-level audit and inference contract |

The individual `FINAL_POLISH_REVIEW.md` files are the detailed audit trail for each row.
