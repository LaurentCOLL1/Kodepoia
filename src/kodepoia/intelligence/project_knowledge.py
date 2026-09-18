from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import quote

from kodepoia.core.research_guard import ResearchGuard
from kodepoia.core.secrets import KodeSecrets
from kodepoia.intelligence.memory import MemoryStore
from kodepoia.intelligence.research.orchestration import redact_research_text
from kodepoia.intelligence.research.synthesis import ResearchPackStore
from kodepoia.kodecode.workspace import WorkspaceBoundary

PROJECT_KNOWLEDGE_SCHEMA_VERSION = 1
_DEFAULT_MAX_FILE_BYTES = 2 * 1024 * 1024
_DEFAULT_MAX_MEMORY_ITEMS = 10_000
_SHA256_CHARS = frozenset("0123456789abcdef")


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


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: str, name: str) -> None:
    if len(value) != 64 or any(character not in _SHA256_CHARS for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def _required_text(value: str, name: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError(f"{name} must not be empty")
    return clean


def _project_scope(value: str) -> str:
    scope = _required_text(value, "project_scope")
    lowered = scope.casefold()
    if lowered == "global" or lowered.startswith("global:"):
        raise ValueError("Project Knowledge requires a non-global project scope")
    return scope


def _json_object(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        normalized = json.loads(_canonical_json(dict(value)))
    except (TypeError, ValueError) as exc:
        raise ValueError("Project Knowledge provenance must be canonical JSON") from exc
    if not isinstance(normalized, dict):
        raise ValueError("Project Knowledge provenance must be an object")
    return normalized


class ProjectKnowledgeSourceKind(StrEnum):
    RESEARCH_PACK = "research_pack"
    PROJECT_FILE = "project_file"
    MEMORY = "memory"


class ProjectKnowledgeState(StrEnum):
    ACTIVE = "active"
    INCLUDED = "included"
    EXCLUDED = "excluded"
    INVALIDATED = "invalidated"


@dataclass(frozen=True, slots=True)
class ProjectKnowledgeItem:
    project_scope: str
    source_kind: ProjectKnowledgeSourceKind
    source_identity: str
    source_digest_sha256: str
    content_sha256: str
    text: str
    trust_class: str
    freshness: str
    locator: str
    version: str = ""
    state: ProjectKnowledgeState = ProjectKnowledgeState.ACTIVE
    suspicious: bool = False
    guard_indicators: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = PROJECT_KNOWLEDGE_SCHEMA_VERSION
    knowledge_id: str = field(init=False)
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != PROJECT_KNOWLEDGE_SCHEMA_VERSION:
            raise ValueError("Unsupported Project Knowledge schema version")
        scope = _project_scope(self.project_scope)
        source_identity = _required_text(self.source_identity, "source_identity")
        trust_class = _required_text(self.trust_class, "trust_class")
        freshness = _required_text(self.freshness, "freshness")
        locator = _required_text(self.locator, "locator")
        _require_sha256(self.source_digest_sha256, "source_digest_sha256")
        _require_sha256(self.content_sha256, "content_sha256")
        indicators = tuple(
            sorted(
                set(
                    _required_text(value, "guard_indicator")
                    for value in self.guard_indicators
                )
            )
        )
        provenance = _json_object(self.provenance)
        object.__setattr__(self, "project_scope", scope)
        object.__setattr__(self, "source_identity", source_identity)
        object.__setattr__(self, "trust_class", trust_class)
        object.__setattr__(self, "freshness", freshness)
        object.__setattr__(self, "locator", locator)
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(self, "guard_indicators", indicators)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(
            self,
            "knowledge_id",
            _sha256_payload(
                {
                    "project_scope": scope,
                    "source_kind": self.source_kind.value,
                    "source_identity": source_identity,
                }
            ),
        )
        object.__setattr__(self, "digest_sha256", _sha256_payload(self._payload_without_digest()))

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_scope": self.project_scope,
            "source_kind": self.source_kind.value,
            "source_identity": self.source_identity,
            "source_digest_sha256": self.source_digest_sha256,
            "content_sha256": self.content_sha256,
            "text": self.text,
            "trust_class": self.trust_class,
            "freshness": self.freshness,
            "locator": self.locator,
            "version": self.version,
            "state": self.state.value,
            "suspicious": self.suspicious,
            "guard_indicators": list(self.guard_indicators),
            "provenance": self.provenance,
            "knowledge_id": self.knowledge_id,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ProjectKnowledgeItem:
        raw_provenance = payload.get("provenance", {})
        if not isinstance(raw_provenance, Mapping):
            raise ValueError("Project Knowledge provenance must be an object")
        item = cls(
            project_scope=str(payload["project_scope"]),
            source_kind=ProjectKnowledgeSourceKind(str(payload["source_kind"])),
            source_identity=str(payload["source_identity"]),
            source_digest_sha256=str(payload["source_digest_sha256"]),
            content_sha256=str(payload["content_sha256"]),
            text=str(payload.get("text", "")),
            trust_class=str(payload["trust_class"]),
            freshness=str(payload["freshness"]),
            locator=str(payload["locator"]),
            version=str(payload.get("version", "")),
            state=ProjectKnowledgeState(str(payload.get("state", ProjectKnowledgeState.ACTIVE.value))),
            suspicious=bool(payload.get("suspicious", False)),
            guard_indicators=tuple(str(value) for value in payload.get("guard_indicators", [])),
            provenance=raw_provenance,
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("knowledge_id", "")) != item.knowledge_id:
            raise ValueError("Project Knowledge ID does not match canonical source identity")
        if str(payload.get("digest_sha256", "")) != item.digest_sha256:
            raise ValueError("Project Knowledge digest does not match canonical item")
        return item


@dataclass(frozen=True, slots=True)
class ProjectKnowledgeCatalog:
    project_scope: str
    items: tuple[ProjectKnowledgeItem, ...]
    schema_version: int = PROJECT_KNOWLEDGE_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != PROJECT_KNOWLEDGE_SCHEMA_VERSION:
            raise ValueError("Unsupported Project Knowledge catalog schema version")
        scope = _project_scope(self.project_scope)
        ordered = tuple(sorted(self.items, key=lambda item: item.knowledge_id))
        if any(item.project_scope != scope for item in ordered):
            raise ValueError("Project Knowledge catalog contains an out-of-scope item")
        ids = [item.knowledge_id for item in ordered]
        if len(ids) != len(set(ids)):
            raise ValueError("Project Knowledge catalog identities must be unique")
        object.__setattr__(self, "project_scope", scope)
        object.__setattr__(self, "items", ordered)
        object.__setattr__(
            self,
            "digest_sha256",
            _sha256_payload(
                {
                    "schema_version": self.schema_version,
                    "project_scope": scope,
                    "items": [item.to_dict() for item in ordered],
                }
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_scope": self.project_scope,
            "items": [item.to_dict() for item in self.items],
            "digest_sha256": self.digest_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ProjectKnowledgeCatalog:
        raw_items = payload.get("items", [])
        if not isinstance(raw_items, list):
            raise ValueError("Project Knowledge catalog items must be an array")
        catalog = cls(
            project_scope=str(payload["project_scope"]),
            items=tuple(ProjectKnowledgeItem.from_dict(value) for value in raw_items),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("digest_sha256", "")) != catalog.digest_sha256:
            raise ValueError("Project Knowledge catalog digest does not match canonical catalog")
        return catalog


@dataclass(slots=True)
class ProjectKnowledgeBuilder:
    project_root: Path
    project_scope: str
    secrets: KodeSecrets | None = None
    max_file_bytes: int = _DEFAULT_MAX_FILE_BYTES
    max_memory_items: int = _DEFAULT_MAX_MEMORY_ITEMS
    _boundary: WorkspaceBoundary = field(init=False, repr=False)
    _packs: ResearchPackStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        if self.max_file_bytes < 1:
            raise ValueError("max_file_bytes must be positive")
        if self.max_memory_items < 1:
            raise ValueError("max_memory_items must be positive")
        self.project_root = root
        self.project_scope = _project_scope(self.project_scope)
        self._boundary = WorkspaceBoundary(root)
        self._packs = ResearchPackStore(root)

    def _require_project(self) -> None:
        metadata = self._boundary.resolve(".kodepoia", must_exist=True)
        if not metadata.is_dir():
            raise FileNotFoundError("Kodepoia project metadata not found")

    def _guard(self, text: str) -> tuple[bool, tuple[str, ...]]:
        guarded = ResearchGuard().wrap(text)
        return guarded.suspicious, tuple(sorted(set(guarded.indicators)))

    def research_pack_items(self) -> tuple[ProjectKnowledgeItem, ...]:
        self._require_project()
        pack_root = self._boundary.resolve(".kodepoia/research/packs")
        if not pack_root.exists():
            return ()
        if not pack_root.is_dir():
            raise ValueError("Research Pack storage must be a directory")
        items: list[ProjectKnowledgeItem] = []
        for path in sorted(pack_root.glob("*.json"), key=lambda candidate: candidate.name):
            pack = self._packs.load(path.stem)
            if pack.digest_sha256 != path.stem:
                raise ValueError("Research Pack filename does not match immutable pack digest")
            text = redact_research_text(pack.synthesis.synthesis, secrets=self.secrets)
            suspicious, indicators = self._guard(text)
            citations = pack.synthesis.citations
            provenance = {
                "pack_digest_sha256": pack.digest_sha256,
                "synthesis_digest_sha256": pack.synthesis.digest_sha256,
                "request_identity": pack.synthesis.request_identity,
                "generated_at": pack.synthesis.generated_at,
                "citation_ids": sorted(citation.citation_id for citation in citations),
                "artifact_ids": sorted({citation.artifact_id for citation in citations}),
                "revision_ids": sorted({citation.revision_id for citation in citations}),
                "source_identity_ids": sorted({citation.source_identity_id for citation in citations}),
                "citation_versions": sorted({citation.version for citation in citations if citation.version}),
                "conflicts": [
                    redact_research_text(value, secrets=self.secrets)
                    for value in pack.synthesis.conflicts
                ],
                "uncertainty": [
                    redact_research_text(value, secrets=self.secrets)
                    for value in pack.synthesis.uncertainty
                ],
            }
            items.append(
                ProjectKnowledgeItem(
                    project_scope=self.project_scope,
                    source_kind=ProjectKnowledgeSourceKind.RESEARCH_PACK,
                    source_identity=pack.digest_sha256,
                    source_digest_sha256=pack.digest_sha256,
                    content_sha256=_sha256_bytes(text.encode("utf-8")),
                    text=text,
                    trust_class="external_guarded_untrusted",
                    freshness="immutable",
                    locator=f"research-pack:///{pack.digest_sha256}",
                    version=str(pack.schema_version),
                    suspicious=suspicious,
                    guard_indicators=indicators,
                    provenance=provenance,
                )
            )
        return tuple(items)

    def project_file_item(self, path: str | Path) -> ProjectKnowledgeItem:
        self._require_project()
        target = self._boundary.resolve(path, must_exist=True)
        if not target.is_file():
            raise ValueError("Project Knowledge file source must be a regular file")
        relative = self._boundary.relative(target)
        if relative == ".kodepoia/knowledge" or relative.startswith(".kodepoia/knowledge/"):
            raise ValueError("Project Knowledge cannot recursively index its derived catalog")
        if target.stat().st_size > self.max_file_bytes:
            raise ValueError("Project Knowledge file source exceeds the bounded byte limit")
        payload = target.read_bytes()
        try:
            raw_text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Project Knowledge file source must be UTF-8 text") from exc
        text = redact_research_text(raw_text, secrets=self.secrets)
        suspicious, indicators = self._guard(text)
        source_digest = _sha256_bytes(payload)
        safe_relative = redact_research_text(relative, secrets=self.secrets)
        source_identity = _sha256_payload({"project_relative_path": relative})
        return ProjectKnowledgeItem(
            project_scope=self.project_scope,
            source_kind=ProjectKnowledgeSourceKind.PROJECT_FILE,
            source_identity=source_identity,
            source_digest_sha256=source_digest,
            content_sha256=_sha256_bytes(text.encode("utf-8")),
            text=text,
            trust_class="project_untrusted",
            freshness="current",
            locator=f"project:///{quote(safe_relative, safe='/')}",
            suspicious=suspicious,
            guard_indicators=indicators,
            provenance={
                "project_relative_path": safe_relative,
                "source_content_sha256": source_digest,
                "source_bytes": len(payload),
                "redacted": text != raw_text or safe_relative != relative,
            },
        )

    def memory_items(self, memory: MemoryStore) -> tuple[ProjectKnowledgeItem, ...]:
        self._require_project()
        records = memory.list(scope=self.project_scope, limit=self.max_memory_items + 1)
        if len(records) > self.max_memory_items:
            raise ValueError("Project Knowledge memory projection exceeds the bounded item limit")
        items: list[ProjectKnowledgeItem] = []
        for record in records:
            if record.project_scope != self.project_scope:
                raise ValueError("MemoryStore returned an out-of-project record")
            _require_sha256(record.integrity_digest, "memory integrity_digest")
            text = redact_research_text(record.content, secrets=self.secrets)
            safe_origin = redact_research_text(record.origin, secrets=self.secrets)
            suspicious, indicators = self._guard(text)
            source_identity = _sha256_payload({"origin": record.origin, "kind": record.kind})
            items.append(
                ProjectKnowledgeItem(
                    project_scope=self.project_scope,
                    source_kind=ProjectKnowledgeSourceKind.MEMORY,
                    source_identity=source_identity,
                    source_digest_sha256=record.integrity_digest,
                    content_sha256=_sha256_bytes(text.encode("utf-8")),
                    text=text,
                    trust_class=record.trust_class,
                    freshness="current",
                    locator=f"memory:///{source_identity}",
                    version=str(record.version),
                    suspicious=suspicious,
                    guard_indicators=indicators,
                    provenance={
                        "origin": safe_origin,
                        "kind": record.kind,
                        "record_class": record.record_class,
                        "record_version": record.version,
                        "integrity_digest": record.integrity_digest,
                        "metadata_sha256": _sha256_payload(record.metadata),
                        "redacted": text != record.content or safe_origin != record.origin,
                    },
                )
            )
        return tuple(items)

    def build(
        self,
        *,
        project_files: Iterable[str | Path] = (),
        memory: MemoryStore | None = None,
    ) -> ProjectKnowledgeCatalog:
        items = list(self.research_pack_items())
        for path in project_files:
            items.append(self.project_file_item(path))
        if memory is not None:
            items.extend(self.memory_items(memory))
        unique: dict[str, ProjectKnowledgeItem] = {}
        for item in items:
            existing = unique.get(item.knowledge_id)
            if existing is not None and existing.digest_sha256 != item.digest_sha256:
                raise ValueError("Project Knowledge identity collision")
            unique[item.knowledge_id] = item
        return ProjectKnowledgeCatalog(
            project_scope=self.project_scope,
            items=tuple(unique.values()),
        )


@dataclass(slots=True)
class ProjectKnowledgeStore:
    project_root: Path
    project_scope: str
    _boundary: WorkspaceBoundary = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        self.project_root = root
        self.project_scope = _project_scope(self.project_scope)
        self._boundary = WorkspaceBoundary(root)

    @property
    def path(self) -> Path:
        return self._boundary.resolve(".kodepoia/knowledge/catalog-v1.json")

    def _require_project(self) -> None:
        metadata = self._boundary.resolve(".kodepoia", must_exist=True)
        if not metadata.is_dir():
            raise FileNotFoundError("Kodepoia project metadata not found")

    def save(self, catalog: ProjectKnowledgeCatalog) -> Path:
        self._require_project()
        if catalog.project_scope != self.project_scope:
            raise ValueError("Project Knowledge catalog scope does not match store scope")
        path = self.path
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(
            catalog.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        ) + "\n"
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
        return path

    def load(self) -> ProjectKnowledgeCatalog:
        self._require_project()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Project Knowledge catalog document must be an object")
        catalog = ProjectKnowledgeCatalog.from_dict(payload)
        if catalog.project_scope != self.project_scope:
            raise ValueError("Project Knowledge catalog scope does not match store scope")
        return catalog
