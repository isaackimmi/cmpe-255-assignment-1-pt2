import pandas as pd
from ml.contracts import ordered_feature_values
from ml.preprocessing import transform_for_distance
from src.experiment import FEATURES, fit_segmenter, make_dataset, score_customers

def score_observation(values: dict, preprocessing: str = "standard", k: int = 3) -> dict:
    """Fit and apply the canonical deterministic teaching pipeline."""
    incoming = pd.DataFrame([ordered_feature_values(values)], columns=FEATURES)
    fitted = fit_segmenter(make_dataset(), preprocessing, k)
    cluster = int(score_customers(incoming, fitted).iloc[0])
    distances = [float(value) for value in fitted["model"].transform(transform_for_distance(incoming, fitted, preprocessing))[0]]
    ordered = sorted(distances)
    return {"cluster": cluster, "preprocessing": preprocessing, "k": k, "distances": [round(value, 6) for value in distances], "nearest_distance": round(ordered[0], 6), "assignment_margin": round(ordered[1] - ordered[0], 6), "note": "geometry diagnostics, not a probability"}
