"""FastAPI API for Project 05's reproducible analytical artifacts."""

from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ml.pipeline import ArtifactContractError, load_artifacts, run  # noqa: E402

app = FastAPI(title="Project 05 · Data Science Skills Lab", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5175", "http://localhost:5175"], allow_methods=["GET"], allow_headers=["*"])


def payload():
    try:
        return run()
    except (FileNotFoundError, ArtifactContractError, ValueError, OSError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/health")
def health():
    return {"status": "ok", "project": "05_data_science_skills_lab", "artifact_backed": True}


@app.get("/api/summary")
def summary():
    return payload()


@app.get("/api/cleaning")
def cleaning():
    return payload()["metrics"]["data_quality"]


@app.get("/api/classification")
def classification():
    return payload()["metrics"]["classification"]


@app.get("/api/regression")
def regression():
    data = payload()
    return {"metrics": data["metrics"]["regression"], "predictions": data["summary"]["regression_predictions"], "excluded_targets": data["summary"]["regression_excluded_test_targets"]}


@app.get("/api/clustering")
def clustering():
    data = payload()
    return {"metrics": data["metrics"]["clustering"], "rows": data["summary"]["analysis_rows"]}


@app.get("/api/rows")
def rows(plan: str = Query("all"), renewal: str = Query("all"), cluster: str = Query("all"), limit: int = Query(100, ge=1, le=1000)):
    if plan not in {"all", "basic", "pro", "enterprise"}:
        raise HTTPException(status_code=422, detail="plan must be one of: all, basic, pro, enterprise")
    if renewal not in {"all", "0", "1"}:
        raise HTTPException(status_code=422, detail="renewal must be one of: all, 0, 1")
    if cluster not in {"all", "0", "1", "2", "3"}:
        raise HTTPException(status_code=422, detail="cluster must be all or a supported cluster index")
    data = payload()["summary"]["analysis_rows"]
    if plan != "all": data = [row for row in data if row["plan"] == plan]
    if renewal != "all": data = [row for row in data if str(row["renewed"]) == renewal]
    if cluster != "all": data = [row for row in data if str(row.get("cluster")) == cluster]
    return {"count": len(data), "rows": data[:limit], "filters": {"plan": plan, "renewal": renewal, "cluster": cluster}}
