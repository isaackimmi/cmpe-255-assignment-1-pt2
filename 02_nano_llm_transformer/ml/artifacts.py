"""Loading and enrichment of checked-in evidence artifacts."""
from __future__ import annotations
import json
from pathlib import Path
from .errors import ArtifactInvalid, ArtifactMissing
from .paths import METRICS_PATH
from .validation import validate_artifact

def load_metrics(path: Path = METRICS_PATH) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ArtifactMissing("metrics.json is not available; regenerate the canonical artifact") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactInvalid("metrics.json is unreadable or invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ArtifactInvalid("metrics.json must contain a JSON object")
    validate_artifact(payload)
    return {**payload, "artifact_backend": payload.get("backend", "unknown"), "inference_backend": "stdlib_char_ngram" if payload.get("backend") == "stdlib_char_ngram" else "unsupported"}
