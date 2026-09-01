from fastapi import APIRouter, HTTPException, Query
from ml.pipeline import score_observation
from server.schemas import Observation
from server.services.artifacts import repository
from server.services.profiles import build_profiles

router = APIRouter(prefix="/api", tags=["segmentation"])

@router.get("/points")
def points(cluster: int | None = Query(default=None, ge=0)) -> list[dict]:
    repository.require_valid()
    rows = repository.read_csv("explorer_points.csv")
    return [row for row in rows if cluster is None or row.get("cluster") == cluster]

@router.get("/profiles")
def profiles() -> list[dict]:
    repository.require_valid()
    rows = repository.read_csv("customer_segments.csv")
    return build_profiles(rows, repository.read_json("summary.json")["features"])

@router.post("/score")
def score(observation: Observation) -> dict:
    selected = repository.require_valid()["manifest"]
    try: return score_observation(observation.model_dump(), preprocessing=selected["selected_preprocessing"], k=int(selected["selected_k"]))
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
