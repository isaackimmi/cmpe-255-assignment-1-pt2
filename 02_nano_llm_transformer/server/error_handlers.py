"""Consistent translation of domain errors into HTTP responses."""
from fastapi import Request
from fastapi.responses import JSONResponse
from ml.errors import ArtifactError

async def artifact_error_handler(_request: Request, exc: ArtifactError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})
