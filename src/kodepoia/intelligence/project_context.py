from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from kodepoia.intelligence.context import ContextBuilder, ContextBundle, ContextItem
from kodepoia.intelligence.project_knowledge import ProjectKnowledgeSourceKind
from kodepoia.intelligence.project_retrieval import (
    ProjectRetrievalHit,
    ProjectRetrievalResult,
    ProjectRetrievalSourceRef,
    ProjectRetrievalState,
)

PROJECT_CONTEXT_SCHEMA_VERSION = 1
_MAX_CONTEXT_BUDGET = 1_000_000


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


class ProjectContextOverride(StrEnum):
    AUTO = "auto"
    INCLUDE = "include"
    EXCLUDE = "exclude"


class ProjectContextDecision(StrEnum):
    SELECTED = "selected"
    OMITTED = "omitted"


class ProjectContextReason(StrEnum):
    USER_INCLUDED = "user_included"
    USER_EXCLUDED = "user_excluded"
    MANDATORY = "mandatory"
    WITHIN_BUDGET = "within_budget"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass(frozen=True, slots=True)
class ProjectContextCandidate:
    content_sha256: str
    primary_knowledge_id: str
    text: str
    retrieval_score: float
    source_refs: tuple[ProjectRetrievalSourceRef, ...]
    trust_classes: tuple[str, ...]
    freshness: tuple[str, ...]
    versions: tuple[str, ...]
    estimated_tokens: int
    schema_version: int = PROJECT_CONTEXT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != PROJECT_CONTEXT_SCHEMA_VERSION:
            raise ValueError("Unsupported project context candidate schema version")
        refs = tuple(sorted(self.source_refs, key=lambda value: value.knowledge_id))
        if not refs:
            raise ValueError("Context candidate requires source traceability")
        if self.primary_knowledge_id != refs[0].knowledge_id:
            raise ValueError("Context candidate primary source must be canonical")
        if self.estimated_tokens < 1:
            raise ValueError("Context candidate token estimate must be positive")
        object.__setattr__(self, "source_refs", refs)
        object.__setattr__(
            self,
            "trust_classes",
            tuple(sorted(set(self.trust_classes))),
        )
        object.__setattr__(
            self,
            "freshness",
            tuple(sorted(set(self.freshness))),
        )
        object.__setattr__(
            self,
            "versions",
            tuple(sorted(set(self.versions))),
        )

    @classmethod
    def from_hit(cls, hit: ProjectRetrievalHit) -> ProjectContextCandidate:
        provisional = _context_item_for_hit(hit, mandatory=False)
        return cls(
            content_sha256=hit.content_sha256,
            primary_knowledge_id=hit.primary_knowledge_id,
            text=hit.text,
            retrieval_score=hit.score,
            source_refs=hit.source_refs,
            trust_classes=tuple(ref.trust_class for ref in hit.source_refs),
            freshness=tuple(ref.freshness for ref in hit.source_refs),
            versions=tuple(ref.version for ref in hit.source_refs if ref.version),
            estimated_tokens=provisional.estimated_tokens,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "content_sha256": self.content_sha256,
            "primary_knowledge_id": self.primary_knowledge_id,
            "retrieval_score": self.retrieval_score,
            "source_refs": [ref.to_dict() for ref in self.source_refs],
            "trust_classes": list(self.trust_classes),
            "freshness": list(self.freshness),
            "versions": list(self.versions),
            "estimated_tokens": self.estimated_tokens,
        }


@dataclass(frozen=True, slots=True)
class ProjectContextSelection:
    candidate: ProjectContextCandidate
    decision: ProjectContextDecision
    reason: ProjectContextReason
    override: ProjectContextOverride
    mandatory: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "decision": self.decision.value,
            "reason": self.reason.value,
            "override": self.override.value,
            "mandatory": self.mandatory,
        }


@dataclass(frozen=True, slots=True)
class ProjectContextBundle:
    retrieval_digest_sha256: str
    budget_tokens: int
    selected_tokens: int
    selected: tuple[ProjectContextSelection, ...]
    omitted: tuple[ProjectContextSelection, ...]
    context: ContextBundle
    schema_version: int = PROJECT_CONTEXT_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != PROJECT_CONTEXT_SCHEMA_VERSION:
            raise ValueError("Unsupported project context bundle schema version")
        if self.budget_tokens < 1 or self.budget_tokens > _MAX_CONTEXT_BUDGET:
            raise ValueError("Context budget is outside the supported range")
        if self.selected_tokens != self.context.estimated_tokens:
            raise ValueError("Context token accounting does not match selected bundle")
        object.__setattr__(
            self,
            "digest_sha256",
            _sha256_payload(self._payload_without_digest()),
        )

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.budget_tokens - self.selected_tokens)

    @property
    def over_budget_tokens(self) -> int:
        return max(0, self.selected_tokens - self.budget_tokens)

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "retrieval_digest_sha256": self.retrieval_digest_sha256,
            "budget_tokens": self.budget_tokens,
            "selected_tokens": self.selected_tokens,
            "remaining_tokens": self.remaining_tokens,
            "over_budget_tokens": self.over_budget_tokens,
            "selected": [item.to_dict() for item in self.selected],
            "omitted": [item.to_dict() for item in self.omitted],
            "rendered_context": self.render(),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload

    def render(self) -> str:
        return self.context.render()


def _source_tags(refs: tuple[ProjectRetrievalSourceRef, ...]) -> tuple[str, ...]:
    tags = {"external", "untrusted", "project_knowledge"}
    kinds = {ref.source_kind for ref in refs}
    if ProjectKnowledgeSourceKind.RESEARCH_PACK in kinds:
        tags.add("research")
    if ProjectKnowledgeSourceKind.PROJECT_FILE in kinds:
        tags.add("document")
    if ProjectKnowledgeSourceKind.MEMORY in kinds:
        tags.add("memory")
    return tuple(sorted(tags))


def _citation_ids(refs: tuple[ProjectRetrievalSourceRef, ...]) -> tuple[str, ...]:
    values: set[str] = set()
    for ref in refs:
        raw = ref.provenance.get("citation_ids", [])
        if isinstance(raw, list):
            values.update(str(value) for value in raw if str(value).strip())
    return tuple(sorted(values))


def _trace_text(hit: ProjectRetrievalHit) -> str:
    source_ids = ",".join(ref.knowledge_id for ref in hit.source_refs)
    source_kinds = ",".join(
        sorted({ref.source_kind.value for ref in hit.source_refs})
    )
    locators = " | ".join(ref.locator for ref in hit.source_refs)
    citations = ",".join(_citation_ids(hit.source_refs)) or "none"
    trust = ",".join(sorted({ref.trust_class for ref in hit.source_refs}))
    freshness = ",".join(sorted({ref.freshness for ref in hit.source_refs}))
    versions = ",".join(
        sorted({ref.version for ref in hit.source_refs if ref.version})
    ) or "none"
    return (
        "SOURCE_TRACE: "
        f"content_sha256={hit.content_sha256}; "
        f"knowledge_ids={source_ids}; "
        f"source_kinds={source_kinds}; "
        f"locators={locators}; "
        f"citations={citations}; "
        f"trust={trust}; freshness={freshness}; versions={versions}; "
        f"retrieval_score={hit.score:.12f}\n\n"
        f"{hit.text}"
    )


def _context_item_for_hit(
    hit: ProjectRetrievalHit,
    *,
    mandatory: bool,
) -> ContextItem:
    return ContextItem(
        source=f"Project Knowledge {hit.content_sha256}",
        content=_trace_text(hit),
        priority=hit.score,
        mandatory=mandatory,
        tags=_source_tags(hit.source_refs),
    )


@dataclass(slots=True)
class ExplainableProjectContextBuilder:
    budget_tokens: int = 16_000

    def __post_init__(self) -> None:
        if self.budget_tokens < 1 or self.budget_tokens > _MAX_CONTEXT_BUDGET:
            raise ValueError(
                f"budget_tokens must be between 1 and {_MAX_CONTEXT_BUDGET}"
            )

    def build(
        self,
        retrieval: ProjectRetrievalResult,
        *,
        overrides: Mapping[str, ProjectContextOverride | str] | None = None,
        mandatory_content_sha256s: tuple[str, ...] = (),
    ) -> ProjectContextBundle:
        if retrieval.state is not ProjectRetrievalState.READY:
            raise ValueError(
                "Explainable context requires a READY project retrieval result"
            )
        raw_overrides = dict(overrides or {})
        mandatory_ids = set(mandatory_content_sha256s)
        hit_by_digest = {hit.content_sha256: hit for hit in retrieval.hits}
        unknown_override = sorted(set(raw_overrides) - set(hit_by_digest))
        if unknown_override:
            raise ValueError("Context override references an unknown retrieval hit")
        unknown_mandatory = sorted(mandatory_ids - set(hit_by_digest))
        if unknown_mandatory:
            raise ValueError("Mandatory context references an unknown retrieval hit")

        effective: list[
            tuple[
                ProjectRetrievalHit,
                ProjectContextCandidate,
                ProjectContextOverride,
                bool,
                ContextItem,
            ]
        ] = []
        excluded: list[ProjectContextSelection] = []
        for hit in retrieval.hits:
            candidate = ProjectContextCandidate.from_hit(hit)
            override = ProjectContextOverride(
                str(raw_overrides.get(hit.content_sha256, ProjectContextOverride.AUTO))
            )
            mandatory = hit.content_sha256 in mandatory_ids
            if override is ProjectContextOverride.EXCLUDE:
                excluded.append(
                    ProjectContextSelection(
                        candidate=candidate,
                        decision=ProjectContextDecision.OMITTED,
                        reason=ProjectContextReason.USER_EXCLUDED,
                        override=override,
                        mandatory=mandatory,
                    )
                )
                continue
            force = mandatory or override is ProjectContextOverride.INCLUDE
            context_item = _context_item_for_hit(hit, mandatory=force)
            effective.append((hit, candidate, override, mandatory, context_item))

        built = ContextBuilder(self.budget_tokens).build(
            item[-1] for item in effective
        )
        selected_sources = {item.source for item in built.items}
        selected: list[ProjectContextSelection] = []
        omitted: list[ProjectContextSelection] = list(excluded)
        for hit, candidate, override, mandatory, context_item in effective:
            if context_item.source in selected_sources:
                if override is ProjectContextOverride.INCLUDE:
                    reason = ProjectContextReason.USER_INCLUDED
                elif mandatory:
                    reason = ProjectContextReason.MANDATORY
                else:
                    reason = ProjectContextReason.WITHIN_BUDGET
                selected.append(
                    ProjectContextSelection(
                        candidate=candidate,
                        decision=ProjectContextDecision.SELECTED,
                        reason=reason,
                        override=override,
                        mandatory=mandatory,
                    )
                )
            else:
                omitted.append(
                    ProjectContextSelection(
                        candidate=candidate,
                        decision=ProjectContextDecision.OMITTED,
                        reason=ProjectContextReason.BUDGET_EXCEEDED,
                        override=override,
                        mandatory=mandatory,
                    )
                )

        order = {
            hit.content_sha256: index for index, hit in enumerate(retrieval.hits)
        }
        selected.sort(key=lambda item: order[item.candidate.content_sha256])
        omitted.sort(key=lambda item: order[item.candidate.content_sha256])
        return ProjectContextBundle(
            retrieval_digest_sha256=retrieval.digest_sha256,
            budget_tokens=self.budget_tokens,
            selected_tokens=built.estimated_tokens,
            selected=tuple(selected),
            omitted=tuple(omitted),
            context=built,
        )
