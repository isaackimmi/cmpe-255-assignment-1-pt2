"""FastAPI application factory."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.router import router
from .config import settings


def create_app() -> FastAPI:
    application = FastAPI(title=settings.title, version=settings.version)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    application.include_router(router, prefix="/api")
    return application
