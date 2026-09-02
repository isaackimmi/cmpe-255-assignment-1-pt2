# Project 09 Final Polish Review

> Audit snapshot: this review records the pre-polish findings. The P0/P1 items below have now been addressed in the current working tree; see the post-polish resolution and verification note at the end of this file.

## Scope and verdict

This audit covers the Python DAG engine, the data-science example and tests, the browser companion, and the checked-in run evidence. It was completed from static source/artifact inspection plus local Python verification; no live browser/server verification is included.

The Python engine is a credible teaching-scale implementation. Its current code enforces declared reads, clears stale state on a new run, records task status and artifact lineage, seeds supported RNGs, and demonstrates a real quality gate. The project is not ready to present as an interactive visualizer of actual DAG execution and artifacts, however: the browser UI is a hardcoded simulation, and the README/evidence still contain stale four-task/6-test claims.

Recommendation: **conditional pass after a small but important polish pass**. At minimum, make the UI’s simulation status truthful and refresh all evidence. If the assignment expects the UI to demonstrate execution/artifact inspection, wire it to a generated run manifest before final submission.

## Prioritized findings

### P0 — The browser “live execution graph” does not execute the Python DAG or inspect real artifacts

**Evidence:** `ui/app.js:1-52` hardcodes the five task definitions and output strings. `ui/app.js:159-175` advances `completed` using a timer and never imports, fetches, or invokes `flowforge`, `Runner`, a manifest, or an artifact payload. `ui/app.js:93-97` displays the hardcoded `task.output` string when a task is marked complete. The graph edges are also synthesized as adjacent pairs in `ui/app.js:116-128`, rather than read from the Python DAG’s dependency declarations. The page labels the area “Live execution graph” in `ui/index.html:84`, while the README correctly describes it as a “static browser companion” in `README.md:18-30`.

**Assessment:** The UI is interactive in the narrow presentation sense—Run, Reset, node selection, status animation, and inspector updates work from the JavaScript state—but it is not evidence that the real runner executed, and it cannot show a real failure, branch, run ID, artifact ID, parent lineage, content hash, schema fingerprint, or manifest task state. A code change to the Python pipeline can therefore leave the UI apparently green while showing obsolete results.

**Action:** Choose one of these before submission:

1. For a lightweight explanatory demo, rename “Live execution graph,” “Latest output,” and “Run demo” to make clear that this is a replay/simulation, and state prominently that outputs are illustrative.
2. Preferably, add a generated JSON run-manifest fixture or a small local endpoint produced by the Python example. Have the UI derive task names, dependency edges, statuses, outputs, run metadata, and artifact lineage from that source. Add a visible “simulation vs. verified run” distinction and a failure-state example.

### P0 — Checked-in documentation and visual evidence are stale relative to the current implementation

**Evidence:** The current test suite contains 14 tests and passes (`tests/test_core.py:9-125`, `tests/test_basic_pipeline.py:7-29`; verified with `python3 -m unittest discover -s tests -v`). The example has five tasks, including `validate_data` (`examples/basic_pipeline.py:57-63`). Nevertheless, `README.md:16` says only that the example and tests ran without stating the current count, `README.md:20` calls the UI a visualization of “the same four tasks,” and `README.md:71` claims “unittest passed 6/6.” The checked-in SVG repeats the obsolete count and omits validation from its pipeline summary (`artifacts/run_evidence.svg:1`).

**Impact:** A reviewer can reasonably conclude that the artifact was generated from an older revision or that the quality gate is absent from the demonstrated execution path. This undermines otherwise strong current code and makes the final deliverable internally inconsistent.

**Action:** Regenerate `artifacts/run_evidence.svg`, update the README to five tasks and the actual test count, and either remove or clearly label the older `DS_REVIEW.md` claims (`DS_REVIEW.md:63-72`) as superseded. Use one canonical command/output source so future code changes cannot silently leave the public evidence behind.

### P1 — Lineage exists in the engine but is not carried into the user-facing artifact story

**Evidence:** `Artifact` records producer, run ID, parent artifact IDs, content hash, schema fingerprint, and timestamp (`flowforge/core.py:122-160`). The runner creates parent links and writes task-level artifact metadata into the in-memory manifest (`flowforge/core.py:259-279`, `flowforge/core.py:470-476`). The public context exposes these records (`flowforge/core.py:197-228`). The UI inspector exposes only a prose type, dependency names, a type-like output label, and a static preview (`ui/index.html:106-115`, `ui/app.js:83-98`); it never displays any artifact envelope fields.

**Assessment:** The core can answer basic “what produced this?” questions during the current process, but the delivered visual experience does not demonstrate that capability. The manifest and payloads are also in-memory only, consistent with the limitation documented in `README.md:57-67`.

**Action:** Export a small JSON manifest alongside the example run, or add a manifest download/view in the UI. Show run ID, task status, artifact ID, parent IDs, content hash, schema fingerprint, and seed in the inspector. Keep payload previews redacted/limited and make clear that the current engine has no durable artifact store.

### P1 — Reproducibility is good for the tested toy case but not yet a complete pipeline contract

**Evidence:** `Runner.run` records seed/config/environment and seeds Python `random` plus NumPy when available (`flowforge/core.py:442-468`). Task code/config fingerprints are recorded in the manifest (`flowforge/core.py:470-476`). The reproducibility test uses a fixed seed and fixed clock (`tests/test_core.py:106-117`). The bundled source is a literal in-memory list (`examples/basic_pipeline.py:14-15`), so it has no external input URI, file hash, query, or snapshot provenance. The environment manifest records only Python and platform (`flowforge/core.py:451-454`), and the run ID is intentionally random (`flowforge/core.py:451`).

**Assessment:** Same-seed replay is demonstrated for a standard-library random task, but arbitrary Python tasks can still depend on other RNGs, wall-clock time, filesystem/network state, package versions, process environment, or unstable object representations. The content fingerprint fallback uses `repr` for unsupported values (`flowforge/core.py:34-51`), which is not a universal reproducibility guarantee.

**Action:** State the supported reproducibility boundary in the README and manifest. For a stronger demo, record dependency/package versions, input snapshot or source hash, task config, code fingerprint, clock policy, and RNG policy; require external-input tasks to declare provenance. Add a test for the manifest fields and for a changed input/config producing a changed fingerprint.

### P1 — Task contracts validate dependency names and access scope, but not input/output schemas

**Evidence:** `Task` validates names, callable shape, dependency collection shape, and duplicate dependencies (`flowforge/core.py:85-119`). `TaskContext.output` rejects undeclared reads (`flowforge/core.py:302-337`), and the test covers both insertion orders (`tests/test_core.py:73-83`). `_schema` computes a descriptive shape after a result exists (`flowforge/core.py:54-64`), but no expected schema is declared on `Task` or checked before a dependent task runs.

**Assessment:** Dependency soundness is now strong for this API, but “contract” currently means graph/access contract, not data contract. A task can return a structurally unexpected mapping/list and the next task will discover the problem only through its own code.

**Action:** Keep the current scoped context, then add optional input/output validators or schema declarations at task boundaries. Record validation results in the manifest, especially for the quality gate, so the UI can show “validated” as an actual run fact rather than a static badge.

### P2 — The data-quality example is solid for teaching, but the imputation policy needs domain framing and richer evidence

**Evidence:** `validate_data` checks non-empty input, exact row keys, age type/non-negativity/finite values, and score type/range (`examples/basic_pipeline.py:18-37`). `clean_data` explicitly distinguishes `None` from a legitimate zero (`examples/basic_pipeline.py:40-44`). Tests cover preservation of zero, explicit imputation, malformed score, negative age, missing field, and empty input (`tests/test_basic_pipeline.py:15-29`).

**Assessment:** This is a meaningful quality-gate example and is no longer the weak missing-data example described in the older review. However, replacing a missing age with zero is still a domain assumption, not a generally safe cleaning rule; the example does not report how many values were imputed or why zero is acceptable. The exact-schema rule and allowed age range are also implicit teaching choices.

**Action:** Add a short rationale/configuration for the imputation policy, return a structured quality/cleaning summary or metrics, and add assertions for NaN/Infinity, boolean values, extra fields, and any chosen maximum-age/domain rule. Keep the current zero-preservation test because it demonstrates the intended distinction clearly.

## Verification summary

- `python3 -m unittest discover -s tests -v`: **PASS**, 14 tests.
- `python3 examples/basic_pipeline.py`: **PASS**, `load_data -> validate_data -> clean_data -> summarize -> report`; mean score `83.3`.
- `python3 -m compileall -q flowforge examples tests`: **PASS**.
- No code or test files were modified during this audit; this review is the requested new project-root artifact.

## Final recommendation

The engine itself is suitable for a teaching-scale Project 09 submission. The browser surface is now explicitly a manifest-backed, replay-only artifact explorer, and the visible DS story aligns with the stronger guarantees already present in `flowforge/core.py`.

## Post-polish resolution (2026-08-31)

- `examples/basic_pipeline.py` now exports a successful run manifest and a real fail-fast fixture. Task records include declared dependencies, status, config, code/config fingerprints, artifact lineage, hashes, schema fingerprints, and bounded output previews.
- `ui/` now loads those manifests, derives task nodes and edges from the recorded DAG, exposes run/task/artifact metadata, and labels replay as a recorded-manifest view rather than live Python execution.
- `README.md`, `DS_REVIEW.md`, and `artifacts/run_evidence.svg` now describe the five-task pipeline and current verification. The current test suite passes 16 tests; `node --check ui/app.js` and `python3 -m compileall -q flowforge examples tests` also pass.
