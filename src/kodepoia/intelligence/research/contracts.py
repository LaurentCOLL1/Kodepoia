from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from kodepoia.core.research_guard import GuardedResearch, ResearchGuard

SCHEMA_VERSION = 1


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _content_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _validate_timestamp(value: str, *, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")


def _validate_sha256(value: str, *, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")


class ResearchSourceKind(StrEnum):
    LOCAL = "local"
    OFFICIAL_DOCS = "official_docs"
    WEB = "web"
    GITHUB = "github"
    COMMUNITY = "community"
    YOUTUBE = "youtube"


class ResearchStatus(StrEnum):
    UNKNOWN = "unknown"
    READY = "ready"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"
    STALE = "stale"


class ResearchFreshness(StrEnum):
    UNKNOWN = "unknown"
    CURRENT = "current"
    STALE = "stale"
    NOT_APPLICABLE = "not_applicable"


class ResearchTrust(StrEnum):
    UNTRUSTED = "untrusted"
    GUARDED = "guarded"


class ResearchFindingKind(StrEnum):
    SOURCE_FACT = "source_fact"
    INFERENCE = "inference"


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    query: str
    source_kinds: tuple[ResearchSourceKind, ...]
    created_at: str
    project_scope: str = ""
    max_results: int = 20
    schema_version: int = SCHEMA_VERSION
    request_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Unsupported research request schema version")
        query = self.query.strip()
        if not query:
            raise ValueError("Research query must not be empty")
        if not self.source_kinds:
            raise ValueError("Research request must select at least one source kind")
        if len(set(self.source_kinds)) != len(self.source_kinds):
            raise ValueError("Research source kinds must be unique")
        if not 1 <= self.max_results <= 100:
            raise ValueError("Research max_results must be between 1 and 100")
        _validate_timestamp(self.created_at, field_name="created_at")
        object.__setattr__(self, "query", query)
        object.__setattr__(self, "project_scope", self.project_scope.strip())
        object.__setattr__(self, "request_id", _sha256(self.identity_payload()))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "query": self.query.strip(),
            "source_kinds": sorted(kind.value for kind in self.source_kinds),
            "project_scope": self.project_scope.strip(),
            "max_results": self.max_results,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "query": self.query,
            "source_kinds": [kind.value for kind in self.source_kinds],
            "created_at": self.created_at,
            "project_scope": self.project_scope,
            "max_results": self.max_results,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResearchRequest:
        request = cls(
            query=str(payload["query"]),
            source_kinds=tuple(ResearchSourceKind(value) for value in payload["source_kinds"]),
            created_at=str(payload["created_at"]),
            project_scope=str(payload.get("project_scope", "")),
            max_results=int(payload.get("max_results", 20)),
            schema_version=int(payload.get("schema_version", 0)),
        )
        stored = str(payload.get("request_id", ""))
        if stored != request.request_id:
            raise ValueError("Research request ID does not match canonical request evidence")
        return request


@dataclass(frozen=True, slots=True)
class ResearchSource:
    kind: ResearchSourceKind
    locator: str
    status: ResearchStatus = ResearchStatus.UNKNOWN
    title: str = ""
    publisher: str = ""
    author: str = ""
    product: str = ""
    version: str = ""
    published_at: str | None = None
    updated_at: str | None = None
    source_id: str = field(init=False)

    def __post_init__(self) -> None:
        locator = self.locator.strip()
        if not locator:
            raise ValueError("Research source locator must not be empty")
        for name, value in (("published_at", self.published_at), ("updated_at", self.updated_at)):
            if value is not None:
                _validate_timestamp(value, field_name=name)
        object.__setattr__(self, "locator", locator)
        object.__setattr__(
            self,
            "source_id",
            _sha256({"kind": self.kind.value, "locator": locator}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "kind": self.kind.value,
            "locator": self.locator,
            "status": self.status.value,
            "title": self.title,
            "publisher": self.publisher,
            "author": self.author,
            "product": self.product,
            "version": self.version,
            "published_at": self.published_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResearchSource:
        source = cls(
            kind=ResearchSourceKind(payload["kind"]),
            locator=str(payload["locator"]),
            status=ResearchStatus(payload.get("status", ResearchStatus.UNKNOWN.value)),
            title=str(payload.get("title", "")),
            publisher=str(payload.get("publisher", "")),
            author=str(payload.get("author", "")),
            product=str(payload.get("product", "")),
            version=str(payload.get("version", "")),
            published_at=(None if payload.get("published_at") is None else str(payload["published_at"])),
            updated_at=(None if payload.get("updated_at") is None else str(payload["updated_at"])),
        )
        if str(payload.get("source_id", "")) != source.source_id:
            raise ValueError("Research source ID does not match canonical source evidence")
        return source


@dataclass(frozen=True, slots=True)
class ResearchArtifact:
    source: ResearchSource
    content: str
    retrieved_at: str
    guarded: GuardedResearch
    freshness: ResearchFreshness = ResearchFreshness.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION
    content_sha256: str = field(init=False)
    artifact_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Unsupported research artifact schema version")
        _validate_timestamp(self.retrieved_at, field_name="retrieved_at")
        _canonical_json(self.metadata)
        digest = _content_sha256(self.content)
        guard_version = int(getattr(self.guarded, "guard_version", 1))
        if guard_version != ResearchGuard.VERSION:
            raise ValueError("Research artifact guard version is unsupported")
        if self.guarded.content != self.content:
            raise ValueError("Guarded research content must equal artifact content")
        object.__setattr__(self, "content_sha256", digest)
        object.__setattr__(
            self,
            "artifact_id",
            _sha256({"source_id": self.source.source_id, "content_sha256": digest}),
        )

    @property
    def trust(self) -> ResearchTrust:
        return ResearchTrust.GUARDED

    @classmethod
    def from_content(
        cls,
        *,
        source: ResearchSource,
        content: str,
        retrieved_at: str,
        freshness: ResearchFreshness = ResearchFreshness.UNKNOWN,
        metadata: dict[str, Any] | None = None,
        guard: ResearchGuard | None = None,
    ) -> ResearchArtifact:
        active_guard = guard or ResearchGuard()
        return cls(
            source=source,
            content=content,
            retrieved_at=retrieved_at,
            guarded=active_guard.wrap(content),
            freshness=freshness,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_id": self.artifact_id,
            "content_sha256": self.content_sha256,
            "source": self.source.to_dict(),
            "content": self.content,
            "retrieved_at": self.retrieved_at,
            "freshness": self.freshness.value,
            "trust": self.trust.value,
            "guard": {
                "version": int(getattr(self.guarded, "guard_version", 1)),
                "suspicious": self.guarded.suspicious,
                "indicators": list(self.guarded.indicators),
                "instruction": self.guarded.instruction,
            },
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResearchArtifact:
        source_payload = payload.get("source")
        if not isinstance(source_payload, dict):
            raise ValueError("Research artifact source must be an object")
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("Research artifact metadata must be an object")
        artifact = cls.from_content(
            source=ResearchSource.from_dict(source_payload),
            content=str(payload["content"]),
            retrieved_at=str(payload["retrieved_at"]),
            freshness=ResearchFreshness(payload.get("freshness", ResearchFreshness.UNKNOWN.value)),
            metadata=metadata,
        )
        if int(payload.get("schema_version", 0)) != SCHEMA_VERSION:
            raise ValueError("Unsupported research artifact schema version")
        if str(payload.get("artifact_id", "")) != artifact.artifact_id:
            raise ValueError("Research artifact ID does not match content evidence")
        stored_digest = str(payload.get("content_sha256", ""))
        _validate_sha256(stored_digest, field_name="content_sha256")
        if stored_digest != artifact.content_sha256:
            raise ValueError("Research artifact content SHA-256 does not match content evidence")
        if payload.get("trust") != artifact.trust.value:
            raise ValueError("Research artifact trust state does not match guarded evidence")
        stored_guard = payload.get("guard")
        if not isinstance(stored_guard, dict):
            raise ValueError("Research artifact guard evidence must be an object")
        expected_guard = artifact.to_dict()["guard"]
        if stored_guard != expected_guard:
            raise ValueError("Research artifact guard evidence does not match recomputed evidence")
        return artifact


@dataclass(frozen=True, slots=True)
class ResearchCitation:
    artifact_id: str
    locator: str
    anchor_start: str = ""
    anchor_end: str = ""
    label: str = ""
    citation_id: str = field(init=False)

    def __post_init__(self) -> None:
        _validate_sha256(self.artifact_id, field_name="artifact_id")
        locator = self.locator.strip()
        if not locator:
            raise ValueError("Research citation locator must not be empty")
        object.__setattr__(self, "locator", locator)
        object.__setattr__(
            self,
            "citation_id",
            _sha256(
                {
                    "artifact_id": self.artifact_id,
                    "locator": locator,
                    "anchor_start": self.anchor_start,
                    "anchor_end": self.anchor_end,
                    "label": self.label,
                }
            ),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "citation_id": self.citation_id,
            "artifact_id": self.artifact_id,
            "locator": self.locator,
            "anchor_start": self.anchor_start,
            "anchor_end": self.anchor_end,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResearchCitation:
        citation = cls(
            artifact_id=str(payload["artifact_id"]),
            locator=str(payload["locator"]),
            anchor_start=str(payload.get("anchor_start", "")),
            anchor_end=str(payload.get("anchor_end", "")),
            label=str(payload.get("label", "")),
        )
        if str(payload.get("citation_id", "")) != citation.citation_id:
            raise ValueError("Research citation ID does not match citation evidence")
        return citation


@dataclass(frozen=True, slots=True)
class ResearchFinding:
    kind: ResearchFindingKind
    claim: str
    citations: tuple[ResearchCitation, ...] = ()
    confidence: float | None = None
    finding_id: str = field(init=False)

    def __post_init__(self) -> None:
        claim = self.claim.strip()
        if not claim:
            raise ValueError("Research finding claim must not be empty")
        if self.kind is ResearchFindingKind.SOURCE_FACT and not self.citations:
            raise ValueError("Source facts require at least one citation")
        citation_ids = [citation.citation_id for citation in self.citations]
        if len(citation_ids) != len(set(citation_ids)):
            raise ValueError("Research finding citations must be unique")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Research finding confidence must be between 0 and 1")
        object.__setattr__(self, "claim", claim)
        object.__setattr__(
            self,
            "finding_id",
            _sha256(
                {
                    "kind": self.kind.value,
                    "claim": claim,
                    "citation_ids": citation_ids,
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "kind": self.kind.value,
            "claim": self.claim,
            "citations": [citation.to_dict() for citation in self.citations],
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResearchFinding:
        raw_citations = payload.get("citations", [])
        if not isinstance(raw_citations, list):
            raise ValueError("Research finding citations must be a list")
        finding = cls(
            kind=ResearchFindingKind(payload["kind"]),
            claim=str(payload["claim"]),
            citations=tuple(ResearchCitation.from_dict(item) for item in raw_citations),
            confidence=None if payload.get("confidence") is None else float(payload["confidence"]),
        )
        if str(payload.get("finding_id", "")) != finding.finding_id:
            raise ValueError("Research finding ID does not match finding evidence")
        return finding


@dataclass(frozen=True, slots=True)
class ResearchReport:
    request: ResearchRequest
    artifacts: tuple[ResearchArtifact, ...]
    findings: tuple[ResearchFinding, ...]
    status: ResearchStatus
    generated_at: str
    schema_version: int = SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Unsupported research report schema version")
        _validate_timestamp(self.generated_at, field_name="generated_at")
        artifact_ids = [artifact.artifact_id for artifact in self.artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("Research report artifacts must be unique")
        finding_ids = [finding.finding_id for finding in self.findings]
        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError("Research report findings must be unique")
        available = set(artifact_ids)
        referenced = {
            citation.artifact_id
            for finding in self.findings
            for citation in finding.citations
        }
        missing = referenced - available
        if missing:
            raise ValueError(f"Research report citations reference absent artifacts: {sorted(missing)}")
        if self.status is ResearchStatus.READY and not self.artifacts:
            raise ValueError("Ready research reports require at least one artifact")
        object.__setattr__(self, "digest_sha256", _sha256(self._payload_without_digest()))

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request": self.request.to_dict(),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "findings": [finding.to_dict() for finding in self.findings],
            "status": self.status.value,
            "generated_at": self.generated_at,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResearchReport:
        request_payload = payload.get("request")
        if not isinstance(request_payload, dict):
            raise ValueError("Research report request must be an object")
        raw_artifacts = payload.get("artifacts")
        raw_findings = payload.get("findings")
        if not isinstance(raw_artifacts, list) or not isinstance(raw_findings, list):
            raise ValueError("Research report artifacts/findings must be lists")
        report = cls(
            request=ResearchRequest.from_dict(request_payload),
            artifacts=tuple(ResearchArtifact.from_dict(item) for item in raw_artifacts),
            findings=tuple(ResearchFinding.from_dict(item) for item in raw_findings),
            status=ResearchStatus(payload["status"]),
            generated_at=str(payload["generated_at"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        stored = str(payload.get("digest_sha256", ""))
        _validate_sha256(stored, field_name="digest_sha256")
        if stored != report.digest_sha256:
            raise ValueError("Research report digest does not match canonical report evidence")
        return report
