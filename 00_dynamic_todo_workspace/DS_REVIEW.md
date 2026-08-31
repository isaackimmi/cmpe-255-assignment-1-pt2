# Project 00 data-science robustness review

Date: 2026-08-31
Scope: `/Users/isaackim/Desktop/MSSE DS/Fall 2026/CMPE 255/HW/cmpe-255-assignment-1-pt2/00_dynamic_todo_workspace`
Review type: source and artifact review after final polish changes.

## Overall assessment

This is a polished local-first CRISP-DM planning demo, not a reproducible retail-demand forecasting or agent-evaluation artifact. The UI now states that the dataset is not connected, data quality is not measured, and the workflow is an example plan. The agent action is explicitly simulated and records only a local activity event.

The task queue is functional: tasks can be added, filtered, searched, completed, removed, normalized on load, and persisted when browser storage is available. Workflow stages can be selected to inspect the expected next evidence, but stage completion remains illustrative and is not derived from task completion. Dataset readiness is presented as a checklist of unmeasured/planned states rather than fabricated quality metrics.

## Findings and disposition

### [RESOLVED] Stale measured-looking claims in the current project documentation

`index.html`, `README.md`, and this review now agree on the planning-only boundary. The source contains no claims such as row counts, quality percentages, agent confidence, time saved, or model metrics. The contract tests protect the most important labels and reject the superseded values.

The superseded project screenshot was removed from the assignment evidence set because it showed the old measured-looking UI. A fresh screenshot should be captured only from the current source in a permitted visual QA environment.

### [RESOLVED] Planning-only value proposition is explicit

The page heading, dataset card, workflow panel, help view, agent-runs view, and README all explain that there is no connected dataset, model, run artifact, or evaluation. “Simulate agent check” now has a status view explaining exactly what it does and does not do.

### [RESOLVED] Workflow and data-readiness interactions are meaningful but honest

The workflow summary is derived from `workflowStages`, and selecting a stage shows its expected evidence status. Its copy uses “drafted” and “example plan” rather than presenting the 50% value as live project progress. The dataset card opens readiness checks for connection, schema profile, time coverage, and leakage checks; all remain planned/unmeasured until artifacts exist.

### [RESOLVED] Dashboard shell affordances are no longer silent

Agent runs, datasets, notifications, and help now open lightweight status views. Non-selected projects are rendered as example labels rather than inactive buttons. The selected overview navigation state is data-driven.

### [RESOLVED] Accessibility/state polish

The add-task control owns and synchronizes `aria-expanded`/`aria-controls`, filter controls expose `aria-pressed`, and the search field has an accessible name. Closing the add form after submission or Escape uses the same state helper.

### [OPEN, INTENTIONAL LIMITATION] No forecasting pipeline or run artifact

This checkout still has no input data, schema/profile payload, feature pipeline, chronological split, leakage assertion, model artifact, forecast, or evaluation report. That is consistent with the narrowed planning-demo scope. It must be resolved before presenting the project as a working forecasting or agent-evaluation product.

## Checks run

- `npm test`: passed; state/workflow tests and UI contract tests passed.
- `node --check src/state.js`: passed.
- `node --check src/app.js`: passed.
- `git diff --check`: passed.
- Static inspection confirmed that no superseded measured-looking labels remain in the current HTML.

## Final decision

Ship as a “local-first CRISP-DM planning demo.” Do not describe it as a working demand-forecasting or agent-evaluation workspace until real data/run artifacts and time-aware evaluation are added.
