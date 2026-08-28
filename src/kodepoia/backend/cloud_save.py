from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Callable, Mapping

from .authority import AuthorityActorContext
from .contracts import canonical_sha256


class CloudSavePolicyError(ValueError):
    pass


class CloudSaveStateError(RuntimeError):
    pass


class CloudSaveAuthorizationError(PermissionError):
    pass


class CloudSaveQuotaError(CloudSaveStateError):
    pass


class SaveConflictStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"


class ConflictResolutionStrategy(StrEnum):
    KEEP_SERVER = "keep_server"
    KEEP_CLIENT = "keep_client"
    MERGE = "merge"


class SaveRevisionOperation(StrEnum):
    UPLOAD = "upload"
    CONFLICT_RESOLUTION = "conflict_resolution"
    ROLLBACK = "rollback"
    MIGRATION = "migration"


@dataclass(frozen=True, slots=True)
class SaveRevision:
    revision_id: str
    slot_id: str
    previous_revision_id: str | None
    source_revision_id: str | None
    schema_id: str
    content_digest: str
    payload: bytes
    created_at_ms: int
    operation: SaveRevisionOperation

    @property
    def payload_bytes(self) -> int:
        return len(self.payload)

    def canonical(self, *, include_payload: bool = False) -> dict:
        value = {
            "revision_id": self.revision_id,
            "slot_id": self.slot_id,
            "previous_revision_id": self.previous_revision_id,
            "source_revision_id": self.source_revision_id,
            "schema_id": self.schema_id,
            "content_digest": self.content_digest,
            "payload_bytes": self.payload_bytes,
            "created_at_ms": self.created_at_ms,
            "operation": self.operation.value,
        }
        if include_payload:
            value["payload_hex"] = self.payload.hex()
        return value

    def digest(self) -> str:
        return canonical_sha256(self.canonical(include_payload=True))


@dataclass(frozen=True, slots=True)
class SaveConflict:
    conflict_id: str
    slot_id: str
    base_revision_id: str
    server_revision_id: str
    proposed_schema_id: str
    proposed_content_digest: str
    proposed_payload: bytes
    created_at_ms: int
    status: SaveConflictStatus = SaveConflictStatus.OPEN
    resolution_id: str | None = None

    def canonical(self, *, include_payload: bool = False) -> dict:
        value = {
            "conflict_id": self.conflict_id,
            "slot_id": self.slot_id,
            "base_revision_id": self.base_revision_id,
            "server_revision_id": self.server_revision_id,
            "proposed_schema_id": self.proposed_schema_id,
            "proposed_content_digest": self.proposed_content_digest,
            "proposed_payload_bytes": len(self.proposed_payload),
            "created_at_ms": self.created_at_ms,
            "status": self.status.value,
            "resolution_id": self.resolution_id,
        }
        if include_payload:
            value["proposed_payload_hex"] = self.proposed_payload.hex()
        return value

    def digest(self) -> str:
        return canonical_sha256(self.canonical(include_payload=True))


@dataclass(frozen=True, slots=True)
class ConflictResolution:
    resolution_id: str
    conflict_id: str
    strategy: ConflictResolutionStrategy
    resulting_revision_id: str | None
    resolved_at_ms: int

    def canonical(self) -> dict:
        return {
            "resolution_id": self.resolution_id,
            "conflict_id": self.conflict_id,
            "strategy": self.strategy.value,
            "resulting_revision_id": self.resulting_revision_id,
            "resolved_at_ms": self.resolved_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class SaveSlotSnapshot:
    slot_id: str
    current_revision_id: str | None
    revision_ids: tuple[str, ...]
    open_conflict_ids: tuple[str, ...]
    total_retained_bytes: int

    def canonical(self) -> dict:
        return {
            "slot_id": self.slot_id,
            "current_revision_id": self.current_revision_id,
            "revision_ids": list(self.revision_ids),
            "open_conflict_ids": list(self.open_conflict_ids),
            "total_retained_bytes": self.total_retained_bytes,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class SaveUploadResult:
    status: str
    current_revision_id: str | None
    revision_id: str | None = None
    conflict_id: str | None = None
    replayed: bool = False

    def canonical(self) -> dict:
        return {
            "status": self.status,
            "current_revision_id": self.current_revision_id,
            "revision_id": self.revision_id,
            "conflict_id": self.conflict_id,
            "replayed": self.replayed,
        }


@dataclass(frozen=True, slots=True)
class _IdempotencyRecord:
    request_digest: str
    result: SaveUploadResult


class InMemoryCloudSaveService:
    def __init__(
        self,
        *,
        clock_ms: Callable[[], int],
        max_payload_bytes: int = 4 * 1024 * 1024,
        max_revisions_per_slot: int = 64,
        max_retained_bytes_per_slot: int = 64 * 1024 * 1024,
        max_open_conflicts_per_slot: int = 8,
    ) -> None:
        for name, value in (
            ("max_payload_bytes", max_payload_bytes),
            ("max_revisions_per_slot", max_revisions_per_slot),
            ("max_retained_bytes_per_slot", max_retained_bytes_per_slot),
            ("max_open_conflicts_per_slot", max_open_conflicts_per_slot),
        ):
            if value <= 0:
                raise CloudSavePolicyError(f"{name}_must_be_positive")
        self.clock_ms = clock_ms
        self.max_payload_bytes = max_payload_bytes
        self.max_revisions_per_slot = max_revisions_per_slot
        self.max_retained_bytes_per_slot = max_retained_bytes_per_slot
        self.max_open_conflicts_per_slot = max_open_conflicts_per_slot
        self._lock = threading.RLock()
        self._revisions: dict[str, SaveRevision] = {}
        self._slot_revisions: dict[str, list[str]] = {}
        self._current: dict[str, str] = {}
        self._conflicts: dict[str, SaveConflict] = {}
        self._slot_conflicts: dict[str, list[str]] = {}
        self._resolutions: dict[str, ConflictResolution] = {}
        self._idempotency: dict[tuple[str, str], _IdempotencyRecord] = {}
        self._trace: list[dict] = []
        self._revision_seq = 0
        self._conflict_seq = 0
        self._resolution_seq = 0

    @staticmethod
    def content_digest(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _validate_identifier(name: str, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 128:
            raise CloudSavePolicyError(f"invalid_{name}")
        if any(ord(ch) < 33 or ord(ch) > 126 for ch in value):
            raise CloudSavePolicyError(f"invalid_{name}")
        return value

    @staticmethod
    def _authorize(actor: AuthorityActorContext, permission: str, slot_id: str) -> None:
        if not actor.can(permission, slot_id):
            raise CloudSaveAuthorizationError("forbidden")

    def _validate_payload(self, payload: bytes, expected_content_digest: str | None) -> str:
        if not isinstance(payload, bytes):
            raise CloudSavePolicyError("payload_must_be_bytes")
        if len(payload) > self.max_payload_bytes:
            raise CloudSaveQuotaError("payload_quota")
        digest = self.content_digest(payload)
        if expected_content_digest is not None and expected_content_digest != digest:
            raise CloudSavePolicyError("content_digest_mismatch")
        return digest

    def _slot_total_bytes(self, slot_id: str) -> int:
        return sum(len(self._revisions[revision_id].payload) for revision_id in self._slot_revisions.get(slot_id, ()))

    def _check_append_capacity(self, slot_id: str, payload_bytes: int) -> None:
        revisions = self._slot_revisions.get(slot_id, ())
        if len(revisions) >= self.max_revisions_per_slot:
            raise CloudSaveQuotaError("revision_quota")
        if self._slot_total_bytes(slot_id) + payload_bytes > self.max_retained_bytes_per_slot:
            raise CloudSaveQuotaError("retained_bytes_quota")

    def _next_revision_id(self) -> str:
        self._revision_seq += 1
        return f"save-rev-{self._revision_seq:06d}"

    def _next_conflict_id(self) -> str:
        self._conflict_seq += 1
        return f"save-conflict-{self._conflict_seq:06d}"

    def _next_resolution_id(self) -> str:
        self._resolution_seq += 1
        return f"save-resolution-{self._resolution_seq:06d}"

    def _append_revision(
        self,
        *,
        slot_id: str,
        schema_id: str,
        payload: bytes,
        operation: SaveRevisionOperation,
        source_revision_id: str | None = None,
    ) -> SaveRevision:
        self._check_append_capacity(slot_id, len(payload))
        previous = self._current.get(slot_id)
        revision = SaveRevision(
            revision_id=self._next_revision_id(),
            slot_id=slot_id,
            previous_revision_id=previous,
            source_revision_id=source_revision_id,
            schema_id=schema_id,
            content_digest=self.content_digest(payload),
            payload=bytes(payload),
            created_at_ms=int(self.clock_ms()),
            operation=operation,
        )
        self._revisions[revision.revision_id] = revision
        self._slot_revisions.setdefault(slot_id, []).append(revision.revision_id)
        self._current[slot_id] = revision.revision_id
        self._trace.append({"event": "revision_appended", **revision.canonical()})
        return revision

    def upload(
        self,
        actor: AuthorityActorContext,
        slot_id: str,
        *,
        schema_id: str,
        payload: bytes,
        base_revision_id: str | None,
        idempotency_key: str,
        expected_content_digest: str | None = None,
    ) -> SaveUploadResult:
        slot_id = self._validate_identifier("slot_id", slot_id)
        schema_id = self._validate_identifier("schema_id", schema_id)
        idempotency_key = self._validate_identifier("idempotency_key", idempotency_key)
        self._authorize(actor, "cloud_save.write", slot_id)
        payload_digest = self._validate_payload(payload, expected_content_digest)
        request_digest = canonical_sha256(
            {
                "slot_id": slot_id,
                "schema_id": schema_id,
                "payload_digest": payload_digest,
                "base_revision_id": base_revision_id,
            }
        )
        with self._lock:
            idem_key = (slot_id, idempotency_key)
            existing_idem = self._idempotency.get(idem_key)
            if existing_idem is not None:
                if existing_idem.request_digest != request_digest:
                    raise CloudSaveStateError("idempotency_conflict")
                return replace(existing_idem.result, replayed=True)

            current = self._current.get(slot_id)
            if current is None:
                if base_revision_id is not None:
                    raise CloudSaveStateError("unknown_base_revision")
                revision = self._append_revision(
                    slot_id=slot_id,
                    schema_id=schema_id,
                    payload=payload,
                    operation=SaveRevisionOperation.UPLOAD,
                )
                result = SaveUploadResult("accepted", revision.revision_id, revision_id=revision.revision_id)
            else:
                if base_revision_id is None:
                    raise CloudSaveStateError("base_revision_required")
                base = self._revisions.get(base_revision_id)
                if base is None or base.slot_id != slot_id:
                    raise CloudSaveStateError("unknown_base_revision")
                current_revision = self._revisions[current]
                if schema_id != current_revision.schema_id:
                    raise CloudSaveStateError("schema_migration_required")
                if base_revision_id != current:
                    open_count = sum(
                        self._conflicts[cid].status is SaveConflictStatus.OPEN
                        for cid in self._slot_conflicts.get(slot_id, ())
                    )
                    if open_count >= self.max_open_conflicts_per_slot:
                        raise CloudSaveQuotaError("conflict_quota")
                    conflict = SaveConflict(
                        conflict_id=self._next_conflict_id(),
                        slot_id=slot_id,
                        base_revision_id=base_revision_id,
                        server_revision_id=current,
                        proposed_schema_id=schema_id,
                        proposed_content_digest=payload_digest,
                        proposed_payload=bytes(payload),
                        created_at_ms=int(self.clock_ms()),
                    )
                    self._conflicts[conflict.conflict_id] = conflict
                    self._slot_conflicts.setdefault(slot_id, []).append(conflict.conflict_id)
                    self._trace.append({"event": "conflict_opened", **conflict.canonical()})
                    result = SaveUploadResult("conflict", current, conflict_id=conflict.conflict_id)
                else:
                    revision = self._append_revision(
                        slot_id=slot_id,
                        schema_id=schema_id,
                        payload=payload,
                        operation=SaveRevisionOperation.UPLOAD,
                    )
                    result = SaveUploadResult("accepted", revision.revision_id, revision_id=revision.revision_id)
            self._idempotency[idem_key] = _IdempotencyRecord(request_digest, result)
            return result

    def migrate(
        self,
        actor: AuthorityActorContext,
        slot_id: str,
        *,
        base_revision_id: str,
        target_schema_id: str,
        payload: bytes,
        expected_content_digest: str | None = None,
    ) -> SaveRevision:
        slot_id = self._validate_identifier("slot_id", slot_id)
        target_schema_id = self._validate_identifier("schema_id", target_schema_id)
        self._authorize(actor, "cloud_save.migrate", slot_id)
        self._validate_payload(payload, expected_content_digest)
        with self._lock:
            current = self._current.get(slot_id)
            if current is None or base_revision_id != current:
                raise CloudSaveStateError("stale_base_revision")
            return self._append_revision(
                slot_id=slot_id,
                schema_id=target_schema_id,
                payload=payload,
                operation=SaveRevisionOperation.MIGRATION,
                source_revision_id=base_revision_id,
            )

    def resolve_conflict(
        self,
        actor: AuthorityActorContext,
        conflict_id: str,
        *,
        strategy: ConflictResolutionStrategy,
        merged_payload: bytes | None = None,
        merged_schema_id: str | None = None,
        expected_content_digest: str | None = None,
    ) -> ConflictResolution:
        with self._lock:
            conflict = self._conflicts.get(conflict_id)
            if conflict is None:
                raise CloudSaveStateError("conflict_not_found")
            self._authorize(actor, "cloud_save.resolve", conflict.slot_id)
            if conflict.status is not SaveConflictStatus.OPEN:
                raise CloudSaveStateError("conflict_terminal")
            current = self._current.get(conflict.slot_id)
            if current != conflict.server_revision_id:
                raise CloudSaveStateError("conflict_server_revision_changed")

            resulting_revision_id: str | None = None
            if strategy is ConflictResolutionStrategy.KEEP_SERVER:
                if merged_payload is not None or merged_schema_id is not None:
                    raise CloudSavePolicyError("unexpected_merged_payload")
            elif strategy is ConflictResolutionStrategy.KEEP_CLIENT:
                if merged_payload is not None or merged_schema_id is not None:
                    raise CloudSavePolicyError("unexpected_merged_payload")
                revision = self._append_revision(
                    slot_id=conflict.slot_id,
                    schema_id=conflict.proposed_schema_id,
                    payload=conflict.proposed_payload,
                    operation=SaveRevisionOperation.CONFLICT_RESOLUTION,
                    source_revision_id=conflict.base_revision_id,
                )
                resulting_revision_id = revision.revision_id
            elif strategy is ConflictResolutionStrategy.MERGE:
                if merged_payload is None:
                    raise CloudSavePolicyError("merged_payload_required")
                schema_id = merged_schema_id or self._revisions[current].schema_id
                if schema_id != self._revisions[current].schema_id:
                    raise CloudSaveStateError("schema_migration_required")
                self._validate_payload(merged_payload, expected_content_digest)
                revision = self._append_revision(
                    slot_id=conflict.slot_id,
                    schema_id=schema_id,
                    payload=merged_payload,
                    operation=SaveRevisionOperation.CONFLICT_RESOLUTION,
                    source_revision_id=conflict.base_revision_id,
                )
                resulting_revision_id = revision.revision_id
            else:
                raise CloudSavePolicyError("unsupported_resolution_strategy")

            resolution = ConflictResolution(
                resolution_id=self._next_resolution_id(),
                conflict_id=conflict_id,
                strategy=strategy,
                resulting_revision_id=resulting_revision_id,
                resolved_at_ms=int(self.clock_ms()),
            )
            self._resolutions[resolution.resolution_id] = resolution
            self._conflicts[conflict_id] = replace(
                conflict,
                status=SaveConflictStatus.RESOLVED,
                resolution_id=resolution.resolution_id,
            )
            self._trace.append({"event": "conflict_resolved", **resolution.canonical()})
            return resolution

    def rollback(
        self,
        actor: AuthorityActorContext,
        slot_id: str,
        *,
        target_revision_id: str,
    ) -> SaveRevision:
        slot_id = self._validate_identifier("slot_id", slot_id)
        self._authorize(actor, "cloud_save.rollback", slot_id)
        with self._lock:
            target = self._revisions.get(target_revision_id)
            if target is None or target.slot_id != slot_id:
                raise CloudSaveStateError("revision_not_found")
            return self._append_revision(
                slot_id=slot_id,
                schema_id=target.schema_id,
                payload=target.payload,
                operation=SaveRevisionOperation.ROLLBACK,
                source_revision_id=target_revision_id,
            )

    def slot(self, actor: AuthorityActorContext, slot_id: str) -> SaveSlotSnapshot:
        slot_id = self._validate_identifier("slot_id", slot_id)
        self._authorize(actor, "cloud_save.read", slot_id)
        with self._lock:
            return SaveSlotSnapshot(
                slot_id=slot_id,
                current_revision_id=self._current.get(slot_id),
                revision_ids=tuple(self._slot_revisions.get(slot_id, ())),
                open_conflict_ids=tuple(
                    cid
                    for cid in self._slot_conflicts.get(slot_id, ())
                    if self._conflicts[cid].status is SaveConflictStatus.OPEN
                ),
                total_retained_bytes=self._slot_total_bytes(slot_id),
            )

    def revision(self, actor: AuthorityActorContext, revision_id: str) -> SaveRevision:
        with self._lock:
            revision = self._revisions.get(revision_id)
            if revision is None:
                raise CloudSaveStateError("revision_not_found")
            self._authorize(actor, "cloud_save.read", revision.slot_id)
            if self.content_digest(revision.payload) != revision.content_digest:
                raise CloudSaveStateError("revision_integrity_failure")
            return revision

    def conflict(self, actor: AuthorityActorContext, conflict_id: str) -> SaveConflict:
        with self._lock:
            conflict = self._conflicts.get(conflict_id)
            if conflict is None:
                raise CloudSaveStateError("conflict_not_found")
            self._authorize(actor, "cloud_save.read", conflict.slot_id)
            return conflict

    def conflicts(self, actor: AuthorityActorContext, slot_id: str) -> tuple[SaveConflict, ...]:
        slot_id = self._validate_identifier("slot_id", slot_id)
        self._authorize(actor, "cloud_save.read", slot_id)
        with self._lock:
            return tuple(self._conflicts[cid] for cid in self._slot_conflicts.get(slot_id, ()))

    def canonical_state(self) -> Mapping[str, object]:
        with self._lock:
            return {
                "slots": {
                    slot_id: {
                        "current_revision_id": self._current.get(slot_id),
                        "revision_ids": list(revision_ids),
                        "conflict_ids": list(self._slot_conflicts.get(slot_id, ())),
                    }
                    for slot_id, revision_ids in sorted(self._slot_revisions.items())
                },
                "revisions": [
                    self._revisions[revision_id].canonical(include_payload=True)
                    for revision_id in sorted(self._revisions)
                ],
                "conflicts": [
                    self._conflicts[conflict_id].canonical(include_payload=True)
                    for conflict_id in sorted(self._conflicts)
                ],
                "resolutions": [
                    self._resolutions[resolution_id].canonical()
                    for resolution_id in sorted(self._resolutions)
                ],
            }

    def state_digest(self) -> str:
        return canonical_sha256(self.canonical_state())

    def trace_digest(self) -> str:
        with self._lock:
            return canonical_sha256({"trace": list(self._trace)})

    def trace(self) -> tuple[dict, ...]:
        with self._lock:
            return tuple(dict(item) for item in self._trace)
