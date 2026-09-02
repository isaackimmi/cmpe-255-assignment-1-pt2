from fastapi import APIRouter, HTTPException, Query

from server.schemas import EstimateRequest, EstimateResponse, HealthResponse, PredictionSliceResponse
from server.services import experiment_service

router = APIRouter(prefix="/api", tags=["experiment"])


@router.get("/health")
def health() -> HealthResponse:
    return {"status": "ok", "project": "01_nyc_taxi_trip_prediction", "artifact_source": "outputs/"}


@router.get("/experiment")
def experiment() -> dict:
    return experiment_service.experiment()


@router.get("/feature-importance")
def feature_importance() -> list[dict]:
    return experiment_service.feature_importance()


@router.get("/predictions")
def predictions(slice: str = Query(default="all"), population: str = Query(default="primary")) -> PredictionSliceResponse:
    try:
        return experiment_service.predictions(slice, population)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/estimate")
def estimate_trip(request: EstimateRequest) -> EstimateResponse:
    try:
        payload = request.model_dump() if hasattr(request, "model_dump") else request.dict()
        return experiment_service.estimate_trip(payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
