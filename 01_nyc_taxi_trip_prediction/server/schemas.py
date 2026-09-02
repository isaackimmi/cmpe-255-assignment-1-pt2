from pydantic import BaseModel, Field
from typing import TypedDict


class EstimateRequest(BaseModel):
    pickup_latitude: float = Field(..., ge=-90, le=90)
    pickup_longitude: float = Field(..., ge=-180, le=180)
    dropoff_latitude: float = Field(..., ge=-90, le=90)
    dropoff_longitude: float = Field(..., ge=-180, le=180)
    pickup_datetime: str
    passenger_count: int = Field(default=1, ge=1, le=10)


class HealthResponse(TypedDict):
    status: str
    project: str
    artifact_source: str


class PredictionSliceResponse(TypedDict):
    slice: str
    population: str
    distance_boundary_miles: float
    metrics: dict
    rows: list[dict]


class EstimateResponse(TypedDict):
    estimated_duration_seconds: int
    estimated_duration_minutes: float
    distance_miles: float
    is_rush_hour: bool
    mode: str
    disclaimer: str
