# Project 00 — Dynamic Todo Workspace

A lightweight runnable workspace for planning data-science-agent work. It combines a project queue, illustrative dataset readiness context, task filtering, example CRISP-DM stages, and a small demo activity log in one local-first web app. It is intentionally a planning demo, not a forecasting engine.

## Run locally

No package installation is required. From this directory, start any static server:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

The app also works by opening `index.html` directly, although some browsers restrict local storage for `file://` pages. Tasks are saved in the browser's local storage when available.

## Features

- Add, complete, and delete tasks.
- Filter the queue by status, priority, and search text.
- Keep a selected workspace brief visible while tasks are edited.
- View dataset readiness checks, example workflow stages, and demo activity.
- Select workflow stages to inspect the evidence expected next.
- Open lightweight status/help views from the dashboard shell without implying connected runs or datasets.
- Seeded example tasks demonstrate a typical CRISP-DM/data-science-agent loop.
- Responsive layout for desktop and narrow screens.
- Polished dashboard presentation with CRISP-DM stage progress, accessible focus states, reduced-motion support, and local static-server compatibility.

## Tests

The pure task/state helpers, workflow summary, and HTML honesty/accessibility contract are covered with Node's built-in test runner:

```bash
node --test tests/*.test.js
```

## Demo-data boundary

This checkout does not contain `retail_orders.parquet`, a profiling report, forecasting code, model output, or evaluation artifacts. The dataset card and workflow therefore describe planned/example work. The agent-check button only records a simulated queue check in the local activity log. No displayed quality score, confidence percentage, time-saved estimate, forecast, leakage check, or model metric is a measured result.

Tasks and the activity log are stored in browser local storage when available. Stored tasks are validated on load: safe numeric-string IDs are migrated to numbers, duplicate or malformed records are discarded, and missing metadata is normalized safely. The footer reports when browser storage is unavailable.

## Documented deviations

The original Project 00 prompt referenced by the assignment was not available in this checkout. Based on the assignment brief, this implementation intentionally uses a dependency-free vanilla HTML/CSS/JavaScript stack rather than a full backend or framework. It does not provide authentication, multi-user sync, a database, drag-and-drop ordering, or a deployed URL. Those are reasonable next steps if the reference prompt requires production persistence or collaboration.

## Files

- `index.html` — application shell and accessible controls.
- `styles.css` — visual system and responsive layout.
- `src/state.js` — pure state helpers used by the app and tests.
- `src/app.js` — DOM rendering and interaction logic.
- `tests/state.test.js` — executable state/model tests.
- `tests/contract.test.js` — checks the honest demo boundary and key accessible controls.
- `screenshots/` — optional visual evidence generated during local QA.
## Integration verification

- **Prompt alignment:** Public Project 00 asks for a modern dynamic todo application; this covers local task queue, filtering, persistence, responsive UI, and seeded workspace context.
- **Results/artifacts:** `index.html`, `styles.css`, and `src/` are the visual artifact; Node tests cover state/workflow behavior plus the honest UI contract.
- **Issue/resolution:** Dependency-free local-first design intentionally omits authentication, multi-user sync, and deployment.
