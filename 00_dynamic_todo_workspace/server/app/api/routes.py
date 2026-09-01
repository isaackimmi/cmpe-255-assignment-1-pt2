from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_workspace_service
from app.models.schemas import ReadinessResponse, TaskCreate, TaskResponse, TaskUpdate, WorkspaceResponse
from app.services.workspace import WorkspaceService

router = APIRouter()
Service = Annotated[WorkspaceService, Depends(get_workspace_service)]


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "fieldnote-api"}


@router.get("/workspace", response_model=WorkspaceResponse)
def workspace(service: Service) -> dict:
    return service.get_workspace()


@router.get("/readiness", response_model=ReadinessResponse)
def readiness(service: Service) -> dict:
    return service.get_readiness()


@router.post("/tasks", response_model=list[TaskResponse])
def create_task(task: TaskCreate, service: Service) -> list[dict]:
    return service.create_task(task)


@router.patch("/tasks/{task_id}", response_model=list[TaskResponse])
def update_task(task_id: int, update: TaskUpdate, service: Service) -> list[dict]:
    return service.update_task(task_id, update)


@router.delete("/tasks/{task_id}", response_model=list[TaskResponse])
def delete_task(task_id: int, service: Service) -> list[dict]:
    return service.delete_task(task_id)


@router.post("/agent-check")
def agent_check(service: Service) -> dict:
    return service.record_agent_check()
