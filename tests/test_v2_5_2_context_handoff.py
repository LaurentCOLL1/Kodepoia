from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kodepoia.intelligence.project_knowledge import ProjectKnowledgeSourceKind
from kodepoia.intelligence.project_workspace import (
    ProjectWorkspaceContextSnapshot,
    ProjectWorkspaceSource,
)
from kodepoia.orchestrator.handoff import DATA_ONLY_AUTHORITY, WorkspaceContextHandoff
from kodepoia.orchestrator.workspaces import WorkspaceIdentity


def _project(root: Path, name: str) -> Path:
    (root / ".kodepoia").mkdir(parents=True)
    (root / ".kodepoia" / "project.yaml").write_text(
        f"schema_version: 1\nname: {name}\nproject_type: tool\nplatforms:\n  - windows\n",
        encoding="utf-8",
    )
    return root


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _snapshot(scope: str) -> ProjectWorkspaceContextSnapshot:
    first = _sha("first")
    second = _sha("second")
    return ProjectWorkspaceContextSnapshot(
        project_scope=scope,
        retrieval_digest_sha256=_sha("retrieval"),
        context_bundle_digest_sha256=_sha("bundle"),
        selected_content_sha256s=(first, second),
        sources=(
            ProjectWorkspaceSource(
                knowledge_id=_sha("knowledge-1"),
                source_kind=ProjectKnowledgeSourceKind.RESEARCH_PACK,
                content_sha256=first,
                source_digest_sha256=_sha("source-1"),
                locator="research-pack:///one",
                trust_class="external_guarded_untrusted",
                freshness="current",
                version="1",
                citation_ids=("c2", "c1"),
            ),
            ProjectWorkspaceSource(
                knowledge_id=_sha("knowledge-2"),
                source_kind=ProjectKnowledgeSourceKind.MEMORY,
                content_sha256=second,
                source_digest_sha256=_sha("source-2"),
                locator="memory:///two",
                trust_class="derived",
                freshness="current",
                version="2",
                citation_ids=(),
            ),
        ),
        rendered_context="<UNTRUSTED_DATA>fixture</UNTRUSTED_DATA>",
    )


def test_handoff_binds_source_destination_snapshot_and_data_only_authority(tmp_path: Path) -> None:
    source = WorkspaceIdentity.from_project_root(_project(tmp_path / "source", "Source"))
    destination = WorkspaceIdentity.from_project_root(_project(tmp_path / "destination", "Destination"))
    snapshot = _snapshot(source.project_scope)

    handoff = WorkspaceContextHandoff.from_snapshot(
        source=source,
        destination=destination,
        snapshot=snapshot,
        purpose="Review shared contract",
    )

    assert handoff.source_workspace_id == source.workspace_id
    assert handoff.destination_workspace_id == destination.workspace_id
    assert handoff.snapshot_digest_sha256 == snapshot.digest_sha256
    assert handoff.authority == DATA_ONLY_AUTHORITY
    assert handoff.global_memory_promotion_allowed is False
    assert handoff.verify_integrity()
    first_content = _sha("first")
    first_source = next(
        item for item in handoff.sources if item.content_sha256 == first_content
    )
    assert first_source.citation_ids == ("c1", "c2")


def test_handoff_include_exclude_is_explicit_and_bounded(tmp_path: Path) -> None:
    source = WorkspaceIdentity.from_project_root(_project(tmp_path / "source", "Source"))
    destination = WorkspaceIdentity.from_project_root(_project(tmp_path / "destination", "Destination"))
    snapshot = _snapshot(source.project_scope)
    first, second = snapshot.selected_content_sha256s

    handoff = WorkspaceContextHandoff.from_snapshot(
        source=source,
        destination=destination,
        snapshot=snapshot,
        purpose="Share one source",
        include_content_sha256s=(first, second),
        exclude_content_sha256s=(second,),
    )

    assert handoff.included_content_sha256s == (first,)
    assert handoff.excluded_content_sha256s == (second,)
    assert [item.content_sha256 for item in handoff.sources] == [first]
    assert handoff.rendered_context == ""

    with pytest.raises(ValueError, match="outside the source snapshot"):
        WorkspaceContextHandoff.from_snapshot(
            source=source,
            destination=destination,
            snapshot=snapshot,
            purpose="invalid",
            include_content_sha256s=(_sha("unknown"),),
        )


def test_handoff_rejects_cross_scope_and_same_workspace(tmp_path: Path) -> None:
    source = WorkspaceIdentity.from_project_root(_project(tmp_path / "source", "Source"))
    destination = WorkspaceIdentity.from_project_root(_project(tmp_path / "destination", "Destination"))

    with pytest.raises(ValueError, match="does not match source workspace"):
        WorkspaceContextHandoff.from_snapshot(
            source=source,
            destination=destination,
            snapshot=_snapshot(destination.project_scope),
            purpose="wrong scope",
        )

    with pytest.raises(ValueError, match="distinct source and destination"):
        WorkspaceContextHandoff.from_snapshot(
            source=source,
            destination=source,
            snapshot=_snapshot(source.project_scope),
            purpose="same workspace",
        )


def test_handoff_digest_changes_on_payload_tampering(tmp_path: Path) -> None:
    source = WorkspaceIdentity.from_project_root(_project(tmp_path / "source", "Source"))
    destination = WorkspaceIdentity.from_project_root(_project(tmp_path / "destination", "Destination"))
    handoff = WorkspaceContextHandoff.from_snapshot(
        source=source,
        destination=destination,
        snapshot=_snapshot(source.project_scope),
        purpose="Integrity test",
    )

    original = handoff.digest_sha256
    object.__setattr__(handoff, "purpose", "tampered")
    assert handoff.digest_sha256 == original
    assert handoff.verify_integrity() is False
