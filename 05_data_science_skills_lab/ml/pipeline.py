"""Compatibility facade for the modular, read-only ML artifact boundary."""

from pathlib import Path

from .artifacts import artifact_paths as _artifact_paths, load_artifacts
from .contracts import ArtifactContractError
from .service import PROJECT_ROOT, build_evidence


def artifact_paths(root=PROJECT_ROOT):
    return _artifact_paths(Path(root))


def run(root=PROJECT_ROOT):
    """Return checked-in evidence; this does not silently retrain models."""
    return build_evidence(Path(root))


__all__ = ["ArtifactContractError", "artifact_paths", "load_artifacts", "run"]
