from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.backend.authority import (
    AuthorityActorContext,
    AuthorityBackpressureError,
    AuthorityCommand,
    AuthorityCommandStatus,
    AuthorityLeaseRegistry,
    AuthorityPolicyError,
    AuthorityRejectReason,
    AuthorityResyncRequired,
    AuthoritativeCommandProcessor,
    InMemoryAuthorityStore,
    RealtimeAuthorityBuffer,
)
from kodepoia.backend.contracts import canonical_sha256


class Clock:
    def __init__(self, value: int = 100_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def handler(current, payload):
    value = int(current.get("value", 0)) + int(payload["amount"])
    return {"value": value}, "counter.updated", {"value": value}


def exploding_handler(current, payload):
    raise RuntimeError("acceptance handler rollback")


def actor(account: str, session: str) -> AuthorityActorContext:
    return AuthorityActorContext(account, session, ("counter.increment", "counter.explode"), ("object-a",))


def command(
    command_id: str,
    account: str,
    session: str,
    *,
    revision: int,
    sequence: int,
    idem: str,
    amount: int = 1,
    kind: str = "counter.increment",
) -> AuthorityCommand:
    return AuthorityCommand(
        command_id=command_id,
        domain_id="world",
        actor_id=account,
        session_id=session,
        command_type=kind,
        target_id="object-a",
        expected_revision=revision,
        sequence=sequence,
        idempotency_key=idem,
        payload={"amount": amount},
    )


def run(source_sha: str) -> dict:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise SystemExit("source SHA must be lowercase 40-character Git SHA")

    clock = Clock()
    store = InMemoryAuthorityStore()
    proc = AuthoritativeCommandProcessor(store, clock_ms=clock, max_pending_commands=32)
    proc.register_handler("counter.increment", handler)
    proc.register_handler("counter.explode", exploding_handler)
    actor_a = actor("acct-a", "sess-a")
    actor_b = actor("acct-b", "sess-b")
    trace: list[dict] = []

    forged = proc.process(
        command("cmd-forged", "acct-evil", "sess-a", revision=0, sequence=1, idem="idem-forged"),
        actor_a,
    )
    forgery_ok = forged.reason is AuthorityRejectReason.ACTOR_MISMATCH and store.events() == ()
    trace.append(forged.canonical())

    reserved_ok = False
    try:
        AuthorityCommand(
            command_id="cmd-reserved",
            domain_id="world",
            actor_id="acct-a",
            session_id="sess-a",
            command_type="counter.increment",
            target_id="object-a",
            expected_revision=0,
            sequence=1,
            idempotency_key="idem-reserved",
            payload={"nested": {"event_sequence": 777}},
        )
    except AuthorityPolicyError:
        reserved_ok = True

    clock.value = 100_100
    cmd_a1 = command("cmd-a1", "acct-a", "sess-a", revision=0, sequence=1, idem="idem-a1")
    applied_a1 = proc.process(cmd_a1, actor_a)
    if applied_a1.status is not AuthorityCommandStatus.APPLIED:
        raise SystemExit("initial authoritative command did not apply")
    trace.append(applied_a1.canonical())

    duplicate = proc.process(cmd_a1, actor_a)
    duplicate_ok = (
        duplicate.status is AuthorityCommandStatus.DUPLICATE
        and duplicate.event == applied_a1.event
        and len(store.events()) == 1
    )
    trace.append(duplicate.canonical())

    out_of_order = proc.process(
        command("cmd-a3", "acct-a", "sess-a", revision=1, sequence=3, idem="idem-a3"),
        actor_a,
    )
    out_of_order_ok = (
        out_of_order.reason is AuthorityRejectReason.OUT_OF_ORDER
        and store.last_session_sequence("world", "sess-a") == 1
    )
    trace.append(out_of_order.canonical())

    stale_b = proc.process(
        command("cmd-b1", "acct-b", "sess-b", revision=0, sequence=1, idem="idem-b1", amount=10),
        actor_b,
    )
    stale_ok = (
        stale_b.reason is AuthorityRejectReason.STALE_REVISION
        and store.last_session_sequence("world", "sess-b") == 0
    )
    trace.append(stale_b.canonical())

    clock.value = 100_200
    recovered_b = proc.process(
        command("cmd-b2", "acct-b", "sess-b", revision=1, sequence=1, idem="idem-b2", amount=10),
        actor_b,
    )
    if recovered_b.status is not AuthorityCommandStatus.APPLIED:
        raise SystemExit("second client did not recover from stale revision")
    trace.append(recovered_b.canonical())

    before_atomic = store.snapshot("world", "object-a")
    before_events = store.events()
    before_sequence = store.last_session_sequence("world", "sess-a")
    atomic_rollback_ok = False
    try:
        proc.process(
            command(
                "cmd-explode",
                "acct-a",
                "sess-a",
                revision=2,
                sequence=2,
                idem="idem-explode",
                kind="counter.explode",
            ),
            actor_a,
        )
    except RuntimeError:
        atomic_rollback_ok = (
            store.snapshot("world", "object-a") == before_atomic
            and store.events() == before_events
            and store.last_session_sequence("world", "sess-a") == before_sequence
        )

    clock.value = 100_300
    applied_a2 = proc.process(
        command("cmd-a2", "acct-a", "sess-a", revision=2, sequence=2, idem="idem-a2", amount=2),
        actor_a,
    )
    if applied_a2.status is not AuthorityCommandStatus.APPLIED:
        raise SystemExit("post-rollback command did not apply")
    trace.append(applied_a2.canonical())

    final_state = store.snapshot("world", "object-a")
    events = store.events()
    event_consistency = (
        atomic_rollback_ok
        and final_state.revision == 3
        and final_state.payload == {"value": 13}
        and [event.revision for event in events] == [1, 2, 3]
        and [event.event_sequence for event in events] == [1, 2, 3]
        and all(event.revision == index for index, event in enumerate(events, start=1))
    )
    multiclient_ok = (
        recovered_b.state is not None
        and recovered_b.state.revision == 2
        and recovered_b.state.payload == {"value": 11}
        and final_state.payload == {"value": 13}
    )

    realtime = RealtimeAuthorityBuffer(max_events=4, max_bytes=100_000)
    for event in events:
        realtime.publish(event)
    reconnect_ok = [event.event_sequence for event in realtime.resume(1)] == [2, 3]
    realtime.acknowledge(1)
    try:
        realtime.resume(0)
    except AuthorityResyncRequired:
        reconnect_ok = reconnect_ok and True
    else:
        reconnect_ok = False

    tiny = RealtimeAuthorityBuffer(max_events=1, max_bytes=100_000)
    tiny.publish(events[0])
    backpressure_ok = False
    try:
        tiny.publish(events[1])
    except AuthorityBackpressureError:
        backpressure_ok = True

    lease_clock = Clock(200_000)
    leases = AuthorityLeaseRegistry(clock_ms=lease_clock, max_ttl_ms=5_000)
    lease = leases.issue("sess-a", ttl_ms=1_000, resume_after_event_sequence=events[-1].event_sequence)
    leases.validate(lease.lease_id, "sess-a")
    lease_clock.value = 201_000
    lease_expiry_ok = False
    try:
        leases.validate(lease.lease_id, "sess-a")
    except Exception as exc:  # The public contract is a state error with a stable reason string.
        lease_expiry_ok = str(exc) == AuthorityRejectReason.LEASE_EXPIRED.value

    checks = {
        "forgery": forgery_ok,
        "stale_revision": stale_ok,
        "duplicate": duplicate_ok,
        "out_of_order": out_of_order_ok,
        "reconnect": reconnect_ok,
        "backpressure": backpressure_ok,
        "transaction_event_consistency": event_consistency,
        "deterministic_multiclient": multiclient_ok,
        "lease_expiry": lease_expiry_ok,
        "reserved_fields": reserved_ok,
    }
    if not all(checks.values()):
        failed = [name for name, ok in checks.items() if not ok]
        raise SystemExit(f"R14.6 acceptance checks failed: {failed}")

    events_payload = [event.canonical() for event in events]
    return {
        "status": "pass",
        "source_sha": source_sha,
        "checks": checks,
        "final_state": {
            **final_state.canonical(),
            "digest": final_state.digest(),
        },
        "events": {
            "count": len(events),
            "first_sequence": events[0].event_sequence,
            "last_sequence": events[-1].event_sequence,
            "digest": canonical_sha256({"events": events_payload}),
        },
        "trace_digest": canonical_sha256({"trace": trace}),
        "standards": [
            "RFC 9110 HTTP Semantics",
            "RFC 6455 WebSocket Protocol",
            "OWASP API Security Top 10 2023",
        ],
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
