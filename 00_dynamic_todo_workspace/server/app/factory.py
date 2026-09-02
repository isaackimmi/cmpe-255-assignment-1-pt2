from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.repositories.workspace import InMemoryWorkspaceRepository
from app.services.workspace import WorkspaceService


def create_app(repository: InMemoryWorkspaceRepository | None = None) -> FastAPI:
    application = FastAPI(title=settings.app_name, version=settings.version)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    workspace_repository = repository or InMemoryWorkspaceRepository()
    application.state.workspace_repository = workspace_repository
    application.state.workspace_service = WorkspaceService(workspace_repository)
    application.include_router(router, prefix="/api")
    return application
