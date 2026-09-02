import math


def haversine_miles(pickup_lat: float, pickup_lon: float, dropoff_lat: float, dropoff_lon: float) -> float:
    delta_latitude = math.radians(dropoff_lat - pickup_lat)
    delta_longitude = math.radians(dropoff_lon - pickup_lon)
    value = math.sin(delta_latitude / 2) ** 2 + math.cos(math.radians(pickup_lat)) * math.cos(math.radians(dropoff_lat)) * math.sin(delta_longitude / 2) ** 2
    return 3958.8 * 2 * math.asin(min(1, math.sqrt(max(0, value))))
