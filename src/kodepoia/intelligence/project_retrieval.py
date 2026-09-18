from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from kodepoia.exceptions import BrainUnavailable
from kodepoia.intelligence.project_knowledge import (
    ProjectKnowledgeCatalog,
    ProjectKnowledgeItem,
    ProjectKnowledgeSourceKind,
    ProjectKnowledgeState,
)

PROJECT_RETRIEVAL_SCHEMA_VERSION = 1
_MAX_RETRIEVAL_LIMIT = 100
_MAX_CANDIDATES = 1000


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


def _project_scope(value: str) -> str:
    scope = _required_text(value, "project_scope")
    lowered = scope.casefold()
    if lowered == "global" or lowered.startswith("global:"):
        raise ValueError("Project retrieval requires a non-global project scope")
    return scope


def _finite_score(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


@dataclass(frozen=True, slots=True)
class ProjectEmbeddingIdentity:
    provider: str
    model: str
    version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _required_text(self.provider, "provider"))
        object.__setattr__(self, "model", _required_text(self.model, "model"))
        object.__setattr__(self, "version", _required_text(self.version, "version"))

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "model": self.model,
            "version": self.version,
        }


class ProjectEmbeddingProvider(Protocol):
    @property
    def identity(self) -> ProjectEmbeddingIdentity: ...

    def embed(self, texts: tuple[str, ...]) -> list[list[float]]: ...


class ProjectRetrievalState(StrEnum):
    READY = "ready"
    EMPTY = "empty"
    EMBEDDING_UNAVAILABLE = "embedding_unavailable"
    CANDIDATE_LIMIT_EXCEEDED = "candidate_limit_exceeded"


@dataclass(frozen=True, slots=True)
class ProjectRetrievalRequest:
    project_scope: str
    query: str
    limit: int = 20
    max_candidates: int = 500
    min_score: float = 0.0
    source_kinds: tuple[ProjectKnowledgeSourceKind, ...] = ()
    schema_version: int = PROJECT_RETRIEVAL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != PROJECT_RETRIEVAL_SCHEMA_VERSION:
            raise ValueError("Unsupported project retrieval request schema version")
        scope = _project_scope(self.project_scope)
        query = _required_text(self.query, "query")
        if self.limit < 1 or self.limit > _MAX_RETRIEVAL_LIMIT:
            raise ValueError(f"limit must be between 1 and {_MAX_RETRIEVAL_LIMIT}")
        if self.max_candidates < 1 or self.max_candidates > _MAX_CANDIDATES:
            raise ValueError(
                f"max_candidates must be between 1 and {_MAX_CANDIDATES}"
            )
        score = _finite_score(self.min_score, "min_score")
        if score < 0.0 or score > 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0")
        kinds = tuple(sorted(set(self.source_kinds), key=lambda value: value.value))
        object.__setattr__(self, "project_scope", scope)
        object.__setattr__(self, "query", query)
        object.__setattr__(self, "min_score", score)
        object.__setattr__(self, "source_kinds", kinds)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_scope": self.project_scope,
            "query": self.query,
            "limit": self.limit,
            "max_candidates": self.max_candidates,
            "min_score": self.min_score,
            "source_kinds": [value.value for value in self.source_kinds],
        }


@dataclass(frozen=True, slots=True)
class ProjectRetrievalSourceRef:
    knowledge_id: str
    source_kind: ProjectKnowledgeSourceKind
    source_identity: str
    source_digest_sha256: str
    content_sha256: str
    locator: str
    trust_class: str
    freshness: str
    version: str
    state: ProjectKnowledgeState
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_item(cls, item: ProjectKnowledgeItem) -> ProjectRetrievalSourceRef:
        provenance = json.loads(_canonical_json(dict(item.provenance)))
        return cls(
            knowledge_id=item.knowledge_id,
            source_kind=item.source_kind,
            source_identity=item.source_identity,
            source_digest_sha256=item.source_digest_sha256,
            content_sha256=item.content_sha256,
            locator=item.locator,
            trust_class=item.trust_class,
            freshness=item.freshness,
            version=item.version,
            state=item.state,
            provenance=provenance,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "source_kind": self.source_kind.value,
            "source_identity": self.source_identity,
            "source_digest_sha256": self.source_digest_sha256,
            "content_sha256": self.content_sha256,
            "locator": self.locator,
            "trust_class": self.trust_class,
            "freshness": self.freshness,
            "version": self.version,
            "state": self.state.value,
            "provenance": self.provenance,
        }


@dataclass(frozen=True, slots=True)
class ProjectRetrievalHit:
    content_sha256: str
    score: float
    primary_knowledge_id: str
    text: str
    source_refs: tuple[ProjectRetrievalSourceRef, ...]

    def __post_init__(self) -> None:
        score = _finite_score(self.score, "score")
        if score < 0.0 or score > 1.0:
            raise ValueError("score must be between 0.0 and 1.0")
        refs = tuple(sorted(self.source_refs, key=lambda value: value.knowledge_id))
        if not refs:
            raise ValueError("Retrieval hit must preserve at least one source reference")
        if self.primary_knowledge_id != refs[0].knowledge_id:
            raise ValueError("primary_knowledge_id must be the canonical first source")
        if any(ref.content_sha256 != self.content_sha256 for ref in refs):
            raise ValueError("Duplicate source references must share content digest")
        object.__setattr__(self, "score", score)
        object.__setattr__(self, "source_refs", refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_sha256": self.content_sha256,
            "score": self.score,
            "primary_knowledge_id": self.primary_knowledge_id,
            "text": self.text,
            "source_refs": [value.to_dict() for value in self.source_refs],
        }


@dataclass(frozen=True, slots=True)
class ProjectRetrievalResult:
    state: ProjectRetrievalState
    request: ProjectRetrievalRequest
    catalog_digest_sha256: str
    provider_identity: ProjectEmbeddingIdentity | None
    eligible_candidates: int
    normalized_candidates: int
    hits: tuple[ProjectRetrievalHit, ...]
    diagnostic: str
    schema_version: int = PROJECT_RETRIEVAL_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != PROJECT_RETRIEVAL_SCHEMA_VERSION:
            raise ValueError("Unsupported project retrieval result schema version")
        if self.eligible_candidates < 0 or self.normalized_candidates < 0:
            raise ValueError("Retrieval candidate counts must be non-negative")
        if self.normalized_candidates > self.eligible_candidates:
            raise ValueError("Normalized candidate count cannot exceed eligible count")
        hits = tuple(self.hits)
        if len(hits) > self.request.limit:
            raise ValueError("Retrieval result exceeds request limit")
        object.__setattr__(self, "hits", hits)
        object.__setattr__(
            self,
            "digest_sha256",
            _sha256_payload(self._payload_without_digest()),
        )

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "state": self.state.value,
            "request": self.request.to_dict(),
            "catalog_digest_sha256": self.catalog_digest_sha256,
            "provider_identity": (
                self.provider_identity.to_dict()
                if self.provider_identity is not None
                else None
            ),
            "eligible_candidates": self.eligible_candidates,
            "normalized_candidates": self.normalized_candidates,
            "hits": [hit.to_dict() for hit in self.hits],
            "diagnostic": self.diagnostic,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload


@dataclass(frozen=True, slots=True)
class _NormalizedCandidate:
    content_sha256: str
    text: str
    refs: tuple[ProjectRetrievalSourceRef, ...]


class ProjectSemanticRetriever:
    """Bounded project-only semantic retrieval with no implicit provider creation."""

    _ELIGIBLE_STATES = frozenset(
        {ProjectKnowledgeState.ACTIVE, ProjectKnowledgeState.INCLUDED}
    )

    @staticmethod
    def _vector(raw: list[float]) -> list[float]:
        values = [float(value) for value in raw]
        if not values or not all(math.isfinite(value) for value in values):
            raise ValueError("Embedding vector must contain finite values")
        return values

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if len(left) != len(right) or not left:
            raise ValueError("Embedding dimensions do not match")
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return max(-1.0, min(1.0, dot / (left_norm * right_norm)))

    @staticmethod
    def _normalize(
        items: tuple[ProjectKnowledgeItem, ...],
    ) -> tuple[_NormalizedCandidate, ...]:
        grouped: dict[str, list[ProjectKnowledgeItem]] = {}
        for item in items:
            grouped.setdefault(item.content_sha256, []).append(item)
        normalized: list[_NormalizedCandidate] = []
        for content_sha256 in sorted(grouped):
            duplicates = sorted(
                grouped[content_sha256],
                key=lambda item: item.knowledge_id,
            )
            texts = {item.text for item in duplicates}
            if len(texts) != 1:
                raise ValueError(
                    "Project Knowledge content digest collision has inconsistent text"
                )
            refs = tuple(
                ProjectRetrievalSourceRef.from_item(item) for item in duplicates
            )
            normalized.append(
                _NormalizedCandidate(
                    content_sha256=content_sha256,
                    text=duplicates[0].text,
                    refs=refs,
                )
            )
        return tuple(normalized)

    @staticmethod
    def _result(
        *,
        state: ProjectRetrievalState,
        request: ProjectRetrievalRequest,
        catalog: ProjectKnowledgeCatalog,
        provider_identity: ProjectEmbeddingIdentity | None,
        eligible_candidates: int,
        normalized_candidates: int,
        hits: tuple[ProjectRetrievalHit, ...] = (),
        diagnostic: str,
    ) -> ProjectRetrievalResult:
        return ProjectRetrievalResult(
            state=state,
            request=request,
            catalog_digest_sha256=catalog.digest_sha256,
            provider_identity=provider_identity,
            eligible_candidates=eligible_candidates,
            normalized_candidates=normalized_candidates,
            hits=hits,
            diagnostic=diagnostic,
        )

    def retrieve(
        self,
        catalog: ProjectKnowledgeCatalog,
        request: ProjectRetrievalRequest,
        *,
        provider: ProjectEmbeddingProvider | None,
    ) -> ProjectRetrievalResult:
        if request.project_scope != catalog.project_scope:
            raise ValueError(
                "Retrieval request project scope does not match catalog scope"
            )

        allowed_kinds = set(request.source_kinds)
        eligible = tuple(
            item
            for item in catalog.items
            if item.project_scope == request.project_scope
            and item.state in self._ELIGIBLE_STATES
            and item.text.strip()
            and (not allowed_kinds or item.source_kind in allowed_kinds)
        )
        eligible_count = len(eligible)
        if eligible_count > request.max_candidates:
            return self._result(
                state=ProjectRetrievalState.CANDIDATE_LIMIT_EXCEEDED,
                request=request,
                catalog=catalog,
                provider_identity=None,
                eligible_candidates=eligible_count,
                normalized_candidates=0,
                diagnostic=(
                    f"{eligible_count} eligible candidates exceed the explicit "
                    f"max_candidates={request.max_candidates}; provider not invoked"
                ),
            )

        normalized = self._normalize(eligible)
        normalized_count = len(normalized)
        if normalized_count == 0:
            return self._result(
                state=ProjectRetrievalState.EMPTY,
                request=request,
                catalog=catalog,
                provider_identity=None,
                eligible_candidates=eligible_count,
                normalized_candidates=0,
                diagnostic="No eligible project knowledge candidates",
            )

        if provider is None:
            return self._result(
                state=ProjectRetrievalState.EMBEDDING_UNAVAILABLE,
                request=request,
                catalog=catalog,
                provider_identity=None,
                eligible_candidates=eligible_count,
                normalized_candidates=normalized_count,
                diagnostic="No embedding provider was supplied",
            )

        identity = provider.identity
        texts = (request.query,) + tuple(candidate.text for candidate in normalized)
        try:
            raw_vectors = provider.embed(texts)
        except BrainUnavailable as exc:
            return self._result(
                state=ProjectRetrievalState.EMBEDDING_UNAVAILABLE,
                request=request,
                catalog=catalog,
                provider_identity=identity,
                eligible_candidates=eligible_count,
                normalized_candidates=normalized_count,
                diagnostic=f"Embedding provider unavailable: {exc}",
            )

        if len(raw_vectors) != len(texts):
            raise ValueError("Embedding provider returned an unexpected vector count")
        vectors = [self._vector(raw) for raw in raw_vectors]
        query_vector = vectors[0]
        hits: list[ProjectRetrievalHit] = []
        for candidate, vector in zip(normalized, vectors[1:], strict=True):
            score = (self._cosine(query_vector, vector) + 1.0) / 2.0
            if score < request.min_score:
                continue
            hits.append(
                ProjectRetrievalHit(
                    content_sha256=candidate.content_sha256,
                    score=score,
                    primary_knowledge_id=candidate.refs[0].knowledge_id,
                    text=candidate.text,
                    source_refs=candidate.refs,
                )
            )
        hits.sort(
            key=lambda hit: (
                -hit.score,
                hit.content_sha256,
                hit.primary_knowledge_id,
            )
        )
        bounded_hits = tuple(hits[: request.limit])
        if not bounded_hits:
            return self._result(
                state=ProjectRetrievalState.EMPTY,
                request=request,
                catalog=catalog,
                provider_identity=identity,
                eligible_candidates=eligible_count,
                normalized_candidates=normalized_count,
                diagnostic="Embedding capability is ready; no candidate met min_score",
            )
        return self._result(
            state=ProjectRetrievalState.READY,
            request=request,
            catalog=catalog,
            provider_identity=identity,
            eligible_candidates=eligible_count,
            normalized_candidates=normalized_count,
            hits=bounded_hits,
            diagnostic="Semantic retrieval completed",
        )
