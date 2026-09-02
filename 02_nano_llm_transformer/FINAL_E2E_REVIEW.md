# Project 02 — Final E2E Review

## Verdict

**Fixes are required.** The Vite/FastAPI/ML structure is present and the current n-gram artifact reproduces exactly through the adapter, but four boundary defects remain before the E2E conversion is robust.

## Actionable findings

### [P1] Prevent silent backend mismatch

`ml/model_adapter.py` always constructs `CharNGram`, even when `metrics.json` declares `torch_transformer`. The UI can therefore label a run as Torch while `/api/generate` serves n-gram output.

**Fix:** Make inference backend-aware. Implement Torch inference when an executable artifact exists, or reject unsupported backends with a clear `409`/`501`. Return separate artifact and inference backend fields and test a Torch-labeled artifact.

### [P1] Enforce artifact/corpus parity

The adapter trusts `split.train_end`, configuration, vocabulary, and the current corpus without checking `corpus_sha256`, split continuity, `<UNK>`, or regenerated vocabulary equality.

**Fix:** Validate corpus hash, ordered split offsets, vocabulary policy, recorded vocabulary, and backend before serving inference. Return a typed artifact-mismatch error. Add negative tests for changed corpus data, invalid offsets, and vocabulary drift.

### [P1] Add real no-server HTTP tests

The current API test class skips completely when FastAPI is absent. When installed, it calls route functions directly rather than exercising ASGI routing, JSON validation, status codes, or exception handling.

**Fix:** Add `httpx` to test dependencies and use `fastapi.testclient.TestClient`. Cover all five routes, deterministic generation, normalized probabilities, malformed bodies, `422` bounds, unsupported backends, and missing/corrupt artifacts. Ensure CI/local integration installs server requirements so a full API skip is not considered green.

### [P1] Render API values safely

`client/src/main.js` interpolates prompt-derived `step.context` and model tokens into `innerHTML`. A prompt containing HTML can inject markup into the trace panel.

**Fix:** Build trace/probability rows with DOM nodes and `textContent`, or escape every API-derived value. Add a client test proving HTML-like prompts render as text.

### [P2] Return useful artifact errors

Missing or invalid `metrics.json`, missing corpus files, and JSON/schema errors currently become generic server errors; the client collapses them into “API unavailable” or “Request error.”

**Fix:** Add typed adapter exceptions and FastAPI handlers for `artifact_missing`, `artifact_invalid`, `artifact_mismatch`, and `backend_unsupported`. Surface the safe server detail in an accessible client error panel.

### [P2] Lock and verify the Vite build

There is no `client/package-lock.json`, and `npm run build` has not been verified. Static tests only check files and route strings.

**Fix:** Commit the lockfile, run `npm ci` and `npm run build`, and verify `client/dist/index.html` plus bundled assets are produced during the sequential integration pass.

### [P3] Align small demo details

The client input caps generation at 40 tokens while FastAPI permits 80, and the Vite footer links to `/README.md`, which is not a client asset.

**Fix:** Use one shared limit and replace the footer link with a valid repository/documentation target.

## Verification evidence

- Core suite: 13 tests, 10 passed, 3 optional PyTorch skips.
- New suite: 2 static/client tests passed; FastAPI contract class skipped because dependencies are absent.
- Python and JavaScript syntax checks passed; `git diff --check` passed.
- Current artifact parity passed: backend, vocabulary, deterministic replay text, and full trace agree between `metrics.json` and the rebuilt n-gram adapter.
- No server or browser was started.
