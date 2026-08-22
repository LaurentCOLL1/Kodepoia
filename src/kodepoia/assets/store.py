from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from kodepoia.assets.boundary import VaultBoundary
from kodepoia.assets.contracts import (
    AssetId,
    AssetKind,
    AssetRecord,
    AssetRevision,
    AssetRevisionId,
    AssetRole,
    AssetStatus,
    PreservationPolicy,
    ProjectAssetReference,
    ProvenanceRef,
    ReuseScope,
)
from kodepoia.assets.serialization import (
    asset_record_document,
    asset_revision_document,
    canonical_json,
    load_asset_record,
    load_asset_revision,
    load_project_reference,
    project_reference_document,
    verify_content,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary


@dataclass(frozen=True, slots=True)
class RebuildReport:
    asset_count: int
    revision_count: int
    project_reference_count: int
    corrupt_manifests: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DeletionPlan:
    revision_id: AssetRevisionId
    protected: bool
    reasons: tuple[str, ...]
    object_would_be_orphaned: bool


class VaultStore:
    """Local content-addressed Vault with canonical manifests and rebuildable SQLite index."""

    SCHEMA_VERSION = 1

    def __init__(self, boundary: VaultBoundary) -> None:
        self.boundary = boundary
        self.objects_root = boundary.resolve("objects/sha256")
        self.manifest_root = boundary.resolve("manifests")
        self.staging_root = boundary.resolve(".staging")
        self.db_path = boundary.resolve("index.sqlite3")
        for path in (self.objects_root, self.manifest_root, self.staging_root):
            path.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS vault_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                display_name TEXT NOT NULL,
                current_revision_id TEXT
            );
            CREATE TABLE IF NOT EXISTS revisions (
                revision_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                content_length INTEGER NOT NULL,
                role TEXT NOT NULL,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                manifest_rel TEXT NOT NULL UNIQUE
            );
            CREATE INDEX IF NOT EXISTS idx_revisions_asset ON revisions(asset_id);
            CREATE INDEX IF NOT EXISTS idx_revisions_content ON revisions(content_sha256, content_length);
            CREATE TABLE IF NOT EXISTS project_refs (
                project_id TEXT NOT NULL,
                revision_id TEXT NOT NULL,
                target_path TEXT,
                manifest_rel TEXT NOT NULL UNIQUE,
                PRIMARY KEY(project_id, revision_id, target_path)
            );
        """)
        self.db.execute(
            "INSERT OR REPLACE INTO vault_meta(key, value) VALUES('schema_version', ?)",
            (str(self.SCHEMA_VERSION),),
        )
        self.db.commit()

    @staticmethod
    def _hash_file(path: Path, chunk_size: int = 1024 * 1024) -> tuple[str, int]:
        digest = hashlib.sha256()
        total = 0
        with path.open("rb") as handle:
            while chunk := handle.read(chunk_size):
                digest.update(chunk)
                total += len(chunk)
        return digest.hexdigest(), total

    def _object_path(self, digest: str) -> Path:
        return self.boundary.resolve(f"objects/sha256/{digest[:2]}/{digest}")

    def object_path(self, revision_id: AssetRevisionId) -> Path:
        row = self.db.execute(
            "SELECT content_sha256, content_length FROM revisions WHERE revision_id = ?",
            (str(revision_id),),
        ).fetchone()
        if row is None:
            raise KeyError(str(revision_id))
        path = self._object_path(str(row["content_sha256"]))
        verify_content(path, str(row["content_sha256"]), int(row["content_length"]))
        return path

    def _atomic_json(self, relative_path: str, document: dict[str, object]) -> Path:
        destination = self.boundary.resolve(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
        temporary.write_text(canonical_json(document) + "\n", encoding="utf-8", newline="\n")
        os.replace(temporary, destination)
        return destination

    def ingest(
        self,
        *,
        project_boundary: WorkspaceBoundary,
        source_path: str,
        asset_id: AssetId,
        kind: AssetKind,
        display_name: str,
        provenance: tuple[ProvenanceRef, ...],
        reuse_scope: ReuseScope = ReuseScope.PROJECT_ONLY,
        preservation: PreservationPolicy = PreservationPolicy.PINNED_SOURCE,
    ) -> AssetRevision:
        source = project_boundary.resolve(source_path, must_exist=True)
        if not source.is_file():
            raise ValueError(f"Asset source is not a file: {source_path}")

        stage = self.boundary.resolve(f".staging/{uuid.uuid4().hex}.part")
        shutil.copyfile(source, stage)
        try:
            digest, length = self._hash_file(stage)
            verify_content(stage, digest, length)
            object_path = self._object_path(digest)
            object_path.parent.mkdir(parents=True, exist_ok=True)
            if object_path.exists():
                verify_content(object_path, digest, length)
                stage.unlink()
            else:
                os.replace(stage, object_path)
                verify_content(object_path, digest, length)

            revision = AssetRevision.create(
                asset_id=asset_id,
                role=AssetRole.SOURCE,
                kind=kind,
                content_sha256=digest,
                content_length=length,
                reuse_scope=reuse_scope,
                preservation=preservation,
                provenance=provenance,
                status=AssetStatus.READY,
            )
            revision_rel = f"manifests/revisions/{revision.revision_id}.json"
            record = AssetRecord(asset_id, kind, display_name, current_revision_id=revision.revision_id)
            record_rel = f"manifests/assets/{asset_id}.json"
            self._atomic_json(revision_rel, asset_revision_document(revision))
            self._atomic_json(record_rel, asset_record_document(record))
            with self.db:
                self.db.execute(
                    "INSERT OR REPLACE INTO assets(asset_id, kind, display_name, current_revision_id) VALUES(?, ?, ?, ?)",
                    (str(asset_id), kind.value, display_name, str(revision.revision_id)),
                )
                self.db.execute(
                    "INSERT OR REPLACE INTO revisions(revision_id, asset_id, content_sha256, content_length, role, kind, status, manifest_rel) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(revision.revision_id),
                        str(asset_id),
                        digest,
                        length,
                        revision.role.value,
                        revision.kind.value,
                        revision.status.value,
                        revision_rel,
                    ),
                )
            return revision
        finally:
            if stage.exists():
                stage.unlink()

    def add_project_reference(
        self,
        reference: ProjectAssetReference,
        *,
        project_boundary: WorkspaceBoundary | None = None,
    ) -> None:
        row = self.db.execute(
            "SELECT status FROM revisions WHERE revision_id = ?",
            (str(reference.revision_id),),
        ).fetchone()
        if row is None:
            raise KeyError(str(reference.revision_id))
        if str(row["status"]) != AssetStatus.READY.value:
            raise ValueError("Project references require a READY revision")
        if project_boundary is not None and reference.target_path is not None:
            project_boundary.resolve(reference.target_path)
        safe_project = hashlib.sha256(reference.project_id.encode("utf-8")).hexdigest()[:16]
        target_key = hashlib.sha256((reference.target_path or "").encode("utf-8")).hexdigest()[:16]
        manifest_rel = f"manifests/project-refs/{safe_project}-{reference.revision_id}-{target_key}.json"
        self._atomic_json(manifest_rel, project_reference_document(reference))
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO project_refs(project_id, revision_id, target_path, manifest_rel) VALUES(?, ?, ?, ?)",
                (reference.project_id, str(reference.revision_id), reference.target_path, manifest_rel),
            )

    def materialize(
        self,
        revision_id: AssetRevisionId,
        *,
        project_boundary: WorkspaceBoundary,
        target_path: str,
        overwrite: bool = False,
    ) -> Path:
        source = self.object_path(revision_id)
        row = self.db.execute(
            "SELECT content_sha256, content_length FROM revisions WHERE revision_id = ?",
            (str(revision_id),),
        ).fetchone()
        assert row is not None
        target = project_boundary.resolve(target_path)
        if target.exists() and not overwrite:
            raise FileExistsError(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        shutil.copyfile(source, temporary)
        verify_content(temporary, str(row["content_sha256"]), int(row["content_length"]))
        os.replace(temporary, target)
        return target

    def deletion_plan(self, revision_id: AssetRevisionId) -> DeletionPlan:
        manifest = self._load_revision_manifest(revision_id)
        ref_count = int(
            self.db.execute(
                "SELECT COUNT(*) FROM project_refs WHERE revision_id = ?",
                (str(revision_id),),
            ).fetchone()[0]
        )
        reasons: list[str] = []
        if ref_count:
            reasons.append(f"referenced-by-{ref_count}-project-records")
        if manifest.preservation is PreservationPolicy.PINNED_SOURCE:
            reasons.append("pinned-source")
        other = int(
            self.db.execute(
                "SELECT COUNT(*) FROM revisions WHERE content_sha256 = ? AND revision_id != ?",
                (manifest.content_sha256, str(revision_id)),
            ).fetchone()[0]
        )
        return DeletionPlan(revision_id, bool(reasons), tuple(reasons), other == 0)

    def delete_revision(self, revision_id: AssetRevisionId, *, confirm: bool = False) -> DeletionPlan:
        plan = self.deletion_plan(revision_id)
        if plan.protected:
            raise PermissionError(f"Revision deletion blocked: {', '.join(plan.reasons)}")
        if not confirm:
            return plan
        revision = self._load_revision_manifest(revision_id)
        manifest_path = self.boundary.resolve(f"manifests/revisions/{revision_id}.json")
        with self.db:
            self.db.execute("DELETE FROM revisions WHERE revision_id = ?", (str(revision_id),))
        if manifest_path.exists():
            manifest_path.unlink()
        if plan.object_would_be_orphaned:
            object_path = self._object_path(revision.content_sha256)
            if object_path.exists():
                verify_content(object_path, revision.content_sha256, revision.content_length)
                object_path.unlink()
        return plan

    def _load_revision_manifest(self, revision_id: AssetRevisionId) -> AssetRevision:
        path = self.boundary.resolve(f"manifests/revisions/{revision_id}.json", must_exist=True)
        return load_asset_revision(json.loads(path.read_text(encoding="utf-8")))

    def list_revisions(self, asset_id: AssetId | None = None) -> list[AssetRevisionId]:
        if asset_id is None:
            rows = self.db.execute("SELECT revision_id FROM revisions ORDER BY revision_id").fetchall()
        else:
            rows = self.db.execute(
                "SELECT revision_id FROM revisions WHERE asset_id = ? ORDER BY revision_id",
                (str(asset_id),),
            ).fetchall()
        return [AssetRevisionId(str(row["revision_id"])) for row in rows]

    def rebuild_index(self) -> RebuildReport:
        corrupt: list[str] = []
        assets: list[tuple[AssetRecord, str]] = []
        revisions: list[tuple[AssetRevision, str]] = []
        references: list[tuple[ProjectAssetReference, str]] = []
        for folder, loader, destination in (
            ("assets", load_asset_record, assets),
            ("revisions", load_asset_revision, revisions),
            ("project-refs", load_project_reference, references),
        ):
            root = self.manifest_root / folder
            if not root.exists():
                continue
            for path in sorted(root.glob("*.json")):
                rel = self.boundary.relative(path)
                try:
                    destination.append((loader(json.loads(path.read_text(encoding="utf-8"))), rel))
                except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                    corrupt.append(rel)
        if corrupt:
            return RebuildReport(0, 0, 0, tuple(corrupt))

        with self.db:
            self.db.execute("DELETE FROM project_refs")
            self.db.execute("DELETE FROM revisions")
            self.db.execute("DELETE FROM assets")
            for record, _ in assets:
                self.db.execute(
                    "INSERT INTO assets(asset_id, kind, display_name, current_revision_id) VALUES(?, ?, ?, ?)",
                    (
                        str(record.asset_id),
                        record.kind.value,
                        record.display_name,
                        str(record.current_revision_id) if record.current_revision_id else None,
                    ),
                )
            for revision, rel in revisions:
                object_path = self._object_path(revision.content_sha256)
                verify_content(object_path, revision.content_sha256, revision.content_length)
                self.db.execute(
                    "INSERT INTO revisions(revision_id, asset_id, content_sha256, content_length, role, kind, status, manifest_rel) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(revision.revision_id),
                        str(revision.asset_id),
                        revision.content_sha256,
                        revision.content_length,
                        revision.role.value,
                        revision.kind.value,
                        revision.status.value,
                        rel,
                    ),
                )
            for reference, rel in references:
                self.db.execute(
                    "INSERT INTO project_refs(project_id, revision_id, target_path, manifest_rel) VALUES(?, ?, ?, ?)",
                    (reference.project_id, str(reference.revision_id), reference.target_path, rel),
                )
        return RebuildReport(len(assets), len(revisions), len(references))

    def close(self) -> None:
        self.db.close()
