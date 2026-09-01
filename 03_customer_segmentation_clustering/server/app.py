"""FastAPI evidence and scoring service for Project 03."""
from __future__ import annotations
import csv, json, os
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from ml.pipeline import score_observation

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
app = FastAPI(title="Project 03 Segmentation API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","), allow_methods=["*"], allow_headers=["*"])

class Observation(BaseModel):
    annual_income_k: float = Field(ge=15)
    spend_score: float = Field(ge=1, le=99)
    purchase_frequency: float = Field(ge=0.2)
    avg_order_value: float = Field(ge=5)

def read_json(name: str) -> Any:
    return json.loads((ARTIFACTS / name).read_text())
def read_csv(name: str) -> list[dict[str, Any]]:
    with (ARTIFACTS / name).open(newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for k, v in list(row.items()):
            try: row[k] = float(v) if "." in v else int(v)
            except (ValueError, TypeError): pass
    return rows

@app.get("/api/health")
def health(): return {"status":"ok", "service":"segmentation-api", "artifacts": ARTIFACTS.exists()}
@app.get("/api/manifest")
def manifest(): return read_json("manifest.json")
@app.get("/api/summary")
def summary(): return read_json("summary.json")
@app.get("/api/points")
def points(cluster: int | None = Query(default=None, ge=0)):
    rows = read_csv("explorer_points.csv")
    return [r for r in rows if cluster is None or r.get("cluster") == cluster]
@app.get("/api/profiles")
def profiles():
    rows = read_csv("customer_segments.csv")
    features = read_json("summary.json")["features"]
    output=[]
    for cluster in sorted({r["cluster"] for r in rows}):
        group=[r for r in rows if r["cluster"]==cluster]
        output.append({"cluster":cluster,"count":len(group),"means":{f:sum(r[f] for r in group)/len(group) for f in features}})
    return output
@app.get("/api/validation")
def validation(): return read_csv("validation_scores.csv")
@app.post("/api/score")
def score(observation: Observation):
    try: return score_observation(observation.model_dump())
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
