from fastapi import HTTPException

from app.models.schemas import TaskCreate, TaskUpdate
from app.repositories.workspace import InMemoryWorkspaceRepository


class WorkspaceService:
    def __init__(self, repository: InMemoryWorkspaceRepository) -> None:
        self.repository = repository

    def get_workspace(self) -> dict:
        return self.repository.workspace()

    def get_readiness(self) -> dict:
        return self.repository.readiness()

    def record_agent_check(self) -> dict:
        self.repository.record_agent_check()
        return {"status": "demo-only"}

    def create_task(self, request: TaskCreate) -> list[dict]:
        title = request.title.strip()
        if not title:
            raise HTTPException(status_code=422, detail="Task title cannot be blank")
        return self.repository.add_task({"title": title, "area": "Workspace", "priority": request.priority, "done": False})

    def update_task(self, task_id: int, request: TaskUpdate) -> list[dict]:
        tasks = self.repository.update_task(task_id, request.done)
        if tasks is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return tasks

    def delete_task(self, task_id: int) -> list[dict]:
        tasks = self.repository.delete_task(task_id)
        if tasks is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return tasks
