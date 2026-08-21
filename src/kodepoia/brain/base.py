from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class BrainMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class BrainResponse:
    content: str
    model: str
    thinking: str | None = None
    tool_calls: tuple[dict[str, Any], ...] = ()
    metrics: dict[str, Any] | None = None


class Brain(Protocol):
    def chat(self, model: str, messages: list[BrainMessage], **kwargs: Any) -> BrainResponse: ...
    def embed(self, model: str, inputs: str | list[str]) -> list[list[float]]: ...
