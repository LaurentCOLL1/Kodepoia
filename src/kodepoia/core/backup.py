from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .guardian import KodeGuardian
from .types import ActionKind, ActionRequest


@dataclass(frozen=True, slots=True)
class BackupRecord:
    backup_id: str
    path: Path
    source: Path
    manifest: Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class KodeBackup:
    """Local content-addressed snapshots with integrity manifests."""

    def __init__(self, guardian: KodeGuardian, backup_root: Path) -> None:
        self.guardian = guardian
        self.backup_root = backup_root
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def create(self, source: Path, *, actor: str = "kodepoia.backup") -> BackupRecord:
        source = source.resolve()
        self.guardian.require_allowed(ActionRequest(ActionKind.BACKUP_CREATE, actor, source, str(source)))
        backup_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        destination = self.backup_root / backup_id / "payload"
        destination.parent.mkdir(parents=True, exist_ok=False)
        files: list[dict[str, str | int]] = []
        if source.is_dir():
            shutil.copytree(source, destination)
            for path in sorted(destination.rglob("*")):
                if path.is_file():
                    files.append({"path": path.relative_to(destination).as_posix(), "size": path.stat().st_size, "sha256": _sha256(path)})
        elif source.is_file():
            destination.mkdir()
            copied = destination / source.name
            shutil.copy2(source, copied)
            files.append({"path": source.name, "size": copied.stat().st_size, "sha256": _sha256(copied)})
        else:
            raise FileNotFoundError(source)
        manifest = destination.parent / "manifest.json"
        manifest.write_text(json.dumps({"backup_id": backup_id, "source": str(source), "created_at": datetime.now(UTC).isoformat(), "files": files}, indent=2, sort_keys=True), encoding="utf-8")
        return BackupRecord(backup_id, destination, source, manifest)

    def verify(self, record: BackupRecord) -> bool:
        data = json.loads(record.manifest.read_text(encoding="utf-8"))
        for entry in data["files"]:
            path = record.path / entry["path"]
            if not path.is_file() or path.stat().st_size != entry["size"] or _sha256(path) != entry["sha256"]:
                return False
        return True

    def restore(self, record: BackupRecord, target: Path, *, actor: str = "kodepoia.backup", confirmed: bool = False) -> None:
        target = target.resolve()
        self.guardian.require_allowed(ActionRequest(ActionKind.BACKUP_RESTORE, actor, target, str(target)), confirmed=confirmed)
        if not self.verify(record):
            raise IOError("backup integrity verification failed")
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.copytree(record.path, target)
