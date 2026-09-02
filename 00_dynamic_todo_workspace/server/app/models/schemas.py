from typing import Literal

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    priority: Literal["high", "medium", "low"] = "medium"


class TaskUpdate(BaseModel):
    done: bool


class TaskResponse(BaseModel):
    id: int
    title: str
    area: str
    priority: Literal["high", "medium", "low"]
    done: bool


class ProjectResponse(BaseModel):
    name: str
    brief: str
    goal: str


class ReadinessResponse(BaseModel):
    status: str
    dataset: str
    score: int = Field(ge=0, le=100)
    note: str
    boundary: str


class WorkflowStageResponse(BaseModel):
    name: str
    status: Literal["complete", "planned"]
    evidence: str
    detail: str


class WorkflowResponse(BaseModel):
    current: str
    stages: list[WorkflowStageResponse]


class ActivityResponse(BaseModel):
    message: str
    detail: str


class WorkspaceResponse(BaseModel):
    project: ProjectResponse
    readiness: ReadinessResponse
    tasks: list[TaskResponse]
    workflow: WorkflowResponse
    activity: list[ActivityResponse]
