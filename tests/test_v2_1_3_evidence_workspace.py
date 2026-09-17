from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchFreshness,
    ResearchSource,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.evidence import (
    EvidenceLifecycle,
    EvidenceSelection,
    EvidenceSelectionStore,
    EvidenceWorkspace,
    canonical_source_identity_id,
    canonicalize_evidence_locator,
)
from kodepoia.intelligence.research.service import ResearchOperationStatus, ResearchViewItem
from kodepoia.intelligence.research.store import ResearchStore


def _source_id(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _candidate(locator: str, provider: str) -> ResearchViewItem:
    return ResearchViewItem(
        source_kind="web",
        source_id=_source_id(f"{provider}:{locator}"),
        locator=locator,
        status=ResearchOperationStatus.READY,
        freshness="unfetched",
        trust="candidate-only",
        title="Candidate",
        reason=f"descriptor_only_not_fetched:{provider}:rank=1",
    )


def _artifact(
    *,
    locator: str,
    retrieved_at: str,
    content: str,
    version: str = "",
) -> ResearchArtifact:
    return ResearchArtifact.from_content(
        source=ResearchSource(
            kind=ResearchSourceKind.WEB,
            locator=locator,
            status=ResearchStatus.READY,
            title="Evidence",
            product="Example",
            version=version,
            updated_at="2026-09-16T00:00:00Z",
        ),
        content=content,
        retrieved_at=retrieved_at,
        freshness=ResearchFreshness.CURRENT,
    )


def _view(artifact: ResearchArtifact) -> ResearchViewItem:
    return ResearchViewItem(
        source_kind=artifact.source.kind.value,
        source_id=artifact.source.source_id,
        locator=artifact.source.locator,
        status=ResearchOperationStatus.READY,
        freshness=artifact.freshness.value,
        trust=artifact.trust.value,
        title=artifact.source.title,
        version=artifact.source.version,
        retrieved_at=artifact.retrieved_at,
        updated_at=artifact.source.updated_at or "",
        artifact_id=artifact.artifact_id,
    )


def test_canonical_locator_normalizes_provider_variants() -> None:
    left = "HTTPS://GitHub.COM/godotengine/godot/?b=2&a=1#readme"
    right = "https://github.com/godotengine/godot?a=1&b=2"
    assert canonicalize_evidence_locator(left) == canonicalize_evidence_locator(right)
    assert canonical_source_identity_id(left) == canonical_source_identity_id(right)


def test_duplicate_candidates_merge_without_becoming_evidence() -> None:
    workspace = EvidenceWorkspace.project(
        (
            _candidate("https://example.com/docs/", "brave-web"),
            _candidate("https://example.com/docs#top", "github-public"),
        )
    )
    assert len(workspace.rows) == 1
    row = workspace.rows[0]
    assert row.lifecycle is EvidenceLifecycle.CANDIDATE_ONLY
    assert row.selection is EvidenceSelection.NOT_APPLICABLE
    assert row.artifact_id == ""
    assert row.provider_ids == ("brave-web", "github-public")


def test_selection_store_only_accepts_fetched_artifacts(tmp_path: Path) -> None:
    (tmp_path / ".kodepoia").mkdir()
    store = EvidenceSelectionStore(tmp_path)
    with pytest.raises(ValueError, match="Only fetched artifacts"):
        store.set("", EvidenceSelection.INCLUDED)
    store.set("a" * 64, EvidenceSelection.EXCLUDED)
    assert store.load() == {"a" * 64: EvidenceSelection.EXCLUDED}


def test_refetch_same_content_persists_distinct_retrieval_revisions(tmp_path: Path) -> None:
    (tmp_path / ".kodepoia").mkdir()
    store = ResearchStore(tmp_path)
    first = _artifact(
        locator="https://example.com/docs",
        retrieved_at="2026-09-16T10:00:00Z",
        content="same content",
        version="1.0.0",
    )
    second = _artifact(
        locator="https://example.com/docs",
        retrieved_at="2026-09-17T10:00:00Z",
        content="same content",
        version="1.0.0",
    )
    assert first.artifact_id == second.artifact_id
    store.save_artifact(first)
    store.save_artifact(second)
    revisions = store.list_evidence_revisions()
    assert len(revisions) == 2
    assert revisions[0].artifact_id == revisions[1].artifact_id == first.artifact_id
    assert revisions[0].revision_id != revisions[1].revision_id
    assert store.load_artifact(first.artifact_id).retrieved_at == "2026-09-17T10:00:00Z"


def test_workspace_exposes_lineage_and_conflicting_versions(tmp_path: Path) -> None:
    (tmp_path / ".kodepoia").mkdir()
    store = ResearchStore(tmp_path)
    first = _artifact(
        locator="https://example.com/docs",
        retrieved_at="2026-09-16T10:00:00Z",
        content="version one",
        version="1.0.0",
    )
    second = _artifact(
        locator="https://example.com/docs/",
        retrieved_at="2026-09-17T10:00:00Z",
        content="version two",
        version="2.0.0",
    )
    store.save_artifact(first)
    store.save_artifact(second)
    workspace = EvidenceWorkspace.project(
        (_view(second),),
        revisions=store.list_evidence_revisions(),
        selections={second.artifact_id: EvidenceSelection.EXCLUDED},
    )
    row = workspace.rows[0]
    assert row.lifecycle is EvidenceLifecycle.FETCHED
    assert row.selection is EvidenceSelection.EXCLUDED
    assert row.lineage_artifact_ids == (first.artifact_id, second.artifact_id)
    assert row.conflicting_versions == ("1.0.0", "2.0.0")
    assert row.has_version_conflict is True
