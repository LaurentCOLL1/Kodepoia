from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kodepoia.intelligence.project_knowledge import (
    ProjectKnowledgeCatalog,
    ProjectKnowledgeItem,
    ProjectKnowledgeSourceKind,
    ProjectKnowledgeState,
)
from kodepoia.intelligence.project_knowledge_lifecycle import (
    ProjectKnowledgeLifecycleManager,
    ProjectKnowledgeLifecycleReason,
    ProjectKnowledgeLifecycleStatus,
    ProjectKnowledgeSelection,
    ProjectKnowledgeVersionInputs,
)
from kodepoia.intelligence.project_retrieval import (
    ProjectRetrievalRequest,
    ProjectRetrievalState,
    ProjectSemanticRetriever,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _item(
    seed: str,
    *,
    kind: ProjectKnowledgeSourceKind = ProjectKnowledgeSourceKind.PROJECT_FILE,
    source_identity: str | None = None,
    source_digest: str | None = None,
    version: str = "",
    locator: str | None = None,
    state: ProjectKnowledgeState = ProjectKnowledgeState.ACTIVE,
) -> ProjectKnowledgeItem:
    identity = source_identity or _digest(f"identity:{seed}")
    source = source_digest or _digest(f"source:{seed}")
    return ProjectKnowledgeItem(
        project_scope="project:fixture",
        source_kind=kind,
        source_identity=identity,
        source_digest_sha256=source,
        content_sha256=_digest(f"content:{seed}:{source}"),
        text=f"knowledge text {seed}",
        trust_class=(
            "external_guarded_untrusted"
            if kind is ProjectKnowledgeSourceKind.RESEARCH_PACK
            else "project_untrusted"
        ),
        freshness="current",
        locator=locator or f"project:///{seed}.md",
        version=version,
        state=state,
        provenance={"seed": seed, "source_digest": source},
    )


def _catalog(*items: ProjectKnowledgeItem) -> ProjectKnowledgeCatalog:
    return ProjectKnowledgeCatalog("project:fixture", tuple(items))


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    return root


def test_refresh_persists_fingerprints_and_selection_state(tmp_path: Path) -> None:
    root = _project(tmp_path)
    first = _item("first", version="4.7")
    catalog = _catalog(first)
    manager = ProjectKnowledgeLifecycleManager(root, "project:fixture")
    versions = ProjectKnowledgeVersionInputs({"engine.godot": "4.7"})

    report = manager.refresh(
        catalog,
        versions,
        version_dependencies={first.knowledge_id: ("engine.godot",)},
    )

    assert report.stale_count == 0
    assert report.invalidated_count == 0
    assert report.items[0].status is ProjectKnowledgeLifecycleStatus.FRESH
    assert report.items[0].reason is ProjectKnowledgeLifecycleReason.CURRENT
    assert manager._lifecycle_store.path.exists()
    persisted = manager._catalog_store.load()
    assert persisted.items[0].state is ProjectKnowledgeState.ACTIVE


def test_source_change_becomes_stale_and_is_not_retrieval_eligible(tmp_path: Path) -> None:
    root = _project(tmp_path)
    identity = _digest("stable:path")
    original = _item("file", source_identity=identity, source_digest=_digest("v1"))
    changed = _item("file", source_identity=identity, source_digest=_digest("v2"))
    manager = ProjectKnowledgeLifecycleManager(root, "project:fixture")
    versions = ProjectKnowledgeVersionInputs({})

    manager.refresh(_catalog(original), versions)
    report = manager.assess(_catalog(changed), versions)
    assert report.items[0].status is ProjectKnowledgeLifecycleStatus.STALE
    assert report.items[0].reason is ProjectKnowledgeLifecycleReason.SOURCE_CHANGED

    effective = manager.effective_catalog(_catalog(changed), versions)
    assert effective.items[0].state is ProjectKnowledgeState.INVALIDATED
    assert effective.items[0].freshness == "stale"
    result = ProjectSemanticRetriever().retrieve(
        effective,
        ProjectRetrievalRequest("project:fixture", "anything"),
        provider=None,
    )
    assert result.state is ProjectRetrievalState.EMPTY
    assert result.eligible_candidates == 0


def test_version_change_invalidates_only_declared_dependencies(tmp_path: Path) -> None:
    root = _project(tmp_path)
    godot = _item("godot")
    blender = _item("blender")
    manager = ProjectKnowledgeLifecycleManager(root, "project:fixture")
    baseline = ProjectKnowledgeVersionInputs(
        {"engine.godot": "4.7", "tool.blender": "4.5"}
    )
    manager.refresh(
        _catalog(godot, blender),
        baseline,
        version_dependencies={
            godot.knowledge_id: ("engine.godot",),
            blender.knowledge_id: ("tool.blender",),
        },
    )

    current = ProjectKnowledgeVersionInputs(
        {"engine.godot": "4.8", "tool.blender": "4.5"}
    )
    report = manager.assess(_catalog(godot, blender), current)
    by_id = {item.knowledge_id: item for item in report.items}
    assert by_id[godot.knowledge_id].status is ProjectKnowledgeLifecycleStatus.INVALIDATED
    assert by_id[godot.knowledge_id].reason is ProjectKnowledgeLifecycleReason.VERSION_CHANGED
    assert by_id[blender.knowledge_id].status is ProjectKnowledgeLifecycleStatus.FRESH


def test_include_exclude_persist_across_explicit_refresh(tmp_path: Path) -> None:
    root = _project(tmp_path)
    first = _item("first")
    second = _item("second")
    versions = ProjectKnowledgeVersionInputs({})
    manager = ProjectKnowledgeLifecycleManager(root, "project:fixture")
    catalog = _catalog(first, second)
    manager.refresh(catalog, versions)

    report = manager.set_selection(
        catalog,
        versions,
        first.knowledge_id,
        ProjectKnowledgeSelection.INCLUDE,
    )
    report = manager.set_selection(
        catalog,
        versions,
        second.knowledge_id,
        ProjectKnowledgeSelection.EXCLUDE,
    )
    by_id = {item.knowledge_id: item for item in report.items}
    assert by_id[first.knowledge_id].selection is ProjectKnowledgeSelection.INCLUDE
    assert by_id[second.knowledge_id].selection is ProjectKnowledgeSelection.EXCLUDE

    refreshed = manager.refresh(catalog, versions)
    by_id = {item.knowledge_id: item for item in refreshed.items}
    assert by_id[first.knowledge_id].selection is ProjectKnowledgeSelection.INCLUDE
    assert by_id[second.knowledge_id].selection is ProjectKnowledgeSelection.EXCLUDE
    persisted = {item.knowledge_id: item for item in manager._catalog_store.load().items}
    assert persisted[first.knowledge_id].state is ProjectKnowledgeState.INCLUDED
    assert persisted[second.knowledge_id].state is ProjectKnowledgeState.EXCLUDED


def test_delete_derived_is_bounded_and_never_deletes_source(tmp_path: Path) -> None:
    root = _project(tmp_path)
    source = root / "notes.md"
    source.write_text("immutable source", encoding="utf-8")
    item = _item("notes", locator="project:///notes.md")
    versions = ProjectKnowledgeVersionInputs({})
    manager = ProjectKnowledgeLifecycleManager(
        root,
        "project:fixture",
        max_delete_items=1,
    )
    manager.refresh(_catalog(item), versions)

    result = manager.delete_derived((item.knowledge_id,))
    assert result.removed_knowledge_ids == (item.knowledge_id,)
    assert result.source_records_deleted is False
    assert result.source_paths_touched == ()
    assert source.read_text(encoding="utf-8") == "immutable source"
    assert manager._catalog_store.load().items == ()
    assert manager._lifecycle_store.load().entries == ()

    with pytest.raises(ValueError, match="bounded item limit"):
        manager.delete_derived((_digest("a"), _digest("b")))


def test_research_pack_identity_is_never_silently_retargeted(tmp_path: Path) -> None:
    root = _project(tmp_path)
    old = _item(
        "pack-old",
        kind=ProjectKnowledgeSourceKind.RESEARCH_PACK,
        source_identity=_digest("pack-a"),
        source_digest=_digest("pack-a"),
        locator="research-pack:///pack-a",
    )
    new = _item(
        "pack-new",
        kind=ProjectKnowledgeSourceKind.RESEARCH_PACK,
        source_identity=_digest("pack-b"),
        source_digest=_digest("pack-b"),
        locator="research-pack:///pack-b",
    )
    manager = ProjectKnowledgeLifecycleManager(root, "project:fixture")
    versions = ProjectKnowledgeVersionInputs({})
    manager.refresh(_catalog(old), versions)

    report = manager.assess(_catalog(new), versions)
    statuses = {item.knowledge_id: item.status for item in report.items}
    reasons = {item.knowledge_id: item.reason for item in report.items}
    assert statuses[old.knowledge_id] is ProjectKnowledgeLifecycleStatus.MISSING
    assert reasons[old.knowledge_id] is ProjectKnowledgeLifecycleReason.SOURCE_MISSING
    assert statuses[new.knowledge_id] is ProjectKnowledgeLifecycleStatus.INVALIDATED
    assert reasons[new.knowledge_id] is ProjectKnowledgeLifecycleReason.BASELINE_MISSING


def test_missing_required_version_input_fails_closed(tmp_path: Path) -> None:
    root = _project(tmp_path)
    item = _item("versioned")
    manager = ProjectKnowledgeLifecycleManager(root, "project:fixture")
    with pytest.raises(ValueError, match="Missing required version fingerprint"):
        manager.refresh(
            _catalog(item),
            ProjectKnowledgeVersionInputs({}),
            version_dependencies={item.knowledge_id: ("engine.godot",)},
        )
