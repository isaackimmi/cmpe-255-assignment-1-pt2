from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any
from fastapi import HTTPException
from src.experiment import validate_artifacts
from server.config import ARTIFACTS

class ArtifactRepository:
    def __init__(self, root: Path = ARTIFACTS): self.root = root

    def status(self) -> dict:
        try:
            result = validate_artifacts(self.root)
            path = self.root / "manifest.json"
            manifest = json.loads(path.read_text()) if path.exists() else None
            return {"valid": bool(result["valid"]), "errors": result["errors"], "manifest": manifest}
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return {"valid": False, "errors": [f"artifact_parse_error: {exc}"], "manifest": None}

    def require_valid(self) -> dict:
        status = self.status()
        if not status["valid"]: raise HTTPException(status_code=503, detail={"code": "artifact_invalid", "errors": status["errors"]})
        return status

    def read_json(self, name: str) -> Any:
        try: return json.loads((self.root / name).read_text())
        except FileNotFoundError as exc: raise HTTPException(status_code=503, detail={"code": "artifact_missing", "artifact": name}) from exc
        except (OSError, json.JSONDecodeError) as exc: raise HTTPException(status_code=503, detail={"code": "artifact_invalid", "artifact": name}) from exc

    def read_csv(self, name: str) -> list[dict[str, Any]]:
        try:
            with (self.root / name).open(newline="") as handle: rows = list(csv.DictReader(handle))
        except FileNotFoundError as exc: raise HTTPException(status_code=503, detail={"code": "artifact_missing", "artifact": name}) from exc
        except OSError as exc: raise HTTPException(status_code=503, detail={"code": "artifact_invalid", "artifact": name}) from exc
        return [{key: _coerce(value) for key, value in row.items()} for row in rows]

def _coerce(value: str) -> Any:
    try: return float(value) if "." in value else int(value)
    except (ValueError, TypeError): return value

repository = ArtifactRepository()
