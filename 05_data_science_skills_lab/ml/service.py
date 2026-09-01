"""Stable, read-only analytical service boundary used by FastAPI."""

import sys
from pathlib import Path

from .artifacts import load_artifacts

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from skills_lab import load_clean  # noqa: E402


def build_evidence(root: Path = PROJECT_ROOT) -> dict:
    """Return checked-in evidence and source metadata without retraining."""
    root = Path(root)
    metrics, summary = load_artifacts(root)
    csv_path = root / "data" / "customer_health.csv"
    rows, duplicates = load_clean(csv_path, impute=False)
    return {
        "metrics": metrics,
        "summary": summary,
        "source": {"rows": len(rows), "duplicates": duplicates, "path": csv_path.name},
    }
