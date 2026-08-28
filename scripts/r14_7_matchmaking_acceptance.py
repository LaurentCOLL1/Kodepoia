from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.contracts import canonical_sha256
from kodepoia.backend.matchmaking import (
    InMemoryMatchmakingService,
    MatchmakingAuthorizationError,
    MatchmakingCapacityError,
    MatchmakingPolicyError,
    MatchmakingStateError,
    PresenceState,
    ReservationStatus,
    TicketStatus,
)


class Clock:
    def __init__(self, value: int = 500_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def actor(account: str, session: str, *objects: str) -> AuthorityActorContext:
    return AuthorityActorContext(account, session, ("*",), tuple(objects))


def run(source_sha: str) -> dict:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise SystemExit("source SHA must be lowercase 40-character Git SHA")

    clock = Clock()
    svc = InMemoryMatchmakingService(
        clock_ms=clock,
        max_queued_tickets=8,
        max_active_reservations=3,
        max_ticket_ttl_ms=60_000,
        max_reservation_ttl_ms=20_000,
        max_reconnect_ttl_ms=5_000,
    )
    trace: list[dict] = []

    owner = actor("acct-owner", "sess-owner", "lobby-main")
    member = actor("acct-member", "sess-member", "lobby-main")
    lobby = svc.create_lobby("lobby-main", owner, max_members=4)
    joined = svc.join_lobby("lobby-main", member)
    duplicate_join = svc.join_lobby("lobby-main", member)
    lobby_lifecycle_ok = (
        lobby.revision == 1
        and joined.revision == 2
        and duplicate_join.revision == 2
        and len(joined.members) == 2
    )
    trace.extend([lobby.canonical(), joined.canonical(), duplicate_join.canonical()])

    object_auth_ok = False
    try:
        svc.join_lobby("lobby-main", actor("acct-evil", "sess-evil", "lobby-other"))
    except MatchmakingAuthorizationError as exc:
        object_auth_ok = str(exc) == "forbidden"

    reserved_fields_ok = False
    try:
        svc.submit_ticket(
            "ticket-reserved",
            actor("acct-reserved", "sess-reserved", "ticket-reserved"),
            criteria={"nested": {"reservation_id": "forged"}},
        )
    except MatchmakingPolicyError:
        reserved_fields_ok = True

    criteria = {"mode": "duo", "region": "eu"}
    ta = svc.submit_ticket("ticket-a", actor("acct-a", "sess-a", "ticket-a"), criteria=criteria, ttl_ms=10_000)
    tb = svc.submit_ticket("ticket-b", actor("acct-b", "sess-b", "ticket-b"), criteria=criteria, ttl_ms=10_000)
    duplicate_ticket = svc.submit_ticket(
        "ticket-a",
        actor("acct-a", "sess-a", "ticket-a"),
        criteria=criteria,
        ttl_ms=10_000,
    )
    duplicate_ticket_ok = duplicate_ticket == ta and len([t for t in svc.tickets() if t.ticket_id == "ticket-a"]) == 1

    tc = svc.submit_ticket(
        "ticket-c",
        actor("acct-c", "sess-c", "ticket-c"),
        criteria={"mode": "duo", "region": "us"},
        ttl_ms=10_000,
    )
    trace.extend([ta.canonical(), tb.canonical(), tc.canonical()])

    reservations = svc.run_matchmaking(group_size=2, reservation_ttl_ms=4_000)
    deterministic_match_ok = len(reservations) == 1 and reservations[0].ticket_ids == ("ticket-a", "ticket-b")
    incompatible_ok = svc.ticket("ticket-c").status is TicketStatus.QUEUED
    no_double_assignment_ok = svc.run_matchmaking(group_size=2, reservation_ttl_ms=4_000) == ()
    reservation = reservations[0]
    trace.append(reservation.canonical())

    stale_presence_ok = False
    presence_actor = actor("acct-a", "sess-a", "acct-a")
    presence = svc.update_presence(
        presence_actor,
        expected_revision=0,
        state=PresenceState.IN_MATCH,
        match_id=reservation.match_id,
    )
    try:
        svc.update_presence(presence_actor, expected_revision=0, state=PresenceState.ONLINE)
    except MatchmakingStateError as exc:
        stale_presence_ok = str(exc) == "stale_presence_revision"
    trace.append(presence.canonical())

    reconnect_actor = actor("acct-a", "sess-a", reservation.reservation_id)
    grant = svc.issue_reconnect(reservation.reservation_id, reconnect_actor, ttl_ms=1_000)
    reconnect_bound_ok = svc.validate_reconnect(grant.grant_id, reconnect_actor) == grant
    try:
        svc.validate_reconnect(
            grant.grant_id,
            actor("acct-a", "sess-forged", reservation.reservation_id),
        )
    except MatchmakingAuthorizationError:
        reconnect_bound_ok = reconnect_bound_ok and True
    else:
        reconnect_bound_ok = False
    trace.append(grant.canonical())

    clock.value += 1_000
    reconnect_expiry_ok = False
    try:
        svc.validate_reconnect(grant.grant_id, reconnect_actor)
    except MatchmakingStateError as exc:
        reconnect_expiry_ok = str(exc) == "reconnect_expired"

    clock.value = reservation.expires_at_ms
    reservation_expiry_ok = svc.reservation(reservation.reservation_id).status is ReservationStatus.EXPIRED
    try:
        svc.issue_reconnect(reservation.reservation_id, reconnect_actor, ttl_ms=500)
    except MatchmakingStateError:
        reservation_expiry_ok = reservation_expiry_ok and True
    else:
        reservation_expiry_ok = False

    cancel_actor = actor("acct-c", "sess-c", "ticket-c")
    cancelled = svc.cancel_ticket("ticket-c", cancel_actor)
    cancel_terminal_ok = cancelled.status is TicketStatus.CANCELLED
    trace.append(cancelled.canonical())

    capacity_clock = Clock(900_000)
    tiny = InMemoryMatchmakingService(clock_ms=capacity_clock, max_queued_tickets=1)
    tiny.submit_ticket(
        "ticket-cap-a",
        actor("acct-cap-a", "sess-cap-a", "ticket-cap-a"),
        criteria={"mode": "duo"},
    )
    capacity_ok = False
    try:
        tiny.submit_ticket(
            "ticket-cap-b",
            actor("acct-cap-b", "sess-cap-b", "ticket-cap-b"),
            criteria={"mode": "duo"},
        )
    except MatchmakingCapacityError as exc:
        capacity_ok = str(exc) == "queue_capacity"

    terminal_statuses = {ticket.ticket_id: ticket.status.value for ticket in svc.tickets()}
    checks = {
        "lobby_lifecycle": lobby_lifecycle_ok,
        "object_authorization": object_auth_ok,
        "duplicate_join": duplicate_join.revision == joined.revision,
        "reserved_fields": reserved_fields_ok,
        "duplicate_ticket": duplicate_ticket_ok,
        "deterministic_match": deterministic_match_ok,
        "incompatible_criteria": incompatible_ok,
        "no_double_assignment": no_double_assignment_ok,
        "cancel_terminal": cancel_terminal_ok,
        "reservation_expiry": reservation_expiry_ok,
        "stale_presence": stale_presence_ok,
        "reconnect_binding": reconnect_bound_ok,
        "reconnect_expiry": reconnect_expiry_ok,
        "bounded_capacity": capacity_ok,
    }
    if not all(checks.values()):
        failed = [name for name, ok in checks.items() if not ok]
        raise SystemExit(f"R14.7 acceptance checks failed: {failed}")

    return {
        "status": "pass",
        "source_sha": source_sha,
        "checks": checks,
        "state_digest": svc.state_digest(),
        "lobby_digest": svc.lobby("lobby-main").digest(),
        "reservation_digest": svc.reservation(reservation.reservation_id).digest(),
        "presence_digest": svc.presence("acct-a").digest() if svc.presence("acct-a") else None,
        "trace_digest": canonical_sha256({"trace": trace}),
        "terminal_ticket_statuses": terminal_statuses,
        "budgets": {
            "max_queued_tickets": svc.max_queued_tickets,
            "max_active_reservations": svc.max_active_reservations,
            "max_ticket_ttl_ms": svc.max_ticket_ttl_ms,
            "max_reservation_ttl_ms": svc.max_reservation_ttl_ms,
            "max_reconnect_ttl_ms": svc.max_reconnect_ttl_ms,
        },
        "external_reference_posture": [
            "Open Match provider-neutral ticket/pool/allocation separation",
            "Amazon GameLift FlexMatch explicit ticket lifecycle and player-session handoff concepts",
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
