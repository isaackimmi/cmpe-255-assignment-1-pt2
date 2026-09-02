"""Application-facing evidence queries and error translation."""

from fastapi import HTTPException

from ml.contracts import ArtifactContractError
from ml.service import build_evidence
from server.schemas import RowFilters


def evidence_payload() -> dict:
    try:
        return build_evidence()
    except (FileNotFoundError, ArtifactContractError, ValueError, OSError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def module_payload(module: str) -> dict:
    data = evidence_payload()
    if module == "regression":
        return {
            "metrics": data["metrics"]["regression"],
            "predictions": data["summary"]["regression_predictions"],
            "excluded_targets": data["summary"]["regression_excluded_test_targets"],
        }
    if module == "clustering":
        return {"metrics": data["metrics"]["clustering"], "rows": data["summary"]["analysis_rows"]}
    return data["metrics"][module]


def filtered_rows(filters: RowFilters, limit: int) -> dict:
    filters.validate()
    rows = evidence_payload()["summary"]["analysis_rows"]
    if filters.plan != "all":
        rows = [row for row in rows if row["plan"] == filters.plan]
    if filters.renewal != "all":
        rows = [row for row in rows if str(row["renewed"]) == filters.renewal]
    if filters.cluster != "all":
        rows = [row for row in rows if str(row.get("cluster")) == filters.cluster]
    return {"count": len(rows), "rows": rows[:limit], "filters": filters.__dict__}
