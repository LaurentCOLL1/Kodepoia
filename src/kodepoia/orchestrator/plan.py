from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from kodepoia.orchestrator.workspaces import WorkspaceIdentity

ORCHESTRATION_PLAN_SCHEMA_VERSION = 1


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _required_text(value: str, name: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError(f"{name} must not be empty")
    return clean


class OrchestrationEffect(StrEnum):
    READ_ONLY = "read_only"
    MUTATION_PROPOSED = "mutation_proposed"


class OrchestrationRoute(StrEnum):
    PROJECT_CONTEXT = "project_context"
    RESEARCH = "research"
    KODECODE = "kodecode"
    KODEGODOT = "kodegodot"
    MODEL_LAB = "model_lab"
    SPECIALIST = "specialist"


@dataclass(frozen=True, slots=True)
class RouteDescriptor:
    route: OrchestrationRoute
    capability: str
    allowed_effects: tuple[OrchestrationEffect, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route.value,
            "capability": self.capability,
            "allowed_effects": [item.value for item in self.allowed_effects],
        }


ROUTE_CATALOG: dict[OrchestrationRoute, RouteDescriptor] = {
    OrchestrationRoute.PROJECT_CONTEXT: RouteDescriptor(
        route=OrchestrationRoute.PROJECT_CONTEXT,
        capability="governed_project_context",
        allowed_effects=(OrchestrationEffect.READ_ONLY,),
    ),
    OrchestrationRoute.RESEARCH: RouteDescriptor(
        route=OrchestrationRoute.RESEARCH,
        capability="governed_research",
        allowed_effects=(OrchestrationEffect.READ_ONLY,),
    ),
    OrchestrationRoute.KODECODE: RouteDescriptor(
        route=OrchestrationRoute.KODECODE,
        capability="kodecode_tooling",
        allowed_effects=(
            OrchestrationEffect.READ_ONLY,
            OrchestrationEffect.MUTATION_PROPOSED,
        ),
    ),
    OrchestrationRoute.KODEGODOT: RouteDescriptor(
        route=OrchestrationRoute.KODEGODOT,
        capability="kodegodot_tooling",
        allowed_effects=(
            OrchestrationEffect.READ_ONLY,
            OrchestrationEffect.MUTATION_PROPOSED,
        ),
    ),
    OrchestrationRoute.MODEL_LAB: RouteDescriptor(
        route=OrchestrationRoute.MODEL_LAB,
        capability="governed_model_lab",
        allowed_effects=(OrchestrationEffect.READ_ONLY,),
    ),
    OrchestrationRoute.SPECIALIST: RouteDescriptor(
        route=OrchestrationRoute.SPECIALIST,
        capability="fixed_specialist",
        allowed_effects=(OrchestrationEffect.READ_ONLY,),
    ),
}


@dataclass(frozen=True, slots=True)
class OrchestrationTask:
    task_id: str
    workspace_id: str
    workspace_scope: str
    goal: str
    route: OrchestrationRoute
    effect: OrchestrationEffect
    dependencies: tuple[str, ...] = ()
    source_workspace_ids: tuple[str, ...] = ()
    input_handoff_digests: tuple[str, ...] = ()
    schema_version: int = ORCHESTRATION_PLAN_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != ORCHESTRATION_PLAN_SCHEMA_VERSION:
            raise ValueError("Unsupported orchestration task schema version")
        task_id = _required_text(self.task_id, "task_id")
        workspace_id = _required_text(self.workspace_id, "workspace_id")
        workspace_scope = _required_text(self.workspace_scope, "workspace_scope")
        if workspace_scope != f"project:{workspace_id}":
            raise ValueError("Task workspace scope must bind its owning workspace")
        descriptor = ROUTE_CATALOG[self.route]
        if self.effect not in descriptor.allowed_effects:
            raise ValueError(
                f"Effect {self.effect.value} is not allowed for route {self.route.value}"
            )
        deps = tuple(dict.fromkeys(_required_text(item, "dependency") for item in self.dependencies))
        if task_id in deps:
            raise ValueError("Task cannot depend on itself")
        sources = tuple(
            dict.fromkeys(
                _required_text(item, "source_workspace_id")
                for item in self.source_workspace_ids
            )
        )
        if workspace_id in sources:
            sources = tuple(item for item in sources if item != workspace_id)
        handoffs = tuple(
            dict.fromkeys(
                _required_text(item, "input_handoff_digest")
                for item in self.input_handoff_digests
            )
        )
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "workspace_id", workspace_id)
        object.__setattr__(self, "workspace_scope", workspace_scope)
        object.__setattr__(self, "goal", _required_text(self.goal, "goal"))
        object.__setattr__(self, "dependencies", deps)
        object.__setattr__(self, "source_workspace_ids", sources)
        object.__setattr__(self, "input_handoff_digests", handoffs)
        object.__setattr__(self, "digest_sha256", _sha256_payload(self._payload_without_digest()))

    @classmethod
    def for_workspace(
        cls,
        *,
        task_id: str,
        workspace: WorkspaceIdentity,
        goal: str,
        route: OrchestrationRoute,
        effect: OrchestrationEffect,
        dependencies: tuple[str, ...] = (),
        source_workspace_ids: tuple[str, ...] = (),
        input_handoff_digests: tuple[str, ...] = (),
    ) -> OrchestrationTask:
        return cls(
            task_id=task_id,
            workspace_id=workspace.workspace_id,
            workspace_scope=workspace.project_scope,
            goal=goal,
            route=route,
            effect=effect,
            dependencies=dependencies,
            source_workspace_ids=source_workspace_ids,
            input_handoff_digests=input_handoff_digests,
        )

    @property
    def capability(self) -> str:
        return ROUTE_CATALOG[self.route].capability

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "workspace_id": self.workspace_id,
            "workspace_scope": self.workspace_scope,
            "goal": self.goal,
            "route": self.route.value,
            "capability": self.capability,
            "effect": self.effect.value,
            "dependencies": list(self.dependencies),
            "source_workspace_ids": list(self.source_workspace_ids),
            "input_handoff_digests": list(self.input_handoff_digests),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload


@dataclass(frozen=True, slots=True)
class OrchestrationPlanPreview:
    topological_order: tuple[str, ...]
    ready_tasks: tuple[str, ...]
    blocked_tasks: tuple[str, ...]
    blockers: dict[str, tuple[str, ...]]
    mutation_proposed_tasks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "topological_order": list(self.topological_order),
            "ready_tasks": list(self.ready_tasks),
            "blocked_tasks": list(self.blocked_tasks),
            "blockers": {key: list(value) for key, value in sorted(self.blockers.items())},
            "mutation_proposed_tasks": list(self.mutation_proposed_tasks),
        }


@dataclass(frozen=True, slots=True)
class OrchestrationPlan:
    plan_id: str
    tasks: tuple[OrchestrationTask, ...]
    schema_version: int = ORCHESTRATION_PLAN_SCHEMA_VERSION
    digest_sha256: str = field(init=False)
    _preview: OrchestrationPlanPreview = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.schema_version != ORCHESTRATION_PLAN_SCHEMA_VERSION:
            raise ValueError("Unsupported orchestration plan schema version")
        plan_id = _required_text(self.plan_id, "plan_id")
        if not self.tasks:
            raise ValueError("Orchestration plan requires at least one task")
        ordered = tuple(sorted(self.tasks, key=lambda item: item.task_id))
        ids = [item.task_id for item in ordered]
        if len(ids) != len(set(ids)):
            raise ValueError("Orchestration plan task IDs must be unique")
        task_ids = set(ids)
        for task in ordered:
            missing = tuple(dep for dep in task.dependencies if dep not in task_ids)
            if missing:
                raise ValueError(
                    f"Task {task.task_id} has unknown dependencies: {', '.join(missing)}"
                )
        topo = self._topological_order(ordered)
        blockers: dict[str, tuple[str, ...]] = {}
        ready: list[str] = []
        blocked: list[str] = []
        for task_id in topo:
            task = next(item for item in ordered if item.task_id == task_id)
            if task.dependencies:
                blockers[task_id] = task.dependencies
                blocked.append(task_id)
            else:
                ready.append(task_id)
        mutations = tuple(
            task.task_id
            for task in ordered
            if task.effect is OrchestrationEffect.MUTATION_PROPOSED
        )
        preview = OrchestrationPlanPreview(
            topological_order=topo,
            ready_tasks=tuple(ready),
            blocked_tasks=tuple(blocked),
            blockers=blockers,
            mutation_proposed_tasks=mutations,
        )
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "tasks", ordered)
        object.__setattr__(self, "_preview", preview)
        object.__setattr__(self, "digest_sha256", _sha256_payload(self._payload_without_digest()))

    @staticmethod
    def _topological_order(tasks: tuple[OrchestrationTask, ...]) -> tuple[str, ...]:
        graph = {task.task_id: set(task.dependencies) for task in tasks}
        emitted: list[str] = []
        remaining = dict(graph)
        while remaining:
            ready = sorted(task_id for task_id, deps in remaining.items() if not deps)
            if not ready:
                raise ValueError("Orchestration plan dependency cycle detected")
            for task_id in ready:
                emitted.append(task_id)
                remaining.pop(task_id)
                for deps in remaining.values():
                    deps.discard(task_id)
        return tuple(emitted)

    def preview(self) -> OrchestrationPlanPreview:
        return self._preview

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "tasks": [task.to_dict() for task in self.tasks],
            "preview": self._preview.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload


__all__ = [
    "ORCHESTRATION_PLAN_SCHEMA_VERSION",
    "ROUTE_CATALOG",
    "OrchestrationEffect",
    "OrchestrationPlan",
    "OrchestrationPlanPreview",
    "OrchestrationRoute",
    "OrchestrationTask",
    "RouteDescriptor",
]
