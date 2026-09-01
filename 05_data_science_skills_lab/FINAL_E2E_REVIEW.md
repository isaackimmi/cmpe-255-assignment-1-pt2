# Project 05 final E2E review

Review scope: `client/`, `server/`, `ml/`, DS artifact contracts, CORS/error handling, and README commands. No server or browser was started.

## Verdict

**Fixes are required before the E2E rebuild is ready for demo.** The underlying data-science pipeline remains strong and its eight numerical/contract tests pass, but the new README describes API capabilities that do not exist and the client does not use the documented API shape.

## Ranked findings

### P1 — README documents four nonexistent endpoints and an unsupported client configuration

- Evidence: `README.md:37-50` claims `/api/metrics`, `/api/evidence/{module}`, and `/api/estimate`, plus `VITE_API_URL` configuration. `server/main.py:24-62` exposes `/api/health`, `/api/summary`, `/api/cleaning`, `/api/classification`, `/api/regression`, `/api/clustering`, and `/api/rows`; no estimator or generic evidence route exists. `client/src/main.js:18-20` hard-codes `/api/summary` and never reads `VITE_API_URL`.
- Impact: following the README gives a false picture of the architecture and makes the demo narrative inaccurate. A reviewer trying the advertised endpoints receives 404s.
- Required fix: either implement the documented routes/configuration or rewrite the E2E section to list the routes and proxy behavior that actually exist. Add a contract test that compares documented routes, server routes, and client fetch paths.

### P1 — The client/server boundary is mostly a single bulk artifact download, not the claimed module API

- Evidence: `client/src/main.js:18-28` performs one request to `/api/summary` and applies all plan/renewal/cluster filters in browser memory. The purpose-built `/api/cleaning`, `/api/classification`, `/api/regression`, `/api/clustering`, and `/api/rows` routes in `server/main.py:34-62` are unused.
- Impact: the UI is visually interactive, but it does not demonstrate the E2E analytical API described in the assignment. Server-side query validation/filtering is not exercised by the client, and a broken module route would not be noticed.
- Required fix: have module navigation fetch the corresponding endpoint and have row filters query `/api/rows`, with loading, empty, and non-2xx states. Keep `/api/summary` only for the initial overview if desired.

### P2 — Query parameters silently accept invalid categorical values

- Evidence: `server/main.py:56-62` constrains only `limit`. Values such as `plan=bogus`, `renewal=yes`, or `cluster=999` return an empty successful response.
- Impact: typos and client/server schema drift look like valid zero-row analyses. That is especially risky in a DS explorer because an empty result can be misinterpreted as a real segment result.
- Required fix: use `Literal`/enum parameters (including `all`) or explicit validation and return HTTP 422 for unsupported categories. Add direct route-function tests that do not start a server.

### P2 — Artifact integrity and parse failures become generic 500 errors

- Evidence: `ml/pipeline.py:22-26` checks only file existence and calls `json.loads` directly. `server/main.py:17-21` translates only `FileNotFoundError` to a 503.
- Impact: corrupted, partially regenerated, or schema-incompatible artifacts produce an opaque internal error rather than an actionable evidence-contract failure.
- Required fix: validate required top-level keys and expected row/metric collections in the ML adapter; translate JSON/schema failures to a stable 503 response with a concise regeneration instruction.

### P2 — Duplicate, unused client stylesheet creates a stale implementation surface

- Evidence: `client/src/main.js:1` imports `style.css`; `client/src/styles.css` is a second, large dashboard stylesheet that is not imported.
- Impact: future fixes can land in the wrong file and appear to have no effect. It also obscures which UI implementation is authoritative during review.
- Required fix: keep only the stylesheet used by the Vite entrypoint or deliberately split and import both with clear responsibilities.

### P3 — External font loading contradicts the offline-ready presentation

- Evidence: `client/src/style.css:1` imports Google Fonts while the UI and README frame the project as offline-ready.
- Impact: the app still works with fallbacks, but visual rendering changes offline and the claim is not exact.
- Required fix: remove the remote import and use the existing system fallbacks, or explicitly document the optional network enhancement.

## Positive evidence

- `client/package.json` and `client/vite.config.js` form a valid Vite structure with a scoped `/api` proxy and deterministic ports.
- `server/main.py` has a clear read-only FastAPI surface and CORS is restricted to the two documented local Vite origins.
- `ml/pipeline.py` keeps model execution out of the browser and avoids silent retraining during API reads.
- The existing DS pipeline preserves train-only imputation for predictive work, observed-target scoring, explicit baselines, scaled clustering, deterministic seeds, and synthetic-data limitations.
- Static verification completed successfully: eight unit tests passed, `node --check client/src/main.js` passed, and `git diff --check` passed.

## Required next step

Implement the P1 findings first, then the P2 contract/error fixes, update the README to the final route set, and rerun the static test suite before any sequential localhost/browser review.
