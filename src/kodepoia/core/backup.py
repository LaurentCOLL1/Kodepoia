from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import uuid
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from kodepoia.core.fault_injection import DeterministicFaultInjector


@dataclass(frozen=True, slots=True)
class BackupEntry:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class BackupManifest:
    schema_version: int
    created_at: str
    project_name: str
    files: tuple[BackupEntry, ...]


class BackupManager:
    MANIFEST_NAME = ".kodepoia-backup-manifest.json"

    def __init__(
        self,
        backup_root: Path,
        fault_injector: DeterministicFaultInjector | None = None,
    ) -> None:
        self.backup_root = backup_root
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.fault_injector = fault_injector

    def _fault(self, stage: str) -> None:
        if self.fault_injector is not None:
            self.fault_injector.hit("backup.restore", stage)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _safe_archive_path(value: str) -> bool:
        path = PurePosixPath(value)
        return not path.is_absolute() and ".." not in path.parts and value not in {"", "."}

    def _manifest_for(self, project_root: Path) -> BackupManifest:
        project_root = project_root.resolve(strict=True)
        entries: list[BackupEntry] = []
        for path in sorted(item for item in project_root.rglob("*") if item.is_file()):
            relative = path.relative_to(project_root).as_posix()
            entries.append(BackupEntry(relative, path.stat().st_size, self._sha256(path)))
        return BackupManifest(
            schema_version=1,
            created_at=datetime.now(UTC).isoformat(),
            project_name=project_root.name,
            files=tuple(entries),
        )

    def create_archive(self, project_root: Path, label: str = "snapshot") -> Path:
        project_root = project_root.resolve(strict=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        archive = self.backup_root / f"{stamp}-{label}.zip"
        manifest = self._manifest_for(project_root)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for entry in manifest.files:
                zf.write(project_root / entry.path, arcname=entry.path)
            zf.writestr(
                self.MANIFEST_NAME,
                json.dumps(asdict(manifest), ensure_ascii=False, indent=2),
            )
        if not self.verify(archive):
            archive.unlink(missing_ok=True)
            raise OSError("Backup verification failed immediately after creation")
        return archive

    def read_manifest(self, archive: Path) -> BackupManifest:
        with zipfile.ZipFile(archive, "r") as zf:
            raw = json.loads(zf.read(self.MANIFEST_NAME).decode("utf-8"))
        return BackupManifest(
            schema_version=int(raw["schema_version"]),
            created_at=str(raw["created_at"]),
            project_name=str(raw["project_name"]),
            files=tuple(BackupEntry(**entry) for entry in raw["files"]),
        )

    def verify(self, archive: Path) -> bool:
        archive = archive.resolve(strict=True)
        try:
            manifest = self.read_manifest(archive)
            if manifest.schema_version != 1:
                return False
            expected_names = {self.MANIFEST_NAME}
            expected_names.update(entry.path for entry in manifest.files)
            if any(not self._safe_archive_path(entry.path) for entry in manifest.files):
                return False

            with zipfile.ZipFile(archive, "r") as zf:
                names = set(zf.namelist())
                if names != expected_names:
                    return False
                for entry in manifest.files:
                    info = zf.getinfo(entry.path)
                    if info.is_dir() or info.file_size != entry.size:
                        return False
                    digest = hashlib.sha256()
                    with zf.open(info, "r") as handle:
                        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                            digest.update(chunk)
                    if digest.hexdigest() != entry.sha256:
                        return False
            return True
        except (KeyError, OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError):
            return False

    def _extract_validated(self, archive: Path, destination: Path) -> BackupManifest:
        manifest = self.read_manifest(archive)
        with zipfile.ZipFile(archive, "r") as zf:
            for entry in manifest.files:
                self._fault("write")
                target = (destination / entry.path).resolve(strict=False)
                if target != destination and destination not in target.parents:
                    raise ValueError(f"Unsafe path in backup: {entry.path}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(entry.path, "r") as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
        for entry in manifest.files:
            self._fault("verify")
            restored = destination / entry.path
            if not restored.is_file() or self._sha256(restored) != entry.sha256:
                raise OSError(f"Restored file failed verification: {entry.path}")
        return manifest

    def restore(self, archive: Path, destination: Path, *, overwrite: bool = False) -> Path:
        if not self.verify(archive):
            raise ValueError("Refusing to restore an invalid or corrupted backup")

        destination = destination.resolve(strict=False)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and destination.is_file():
            raise FileExistsError(f"Restore destination is a file: {destination}")
        if destination.exists() and any(destination.iterdir()) and not overwrite:
            raise FileExistsError(f"Restore destination is not empty: {destination}")

        self._fault("prepare")
        stage = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.restore-",
                dir=destination.parent,
            )
        )
        rollback = destination.parent / f".{destination.name}.rollback-{uuid.uuid4().hex}"
        moved_previous = False
        committed = False
        try:
            self._extract_validated(archive, stage)
            self._fault("commit")
            if destination.exists():
                destination.replace(rollback)
                moved_previous = True
                self._fault("commit")
            stage.replace(destination)
            committed = True

            manifest = self.read_manifest(archive)
            for entry in manifest.files:
                self._fault("verify")
                restored = destination / entry.path
                if not restored.is_file() or self._sha256(restored) != entry.sha256:
                    raise OSError(f"Committed restore failed verification: {entry.path}")
            self._fault("cleanup")
        except Exception:
            if committed and destination.exists():
                shutil.rmtree(destination)
            if moved_previous and rollback.exists():
                rollback.replace(destination)
                moved_previous = False
            raise
        finally:
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)
            if moved_previous and rollback.exists():
                shutil.rmtree(rollback, ignore_errors=True)
        return destination
