"""Compatibility facade for the modular artifact-backed ML layer."""

from ml.artifacts import load_feature_importance, load_metrics, load_predictions
from ml.estimator import estimate
from ml.slicing import prediction_slice

__all__ = ["estimate", "load_feature_importance", "load_metrics", "load_predictions", "prediction_slice"]
