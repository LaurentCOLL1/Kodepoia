from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.intelligence.memory import MemoryStore
from kodepoia.intelligence.project_knowledge import (
    ProjectKnowledgeBuilder,
    ProjectKnowledgeCatalog,
    ProjectKnowledgeItem,
    ProjectKnowledgeSourceKind,
    ProjectKnowledgeState,
    ProjectKnowledgeStore,
)
from kodepoia.intelligence.research.contracts import ResearchFindingKind
from kodepoia.intelligence.research.synthesis import (
    CitationSnapshot,
    ResearchPack,
    ResearchPackStore,
    ResearchSynthesis,
    SynthesizedClaim,
)
from kodepoia.kodecode.workspace import WorkspaceViolation


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    return root


def _pack() -> ResearchPack:
    citation = CitationSnapshot(
        artifact_id=_digest("artifact"),
        revision_id=_digest("revision"),
        source_identity_id=_digest("source-identity"),
        canonical_locator="https://example.com/docs",
        content_sha256=_digest("source-content"),
        retrieved_at="2026-09-18T00:00:00Z",
        source_kind="web",
        version="4.7",
        label="Example docs",
    )
    claim = SynthesizedClaim(
        kind=ResearchFindingKind.SOURCE_FACT,
        claim="The governed source supports this fact.",
        citation_ids=(citation.citation_id,),
        confidence=0.9,
    )
    synthesis = ResearchSynthesis(
        question="What is supported?",
        request_identity=_digest("request"),
        generated_at="2026-09-18T00:01:00Z",
        citations=(citation,),
        claims=(claim,),
        synthesis="[1] source_fact: The governed source supports this fact.",
    )
    return ResearchPack(synthesis=synthesis)


def _memory(path: Path) -> MemoryStore:
    memory = MemoryStore(path)
    memory.add(
        "project:fixture",
        "decision",
        "Use deterministic project knowledge.",
        origin="project:decision",
        project_scope="project:fixture",
        trust_class="project",
        record_class="project_fact",
        version=2,
    )
    memory.add(
        "project:other",
        "decision",
        "Other project only.",
        origin="other:decision",
        project_scope="project:other",
        trust_class="project",
        record_class="project_fact",
        version=1,
    )
    return memory


def test_item_and_catalog_roundtrip_preserve_deterministic_identity() -> None:
    item = ProjectKnowledgeItem(
        project_scope="project:fixture",
        source_kind=ProjectKnowledgeSourceKind.PROJECT_FILE,
        source_identity=_digest("README.md"),
        source_digest_sha256=_digest("raw"),
        content_sha256=_digest("rendered"),
        text="bounded data",
        trust_class="project_untrusted",
        freshness="current",
        locator="project:///README.md",
        state=ProjectKnowledgeState.EXCLUDED,
        provenance={"project_relative_path": "README.md"},
    )
    restored = ProjectKnowledgeItem.from_dict(item.to_dict())
    assert restored.knowledge_id == item.knowledge_id
    assert restored.digest_sha256 == item.digest_sha256
    assert restored.state is ProjectKnowledgeState.EXCLUDED

    catalog = ProjectKnowledgeCatalog(project_scope="project:fixture", items=(item,))
    catalog_restored = ProjectKnowledgeCatalog.from_dict(catalog.to_dict())
    assert catalog_restored.digest_sha256 == catalog.digest_sha256
    assert catalog_restored.items == (item,)


def test_builder_projects_pack_file_and_only_active_project_memory(tmp_path: Path) -> None:
    root = _project(tmp_path)
    pack = _pack()
    pack_path = ResearchPackStore(root).save(pack)
    pack_bytes = pack_path.read_bytes()
    source = root / "docs" / "design.md"
    source.parent.mkdir()
    source.write_text("# Design\nProject-scoped knowledge.", encoding="utf-8")
    memory = _memory(tmp_path / "memory.sqlite")
    before_rows = memory.db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    builder = ProjectKnowledgeBuilder(root, "project:fixture")
    catalog = builder.build(project_files=("docs/design.md",), memory=memory)

    assert {item.source_kind for item in catalog.items} == {
        ProjectKnowledgeSourceKind.RESEARCH_PACK,
        ProjectKnowledgeSourceKind.PROJECT_FILE,
        ProjectKnowledgeSourceKind.MEMORY,
    }
    assert len(catalog.items) == 3
    memory_item = next(
        item for item in catalog.items if item.source_kind is ProjectKnowledgeSourceKind.MEMORY
    )
    assert memory_item.provenance["origin"] == "project:decision"
    assert memory_item.version == "2"
    assert "Other project only." not in json.dumps(catalog.to_dict())
    assert memory.db.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == before_rows
    assert [record.content for record in memory.list_project_scope("project:other")] == [
        "Other project only."
    ]
    assert pack_path.read_bytes() == pack_bytes
    memory.close()


def test_build_is_deterministic_and_deduplicates_explicit_file_inputs(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "a.md").write_text("alpha", encoding="utf-8")
    (root / "b.md").write_text("beta", encoding="utf-8")
    builder = ProjectKnowledgeBuilder(root, "project:fixture")

    first = builder.build(project_files=("b.md", "a.md", "a.md"))
    second = builder.build(project_files=("a.md", "b.md"))

    assert len(first.items) == 2
    assert first.digest_sha256 == second.digest_sha256
    assert [item.knowledge_id for item in first.items] == sorted(
        item.knowledge_id for item in first.items
    )


def test_store_is_project_confined_atomic_and_digest_validated(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "README.md").write_text("catalog me", encoding="utf-8")
    builder = ProjectKnowledgeBuilder(root, "project:fixture")
    catalog = builder.build(project_files=("README.md",))
    store = ProjectKnowledgeStore(root, "project:fixture")

    path = store.save(catalog)
    assert path == root / ".kodepoia" / "knowledge" / "catalog-v1.json"
    assert store.load().digest_sha256 == catalog.digest_sha256
    assert not path.with_name(f".{path.name}.tmp").exists()

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["items"][0]["text"] = "tampered derived knowledge"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        store.load()


def test_project_file_projection_fails_closed_on_workspace_escape_and_self_index(tmp_path: Path) -> None:
    root = _project(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    derived = root / ".kodepoia" / "knowledge" / "catalog-v1.json"
    derived.parent.mkdir(parents=True)
    derived.write_text("{}", encoding="utf-8")
    builder = ProjectKnowledgeBuilder(root, "project:fixture")

    with pytest.raises(WorkspaceViolation):
        builder.project_file_item("../outside.txt")
    with pytest.raises(WorkspaceViolation):
        builder.project_file_item(outside)
    with pytest.raises(ValueError, match="recursively index"):
        builder.project_file_item(".kodepoia/knowledge/catalog-v1.json")


def test_project_file_projection_is_bounded_utf8_and_secret_redacted(tmp_path: Path) -> None:
    root = _project(tmp_path)
    secret = "supersecretvalue123456789"
    source = root / "notes.txt"
    source.write_text(f"api_key={secret}\nnormal fact", encoding="utf-8")
    builder = ProjectKnowledgeBuilder(root, "project:fixture", max_file_bytes=128)
    catalog = builder.build(project_files=("notes.txt",))
    item = catalog.items[0]

    assert secret not in item.text
    assert "***REDACTED***" in item.text
    assert item.provenance["redacted"] is True
    store = ProjectKnowledgeStore(root, "project:fixture")
    persisted = store.save(catalog).read_text(encoding="utf-8")
    assert secret not in persisted

    (root / "too-large.txt").write_text("x" * 129, encoding="utf-8")
    with pytest.raises(ValueError, match="byte limit"):
        builder.project_file_item("too-large.txt")

    (root / "binary.txt").write_bytes(b"\xff\xfe")
    with pytest.raises(ValueError, match="UTF-8"):
        builder.project_file_item("binary.txt")


def test_research_pack_filename_must_match_immutable_pack_digest(tmp_path: Path) -> None:
    root = _project(tmp_path)
    pack = _pack()
    original = ResearchPackStore(root).save(pack)
    mismatched = original.with_name(f"{'0' * 64}.json")
    mismatched.write_bytes(original.read_bytes())

    builder = ProjectKnowledgeBuilder(root, "project:fixture")
    with pytest.raises(ValueError, match="filename"):
        builder.research_pack_items()


def test_memory_projection_is_bounded_and_preserves_integrity_metadata(tmp_path: Path) -> None:
    root = _project(tmp_path)
    memory = _memory(tmp_path / "memory.sqlite")
    builder = ProjectKnowledgeBuilder(root, "project:fixture", max_memory_items=1)
    items = builder.memory_items(memory)
    assert len(items) == 1
    assert items[0].source_kind is ProjectKnowledgeSourceKind.MEMORY
    assert items[0].provenance["integrity_digest"] == items[0].source_digest_sha256

    memory.add(
        "project:fixture",
        "note",
        "second eligible record",
        origin="project:note",
        project_scope="project:fixture",
        trust_class="project",
    )
    with pytest.raises(ValueError, match="bounded item limit"):
        builder.memory_items(memory)
    memory.close()


@pytest.mark.parametrize("scope", ["", "global", "GLOBAL:shared"])
def test_non_project_scope_is_rejected(tmp_path: Path, scope: str) -> None:
    root = _project(tmp_path)
    with pytest.raises(ValueError):
        ProjectKnowledgeBuilder(root, scope)
    with pytest.raises(ValueError):
        ProjectKnowledgeStore(root, scope)
