from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from kodepoia.intelligence.research.contracts import ResearchArtifact
from kodepoia.intelligence.research.service import ResearchViewItem
from kodepoia.kodecode.workspace import WorkspaceBoundary

EVIDENCE_WORKSPACE_SCHEMA_VERSION = 1


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


def canonicalize_evidence_locator(locator: str) -> str:
    """Normalize a source locator without changing its semantic resource identity."""

    value = locator.strip()
    if not value:
        return ""
    parsed = urlsplit(value)
    if parsed.scheme.lower() in {"http", "https"} and parsed.hostname:
        scheme = parsed.scheme.lower()
        host = parsed.hostname.lower()
        port = parsed.port
        if port is not None and not (
            (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
        ):
            host = f"{host}:{port}"
        path = parsed.path or "/"
        if path != "/":
            path = path.rstrip("/") or "/"
        query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
        return urlunsplit((scheme, host, path, query, ""))
    return value.replace("\\", "/")


def canonical_source_identity_id(locator: str) -> str:
    canonical = canonicalize_evidence_locator(locator)
    if not canonical:
        return ""
    return _sha256({"canonical_locator": canonical})


class EvidenceLifecycle(StrEnum):
    CANDIDATE_ONLY = "candidate_only"
    FETCHED = "fetched"


class EvidenceSelection(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    INCLUDED = "included"
    EXCLUDED = "excluded"


@dataclass(frozen=True, slots=True)
class EvidenceRevision:
    artifact_id: str
    source_identity_id: str
    canonical_locator: str
    source_kind: str
    retrieved_at: str
    content_sha256: str
    version: str = ""
    published_at: str = ""
    updated_at: str = ""
    provider_ids: tuple[str, ...] = ()
    schema_version: int = EVIDENCE_WORKSPACE_SCHEMA_VERSION
    revision_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != EVIDENCE_WORKSPACE_SCHEMA_VERSION:
            raise ValueError("Unsupported evidence workspace schema version")
        if not self.artifact_id or not self.source_identity_id or not self.canonical_locator:
            raise ValueError("Evidence revisions require artifact/source identity and canonical locator")
        providers = tuple(sorted({value.strip() for value in self.provider_ids if value.strip()}))
        object.__setattr__(self, "provider_ids", providers)
        object.__setattr__(
            self,
            "revision_id",
            _sha256(
                {
                    "artifact_id": self.artifact_id,
                    "source_identity_id": self.source_identity_id,
                    "retrieved_at": self.retrieved_at,
                    "provider_ids": list(providers),
                }
            ),
        )

    @classmethod
    def from_artifact(
        cls,
        artifact: ResearchArtifact,
        *,
        provider_ids: Iterable[str] = (),
    ) -> "EvidenceRevision":
        canonical = canonicalize_evidence_locator(artifact.source.locator)
        metadata_providers: list[str] = []
        raw_provider = artifact.metadata.get("provider_id")
        if isinstance(raw_provider, str):
            metadata_providers.append(raw_provider)
        raw_providers = artifact.metadata.get("provider_ids")
        if isinstance(raw_providers, (list, tuple)):
            metadata_providers.extend(str(value) for value in raw_providers)
        return cls(
            artifact_id=artifact.artifact_id,
            source_identity_id=canonical_source_identity_id(canonical),
            canonical_locator=canonical,
            source_kind=artifact.source.kind.value,
            retrieved_at=artifact.retrieved_at,
            content_sha256=artifact.content_sha256,
            version=artifact.source.version,
            published_at=artifact.source.published_at or "",
            updated_at=artifact.source.updated_at or "",
            provider_ids=tuple(provider_ids) + tuple(metadata_providers),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "revision_id": self.revision_id,
            "artifact_id": self.artifact_id,
            "source_identity_id": self.source_identity_id,
            "canonical_locator": self.canonical_locator,
            "source_kind": self.source_kind,
            "retrieved_at": self.retrieved_at,
            "content_sha256": self.content_sha256,
            "version": self.version,
            "published_at": self.published_at,
            "updated_at": self.updated_at,
            "provider_ids": list(self.provider_ids),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EvidenceRevision":
        revision = cls(
            artifact_id=str(payload["artifact_id"]),
            source_identity_id=str(payload["source_identity_id"]),
            canonical_locator=str(payload["canonical_locator"]),
            source_kind=str(payload["source_kind"]),
            retrieved_at=str(payload["retrieved_at"]),
            content_sha256=str(payload["content_sha256"]),
            version=str(payload.get("version", "")),
            published_at=str(payload.get("published_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            provider_ids=tuple(str(value) for value in payload.get("provider_ids", [])),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("revision_id", "")) != revision.revision_id:
            raise ValueError("Evidence revision ID does not match canonical revision evidence")
        return revision


@dataclass(frozen=True, slots=True)
class EvidenceWorkspaceRow:
    source_identity_id: str
    canonical_locator: str
    source_kind: str
    lifecycle: EvidenceLifecycle
    selection: EvidenceSelection
    provider_ids: tuple[str, ...] = ()
    artifact_id: str = ""
    title: str = ""
    status: str = ""
    freshness: str = ""
    trust: str = ""
    version: str = ""
    retrieved_at: str = ""
    published_at: str = ""
    updated_at: str = ""
    suspicious: bool = False
    lineage_revision_ids: tuple[str, ...] = ()
    lineage_artifact_ids: tuple[str, ...] = ()
    conflicting_versions: tuple[str, ...] = ()
    row_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.lifecycle is EvidenceLifecycle.CANDIDATE_ONLY:
            if self.artifact_id:
                raise ValueError("Candidate-only workspace rows cannot reference fetched artifacts")
            if self.selection is not EvidenceSelection.NOT_APPLICABLE:
                raise ValueError("Candidate-only workspace rows cannot be included/excluded")
        elif not self.artifact_id:
            raise ValueError("Fetched workspace rows require an artifact ID")
        object.__setattr__(self, "provider_ids", tuple(sorted(set(self.provider_ids))))
        object.__setattr__(self, "lineage_revision_ids", tuple(dict.fromkeys(self.lineage_revision_ids)))
        object.__setattr__(self, "lineage_artifact_ids", tuple(dict.fromkeys(self.lineage_artifact_ids)))
        object.__setattr__(self, "conflicting_versions", tuple(sorted(set(self.conflicting_versions))))
        object.__setattr__(
            self,
            "row_id",
            _sha256(
                {
                    "source_identity_id": self.source_identity_id,
                    "lifecycle": self.lifecycle.value,
                    "artifact_id": self.artifact_id,
                }
            ),
        )

    @property
    def has_version_conflict(self) -> bool:
        return len(self.conflicting_versions) > 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_id": self.row_id,
            "source_identity_id": self.source_identity_id,
            "canonical_locator": self.canonical_locator,
            "source_kind": self.source_kind,
            "lifecycle": self.lifecycle.value,
            "selection": self.selection.value,
            "provider_ids": list(self.provider_ids),
            "artifact_id": self.artifact_id,
            "title": self.title,
            "status": self.status,
            "freshness": self.freshness,
            "trust": self.trust,
            "version": self.version,
            "retrieved_at": self.retrieved_at,
            "published_at": self.published_at,
            "updated_at": self.updated_at,
            "suspicious": self.suspicious,
            "lineage_revision_ids": list(self.lineage_revision_ids),
            "lineage_artifact_ids": list(self.lineage_artifact_ids),
            "conflicting_versions": list(self.conflicting_versions),
            "has_version_conflict": self.has_version_conflict,
        }


def _provider_ids(item: ResearchViewItem) -> tuple[str, ...]:
    prefix = "descriptor_only_not_fetched:"
    if item.reason.startswith(prefix):
        remainder = item.reason[len(prefix) :]
        provider = remainder.split(":", 1)[0].strip()
        return (provider,) if provider else ()
    return ()


@dataclass(slots=True)
class EvidenceSelectionStore:
    project_root: Path
    _boundary: WorkspaceBoundary = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        self.project_root = root
        self._boundary = WorkspaceBoundary(root)

    @property
    def path(self) -> Path:
        return self._boundary.resolve(".kodepoia/research/evidence-selection.json")

    def load(self) -> dict[str, EvidenceSelection]:
        if not self.path.is_file():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or int(payload.get("schema_version", 0)) != EVIDENCE_WORKSPACE_SCHEMA_VERSION:
            raise ValueError("Unsupported evidence selection document")
        raw = payload.get("artifacts", {})
        if not isinstance(raw, dict):
            raise ValueError("Evidence selection artifacts must be an object")
        result: dict[str, EvidenceSelection] = {}
        for artifact_id, value in raw.items():
            selection = EvidenceSelection(str(value))
            if selection is EvidenceSelection.NOT_APPLICABLE:
                raise ValueError("Persisted fetched evidence selection cannot be not_applicable")
            result[str(artifact_id)] = selection
        return result

    def set(self, artifact_id: str, selection: EvidenceSelection) -> None:
        if not artifact_id:
            raise ValueError("Only fetched artifacts can be included/excluded")
        if selection is EvidenceSelection.NOT_APPLICABLE:
            raise ValueError("Fetched artifacts must be included or excluded")
        current = self.load()
        current[artifact_id] = selection
        payload = {
            "schema_version": EVIDENCE_WORKSPACE_SCHEMA_VERSION,
            "artifacts": {key: value.value for key, value in sorted(current.items())},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)


@dataclass(frozen=True, slots=True)
class EvidenceWorkspace:
    rows: tuple[EvidenceWorkspaceRow, ...]
    schema_version: int = EVIDENCE_WORKSPACE_SCHEMA_VERSION

    @classmethod
    def project(
        cls,
        items: Iterable[ResearchViewItem],
        *,
        revisions: Iterable[EvidenceRevision] = (),
        selections: Mapping[str, EvidenceSelection] | None = None,
    ) -> "EvidenceWorkspace":
        selection_map = dict(selections or {})
        revision_groups: dict[str, list[EvidenceRevision]] = {}
        for revision in revisions:
            revision_groups.setdefault(revision.source_identity_id, []).append(revision)
        for group in revision_groups.values():
            group.sort(key=lambda item: (item.retrieved_at, item.revision_id))

        source_groups: dict[str, list[ResearchViewItem]] = {}
        for item in items:
            canonical = canonicalize_evidence_locator(item.locator)
            identity = canonical_source_identity_id(canonical)
            if not identity:
                identity = _sha256({"item_id": item.item_id})
            source_groups.setdefault(identity, []).append(item)

        rows: list[EvidenceWorkspaceRow] = []
        for identity, grouped_items in sorted(source_groups.items()):
            providers = tuple(sorted({provider for item in grouped_items for provider in _provider_ids(item)}))
            fetched = [item for item in grouped_items if item.artifact_id]
            candidates = [item for item in grouped_items if not item.artifact_id]
            lineage = revision_groups.get(identity, [])
            lineage_revision_ids = tuple(item.revision_id for item in lineage)
            lineage_artifact_ids = tuple(dict.fromkeys(item.artifact_id for item in lineage))
            versions = tuple(sorted({item.version for item in lineage if item.version}))
            if fetched:
                for item in sorted(fetched, key=lambda value: (value.retrieved_at, value.artifact_id)):
                    rows.append(
                        EvidenceWorkspaceRow(
                            source_identity_id=identity,
                            canonical_locator=canonicalize_evidence_locator(item.locator),
                            source_kind=item.source_kind,
                            lifecycle=EvidenceLifecycle.FETCHED,
                            selection=selection_map.get(item.artifact_id, EvidenceSelection.INCLUDED),
                            provider_ids=providers,
                            artifact_id=item.artifact_id,
                            title=item.title,
                            status=item.status.value,
                            freshness=item.freshness,
                            trust=item.trust,
                            version=item.version,
                            retrieved_at=item.retrieved_at,
                            published_at=item.published_at,
                            updated_at=item.updated_at,
                            suspicious=item.suspicious,
                            lineage_revision_ids=lineage_revision_ids,
                            lineage_artifact_ids=lineage_artifact_ids or (item.artifact_id,),
                            conflicting_versions=versions or ((item.version,) if item.version else ()),
                        )
                    )
            elif candidates:
                representative = sorted(candidates, key=lambda value: value.item_id)[0]
                rows.append(
                    EvidenceWorkspaceRow(
                        source_identity_id=identity,
                        canonical_locator=canonicalize_evidence_locator(representative.locator),
                        source_kind=representative.source_kind,
                        lifecycle=EvidenceLifecycle.CANDIDATE_ONLY,
                        selection=EvidenceSelection.NOT_APPLICABLE,
                        provider_ids=providers,
                        title=representative.title,
                        status=representative.status.value,
                        freshness=representative.freshness,
                        trust=representative.trust,
                        version=representative.version,
                        published_at=representative.published_at,
                        updated_at=representative.updated_at,
                        suspicious=representative.suspicious,
                    )
                )
        return cls(tuple(rows))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "rows": [row.to_dict() for row in self.rows],
        }
