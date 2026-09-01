"""Read and validate checked-in analytical artifacts."""

import json
from pathlib import Path

from .contracts import ArtifactContractError, REQUIRED_METRIC_SECTIONS


def _require_mapping(value, path: str) -> dict:
    if not isinstance(value, dict):
        raise ArtifactContractError(f"{path} must be an object")
    return value


def _require_number(mapping: dict, key: str, path: str) -> None:
    value = mapping.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ArtifactContractError(f"{path}.{key} must be numeric")


def _validate_nested_metrics(metrics: dict) -> None:
    quality = _require_mapping(metrics["data_quality"], "metrics.data_quality")
    for key in ("raw_rows", "clean_rows", "duplicates_removed", "missing_values_imputed"):
        _require_number(quality, key, "metrics.data_quality")
    _require_mapping(quality.get("missing_values_by_column"), "metrics.data_quality.missing_values_by_column")

    classification = _require_mapping(metrics["classification"], "metrics.classification")
    for key in ("accuracy", "f1", "balanced_accuracy", "precision", "recall", "specificity"):
        _require_number(classification, key, "metrics.classification")
    matrix = classification.get("confusion_matrix")
    if not isinstance(matrix, list) or len(matrix) != 2 or any(not isinstance(row, list) or len(row) != 2 for row in matrix):
        raise ArtifactContractError("metrics.classification.confusion_matrix must be a 2x2 list")

    regression = _require_mapping(metrics["regression"], "metrics.regression")
    for key in ("mae", "mean_baseline_mae", "r2", "scored_rows"):
        _require_number(regression, key, "metrics.regression")

    clustering = _require_mapping(metrics["clustering"], "metrics.clustering")
    for key in ("k", "silhouette"):
        _require_number(clustering, key, "metrics.clustering")
    centers = clustering.get("centers")
    if not isinstance(centers, list) or any(not isinstance(center, list) or len(center) != 2 for center in centers):
        raise ArtifactContractError("metrics.clustering.centers must contain two-dimensional centers")


def artifact_paths(root: Path) -> tuple[Path, Path]:
    artifact_root = Path(root) / "artifacts"
    return artifact_root / "metrics.json", artifact_root / "summary.json"


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ArtifactContractError(
            f"{path.name} is corrupted; run python3 run_lab.py to regenerate artifacts"
        ) from exc
    if not isinstance(value, dict):
        raise ArtifactContractError(f"{path.name} must contain a JSON object")
    return value


def load_artifacts(root: Path) -> tuple[dict, dict]:
    metrics_path, summary_path = artifact_paths(root)
    if not metrics_path.exists() or not summary_path.exists():
        raise FileNotFoundError(
            "Missing metrics.json or summary.json; run python3 run_lab.py before starting the API"
        )
    metrics, summary = _read_json(metrics_path), _read_json(summary_path)
    missing = sorted(REQUIRED_METRIC_SECTIONS - set(metrics))
    if missing:
        raise ArtifactContractError(
            f"metrics.json is missing required sections: {', '.join(missing)}; run python3 run_lab.py"
        )
    _validate_nested_metrics(metrics)
    if not isinstance(summary.get("analysis_rows"), list) or not isinstance(
        summary.get("regression_predictions"), list
    ):
        raise ArtifactContractError(
            "summary.json must contain analysis_rows and regression_predictions lists; run python3 run_lab.py"
        )
    for index, row in enumerate(summary["analysis_rows"]):
        if not isinstance(row, dict) or not {"customer_id", "plan", "renewed", "cluster"}.issubset(row):
            raise ArtifactContractError(f"summary.analysis_rows[{index}] has an invalid row contract")
    for index, row in enumerate(summary["regression_predictions"]):
        if not isinstance(row, dict) or not {"customer_id", "actual_usage", "predicted_usage"}.issubset(row):
            raise ArtifactContractError(f"summary.regression_predictions[{index}] has an invalid row contract")
    return metrics, summary
