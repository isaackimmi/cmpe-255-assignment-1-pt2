# Project 00 — Final E2E Review

Review scope: newly added `client/` and `server/` architecture only.  
Review date: 2026-08-31  
Reviewer: independent robustness pass

## Summary

The project now has the requested high-level split: a Vite-compatible raw HTML/CSS/JavaScript client and a FastAPI service. The API has sensible typed task inputs, bounded titles, constrained priority values, explicit 404 responses, and a good planning-only data-science boundary. No `ml/` directory is required because Project 00 is a workflow/readiness application and does not claim to train or serve a model.

Fixes are required before this can be considered a working E2E implementation. The documented Vite and FastAPI commands do not currently connect to one another, and mutation failures are not surfaced in the UI. The review test file also needs to be restored or the README must stop claiming it exists.

## Findings

### High — Vite client has no API proxy

**Evidence:** `client/src/main.js` requests `/api/workspace`, `/api/tasks`, and `/api/agent-check`. `client/package.json` starts Vite, but there is no `client/vite.config.js` (or equivalent proxy configuration) forwarding `/api` to `http://127.0.0.1:8000`.

**Impact:** With the README's two-terminal commands, the browser sends `/api` requests to Vite on port 5173. Vite will return a client-side 404 instead of reaching FastAPI, so the new E2E app displays its API-unavailable state and CRUD cannot work.

**Recommendation:** Add a Vite config with a development proxy for `/api` to the FastAPI origin, or make the API base URL configurable and document the required origin. Add an integration smoke test that proves the configured client base path matches the API path without starting a server in the test process.

### High — Client mutation errors are unhandled

**Evidence:** The submit, checkbox, delete, and `#simulate` handlers call `api(...)` without `try/catch`, a busy/disabled state, or an error surface. Only the initial `start()` request handles errors.

**Impact:** A failed mutation produces an unhandled promise rejection and leaves the user without an explanation. A checkbox can visually change before the API request fails, making the visible state disagree with server state after reload.

**Recommendation:** Centralize request state, disable the active control while a mutation is pending, restore the prior control state on failure, and show an `aria-live` error/status region. Handle network failures and non-JSON responses as well as normal FastAPI validation errors.

### High — Review test contract is missing and no API test command is documented

**Evidence:** The README lists `tests/test_server_contract.py`, but that file was not present during review. The existing Node tests cover the legacy root app, not the new FastAPI routes. The README's test section only runs `node --test tests/*.test.js` and does not provide a Python command for the server contract.

**Impact:** The new API's route, validation, and response-shape promises are currently unverified. A future server change could break the client contract without turning the test suite red.

**Recommendation:** Add no-server contract tests that parse or import the FastAPI app as appropriate, cover health/workspace/readiness routes, valid and invalid task creation, update/delete 404s, and the planning-only metadata. Add the exact command to README and ensure the required test dependency is declared.

### Medium — Server state is global process memory

**Evidence:** `server/main.py` stores mutable data in module-level `state = deepcopy(SEED)`.

**Impact:** All users share one process state, concurrent requests can race, and every restart resets the queue. This is acceptable for a single-user demonstration but is not a persistent local-first application in the usual sense.

**Recommendation:** Keep the in-memory implementation if intentionally scoped to a demo, but label it prominently as single-process session state and add a reset endpoint or documented restart behavior. If persistence is required by the assignment prompt, use a small SQLite repository with explicit schema and tests.

### Medium — API origin is hardcoded in the client path

**Evidence:** `fetch(`/api${path}`)` assumes the API is same-origin or proxied. The legacy static root app is still the GitHub Pages fallback, but it cannot use these endpoints.

**Impact:** The E2E client only works in a correctly configured Vite development environment. Previewing the built client from a different static origin will fail unless a reverse proxy is supplied.

**Recommendation:** Add a documented `VITE_API_BASE_URL`-style configuration with a safe local default, or provide a FastAPI static mount/reverse-proxy mode for one-command local demos.

### Low — Several interactive elements are not keyboard-semantic

**Evidence:** Workflow stages are clickable `<div>` elements rather than buttons, and the sidebar's “Agent runs” and “Datasets” controls have no behavior. The task form does not expose an `aria-expanded` relationship for the Add button.

**Impact:** Keyboard and assistive-technology users cannot fully access the same workflow detail behavior, and inert controls suggest functionality that is not implemented.

**Recommendation:** Use native buttons for stage selection, either implement or visually mark unavailable navigation, and add explicit expanded/status semantics to the task form.

## Positive findings

- Task input is bounded with Pydantic (`min_length`, `max_length`, and a `Literal` priority set).
- Task titles are trimmed server-side and HTML-escaped client-side before interpolation.
- Unknown task IDs return explicit 404 errors rather than silently succeeding.
- CORS is limited to the documented local Vite origins rather than allowing every origin.
- The UI accurately says that no dataset, model artifact, metric, or measured lift is connected.
- The workflow copy gives appropriate CRISP-DM guidance without presenting planned steps as completed model evidence.
- Omitting `ml/` is appropriate for this project’s stated planning/readiness purpose.

## Verdict

**Not ready to approve as E2E yet.** Fix the Vite-to-FastAPI proxy/base URL, add the missing server contract tests and test command, and handle mutation errors in the client. After those changes, perform one sequential local smoke run and verify task CRUD plus the readiness/workflow views.
