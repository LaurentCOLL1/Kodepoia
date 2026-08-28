from __future__ import annotations

import threading

import pytest

from kodepoia.backend.authority import (
    AuthorityActorContext,
    AuthorityBackpressureError,
    AuthorityCommand,
    AuthorityCommandStatus,
    AuthorityLeaseRegistry,
    AuthorityPolicyError,
    AuthorityRejectReason,
    AuthorityResyncRequired,
    AuthorityStateError,
    AuthorityTransportEnvelope,
    AuthorityTransportKind,
    AuthoritativeCommandProcessor,
    InMemoryAuthorityStore,
    RealtimeAuthorityBuffer,
)
from kodepoia.backend.contracts import canonical_sha256


class Clock:
    def __init__(self, value: int = 1_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def increment_handler(current, payload):
    value = int(current.get("value", 0)) + int(payload["amount"])
    return {"value": value}, "counter.updated", {"value": value}


def exploding_handler(current, payload):
    raise RuntimeError("handler failed")


def actor(account="acct-a", session="sess-a", target="object-a", permission="counter.increment"):
    return AuthorityActorContext(account, session, (permission,), (target,))


def command(
    command_id="cmd-1",
    *,
    account="acct-a",
    session="sess-a",
    target="object-a",
    expected_revision=0,
    sequence=1,
    idempotency_key="idem-1",
    amount=1,
    command_type="counter.increment",
):
    return AuthorityCommand(
        command_id=command_id,
        domain_id="world",
        actor_id=account,
        session_id=session,
        command_type=command_type,
        target_id=target,
        expected_revision=expected_revision,
        sequence=sequence,
        idempotency_key=idempotency_key,
        payload={"amount": amount},
    )


def processor(clock=None, *, max_pending_commands=128):
    store = InMemoryAuthorityStore()
    clock = clock or Clock()
    proc = AuthoritativeCommandProcessor(store, clock_ms=clock, max_pending_commands=max_pending_commands)
    proc.register_handler("counter.increment", increment_handler)
    return proc, store


def test_client_cannot_set_reserved_authoritative_fields_recursively():
    with pytest.raises(AuthorityPolicyError, match="reserved field"):
        AuthorityCommand(
            command_id="cmd-bad",
            domain_id="world",
            actor_id="acct-a",
            session_id="sess-a",
            command_type="counter.increment",
            target_id="object-a",
            expected_revision=0,
            sequence=1,
            idempotency_key="idem-bad",
            payload={"nested": {"server_revision": 99}},
        )


def test_actor_forgery_rejected_without_state_sequence_or_event_change():
    proc, store = processor()
    outcome = proc.process(command(account="acct-other"), actor())
    assert outcome.status is AuthorityCommandStatus.REJECTED
    assert outcome.reason is AuthorityRejectReason.ACTOR_MISMATCH
    assert store.snapshot("world", "object-a").revision == 0
    assert store.last_session_sequence("world", "sess-a") == 0
    assert store.events() == ()


def test_session_mismatch_is_rejected():
    proc, store = processor()
    outcome = proc.process(command(session="sess-other"), actor())
    assert outcome.reason is AuthorityRejectReason.SESSION_MISMATCH
    assert store.snapshot("world", "object-a").revision == 0


def test_permission_and_object_authorization_are_separate():
    proc, _ = processor()
    forbidden_permission = actor(permission="counter.read")
    assert proc.process(command(), forbidden_permission).reason is AuthorityRejectReason.UNAUTHORIZED
    forbidden_object = actor(target="object-b")
    assert proc.process(command(), forbidden_object).reason is AuthorityRejectReason.OBJECT_FORBIDDEN


def test_unknown_command_is_rejected_after_authorization():
    proc, _ = processor()
    unknown_actor = actor(permission="counter.delete")
    outcome = proc.process(command(command_type="counter.delete"), unknown_actor)
    assert outcome.reason is AuthorityRejectReason.UNKNOWN_COMMAND


def test_applied_command_server_owns_revision_event_sequence_and_time():
    clock = Clock(12_345)
    proc, store = processor(clock)
    outcome = proc.process(command(), actor())
    assert outcome.status is AuthorityCommandStatus.APPLIED
    assert outcome.state is not None and outcome.state.revision == 1
    assert outcome.state.payload == {"value": 1}
    assert outcome.event is not None
    assert outcome.event.revision == outcome.state.revision
    assert outcome.event.event_sequence == 1
    assert outcome.event.server_time_ms == 12_345
    assert store.last_session_sequence("world", "sess-a") == 1


def test_stale_revision_is_rejected_and_does_not_consume_sequence():
    proc, store = processor()
    assert proc.process(command(), actor()).status is AuthorityCommandStatus.APPLIED
    stale = command(
        "cmd-2",
        expected_revision=0,
        sequence=2,
        idempotency_key="idem-2",
    )
    outcome = proc.process(stale, actor())
    assert outcome.reason is AuthorityRejectReason.STALE_REVISION
    assert store.last_session_sequence("world", "sess-a") == 1
    assert len(store.events()) == 1


def test_out_of_order_sequence_is_rejected_without_mutation():
    proc, store = processor()
    outcome = proc.process(command(sequence=2), actor())
    assert outcome.reason is AuthorityRejectReason.OUT_OF_ORDER
    assert store.snapshot("world", "object-a").revision == 0
    assert store.events() == ()


def test_duplicate_replay_returns_original_state_event_without_mutating_again():
    proc, store = processor()
    cmd = command()
    first = proc.process(cmd, actor())
    duplicate = proc.process(cmd, actor())
    assert first.status is AuthorityCommandStatus.APPLIED
    assert duplicate.status is AuthorityCommandStatus.DUPLICATE
    assert duplicate.duplicate_of == "cmd-1"
    assert duplicate.state == first.state
    assert duplicate.event == first.event
    assert store.snapshot("world", "object-a").payload == {"value": 1}
    assert len(store.events()) == 1


def test_idempotency_key_cannot_be_rebound_to_different_request_digest():
    proc, store = processor()
    assert proc.process(command(), actor()).status is AuthorityCommandStatus.APPLIED
    conflict = command(
        "cmd-2",
        expected_revision=1,
        sequence=2,
        idempotency_key="idem-1",
        amount=9,
    )
    outcome = proc.process(conflict, actor())
    assert outcome.reason is AuthorityRejectReason.IDEMPOTENCY_CONFLICT
    assert store.snapshot("world", "object-a").payload == {"value": 1}
    assert len(store.events()) == 1


def test_handler_failure_is_atomic():
    store = InMemoryAuthorityStore()
    proc = AuthoritativeCommandProcessor(store, clock_ms=Clock())
    proc.register_handler("counter.explode", exploding_handler)
    cmd = command(command_type="counter.explode")
    who = actor(permission="counter.explode")
    with pytest.raises(RuntimeError, match="handler failed"):
        proc.process(cmd, who)
    assert store.snapshot("world", "object-a").revision == 0
    assert store.last_session_sequence("world", "sess-a") == 0
    assert store.events() == ()


def test_deterministic_two_client_conflict_and_recovery():
    proc, store = processor()
    actor_a = actor(account="acct-a", session="sess-a")
    actor_b = actor(account="acct-b", session="sess-b")

    first = proc.process(command(), actor_a)
    assert first.status is AuthorityCommandStatus.APPLIED

    stale_b = command(
        "cmd-b1",
        account="acct-b",
        session="sess-b",
        expected_revision=0,
        sequence=1,
        idempotency_key="idem-b1",
        amount=10,
    )
    assert proc.process(stale_b, actor_b).reason is AuthorityRejectReason.STALE_REVISION
    assert store.last_session_sequence("world", "sess-b") == 0

    recovered_b = command(
        "cmd-b2",
        account="acct-b",
        session="sess-b",
        expected_revision=1,
        sequence=1,
        idempotency_key="idem-b2",
        amount=10,
    )
    recovered = proc.process(recovered_b, actor_b)
    assert recovered.status is AuthorityCommandStatus.APPLIED
    assert recovered.state is not None and recovered.state.revision == 2
    assert recovered.state.payload == {"value": 11}
    assert recovered.event is not None and recovered.event.event_sequence == 2


def test_simultaneous_clients_cannot_both_commit_same_revision():
    proc, store = processor()
    barrier = threading.Barrier(3)
    outcomes = []

    def run(cmd, who):
        barrier.wait()
        outcomes.append(proc.process(cmd, who))

    cmd_a = command()
    cmd_b = command(
        "cmd-b1",
        account="acct-b",
        session="sess-b",
        idempotency_key="idem-b1",
        amount=5,
    )
    thread_a = threading.Thread(target=run, args=(cmd_a, actor()))
    thread_b = threading.Thread(
        target=run,
        args=(cmd_b, actor(account="acct-b", session="sess-b")),
    )
    thread_a.start()
    thread_b.start()
    barrier.wait()
    thread_a.join(timeout=2)
    thread_b.join(timeout=2)
    assert not thread_a.is_alive() and not thread_b.is_alive()
    assert sorted(outcome.status.value for outcome in outcomes) == ["applied", "rejected"]
    assert {outcome.reason for outcome in outcomes if outcome.reason} == {AuthorityRejectReason.STALE_REVISION}
    assert store.snapshot("world", "object-a").revision == 1
    assert len(store.events()) == 1


def test_realtime_buffer_enforces_capacity_and_resume_cursor():
    proc, _ = processor()
    first = proc.process(command(), actor())
    second = proc.process(
        command("cmd-2", expected_revision=1, sequence=2, idempotency_key="idem-2"),
        actor(),
    )
    assert first.event is not None and second.event is not None

    buffer = RealtimeAuthorityBuffer(max_events=2, max_bytes=100_000)
    buffer.publish(first.event)
    buffer.publish(second.event)
    assert [event.event_sequence for event in buffer.resume(0)] == [1, 2]

    with pytest.raises(AuthorityBackpressureError):
        buffer.publish(
            type(second.event)(
                event_id="event-3",
                domain_id="world",
                target_id="object-a",
                command_id="cmd-3",
                revision=3,
                event_sequence=3,
                event_type="counter.updated",
                server_time_ms=2_000,
                payload={"value": 3},
            )
        )

    buffer.acknowledge(1)
    assert [event.event_sequence for event in buffer.resume(1)] == [2]
    with pytest.raises(AuthorityResyncRequired):
        buffer.resume(0)


def test_realtime_buffer_rejects_non_monotonic_event_sequence():
    proc, _ = processor()
    outcome = proc.process(command(), actor())
    assert outcome.event is not None
    buffer = RealtimeAuthorityBuffer()
    buffer.publish(outcome.event)
    with pytest.raises(AuthorityStateError, match="strictly increasing"):
        buffer.publish(outcome.event)


def test_server_issued_lease_expiry_and_revocation_use_server_clock():
    clock = Clock(5_000)
    leases = AuthorityLeaseRegistry(clock_ms=clock, max_ttl_ms=10_000)
    lease = leases.issue("sess-a", ttl_ms=2_000, resume_after_event_sequence=7)
    assert lease.issued_at_ms == 5_000
    assert lease.expires_at_ms == 7_000
    assert leases.validate(lease.lease_id, "sess-a") == lease

    clock.value = 7_000
    with pytest.raises(AuthorityStateError, match="lease_expired"):
        leases.validate(lease.lease_id, "sess-a")

    clock.value = 8_000
    lease2 = leases.issue("sess-a", ttl_ms=1_000, resume_after_event_sequence=8)
    leases.revoke(lease2.lease_id)
    with pytest.raises(AuthorityStateError, match="lease_expired"):
        leases.validate(lease2.lease_id, "sess-a")


def test_transport_envelope_is_semantic_not_protocol_control():
    digest = canonical_sha256({"command_id": "cmd-1"})
    envelope = AuthorityTransportEnvelope(
        request_id="req-1",
        transport=AuthorityTransportKind.REALTIME_STREAM,
        message_kind="command",
        payload_digest=digest,
        correlation_id="corr-1",
    )
    assert envelope.canonical() == {
        "request_id": "req-1",
        "transport": "realtime_stream",
        "message_kind": "command",
        "payload_digest": digest,
        "correlation_id": "corr-1",
    }


def test_command_payload_size_is_bounded():
    with pytest.raises(AuthorityPolicyError, match="exceeds"):
        AuthorityCommand(
            command_id="cmd-large",
            domain_id="world",
            actor_id="acct-a",
            session_id="sess-a",
            command_type="counter.increment",
            target_id="object-a",
            expected_revision=0,
            sequence=1,
            idempotency_key="idem-large",
            payload={"blob": "x" * 100},
            max_payload_bytes=16,
        )
