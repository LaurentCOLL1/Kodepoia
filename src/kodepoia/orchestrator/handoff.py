from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from kodepoia.intelligence.project_workspace import (
    ProjectWorkspaceContextSnapshot,
    ProjectWorkspaceSource,
)
from kodepoia.orchestrator.workspaces import WorkspaceIdentity

WORKSPACE_HANDOFF_SCHEMA_VERSION = 1
DATA_ONLY_AUTHORITY = "data_only"
UNUSABLE_FRESHNESS_STATES = frozenset({"stale", "revoked", "quarantined", "expired", "missing"})


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


@dataclass(frozen=True, slots=True)
class WorkspaceHandoffSource:
    knowledge_id: str
    source_kind: str
    content_sha256: str
    source_digest_sha256: str
    locator: str
    trust_class: str
    freshness: str
    version: str
    citation_ids: tuple[str, ...] = ()

    @classmethod
    def from_workspace_source(cls, source: ProjectWorkspaceSource) -> WorkspaceHandoffSource:
        return cls(
            knowledge_id=source.knowledge_id,
            source_kind=source.source_kind.value,
            content_sha256=source.content_sha256,
            source_digest_sha256=source.source_digest_sha256,
            locator=source.locator,
            trust_class=source.trust_class,
            freshness=source.freshness,
            version=source.version,
            citation_ids=source.citation_ids,
        )

    def __post_init__(self) -> None:
        for name in (
            "knowledge_id",
            "source_kind",
            "content_sha256",
            "source_digest_sha256",
            "locator",
            "trust_class",
            "freshness",
        ):
            object.__setattr__(self, name, _required_text(str(getattr(self, name)), name))
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(
            self,
            "citation_ids",
            tuple(sorted(set(item.strip() for item in self.citation_ids if item.strip()))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "source_kind": self.source_kind,
            "content_sha256": self.content_sha256,
            "source_digest_sha256": self.source_digest_sha256,
            "locator": self.locator,
            "trust_class": self.trust_class,
            "freshness": self.freshness,
            "version": self.version,
            "citation_ids": list(self.citation_ids),
        }


@dataclass(frozen=True, slots=True)
class WorkspaceContextHandoff:
    source_workspace_id: str
    source_project_scope: str
    destination_workspace_id: str
    destination_project_scope: str
    purpose: str
    snapshot_digest_sha256: str
    retrieval_digest_sha256: str
    context_bundle_digest_sha256: str
    included_content_sha256s: tuple[str, ...]
    excluded_content_sha256s: tuple[str, ...]
    sources: tuple[WorkspaceHandoffSource, ...]
    rendered_context: str
    authority: str = DATA_ONLY_AUTHORITY
    global_memory_promotion_allowed: bool = False
    schema_version: int = WORKSPACE_HANDOFF_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != WORKSPACE_HANDOFF_SCHEMA_VERSION:
            raise ValueError("Unsupported workspace handoff schema version")
        source = _required_text(self.source_workspace_id, "source_workspace_id")
        destination = _required_text(self.destination_workspace_id, "destination_workspace_id")
        if source == destination:
            raise ValueError("Cross-workspace handoff requires distinct source and destination")
        source_scope = _required_text(self.source_project_scope, "source_project_scope")
        destination_scope = _required_text(self.destination_project_scope, "destination_project_scope")
        if source_scope == destination_scope:
            raise ValueError("Cross-workspace handoff requires distinct project scopes")
        if source_scope != f"project:{source}":
            raise ValueError("Source project scope is not bound to source workspace")
        if destination_scope != f"project:{destination}":
            raise ValueError("Destination project scope is not bound to destination workspace")
        if self.authority != DATA_ONLY_AUTHORITY:
            raise ValueError("Cross-workspace handoff authority must remain data_only")
        if self.global_memory_promotion_allowed:
            raise ValueError("Cross-workspace handoff cannot authorize global memory promotion")

        included = tuple(dict.fromkeys(self.included_content_sha256s))
        excluded = tuple(dict.fromkeys(self.excluded_content_sha256s))
        if set(included) & set(excluded):
            raise ValueError("Handoff content cannot be both included and excluded")
        ordered_sources = tuple(
            sorted(
                self.sources,
                key=lambda item: (item.content_sha256, item.knowledge_id, item.locator),
            )
        )
        source_contents = {item.content_sha256 for item in ordered_sources}
        if source_contents - set(included):
            raise ValueError("Handoff sources must belong to explicitly included content")

        object.__setattr__(self, "source_workspace_id", source)
        object.__setattr__(self, "destination_workspace_id", destination)
        object.__setattr__(self, "source_project_scope", source_scope)
        object.__setattr__(self, "destination_project_scope", destination_scope)
        object.__setattr__(self, "purpose", _required_text(self.purpose, "purpose"))
        object.__setattr__(self, "included_content_sha256s", included)
        object.__setattr__(self, "excluded_content_sha256s", excluded)
        object.__setattr__(self, "sources", ordered_sources)
        object.__setattr__(self, "rendered_context", self.rendered_context.strip())
        object.__setattr__(self, "digest_sha256", _sha256_payload(self._payload_without_digest()))

    @classmethod
    def from_snapshot(
        cls,
        *,
        source: WorkspaceIdentity,
        destination: WorkspaceIdentity,
        snapshot: ProjectWorkspaceContextSnapshot,
        purpose: str,
        include_content_sha256s: tuple[str, ...] | None = None,
        exclude_content_sha256s: tuple[str, ...] = (),
    ) -> WorkspaceContextHandoff:
        if snapshot.project_scope != source.project_scope:
            raise ValueError("Snapshot project scope does not match source workspace")

        selected = tuple(snapshot.selected_content_sha256s)
        selected_set = set(selected)
        requested = set(selected if include_content_sha256s is None else include_content_sha256s)
        excluded = set(exclude_content_sha256s)
        unknown = (requested | excluded) - selected_set
        if unknown:
            raise ValueError("Handoff selection references content outside the source snapshot")
        included = tuple(item for item in selected if item in requested and item not in excluded)
        omitted = tuple(item for item in selected if item not in included)

        sources = tuple(
            WorkspaceHandoffSource.from_workspace_source(item)
            for item in snapshot.sources
            if item.content_sha256 in set(included)
        )
        rendered = snapshot.rendered_context if tuple(included) == selected else ""

        return cls(
            source_workspace_id=source.workspace_id,
            source_project_scope=source.project_scope,
            destination_workspace_id=destination.workspace_id,
            destination_project_scope=destination.project_scope,
            purpose=purpose,
            snapshot_digest_sha256=snapshot.digest_sha256,
            retrieval_digest_sha256=snapshot.retrieval_digest_sha256,
            context_bundle_digest_sha256=snapshot.context_bundle_digest_sha256,
            included_content_sha256s=included,
            excluded_content_sha256s=omitted,
            sources=sources,
            rendered_context=rendered,
        )

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_workspace_id": self.source_workspace_id,
            "source_project_scope": self.source_project_scope,
            "destination_workspace_id": self.destination_workspace_id,
            "destination_project_scope": self.destination_project_scope,
            "purpose": self.purpose,
            "snapshot_digest_sha256": self.snapshot_digest_sha256,
            "retrieval_digest_sha256": self.retrieval_digest_sha256,
            "context_bundle_digest_sha256": self.context_bundle_digest_sha256,
            "included_content_sha256s": list(self.included_content_sha256s),
            "excluded_content_sha256s": list(self.excluded_content_sha256s),
            "sources": [item.to_dict() for item in self.sources],
            "rendered_context": self.rendered_context,
            "authority": self.authority,
            "global_memory_promotion_allowed": self.global_memory_promotion_allowed,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload

    def verify_integrity(self) -> bool:
        return self.digest_sha256 == _sha256_payload(self._payload_without_digest())

    def assert_usable_for(
        self,
        destination_workspace_id: str,
        *,
        source_workspace_ids: tuple[str, ...] = (),
    ) -> None:
        if not self.verify_integrity():
            raise ValueError("Cross-workspace handoff integrity check failed")
        if self.authority != DATA_ONLY_AUTHORITY or self.global_memory_promotion_allowed:
            raise ValueError("Cross-workspace handoff authority is not data-only")
        if self.destination_workspace_id != destination_workspace_id:
            raise ValueError("Cross-workspace handoff destination mismatch")
        if source_workspace_ids and self.source_workspace_id not in set(source_workspace_ids):
            raise ValueError("Cross-workspace handoff source is not authorized by the task")
        unusable = sorted(
            {
                source.freshness.strip().casefold()
                for source in self.sources
                if source.freshness.strip().casefold() in UNUSABLE_FRESHNESS_STATES
            }
        )
        if unusable:
            raise ValueError(
                "Cross-workspace handoff contains unusable source freshness: "
                + ", ".join(unusable)
            )


__all__ = [
    "DATA_ONLY_AUTHORITY",
    "UNUSABLE_FRESHNESS_STATES",
    "WORKSPACE_HANDOFF_SCHEMA_VERSION",
    "WorkspaceContextHandoff",
    "WorkspaceHandoffSource",
]
