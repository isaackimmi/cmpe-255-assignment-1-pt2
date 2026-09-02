from ml.artifacts import load_feature_importance, load_metrics
from ml.estimator import estimate
from ml.slicing import prediction_slice


class ExperimentService:
    """Application boundary between HTTP concerns and artifact-backed ML logic."""

    def experiment(self) -> dict:
        return load_metrics()

    def feature_importance(self) -> list[dict]:
        return load_feature_importance()

    def predictions(self, slice_name: str, population: str) -> dict:
        return prediction_slice(slice_name, population)

    def estimate_trip(self, payload: dict) -> dict:
        return estimate(payload)


experiment_service = ExperimentService()
