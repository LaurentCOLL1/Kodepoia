from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.assets import (
    AssetId,
    AssetKind,
    PreservationPolicy,
    ProjectAssetReference,
    ProvenanceRef,
    ReuseScope,
    VaultBoundary,
    VaultStore,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary


def _project(tmp_path: Path, name: str) -> tuple[Path, WorkspaceBoundary]:
    root = tmp_path / name
    root.mkdir()
    return root, WorkspaceBoundary(root)


def test_cross_project_reuse_stores_bytes_once_and_preserves_provenance(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    project_a, boundary_a = _project(tmp_path, "project-a")
    project_b, boundary_b = _project(tmp_path, "project-b")
    payload = b"same-source-bytes"
    (project_a / "crate.bin").write_bytes(payload)
    (project_b / "crate.bin").write_bytes(payload)
    store = VaultStore(VaultBoundary(vault_root))
    try:
        first = store.ingest(
            project_boundary=boundary_a,
            source_path="crate.bin",
            asset_id=AssetId.from_seed("project-a", "crate"),
            kind=AssetKind.GENERIC,
            display_name="Crate A",
            provenance=(ProvenanceRef("project", "project-a/crate.bin"),),
            reuse_scope=ReuseScope.VAULT_LOCAL,
        )
        second = store.ingest(
            project_boundary=boundary_b,
            source_path="crate.bin",
            asset_id=AssetId.from_seed("project-b", "crate"),
            kind=AssetKind.GENERIC,
            display_name="Crate B",
            provenance=(ProvenanceRef("project", "project-b/crate.bin"),),
            reuse_scope=ReuseScope.VAULT_LOCAL,
        )
        assert first.content_sha256 == second.content_sha256
        assert first.revision_id != second.revision_id
        objects = [path for path in (vault_root / "objects" / "sha256").rglob("*") if path.is_file()]
        assert len(objects) == 1
        assert len(store.list_revisions()) == 2
    finally:
        store.close()


def test_project_reference_protects_revision_and_materialization_verifies_bytes(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    project, boundary = _project(tmp_path, "project")
    (project / "source.bin").write_bytes(b"asset-data")
    store = VaultStore(VaultBoundary(vault_root))
    try:
        revision = store.ingest(
            project_boundary=boundary,
            source_path="source.bin",
            asset_id=AssetId.from_seed("project", "asset"),
            kind=AssetKind.GENERIC,
            display_name="Asset",
            provenance=(ProvenanceRef("project", "source.bin"),),
            preservation=PreservationPolicy.REFERENCED,
        )
        reference = ProjectAssetReference("project", revision.asset_id, revision.revision_id, "materialized.bin")
        store.add_project_reference(reference, project_boundary=boundary)
        target = store.materialize(revision.revision_id, project_boundary=boundary, target_path="materialized.bin")
        assert target.read_bytes() == b"asset-data"
        plan = store.deletion_plan(revision.revision_id)
        assert plan.protected
        with pytest.raises(PermissionError, match="referenced"):
            store.delete_revision(revision.revision_id, confirm=True)
    finally:
        store.close()


def test_pinned_source_is_never_automatically_removed(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    project, boundary = _project(tmp_path, "project")
    (project / "source.bin").write_bytes(b"pinned")
    store = VaultStore(VaultBoundary(vault_root))
    try:
        revision = store.ingest(
            project_boundary=boundary,
            source_path="source.bin",
            asset_id=AssetId.from_seed("project", "pinned"),
            kind=AssetKind.GENERIC,
            display_name="Pinned",
            provenance=(ProvenanceRef("project", "source.bin"),),
            preservation=PreservationPolicy.PINNED_SOURCE,
        )
        assert store.deletion_plan(revision.revision_id).protected
        with pytest.raises(PermissionError, match="pinned-source"):
            store.delete_revision(revision.revision_id, confirm=True)
    finally:
        store.close()


def test_index_rebuild_from_canonical_manifests(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    project, boundary = _project(tmp_path, "project")
    (project / "source.bin").write_bytes(b"rebuild-me")
    store = VaultStore(VaultBoundary(vault_root))
    revision = store.ingest(
        project_boundary=boundary,
        source_path="source.bin",
        asset_id=AssetId.from_seed("project", "rebuild"),
        kind=AssetKind.GENERIC,
        display_name="Rebuild",
        provenance=(ProvenanceRef("project", "source.bin"),),
    )
    store.close()

    for suffix in ("", "-wal", "-shm"):
        candidate = vault_root / f"index.sqlite3{suffix}"
        if candidate.exists():
            candidate.unlink()
    rebuilt = VaultStore(VaultBoundary(vault_root))
    try:
        report = rebuilt.rebuild_index()
        assert report.corrupt_manifests == ()
        assert report.asset_count == 1
        assert report.revision_count == 1
        assert rebuilt.list_revisions() == [revision.revision_id]
    finally:
        rebuilt.close()


def test_corrupt_object_prevents_ready_materialization_and_rebuild(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    project, boundary = _project(tmp_path, "project")
    (project / "source.bin").write_bytes(b"trusted")
    store = VaultStore(VaultBoundary(vault_root))
    try:
        revision = store.ingest(
            project_boundary=boundary,
            source_path="source.bin",
            asset_id=AssetId.from_seed("project", "corrupt"),
            kind=AssetKind.GENERIC,
            display_name="Corrupt",
            provenance=(ProvenanceRef("project", "source.bin"),),
        )
        store.object_path(revision.revision_id).write_bytes(b"tampered")
        with pytest.raises(ValueError, match="mismatch"):
            store.materialize(revision.revision_id, project_boundary=boundary, target_path="copy.bin")
        with pytest.raises(ValueError, match="mismatch"):
            store.rebuild_index()
    finally:
        store.close()
