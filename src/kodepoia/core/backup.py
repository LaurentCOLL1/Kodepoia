from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path


class BackupManager:
    def __init__(self, backup_root: Path) -> None:
        self.backup_root = backup_root
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def create_archive(self, project_root: Path, label: str = "snapshot") -> Path:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        base = self.backup_root / f"{stamp}-{label}"
        archive = shutil.make_archive(str(base), "zip", root_dir=project_root)
        return Path(archive)
