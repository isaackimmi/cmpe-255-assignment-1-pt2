from .artifacts import load_predictions
from .numeric import finite
from .scoring import score


def matches_slice(row: dict, slice_name: str, distance_median: float) -> bool:
    if slice_name in ("all", ""):
        return True
    if slice_name == "rush":
        if row.get("is_rush_hour") not in (None, ""):
            return row.get("is_rush_hour") in ("1", "1.0", "true", "True")
        hour = finite(row.get("hour"), "hour")
        return 7 <= hour <= 9 or 16 <= hour <= 19
    if slice_name == "off_peak":
        return not matches_slice(row, "rush", distance_median)
    if slice_name == "weekend":
        if row.get("is_weekend") not in (None, ""):
            return row.get("is_weekend") in ("1", "1.0", "true", "True")
        return finite(row.get("weekday"), "weekday") >= 5
    if slice_name == "weekday":
        return not matches_slice(row, "weekend", distance_median)
    distance = finite(row.get("distance_miles"), "distance_miles")
    if slice_name == "short":
        return distance < distance_median
    if slice_name == "long":
        return distance >= distance_median
    raise ValueError(f"unknown_slice:{slice_name}")


def prediction_slice(slice_name: str = "all", population: str = "primary") -> dict:
    all_rows = load_predictions()
    distances = [finite(row.get("distance_miles"), "distance_miles") for row in all_rows]
    distance_median = sorted(distances)[len(distances) // 2]
    rows = all_rows
    if population == "robust":
        rows = [row for row in rows if row.get("robust_inlier") in ("1", "1.0", "true", "True")]
    elif population != "primary":
        raise ValueError(f"unknown_population:{population}")
    rows = [row for row in rows if matches_slice(row, slice_name, distance_median)]
    for row in rows:
        row["actual"] = finite(row.get("actual_seconds"), "actual_seconds")
        row["prediction"] = finite(row.get("predicted_seconds"), "predicted_seconds")
        row["residual_seconds"] = round(row["prediction"] - row["actual"], 3)
    metrics = score(rows)
    baseline_rows = [{"actual": row["actual"], "prediction": finite(row.get("global_median_seconds"), "global_median_seconds")} for row in rows]
    metrics["baseline"] = score(baseline_rows)
    return {"slice": slice_name, "population": population, "distance_boundary_miles": round(distance_median, 4), "metrics": metrics, "rows": rows}
