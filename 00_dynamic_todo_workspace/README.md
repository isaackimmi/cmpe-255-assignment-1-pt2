# Project 00 — Dynamic Todo Workspace

A lightweight runnable workspace for planning data-science-agent work. It combines a project queue, illustrative dataset readiness context, task filtering, example CRISP-DM stages, and a small demo activity log in one local-first web app. It is intentionally a planning demo, not a forecasting engine.

## Run locally

The polished version is a real E2E split application: `client/` is a React 19 application built by Vite, Radix UI supplies accessible interaction primitives, and `server/` is a layered FastAPI service. The legacy root `index.html` remains a separate static fallback for GitHub Pages.

For a demo, one command handles dependencies, starts both processes, opens <http://127.0.0.1:5173>, and stops everything with one `Ctrl-C`:

```bash
./run_demo.sh
```

The commands below are the equivalent manual development workflow.

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
npm ci
npm run dev
```

Open <http://127.0.0.1:5173>. `client/vite.config.js` proxies `/api` to `http://127.0.0.1:8000`; set `VITE_API_BASE_URL` before `npm run dev` when using a different API origin. The client loads `/api/workspace`, uses the task mutation endpoints, and refreshes the workspace after a demo agent check. `/api/readiness` remains available as an independently typed API resource. Run the API and client separately; do not use multiple project servers simultaneously during the portfolio demo.

### Legacy static fallback

The legacy root app is dependency-free and does not exercise FastAPI. From this project directory, start any static server:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

The root app also works by opening `index.html` directly. Its local-storage behavior and Node tests apply only to this fallback—not to the React/FastAPI application.

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

The React client is covered by Vitest, React Testing Library, and user-event. Tests render the real component tree and cover loading/error states, filtering, workflow accessibility, mutation failures, overlapping-write protection, and agent-check refresh:

```bash
cd client
npm ci
npm run test:client
npm run build
```

Use `npm run check` after dependencies are installed to run the React tests and production build together.

The legacy fallback's pure task/state helpers and HTML honesty contract remain covered separately with Node's built-in test runner:

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

The legacy fallback stores tasks and activity in browser local storage when available. Its stored tasks are validated on load: safe numeric-string IDs are migrated to numbers, duplicate or malformed records are discarded, and missing metadata is normalized safely.

The React E2E client does not use browser persistence; it reads and mutates the FastAPI service. The server keeps state in a thread-safe in-memory repository for the process lifetime. Routes, response/request schemas, services, and repository concerns are separated. The app is intentionally not a forecasting engine and does not claim a measured dataset profile, model score, or time saving.

## Documented deviations

The original Project 00 prompt referenced by the assignment was not available in this checkout. The E2E implementation uses React, Radix UI, Vite, and an in-memory FastAPI repository rather than a database or authentication system. A production version could add persistence, multi-user sync, and auth.

## Files

- `index.html` — application shell and accessible controls.
- `styles.css` — visual system and responsive layout.
- `src/state.js` — pure state helpers used by the app and tests.
- `src/app.js` — DOM rendering and interaction logic.
- `tests/state.test.js` — executable state/model tests.
- `tests/contract.test.js` — checks the honest demo boundary and key accessible controls.
- `client/src/components/layout/` — shell, sidebar/mobile identity, and dashboard header.
- `client/src/components/project/` — project context and reusable metric cards.
- `client/src/components/tasks/` — composable task board, form, and rows.
- `client/src/components/workflow/` — accessible stage selection and evidence detail.
- `client/src/components/ui/` — small local design-system wrappers; Radix primitives are used within feature components.
- `client/src/hooks/` — cancellable workspace loading and single-flight mutation orchestration.
- `client/src/services/` — HTTP transport and normalized API errors.
- `client/src/test/` — React behavior and accessibility-focused component tests.
- `server/app/api/` — transport-focused routes and dependencies.
- `server/app/models/` — request and response schemas.
- `server/app/services/` — use cases and error policy.
- `server/app/repositories/` — thread-safe in-memory state and the explicit planning-only seed.
- `server/main.py` — thin ASGI bootstrap retained for `uvicorn main:app`.
- `tests/test_server_contract.py` — dependency-light API contract checks.
- `screenshots/` — optional visual evidence generated during local QA.
## Integration verification

- **Prompt alignment:** Public Project 00 asks for a modern dynamic todo application; this covers local task queue, filtering, persistence, responsive UI, and seeded workspace context.
- **Results/artifacts:** `index.html`, `styles.css`, and `src/` are the visual artifact; Node tests cover state/workflow behavior plus the honest UI contract.
- **Issue/resolution:** The E2E client/server is intentionally local-first and session-scoped; it omits authentication, multi-user sync, and database persistence.
