from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import BackupManager
from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.media.serialization import canonical_json_bytes, canonical_sha256


_MAX_MIGRATION_STEPS = 16
_MAX_STATE_BYTES = 8 * 1024 * 1024


class CompatibilityState(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    MIGRATION_REQUIRED = "MIGRATION_REQUIRED"
    UNSUPPORTED_NEWER = "UNSUPPORTED_NEWER"
    CORRUPT = "CORRUPT"


@dataclass(frozen=True, slots=True)
class CompatibilityReport:
    state: CompatibilityState
    source_schema_version: int | None
    target_schema_version: int
    migration_step_ids: tuple[str, ...] = ()
    reason: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "source_schema_version": self.source_schema_version,
            "target_schema_version": self.target_schema_version,
            "migration_step_ids": list(self.migration_step_ids),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class SaveBridgeDocument:
    schema_id: str
    schema_version: int
    project_id: str
    franchise_dna_id: str
    content_version: str
    canon_snapshot_digest: str
    state: dict[str, Any]
    extensions: dict[str, Any]
    checksum: str

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "franchise_dna_id": self.franchise_dna_id,
            "content_version": self.content_version,
            "canon_snapshot_digest": self.canon_snapshot_digest,
            "state": self.state,
            "extensions": self.extensions,
        }

    def canonical(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["checksum"] = self.checksum
        return payload

    def verify(self) -> bool:
        return self.checksum == canonical_sha256(self.payload_without_checksum())


def _validate_digest(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{field} must be lowercase SHA-256")


def _validate_extensions(extensions: dict[str, Any]) -> None:
    if not isinstance(extensions, dict) or len(extensions) > 128:
        raise ValueError("extensions must be a bounded object")
    for key in extensions:
        if not isinstance(key, str) or "." not in key or key.startswith(".") or key.endswith(".") or len(key) > 128:
            raise ValueError("SaveBridge extension keys must be namespaced")
    canonical_json_bytes(extensions)


def build_save_document(
    *,
    schema_id: str,
    schema_version: int,
    project_id: str,
    franchise_dna_id: str,
    content_version: str,
    canon_snapshot_digest: str,
    state: dict[str, Any],
    extensions: dict[str, Any] | None = None,
) -> SaveBridgeDocument:
    for value, field in ((schema_id, "schema_id"), (project_id, "project_id"), (franchise_dna_id, "franchise_dna_id"), (content_version, "content_version")):
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise ValueError(f"{field} must be non-empty and bounded")
    if not isinstance(schema_version, int) or schema_version < 1 or schema_version > 1_000_000:
        raise ValueError("schema_version must be a positive bounded integer")
    _validate_digest(canon_snapshot_digest, "canon_snapshot_digest")
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    if len(canonical_json_bytes(state)) > _MAX_STATE_BYTES:
        raise ValueError("SaveBridge state byte budget exceeded")
    ext = dict(extensions or {})
    _validate_extensions(ext)
    payload = {
        "schema_id": schema_id,
        "schema_version": schema_version,
        "project_id": project_id,
        "franchise_dna_id": franchise_dna_id,
        "content_version": content_version,
        "canon_snapshot_digest": canon_snapshot_digest,
        "state": state,
        "extensions": ext,
    }
    return SaveBridgeDocument(checksum=canonical_sha256(payload), **payload)


def parse_save_document(raw: bytes | str | dict[str, Any]) -> SaveBridgeDocument:
    if isinstance(raw, bytes):
        if len(raw) > _MAX_STATE_BYTES + 1024 * 1024:
            raise ValueError("SaveBridge document byte budget exceeded")
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("SaveBridge document is corrupt or truncated") from exc
    else:
        data = dict(raw)
    expected = {"schema_id", "schema_version", "project_id", "franchise_dna_id", "content_version", "canon_snapshot_digest", "state", "extensions", "checksum"}
    if set(data) != expected:
        raise ValueError("SaveBridge document fields are invalid")
    doc = build_save_document(
        schema_id=data["schema_id"],
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        franchise_dna_id=data["franchise_dna_id"],
        content_version=data["content_version"],
        canon_snapshot_digest=data["canon_snapshot_digest"],
        state=data["state"],
        extensions=data["extensions"],
    )
    if not isinstance(data["checksum"], str) or data["checksum"] != doc.checksum:
        raise ValueError("SaveBridge checksum mismatch")
    return doc


MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class MigrationStep:
    step_id: str
    source_version: int
    target_version: int
    migrate_state: MigrationFn

    def __post_init__(self) -> None:
        if not self.step_id or len(self.step_id) > 128:
            raise ValueError("Migration step_id must be non-empty and bounded")
        if self.source_version < 1 or self.target_version < 1 or self.source_version == self.target_version:
            raise ValueError("Migration step must change positive schema version")
        if not callable(self.migrate_state):
            raise ValueError("Migration function must be trusted callable code")


class MigrationRegistry:
    def __init__(self) -> None:
        self._steps: dict[str, MigrationStep] = {}

    def register(self, step: MigrationStep) -> None:
        if step.step_id in self._steps:
            raise ValueError(f"Duplicate migration step: {step.step_id}")
        candidate = dict(self._steps)
        candidate[step.step_id] = step
        _reject_version_cycles(candidate.values())
        self._steps = candidate

    def path(self, source_version: int, target_version: int) -> tuple[MigrationStep, ...]:
        if source_version == target_version:
            return ()
        queue: deque[tuple[int, tuple[MigrationStep, ...]]] = deque([(source_version, ())])
        visited: set[int] = {source_version}
        by_source: dict[int, list[MigrationStep]] = {}
        for step in self._steps.values():
            by_source.setdefault(step.source_version, []).append(step)
        for steps in by_source.values():
            steps.sort(key=lambda item: item.step_id)
        while queue:
            version, path = queue.popleft()
            if len(path) >= _MAX_MIGRATION_STEPS:
                continue
            for step in by_source.get(version, []):
                next_path = path + (step,)
                if step.target_version == target_version:
                    return next_path
                if step.target_version not in visited:
                    visited.add(step.target_version)
                    queue.append((step.target_version, next_path))
        raise ValueError(f"No bounded migration path {source_version} -> {target_version}")


def _reject_version_cycles(steps: Any) -> None:
    graph: dict[int, set[int]] = {}
    for step in steps:
        graph.setdefault(step.source_version, set()).add(step.target_version)
        graph.setdefault(step.target_version, set())
    visiting: set[int] = set()
    visited: set[int] = set()

    def visit(node: int) -> None:
        if node in visiting:
            raise ValueError("Migration version graph contains a cycle")
        if node in visited:
            return
        visiting.add(node)
        for target in sorted(graph[node]):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node)


def check_compatibility(document: SaveBridgeDocument | dict[str, Any] | str | bytes, *, target_schema_version: int, registry: MigrationRegistry) -> CompatibilityReport:
    try:
        doc = document if isinstance(document, SaveBridgeDocument) else parse_save_document(document)
    except (UnicodeDecodeError, ValueError) as exc:
        return CompatibilityReport(CompatibilityState.CORRUPT, None, target_schema_version, reason=str(exc))
    if doc.schema_version == target_schema_version:
        return CompatibilityReport(CompatibilityState.COMPATIBLE, doc.schema_version, target_schema_version)
    if doc.schema_version > target_schema_version:
        return CompatibilityReport(CompatibilityState.UNSUPPORTED_NEWER, doc.schema_version, target_schema_version, reason="newer save schema is not downgraded automatically")
    try:
        path = registry.path(doc.schema_version, target_schema_version)
    except ValueError as exc:
        return CompatibilityReport(CompatibilityState.MIGRATION_REQUIRED, doc.schema_version, target_schema_version, reason=str(exc))
    return CompatibilityReport(CompatibilityState.MIGRATION_REQUIRED, doc.schema_version, target_schema_version, tuple(step.step_id for step in path))


def migrate_document(document: SaveBridgeDocument, *, target_schema_version: int, registry: MigrationRegistry) -> tuple[SaveBridgeDocument, CompatibilityReport]:
    if not document.verify():
        raise ValueError("Cannot migrate tampered SaveBridge document")
    if document.schema_version > target_schema_version:
        raise ValueError("UNSUPPORTED_NEWER saves cannot be destructively downgraded")
    path = registry.path(document.schema_version, target_schema_version)
    if not path:
        return document, CompatibilityReport(CompatibilityState.COMPATIBLE, document.schema_version, target_schema_version)
    state = json.loads(json.dumps(document.state, ensure_ascii=False, allow_nan=False))
    for step in path:
        migrated = step.migrate_state(state)
        if not isinstance(migrated, dict):
            raise ValueError(f"Migration step {step.step_id} did not return an object")
        canonical_json_bytes(migrated)
        state = migrated
    result = build_save_document(
        schema_id=document.schema_id,
        schema_version=target_schema_version,
        project_id=document.project_id,
        franchise_dna_id=document.franchise_dna_id,
        content_version=document.content_version,
        canon_snapshot_digest=document.canon_snapshot_digest,
        state=state,
        extensions=document.extensions,
    )
    report = CompatibilityReport(
        CompatibilityState.COMPATIBLE,
        document.schema_version,
        target_schema_version,
        tuple(step.step_id for step in path),
    )
    return result, report


class SaveBridgeStore:
    def __init__(
        self,
        *,
        project_root: Path,
        snapshot_root: Path,
        backup_root: Path,
        guardian: KodeGuardian,
        audit: AuditLog,
        recovery: RecoveryJournal,
        post_write_verifier: Callable[[SaveBridgeDocument], None] | None = None,
    ) -> None:
        self.project_root = project_root.resolve(strict=False)
        self.safe_change = SafeChangeManager(self.project_root, snapshot_root)
        self.backups = BackupManager(backup_root)
        self.guardian = guardian
        self.audit = audit
        self.recovery = recovery
        self.post_write_verifier = post_write_verifier

    def migrate_file(
        self,
        relative_path: Path,
        *,
        target_schema_version: int,
        registry: MigrationRegistry,
        actor: str,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        target = self.safe_change.ensure_inside_project(self.project_root / relative_path)
        before_bytes = target.read_bytes()
        before = parse_save_document(before_bytes)
        migrated, report = migrate_document(before, target_schema_version=target_schema_version, registry=registry)
        before_digest = canonical_sha256(before.canonical())
        after_digest = canonical_sha256(migrated.canonical())
        base_result = {
            "status": "DRY_RUN" if dry_run else "MIGRATED",
            "before_digest": before_digest,
            "after_digest": after_digest,
            "migration_step_ids": list(report.migration_step_ids),
        }
        if dry_run or before_digest == after_digest:
            return base_result

        decision = self.guardian.authorize(ActionRequest(ActionType.WRITE, actor=actor, target=str(target), project_root=self.project_root))
        if decision.kind is not DecisionKind.ALLOW:
            raise PermissionError(f"Guardian did not allow save migration: {decision.reason}")
        safe_snapshot = self.safe_change.snapshot([target]) if decision.snapshot_required else None
        backup_archive = self.backups.create_archive(target.parent, label="savebridge")
        self.recovery.save(
            f"savebridge:{relative_path.as_posix()}",
            "prepared",
            {"before_digest": before_digest, "after_digest": after_digest, "backup_archive": backup_archive.name},
        )
        payload = json.dumps(migrated.canonical(), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
        temporary = target.with_suffix(target.suffix + ".tmp")
        try:
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(target)
            verified = parse_save_document(target.read_bytes())
            if canonical_sha256(verified.canonical()) != after_digest:
                raise ValueError("Post-write SaveBridge verification digest mismatch")
            if self.post_write_verifier is not None:
                self.post_write_verifier(verified)
        except Exception:
            target.write_bytes(before_bytes)
            self.recovery.save(
                f"savebridge:{relative_path.as_posix()}",
                "rolled_back",
                {"restored_digest": canonical_sha256(parse_save_document(target.read_bytes()).canonical())},
            )
            self.audit.append("savebridge", "migrate", actor, "rolled_back", {"target": relative_path.as_posix(), "before_digest": before_digest})
            raise
        finally:
            temporary.unlink(missing_ok=True)

        self.recovery.clear()
        event = self.audit.append(
            "savebridge",
            "migrate",
            actor,
            "success",
            {
                "target": relative_path.as_posix(),
                "before_digest": before_digest,
                "after_digest": after_digest,
                "steps": list(report.migration_step_ids),
                "safe_snapshot": None if safe_snapshot is None else safe_snapshot.name,
                "backup_archive": backup_archive.name,
            },
        )
        return {
            **base_result,
            "backup_verified": self.backups.verify(backup_archive),
            "safe_snapshot_created": safe_snapshot is not None,
            "audit_event_hash": event.event_hash,
        }
