# FlowForge Data-Science Robustness Review

> Historical review: the findings below describe the pre-polish implementation. Current behavior and verification are documented in `FINAL_POLISH_REVIEW.md` and `README.md`; stale counts and examples in this audit are superseded.

## Scope and overall assessment

Reviewed the Python DAG engine, its unit tests, the data-science example, and the browser companion in project 09. The scheduler is correct for a small, single-process graph whose tasks honor their declared dependencies: it validates unknown dependencies and cycles, produces a stable insertion-order Kahn traversal, and stops before later tasks after an exception. That is not yet a guarantee of sound, lineage-preserving, reproducible data-science execution. The main risks are stale run state, undeclared data access, lack of artifact lineage and contracts, and the absence of reproducibility controls around arbitrary Python callables.

## Findings

### [HIGH] Failed runs can expose stale artifacts when a `PipelineContext` is reused

**Evidence:** `flowforge/core.py:31-41` makes `outputs` and `execution_order` caller-supplied mutable state. `flowforge/core.py:94-104` writes an output only after the task succeeds and appends execution order only after success; the failure path raises without clearing an existing output or recording a failed/invalid state. A supplied context is explicitly supported by `tests/test_core.py:42-46`, but the tests cover only a successful run.

**Observed behavior:** With `PipelineContext(outputs={"bad": "stale-from-prior-run"}, execution_order=["bad"])`, a task that raises still leaves `ctx.output("bad") == "stale-from-prior-run"` after `Runner.run` raises. This can cause a caller to mistake an artifact from a previous run for the failed run's output. The same context also retains a misleading execution history.

**Why it matters for data science:** A failed feature build, model fit, or evaluation can leave a seemingly available artifact that downstream code, reporting, or a retry reuses accidentally. The engine does not provide transactional run semantics or an unambiguous failed-artifact state.

**Concrete fix:** Treat each invocation as a distinct run. Either reject a non-empty context or reset run-owned outputs and execution history before execution. Prefer a `RunResult`/run manifest with per-task states (`pending`, `running`, `succeeded`, `failed`, `skipped`), and mark all outputs from a failed run invalid. Add a regression test that reuses a context containing a prior output and verifies that a failed task cannot expose it.

### [HIGH] Artifact lineage and data contracts are not represented or enforced

**Evidence:** `PipelineContext` contains only raw `outputs`, free-form `metadata`, and an execution list (`flowforge/core.py:30-41`). `Runner` stores the raw return value under the task name (`flowforge/core.py:97-103`); it does not record run ID, producer, dependency versions, input artifact IDs, content hashes, schema, or validation results. The raw mutable values remain directly accessible through `context.outputs`.

**Why it matters for data science:** The engine cannot answer which exact inputs produced a dataset/model/report, whether an artifact was changed after production, or whether a cached/retrieved artifact is compatible with the current run. A downstream task can also mutate a list/dict returned by an upstream task, changing the upstream value without any lineage event. This prevents trustworthy auditability and makes accidental data leakage or feature drift difficult to detect.

**Concrete fix:** Introduce an immutable artifact envelope containing `artifact_id`, producer task, run ID, parent artifact IDs, content/schema fingerprints, and creation metadata. Expose read-only artifact access rather than the public mutable dictionary, validate declared input/output schemas at task boundaries, and persist the manifest alongside serialized artifacts. Record hashes for file/data inputs and the code/config/environment fingerprints needed to reproduce a run.

### [HIGH] Declared dependencies do not constrain actual data access

**Evidence:** Dependency names are used only to build scheduler edges (`flowforge/core.py:67-83`). Task functions receive the whole shared context (`flowforge/core.py:15-18`, `flowforge/core.py:97-100`) and can call `ctx.output` for any task, regardless of `depends_on`. No access is checked against the current task's declaration.

**Observed behavior:** A `consumer` with no declared dependency on `source` fails if inserted before `source`, because it reads `ctx.output("source")` before that task runs. If insertion order happens to put `source` first, the same undeclared access succeeds. Thus correctness depends on incidental graph insertion order rather than the data dependency expressed by the pipeline.

**Concrete fix:** Make task inputs explicit and pass only declared inputs (for example, `function(inputs, context)`), or add a task-scoped context that rejects reads of undeclared artifacts. Validate that every consumed artifact is declared before execution. Add tests for both insertion orders and for undeclared reads.

### [MEDIUM] Reproducibility is only a scheduler property, not a pipeline guarantee

**Evidence:** `DAG.topological_order` is stable for a fixed `OrderedDict` insertion order (`flowforge/core.py:44-55`, `67-87`), but `Task.function` is an unrestricted Python callable (`flowforge/core.py:14-27`) and the runner captures no random seed, clock, environment, dependency version, input snapshot, or code/config fingerprint (`flowforge/core.py:90-104`). The README's production-limitations section acknowledges in-memory, non-persistent execution and no cache/resume (`README.md:54-64`).

**Observed behavior:** Two runs of a task returning `random.random()` produced different values when invoked through the same runner. The bundled example repeats because its input is a literal list (`examples/basic_pipeline.py:11-12`), not because FlowForge controls randomness or inputs.

**Concrete fix:** Define a reproducibility contract: accept a run seed and deterministic clock/config, seed supported RNGs at run start, snapshot or hash inputs, record Python/package/platform versions and task source/config fingerprints, and use a canonical tie-break policy (such as task name) when insertion order is not intentionally part of the API. Persist this manifest and make nondeterministic/external-input tasks declare their provenance.

### [MEDIUM] The data-science example hides a weak missing-data policy and has no validation

**Evidence:** `examples/basic_pipeline.py:11-12` hard-codes three rows and does not validate schema, types, ranges, or missingness. `examples/basic_pipeline.py:15-18` replaces `age` with zero using `row["age"] or 0`, conflating missing values with a legitimate falsy value and silently applying an undocumented imputation rule. `examples/basic_pipeline.py:20-22` assumes every score is numeric and divides by `len(rows)` without handling an empty input.

**Why it matters for data science:** The example demonstrates task wiring, but it does not demonstrate production-safe ingestion, data-quality gates, or a defensible transformation. Silent imputation can bias downstream analysis; malformed or empty data fails late and without a task-level data-quality explanation.

**Concrete fix:** Add an explicit schema/data-quality task before cleaning, distinguish `None`/NA from valid zero, document and parameterize the imputation policy, validate score types/ranges, and define behavior for empty input. Include assertions or tests for missing values, valid zero ages, malformed rows, and empty datasets. Keep the sample input deterministic but show the run seed/provenance in the resulting report.

### [LOW] Cycle diagnostics can name downstream nodes as if they were in the cycle

**Evidence:** On failure, `flowforge/core.py:84-86` reports every node with nonzero remaining indegree. In Kahn's algorithm, that set includes nodes downstream of a cycle, not only nodes participating in one. For a cycle `a <-> b` with `c` depending on `a`, the message includes `a`, `b`, and `c`.

**Concrete fix:** After detecting incomplete ordering, run a DFS/Tarjan strongly connected-components pass and report only cyclic components, while separately identifying blocked descendants. Add a test covering a cycle with a downstream node.

### [LOW] Task input typing is permissive enough to create malformed dependency graphs

**Evidence:** `Task.__init__` converts any iterable directly to a tuple (`flowforge/core.py:20-27`). Passing a single string such as `depends_on="source"` silently becomes `("s", "o", "u", "r", "c", "e")`; non-string dependency values can also reach validation, where `sorted(unknown)` may raise a comparison `TypeError` rather than a `DAGError` (`flowforge/core.py:59-62`).

**Concrete fix:** Reject a string as the dependency collection unless the API intentionally supports one name, validate every dependency is a non-empty string, and normalize/deduplicate dependencies with a clear error for duplicates.

## Test and verification results

Executed from the project root:

- `python3 -m unittest discover -s tests -v`: **PASS**, 16 tests.
- `python3 examples/basic_pipeline.py`: **PASS**, output order `load_data -> validate_data -> clean_data -> summarize -> report`; mean score `83.3`, with success and failure manifests exported.
- `python3 -m compileall -q flowforge examples tests`: **PASS**.
- Targeted checks reproduced stale output after a failed reused-context run, failure from an undeclared dependency, and differing values from an unseeded random task.

The README commands use `python`; this environment provides `python3` but no `python` executable, so the documented commands were run with the available interpreter name.

## Recommended priority

1. Establish isolated, explicitly tracked run state and prevent stale outputs after failure.
2. Add explicit inputs plus artifact envelopes/lineage and schema/data-quality validation.
3. Define and implement the reproducibility manifest/seed contract.
4. Strengthen the example and add regression tests for failure propagation, hidden dependencies, context reuse, artifact mutation, empty/malformed data, and cycle diagnostics.
