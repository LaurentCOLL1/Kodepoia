from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^(asset|rev)_[0-9a-f]{32}$")


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _require_sha256(value: str, *, field_name: str) -> str:
    normalized = value.lower()
    if not _HEX64_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return normalized


@dataclass(frozen=True, slots=True)
class AssetId:
    value: str

    def __post_init__(self) -> None:
        if not _ID_RE.fullmatch(self.value) or not self.value.startswith("asset_"):
            raise ValueError(f"Invalid AssetId: {self.value!r}")

    @classmethod
    def from_seed(cls, namespace: str, stable_key: str) -> "AssetId":
        if not namespace.strip() or not stable_key.strip():
            raise ValueError("AssetId seed fields must be non-empty")
        digest = hashlib.sha256(_canonical_bytes({"namespace": namespace, "stable_key": stable_key})).hexdigest()
        return cls(f"asset_{digest[:32]}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AssetRevisionId:
    value: str

    def __post_init__(self) -> None:
        if not _ID_RE.fullmatch(self.value) or not self.value.startswith("rev_"):
            raise ValueError(f"Invalid AssetRevisionId: {self.value!r}")

    @classmethod
    def from_identity(cls, payload: dict[str, Any]) -> "AssetRevisionId":
        digest = hashlib.sha256(_canonical_bytes(payload)).hexdigest()
        return cls(f"rev_{digest[:32]}")

    def __str__(self) -> str:
        return self.value


class AssetRole(StrEnum):
    SOURCE = "source"
    DERIVED = "derived"


class AssetKind(StrEnum):
    GENERIC = "generic"
    IMAGE = "image"
    TEXTURE = "texture"
    MODEL_3D = "model_3d"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    UI = "ui"
    FONT = "font"


class ReuseScope(StrEnum):
    PROJECT_ONLY = "project_only"
    VAULT_LOCAL = "vault_local"
    EXPORTABLE = "exportable"


class PreservationPolicy(StrEnum):
    PINNED_SOURCE = "pinned_source"
    REFERENCED = "referenced"
    EVICTABLE_DERIVED = "evictable_derived"


class AssetStatus(StrEnum):
    STAGED = "staged"
    READY = "ready"
    MISSING = "missing"
    CORRUPT = "corrupt"
    BLOCKED = "blocked"
    STALE = "stale"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ProvenanceRef:
    source_kind: str
    locator: str
    evidence_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.source_kind.strip() or not self.locator.strip():
            raise ValueError("Provenance source_kind and locator must be non-empty")
        if self.evidence_sha256 is not None:
            object.__setattr__(self, "evidence_sha256", _require_sha256(self.evidence_sha256, field_name="evidence_sha256"))

    def canonical(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "locator": self.locator,
            "evidence_sha256": self.evidence_sha256,
        }


@dataclass(frozen=True, slots=True)
class LineageRef:
    input_revision_id: AssetRevisionId
    relation: str = "input"
    transform_id: str | None = None

    def __post_init__(self) -> None:
        if not self.relation.strip():
            raise ValueError("Lineage relation must be non-empty")

    def canonical(self) -> dict[str, Any]:
        return {
            "input_revision_id": str(self.input_revision_id),
            "relation": self.relation,
            "transform_id": self.transform_id,
        }


@dataclass(frozen=True, slots=True)
class AssetRevision:
    asset_id: AssetId
    revision_id: AssetRevisionId
    role: AssetRole
    kind: AssetKind
    content_sha256: str
    content_length: int
    reuse_scope: ReuseScope = ReuseScope.PROJECT_ONLY
    preservation: PreservationPolicy = PreservationPolicy.REFERENCED
    provenance: tuple[ProvenanceRef, ...] = ()
    lineage: tuple[LineageRef, ...] = ()
    status: AssetStatus = AssetStatus.STAGED

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_sha256", _require_sha256(self.content_sha256, field_name="content_sha256"))
        if self.content_length < 0:
            raise ValueError("content_length must be >= 0")
        expected = AssetRevisionId.from_identity(self.identity_payload())
        if expected != self.revision_id:
            raise ValueError("AssetRevisionId does not match canonical revision identity")

    @classmethod
    def create(
        cls,
        *,
        asset_id: AssetId,
        role: AssetRole,
        kind: AssetKind,
        content_sha256: str,
        content_length: int,
        reuse_scope: ReuseScope = ReuseScope.PROJECT_ONLY,
        preservation: PreservationPolicy = PreservationPolicy.REFERENCED,
        provenance: tuple[ProvenanceRef, ...] = (),
        lineage: tuple[LineageRef, ...] = (),
        status: AssetStatus = AssetStatus.STAGED,
    ) -> "AssetRevision":
        normalized_sha = _require_sha256(content_sha256, field_name="content_sha256")
        payload = cls._identity_payload(
            asset_id=asset_id,
            role=role,
            kind=kind,
            content_sha256=normalized_sha,
            content_length=content_length,
            reuse_scope=reuse_scope,
            preservation=preservation,
            provenance=provenance,
            lineage=lineage,
        )
        return cls(
            asset_id=asset_id,
            revision_id=AssetRevisionId.from_identity(payload),
            role=role,
            kind=kind,
            content_sha256=normalized_sha,
            content_length=content_length,
            reuse_scope=reuse_scope,
            preservation=preservation,
            provenance=provenance,
            lineage=lineage,
            status=status,
        )

    @staticmethod
    def _identity_payload(
        *,
        asset_id: AssetId,
        role: AssetRole,
        kind: AssetKind,
        content_sha256: str,
        content_length: int,
        reuse_scope: ReuseScope,
        preservation: PreservationPolicy,
        provenance: tuple[ProvenanceRef, ...],
        lineage: tuple[LineageRef, ...],
    ) -> dict[str, Any]:
        return {
            "asset_id": str(asset_id),
            "role": role.value,
            "kind": kind.value,
            "content_sha256": content_sha256,
            "content_length": content_length,
            "reuse_scope": reuse_scope.value,
            "preservation": preservation.value,
            "provenance": [item.canonical() for item in provenance],
            "lineage": [item.canonical() for item in lineage],
        }

    def identity_payload(self) -> dict[str, Any]:
        return self._identity_payload(
            asset_id=self.asset_id,
            role=self.role,
            kind=self.kind,
            content_sha256=self.content_sha256,
            content_length=self.content_length,
            reuse_scope=self.reuse_scope,
            preservation=self.preservation,
            provenance=self.provenance,
            lineage=self.lineage,
        )

    def manifest_payload(self) -> dict[str, Any]:
        return {**self.identity_payload(), "revision_id": str(self.revision_id), "status": self.status.value}


@dataclass(frozen=True, slots=True)
class AssetRecord:
    asset_id: AssetId
    kind: AssetKind
    display_name: str
    tags: tuple[str, ...] = ()
    current_revision_id: AssetRevisionId | None = None

    def __post_init__(self) -> None:
        if not self.display_name.strip():
            raise ValueError("display_name must be non-empty")
        normalized = tuple(dict.fromkeys(tag.strip() for tag in self.tags if tag.strip()))
        object.__setattr__(self, "tags", normalized)


@dataclass(frozen=True, slots=True)
class ProjectAssetReference:
    project_id: str
    asset_id: AssetId
    revision_id: AssetRevisionId
    target_path: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id must be non-empty")
        if self.target_path is not None and not self.target_path.strip():
            raise ValueError("target_path must be non-empty when supplied")
