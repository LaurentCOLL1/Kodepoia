from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ModelRole(StrEnum):
    FAST = "fast"
    CORE = "core"
    CODER = "coder"
    EMBED = "embed"
    VISION = "vision"


@dataclass(frozen=True, slots=True)
class ModelSpec:
    name: str
    role: ModelRole
    estimated_vram_mb: int | None = None
    supports_vision: bool = False
    supports_tools: bool = False
    supports_structured: bool = False


@dataclass(frozen=True, slots=True)
class TaskProfile:
    code_complexity: float = 0.0
    visual_requirement: float = 0.0
    repository_scope: float = 0.0
    reasoning_depth: float = 0.0
    latency_importance: float = 0.5
    needs_embeddings: bool = False


@dataclass(slots=True)
class ModelRegistry:
    models: list[ModelSpec] = field(default_factory=list)

    def add(self, model: ModelSpec) -> None:
        self.models = [item for item in self.models if item.name != model.name]
        self.models.append(model)

    def by_role(self, role: ModelRole) -> list[ModelSpec]:
        return [item for item in self.models if item.role is role]


class KodeModelRouter:
    def __init__(self, registry: ModelRegistry, max_vram_mb: int = 12_000) -> None:
        self.registry = registry
        self.max_vram_mb = max_vram_mb

    def route(self, task: TaskProfile) -> ModelSpec:
        if task.needs_embeddings:
            role = ModelRole.EMBED
        elif task.visual_requirement >= 0.5:
            vision = [m for m in self.registry.models if m.supports_vision]
            if vision:
                return self._fit(vision)[0]
            role = ModelRole.VISION
        elif max(task.code_complexity, task.repository_scope, task.reasoning_depth) >= 0.75:
            role = ModelRole.CODER
        elif task.latency_importance >= 0.75 and task.code_complexity < 0.5:
            role = ModelRole.FAST
        else:
            role = ModelRole.CORE
        candidates = self.registry.by_role(role) or self.registry.by_role(ModelRole.CORE)
        if not candidates:
            raise LookupError(f"No model registered for role {role}")
        return self._fit(candidates)[0]

    def _fit(self, candidates: list[ModelSpec]) -> list[ModelSpec]:
        fitting = [m for m in candidates if m.estimated_vram_mb is None or m.estimated_vram_mb <= self.max_vram_mb]
        return fitting or candidates
