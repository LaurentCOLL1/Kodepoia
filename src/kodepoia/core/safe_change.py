from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from kodepoia.core.fault_injection import DeterministicFaultInjector


@dataclass(frozen=True, slots=True)
class ChangeItem:
    operation: str
    path: Path


@dataclass(frozen=True, slots=True)
class ChangePlan:
    items: tuple[ChangeItem, ...]

    @property
    def destructive_count(self) -> int:
        return sum(item.operation in {"delete", "replace"} for item in self.items)


class SafeChangeManager:
    MANIFEST_NAME = "MANIFEST.json"
    SCHEMA_VERSION = 2

    def __init__(
        self,
        project_root: Path,
        snapshot_root: Path,
        fault_injector: DeterministicFaultInjector | None = None,
    ) -> None:
        self.project_root = project_root.resolve(strict=False)
        self.snapshot_root = snapshot_root.resolve(strict=False)
        self.snapshot_root.mkdir(parents=True, exist_ok=True)
        self.fault_injector = fault_injector

    def _fault(self, component: str, stage: str) -> None:
        if self.fault_injector is not None:
            self.fault_injector.hit(component, stage)

    def ensure_inside_project(self, path: Path) -> Path:
        resolved = path.resolve(strict=False)
        if resolved != self.project_root and self.project_root not in resolved.parents:
            raise ValueError(f"Path escapes project root: {path}")
        return resolved

    @staticmethod
    def _safe_relative(value: str) -> Path:
        pure = PurePosixPath(value)
        if pure.is_absolute() or ".." in pure.parts or value in {"", "."}:
            raise ValueError(f"Unsafe snapshot path: {value}")
        return Path(*pure.parts)

    @staticmethod
    def _remove(path: Path) -> None:
        if path.is_symlink() or path.is_file():
            path.unlink(missing_ok=True)
        elif path.exists():
            shutil.rmtree(path)

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def _tree_hash(cls, root: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
            if path.is_symlink():
                raise ValueError(f"Snapshot trees cannot contain symbolic links: {path}")
            relative = path.relative_to(root).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            if path.is_dir():
                digest.update(b"D")
            elif path.is_file():
                digest.update(b"F")
                digest.update(bytes.fromhex(cls._hash(path)))
        return digest.hexdigest()

    def _capture(self, paths: list[Path], destination: Path) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for path in paths:
            source = self.ensure_inside_project(path)
            relative = source.relative_to(self.project_root)
            target = destination / relative
            if source.is_symlink():
                raise ValueError(f"Snapshot does not follow symbolic links: {source}")
            if not source.exists():
                entries.append({"path": relative.as_posix(), "kind": "missing"})
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                source_digest = self._tree_hash(source)
                shutil.copytree(source, target)
                target_digest = self._tree_hash(target)
                if target_digest != source_digest:
                    raise OSError(f"Snapshot directory changed during capture: {source}")
                entries.append(
                    {
                        "path": relative.as_posix(),
                        "kind": "directory",
                        "sha256": target_digest,
                    }
                )
            else:
                shutil.copy2(source, target)
                entries.append(
                    {
                        "path": relative.as_posix(),
                        "kind": "file",
                        "sha256": self._hash(target),
                    }
                )
        return entries

    @staticmethod
    def _write_manifest(destination: Path, entries: list[dict[str, Any]]) -> None:
        payload = {
            "schema_version": SafeChangeManager.SCHEMA_VERSION,
            "entries": entries,
        }
        (destination / SafeChangeManager.MANIFEST_NAME).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        legacy = [
            f"{entry['path']} {entry.get('sha256', entry['kind'].upper())}"
            for entry in entries
            if entry["kind"] != "missing"
        ]
        (destination / "MANIFEST.txt").write_text("\n".join(legacy), encoding="utf-8")

    def snapshot(self, paths: list[Path]) -> Path:
        self._fault("safe_change.snapshot", "prepare")
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        destination = self.snapshot_root / stamp
        destination.mkdir(parents=True, exist_ok=False)
        try:
            self._fault("safe_change.snapshot", "write")
            entries = self._capture(paths, destination)
            self._write_manifest(destination, entries)
            self._fault("safe_change.snapshot", "commit")
            self._validate_snapshot(destination)
            self._fault("safe_change.snapshot", "verify")
            self._fault("safe_change.snapshot", "cleanup")
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise
        return destination

    def _read_manifest(self, snapshot: Path) -> list[dict[str, Any]]:
        manifest_path = snapshot / self.MANIFEST_NAME
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("SafeChange snapshot manifest is invalid") from exc
        if not isinstance(raw, dict) or raw.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("Unsupported SafeChange snapshot manifest")
        entries = raw.get("entries")
        if not isinstance(entries, list):
            raise ValueError("SafeChange snapshot entries are invalid")
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw_entry in entries:
            if not isinstance(raw_entry, dict):
                raise ValueError("SafeChange snapshot entry must be an object")
            value = raw_entry.get("path")
            kind = raw_entry.get("kind")
            if not isinstance(value, str) or kind not in {"file", "directory", "missing"}:
                raise ValueError("SafeChange snapshot entry is invalid")
            relative = self._safe_relative(value)
            posix = relative.as_posix()
            if posix in seen:
                raise ValueError(f"Duplicate SafeChange snapshot path: {posix}")
            seen.add(posix)
            entry = {"path": posix, "kind": kind}
            if kind != "missing":
                digest = raw_entry.get("sha256")
                if not isinstance(digest, str) or len(digest) != 64:
                    raise ValueError("SafeChange snapshot digest is invalid")
                entry["sha256"] = digest
            normalized.append(entry)
        return normalized

    def _validate_snapshot(self, snapshot: Path) -> list[dict[str, Any]]:
        snapshot = snapshot.resolve(strict=True)
        if snapshot == self.snapshot_root or self.snapshot_root not in snapshot.parents:
            raise ValueError(f"Snapshot escapes snapshot root: {snapshot}")
        entries = self._read_manifest(snapshot)
        for entry in entries:
            relative = self._safe_relative(str(entry["path"]))
            archived = snapshot / relative
            kind = entry["kind"]
            if kind == "missing":
                if archived.exists():
                    raise ValueError(f"Missing snapshot path unexpectedly has data: {relative}")
                continue
            if archived.is_symlink():
                raise ValueError(f"Snapshot contains symbolic link: {relative}")
            expected = str(entry["sha256"])
            if kind == "file":
                if not archived.is_file() or self._hash(archived) != expected:
                    raise ValueError(f"SafeChange snapshot file failed verification: {relative}")
            elif not archived.is_dir() or self._tree_hash(archived) != expected:
                raise ValueError(f"SafeChange snapshot directory failed verification: {relative}")
        return entries

    def _apply_entries(
        self,
        snapshot: Path,
        entries: list[dict[str, Any]],
        *,
        inject: bool,
    ) -> None:
        for entry in entries:
            if inject:
                self._fault("safe_change.restore", "write")
            relative = self._safe_relative(str(entry["path"]))
            target = self.ensure_inside_project(self.project_root / relative)
            archived = snapshot / relative
            self._remove(target)
            if entry["kind"] == "file":
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(archived, target)
            elif entry["kind"] == "directory":
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(archived, target)

    def _verify_project_entries(self, entries: list[dict[str, Any]], *, inject: bool) -> None:
        for entry in entries:
            if inject:
                self._fault("safe_change.restore", "verify")
            relative = self._safe_relative(str(entry["path"]))
            target = self.ensure_inside_project(self.project_root / relative)
            kind = entry["kind"]
            if kind == "missing":
                if target.exists():
                    raise OSError(f"SafeChange rollback failed to remove: {relative}")
            elif kind == "file":
                if not target.is_file() or self._hash(target) != entry["sha256"]:
                    raise OSError(f"SafeChange restored file failed verification: {relative}")
            elif not target.is_dir() or self._tree_hash(target) != entry["sha256"]:
                raise OSError(f"SafeChange restored directory failed verification: {relative}")

    def restore_snapshot(self, snapshot: Path) -> tuple[Path, ...]:
        self._fault("safe_change.restore", "prepare")
        snapshot = snapshot.resolve(strict=True)
        entries = self._validate_snapshot(snapshot)
        paths = [self.project_root / self._safe_relative(str(item["path"])) for item in entries]

        with tempfile.TemporaryDirectory(
            prefix=".restore-rollback-",
            dir=self.snapshot_root,
        ) as rollback_name:
            rollback = Path(rollback_name)
            rollback_entries = self._capture(paths, rollback)
            self._write_manifest(rollback, rollback_entries)
            try:
                self._apply_entries(snapshot, entries, inject=True)
                self._fault("safe_change.restore", "commit")
                self._verify_project_entries(entries, inject=True)
                self._fault("safe_change.restore", "cleanup")
            except Exception:
                self._apply_entries(rollback, rollback_entries, inject=False)
                self._verify_project_entries(rollback_entries, inject=False)
                raise
        return tuple(paths)
