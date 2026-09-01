"""Stable ML boundary for the E2E application.

The original experiment remains the source of truth. This adapter gives the
FastAPI layer one narrow entry point and keeps model execution out of the
browser. It intentionally does not silently retrain during API reads.
"""

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from skills_lab import load_clean  # noqa: E402


class ArtifactContractError(ValueError):
    """Raised when checked-in evidence is missing or structurally invalid."""


def artifact_paths(root=PROJECT_ROOT):
    root = Path(root)
    return root / "artifacts" / "metrics.json", root / "artifacts" / "summary.json"


def load_artifacts(root=PROJECT_ROOT):
    metrics_path, summary_path = artifact_paths(root)
    if not metrics_path.exists() or not summary_path.exists():
        raise FileNotFoundError("Missing metrics.json or summary.json; run python3 run_lab.py before starting the API")
    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ArtifactContractError("Artifact JSON is corrupted; run python3 run_lab.py to regenerate metrics.json and summary.json") from exc
    if not isinstance(metrics, dict) or not isinstance(summary, dict):
        raise ArtifactContractError("Artifact contract requires JSON objects; run python3 run_lab.py to regenerate outputs")
    required_metrics = {"data_quality", "eda", "regression", "classification", "clustering", "reproducibility"}
    missing_metrics = sorted(required_metrics - set(metrics))
    if missing_metrics:
        raise ArtifactContractError(f"metrics.json is missing required sections: {', '.join(missing_metrics)}; run python3 run_lab.py")
    if not isinstance(summary.get("analysis_rows"), list) or not isinstance(summary.get("regression_predictions"), list):
        raise ArtifactContractError("summary.json must contain analysis_rows and regression_predictions lists; run python3 run_lab.py")
    return metrics, summary


def run(root=PROJECT_ROOT):
    """Return checked-in artifacts plus a compact source-data contract."""
    metrics, summary = load_artifacts(root)
    csv_path = Path(root) / "data" / "customer_health.csv"
    rows, duplicates = load_clean(csv_path, impute=False)
    return {"metrics": metrics, "summary": summary, "source": {"rows": len(rows), "duplicates": duplicates, "path": str(csv_path.name)}}
