"""FastAPI API for the NYC taxi experiment."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.model import estimate, load_feature_importance, load_metrics, prediction_slice  # noqa: E402

app = FastAPI(title="Project 01 · NYC Taxi Trip Duration API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class EstimateRequest(BaseModel):
    pickup_latitude: float = Field(..., ge=-90, le=90)
    pickup_longitude: float = Field(..., ge=-180, le=180)
    dropoff_latitude: float = Field(..., ge=-90, le=90)
    dropoff_longitude: float = Field(..., ge=-180, le=180)
    pickup_datetime: str
    passenger_count: int = Field(default=1, ge=1, le=10)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "project": "01_nyc_taxi_trip_prediction", "artifact_source": "outputs/"}


@app.get("/api/experiment")
def experiment() -> dict:
    return load_metrics()


@app.get("/api/feature-importance")
def feature_importance() -> list[dict]:
    return load_feature_importance()


@app.get("/api/predictions")
def predictions(
    slice: str = Query(default="all"),
    population: str = Query(default="primary"),
) -> dict:
    try:
        return prediction_slice(slice, population)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/estimate")
def estimate_trip(request: EstimateRequest) -> dict:
    try:
        payload = request.model_dump() if hasattr(request, "model_dump") else request.dict()
        return estimate(payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
