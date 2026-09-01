"""FastAPI evidence and scoring service for Project 03."""
from __future__ import annotations
import csv, json, os
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from ml.pipeline import score_observation
from src.experiment import validate_artifacts

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
app = FastAPI(title="Project 03 Segmentation API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","), allow_methods=["*"], allow_headers=["*"])

class Observation(BaseModel):
    annual_income_k: float = Field(ge=15)
    spend_score: float = Field(ge=1, le=99)
    purchase_frequency: float = Field(ge=0.2)
    avg_order_value: float = Field(ge=5)

def evidence_status() -> dict:
    try:
        result = validate_artifacts(ARTIFACTS)
        manifest = read_json("manifest.json") if (ARTIFACTS / "manifest.json").exists() else None
        return {"valid": bool(result["valid"]), "errors": result["errors"], "manifest": manifest}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"valid": False, "errors": [f"artifact_parse_error: {exc}"], "manifest": None}

def require_evidence() -> dict:
    status = evidence_status()
    if not status["valid"]:
        raise HTTPException(status_code=503, detail={"code": "artifact_invalid", "errors": status["errors"]})
    return status

def read_json(name: str) -> Any:
    try:
        return json.loads((ARTIFACTS / name).read_text())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail={"code": "artifact_missing", "artifact": name}) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail={"code": "artifact_invalid", "artifact": name}) from exc
def read_csv(name: str) -> list[dict[str, Any]]:
    try:
        with (ARTIFACTS / name).open(newline="") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail={"code": "artifact_missing", "artifact": name}) from exc
    except OSError as exc:
        raise HTTPException(status_code=503, detail={"code": "artifact_invalid", "artifact": name}) from exc
    for row in rows:
        for k, v in list(row.items()):
            try: row[k] = float(v) if "." in v else int(v)
            except (ValueError, TypeError): pass
    return rows

@app.get("/api/health")
def health(): return {"status":"ok", "service":"segmentation-api", "artifacts": ARTIFACTS.exists(), "evidence_valid": evidence_status()["valid"]}
@app.get("/api/evidence-status")
def evidence(): return evidence_status()
@app.get("/api/manifest")
def manifest(): return require_evidence()["manifest"]
@app.get("/api/summary")
def summary(): require_evidence(); return read_json("summary.json")
@app.get("/api/points")
def points(cluster: int | None = Query(default=None, ge=0)):
    require_evidence()
    rows = read_csv("explorer_points.csv")
    return [r for r in rows if cluster is None or r.get("cluster") == cluster]
@app.get("/api/profiles")
def profiles():
    require_evidence()
    rows = read_csv("customer_segments.csv")
    features = read_json("summary.json")["features"]
    output=[]
    for cluster in sorted({r["cluster"] for r in rows}):
        group=[r for r in rows if r["cluster"]==cluster]
        means={f:sum(r[f] for r in group)/len(group) for f in features}
        output.append({"cluster":cluster,"count":len(group),"means":means})
    ranked = sorted(output, key=lambda p: (-p["means"]["avg_order_value"], -p["means"]["purchase_frequency"], p["cluster"]))
    roles = ["Premium value", "Frequent loyalists", "Budget starters"]
    for index, profile in enumerate(ranked):
        profile["name"] = roles[index] if index < len(roles) else f"Cluster {profile['cluster']}"
        profile["guidance"] = "Hypothesis only · validate on observed outcomes."
        profile["name_basis"] = {"ranked_by": ["avg_order_value", "purchase_frequency", "cluster"], "rank": index + 1}
    return output
@app.get("/api/validation")
def validation(): require_evidence(); return read_csv("validation_scores.csv")
@app.post("/api/score")
def score(observation: Observation):
    status = require_evidence()
    selected = status["manifest"]
    try: return score_observation(observation.model_dump(), preprocessing=selected["selected_preprocessing"], k=int(selected["selected_k"]))
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
