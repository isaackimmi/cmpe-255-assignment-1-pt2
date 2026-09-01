"""Backward-compatible public façade for the modular ML adapter."""
from .artifacts import load_metrics
from .errors import ArtifactError, ArtifactInvalid, ArtifactMismatch, ArtifactMissing, BackendUnsupported
from .inference import build_model, generate, probabilities
from .validation import validate_artifact

__all__ = [
    "ArtifactError", "ArtifactInvalid", "ArtifactMismatch", "ArtifactMissing",
    "BackendUnsupported", "build_model", "generate", "load_metrics",
    "probabilities", "validate_artifact",
]
