# Final polish review — Project 00

Date: 2026-08-30  
Scope: `/Users/isaackim/Desktop/MSSE DS/Fall 2026/CMPE 255/HW/cmpe-255-assignment-1-pt2/00_dynamic_todo_workspace`  
Method: Static source and artifact inspection only; implementation files were not modified.

## Verdict

This is an honest and visually polished local-first task-planning workspace. The current UI clearly says `Demo plan`, `Not connected`, `planned`, `illustrative`, and `Not measured` (`index.html:34-38`), and the README explicitly disclaims any real dataset, forecast, model, metric, leakage check, or evaluation artifact (`README.md:35-39`). That is a meaningful improvement over a dashboard that presents fabricated analytics as measured results.

It is useful as a lightweight CRISP-DM work queue and planning surface, but not yet as a substantive data-science workspace: there is no input dataset, schema/profile payload, feature pipeline, forecast, validation split, model artifact, or evaluation report (`README.md:37`; project artifact inventory). The queue interactions are real (`src/app.js:150-187`), but the surrounding navigation, workflow, and agent-run surfaces are mostly presentation. The result feels like an interactive todo demo embedded in a static dashboard shell rather than an end-to-end DS workspace.

Recommendation: conditional pass for a local planning/demo deliverable. Before presenting it as a forecasting or data-science-agent product, resolve the stale evidence, make the interactive boundary explicit, and either connect the workflow to real run artifacts or narrow the product language to planning.

## Prioritized findings

### P0 — Remove or update stale evidence that contradicts the current honest UI

Evidence:

- The current `index.html` labels the dataset as not connected and data quality as not measured (`index.html:35`), while `DS_REVIEW.md` still says the UI claims `2.4M rows`, `38 columns`, `94%` quality, `87%` confidence, and `4.5h` saved (`DS_REVIEW.md:15-25`). Those statements no longer describe the current source.
- The bundled screenshot `../ui_screenshots/project-00.png` visibly contains the superseded measured-looking claims and labels such as “ON TRACK,” “2.4M rows,” “94%,” “Agent confidence,” and “4.5h.”
- The existing review also reports four tests and old line locations (`DS_REVIEW.md:73-90`), whereas the current test file contains 11 cases (`tests/state.test.js:1-42`) and the README reports 11 state/workflow cases (`README.md:53-57`).

Impact: A grader or stakeholder may judge the project from the stale screenshot or review and conclude that it still makes unsupported analytics claims. This is the largest final-submission risk because the source has already moved toward a more trustworthy presentation.

Action: Replace `DS_REVIEW.md` with a current review or mark it superseded, and regenerate or remove `../ui_screenshots/project-00.png`. Ensure the delivered screenshot, README, review, and live HTML all describe the same demo-data boundary.

### P1 — Make the data-science value proposition either real or explicitly planning-only

Evidence:

- The project brief promises a 12-week demand forecast (`index.html:34`), but the README states that no dataset, profiling report, forecasting code, model output, or evaluation artifact exists (`README.md:35-37`).
- The only workflow content is a frozen six-stage demo plan (`src/state.js:11-20`), and the only “agent” action disables a button for 700 ms and appends explanatory demo activity; it does not inspect data, execute checks, or produce a run artifact (`src/app.js:174-183`).
- The seeded tasks are planning prompts, including “Compare seasonal naive baseline,” rather than results (`src/state.js:4-8`).

Impact: The app is honest, but a user cannot use it to answer a DS question or audit a forecast. “Simulate agent check” provides motion and activity history without analytical utility.

Action: Choose one clear product boundary. For a planning-only deliverable, rename the page/subtitle and agent action around “forecasting plan” and “demo checklist,” and add a visible “next artifact” or “connect dataset” state. For a substantive DS workspace, add a versioned local run payload containing schema/profile results, chronological split definitions, leakage checks, baseline/model metrics, and provenance; render those values from the payload rather than from markup.

### P1 — Connect workflow progress to state, or make it clearly non-interactive

Evidence:

- `workflowStages` is deliberately separate from task state (`src/state.js:11-20`), and `renderWorkflow()` renders that fixed array (`src/app.js:121-129`). It is called at startup only (`src/app.js:188-190`).
- Task completion updates counts and activity, but no task or agent handler updates a workflow stage (`src/app.js:162-182`).
- The workflow panel is labeled “Illustrative” (`index.html:42`), which is honest but confirms that its 50% progress is not project progress.

Impact: The queue can change while the workflow summary remains unchanged. That weakens the core workspace promise: users cannot tell whether completing a task advances the plan.

Action: Either (a) persist stage state and provide an explicit stage interaction, (b) derive stage status from structured task metadata and document the mapping, or (c) keep it as a static “example CRISP-DM plan” and visually de-emphasize progress language such as percent complete.

### P1 — Implement or de-emphasize the nonfunctional dashboard shell

Evidence:

- `Overview`, `Agent runs`, and `Datasets` are buttons in the sidebar, and three project names are also buttons (`index.html:15-24`), but `src/app.js:150-187` attaches no handlers to them.
- Notifications, Help, and the three project links have no state change or destination (`index.html:30`, `src/app.js:150-187`).
- The “Agent runs 3” count is static markup (`index.html:17`) and is not derived from the activity/run state.

Impact: The visual language implies multiple navigable workspaces and run history, but most of those affordances do nothing. This is the main reason the app can feel like a landing page despite the functioning task queue.

Action: Add minimal views or dialogs for datasets, agent runs, help, and project selection; or convert these controls into clearly non-interactive labels and remove static counts. At minimum, make the selected project and active navigation state data-driven.

### P2 — Close the small accessibility/state-polish gaps

Evidence:

- The add-task button gets `aria-expanded` on open/close (`src/app.js:150-151`), but successful submission hides the form without resetting that attribute (`src/app.js:152`). The control can therefore advertise an expanded form that is no longer visible.
- Filter buttons use a CSS `active` class only (`index.html:41`, `src/app.js:115`); they do not expose a pressed/selected state with `aria-pressed` or equivalent.
- The search input is wrapped in a label containing only the glyph `⌕` and has a placeholder but no explicit text label (`index.html:41`).

Impact: Keyboard and assistive-technology users receive less reliable state information than sighted mouse users, and the UI polish is inconsistent at the exact points where state changes.

Action: Add `aria-controls` and keep `aria-expanded` synchronized on every close path, add `aria-pressed` to filters, and give the search field an explicit accessible name such as “Search tasks.” Preserve focus after task-list rerenders where practical.

### P2 — Expand tests from pure helpers to the user-visible contract

Evidence:

- The current tests cover state helpers and workflow summary (`tests/state.test.js:1-42`), and the README accurately describes them as pure task/state coverage (`README.md:27-33`).
- There are no tests for DOM rendering, navigation affordances, add-form visibility, storage failure messaging, activity persistence, agent simulation lifecycle, or the correspondence between displayed labels and demo-data status.

Impact: The strongest claims about interactivity and honesty are not protected against regressions.

Action: Add a small browser-level smoke suite for add/filter/search/complete/reload and a contract check that rejects measured-looking dataset/model labels when no run payload is connected. Keep the existing unit tests as the fast foundation.

## What is already strong

- The demo boundary is now explicit in both the UI and README (`index.html:34-38`; `README.md:35-39`).
- Task state is normalized and deduplicated at the pure-helper layer (`src/state.js:29-63`), and the current suite covers malformed records, IDs, priorities, and workflow math (`tests/state.test.js:10-42`).
- The main queue has a coherent interaction model: task creation, status filters, search, completion/removal, activity logging, keyboard shortcuts, and local persistence hooks (`src/app.js:150-187`).
- The visual system is consistent and responsive, with focus-visible and reduced-motion treatments (`refinements.css:1-28`).

## Final decision

Ship only as a “local-first CRISP-DM planning demo” after synchronizing the stale review/screenshot artifacts. Do not describe it as a working demand-forecasting or agent-evaluation workspace until real data/run artifacts exist. The highest-return polish is to make the dashboard shell honest about what is clickable and to connect—or deliberately detach—the workflow progress from task state.
