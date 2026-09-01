import math
from datetime import datetime

from run_experiment import parse_timestamp

from .config import SERVICE_AREA
from .geo import haversine_miles


def estimate(payload: dict) -> dict:
    try:
        pickup_lat = float(payload["pickup_latitude"])
        pickup_lon = float(payload["pickup_longitude"])
        dropoff_lat = float(payload["dropoff_latitude"])
        dropoff_lon = float(payload["dropoff_longitude"])
        passengers = int(payload.get("passenger_count", 1))
        raw_datetime = str(payload["pickup_datetime"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid_estimate_request") from error
    if not 1 <= passengers <= 10:
        raise ValueError("passenger_count_out_of_range")
    if not all(math.isfinite(value) for value in (pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)):
        raise ValueError("coordinates_must_be_finite")
    if not SERVICE_AREA["latitude"][0] <= pickup_lat <= SERVICE_AREA["latitude"][1] or not SERVICE_AREA["latitude"][0] <= dropoff_lat <= SERVICE_AREA["latitude"][1]:
        raise ValueError("coordinates_outside_service_area")
    if not SERVICE_AREA["longitude"][0] <= pickup_lon <= SERVICE_AREA["longitude"][1] or not SERVICE_AREA["longitude"][0] <= dropoff_lon <= SERVICE_AREA["longitude"][1]:
        raise ValueError("coordinates_outside_service_area")
    try:
        pickup_datetime = parse_timestamp(raw_datetime)
    except ValueError as error:
        raise ValueError(str(error)) from error
    if not datetime(2010, 1, 1) <= pickup_datetime < datetime(2030, 1, 1):
        raise ValueError("timestamp_out_of_coverage")
    distance = haversine_miles(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)
    if distance <= 0:
        raise ValueError("route_distance_must_be_positive")
    if distance >= 100:
        raise ValueError("route_exceeds_100_miles")
    rush = int(7 <= pickup_datetime.hour <= 9 or 16 <= pickup_datetime.hour <= 19)
    seconds = max(60, round(240 + 115 * distance + 90 * rush + 25 * (passengers - 1)))
    return {
        "estimated_duration_seconds": seconds,
        "estimated_duration_minutes": round(seconds / 60, 2),
        "distance_miles": round(distance, 3),
        "is_rush_hour": bool(rush),
        "mode": "deterministic synthetic teaching estimate",
        "disclaimer": "This is a deterministic synthetic teaching estimate that mirrors the fallback generator's directional relationships; it is not a production prediction service.",
    }
