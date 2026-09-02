"""Use-case functions for serving validated evidence."""
from ml.artifacts import load_metrics

def metrics_payload() -> dict:
    return load_metrics()

def behavior_payload() -> dict:
    return load_metrics().get("behavior", {})
