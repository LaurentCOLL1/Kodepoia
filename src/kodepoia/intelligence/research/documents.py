from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any
from urllib.parse import quote, urlsplit

import yaml

from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchCitation,
    ResearchFreshness,
    ResearchSource,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.store import ResearchStore
from kodepoia.kodecode.workspace import WorkspaceBoundary

MANIFEST_SCHEMA_VERSION = 1


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


class DocumentFormat(StrEnum):
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"


@dataclass(frozen=True, slots=True)
class OfficialDocEntry:
    key: str
    local_root: str
    canonical_base_url: str
    publisher: str
    product: str
    version: str = ""
    domain: str = field(init=False)
    entry_id: str = field(init=False)

    def __post_init__(self) -> None:
        key = self.key.strip()
        local_root = self.local_root.strip().replace("\\", "/")
        base = self.canonical_base_url.strip().rstrip("/")
        publisher = self.publisher.strip()
        product = self.product.strip()
        version = self.version.strip()
        if not key:
            raise ValueError("Official documentation key must not be empty")
        if not local_root:
            raise ValueError("Official documentation local_root must not be empty")
        path = Path(local_root)
        windows_path = PureWindowsPath(local_root)
        if path.is_absolute() or windows_path.is_absolute() or ".." in path.parts:
            raise ValueError("Official documentation local_root must stay project-relative")
        parsed = urlsplit(base)
        if parsed.scheme.lower() != "https" or not parsed.hostname:
            raise ValueError("Official documentation canonical base must be an HTTPS URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Official documentation canonical base must not contain credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("Official documentation canonical base must not contain query/fragment")
        if not publisher or not product:
            raise ValueError("Official documentation publisher and product are required")
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "local_root", local_root.rstrip("/"))
        object.__setattr__(self, "canonical_base_url", base)
        object.__setattr__(self, "publisher", publisher)
        object.__setattr__(self, "product", product)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "domain", parsed.hostname.lower())
        object.__setattr__(self, "entry_id", _canonical_digest(self.identity_payload()))

    def identity_payload(self) -> dict[str, str]:
        return {
            "key": self.key.strip(),
            "local_root": self.local_root.strip().replace("\\", "/").rstrip("/"),
            "canonical_base_url": self.canonical_base_url.strip().rstrip("/"),
            "publisher": self.publisher.strip(),
            "product": self.product.strip(),
            "version": self.version.strip(),
            "domain": self.domain,
        }

    def to_dict(self) -> dict[str, str]:
        return {"entry_id": self.entry_id, **self.identity_payload()}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> OfficialDocEntry:
        entry = cls(
            key=str(payload["key"]),
            local_root=str(payload["local_root"]),
            canonical_base_url=str(payload["canonical_base_url"]),
            publisher=str(payload["publisher"]),
            product=str(payload["product"]),
            version=str(payload.get("version", "")),
        )
        if "domain" in payload and str(payload["domain"]).lower() != entry.domain:
            raise ValueError("Official documentation domain does not match canonical base")
        if "entry_id" in payload and str(payload["entry_id"]) != entry.entry_id:
            raise ValueError("Official documentation entry ID does not match canonical evidence")
        return entry


@dataclass(frozen=True, slots=True)
class OfficialDocsManifest:
    entries: tuple[OfficialDocEntry, ...]
    schema_version: int = MANIFEST_SCHEMA_VERSION
    manifest_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError("Unsupported official documentation manifest schema version")
        if not self.entries:
            raise ValueError("Official documentation manifest requires at least one entry")
        keys = [entry.key for entry in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("Official documentation manifest keys must be unique")
        object.__setattr__(
            self,
            "manifest_id",
            _canonical_digest(
                {
                    "schema_version": self.schema_version,
                    "entries": [entry.to_dict() for entry in self.entries],
                }
            ),
        )

    def get(self, key: str) -> OfficialDocEntry:
        for entry in self.entries:
            if entry.key == key:
                return entry
        raise KeyError(f"Unknown official documentation source: {key}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> OfficialDocsManifest:
        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, list):
            raise ValueError("Official documentation manifest entries must be a list")
        manifest = cls(
            entries=tuple(OfficialDocEntry.from_dict(item) for item in raw_entries),
            schema_version=int(payload.get("schema_version", 0)),
        )
        stored_id = payload.get("manifest_id")
        if stored_id is not None and str(stored_id) != manifest.manifest_id:
            raise ValueError("Official documentation manifest ID does not match canonical evidence")
        return manifest

    @classmethod
    def load(cls, project_root: Path, path: str | Path) -> OfficialDocsManifest:
        boundary = WorkspaceBoundary(project_root.resolve(strict=False))
        target = boundary.resolve(path, must_exist=True)
        if not target.is_file():
            raise ValueError("Official documentation manifest must be a regular file")
        text = target.read_text(encoding="utf-8")
        if target.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text)
        if not isinstance(payload, dict):
            raise ValueError("Official documentation manifest must be an object")
        return cls.from_dict(payload)


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    artifact_id: str
    source_locator: str
    content: str
    line_start: int
    line_end: int
    heading: str = ""
    chunk_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.line_start < 1 or self.line_end < self.line_start:
            raise ValueError("Document chunk line range is invalid")
        if not _is_sha256(self.artifact_id):
            raise ValueError("Document chunk artifact ID must be a lowercase SHA-256 digest")
        if not self.source_locator.strip():
            raise ValueError("Document chunk source locator must not be empty")
        object.__setattr__(
            self,
            "chunk_id",
            _canonical_digest(
                {
                    "artifact_id": self.artifact_id,
                    "source_locator": self.source_locator,
                    "content_sha256": hashlib.sha256(self.content.encode("utf-8")).hexdigest(),
                    "line_start": self.line_start,
                    "line_end": self.line_end,
                    "heading": self.heading,
                }
            ),
        )

    @property
    def citation(self) -> ResearchCitation:
        return ResearchCitation(
            artifact_id=self.artifact_id,
            locator=self.source_locator,
            anchor_start=f"L{self.line_start}",
            anchor_end=f"L{self.line_end}",
            label=self.heading,
        )


@dataclass(frozen=True, slots=True)
class DocumentResearchResult:
    status: ResearchStatus
    artifact: ResearchArtifact | None
    chunks: tuple[DocumentChunk, ...]
    cache_hit: bool = False
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status in {ResearchStatus.READY, ResearchStatus.STALE} and self.artifact is None:
            raise ValueError("Available document result requires an artifact")
        if self.artifact is None and self.chunks:
            raise ValueError("Unavailable document result cannot contain chunks")
        if self.cache_hit and self.artifact is None:
            raise ValueError("Cache hit requires an artifact")


@dataclass(slots=True)
class LocalDocumentAdapter:
    project_root: Path
    max_read_bytes: int = 2 * 1024 * 1024
    max_chunk_lines: int = 80
    _boundary: WorkspaceBoundary = field(init=False, repr=False)
    _store: ResearchStore = field(init=False, repr=False)

    SUPPORTED_SUFFIXES = {
        ".txt": DocumentFormat.TEXT,
        ".md": DocumentFormat.MARKDOWN,
        ".markdown": DocumentFormat.MARKDOWN,
        ".json": DocumentFormat.JSON,
        ".yaml": DocumentFormat.YAML,
        ".yml": DocumentFormat.YAML,
    }

    def __post_init__(self) -> None:
        root = self.project_root.resolve(strict=False)
        if self.max_read_bytes < 1:
            raise ValueError("Document byte limit must be positive")
        if self.max_chunk_lines < 1:
            raise ValueError("Document chunk line limit must be positive")
        self.project_root = root
        self._boundary = WorkspaceBoundary(root)
        self._store = ResearchStore(root)

    @staticmethod
    def _freshness(
        *,
        source_kind: ResearchSourceKind,
        version: str,
        target_version: str | None,
    ) -> ResearchFreshness:
        if source_kind is ResearchSourceKind.LOCAL and not version and target_version is None:
            return ResearchFreshness.NOT_APPLICABLE
        if not version or target_version is None or not target_version.strip():
            return ResearchFreshness.UNKNOWN
        if version.strip() == target_version.strip():
            return ResearchFreshness.CURRENT
        return ResearchFreshness.STALE

    @staticmethod
    def _unavailable(reason: str) -> DocumentResearchResult:
        return DocumentResearchResult(
            status=ResearchStatus.UNAVAILABLE,
            artifact=None,
            chunks=(),
            cache_hit=False,
            reason=reason,
        )

    def research(
        self,
        path: str | Path,
        *,
        retrieved_at: str,
        source_kind: ResearchSourceKind = ResearchSourceKind.LOCAL,
        canonical_locator: str | None = None,
        title: str = "",
        publisher: str = "",
        product: str = "",
        version: str = "",
        target_version: str | None = None,
        persist_cache: bool = True,
    ) -> DocumentResearchResult:
        if source_kind not in {ResearchSourceKind.LOCAL, ResearchSourceKind.OFFICIAL_DOCS}:
            raise ValueError("R7.2 document adapter only accepts local or official_docs sources")
        try:
            target = self._boundary.resolve(path, must_exist=True)
        except FileNotFoundError:
            return self._unavailable("not_found")
        if not target.is_file():
            return self._unavailable("not_regular_file")
        document_format = self.SUPPORTED_SUFFIXES.get(target.suffix.lower())
        if document_format is None:
            return self._unavailable("unsupported_format")
        if target.stat().st_size > self.max_read_bytes:
            return self._unavailable("too_large")
        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return self._unavailable("invalid_utf8")
        if document_format is DocumentFormat.JSON:
            try:
                json.loads(content)
            except json.JSONDecodeError:
                return self._unavailable("invalid_json")
        elif document_format is DocumentFormat.YAML:
            try:
                yaml.safe_load(content)
            except yaml.YAMLError:
                return self._unavailable("invalid_yaml")

        relative = self._boundary.relative(target)
        locator = canonical_locator or f"project:///{quote(relative, safe='/')}"
        freshness = self._freshness(
            source_kind=source_kind,
            version=version,
            target_version=target_version,
        )
        status = ResearchStatus.STALE if freshness is ResearchFreshness.STALE else ResearchStatus.READY
        source = ResearchSource(
            kind=source_kind,
            locator=locator,
            status=status,
            title=title or target.name,
            publisher=publisher,
            product=product,
            version=version,
        )
        candidate = ResearchArtifact.from_content(
            source=source,
            content=content,
            retrieved_at=retrieved_at,
            freshness=freshness,
            metadata={
                "document_format": document_format.value,
                "project_relative_path": relative,
            },
        )
        artifact = candidate
        cache_hit = False
        if persist_cache:
            if self._store.has_artifact(candidate.artifact_id):
                cached = self._store.load_artifact(candidate.artifact_id)
                if (
                    cached.source.to_dict() == candidate.source.to_dict()
                    and cached.freshness is candidate.freshness
                    and cached.metadata == candidate.metadata
                ):
                    artifact = cached
                    cache_hit = True
                else:
                    self._store.save_artifact(candidate)
            else:
                self._store.save_artifact(candidate)
        chunks = self._chunk(artifact, document_format)
        return DocumentResearchResult(
            status=status,
            artifact=artifact,
            chunks=chunks,
            cache_hit=cache_hit,
        )

    def _chunk(
        self,
        artifact: ResearchArtifact,
        document_format: DocumentFormat,
    ) -> tuple[DocumentChunk, ...]:
        lines = artifact.content.splitlines()
        if not lines:
            return (
                DocumentChunk(
                    artifact_id=artifact.artifact_id,
                    source_locator=artifact.source.locator,
                    content="",
                    line_start=1,
                    line_end=1,
                ),
            )
        ranges: list[tuple[int, int, str]] = []
        start = 1
        heading = ""
        for index, line in enumerate(lines, start=1):
            next_heading = ""
            if document_format is DocumentFormat.MARKDOWN:
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    marker = len(stripped) - len(stripped.lstrip("#"))
                    if marker > 0 and len(stripped) > marker and stripped[marker] == " ":
                        next_heading = stripped[marker + 1 :].strip()
            if next_heading and index > start:
                ranges.append((start, index - 1, heading))
                start = index
                heading = next_heading
            elif next_heading:
                heading = next_heading
            if index - start + 1 >= self.max_chunk_lines:
                ranges.append((start, index, heading))
                start = index + 1
        if start <= len(lines):
            ranges.append((start, len(lines), heading))
        return tuple(
            DocumentChunk(
                artifact_id=artifact.artifact_id,
                source_locator=artifact.source.locator,
                content="\n".join(lines[line_start - 1 : line_end]),
                line_start=line_start,
                line_end=line_end,
                heading=chunk_heading,
            )
            for line_start, line_end, chunk_heading in ranges
        )


@dataclass(slots=True)
class OfficialDocsAdapter:
    project_root: Path
    manifest: OfficialDocsManifest
    max_read_bytes: int = 2 * 1024 * 1024
    max_chunk_lines: int = 80
    _project_boundary: WorkspaceBoundary = field(init=False, repr=False)
    _local: LocalDocumentAdapter = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = self.project_root.resolve(strict=False)
        self.project_root = root
        self._project_boundary = WorkspaceBoundary(root)
        self._local = LocalDocumentAdapter(
            root,
            max_read_bytes=self.max_read_bytes,
            max_chunk_lines=self.max_chunk_lines,
        )

    def research(
        self,
        key: str,
        relative_path: str | Path,
        *,
        retrieved_at: str,
        target_version: str | None = None,
        persist_cache: bool = True,
    ) -> DocumentResearchResult:
        entry = self.manifest.get(key)
        snapshot_root = self._project_boundary.resolve(entry.local_root, must_exist=True)
        if not snapshot_root.is_dir():
            return DocumentResearchResult(
                status=ResearchStatus.UNAVAILABLE,
                artifact=None,
                chunks=(),
                reason="official_snapshot_root_not_directory",
            )
        snapshot_boundary = WorkspaceBoundary(snapshot_root)
        try:
            target = snapshot_boundary.resolve(relative_path, must_exist=True)
        except FileNotFoundError:
            return DocumentResearchResult(
                status=ResearchStatus.UNAVAILABLE,
                artifact=None,
                chunks=(),
                reason="not_found",
            )
        project_relative = self._project_boundary.relative(target)
        official_relative = snapshot_boundary.relative(target)
        locator = f"{entry.canonical_base_url}/{quote(official_relative, safe='/')}"
        return self._local.research(
            project_relative,
            retrieved_at=retrieved_at,
            source_kind=ResearchSourceKind.OFFICIAL_DOCS,
            canonical_locator=locator,
            title=target.name,
            publisher=entry.publisher,
            product=entry.product,
            version=entry.version,
            target_version=target_version,
            persist_cache=persist_cache,
        )
