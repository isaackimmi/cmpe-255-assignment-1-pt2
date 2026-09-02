"""FastAPI application composition root for Project 05."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import API_TITLE, API_VERSION, CORS_ORIGINS
from server.routers import evidence, health


def create_app() -> FastAPI:
    application = FastAPI(title=API_TITLE, version=API_VERSION)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    application.include_router(health.router)
    application.include_router(evidence.router)
    return application


app = create_app()
