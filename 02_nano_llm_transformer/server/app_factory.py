"""FastAPI composition root."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ml.errors import ArtifactError
from server.config import ALLOWED_ORIGINS, API_TITLE, API_VERSION
from server.error_handlers import artifact_error_handler
from server.routers import evidence, health, inference

def create_app() -> FastAPI:
    app = FastAPI(title=API_TITLE, version=API_VERSION)
    app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"])
    app.add_exception_handler(ArtifactError, artifact_error_handler)
    for router in (health.router, evidence.router, inference.router):
        app.include_router(router, prefix="/api")
    return app
