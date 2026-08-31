# Project 00 data-science robustness review

Date: 2026-08-30  
Scope: `/Users/isaackim/Desktop/MSSE DS/Fall 2026/CMPE 255/HW/cmpe-255-assignment-1-pt2/00_dynamic_todo_workspace`  
Review type: read-only robustness review; source code was not modified.

## Overall assessment

This is a polished local task-planning/demo UI, not a reproducible retail-demand forecasting or agent-evaluation artifact. The task helpers are small and readable, and the documented Node tests pass, but the UI presents several hard-coded data, quality, confidence, progress, and agent-result claims without corresponding data or computation. Leakage prevention, time-aware validation, model metrics, and forecast reproducibility therefore cannot be established from this checkout.

The README does describe seeded example tasks and an intentionally dependency-free local-first design (`README.md:17-37`), so mock content may be intentional. It should nevertheless be labeled as mock/demo content wherever it resembles a measured result.

## Findings

### [HIGH] Measured-looking dataset and agent claims are not backed by artifacts or computation

Evidence:

- The UI claims `2.4M rows`, `38 columns`, a Jan 2021–Dec 2024 range, and `Data quality 94%` (`index.html:35`). No dataset, schema, profiling output, or quality report is present in the project artifact inventory.
- It also claims `Agent confidence 87%`, `Based on 6 checks`, `4.5h` saved, and week-over-week percentage changes (`index.html:38`). These values are static markup and are never updated by `src/app.js`.
- The activity feed contains hard-coded findings such as “Seasonality signal is strong in 84% of stores” and “12 missing promotion values” (`src/app.js:7-10`). “Run agent check” only waits 700 ms and appends “No blocking issues found” (`src/app.js:35`); it does not inspect data, tasks, or a model.

Risk: A reviewer or stakeholder can reasonably interpret these as measured results from `retail_orders.parquet`, although the checkout contains no corresponding data or analysis. This undermines trust and makes the apparent DS conclusions non-auditable.

Recommended fix: Either label all seeded values as “demo/mock” and rename the button to indicate simulation, or connect the UI to a versioned data/profile/run artifact. Store provenance (dataset URI/hash, run timestamp, checks performed, and result payload) and test that displayed values are derived from that payload.

### [HIGH] No forecasting, leakage check, validation, or evaluation artifact exists

Evidence:

- The repository contains UI/state code, CSS, tests, and an SVG evidence card, but no `.parquet`/`.csv` data snapshot, notebook, model, feature pipeline, split definition, metric output, or evaluation report. The only likely data/model filename match is `package.json`.
- The stated forecast is “next 12 weeks of demand” (`index.html:34`), while the only modeling-related implementation is a seeded task to “Compare seasonal naive baseline” (`src/state.js:2-4`). The CRISP-DM panel is static presentation (`index.html:42`), not an executable workflow.

Risk: It is impossible to verify that features are constructed using information available at prediction time, that future observations are excluded from training, or that the model generalizes across forecast horizons/stores. The absence of an implementation is not evidence of leakage safety.

Recommended fix: Add an executable, versioned pipeline with an explicit chronological train/validation/test cutoff (and a documented gap when rolling/lag features require it), feature-time assertions, a seasonal-naive baseline, model artifacts, and per-horizon/per-store metrics with clear aggregation. Until then, the UI should state that modeling and evaluation are planned rather than complete.

### [MEDIUM] Workflow progress is internally inconsistent and disconnected from state

Evidence:

- The panel displays `68%` and “4 of 6 stages complete” (`index.html:42`), but only Business understanding, Data understanding, and Data preparation have the `complete` class; Modeling is `current`, and Evaluation/Deployment are incomplete (`index.html:42`). Thus the visible completed count is 3/6, while 4/6 could at most mean “through the current stage”; 4/6 is also 66.7%, not 68%.
- No task action or agent action updates the stage list or progress value; the values are static HTML/CSS (`index.html:42`, `refinements.css:22-23`).

Risk: Users cannot rely on the workflow summary to represent actual project state, and the discrepancy is visible even before considering the missing model artifacts.

Recommended fix: Define one source of truth for stage status, derive percentage from it, distinguish “completed” from “current/in progress,” and add a regression test for the displayed count and percentage. Mark the panel as illustrative if it remains static.

### [MEDIUM] Persisted task state is accepted without schema validation or invariant enforcement

Evidence:

- `loadTasks()` accepts any JSON array from local storage without validating item shape, status, priority, or ID uniqueness (`src/app.js:14`). A corrupted item can reach rendering and filtering.
- `visibleTasks()` assumes `task.title` and `task.meta` are strings (`src/state.js:8-10`); for a missing `meta`, a non-matching search throws `TypeError: Cannot read properties of undefined (reading 'toLowerCase')` in the executed edge probe.
- `addTask()` trims the title but the pure helper still accepts a blank title when called directly (`src/state.js:21-24`). `toggleTask()` uses strict ID equality (`src/state.js:17-19`), so a stored string ID does not toggle when the DOM supplies a number; duplicate IDs toggle multiple rows.

Risk: Manual local-storage edits, older state formats, or partial writes can make search or rendering fail, while inconsistent IDs/statuses can silently produce incorrect task updates and counts.

Recommended fix: Validate and normalize storage on load; migrate or discard invalid records; use one canonical ID type and enforce uniqueness; validate title/priority/status in the helper boundary; and add tests for malformed records, string IDs, duplicates, blank titles, and unknown statuses.

### [MEDIUM] Reproducibility and audit history are weak for a stateful local demo

Evidence:

- Seeded task metadata and activity timestamps are fixed strings (`src/state.js:1-6`, `src/app.js:7-10`), while newly logged timestamps depend on the machine locale/time zone (`src/app.js:27`).
- Activities are held only in memory and are reset on reload (`src/app.js:7`, `src/app.js:26-27`); only tasks are written to local storage (`src/app.js:14-15`). The agent check has no run ID, inputs, output artifact, or deterministic result (`src/app.js:35`).
- The README describes local storage as available only when the browser permits it (`README.md:15`), but the UI always says “changes are saved automatically” (`index.html:45`).

Risk: A second user or evaluator cannot reconstruct what was checked, with which data, or why a displayed activity occurred. A storage failure can also look like a successful save.

Recommended fix: Persist versioned run/activity records with UTC timestamps, run IDs, input hashes, and result summaries; inject a clock for deterministic tests; and surface storage availability/save failures in the UI. Keep the wording conditional (“saved locally when available”) unless persistence is confirmed.

### [LOW] Green test status covers only four pure helper examples, not the user-visible contract

Evidence:

- `README.md:27-33` and `README.md:49-50` report the Node suite as `4/4` passed. `tests/state.test.js:6-9` covers only counts, basic filtering, one toggle, and one add case.
- There are no tests for `loadTasks()`/`save()`, DOM rendering, the add/delete/filter interactions, the agent-check lifecycle, malformed storage, the displayed progress metrics, or the hard-coded-vs-derived UI claims.

Risk: The passing suite is accurate but can give disproportionate confidence in a UI whose important behavior and DS-facing claims are untested.

Recommended fix: Add browser-level smoke tests for the critical interactions and contract tests for storage normalization and displayed summaries. Keep the current unit tests, but describe them as helper-only coverage.

## Checks run

- `npm test`: passed, 4 tests / 4 passed.
- `node --check src/state.js`: passed.
- `node --check src/app.js`: passed.
- `git diff --check`: passed before this report was added.
- Static inventory/search confirmed no data/model/evaluation artifact matching the project’s forecast claims. A local HTTP-server smoke test could not be completed in the managed environment because binding to the test port was restricted; this does not affect the Node results.

## Suggested priority order

1. Correct or explicitly label the unbacked UI claims and inconsistent workflow progress.
2. If forecasting is in scope, add the data/feature/split/model/evaluation pipeline with time-aware leakage tests and reproducible run artifacts.
3. Harden and test persisted task-state validation before treating local storage as reliable.
4. Add browser/integration coverage for the user-visible behavior.
