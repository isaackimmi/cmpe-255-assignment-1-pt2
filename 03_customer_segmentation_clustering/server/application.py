from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.config import cors_origins
from server.routers.evidence import router as evidence_router
from server.routers.segmentation import router as segmentation_router

def create_app() -> FastAPI:
    app = FastAPI(title="Project 03 Segmentation API", version="1.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=cors_origins(), allow_methods=["*"], allow_headers=["*"])
    app.include_router(evidence_router)
    app.include_router(segmentation_router)
    return app
