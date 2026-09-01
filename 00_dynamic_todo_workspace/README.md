# Project 00 — Dynamic Todo Workspace

A lightweight runnable workspace for planning data-science-agent work. It combines a project queue, illustrative dataset readiness context, task filtering, example CRISP-DM stages, and a small demo activity log in one local-first web app. It is intentionally a planning demo, not a forecasting engine.

## Run locally

The polished version is a real E2E split application: `client/` is a Vite-compatible raw HTML/CSS/JavaScript client, and `server/` is a FastAPI service. The legacy root `index.html` remains as a static fallback for GitHub Pages.

Terminal 1 — API:

```bash
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Terminal 2 — Vite client:

```bash
cd client
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. `client/vite.config.js` proxies `/api` to `http://127.0.0.1:8000`; set `VITE_API_BASE_URL` before `npm run dev` when using a different API origin. The client calls `/api/workspace`, `/api/readiness`, and the task mutation endpoints. Run the API and client separately; do not use multiple project servers simultaneously during the portfolio demo.

No package installation is required. From this directory, start any static server:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

The original root app also works by opening `index.html` directly, although it does not exercise the FastAPI API.

## Features

- Add, complete, and delete tasks through FastAPI-backed CRUD endpoints.
- Filter the queue by status, priority, and search text.
- Keep a selected workspace brief visible while tasks are edited.
- View dataset readiness checks, example workflow stages, and demo activity.
- Select workflow stages to inspect the evidence expected next.
- Open lightweight status/help views from the dashboard shell without implying connected runs or datasets.
- Seeded example tasks demonstrate a typical CRISP-DM/data-science-agent loop.
- Responsive layout for desktop and narrow screens.
- Polished dashboard presentation with CRISP-DM stage progress, readiness evidence, API loading/error states, accessible controls, and Vite dev-server compatibility.

## Tests

The pure task/state helpers, workflow summary, and HTML honesty/accessibility contract are covered with Node's built-in test runner:

```bash
node --test tests/*.test.js
```

The FastAPI route and Vite configuration contract is checked without starting a server:

```bash
python3 -m unittest discover -s tests -p 'test_server_contract.py' -v
```

These contract checks use the standard library. If the FastAPI dependencies are installed, the same file additionally exercises valid task creation, validation failures, and unknown-ID 404 responses through FastAPI's test client.

## Demo-data boundary

This checkout does not contain `retail_orders.parquet`, a profiling report, forecasting code, model output, or evaluation artifacts. The dataset card and workflow therefore describe planned/example work. The agent-check button only records a simulated queue check in the local activity log. No displayed quality score, confidence percentage, time-saved estimate, forecast, leakage check, or model metric is a measured result.

Tasks and the activity log are stored in browser local storage when available. Stored tasks are validated on load: safe numeric-string IDs are migrated to numbers, duplicate or malformed records are discarded, and missing metadata is normalized safely. The footer reports when browser storage is unavailable.

The FastAPI demo server keeps state in memory for the session. It is intentionally not a forecasting engine and does not claim a measured dataset profile, model score, or time saving.

## Documented deviations

The original Project 00 prompt referenced by the assignment was not available in this checkout. The E2E implementation intentionally uses raw HTML/CSS/JavaScript rather than React and uses an in-memory FastAPI service rather than a database or authentication system. A production version could add persistence, multi-user sync, and auth.

## Files

- `index.html` — application shell and accessible controls.
- `styles.css` — visual system and responsive layout.
- `src/state.js` — pure state helpers used by the app and tests.
- `src/app.js` — DOM rendering and interaction logic.
- `tests/state.test.js` — executable state/model tests.
- `tests/contract.test.js` — checks the honest demo boundary and key accessible controls.
- `client/` — Vite-compatible browser client.
- `server/` — FastAPI API and in-memory session state.
- `tests/test_server_contract.py` — dependency-light API contract checks.
- `screenshots/` — optional visual evidence generated during local QA.
## Integration verification

- **Prompt alignment:** Public Project 00 asks for a modern dynamic todo application; this covers local task queue, filtering, persistence, responsive UI, and seeded workspace context.
- **Results/artifacts:** `index.html`, `styles.css`, and `src/` are the visual artifact; Node tests cover state/workflow behavior plus the honest UI contract.
- **Issue/resolution:** The E2E client/server is intentionally local-first and session-scoped; it omits authentication, multi-user sync, and database persistence.
