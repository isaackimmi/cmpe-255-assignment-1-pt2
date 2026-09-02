from fastapi import APIRouter
from server.services.evidence import behavior_payload, metrics_payload

router = APIRouter(tags=["evidence"])

@router.get("/metrics")
def metrics() -> dict:
    return metrics_payload()

@router.get("/behavior")
def behavior() -> dict:
    return behavior_payload()
