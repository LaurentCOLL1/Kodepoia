from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol


@dataclass(frozen=True, slots=True)
class BrainMessage:
    role: str
    content: str
    images: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BrainResponse:
    content: str
    model: str
    thinking: str | None = None
    tool_calls: tuple[dict[str, Any], ...] = ()
    metrics: dict[str, Any] | None = None
    done: bool = True


class Brain(Protocol):
    def chat(self, model: str, messages: list[BrainMessage], **kwargs: Any) -> BrainResponse: ...

    def stream_chat(
        self,
        model: str,
        messages: list[BrainMessage],
        **kwargs: Any,
    ) -> Iterable[BrainResponse]: ...

    def embed(self, model: str, inputs: str | list[str], **kwargs: Any) -> list[list[float]]: ...
