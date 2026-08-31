"""Core graph validation and deterministic execution primitives.

The engine deliberately remains small and in-process, but task boundaries are
treated as data boundaries: a task can read only the artifacts it declares,
and each successful result is captured in an immutable lineage envelope.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import inspect
import json
import platform
import random
import sys
from types import MappingProxyType
from typing import Any
from uuid import uuid4


class DAGError(ValueError):
    """Raised when a graph or task input contract is structurally invalid."""


class DependencyError(DAGError):
    """Raised when a task attempts to read an undeclared input artifact."""


def _canonical(value: Any) -> Any:
    """Return a JSON-friendly, stable representation for fingerprints."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(item) for item in value), key=repr)
    return {"type": f"{type(value).__module__}.{type(value).__qualname__}", "repr": repr(value)}


def _fingerprint(value: Any) -> str:
    payload = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _schema(value: Any) -> Any:
    """Describe the shape and Python types of a value without inspecting contents deeply."""
    if isinstance(value, Mapping):
        return {
            "type": "mapping",
            "fields": {str(key): type(item).__name__ for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))},
        }
    if isinstance(value, (list, tuple)):
        item_types = sorted({type(item).__name__ for item in value})
        return {"type": type(value).__name__, "items": item_types}
    return {"type": type(value).__name__}


def _timestamp(clock: Callable[[], Any] | None) -> str:
    value = clock() if clock is not None else datetime.now(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def _function_fingerprint(function: Callable[..., Any]) -> str:
    try:
        source = inspect.getsource(function)
    except (OSError, TypeError):
        source = repr(function)
    identity = f"{function.__module__}.{getattr(function, '__qualname__', repr(function))}\n{source}"
    return _fingerprint(identity)


@dataclass(frozen=True)
class Task:
    name: str
    function: Callable[..., Any]
    depends_on: tuple[str, ...] = ()
    config: Mapping[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        function: Callable[..., Any],
        depends_on: Iterable[str] = (),
        config: Mapping[str, Any] | None = None,
    ):
        if not isinstance(name, str) or not name.strip():
            raise DAGError("task name must be a non-empty string")
        if not callable(function):
            raise TypeError("task function must be callable")
        if isinstance(depends_on, str):
            raise DAGError("depends_on must be an iterable of dependency names, not a string")
        try:
            dependencies = tuple(depends_on)
        except TypeError as exc:
            raise DAGError("depends_on must be an iterable of dependency names") from exc
        for dependency in dependencies:
            if not isinstance(dependency, str) or not dependency.strip():
                raise DAGError("each dependency name must be a non-empty string")
        if len(set(dependencies)) != len(dependencies):
            raise DAGError(f"task {name!r} has duplicate dependencies: {dependencies!r}")
        if config is not None and not isinstance(config, Mapping):
            raise DAGError("task config must be a mapping")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "function", function)
        object.__setattr__(self, "depends_on", dependencies)
        object.__setattr__(self, "config", MappingProxyType(dict(config or {})))


@dataclass(frozen=True)
class Artifact:
    """A read-only lineage record for one task result."""

    artifact_id: str
    producer: str
    run_id: str
    parent_artifact_ids: tuple[str, ...]
    content_hash: str
    schema_fingerprint: str
    created_at: str
    _payload: Any = field(repr=False, compare=False)

    @property
    def value(self) -> Any:
        return deepcopy(self._payload)

    @classmethod
    def create(
        cls,
        value: Any,
        producer: str,
        run_id: str,
        parent_artifact_ids: Iterable[str],
        created_at: str,
    ) -> "Artifact":
        content_hash = _fingerprint(value)
        schema_fingerprint = _fingerprint(_schema(value))
        parents = tuple(parent_artifact_ids)
        artifact_id = _fingerprint({"run_id": run_id, "producer": producer, "parents": parents, "content": content_hash})[:24]
        return cls(
            artifact_id=artifact_id,
            producer=producer,
            run_id=run_id,
            parent_artifact_ids=parents,
            content_hash=content_hash,
            schema_fingerprint=schema_fingerprint,
            created_at=created_at,
            _payload=deepcopy(value),
        )


class PipelineContext:
    """Run state with read-only public artifact snapshots.

    A context may be supplied to a runner for configuration and metadata, but
    every invocation gets a fresh run state. Prior outputs and execution
    history are discarded before validation or task execution begins.
    """

    def __init__(
        self,
        outputs: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        execution_order: Iterable[str] | None = None,
    ) -> None:
        self.metadata: dict[str, Any] = dict(metadata or {})
        self._legacy_outputs: dict[str, Any] = deepcopy(dict(outputs or {}))
        self._artifacts: dict[str, Artifact] = {}
        self._execution_order: list[str] = list(execution_order or [])
        self._manifest: dict[str, Any] = {}
        self._run_id: str | None = None
        self._status = "new"

    @property
    def outputs(self) -> Mapping[str, Any]:
        """A detached, read-only snapshot of successful output values."""
        if self._artifacts:
            values = {name: artifact.value for name, artifact in self._artifacts.items()}
        elif self._status == "new":
            values = deepcopy(self._legacy_outputs)
        else:
            values = {}
        return MappingProxyType(values)

    @property
    def artifacts(self) -> Mapping[str, Artifact]:
        """The immutable artifact envelopes produced by the current run."""
        return MappingProxyType(dict(self._artifacts))

    @property
    def execution_order(self) -> list[str]:
        return list(self._execution_order)

    @property
    def manifest(self) -> dict[str, Any]:
        return deepcopy(self._manifest)

    @property
    def run_id(self) -> str | None:
        return self._run_id

    @property
    def status(self) -> str:
        return self._status

    def output(self, task_name: str) -> Any:
        if task_name in self._artifacts:
            return self._artifacts[task_name].value
        if self._status == "new" and task_name in self._legacy_outputs:
            return deepcopy(self._legacy_outputs[task_name])
        raise KeyError(f"no output available for task {task_name!r}")

    def artifact(self, task_name: str) -> Artifact:
        if task_name not in self._artifacts:
            raise KeyError(f"no artifact available for task {task_name!r}")
        return self._artifacts[task_name]

    def _begin_run(
        self,
        run_id: str,
        seed: int | None,
        config: Mapping[str, Any] | None,
        started_at: str,
        environment: Mapping[str, str],
    ) -> None:
        self._legacy_outputs.clear()
        self._artifacts.clear()
        self._execution_order.clear()
        self._run_id = run_id
        self._status = "running"
        run_config = dict(config or {})
        self.metadata.update({"run_id": run_id, "seed": seed, "config": deepcopy(run_config), "started_at": started_at})
        self._manifest = {
            "run_id": run_id,
            "status": "running",
            "seed": seed,
            "config": deepcopy(run_config),
            "started_at": started_at,
            "environment": dict(environment),
            "execution_order": [],
            "tasks": {},
        }

    def _task_context(self, task_name: str, dependencies: Iterable[str]) -> "TaskContext":
        return TaskContext(self, task_name, dependencies)

    def _store_artifact(self, task: Task, value: Any, clock: Callable[[], Any] | None) -> Artifact:
        parents = [self._artifacts[name].artifact_id for name in task.depends_on]
        artifact = Artifact.create(value, task.name, self._run_id or "unknown", parents, _timestamp(clock))
        self._artifacts[task.name] = artifact
        self._execution_order.append(task.name)
        task_record = self._manifest["tasks"][task.name]
        task_record.update(
            {
                "status": "succeeded",
                "output": {
                    "artifact_id": artifact.artifact_id,
                    "producer": artifact.producer,
                    "run_id": artifact.run_id,
                    "parent_artifact_ids": list(artifact.parent_artifact_ids),
                    "content_hash": artifact.content_hash,
                    "schema_fingerprint": artifact.schema_fingerprint,
                    "created_at": artifact.created_at,
                },
            }
        )
        self._manifest["execution_order"].append(task.name)
        return artifact

    def _fail_run(self, failed_task: str | None, error: BaseException) -> None:
        if failed_task is not None and failed_task in self._manifest.get("tasks", {}):
            self._manifest["tasks"][failed_task].update(
                {"status": "failed", "error": {"type": type(error).__name__, "message": str(error)}}
            )
        for task_record in self._manifest.get("tasks", {}).values():
            if task_record["status"] in {"pending", "running"}:
                task_record["status"] = "skipped"
        self._artifacts.clear()
        self._execution_order.clear()
        self._status = "failed"
        self._manifest["status"] = "failed"
        self._manifest["error"] = {"type": type(error).__name__, "message": str(error)}

    def _finish_run(self, finished_at: str) -> None:
        self._status = "succeeded"
        self._manifest["status"] = "succeeded"
        self._manifest["finished_at"] = finished_at


class TaskContext:
    """Task-scoped view that enforces the task's declared input contract."""

    def __init__(self, parent: PipelineContext, task_name: str, dependencies: Iterable[str]) -> None:
        self._parent = parent
        self.task_name = task_name
        self._dependencies = tuple(dependencies)
        self._dependency_set = frozenset(self._dependencies)

    @property
    def run_id(self) -> str | None:
        return self._parent.run_id

    @property
    def metadata(self) -> Mapping[str, Any]:
        return MappingProxyType(deepcopy(self._parent.metadata))

    @property
    def outputs(self) -> Mapping[str, Any]:
        return MappingProxyType({name: self.output(name) for name in self._dependencies if name in self._parent._artifacts})

    def output(self, task_name: str) -> Any:
        if task_name not in self._dependency_set:
            raise DependencyError(
                f"task {self.task_name!r} attempted to read undeclared input {task_name!r}; "
                f"declare it in depends_on"
            )
        return self._parent.output(task_name)

    def artifact(self, task_name: str) -> Artifact:
        if task_name not in self._dependency_set:
            raise DependencyError(
                f"task {self.task_name!r} attempted to read undeclared input {task_name!r}; "
                f"declare it in depends_on"
            )
        return self._parent.artifact(task_name)


class DAG:
    def __init__(self) -> None:
        self._tasks: OrderedDict[str, Task] = OrderedDict()

    @property
    def tasks(self) -> tuple[Task, ...]:
        return tuple(self._tasks.values())

    def add_task(self, task: Task) -> None:
        if not isinstance(task, Task):
            raise TypeError("dag tasks must be Task instances")
        if task.name in self._tasks:
            raise DAGError(f"duplicate task name: {task.name!r}")
        self._tasks[task.name] = task

    def _validate_dependencies(self) -> None:
        names = set(self._tasks)
        for task in self.tasks:
            unknown = set(task.depends_on) - names
            if unknown:
                raise DAGError(f"task {task.name!r} has unknown dependencies: {sorted(unknown)!r}")
            if task.name in task.depends_on:
                raise DAGError(f"task {task.name!r} cannot depend on itself")

    def validate(self) -> None:
        self._validate_dependencies()
        self.topological_order()

    def _cyclic_components(self) -> list[list[str]]:
        """Return only strongly connected components that actually contain cycles."""
        adjacency = {name: list(self._tasks[name].depends_on) for name in self._tasks}
        insertion_order = {name: index for index, name in enumerate(self._tasks)}
        index = 0
        indices: dict[str, int] = {}
        lowlinks: dict[str, int] = {}
        stack: list[str] = []
        on_stack: set[str] = set()
        components: list[list[str]] = []

        def strongconnect(node: str) -> None:
            nonlocal index
            indices[node] = index
            lowlinks[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)
            for neighbor in adjacency[node]:
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
                elif neighbor in on_stack:
                    lowlinks[node] = min(lowlinks[node], indices[neighbor])
            if lowlinks[node] == indices[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack.remove(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1 or component[0] in adjacency[component[0]]:
                    components.append(sorted(component, key=insertion_order.__getitem__))

        for name in self._tasks:
            if name not in indices:
                strongconnect(name)
        return sorted(components, key=lambda component: insertion_order[component[0]])

    def topological_order(self) -> list[str]:
        """Return a stable Kahn topological ordering, or raise on cycles."""
        self._validate_dependencies()
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
            cyclic_components = self._cyclic_components()
            cyclic_nodes = {name for component in cyclic_components for name in component}
            blocked = [name for name, degree in indegree.items() if degree and name not in cyclic_nodes]
            cycle_text = "; ".join(repr(component) for component in cyclic_components)
            message = f"cycle detected involving: {cycle_text}"
            if blocked:
                message += f"; blocked descendants: {blocked!r}"
            raise DAGError(message)
        return order


class Runner:
    def __init__(self, dag: DAG):
        self.dag = dag

    def run(
        self,
        context: PipelineContext | None = None,
        *,
        seed: int | None = None,
        config: Mapping[str, Any] | None = None,
        clock: Callable[[], Any] | None = None,
    ) -> PipelineContext:
        context = PipelineContext() if context is None else context
        run_id = uuid4().hex
        started_at = _timestamp(clock)
        environment = {"python": sys.version.split()[0], "platform": platform.platform()}
        context._begin_run(run_id, seed, config, started_at, environment)
        try:
            order = self.dag.topological_order()
        except Exception as exc:
            context._fail_run(None, exc)
            raise

        if seed is not None:
            random.seed(seed)
            try:
                import numpy as np  # type: ignore

                np.random.seed(seed % (2**32 - 1))
            except ImportError:
                pass

        for task in self.dag.tasks:
            context._manifest["tasks"][task.name] = {
                "status": "pending",
                "depends_on": list(task.depends_on),
                "inputs": [],
                "code_fingerprint": _function_fingerprint(task.function),
                "config_fingerprint": _fingerprint(dict(task.config)),
            }
        try:
            for name in order:
                task = next(task for task in self.dag.tasks if task.name == name)
                record = context._manifest["tasks"][name]
                record["status"] = "running"
                record["inputs"] = [context.artifact(dependency).artifact_id for dependency in task.depends_on]
                try:
                    value = task.function(context._task_context(task.name, task.depends_on))
                    context._store_artifact(task, value, clock)
                except Exception as exc:
                    context._fail_run(task.name, exc)
                    raise RuntimeError(f"task {name!r} failed: {exc}") from exc
            context._finish_run(_timestamp(clock))
            return context
        except RuntimeError:
            raise
        except Exception as exc:
            context._fail_run(None, exc)
            raise
