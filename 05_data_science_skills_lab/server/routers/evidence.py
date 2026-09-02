from fastapi import APIRouter, Query

from server.schemas import RowFilters
from server.services.evidence import evidence_payload, filtered_rows, module_payload

router = APIRouter(prefix="/api", tags=["evidence"])


@router.get("/summary")
def summary():
    return evidence_payload()


@router.get("/cleaning")
def cleaning():
    return module_payload("data_quality")


@router.get("/classification")
def classification():
    return module_payload("classification")


@router.get("/regression")
def regression():
    return module_payload("regression")


@router.get("/clustering")
def clustering():
    return module_payload("clustering")


@router.get("/rows")
def rows(
    plan: str = Query("all"),
    renewal: str = Query("all"),
    cluster: str = Query("all"),
    limit: int = Query(100, ge=1, le=1000),
):
    return filtered_rows(RowFilters(plan=plan, renewal=renewal, cluster=cluster), limit)
