# Project 04 — Final E2E robustness review

Review date: 2026-08-31  
Scope: `client/`, `server/`, `ml/`, API/threshold contracts, mining semantics, tests, and README instructions.  
Runtime constraint honored: no server or browser was started.

## Verdict

**Fixes are required before this project should be treated as a finished E2E implementation.** The Apriori implementation itself remains sound and the static verification suite passes, but the current server/ML boundary and run documentation do not describe or test the code path the client actually uses.

## Ranked findings

### P1 — The FastAPI server bypasses the declared ML layer

`server/main.py:14-21` imports `apriori`, `association_rules`, and loaders directly from `analysis.py`; it never imports either `ml/pipeline.py` or `ml/mining.py`. Two separate ML adapters now exist, but neither is the source of the API responses. This makes the `client → server → ml` architecture cosmetic and allows three implementations/contracts to drift. It also contradicts `README.md:34` and `README.md:63`, which say FastAPI calls `ml/mining.py` and that the ML layer is the source of truth.

**Required fix:** choose one ML service module, route all API mining through it, and remove or clearly deprecate the duplicate adapter. The API should perform only transport/query validation and serialization.

### P1 — The documented run/API contract does not match the implementation

`README.md:31-34` tells the user to run Vite on port 5174, says the browser calls `/api/mine`, and documents `VITE_API_URL`. The actual Vite configuration uses port 5173 (`client/vite.config.js:4`), the client calls `/api/summary`, `/api/itemsets`, `/api/rules`, `/api/transactions`, and `/api/context`, and `client/src/main.js` does not read `VITE_API_URL`. These are material demo/run instructions, not cosmetic wording.

**Required fix:** select one port and API-origin strategy, update the configuration and README together, and document the real endpoint set.

### P1 — Tests do not exercise the FastAPI behavior used by the client

`tests/test_e2e_contract.py:15-20` checks route names as strings rather than calling routes. `tests/test_api_contract.py` tests `ml/mining.py`, which the server does not use. Therefore the green 22-test result does not prove that FastAPI validation, response schemas, sorting, context behavior, or API/ML parity work.

**Required fix:** add FastAPI `TestClient` tests for health, summary, transactions, itemsets, rules, context, invalid queries, and unknown items. Compare returned itemset/rule metrics against the independent analysis oracle.

### P2 — The count-floor domain permits impossible support metadata

Every `min_count` query is constrained only with `ge=1` (`server/main.py:87`, `118`, `132`). A value above the 24-basket denominator returns an empty result while `summary()` reports an effective support above 100% (`server/main.py:98-99`).

**Required fix:** reject `min_count > transaction_count` with a clear 422 response, or cap it explicitly and disclose that behavior. Add a boundary test for 24 and 25.

### P2 — Rule evidence omits exact confidence/lift denominators

`_rule_record()` returns `support_count` as floating-point multiplication (`server/main.py:72`) and omits `antecedent_count` and `consequent_count`. The client can display support counts but cannot prove confidence as `support_count / antecedent_count` or lift against consequent prevalence. The earlier offline dashboard exposed those exact denominators.

**Required fix:** use `support_count()` for an integer numerator and include integer antecedent/consequent counts in the API and rule cards.

### P2 — Frontend install is not locked and duplicate client assets remain

There is no `client/package-lock.json`, so the Vite dependency is not fully reproducible. Both `client/src/style.css` and `client/src/styles.css` exist, while only `styles.css` is imported.

**Required fix:** generate and commit the npm lockfile after installation and remove or document the unused stylesheet after confirming which design is canonical.

### P2 — Rapid control changes can render stale responses

Each slider input immediately triggers a four-request `Promise.all` refresh. There is no request sequence guard or cancellation, so an older, slower response can overwrite a newer threshold selection.

**Required fix:** debounce slider updates and/or use an `AbortController` or monotonically increasing request token before rendering results.

## What is already strong

- `analysis.py` retains deterministic Apriori pruning and exact support/confidence/lift calculations.
- Whole-basket support counts and the synthetic/in-sample limitation are clearly explained.
- The Vite client is substantive and interactive, with threshold, size, sort, and context controls.
- FastAPI exposes the expected analytical surfaces and validates probability/ranking query types.
- Static verification completed successfully: **22 pytest tests passed**, Python compilation passed, JavaScript syntax checks passed, and `git diff --check` passed.

## Required completion gate

Resolve all P1 findings, add route-level parity tests, correct README commands, and then run the client/server sequentially for the browser smoke test and screenshots. P2 items should be addressed in the same pass where practical because they affect analytical evidence and demo reliability.
