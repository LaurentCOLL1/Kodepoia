from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from kodepoia.core.trust import (
    TrustMetadata,
    TrustOrigin,
    external_origin_from_tags,
    provenance_sha256,
)


@dataclass(frozen=True, slots=True)
class ContextItem:
    source: str
    content: str
    priority: float = 0.5
    mandatory: bool = False
    tags: tuple[str, ...] = ()
    trust: TrustMetadata | None = None

    def __post_init__(self) -> None:
        if self.trust is not None:
            return
        origin = external_origin_from_tags(self.tags)
        if origin is None:
            return
        provenance = provenance_sha256(origin.value, self.source, self.content)
        if origin is TrustOrigin.UNKNOWN:
            trust = TrustMetadata.unknown(provenance_id=provenance)
        else:
            trust = TrustMetadata.untrusted(origin, provenance_id=provenance)
        object.__setattr__(self, "trust", trust)

    @property
    def estimated_tokens(self) -> int:
        overhead = 48 if self.trust is not None else 0
        return max(1, len(self.content) // 4 + overhead)

    def render(self) -> str:
        if self.trust is None:
            return f"## {self.source}\n{self.content}"
        metadata = self.trust
        header = (
            f"origin={metadata.origin.value}; level={metadata.level.value}; "
            f"authority={metadata.authority.value}; provenance_id={metadata.provenance_id}"
        )
        return (
            f"## {self.source}\n"
            f"SECURITY_CONTEXT: {header}\n"
            "<UNTRUSTED_DATA>\n"
            f"{self.content}\n"
            "</UNTRUSTED_DATA>"
        )


@dataclass(slots=True)
class ContextBundle:
    items: list[ContextItem] = field(default_factory=list)

    @property
    def estimated_tokens(self) -> int:
        return sum(item.estimated_tokens for item in self.items)

    def render(self) -> str:
        return "\n\n".join(item.render() for item in self.items)


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
