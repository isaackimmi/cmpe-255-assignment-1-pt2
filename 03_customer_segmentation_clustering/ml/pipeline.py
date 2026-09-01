"""Thin adapter exposing the reproducible experiment as a service boundary."""
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path: sys.path.insert(0, str(PROJECT))

from src.experiment import FEATURES, SEED, fit_segmenter, make_dataset, score_customers  # noqa: E402

def score_observation(values: dict, preprocessing: str = "standard", k: int = 3) -> dict:
    """Apply the canonical scoring path for either measured preprocessing variant."""
    import pandas as pd
    frame = make_dataset()
    fitted = fit_segmenter(frame, preprocessing, k)
    incoming = pd.DataFrame([values], columns=FEATURES)
    assignments = score_customers(incoming, fitted)
    transformed = fitted["scaler"].transform(__import__("src.experiment", fromlist=["_raw_values"])._raw_values(incoming, preprocessing))
    distances = fitted["model"].transform(transformed)[0]
    ordered = sorted(float(distance) for distance in distances)
    return {"cluster": int(assignments.iloc[0]), "preprocessing": preprocessing, "k": k, "distances": [round(float(x), 6) for x in distances], "nearest_distance": round(ordered[0], 6), "assignment_margin": round(ordered[1] - ordered[0], 6), "note": "geometry diagnostics, not a probability"}

__all__ = ["FEATURES", "SEED", "fit_segmenter", "make_dataset", "score_customers", "score_observation"]
