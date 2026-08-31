"""A small data-science-style pipeline using FlowForge."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flowforge import DAG, PipelineContext, Runner, Task


def load_data(ctx: PipelineContext) -> list[dict]:
    return [{"age": 22, "score": 81}, {"age": None, "score": 74}, {"age": 31, "score": 95}]


def clean_data(ctx: PipelineContext) -> list[dict]:
    rows = ctx.output("load_data")
    return [{**row, "age": row["age"] or 0} for row in rows]


def summarize(ctx: PipelineContext) -> dict:
    rows = ctx.output("clean_data")
    return {"count": len(rows), "mean_score": sum(row["score"] for row in rows) / len(rows)}


def report(ctx: PipelineContext) -> str:
    summary = ctx.output("summarize")
    return f"Processed {summary['count']} rows; mean score={summary['mean_score']:.1f}"


def build_pipeline() -> DAG:
    dag = DAG()
    dag.add_task(Task("load_data", load_data))
    dag.add_task(Task("clean_data", clean_data, ["load_data"]))
    dag.add_task(Task("summarize", summarize, ["clean_data"]))
    dag.add_task(Task("report", report, ["summarize"]))
    return dag


if __name__ == "__main__":
    context = Runner(build_pipeline()).run()
    print("Execution order:", " -> ".join(context.execution_order))
    print(context.output("report"))
