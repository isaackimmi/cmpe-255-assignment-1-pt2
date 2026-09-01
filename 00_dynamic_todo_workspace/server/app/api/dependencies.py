from fastapi import Request

from app.services.workspace import WorkspaceService


def get_workspace_service(request: Request) -> WorkspaceService:
    return request.app.state.workspace_service
