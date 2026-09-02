from fastapi import APIRouter
from server.services.artifacts import repository

router = APIRouter(prefix="/api", tags=["evidence"])

@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "segmentation-api", "artifacts": repository.root.exists(), "evidence_valid": repository.status()["valid"]}

@router.get("/evidence-status")
def evidence_status() -> dict: return repository.status()

@router.get("/manifest")
def manifest() -> dict: return repository.require_valid()["manifest"]

@router.get("/summary")
def summary() -> dict:
    repository.require_valid()
    return repository.read_json("summary.json")

@router.get("/validation")
def validation() -> list[dict]:
    repository.require_valid()
    return repository.read_csv("validation_scores.csv")
