"""Contracts shared by the artifact repository and API service."""


class ArtifactContractError(ValueError):
    """Raised when checked-in evidence is missing or structurally invalid."""


REQUIRED_METRIC_SECTIONS = {
    "data_quality", "eda", "regression", "classification", "clustering", "reproducibility"
}
