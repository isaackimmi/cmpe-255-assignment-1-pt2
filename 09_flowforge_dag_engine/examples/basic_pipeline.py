"""A small data-science-style pipeline using FlowForge."""

from pathlib import Path
import sys
import math
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flowforge import DAG, PipelineContext, Runner, Task

RUN_SEED = 255
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def load_data(ctx: PipelineContext) -> list[dict]:
    return [{"age": 22, "score": 81}, {"age": None, "score": 74}, {"age": 31, "score": 95}]


def validate_data(ctx: PipelineContext) -> list[dict]:
    rows = ctx.output("load_data")
    if not isinstance(rows, list) or not rows:
        raise ValueError("data-quality validation failed: expected a non-empty list of rows")
    required = {"age", "score"}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError(f"data-quality validation failed: row {index} must contain age and score")
        age = row["age"]
        if age is not None and (
            isinstance(age, bool)
            or not isinstance(age, (int, float))
            or not math.isfinite(age)
            or age < 0
        ):
            raise ValueError(f"data-quality validation failed: row {index} has an invalid age")
        score = row["score"]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise ValueError(f"data-quality validation failed: row {index} has an invalid score")
    return rows


def clean_data(ctx: PipelineContext) -> list[dict]:
    rows = ctx.output("validate_data")
    # The policy is explicit: only missing ages (None) are imputed to zero;
    # a legitimate age of zero remains zero without being conflated with NA.
    return [{**row, "age": 0 if row["age"] is None else row["age"]} for row in rows]


def summarize(ctx: PipelineContext) -> dict:
    rows = ctx.output("clean_data")
    return {"count": len(rows), "mean_score": sum(row["score"] for row in rows) / len(rows)}


def report(ctx: PipelineContext) -> str:
    summary = ctx.output("summarize")
    return f"Processed {summary['count']} rows; mean score={summary['mean_score']:.1f}; run seed={ctx.metadata['seed']}"


def build_pipeline(rows: list[dict] | None = None) -> DAG:
    dag = DAG()
    loader = load_data if rows is None else lambda ctx: rows
    dag.add_task(Task("load_data", loader, config={"source": "inline-observations"}))
    dag.add_task(Task("validate_data", validate_data, ["load_data"]))
    dag.add_task(
        Task(
            "clean_data",
            clean_data,
            ["validate_data"],
            config={"missing_age_policy": "None -> 0; preserve legitimate zero"},
        )
    )
    dag.add_task(Task("summarize", summarize, ["clean_data"]))
    dag.add_task(Task("report", report, ["summarize"]))
    return dag


def write_manifest(context: PipelineContext, filename: str = "run_manifest.json") -> Path:
    """Persist the inspectable run envelope used by the browser companion."""
    ARTIFACT_DIR.mkdir(exist_ok=True)
    path = ARTIFACT_DIR / filename
    path.write_text(json.dumps(context.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    context = Runner(build_pipeline()).run(
        seed=RUN_SEED,
        config={"dataset": "inline-observations", "imputation_policy": "missing_age_to_zero"},
    )
    write_manifest(context)

    # Keep a real failure-state manifest alongside the successful run so the
    # browser can inspect fail-fast and skipped-task behavior without inventing
    # statuses in JavaScript.
    failed_context = PipelineContext()
    try:
        Runner(build_pipeline([{"age": 22, "score": "not-a-number"}])).run(
            failed_context,
            seed=RUN_SEED,
            config={"dataset": "malformed-fixture"},
        )
    except RuntimeError:
        pass
    write_manifest(failed_context, "run_manifest_failure.json")

    print("Execution order:", " -> ".join(context.execution_order))
    print(context.output("report"))
    print("Run manifest:", ARTIFACT_DIR / "run_manifest.json")
    print("Failure manifest:", ARTIFACT_DIR / "run_manifest_failure.json")
