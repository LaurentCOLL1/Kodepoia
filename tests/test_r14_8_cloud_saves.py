from __future__ import annotations

import threading
from dataclasses import replace

import pytest

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
    def __init__(self, value: int = 100_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def actor(slot: str, *permissions: str) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id="acct-a",
        session_id="sess-a",
        permissions=permissions or ("*",),
        authorized_object_ids=(slot,),
    )


def other_actor(slot: str) -> AuthorityActorContext:
    return AuthorityActorContext("acct-b", "sess-b", ("*",), (slot,))


def service(**kwargs) -> tuple[InMemoryCloudSaveService, Clock]:
    clock = Clock()
    return InMemoryCloudSaveService(clock_ms=clock, **kwargs), clock


def first_upload(svc: InMemoryCloudSaveService, slot: str = "slot-a", payload: bytes = b"v1"):
    return svc.upload(
        actor(slot),
        slot,
        schema_id="save-v1",
        payload=payload,
        base_revision_id=None,
        idempotency_key="idem-1",
    )


def test_initial_upload_is_immutable_and_readable():
    svc, _ = service()
    result = first_upload(svc)
    assert result.status == "accepted"
    revision = svc.revision(actor("slot-a", "cloud_save.read"), result.revision_id)
    assert revision.payload == b"v1"
    assert revision.operation is SaveRevisionOperation.UPLOAD
    assert revision.previous_revision_id is None
    slot = svc.slot(actor("slot-a", "cloud_save.read"), "slot-a")
    assert slot.current_revision_id == result.revision_id
    assert slot.revision_ids == (result.revision_id,)


def test_idempotent_replay_is_mutation_free():
    svc, _ = service()
    first = first_upload(svc)
    digest = svc.state_digest()
    replay = svc.upload(
        actor("slot-a"),
        "slot-a",
        schema_id="save-v1",
        payload=b"v1",
        base_revision_id=None,
        idempotency_key="idem-1",
    )
    assert replay.replayed is True
    assert replay.revision_id == first.revision_id
    assert svc.state_digest() == digest


def test_idempotency_key_rebind_fails_closed():
    svc, _ = service()
    first_upload(svc)
    with pytest.raises(CloudSaveStateError, match="idempotency_conflict"):
        svc.upload(
            actor("slot-a"),
            "slot-a",
            schema_id="save-v1",
            payload=b"forged",
            base_revision_id=None,
            idempotency_key="idem-1",
        )


def test_stale_base_creates_explicit_conflict_without_overwrite():
    svc, _ = service()
    r1 = first_upload(svc).revision_id
    r2 = svc.upload(
        actor("slot-a"),
        "slot-a",
        schema_id="save-v1",
        payload=b"v2-server",
        base_revision_id=r1,
        idempotency_key="idem-2",
    ).revision_id
    conflict_result = svc.upload(
        actor("slot-a"),
        "slot-a",
        schema_id="save-v1",
        payload=b"v2-client",
        base_revision_id=r1,
        idempotency_key="idem-conflict",
    )
    assert conflict_result.status == "conflict"
    assert conflict_result.current_revision_id == r2
    slot = svc.slot(actor("slot-a", "cloud_save.read"), "slot-a")
    assert slot.current_revision_id == r2
    assert slot.revision_ids == (r1, r2)
    conflict = svc.conflict(actor("slot-a", "cloud_save.read"), conflict_result.conflict_id)
    assert conflict.server_revision_id == r2
    assert conflict.proposed_payload == b"v2-client"


def make_conflict(svc: InMemoryCloudSaveService):
    r1 = first_upload(svc).revision_id
    r2 = svc.upload(
        actor("slot-a"),
        "slot-a",
        schema_id="save-v1",
        payload=b"server",
        base_revision_id=r1,
        idempotency_key="idem-2",
    ).revision_id
    conflict = svc.upload(
        actor("slot-a"),
        "slot-a",
        schema_id="save-v1",
        payload=b"client",
        base_revision_id=r1,
        idempotency_key="idem-c",
    ).conflict_id
    return r1, r2, conflict


def test_keep_server_resolves_without_new_revision():
    svc, _ = service()
    _, r2, conflict_id = make_conflict(svc)
    resolution = svc.resolve_conflict(
        actor("slot-a", "cloud_save.resolve"),
        conflict_id,
        strategy=ConflictResolutionStrategy.KEEP_SERVER,
    )
    assert resolution.resulting_revision_id is None
    assert svc.slot(actor("slot-a", "cloud_save.read"), "slot-a").current_revision_id == r2
    assert svc.conflict(actor("slot-a", "cloud_save.read"), conflict_id).status is SaveConflictStatus.RESOLVED


def test_keep_client_appends_new_revision_and_preserves_server_revision():
    svc, _ = service()
    _, r2, conflict_id = make_conflict(svc)
    resolution = svc.resolve_conflict(
        actor("slot-a", "cloud_save.resolve"),
        conflict_id,
        strategy=ConflictResolutionStrategy.KEEP_CLIENT,
    )
    resulting = svc.revision(actor("slot-a", "cloud_save.read"), resolution.resulting_revision_id)
    assert resulting.payload == b"client"
    assert resulting.previous_revision_id == r2
    assert resulting.operation is SaveRevisionOperation.CONFLICT_RESOLUTION
    assert svc.revision(actor("slot-a", "cloud_save.read"), r2).payload == b"server"


def test_merge_resolution_requires_explicit_payload():
    svc, _ = service()
    _, _, conflict_id = make_conflict(svc)
    with pytest.raises(CloudSavePolicyError, match="merged_payload_required"):
        svc.resolve_conflict(
            actor("slot-a", "cloud_save.resolve"),
            conflict_id,
            strategy=ConflictResolutionStrategy.MERGE,
        )
    resolution = svc.resolve_conflict(
        actor("slot-a", "cloud_save.resolve"),
        conflict_id,
        strategy=ConflictResolutionStrategy.MERGE,
        merged_payload=b"merged",
    )
    assert svc.revision(actor("slot-a", "cloud_save.read"), resolution.resulting_revision_id).payload == b"merged"


def test_conflict_cannot_be_resolved_twice():
    svc, _ = service()
    _, _, conflict_id = make_conflict(svc)
    resolver = actor("slot-a", "cloud_save.resolve")
    svc.resolve_conflict(resolver, conflict_id, strategy=ConflictResolutionStrategy.KEEP_SERVER)
    with pytest.raises(CloudSaveStateError, match="conflict_terminal"):
        svc.resolve_conflict(resolver, conflict_id, strategy=ConflictResolutionStrategy.KEEP_SERVER)


def test_object_authorization_is_checked_for_slot_revision_conflict_and_write():
    svc, _ = service()
    first = first_upload(svc)
    wrong = AuthorityActorContext("acct-a", "sess-a", ("*",), ("slot-b",))
    with pytest.raises(CloudSaveAuthorizationError, match="forbidden"):
        svc.slot(wrong, "slot-a")
    with pytest.raises(CloudSaveAuthorizationError, match="forbidden"):
        svc.revision(wrong, first.revision_id)
    with pytest.raises(CloudSaveAuthorizationError, match="forbidden"):
        svc.upload(
            wrong,
            "slot-a",
            schema_id="save-v1",
            payload=b"x",
            base_revision_id=first.revision_id,
            idempotency_key="evil",
        )


def test_function_permission_is_separate_from_object_authorization():
    svc, _ = service()
    read_only = actor("slot-a", "cloud_save.read")
    with pytest.raises(CloudSaveAuthorizationError, match="forbidden"):
        svc.upload(
            read_only,
            "slot-a",
            schema_id="save-v1",
            payload=b"v1",
            base_revision_id=None,
            idempotency_key="idem",
        )


def test_rollback_is_append_only_and_copies_retained_revision():
    svc, _ = service()
    r1 = first_upload(svc).revision_id
    r2 = svc.upload(
        actor("slot-a"),
        "slot-a",
        schema_id="save-v1",
        payload=b"v2",
        base_revision_id=r1,
        idempotency_key="idem-2",
    ).revision_id
    rollback = svc.rollback(actor("slot-a", "cloud_save.rollback"), "slot-a", target_revision_id=r1)
    assert rollback.payload == b"v1"
    assert rollback.source_revision_id == r1
    assert rollback.previous_revision_id == r2
    assert rollback.operation is SaveRevisionOperation.ROLLBACK
    assert svc.revision(actor("slot-a", "cloud_save.read"), r1).payload == b"v1"
    assert svc.revision(actor("slot-a", "cloud_save.read"), r2).payload == b"v2"


def test_digest_mismatch_fails_before_mutation():
    svc, _ = service()
    with pytest.raises(CloudSavePolicyError, match="content_digest_mismatch"):
        svc.upload(
            actor("slot-a"),
            "slot-a",
            schema_id="save-v1",
            payload=b"v1",
            base_revision_id=None,
            idempotency_key="idem",
            expected_content_digest="0" * 64,
        )
    assert svc.slot(actor("slot-a", "cloud_save.read"), "slot-a").current_revision_id is None


def test_payload_revision_and_retained_byte_quotas_fail_closed():
    payload_svc, _ = service(max_payload_bytes=2)
    with pytest.raises(CloudSaveQuotaError, match="payload_quota"):
        first_upload(payload_svc, payload=b"123")

    revision_svc, _ = service(max_revisions_per_slot=1)
    r1 = first_upload(revision_svc).revision_id
    with pytest.raises(CloudSaveQuotaError, match="revision_quota"):
        revision_svc.upload(
            actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"v2",
            base_revision_id=r1, idempotency_key="idem-2"
        )

    bytes_svc, _ = service(max_retained_bytes_per_slot=3)
    r1 = first_upload(bytes_svc, payload=b"12").revision_id
    with pytest.raises(CloudSaveQuotaError, match="retained_bytes_quota"):
        bytes_svc.upload(
            actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"34",
            base_revision_id=r1, idempotency_key="idem-2"
        )


def test_open_conflict_quota_is_bounded():
    svc, _ = service(max_open_conflicts_per_slot=1)
    r1 = first_upload(svc).revision_id
    svc.upload(actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"server", base_revision_id=r1, idempotency_key="server")
    first = svc.upload(actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"client-a", base_revision_id=r1, idempotency_key="client-a")
    assert first.status == "conflict"
    with pytest.raises(CloudSaveQuotaError, match="conflict_quota"):
        svc.upload(actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"client-b", base_revision_id=r1, idempotency_key="client-b")


def test_schema_change_requires_explicit_migration_permission():
    svc, _ = service()
    r1 = first_upload(svc).revision_id
    with pytest.raises(CloudSaveStateError, match="schema_migration_required"):
        svc.upload(
            actor("slot-a"), "slot-a", schema_id="save-v2", payload=b"v2",
            base_revision_id=r1, idempotency_key="idem-v2"
        )
    migrated = svc.migrate(
        actor("slot-a", "cloud_save.migrate"),
        "slot-a",
        base_revision_id=r1,
        target_schema_id="save-v2",
        payload=b"v2",
    )
    assert migrated.schema_id == "save-v2"
    assert migrated.operation is SaveRevisionOperation.MIGRATION


def test_migration_uses_compare_and_swap_base_revision():
    svc, _ = service()
    r1 = first_upload(svc).revision_id
    r2 = svc.upload(actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"v2", base_revision_id=r1, idempotency_key="idem-2").revision_id
    with pytest.raises(CloudSaveStateError, match="stale_base_revision"):
        svc.migrate(actor("slot-a", "cloud_save.migrate"), "slot-a", base_revision_id=r1, target_schema_id="save-v2", payload=b"new")
    assert svc.slot(actor("slot-a", "cloud_save.read"), "slot-a").current_revision_id == r2


def test_revision_integrity_failure_is_detected_on_read():
    svc, _ = service()
    revision_id = first_upload(svc).revision_id
    original = svc._revisions[revision_id]
    svc._revisions[revision_id] = replace(original, payload=b"tampered")
    with pytest.raises(CloudSaveStateError, match="revision_integrity_failure"):
        svc.revision(actor("slot-a", "cloud_save.read"), revision_id)


def test_revision_from_other_slot_cannot_be_used_as_base_or_rollback_target():
    svc, _ = service()
    a = first_upload(svc, slot="slot-a").revision_id
    b = svc.upload(actor("slot-b"), "slot-b", schema_id="save-v1", payload=b"b", base_revision_id=None, idempotency_key="b1").revision_id
    with pytest.raises(CloudSaveStateError, match="unknown_base_revision"):
        svc.upload(actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"x", base_revision_id=b, idempotency_key="cross")
    with pytest.raises(CloudSaveStateError, match="revision_not_found"):
        svc.rollback(actor("slot-a", "cloud_save.rollback"), "slot-a", target_revision_id=b)
    assert svc.slot(actor("slot-a", "cloud_save.read"), "slot-a").current_revision_id == a


def test_conflict_idempotent_replay_does_not_duplicate_conflict():
    svc, _ = service()
    r1 = first_upload(svc).revision_id
    svc.upload(actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"server", base_revision_id=r1, idempotency_key="server")
    request = dict(schema_id="save-v1", payload=b"client", base_revision_id=r1, idempotency_key="conflict")
    first = svc.upload(actor("slot-a"), "slot-a", **request)
    digest = svc.state_digest()
    replay = svc.upload(actor("slot-a"), "slot-a", **request)
    assert replay.replayed is True
    assert replay.conflict_id == first.conflict_id
    assert svc.state_digest() == digest


def test_concurrent_same_base_has_one_accept_and_one_conflict():
    svc, _ = service()
    r1 = first_upload(svc).revision_id
    barrier = threading.Barrier(3)
    results = []

    def writer(name: str, payload: bytes):
        barrier.wait()
        results.append(
            svc.upload(
                actor("slot-a"),
                "slot-a",
                schema_id="save-v1",
                payload=payload,
                base_revision_id=r1,
                idempotency_key=name,
            )
        )

    t1 = threading.Thread(target=writer, args=("writer-a", b"a"))
    t2 = threading.Thread(target=writer, args=("writer-b", b"b"))
    t1.start(); t2.start(); barrier.wait(); t1.join(timeout=2); t2.join(timeout=2)
    assert not t1.is_alive() and not t2.is_alive()
    assert sorted(result.status for result in results) == ["accepted", "conflict"]
    slot = svc.slot(actor("slot-a", "cloud_save.read"), "slot-a")
    assert len(slot.revision_ids) == 2
    assert len(slot.open_conflict_ids) == 1


def test_same_scenario_has_deterministic_state_and_trace_digests():
    def scenario():
        svc, _ = service()
        r1 = first_upload(svc).revision_id
        svc.upload(actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"server", base_revision_id=r1, idempotency_key="server")
        conflict = svc.upload(actor("slot-a"), "slot-a", schema_id="save-v1", payload=b"client", base_revision_id=r1, idempotency_key="client")
        svc.resolve_conflict(actor("slot-a", "cloud_save.resolve"), conflict.conflict_id, strategy=ConflictResolutionStrategy.MERGE, merged_payload=b"merged")
        return svc.state_digest(), svc.trace_digest()

    assert scenario() == scenario()
