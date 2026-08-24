from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contracts import MediaState, stable_id
from .contracts import TTSBackendCapabilities


@dataclass(frozen=True, slots=True)
class TTSBackendDescriptor:
    backend_id: str
    state: MediaState
    role: str
    canonical_production: bool
    capabilities: TTSBackendCapabilities | None = None

    def __post_init__(self) -> None:
        stable_id(self.backend_id, field="backend_id")
        stable_id(self.role, field="role")
        if self.state not in {MediaState.AVAILABLE, MediaState.UNAVAILABLE, MediaState.BLOCKED, MediaState.RIGHTS_BLOCKED}:
            raise ValueError("invalid TTS backend state")
        if self.state is MediaState.AVAILABLE and self.capabilities is None:
            raise ValueError("available backend requires capabilities")
        if self.capabilities is not None and self.capabilities.backend_id != self.backend_id:
            raise ValueError("backend descriptor/capability identity mismatch")

    def canonical(self) -> dict[str, Any]:
        return {
            "backend_id": self.backend_id,
            "state": self.state.value,
            "role": self.role,
            "canonical_production": self.canonical_production,
            "capabilities": None if self.capabilities is None else self.capabilities.canonical(),
        }


class TTSBackendRegistry:
    """Small deterministic registry. Missing backends are UNAVAILABLE, never implicit failures."""

    def __init__(self) -> None:
        self._items: dict[str, TTSBackendDescriptor] = {}

    def register(self, descriptor: TTSBackendDescriptor) -> None:
        if descriptor.backend_id in self._items:
            raise ValueError(f"TTS backend already registered: {descriptor.backend_id}")
        self._items[descriptor.backend_id] = descriptor

    def get(self, backend_id: str, *, role: str = "production") -> TTSBackendDescriptor:
        stable_id(backend_id, field="backend_id")
        stable_id(role, field="role")
        return self._items.get(
            backend_id,
            TTSBackendDescriptor(
                backend_id=backend_id,
                state=MediaState.UNAVAILABLE,
                role=role,
                canonical_production=False,
                capabilities=None,
            ),
        )

    def canonical(self) -> list[dict[str, Any]]:
        return [self._items[key].canonical() for key in sorted(self._items)]
