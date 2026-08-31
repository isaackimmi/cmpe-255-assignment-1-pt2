# FlowForge: Lightweight DAG Engine

FlowForge is a small, dependency-free Python implementation of a directed acyclic graph (DAG) engine for data-science workflows. It models a pipeline as named tasks connected by dependencies, validates the graph before execution, and runs each task once in topological order.

The example pipeline loads observations, cleans them, computes summary statistics, and produces a report. Each task receives a shared `PipelineContext`, making intermediate datasets and metrics explicit and easy to inspect.

## Quick start

From this directory:

```bash
python examples/basic_pipeline.py
python -m unittest discover -s tests -v
```

The example prints the execution order and a small report. No third-party packages are required; Python 3.10+ is recommended.

## Concepts

- `Task`: a named unit of work with a callable and zero or more upstream task names.
- `DAG`: stores tasks, rejects duplicate names and unknown dependencies, and detects cycles.
- `PipelineContext`: shared run state containing task outputs, metadata, and the current execution order.
- `Runner`: validates and executes ready tasks in deterministic topological order. A task runs only after every dependency succeeds.

This maps naturally to data-science work: ingestion precedes validation and feature engineering; features precede model training; training precedes evaluation and publishing. The graph makes dependencies and reproducibility visible rather than relying on manually ordered notebook cells.

## API example

```python
from flowforge import DAG, PipelineContext, Runner, Task

dag = DAG()
dag.add_task(Task("numbers", lambda ctx: [1, 2, 3]))
dag.add_task(Task("total", lambda ctx: sum(ctx.output("numbers")), depends_on=["numbers"]))

context = Runner(dag).run()
assert context.output("total") == 6
```

## Design choices and deviations

This is intentionally a teaching-scale implementation. It differs from production workflow systems in several ways:

- Execution is in-process and sequential; there are no workers, retries, distributed scheduling, or parallel branches.
- Outputs live in memory for one run; there is no artifact store, cache, serialization, or resume support.
- Tasks are Python callables, not containerized commands or declarative operators.
- Validation covers structural correctness (names, dependencies, cycles); schema checks and data-quality rules remain task responsibilities.
- Failure is fail-fast and leaves the exception attached to the task name; production systems would typically add retry and observability policies.

These constraints keep the core DAG semantics readable and runnable for the assignment while preserving the important workflow ideas: explicit dependencies, deterministic scheduling, validation before work, and inspectable intermediate results.
## Integration verification

- **Prompt alignment:** Public Project 09 asks for an end-to-end demonstration; this reproduction focuses on reusable DAG semantics and a multi-step data pipeline.
- **Results/artifacts:** Example order was `load_data -> clean_data -> summarize -> report`; unittest passed 6/6.
- **Issue/resolution:** External skills, frontend, and distributed runtime were not needed to validate core DAG behavior.
