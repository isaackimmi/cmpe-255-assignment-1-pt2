"""FastAPI API exposing auditable Project 02 artifacts and local inference."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.model_adapter import (  # noqa: E402
    ArtifactError, BackendUnsupported, generate, load_metrics, probabilities,
)

app = FastAPI(title="Nano LLM Evidence API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5175", "http://localhost:5175"], allow_methods=["GET", "POST"], allow_headers=["*"])


@app.exception_handler(ArtifactError)
async def artifact_error_handler(_request: Request, exc: ArtifactError):
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


class GenerationRequest(BaseModel):
    prompt: str = Field(default="", max_length=500)
    max_new_tokens: int = Field(default=16, ge=1, le=80)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class ProbabilityRequest(BaseModel):
    context: str = Field(default="", max_length=200)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "nano-llm-evidence-api"}


@app.get("/api/metrics")
def metrics() -> dict:
    return load_metrics()


@app.get("/api/behavior")
def behavior() -> dict:
    return load_metrics().get("behavior", {})


@app.post("/api/generate")
def generate_text(request: GenerationRequest) -> dict:
    try:
        return generate(request.prompt, request.max_new_tokens, request.temperature)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/probabilities")
def next_probabilities(request: ProbabilityRequest) -> dict:
    try:
        return {"context": request.context, "candidates": probabilities(request.context)}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
