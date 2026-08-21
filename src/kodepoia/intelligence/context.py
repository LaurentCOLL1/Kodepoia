from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ContextItem:
    source: str
    content: str
    priority: float = 0.5
    mandatory: bool = False
    tags: tuple[str, ...] = ()

    @property
    def estimated_tokens(self) -> int:
        return max(1, len(self.content) // 4)


@dataclass(slots=True)
class ContextBundle:
    items: list[ContextItem] = field(default_factory=list)

    @property
    def estimated_tokens(self) -> int:
        return sum(item.estimated_tokens for item in self.items)

    def render(self) -> str:
        return "\n\n".join(f"## {item.source}\n{item.content}" for item in self.items)


class ContextBuilder:
    def __init__(self, budget_tokens: int = 16_000) -> None:
        self.budget_tokens = budget_tokens

    def build(self, candidates: Iterable[ContextItem]) -> ContextBundle:
        ordered = sorted(candidates, key=lambda item: (not item.mandatory, -item.priority))
        selected: list[ContextItem] = []
        used = 0
        for item in ordered:
            cost = item.estimated_tokens
            if item.mandatory or used + cost <= self.budget_tokens:
                selected.append(item)
                used += cost
        return ContextBundle(selected)
