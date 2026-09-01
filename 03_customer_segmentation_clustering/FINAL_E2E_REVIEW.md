# Project 03 final E2E robustness review

Review scope: `client/`, `server/`, `ml/`, API wiring, clustering/scaling/k-selection contracts, error states, tests, and README commands. No server or browser was started.

## Ranked findings

### P1 — API scoring bypasses the selected preprocessing contract

`ml/pipeline.py::score_observation()` fits the correct selected segmenter, but then calls `fitted["scaler"].transform(frame[FEATURES])` directly. For a selected `log1p` run, that feeds raw monetary features to a scaler that was fit on log-transformed values. The canonical `score_customers()` path correctly calls `_raw_values(..., fitted["preprocessing"])` before scaling, but the API adapter does not use it. This can produce materially wrong cluster assignments while the response reports the selected preprocessing as applied.

**Recommendation:** delegate scoring to `src.experiment.score_customers(frame, fitted)` or apply the same `_raw_values` contract explicitly. Add a parity test asserting the API adapter and canonical scoring path return the same assignment for both `standard` and `log1p` fitted models.

### P1 — The client claims manifest verification without loading or validating the manifest

The client boot path fetches only `/summary` and `/points`, then renders `API VERIFIED`, `READY`, and “manifest and hashes verified.” It never calls `/manifest`, `/health`, or a server-side verification endpoint, and the server routes return artifact files without running `validate_artifacts()`. Merely loading two files does not prove the checked-in artifact set is complete, internally consistent, or hash-valid.

**Recommendation:** add an API evidence/status endpoint that executes the canonical artifact validator and returns the manifest plus explicit validation state. Gate the green status on that response; otherwise show a blocked/stale evidence state. Test corruption/missing-file behavior.

### P1 — Segment names are attached to arbitrary K-Means labels

The client assigns “Budget starters,” “Frequent loyalists,” and “Premium value” by the array index returned from a `Map` keyed by raw cluster label. K-Means numeric labels have no semantic order and can permute across compatible refits. As a result, a persuasive business name can be attached to the wrong profile even when the underlying clustering is valid.

**Recommendation:** derive names from profile statistics, as the legacy dashboard did, or have the server export a deterministic profile-role mapping based on ranked feature means. Include the feature evidence used to assign each name and retain “hypothesis only” language.

### P1 — Documented run commands omit the server dependency installation

The README initially installs only the root `requirements.txt`, which contains the modeling stack but not FastAPI/Uvicorn. It later instructs users to run `python3 -m uvicorn server.app:app`, without first installing `server/requirements.txt`. A clean environment following the documented commands will fail before the API starts.

**Recommendation:** provide one exact setup sequence that installs both requirement files, or consolidate server dependencies into a single project-level requirements file. Include a supported Python version and an optional virtual-environment step.

### P1 — Contract tests do not exercise the FastAPI or ML boundary

`tests/test_server_contract.py` counts route decorators and checks that files exist. It never imports the application, invokes a route, validates response schemas, tests CORS/error behavior, or compares `/api/score` with the canonical scoring function. Consequently, the preprocessing defect and false verification state both pass the current suite.

**Recommendation:** use FastAPI `TestClient` with a temporary/copy artifact directory and add tests for health/evidence status, point filtering, profiles, validation schema, missing/corrupt artifacts, Pydantic domain rejection, and score parity for both preprocessing variants. Add a client contract test that requires manifest/status fetching before a verified badge is rendered.

### P2 — Scoring refits a model per request instead of loading a run-bound model bundle

Every `/api/score` request rebuilds the deterministic synthetic training frame and refits K-Means. This is repeatable today, but it is inefficient and not cryptographically bound to the manifest that supplied the UI metrics. If generator code, dependencies, seed, or artifacts drift, the score path can diverge from the evidence displayed by the client.

**Recommendation:** persist a versioned scaler/model bundle and schema fingerprint during `src.experiment.run()`, include its hash in the manifest, load it once at API startup, and refuse scoring when bundle/manifest/schema fingerprints disagree. For this teaching project, a cached in-memory deterministic fit is an acceptable interim step if its source hash is validated.

### P2 — Artifact read failures become generic 500 responses

`read_json()` and `read_csv()` allow missing files, malformed JSON/CSV, non-finite values, or schema drift to propagate as unstructured internal errors. The client can only display a generic “Evidence API unavailable” page, which does not distinguish a stopped server from stale or corrupt experiment evidence.

**Recommendation:** centralize artifact loading and validation, map known evidence failures to a typed 503 response, and expose actionable error codes such as `artifact_missing`, `manifest_mismatch`, and `schema_invalid`. Preserve internal exception details in logs rather than browser responses.

### P2 — Server profile endpoint exists but the client silently recomputes profiles

The API exposes `/api/profiles`, yet the client ignores it and computes means from `/points`. This duplicates analytical logic across client and server, makes the server contract partly decorative, and prevents the API from owning deterministic semantic profile mapping.

**Recommendation:** return profile statistics and evidence-based names from `/api/profiles`; have the client render that response while using `/points` only for the scatter/inspector.

### P3 — Point controls are not fully keyboard-operable

SVG circles receive `tabindex="0"` and `role="button"`, but only a click listener is registered. Enter and Space do not select a focused point. The controls therefore advertise button semantics without matching keyboard behavior.

**Recommendation:** add Enter/Space handlers or use an accessible point list synchronized with the chart.

## What is sound

- The canonical experiment preserves split-local scaling during repeated validation and predeclares `k=2…7`.
- K-selection uses held-out silhouette with ARI stability and lower-k tie-breaking; full-sample metrics are labeled descriptive.
- The client clearly states that the data are synthetic, clusters are hypotheses, and geometry confidence is not a probability.
- Pydantic input bounds mirror the documented feature domains for the API request model.
- The E2E directory split and API surface are directionally aligned with the requested Vite/FastAPI/ML architecture.

## Recommended acceptance gate

Do not treat Project 03 as E2E-complete until the P1 findings are fixed and proven by API-level tests. At minimum, acceptance should require: canonical/API scoring parity for both preprocessing variants; real manifest validation before a verified UI status; deterministic evidence-based segment naming; clean-environment run instructions; and TestClient coverage of success, validation failure, and corrupt-artifact paths.
