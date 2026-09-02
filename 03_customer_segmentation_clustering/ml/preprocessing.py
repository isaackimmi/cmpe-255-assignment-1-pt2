from src.experiment import _raw_values

def transform_for_distance(frame, fitted: dict, preprocessing: str):
    """Apply the exact canonical feature transform before centroid distances."""
    return fitted["scaler"].transform(_raw_values(frame, preprocessing))
