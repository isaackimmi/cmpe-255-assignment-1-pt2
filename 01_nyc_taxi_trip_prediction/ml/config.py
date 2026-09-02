from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = PROJECT_ROOT / "outputs"
SERVICE_AREA = {"longitude": (-74.3, -73.65), "latitude": (40.45, 40.95)}
REQUIRED_PREDICTION_COLUMNS = {
    "pickup_datetime", "actual_seconds", "predicted_seconds", "global_median_seconds",
    "distance_miles", "hour", "weekday", "is_weekend", "robust_inlier",
}
