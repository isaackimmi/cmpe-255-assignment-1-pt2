# Project 00 — Independent Frontend Review

## Verdict

**Fixes required before this refactor should be treated as production-quality frontend architecture.** The implementation is a genuine React composition rather than a renamed monolith: `App.jsx` assembles focused sections, `useWorkspace` owns orchestration, `services/api.js` owns transport, Radix Checkbox/Progress primitives are used in the rendered tree, and the FastAPI entry point is now thin. The largest remaining risks are reproducible dependency installation, missing tests for the React application, and mutation error/race handling.

## Findings

### P1 — The checked-out React client cannot currently build, and there is no lockfile contract

Files: `client/package.json`, `client/vite.config.js`, repository `.gitignore`

`npm run build` fails with `ERR_MODULE_NOT_FOUND` for `@vitejs/plugin-react`. `npm ls --depth=0` also reports React, React DOM, both Radix packages, and the React Vite plugin as unmet. The dependencies are declared correctly, but the repository ignores `client/package-lock.json`, so a clean or stale checkout has no exact dependency graph and cannot use `npm ci`.

Recommendation: run a clean install, commit the generated lockfile, stop globally ignoring client lockfiles, and add a CI/check command that uses `npm ci && npm run build`. Keep React, React DOM, Vite, and the React plugin on a tested compatible version set.

### P1 — The frontend test command does not test the React client

Files: `client/package.json`, `tests/contract.test.js`, `tests/state.test.js`, `tests/test_server_contract.py`

`npm test` passes 13 tests, but those tests read the legacy root `index.html`, `src/app.js`, and `src/state.js`. They never render `client/src/App.jsx`, exercise `useWorkspace`, verify Radix interactions, or test loading/error/mutation behavior. The Python contract only checks dependency strings and a minimum component-file count, so disconnected or broken components could still pass.

Recommendation: add Vitest plus React Testing Library and user-event. Cover initial loading/API failure, task creation, toggle/delete, filtering/search, agent-check refresh, disabled/pending states, and accessible names/selected states. Retain the legacy tests only as explicitly named fallback-client tests.

### P1 — Mutation failures can become unhandled rejections, and concurrent actions can race

Files: `client/src/hooks/useWorkspace.js`, `client/src/components/TaskForm.jsx`, `client/src/components/TaskRow.jsx`, `client/src/components/TaskBoard.jsx`

`mutate()` updates the status message and then rethrows. `TaskForm.handleSubmit`, checkbox callbacks, delete callbacks, and the agent-check button do not catch the returned rejection. A failed request can therefore produce both the visible status and an unhandled promise rejection. Also, `pending` stores only one string while task rows disable only the matching action; another task mutation can start before the first completes, overwrite `pending`, and apply responses out of order.

Recommendation: define one mutation policy. Either catch errors at each event boundary or make `mutate()` return a typed success/failure result without rethrowing. Disable all conflicting mutation controls while a write is active, or track pending operations by key and ignore stale responses. Add tests for rejected and overlapping requests.

### P2 — Component placement is still too flat for a growing feature surface

Files: `client/src/components/*.jsx`, `client/src/components/ui/*.jsx`

The split is meaningful, but thirteen domain components share one directory while only `Button` and `Card` live under `ui/`. The current names are understandable at this size, yet the layout, task, workflow, status, and project-context concerns are not grouped, and `ProjectBriefCard`/`ReadinessCard` are private components inside `ProjectContext.jsx` while similar cards are separate files elsewhere.

Recommendation: organize by responsibility, for example `components/layout/`, `components/tasks/`, `components/workflow/`, `components/project/`, and `components/ui/`. Keep feature-specific composition near its feature and expose small `index.js` barrels only where they improve imports. Avoid turning every one-line element into a file; split on reusable behavior or independently testable UI.

### P2 — Several interaction states are not fully represented to assistive technology

Files: `client/src/components/WorkflowStage.jsx`, `client/src/components/WorkflowPanel.jsx`, `client/src/App.jsx`, `client/src/components/Sidebar.jsx`

The workflow buttons visually select a detail, but they do not expose `aria-pressed`, `aria-selected`, or a relationship to the detail region. The initial loading view is a plain `div` without `role="status"`/`aria-live`. Disabled sidebar items rely on `title`, but disabled controls are not reliably focusable, so keyboard and touch users may not receive the explanation. At mobile widths the entire sidebar/navigation disappears without a compact replacement.

Recommendation: expose workflow selection state and connect each stage to a named detail region with `aria-controls`; make loading a live status; render planned navigation as descriptive text or an accessible tooltip trigger rather than disabled buttons; provide a small mobile header/navigation affordance.

### P2 — Request lifecycle handling is incomplete under React Strict Mode

Files: `client/src/main.jsx`, `client/src/hooks/useWorkspace.js`, `client/src/services/api.js`

The app correctly enables `StrictMode`, but the initial effect has no cancellation or stale-response guard. Development Strict Mode can issue the initial GET twice, and a slow response can update state after a newer load or unmount. The API helper also has no `signal` option convention despite forwarding general options.

Recommendation: create an `AbortController` in the load effect, pass its signal through the API service, and ignore abort errors. If refresh/retry is added, guard state by request identity so the latest request wins.

### P2 — README documentation contradicts the new architecture

File: `README.md`

The run section still calls the client “raw HTML/CSS/JavaScript,” the deviations section says React is intentionally not used, and the file list documents the legacy DOM client as if it were the E2E implementation. It also says “No package installation is required” immediately after instructing the user to run `npm install`, and describes browser local-storage behavior that belongs to the fallback client rather than the FastAPI-backed React client.

Recommendation: separate “React E2E app” and “legacy static fallback” sections. Document React, Radix, the component/hook/service layout, exact install/build/test commands, in-memory server persistence, and which tests cover each client.

### P2 — Server layering is improved, but routes still bypass the service boundary

Files: `server/app/api/routes.py`, `server/app/services/workspace.py`, `server/app/models/schemas.py`

The app factory, dependency injection, repository, service, and thin `main.py` are good improvements. However, `/workspace` and `/readiness` call `service.repository` directly, leaking repository access into the HTTP layer. Routes also return untyped `dict`/`list[dict]` values rather than response models, so the API contract is less explicit than the request contract.

Recommendation: add `WorkspaceService.get_workspace()` and `get_readiness()`, keep the repository private, define response schemas, and declare `response_model` on routes. This will keep route code transport-focused and make client/server drift detectable.

### P3 — Presentational components contain demo identity/content that limits reuse

Files: `client/src/components/Sidebar.jsx`, `client/src/components/ProjectContext.jsx`, `client/src/components/DashboardHeader.jsx`

Names such as “Alex Kim,” initials, role, and portions of the forecast-specific hero copy are embedded inside otherwise reusable layout components. This is acceptable for a single demo but weakens composability if the shell is reused for another project.

Recommendation: pass profile and copy/configuration as props (or a small workspace view model) while keeping sensible defaults in a project-level container.

## Positive observations

- `App.jsx` is a concise composition root; it does not contain DOM manipulation or transport code.
- `useWorkspace.js` centralizes server state and exposes a coherent action interface.
- `services/api.js` normalizes non-JSON/error responses into a dedicated `ApiError`.
- `TaskBoard`, `TaskForm`, and `TaskRow` have sensible ownership boundaries, and filtering is memoized.
- Radix Checkbox and Progress are used for behavior/semantics rather than listed as unused dependencies.
- CSS tokens are separated from application layout, focus-visible styling is present, and narrow layouts are addressed.
- The server factory supports repository injection, the repository uses defensive copies and a lock, and `main.py` is appropriately thin.

## Verification performed

- `npm test`: **13 passed**, but all are legacy static-client/state tests as described above.
- `npm run build`: **failed** because the newly declared React/Radix/plugin dependencies are not installed in the current checkout.
- `npm ls --depth=0`: reports the React, React DOM, Radix, and React Vite plugin dependencies as unmet.
- `git diff --check -- 00_dynamic_todo_workspace`: passed.
