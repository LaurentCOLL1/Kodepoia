from __future__ import annotations

from pathlib import Path

from PIL import Image

from kodepoia.assets import (
    AssetId, AssetKind, DuplicateDecisionKind, DuplicateDetector, ProvenanceRef, VaultBoundary, VaultStore,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary


def _ingest(store: VaultStore, project: Path, name: str, asset_key: str, kind: AssetKind):
    return store.ingest(
        project_boundary=WorkspaceBoundary(project),
        source_path=name,
        asset_id=AssetId.from_seed("duplicates", asset_key),
        kind=kind,
        display_name=asset_key,
        provenance=(ProvenanceRef("project", name),),
    )


def test_exact_duplicates_group_bytes_but_preserve_distinct_revisions(tmp_path: Path) -> None:
    vault = tmp_path / "vault"; vault.mkdir()
    project = tmp_path / "project"; project.mkdir()
    (project / "a.txt").write_text("same", encoding="utf-8")
    (project / "b.txt").write_text("same", encoding="utf-8")
    store = VaultStore(VaultBoundary(vault))
    try:
        a = _ingest(store, project, "a.txt", "a", AssetKind.DOCUMENT)
        b = _ingest(store, project, "b.txt", "b", AssetKind.DOCUMENT)
        groups = DuplicateDetector(store).exact_groups()
        assert (a.revision_id, b.revision_id) in groups or (b.revision_id, a.revision_id) in groups
        assert a.revision_id != b.revision_id
        assert len(store.list_revisions()) == 2
    finally:
        store.close()


def test_image_dhash_reports_near_duplicate_without_mutation(tmp_path: Path) -> None:
    vault = tmp_path / "vault"; vault.mkdir()
    project = tmp_path / "project"; project.mkdir()
    base = Image.new("L", (9, 8))
    for y in range(8):
        for x in range(9):
            base.putpixel((x, y), x * 25)
    base.save(project / "a.png")
    near = base.copy(); near.putpixel((4, 4), 80); near.save(project / "b.png")
    store = VaultStore(VaultBoundary(vault))
    try:
        a = _ingest(store, project, "a.png", "image-a", AssetKind.IMAGE)
        b = _ingest(store, project, "b.png", "image-b", AssetKind.IMAGE)
        candidates = DuplicateDetector(store).near_candidates(threshold=0.85)
        pair = {(str(item.left), str(item.right)) for item in candidates}
        assert (str(a.revision_id), str(b.revision_id)) in pair or (str(b.revision_id), str(a.revision_id)) in pair
        assert len(store.list_revisions()) == 2
    finally:
        store.close()


def test_text_normalization_is_similarity_evidence_not_identity(tmp_path: Path) -> None:
    vault = tmp_path / "vault"; vault.mkdir()
    project = tmp_path / "project"; project.mkdir()
    (project / "a.txt").write_text("Hello   World", encoding="utf-8")
    (project / "b.txt").write_text("hello world\n", encoding="utf-8")
    store = VaultStore(VaultBoundary(vault))
    try:
        a = _ingest(store, project, "a.txt", "text-a", AssetKind.DOCUMENT)
        b = _ingest(store, project, "b.txt", "text-b", AssetKind.DOCUMENT)
        assert a.content_sha256 != b.content_sha256
        candidates = DuplicateDetector(store).near_candidates(threshold=1.0)
        assert any({item.left, item.right} == {a.revision_id, b.revision_id} for item in candidates)
    finally:
        store.close()


def test_duplicate_decision_is_audit_record_and_does_not_delete_assets(tmp_path: Path) -> None:
    vault = tmp_path / "vault"; vault.mkdir()
    project = tmp_path / "project"; project.mkdir()
    (project / "a.txt").write_text("same", encoding="utf-8")
    (project / "b.txt").write_text("same", encoding="utf-8")
    store = VaultStore(VaultBoundary(vault))
    try:
        a = _ingest(store, project, "a.txt", "decision-a", AssetKind.DOCUMENT)
        b = _ingest(store, project, "b.txt", "decision-b", AssetKind.DOCUMENT)
        path = DuplicateDetector(store).record_decision(a.revision_id, b.revision_id, DuplicateDecisionKind.KEEP_SEPARATE, reason="Different provenance")
        assert path.exists()
        assert len(store.list_revisions()) == 2
        assert store.object_path(a.revision_id).exists() and store.object_path(b.revision_id).exists()
    finally:
        store.close()
