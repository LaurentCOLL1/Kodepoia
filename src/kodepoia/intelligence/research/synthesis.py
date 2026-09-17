from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from kodepoia.core.secrets import KodeSecrets
from kodepoia.intelligence.research.contracts import ResearchFindingKind
from kodepoia.intelligence.research.evidence import (
    EvidenceLifecycle,
    EvidenceRevision,
    EvidenceSelection,
    EvidenceWorkspace,
    EvidenceWorkspaceRow,
)
from kodepoia.intelligence.research.orchestration import redact_research_text
from kodepoia.intelligence.research.store import ResearchStore
from kodepoia.kodecode.workspace import WorkspaceBoundary

CITED_SYNTHESIS_SCHEMA_VERSION = 1


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


def _validate_sha256(value: str, *, name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def _compact_text(value: str, *, limit: int = 700) -> str:
    compact = " ".join(value.split()).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


@dataclass(frozen=True, slots=True)
class CitationSnapshot:
    artifact_id: str
    revision_id: str
    source_identity_id: str
    canonical_locator: str
    content_sha256: str
    retrieved_at: str
    source_kind: str
    version: str = ""
    label: str = ""
    schema_version: int = CITED_SYNTHESIS_SCHEMA_VERSION
    citation_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != CITED_SYNTHESIS_SCHEMA_VERSION:
            raise ValueError("Unsupported cited synthesis schema version")
        for name, value in (
            ("artifact_id", self.artifact_id),
            ("revision_id", self.revision_id),
            ("source_identity_id", self.source_identity_id),
            ("content_sha256", self.content_sha256),
        ):
            _validate_sha256(value, name=name)
        if not self.canonical_locator.strip() or not self.retrieved_at.strip():
            raise ValueError("Citation snapshots require canonical locator and retrieval timestamp")
        object.__setattr__(
            self,
            "citation_id",
            _sha256(
                {
                    "artifact_id": self.artifact_id,
                    "revision_id": self.revision_id,
                    "source_identity_id": self.source_identity_id,
                    "canonical_locator": self.canonical_locator,
                    "content_sha256": self.content_sha256,
                    "retrieved_at": self.retrieved_at,
                    "source_kind": self.source_kind,
                    "version": self.version,
                    "label": self.label,
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "citation_id": self.citation_id,
            "artifact_id": self.artifact_id,
            "revision_id": self.revision_id,
            "source_identity_id": self.source_identity_id,
            "canonical_locator": self.canonical_locator,
            "content_sha256": self.content_sha256,
            "retrieved_at": self.retrieved_at,
            "source_kind": self.source_kind,
            "version": self.version,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CitationSnapshot:
        citation = cls(
            artifact_id=str(payload["artifact_id"]),
            revision_id=str(payload["revision_id"]),
            source_identity_id=str(payload["source_identity_id"]),
            canonical_locator=str(payload["canonical_locator"]),
            content_sha256=str(payload["content_sha256"]),
            retrieved_at=str(payload["retrieved_at"]),
            source_kind=str(payload["source_kind"]),
            version=str(payload.get("version", "")),
            label=str(payload.get("label", "")),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("citation_id", "")) != citation.citation_id:
            raise ValueError("Citation snapshot ID does not match immutable provenance")
        return citation


@dataclass(frozen=True, slots=True)
class SynthesizedClaim:
    kind: ResearchFindingKind
    claim: str
    citation_ids: tuple[str, ...] = ()
    confidence: float | None = None
    uncertainty: str = ""
    claim_id: str = field(init=False)

    def __post_init__(self) -> None:
        text = self.claim.strip()
        if not text:
            raise ValueError("Synthesized claim must not be empty")
        if self.kind is ResearchFindingKind.SOURCE_FACT and not self.citation_ids:
            raise ValueError("Source-backed synthesized claims require citations")
        if len(set(self.citation_ids)) != len(self.citation_ids):
            raise ValueError("Synthesized claim citations must be unique")
        for citation_id in self.citation_ids:
            _validate_sha256(citation_id, name="citation_id")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Synthesized claim confidence must be between 0 and 1")
        object.__setattr__(self, "claim", text)
        object.__setattr__(
            self,
            "claim_id",
            _sha256(
                {
                    "kind": self.kind.value,
                    "claim": text,
                    "citation_ids": list(self.citation_ids),
                    "confidence": self.confidence,
                    "uncertainty": self.uncertainty,
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "kind": self.kind.value,
            "claim": self.claim,
            "citation_ids": list(self.citation_ids),
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SynthesizedClaim:
        claim = cls(
            kind=ResearchFindingKind(str(payload["kind"])),
            claim=str(payload["claim"]),
            citation_ids=tuple(str(value) for value in payload.get("citation_ids", [])),
            confidence=None if payload.get("confidence") is None else float(payload["confidence"]),
            uncertainty=str(payload.get("uncertainty", "")),
        )
        if str(payload.get("claim_id", "")) != claim.claim_id:
            raise ValueError("Synthesized claim ID does not match canonical claim evidence")
        return claim


@dataclass(frozen=True, slots=True)
class ResearchSynthesis:
    question: str
    request_identity: str
    generated_at: str
    citations: tuple[CitationSnapshot, ...]
    claims: tuple[SynthesizedClaim, ...]
    synthesis: str
    conflicts: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
    schema_version: int = CITED_SYNTHESIS_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != CITED_SYNTHESIS_SCHEMA_VERSION:
            raise ValueError("Unsupported cited synthesis schema version")
        question = self.question.strip()
        if not question:
            raise ValueError("Synthesis question must not be empty")
        _validate_sha256(self.request_identity, name="request_identity")
        citation_ids = [item.citation_id for item in self.citations]
        if len(citation_ids) != len(set(citation_ids)):
            raise ValueError("Synthesis citations must be unique")
        available = set(citation_ids)
        referenced = {value for claim in self.claims for value in claim.citation_ids}
        if referenced - available:
            raise ValueError("Synthesized claims reference unavailable citation snapshots")
        if not self.claims:
            raise ValueError("Synthesis requires at least one claim")
        object.__setattr__(self, "question", question)
        object.__setattr__(self, "digest_sha256", _sha256(self._payload_without_digest()))

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "question": self.question,
            "request_identity": self.request_identity,
            "generated_at": self.generated_at,
            "citations": [item.to_dict() for item in self.citations],
            "claims": [item.to_dict() for item in self.claims],
            "synthesis": self.synthesis,
            "conflicts": list(self.conflicts),
            "uncertainty": list(self.uncertainty),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ResearchSynthesis:
        synthesis = cls(
            question=str(payload["question"]),
            request_identity=str(payload["request_identity"]),
            generated_at=str(payload["generated_at"]),
            citations=tuple(CitationSnapshot.from_dict(value) for value in payload.get("citations", [])),
            claims=tuple(SynthesizedClaim.from_dict(value) for value in payload.get("claims", [])),
            synthesis=str(payload.get("synthesis", "")),
            conflicts=tuple(str(value) for value in payload.get("conflicts", [])),
            uncertainty=tuple(str(value) for value in payload.get("uncertainty", [])),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("digest_sha256", "")) != synthesis.digest_sha256:
            raise ValueError("Research synthesis digest does not match canonical synthesis evidence")
        return synthesis


@dataclass(frozen=True, slots=True)
class ResearchPack:
    synthesis: ResearchSynthesis
    schema_version: int = CITED_SYNTHESIS_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != CITED_SYNTHESIS_SCHEMA_VERSION:
            raise ValueError("Unsupported Research Pack schema version")
        object.__setattr__(
            self,
            "digest_sha256",
            _sha256(
                {
                    "schema_version": self.schema_version,
                    "synthesis_digest_sha256": self.synthesis.digest_sha256,
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "digest_sha256": self.digest_sha256,
            "synthesis_digest_sha256": self.synthesis.digest_sha256,
            "synthesis": self.synthesis.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ResearchPack:
        raw_synthesis = payload.get("synthesis")
        if not isinstance(raw_synthesis, Mapping):
            raise ValueError("Research Pack synthesis must be an object")
        pack = cls(
            synthesis=ResearchSynthesis.from_dict(raw_synthesis),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("synthesis_digest_sha256", "")) != pack.synthesis.digest_sha256:
            raise ValueError("Research Pack synthesis digest does not match embedded synthesis")
        if str(payload.get("digest_sha256", "")) != pack.digest_sha256:
            raise ValueError("Research Pack digest does not match canonical pack evidence")
        return pack


@dataclass(slots=True)
class ResearchPackStore:
    project_root: Path
    _boundary: WorkspaceBoundary = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        self.project_root = root
        self._boundary = WorkspaceBoundary(root)

    def _require_project(self) -> None:
        if not self._boundary.resolve(".kodepoia").is_dir():
            raise FileNotFoundError("Kodepoia project metadata not found")

    def _path(self, digest: str) -> Path:
        _validate_sha256(digest, name="Research Pack digest")
        return self._boundary.resolve(f".kodepoia/research/packs/{digest}.json")

    def save(self, pack: ResearchPack) -> Path:
        self._require_project()
        path = self._path(pack.digest_sha256)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(pack.to_dict(), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if path.is_file():
            if path.read_text(encoding="utf-8") != text:
                raise ValueError("Research Pack digest collision")
            return path
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
        return path

    def load(self, digest: str) -> ResearchPack:
        self._require_project()
        payload = json.loads(self._path(digest).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Research Pack document must be a JSON object")
        return ResearchPack.from_dict(payload)


def _matching_revision(row: EvidenceWorkspaceRow, revisions: Iterable[EvidenceRevision]) -> EvidenceRevision:
    candidates = [
        revision
        for revision in revisions
        if revision.artifact_id == row.artifact_id
        and revision.source_identity_id == row.source_identity_id
    ]
    if not candidates:
        raise ValueError(f"Fetched evidence has no persisted revision: {row.artifact_id}")
    exact = [revision for revision in candidates if revision.retrieved_at == row.retrieved_at]
    selected = exact or candidates
    return sorted(selected, key=lambda item: (item.retrieved_at, item.revision_id))[-1]


@dataclass(slots=True)
class CitedSynthesisService:
    project_root: Path
    secrets: KodeSecrets | None = None
    _store: ResearchStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        self.project_root = root
        self._store = ResearchStore(root)

    def synthesize(
        self,
        question: str,
        workspace: EvidenceWorkspace,
        *,
        explicit_selections: Mapping[str, EvidenceSelection],
        generated_at: str,
    ) -> ResearchSynthesis:
        clean_question = redact_research_text(question, secrets=self.secrets).strip()
        if not clean_question:
            raise ValueError("Synthesis question must not be empty")
        included_rows = tuple(
            row
            for row in workspace.rows
            if row.lifecycle is EvidenceLifecycle.FETCHED
            and bool(row.artifact_id)
            and explicit_selections.get(row.artifact_id) is EvidenceSelection.INCLUDED
        )
        if not included_rows:
            raise ValueError("Synthesis requires explicitly included fetched evidence")

        revisions = self._store.list_evidence_revisions()
        citations: list[CitationSnapshot] = []
        claims: list[SynthesizedClaim] = []
        conflicts: list[str] = []
        uncertainty: list[str] = []
        for row in sorted(included_rows, key=lambda item: (item.source_identity_id, item.artifact_id)):
            artifact = self._store.load_artifact(row.artifact_id)
            revision = _matching_revision(row, revisions)
            locator = redact_research_text(revision.canonical_locator, secrets=self.secrets)
            citation = CitationSnapshot(
                artifact_id=artifact.artifact_id,
                revision_id=revision.revision_id,
                source_identity_id=revision.source_identity_id,
                canonical_locator=locator,
                content_sha256=artifact.content_sha256,
                retrieved_at=revision.retrieved_at,
                source_kind=revision.source_kind,
                version=revision.version,
                label=redact_research_text(artifact.source.title, secrets=self.secrets),
            )
            citations.append(citation)
            claim_text = _compact_text(redact_research_text(artifact.content, secrets=self.secrets))
            if not claim_text:
                claim_text = f"Fetched evidence from {locator} contains no renderable text."
            row_uncertainty: list[str] = []
            if row.freshness.casefold() == "stale":
                row_uncertainty.append("stale evidence")
            if row.suspicious:
                row_uncertainty.append("guarded suspicious source content")
            if row.has_version_conflict:
                conflict = (
                    f"Version conflict for {locator}: "
                    + ", ".join(row.conflicting_versions)
                )
                conflicts.append(conflict)
                row_uncertainty.append("conflicting source versions")
            uncertainty_text = "; ".join(row_uncertainty)
            if uncertainty_text:
                uncertainty.append(f"{locator}: {uncertainty_text}")
            claims.append(
                SynthesizedClaim(
                    kind=ResearchFindingKind.SOURCE_FACT,
                    claim=claim_text,
                    citation_ids=(citation.citation_id,),
                    confidence=0.65 if row_uncertainty else 0.9,
                    uncertainty=uncertainty_text,
                )
            )

        citation_ids = tuple(item.citation_id for item in citations)
        claims.append(
            SynthesizedClaim(
                kind=ResearchFindingKind.INFERENCE,
                claim=(
                    f"Synthesis is limited to {len(citations)} explicitly included fetched "
                    "evidence revision(s); excluded or unfetched sources were not used."
                ),
                citation_ids=citation_ids,
                confidence=0.8,
                uncertainty="; ".join(sorted(set(uncertainty))),
            )
        )
        rendered = "\n".join(
            f"[{index}] {claim.kind.value}: {claim.claim}"
            for index, claim in enumerate(claims, start=1)
        )
        request_identity = _sha256({"question": clean_question})
        return ResearchSynthesis(
            question=clean_question,
            request_identity=request_identity,
            generated_at=generated_at,
            citations=tuple(citations),
            claims=tuple(claims),
            synthesis=rendered,
            conflicts=tuple(sorted(set(conflicts))),
            uncertainty=tuple(sorted(set(uncertainty))),
        )

    @staticmethod
    def pack(synthesis: ResearchSynthesis) -> ResearchPack:
        return ResearchPack(synthesis=synthesis)
