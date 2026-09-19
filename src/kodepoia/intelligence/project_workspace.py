from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from kodepoia.core.governance import DataScope, GovernancePolicy
from kodepoia.intelligence.memory import MemoryRecord, MemoryStore
from kodepoia.intelligence.project_context import ProjectContextBundle
from kodepoia.intelligence.project_knowledge import ProjectKnowledgeSourceKind
from kodepoia.intelligence.project_retrieval import (
    ProjectRetrievalResult,
    ProjectRetrievalState,
)

PROJECT_WORKSPACE_CONTEXT_SCHEMA_VERSION = 1


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
        raise ValueError("Project workspace context requires a non-global project scope")
    return scope


class ProjectWorkspaceSurface(StrEnum):
    CHAT = "chat"
    KODECODE = "kodecode"
    SPECIALIST = "specialist"


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceSource:
    knowledge_id: str
    source_kind: ProjectKnowledgeSourceKind
    content_sha256: str
    source_digest_sha256: str
    locator: str
    trust_class: str
    freshness: str
    version: str
    citation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "knowledge_id", _required_text(self.knowledge_id, "knowledge_id"))
        object.__setattr__(self, "content_sha256", _required_text(self.content_sha256, "content_sha256"))
        object.__setattr__(
            self,
            "source_digest_sha256",
            _required_text(self.source_digest_sha256, "source_digest_sha256"),
        )
        object.__setattr__(self, "locator", _required_text(self.locator, "locator"))
        object.__setattr__(self, "trust_class", _required_text(self.trust_class, "trust_class"))
        object.__setattr__(self, "freshness", _required_text(self.freshness, "freshness"))
        object.__setattr__(
            self,
            "citation_ids",
            tuple(sorted(set(value.strip() for value in self.citation_ids if value.strip()))),
        )
        object.__setattr__(self, "version", self.version.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "source_kind": self.source_kind.value,
            "content_sha256": self.content_sha256,
            "source_digest_sha256": self.source_digest_sha256,
            "locator": self.locator,
            "trust_class": self.trust_class,
            "freshness": self.freshness,
            "version": self.version,
            "citation_ids": list(self.citation_ids),
        }


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceContextSnapshot:
    project_scope: str
    retrieval_digest_sha256: str
    context_bundle_digest_sha256: str
    selected_content_sha256s: tuple[str, ...]
    sources: tuple[ProjectWorkspaceSource, ...]
    rendered_context: str
    schema_version: int = PROJECT_WORKSPACE_CONTEXT_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != PROJECT_WORKSPACE_CONTEXT_SCHEMA_VERSION:
            raise ValueError("Unsupported project workspace context schema version")
        object.__setattr__(self, "project_scope", _project_scope(self.project_scope))
        object.__setattr__(
            self,
            "selected_content_sha256s",
            tuple(self.selected_content_sha256s),
        )
        ordered_sources = tuple(
            sorted(
                self.sources,
                key=lambda value: (value.knowledge_id, value.locator),
            )
        )
        object.__setattr__(self, "sources", ordered_sources)
        object.__setattr__(self, "rendered_context", self.rendered_context.strip())
        object.__setattr__(
            self,
            "digest_sha256",
            _sha256_payload(self._payload_without_digest()),
        )

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_scope": self.project_scope,
            "retrieval_digest_sha256": self.retrieval_digest_sha256,
            "context_bundle_digest_sha256": self.context_bundle_digest_sha256,
            "selected_content_sha256s": list(self.selected_content_sha256s),
            "sources": [source.to_dict() for source in self.sources],
            "rendered_context": self.rendered_context,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload

    def render(self) -> str:
        return self.rendered_context


@dataclass(frozen=True, slots=True)
class ProjectWorkspaceContext:
    surface: ProjectWorkspaceSurface
    workspace_id: str
    snapshot: ProjectWorkspaceContextSnapshot
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        workspace_id = _required_text(self.workspace_id, "workspace_id")
        object.__setattr__(self, "workspace_id", workspace_id)
        object.__setattr__(
            self,
            "digest_sha256",
            _sha256_payload(
                {
                    "surface": self.surface.value,
                    "workspace_id": workspace_id,
                    "snapshot_digest_sha256": self.snapshot.digest_sha256,
                }
            ),
        )

    @property
    def project_scope(self) -> str:
        return self.snapshot.project_scope

    @property
    def sources(self) -> tuple[ProjectWorkspaceSource, ...]:
        return self.snapshot.sources

    def render(self) -> str:
        return self.snapshot.render()

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface.value,
            "workspace_id": self.workspace_id,
            "project_scope": self.project_scope,
            "snapshot_digest_sha256": self.snapshot.digest_sha256,
            "digest_sha256": self.digest_sha256,
            "selected_content_sha256s": list(self.snapshot.selected_content_sha256s),
            "sources": [source.to_dict() for source in self.sources],
            "rendered_context": self.render(),
        }


@dataclass(slots=True)
class ProjectWorkspaceContextSession:
    expected_project_scope: str | None = None
    _snapshot: ProjectWorkspaceContextSnapshot | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.expected_project_scope is not None:
            self.expected_project_scope = _project_scope(self.expected_project_scope)

    @staticmethod
    def _citation_ids(provenance: object) -> tuple[str, ...]:
        if not isinstance(provenance, dict):
            return ()
        raw = provenance.get("citation_ids", [])
        if not isinstance(raw, list):
            return ()
        return tuple(sorted(set(str(value).strip() for value in raw if str(value).strip())))

    def activate(
        self,
        retrieval: ProjectRetrievalResult,
        bundle: ProjectContextBundle,
    ) -> ProjectWorkspaceContextSnapshot:
        if retrieval.state is not ProjectRetrievalState.READY:
            raise ValueError("Workspace context requires a READY retrieval result")
        scope = _project_scope(retrieval.request.project_scope)
        if self.expected_project_scope is not None and scope != self.expected_project_scope:
            raise ValueError("Workspace context project scope does not match active project")
        if bundle.retrieval_digest_sha256 != retrieval.digest_sha256:
            raise ValueError("Workspace context bundle is not bound to this retrieval result")

        selected_digests = tuple(
            selection.candidate.content_sha256 for selection in bundle.selected
        )
        sources: dict[tuple[str, str], ProjectWorkspaceSource] = {}
        for selection in bundle.selected:
            for ref in selection.candidate.source_refs:
                key = (ref.knowledge_id, ref.locator)
                sources[key] = ProjectWorkspaceSource(
                    knowledge_id=ref.knowledge_id,
                    source_kind=ref.source_kind,
                    content_sha256=ref.content_sha256,
                    source_digest_sha256=ref.source_digest_sha256,
                    locator=ref.locator,
                    trust_class=ref.trust_class,
                    freshness=ref.freshness,
                    version=ref.version,
                    citation_ids=self._citation_ids(dict(ref.provenance)),
                )

        snapshot = ProjectWorkspaceContextSnapshot(
            project_scope=scope,
            retrieval_digest_sha256=retrieval.digest_sha256,
            context_bundle_digest_sha256=bundle.digest_sha256,
            selected_content_sha256s=selected_digests,
            sources=tuple(sources.values()),
            rendered_context=bundle.render(),
        )
        self.expected_project_scope = scope
        self._snapshot = snapshot
        return snapshot

    @property
    def snapshot(self) -> ProjectWorkspaceContextSnapshot | None:
        return self._snapshot

    def clear(self) -> None:
        self._snapshot = None

    def context_for(
        self,
        surface: ProjectWorkspaceSurface,
        *,
        workspace_id: str,
    ) -> ProjectWorkspaceContext | None:
        if self._snapshot is None:
            return None
        return ProjectWorkspaceContext(
            surface=surface,
            workspace_id=workspace_id,
            snapshot=self._snapshot,
        )


@dataclass(slots=True)
class ProjectMemoryBridge:
    memory: MemoryStore
    project_scope: str

    def __post_init__(self) -> None:
        self.project_scope = _project_scope(self.project_scope)

    @staticmethod
    def _metadata(context: ProjectWorkspaceContext) -> dict[str, object]:
        citations = sorted(
            {
                citation
                for source in context.sources
                for citation in source.citation_ids
            }
        )
        return {
            "context_snapshot_digest_sha256": context.snapshot.digest_sha256,
            "context_bundle_digest_sha256": context.snapshot.context_bundle_digest_sha256,
            "retrieval_digest_sha256": context.snapshot.retrieval_digest_sha256,
            "selected_content_sha256s": list(context.snapshot.selected_content_sha256s),
            "source_knowledge_ids": [source.knowledge_id for source in context.sources],
            "citation_ids": citations,
            "workspace_surface": context.surface.value,
            "workspace_id": context.workspace_id,
            "derived_untrusted": True,
            "global_promotion_allowed": False,
            "training_dataset_allowed": False,
        }

    def store_context(
        self,
        context: ProjectWorkspaceContext,
        *,
        explicit_opt_in: bool = False,
        importance: float = 0.4,
        origin: str | None = None,
        version: int = 1,
    ) -> int:
        if not explicit_opt_in:
            raise ValueError("Project Memory persistence requires explicit opt-in")
        if context.project_scope != self.project_scope:
            raise ValueError("Project Memory bridge scope does not match workspace context")
        governance = GovernancePolicy(
            scope=DataScope.PROJECT,
            allow_global_memory=False,
            allow_training_dataset=False,
            delete_with_project=True,
            confidential=False,
        )
        return self.memory.add(
            self.project_scope,
            "project_context_derived",
            context.render(),
            importance=importance,
            metadata=self._metadata(context),
            governance=governance,
            origin=origin or f"project-context:{context.snapshot.digest_sha256}",
            project_scope=self.project_scope,
            trust_class="derived",
            record_class="derived_summary",
            version=version,
        )

    def list_contexts(self, *, limit: int = 100) -> tuple[MemoryRecord, ...]:
        records = self.memory.list_project_scope(
            self.project_scope,
            kind="project_context_derived",
            limit=limit,
        )
        return tuple(
            record
            for record in records
            if record.trust_class in {"derived", "untrusted"}
            and record.record_class == "derived_summary"
        )
