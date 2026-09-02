from copy import deepcopy
from threading import RLock
from typing import Any

from app.repositories.seed import SEED_WORKSPACE


class InMemoryWorkspaceRepository:
    """Session-scoped repository with defensive copies at every boundary."""

    def __init__(self, seed: dict[str, Any] | None = None) -> None:
        self._seed = deepcopy(seed or SEED_WORKSPACE)
        self._state = deepcopy(self._seed)
        self._lock = RLock()

    def reset(self) -> None:
        with self._lock:
            self._state = deepcopy(self._seed)

    def workspace(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._state)

    def readiness(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._state["readiness"])

    def add_task(self, task: dict[str, Any]) -> list[dict[str, Any]]:
        with self._lock:
            next_id = max((item["id"] for item in self._state["tasks"]), default=0) + 1
            self._state["tasks"].insert(0, {"id": next_id, **task})
            return deepcopy(self._state["tasks"])

    def update_task(self, task_id: int, done: bool) -> list[dict[str, Any]] | None:
        with self._lock:
            for task in self._state["tasks"]:
                if task["id"] == task_id:
                    task["done"] = done
                    return deepcopy(self._state["tasks"])
            return None

    def delete_task(self, task_id: int) -> list[dict[str, Any]] | None:
        with self._lock:
            remaining = [task for task in self._state["tasks"] if task["id"] != task_id]
            if len(remaining) == len(self._state["tasks"]):
                return None
            self._state["tasks"] = remaining
            return deepcopy(remaining)

    def record_agent_check(self) -> None:
        with self._lock:
            self._state["activity"].insert(0, {
                "message": "Demo check completed",
                "detail": "Queue reviewed. Forecasting, leakage, and model evaluation were not run.",
            })
