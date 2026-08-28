from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.cloud_save import (
    CloudSaveAuthorizationError,
    CloudSavePolicyError,
    CloudSaveQuotaError,
    CloudSaveStateError,
    ConflictResolutionStrategy,
    InMemoryCloudSaveService,
    SaveConflictStatus,
    SaveRevisionOperation,
)


class Clock:
    def __init__(self, value: int = 800_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def actor(slot_id: str, *permissions: str) -> AuthorityActorContext:
    return AuthorityActorContext("acct-player", "sess-player", permissions or ("*",), (slot_id,))


def run(source_sha: str) -> dict:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise SystemExit("source SHA must be lowercase 40-character Git SHA")

    clock = Clock()
    svc = InMemoryCloudSaveService(
        clock_ms=clock,
        max_payload_bytes=1024,
        max_revisions_per_slot=12,
        max_retained_bytes_per_slot=8192,
        max_open_conflicts_per_slot=3,
    )
    slot = "slot-main"
    rw = actor(slot)
    reader = actor(slot, "cloud_save.read")

    initial = svc.upload(
        rw, slot, schema_id="save-v1", payload=b'{"chapter":1,"coins":10}',
        base_revision_id=None, idempotency_key="upload-1"
    )
    initial_revision = svc.revision(reader, initial.revision_id)
    immutable_revision_ok = initial_revision.payload == b'{"chapter":1,"coins":10}'

    state_before_replay = svc.state_digest()
    replay = svc.upload(
        rw, slot, schema_id="save-v1", payload=initial_revision.payload,
        base_revision_id=None, idempotency_key="upload-1"
    )
    idempotent_replay_ok = replay.replayed and svc.state_digest() == state_before_replay

    idempotency_rebind_ok = False
    try:
        svc.upload(
            rw, slot, schema_id="save-v1", payload=b"different",
            base_revision_id=None, idempotency_key="upload-1"
        )
    except CloudSaveStateError as exc:
        idempotency_rebind_ok = str(exc) == "idempotency_conflict"

    clock.value += 10
    server = svc.upload(
        rw, slot, schema_id="save-v1", payload=b'{"chapter":2,"coins":12}',
        base_revision_id=initial.revision_id, idempotency_key="upload-server"
    )
    clock.value += 10
    conflict_result = svc.upload(
        rw, slot, schema_id="save-v1", payload=b'{"chapter":2,"coins":15}',
        base_revision_id=initial.revision_id, idempotency_key="upload-client"
    )
    conflict = svc.conflict(reader, conflict_result.conflict_id)
    conflict_explicit_ok = (
        conflict_result.status == "conflict"
        and conflict.server_revision_id == server.revision_id
        and svc.slot(reader, slot).current_revision_id == server.revision_id
    )

    conflict_state = svc.state_digest()
    conflict_replay = svc.upload(
        rw, slot, schema_id="save-v1", payload=conflict.proposed_payload,
        base_revision_id=initial.revision_id, idempotency_key="upload-client"
    )
    conflict_replay_ok = (
        conflict_replay.replayed
        and conflict_replay.conflict_id == conflict.conflict_id
        and svc.state_digest() == conflict_state
    )

    clock.value += 10
    resolution = svc.resolve_conflict(
        actor(slot, "cloud_save.resolve"), conflict.conflict_id,
        strategy=ConflictResolutionStrategy.MERGE,
        merged_payload=b'{"chapter":2,"coins":15,"merged":true}'
    )
    merged = svc.revision(reader, resolution.resulting_revision_id)
    conflict_resolution_ok = (
        merged.operation is SaveRevisionOperation.CONFLICT_RESOLUTION
        and svc.conflict(reader, conflict.conflict_id).status is SaveConflictStatus.RESOLVED
    )

    double_resolve_ok = False
    try:
        svc.resolve_conflict(
            actor(slot, "cloud_save.resolve"), conflict.conflict_id,
            strategy=ConflictResolutionStrategy.KEEP_SERVER
        )
    except CloudSaveStateError as exc:
        double_resolve_ok = str(exc) == "conflict_terminal"

    clock.value += 10
    migrated = svc.migrate(
        actor(slot, "cloud_save.migrate"), slot,
        base_revision_id=merged.revision_id,
        target_schema_id="save-v2",
        payload=b'{"chapter":2,"coins":15,"schema":2}'
    )
    migration_ok = migrated.schema_id == "save-v2" and migrated.operation is SaveRevisionOperation.MIGRATION

    silent_schema_change_ok = False
    try:
        svc.upload(
            rw, slot, schema_id="save-v3", payload=b"bad",
            base_revision_id=migrated.revision_id, idempotency_key="bad-schema"
        )
    except CloudSaveStateError as exc:
        silent_schema_change_ok = str(exc) == "schema_migration_required"

    clock.value += 10
    rollback = svc.rollback(
        actor(slot, "cloud_save.rollback"), slot,
        target_revision_id=initial.revision_id
    )
    rollback_append_only_ok = (
        rollback.operation is SaveRevisionOperation.ROLLBACK
        and rollback.source_revision_id == initial.revision_id
        and rollback.revision_id != initial.revision_id
        and svc.revision(reader, initial.revision_id).payload == initial_revision.payload
    )

    wrong_object = AuthorityActorContext("acct-player", "sess-player", ("*",), ("slot-other",))
    object_authorization_ok = False
    try:
        svc.slot(wrong_object, slot)
    except CloudSaveAuthorizationError as exc:
        object_authorization_ok = str(exc) == "forbidden"

    function_authorization_ok = False
    try:
        svc.upload(
            actor(slot, "cloud_save.read"), slot, schema_id="save-v2", payload=b"forbidden",
            base_revision_id=rollback.revision_id, idempotency_key="forbidden"
        )
    except CloudSaveAuthorizationError as exc:
        function_authorization_ok = str(exc) == "forbidden"

    integrity_slot = "slot-integrity"
    integrity_guard_ok = False
    try:
        svc.upload(
            actor(integrity_slot), integrity_slot,
            schema_id="save-v1", payload=b"payload", base_revision_id=None,
            idempotency_key="integrity", expected_content_digest="0" * 64
        )
    except CloudSavePolicyError as exc:
        integrity_guard_ok = str(exc) == "content_digest_mismatch"

    tiny = InMemoryCloudSaveService(clock_ms=clock, max_payload_bytes=2)
    bounded_quota_ok = False
    try:
        tiny.upload(
            actor("slot-tiny"), "slot-tiny", schema_id="save-v1", payload=b"123",
            base_revision_id=None, idempotency_key="tiny"
        )
    except CloudSaveQuotaError as exc:
        bounded_quota_ok = str(exc) == "payload_quota"

    slot_snapshot = svc.slot(reader, slot)
    checks = {
        "immutable_revision": immutable_revision_ok,
        "idempotent_replay": idempotent_replay_ok,
        "idempotency_rebind_rejected": idempotency_rebind_ok,
        "explicit_conflict": conflict_explicit_ok,
        "conflict_replay": conflict_replay_ok,
        "deterministic_resolution": conflict_resolution_ok,
        "double_resolution_rejected": double_resolve_ok,
        "explicit_migration": migration_ok,
        "silent_schema_change_rejected": silent_schema_change_ok,
        "append_only_rollback": rollback_append_only_ok,
        "object_authorization": object_authorization_ok,
        "function_authorization": function_authorization_ok,
        "integrity_guard": integrity_guard_ok,
        "bounded_quota": bounded_quota_ok,
    }
    if not all(checks.values()):
        raise SystemExit(f"R14.8 acceptance checks failed: {[k for k, v in checks.items() if not v]}")

    return {
        "status": "pass",
        "source_sha": source_sha,
        "checks": checks,
        "state_digest": svc.state_digest(),
        "trace_digest": svc.trace_digest(),
        "slot_digest": slot_snapshot.digest(),
        "current_revision_digest": svc.revision(reader, slot_snapshot.current_revision_id).digest(),
        "resolved_conflict_digest": svc.conflict(reader, conflict.conflict_id).digest(),
        "revision_count": len(slot_snapshot.revision_ids),
        "retained_bytes": slot_snapshot.total_retained_bytes,
        "budgets": {
            "max_payload_bytes": svc.max_payload_bytes,
            "max_revisions_per_slot": svc.max_revisions_per_slot,
            "max_retained_bytes_per_slot": svc.max_retained_bytes_per_slot,
            "max_open_conflicts_per_slot": svc.max_open_conflicts_per_slot,
        },
        "external_reference_posture": [
            "RFC 9110 conditional request / lost-update prevention semantics as CAS reference only",
            "Google Play Games Saved Games explicit multi-device conflict handling reference",
            "OWASP API1:2023 object-level authorization",
        ],
        "provider_live_claim": False,
        "secrets_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = run(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
