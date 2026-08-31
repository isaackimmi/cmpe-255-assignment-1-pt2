# FlowForge: Lightweight DAG Engine

FlowForge is a small, dependency-free Python implementation of a directed acyclic graph (DAG) engine for data-science workflows. It models a pipeline as named tasks connected by dependencies, validates the graph before execution, and runs each task once in topological order.

The example pipeline loads observations, validates their quality, cleans them, computes summary statistics, and produces a report. Each task receives a task-scoped context: it can inspect only the artifacts named in its `depends_on` contract.

## Quick start

From this directory:

```bash
python examples/basic_pipeline.py
python -m unittest discover -s tests -v
```

The example prints the execution order and a small report with its run seed. No third-party packages are required; Python 3.10+ is recommended.

## Browser UI companion

The `ui/` directory contains a dependency-light static browser companion for the example pipeline. It visualizes the same four tasks, their dependency edges, execution order, task outputs, and the data-science story behind each step. The UI demo is for explanation and interaction; the Python engine remains the source of truth.

To launch it locally, from this directory run:

```bash
python -m http.server 8000
```

Then open <http://localhost:8000/ui/> and click **Run demo**. Select any graph node to inspect its dependencies and latest output, or use **Replay demo** and **Reset** to repeat the visualization. Stop the server with `Ctrl-C` when finished.

The browser companion uses only local HTML, CSS, and JavaScript—there is no frontend build step or package installation. For authoritative execution and tests, use the Python commands in [Quick start](#quick-start).

## Concepts

- `Task`: a named unit of work with a callable, zero or more upstream task names, and optional configuration. A dependency collection must contain unique, non-empty strings.
- `DAG`: stores tasks, rejects duplicate names and unknown dependencies, and detects cycles while distinguishing cyclic nodes from blocked descendants.
- `PipelineContext`: run state containing detached output snapshots, immutable `Artifact` lineage envelopes, metadata, execution status, and a run manifest. Reusing a context starts a fresh run and cannot expose stale outputs after failure.
- `TaskContext`: the scoped view passed to a task. Reading an undeclared artifact raises `DependencyError`; task results are copied at the boundary.
- `Runner`: validates and executes tasks in deterministic topological order. Optional `seed`, `config`, and `clock` arguments are recorded in the manifest; supported random generators are seeded at run start.

This maps naturally to data-science work: ingestion precedes validation and feature engineering; features precede model training; training precedes evaluation and publishing. The graph makes dependencies and reproducibility visible rather than relying on manually ordered notebook cells.

## API example

```python
from flowforge import DAG, PipelineContext, Runner, Task

dag = DAG()
dag.add_task(Task("numbers", lambda ctx: [1, 2, 3]))
dag.add_task(Task("total", lambda ctx: sum(ctx.output("numbers")), depends_on=["numbers"]))

context = Runner(dag).run(seed=255, config={"experiment": "demo"})
assert context.output("total") == 6
assert context.artifact("total").parent_artifact_ids
assert context.manifest["status"] == "succeeded"
```

## Design choices and deviations

This is intentionally a teaching-scale implementation. It differs from production workflow systems in several ways:

- Execution is in-process and sequential; there are no workers, retries, distributed scheduling, or parallel branches.
- Outputs live in memory for one run; there is no external artifact store, cache, serialization, or resume support. The in-memory artifact envelopes provide lineage and fingerprints for that run.
- Tasks are Python callables, not containerized commands or declarative operators.
- Validation covers structural correctness (names, dependencies, cycles), while task-level schemas and data-quality rules remain task responsibilities. The bundled example demonstrates a dedicated quality gate.
- Failure is fail-fast, invalidates all current-run outputs, and records failed/skipped task states in the manifest; production systems would typically add retry and external observability policies.

These constraints keep the core DAG semantics readable and runnable for the assignment while preserving the important workflow ideas: explicit dependencies, deterministic scheduling, validation before work, and inspectable intermediate results.
## Integration verification

- **Prompt alignment:** Public Project 09 asks for an end-to-end demonstration; this reproduction focuses on reusable DAG semantics and a multi-step data pipeline.
- **Results/artifacts:** Example order was `load_data -> clean_data -> summarize -> report`; unittest passed 6/6.
- **Issue/resolution:** External skills, frontend, and distributed runtime were not needed to validate core DAG behavior.
