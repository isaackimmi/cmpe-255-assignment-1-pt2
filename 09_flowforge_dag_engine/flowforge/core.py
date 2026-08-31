"""Core graph validation and deterministic execution primitives."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


class DAGError(ValueError):
    """Raised when a graph is structurally invalid."""


@dataclass(frozen=True)
class Task:
    name: str
    function: Callable[["PipelineContext"], Any]
    depends_on: tuple[str, ...] = ()

    def __init__(self, name: str, function: Callable[["PipelineContext"], Any], depends_on: Iterable[str] = ()):
        if not isinstance(name, str) or not name.strip():
            raise DAGError("task name must be a non-empty string")
        if not callable(function):
            raise TypeError("task function must be callable")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "function", function)
        object.__setattr__(self, "depends_on", tuple(depends_on))


@dataclass
class PipelineContext:
    """Mutable state shared by tasks during one pipeline run."""

    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_order: list[str] = field(default_factory=list)

    def output(self, task_name: str) -> Any:
        if task_name not in self.outputs:
            raise KeyError(f"no output available for task {task_name!r}")
        return self.outputs[task_name]


class DAG:
    def __init__(self) -> None:
        self._tasks: OrderedDict[str, Task] = OrderedDict()

    @property
    def tasks(self) -> tuple[Task, ...]:
        return tuple(self._tasks.values())

    def add_task(self, task: Task) -> None:
        if task.name in self._tasks:
            raise DAGError(f"duplicate task name: {task.name!r}")
        self._tasks[task.name] = task

    def validate(self) -> None:
        names = set(self._tasks)
        for task in self.tasks:
            unknown = set(task.depends_on) - names
            if unknown:
                raise DAGError(f"task {task.name!r} has unknown dependencies: {sorted(unknown)!r}")
            if task.name in task.depends_on:
                raise DAGError(f"task {task.name!r} cannot depend on itself")
        self.topological_order()

    def topological_order(self) -> list[str]:
        """Return a stable Kahn topological ordering, or raise on cycles."""
        indegree = {name: 0 for name in self._tasks}
        children: dict[str, list[str]] = {name: [] for name in self._tasks}
        for task in self.tasks:
            for dependency in task.depends_on:
                indegree[task.name] += 1
                children[dependency].append(task.name)
        ready = [name for name in self._tasks if indegree[name] == 0]
        order: list[str] = []
        while ready:
            current = ready.pop(0)
            order.append(current)
            for child in children[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        if len(order) != len(self._tasks):
            cyclic = sorted(name for name, degree in indegree.items() if degree)
            raise DAGError(f"cycle detected involving: {cyclic!r}")
        return order


class Runner:
    def __init__(self, dag: DAG):
        self.dag = dag

    def run(self, context: PipelineContext | None = None) -> PipelineContext:
        self.dag.validate()
        context = context or PipelineContext()
        for name in self.dag.topological_order():
            task = next(task for task in self.dag.tasks if task.name == name)
            try:
                context.outputs[name] = task.function(context)
            except Exception as exc:
                raise RuntimeError(f"task {name!r} failed: {exc}") from exc
            context.execution_order.append(name)
        return context
