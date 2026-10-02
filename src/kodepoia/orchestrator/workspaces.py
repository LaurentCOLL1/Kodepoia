from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

from kodepoia.kodestudio.project_sessions import (
    PROJECT_MARKER,
    canonical_project_root,
    validate_project_root,
)

WORKSPACE_REGISTRY_SCHEMA_VERSION = 1
DEFAULT_MAX_WORKSPACES = 12


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


class WorkspaceRelationshipKind(StrEnum):
    DEPENDS_ON = "depends_on"
    PRODUCES_FOR = "produces_for"
    CONSUMES_FROM = "consumes_from"
    SHARED_CONTRACT = "shared_contract"
    SHARED_ASSET = "shared_asset"
    COMPANION = "companion"


@dataclass(frozen=True, slots=True)
class WorkspaceIdentity:
    workspace_id: str
    project_scope: str
    canonical_root: str
    project_name: str
    project_marker_sha256: str
    schema_version: int = WORKSPACE_REGISTRY_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != WORKSPACE_REGISTRY_SCHEMA_VERSION:
            raise ValueError("Unsupported workspace identity schema version")
        workspace_id = _required_text(self.workspace_id, "workspace_id")
        scope = _required_text(self.project_scope, "project_scope")
        if scope == "global" or scope.startswith("global:"):
            raise ValueError("Workspace identity requires a project scope")
        if scope != f"project:{workspace_id}":
            raise ValueError("Workspace project scope must bind the workspace identity")
        root = canonical_project_root(self.canonical_root)
        object.__setattr__(self, "workspace_id", workspace_id)
        object.__setattr__(self, "project_scope", scope)
        object.__setattr__(self, "canonical_root", str(root))
        object.__setattr__(self, "project_name", _required_text(self.project_name, "project_name"))
        marker_sha = _required_text(self.project_marker_sha256, "project_marker_sha256")
        if len(marker_sha) != 64:
            raise ValueError("project_marker_sha256 must be a SHA-256 digest")
        object.__setattr__(self, "project_marker_sha256", marker_sha)
        object.__setattr__(self, "digest_sha256", _sha256_payload(self._payload_without_digest()))

    @classmethod
    def from_project_root(cls, value: Path | str) -> WorkspaceIdentity:
        root = validate_project_root(value)
        marker = root / PROJECT_MARKER
        marker_bytes = marker.read_bytes()
        marker_sha = hashlib.sha256(marker_bytes).hexdigest()
        payload = yaml.safe_load(marker_bytes.decode("utf-8")) or {}
        name = root.name
        if isinstance(payload, dict):
            candidate = payload.get("name")
            if isinstance(candidate, str) and candidate.strip():
                name = candidate.strip()
        identity_seed = {
            "canonical_root": str(root).casefold(),
            "project_marker_sha256": marker_sha,
        }
        workspace_id = _sha256_payload(identity_seed)
        return cls(
            workspace_id=workspace_id,
            project_scope=f"project:{workspace_id}",
            canonical_root=str(root),
            project_name=name,
            project_marker_sha256=marker_sha,
        )

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workspace_id": self.workspace_id,
            "project_scope": self.project_scope,
            "canonical_root": self.canonical_root,
            "project_name": self.project_name,
            "project_marker_sha256": self.project_marker_sha256,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload


@dataclass(frozen=True, slots=True)
class WorkspaceRelationship:
    source_workspace_id: str
    destination_workspace_id: str
    kind: WorkspaceRelationshipKind
    label: str = ""
    schema_version: int = WORKSPACE_REGISTRY_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != WORKSPACE_REGISTRY_SCHEMA_VERSION:
            raise ValueError("Unsupported workspace relationship schema version")
        source = _required_text(self.source_workspace_id, "source_workspace_id")
        destination = _required_text(self.destination_workspace_id, "destination_workspace_id")
        if source == destination:
            raise ValueError("Workspace relationship requires distinct source and destination")
        object.__setattr__(self, "source_workspace_id", source)
        object.__setattr__(self, "destination_workspace_id", destination)
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(self, "digest_sha256", _sha256_payload(self._payload_without_digest()))

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_workspace_id": self.source_workspace_id,
            "destination_workspace_id": self.destination_workspace_id,
            "kind": self.kind.value,
            "label": self.label,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload


@dataclass(slots=True)
class WorkspaceRegistry:
    max_workspaces: int = DEFAULT_MAX_WORKSPACES
    _workspaces: dict[str, WorkspaceIdentity] = field(default_factory=dict, init=False, repr=False)
    _root_to_id: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _relationships: dict[str, WorkspaceRelationship] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.max_workspaces, int) or self.max_workspaces < 1:
            raise ValueError("max_workspaces must be a positive integer")

    @staticmethod
    def _root_key(value: Path | str) -> str:
        return str(canonical_project_root(value)).casefold()

    def register(self, value: Path | str) -> WorkspaceIdentity:
        identity = WorkspaceIdentity.from_project_root(value)
        root_key = self._root_key(identity.canonical_root)
        if root_key in self._root_to_id:
            raise ValueError("Workspace path alias or duplicate is already registered")
        if identity.workspace_id in self._workspaces:
            raise ValueError("Workspace identity is already registered")
        if len(self._workspaces) >= self.max_workspaces:
            raise ValueError("Workspace registry capacity exceeded")
        self._workspaces[identity.workspace_id] = identity
        self._root_to_id[root_key] = identity.workspace_id
        return identity

    def register_many(self, values: Iterable[Path | str]) -> tuple[WorkspaceIdentity, ...]:
        added: list[WorkspaceIdentity] = []
        for value in values:
            added.append(self.register(value))
        return tuple(added)

    def workspace(self, workspace_id: str) -> WorkspaceIdentity:
        try:
            return self._workspaces[workspace_id]
        except KeyError as exc:
            raise KeyError(f"Unknown workspace: {workspace_id}") from exc

    def workspaces(self) -> tuple[WorkspaceIdentity, ...]:
        return tuple(
            sorted(
                self._workspaces.values(),
                key=lambda item: (item.project_name.casefold(), item.canonical_root.casefold()),
            )
        )

    def add_relationship(
        self,
        source_workspace_id: str,
        destination_workspace_id: str,
        kind: WorkspaceRelationshipKind,
        *,
        label: str = "",
    ) -> WorkspaceRelationship:
        self.workspace(source_workspace_id)
        self.workspace(destination_workspace_id)
        relationship = WorkspaceRelationship(
            source_workspace_id=source_workspace_id,
            destination_workspace_id=destination_workspace_id,
            kind=kind,
            label=label,
        )
        if relationship.digest_sha256 in self._relationships:
            raise ValueError("Workspace relationship is already registered")
        self._relationships[relationship.digest_sha256] = relationship
        return relationship

    def relationships(self) -> tuple[WorkspaceRelationship, ...]:
        return tuple(
            sorted(
                self._relationships.values(),
                key=lambda item: (
                    item.source_workspace_id,
                    item.destination_workspace_id,
                    item.kind.value,
                    item.label,
                ),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        workspaces = self.workspaces()
        relationships = self.relationships()
        payload = {
            "schema_version": WORKSPACE_REGISTRY_SCHEMA_VERSION,
            "max_workspaces": self.max_workspaces,
            "workspaces": [item.to_dict() for item in workspaces],
            "relationships": [item.to_dict() for item in relationships],
        }
        payload["digest_sha256"] = _sha256_payload(payload)
        return payload


__all__ = [
    "DEFAULT_MAX_WORKSPACES",
    "WORKSPACE_REGISTRY_SCHEMA_VERSION",
    "WorkspaceIdentity",
    "WorkspaceRegistry",
    "WorkspaceRelationship",
    "WorkspaceRelationshipKind",
]
