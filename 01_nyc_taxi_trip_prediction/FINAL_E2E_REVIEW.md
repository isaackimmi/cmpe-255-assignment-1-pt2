# Final E2E review — Project 01

**Status: fixes are required before this project meets the requested E2E architecture.**

## Ranked findings

### P0 — No Vite client exists, so the new FastAPI layer is not end-to-end wired

The project currently has no `client/` directory, no `package.json` for a Vite client, and no browser code that calls the FastAPI routes. The existing top-level `index.html`/`app.js` remains a dependency-free static artifact viewer and computes its estimator entirely in the browser. Consequently, the new `server/main.py` endpoints are unreachable from the intended UI and the project does not yet provide the requested client/server E2E path.

**Recommendation:** add `client/` with a Vite-compatible package manifest, raw HTML/CSS/JS entry point, API base/proxy configuration, loading/error states, and controls that call `/api/experiment`, `/api/predictions`, `/api/feature-importance`, and `/api/estimate`.

### P1 — The FastAPI server has no API contract tests and is not covered by the existing test suite

The only current tests are `tests/test_run_experiment.py`, which exercise the training experiment but never import `server.main` or `ml.model`. There are no tests for response shapes, invalid query parameters, estimator validation, missing artifacts, or the API-to-artifact path. This makes integration regressions likely and does not establish that FastAPI can import successfully in the documented environment.

**Recommendation:** add no-server tests for health, experiment metadata, feature importance, prediction slice output, invalid slice/population handling, valid estimator output, and invalid estimator inputs. Use direct route-function calls or a test client only if the dependency is available; keep the tests independent of a running process.

### P1 — Estimator validation is weaker than the training data contract

`ml/model.py::estimate` accepts globally valid coordinates but does not enforce the experiment's NYC-like service-area bounds, does not reject zero-distance routes, does not reject ambiguous local timestamps, and does not normalize/validate timestamp awareness consistently with `run_experiment.py`. It also uses the fallback generator formula rather than model weights, which is acceptable only if the API labels this as an illustrative teaching estimate and the README explains the distinction.

**Recommendation:** either reuse the experiment's shared validation helpers or explicitly mirror its service-area, timestamp, distance, and passenger contracts. Add tests for out-of-area coordinates, ambiguous timestamps, malformed timestamps, excessive routes, and the documented illustrative behavior.

### P1 — Slice scoring needs a documented and stable population contract

`prediction_slice` recomputes the distance median from the currently selected population. Therefore the `short`/`long` boundary changes when `population=robust`, rather than remaining the primary holdout boundary recorded by the run. The function also silently converts malformed numeric artifact values to zero through `_number`, which could produce misleading scores instead of failing loudly on corrupted artifacts.

**Recommendation:** persist/use a run-level distance-slice boundary from `metrics.json`, validate artifact schemas and finite values, and return an explicit error when checked-in predictions are malformed. Document whether the robust population is sensitivity-only and how its slices are defined.

### P2 — README still documents only the legacy static-server workflow

The current README instructs users to run `python3 -m http.server 8000` and describes a static UI with “no build step.” It does not document `server/requirements.txt`, a FastAPI/uvicorn command, a Vite install/build/dev command, API configuration, or the expected client/server startup order. This conflicts with the requested architecture and will make the project difficult to demo reproducibly.

**Recommendation:** document separate terminal commands, for example: create a server environment and install `server/requirements.txt`; run `uvicorn server.main:app --reload --port 8001`; install client dependencies and run `npm run dev`; explain the Vite proxy and artifact-backed/illustrative estimator boundary.

### P2 — Import/deployment layout should be tested from the documented launch directory

`server/main.py` mutates `sys.path` to import `ml.model`, which can work from the repository root but is not currently validated with uvicorn or an import test. The README's current `cd project && python3 -m http.server` path does not exercise this layout. A clean import test should verify that `server.main:app` resolves from the project root and that all artifact paths are project-relative.

## Positive observations

- The existing training experiment has strong chronological split, timestamp-awareness, structural-cleaning, and train-only target-policy tests.
- The API separates artifact loading and deterministic estimation into `ml/model.py`, which is a reasonable seam for the requested architecture.
- The endpoints are narrowly scoped and include useful resources for an analytical explorer: metrics, predictions/slices, feature importance, and estimation.
- The server includes CORS configuration for local Vite origins and uses typed request fields with basic numeric bounds.

## Review conclusion

The modeling/evaluation foundation is solid, but the requested E2E deliverable is incomplete. Fixes are needed, especially the missing Vite client, missing API tests, README run instructions, and estimator/slice contract hardening. No server or browser was started during this review.
