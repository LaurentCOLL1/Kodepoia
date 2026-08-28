from __future__ import annotations

import threading

import pytest

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.matchmaking import (
    InMemoryMatchmakingService,
    LobbyRole,
    MatchmakingAuthorizationError,
    MatchmakingCapacityError,
    MatchmakingPolicyError,
    MatchmakingStateError,
    PresenceState,
    ReservationStatus,
    TicketStatus,
)


class Clock:
    def __init__(self, value: int = 10_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def actor(account: str, session: str, *objects: str) -> AuthorityActorContext:
    return AuthorityActorContext(account, session, ("*",), tuple(objects))


def service(clock: Clock | None = None, **kwargs) -> tuple[InMemoryMatchmakingService, Clock]:
    clock = clock or Clock()
    return InMemoryMatchmakingService(clock_ms=clock, **kwargs), clock


def submit_pair(svc: InMemoryMatchmakingService, *, prefix: str = "p", criteria=None):
    criteria = criteria or {"mode": "duo", "region": "eu"}
    a = actor(f"acct-{prefix}a", f"sess-{prefix}a", f"ticket-{prefix}a")
    b = actor(f"acct-{prefix}b", f"sess-{prefix}b", f"ticket-{prefix}b")
    first = svc.submit_ticket(f"ticket-{prefix}a", a, criteria=criteria)
    second = svc.submit_ticket(f"ticket-{prefix}b", b, criteria=criteria)
    return first, second


def test_lobby_owner_member_lifecycle_and_duplicate_join_is_mutation_free():
    svc, _ = service()
    owner = actor("acct-owner", "sess-owner", "lobby-a")
    member = actor("acct-member", "sess-member", "lobby-a")

    created = svc.create_lobby("lobby-a", owner, max_members=3)
    assert created.revision == 1
    assert created.members[0].role is LobbyRole.OWNER

    joined = svc.join_lobby("lobby-a", member)
    assert joined.revision == 2
    assert joined.member("acct-member") is not None
    duplicate = svc.join_lobby("lobby-a", member)
    assert duplicate == joined
    assert duplicate.revision == 2

    left = svc.remove_member("lobby-a", "acct-member", member)
    assert left.revision == 3
    assert left.member("acct-member") is None


def test_lobby_object_authorization_and_role_authorization_are_separate():
    svc, _ = service()
    owner = actor("acct-owner", "sess-owner", "lobby-a")
    member_a = actor("acct-a", "sess-a", "lobby-a")
    member_b = actor("acct-b", "sess-b", "lobby-a")
    svc.create_lobby("lobby-a", owner)
    svc.join_lobby("lobby-a", member_a)
    svc.join_lobby("lobby-a", member_b)

    wrong_object = actor("acct-a", "sess-a", "lobby-b")
    with pytest.raises(MatchmakingAuthorizationError, match="forbidden"):
        svc.join_lobby("lobby-a", wrong_object)

    with pytest.raises(MatchmakingAuthorizationError, match="owner_required"):
        svc.remove_member("lobby-a", "acct-b", member_a)

    kicked = svc.remove_member("lobby-a", "acct-b", owner)
    assert kicked.member("acct-b") is None


def test_lobby_capacity_and_closed_lobby_fail_closed():
    svc, _ = service()
    owner = actor("acct-owner", "sess-owner", "lobby-a")
    member = actor("acct-member", "sess-member", "lobby-a")
    extra = actor("acct-extra", "sess-extra", "lobby-a")
    svc.create_lobby("lobby-a", owner, max_members=2)
    svc.join_lobby("lobby-a", member)
    with pytest.raises(MatchmakingCapacityError, match="lobby_capacity"):
        svc.join_lobby("lobby-a", extra)

    svc.close_lobby("lobby-a", owner)
    with pytest.raises(MatchmakingStateError, match="lobby_closed"):
        svc.join_lobby("lobby-a", extra)


def test_client_criteria_cannot_set_reserved_server_fields_recursively():
    svc, _ = service()
    who = actor("acct-a", "sess-a", "ticket-a")
    with pytest.raises(MatchmakingPolicyError, match="reserved field"):
        svc.submit_ticket("ticket-a", who, criteria={"nested": {"match_id": "forged"}})


def test_duplicate_ticket_is_idempotent_but_conflicting_rebind_is_rejected():
    svc, _ = service()
    who = actor("acct-a", "sess-a", "ticket-a")
    first = svc.submit_ticket("ticket-a", who, criteria={"mode": "duo"}, ttl_ms=2_000)
    duplicate = svc.submit_ticket("ticket-a", who, criteria={"mode": "duo"}, ttl_ms=2_000)
    assert duplicate == first
    assert len(svc.tickets()) == 1

    with pytest.raises(MatchmakingStateError, match="ticket_idempotency_conflict"):
        svc.submit_ticket("ticket-a", who, criteria={"mode": "squad"}, ttl_ms=2_000)


def test_queue_capacity_is_bounded():
    svc, _ = service(max_queued_tickets=1)
    svc.submit_ticket("ticket-a", actor("acct-a", "sess-a", "ticket-a"), criteria={"mode": "duo"})
    with pytest.raises(MatchmakingCapacityError, match="queue_capacity"):
        svc.submit_ticket("ticket-b", actor("acct-b", "sess-b", "ticket-b"), criteria={"mode": "duo"})


def test_matcher_is_deterministic_oldest_first_and_same_inputs_same_digest():
    svc_a, _ = service()
    svc_b, _ = service()
    for svc in (svc_a, svc_b):
        for suffix in ("c", "a", "b", "d"):
            ticket_id = f"ticket-{suffix}"
            svc.submit_ticket(
                ticket_id,
                actor(f"acct-{suffix}", f"sess-{suffix}", ticket_id),
                criteria={"mode": "duo", "region": "eu"},
            )

    matches_a = svc_a.run_matchmaking(group_size=2, reservation_ttl_ms=5_000)
    matches_b = svc_b.run_matchmaking(group_size=2, reservation_ttl_ms=5_000)
    assert [item.ticket_ids for item in matches_a] == [("ticket-c", "ticket-a"), ("ticket-b", "ticket-d")]
    assert [item.canonical() for item in matches_a] == [item.canonical() for item in matches_b]
    assert svc_a.state_digest() == svc_b.state_digest()


def test_incompatible_criteria_do_not_match():
    svc, _ = service()
    svc.submit_ticket("ticket-a", actor("acct-a", "sess-a", "ticket-a"), criteria={"mode": "duo", "region": "eu"})
    svc.submit_ticket("ticket-b", actor("acct-b", "sess-b", "ticket-b"), criteria={"mode": "duo", "region": "us"})
    assert svc.run_matchmaking() == ()
    assert {item.status for item in svc.tickets()} == {TicketStatus.QUEUED}


def test_matched_tickets_are_terminal_and_cannot_be_double_assigned():
    svc, _ = service()
    first, second = submit_pair(svc)
    reservation = svc.run_matchmaking()[0]
    assert reservation.ticket_ids == (first.ticket_id, second.ticket_id)
    assert svc.ticket(first.ticket_id).status is TicketStatus.MATCHED
    assert svc.ticket(second.ticket_id).status is TicketStatus.MATCHED
    assert svc.run_matchmaking() == ()
    with pytest.raises(MatchmakingStateError, match="ticket_terminal"):
        svc.cancel_ticket(first.ticket_id, actor(first.account_id, first.session_id, first.ticket_id))


def test_cancel_vs_match_race_has_one_authoritative_terminal_outcome():
    svc, _ = service()
    first, _ = submit_pair(svc, prefix="r")
    barrier = threading.Barrier(3)
    outcomes: list[str] = []

    def cancel():
        barrier.wait()
        try:
            outcomes.append("cancel:" + svc.cancel_ticket(
                first.ticket_id,
                actor(first.account_id, first.session_id, first.ticket_id),
            ).status.value)
        except MatchmakingStateError as exc:
            outcomes.append("cancel-error:" + str(exc))

    def match():
        barrier.wait()
        outcomes.append("match:" + str(len(svc.run_matchmaking())))

    t1 = threading.Thread(target=cancel)
    t2 = threading.Thread(target=match)
    t1.start()
    t2.start()
    barrier.wait()
    t1.join(timeout=2)
    t2.join(timeout=2)
    assert not t1.is_alive() and not t2.is_alive()

    terminal = svc.ticket(first.ticket_id).status
    assert terminal in {TicketStatus.CANCELLED, TicketStatus.MATCHED}
    if terminal is TicketStatus.CANCELLED:
        assert "cancel:cancelled" in outcomes
        assert "match:0" in outcomes
    else:
        assert "match:1" in outcomes
        assert "cancel-error:ticket_terminal" in outcomes


def test_ticket_and_reservation_expiry_use_server_clock():
    svc, clock = service()
    who = actor("acct-a", "sess-a", "ticket-a")
    svc.submit_ticket("ticket-a", who, criteria={"mode": "solo-wait"}, ttl_ms=500)
    clock.value += 500
    assert svc.ticket("ticket-a").status is TicketStatus.EXPIRED

    first, second = submit_pair(svc, prefix="x")
    reservation = svc.run_matchmaking(reservation_ttl_ms=1_000)[0]
    assert reservation.status is ReservationStatus.ACTIVE
    clock.value += 1_000
    assert svc.reservation(reservation.reservation_id).status is ReservationStatus.EXPIRED
    assert svc.ticket(first.ticket_id).status is TicketStatus.MATCHED
    assert svc.ticket(second.ticket_id).status is TicketStatus.MATCHED


def test_reservation_capacity_is_bounded():
    svc, _ = service(max_active_reservations=1)
    submit_pair(svc, prefix="a")
    submit_pair(svc, prefix="b")
    assert len(svc.run_matchmaking()) == 1
    with pytest.raises(MatchmakingCapacityError, match="reservation_capacity"):
        svc.run_matchmaking()


def test_presence_revision_is_authoritative_and_membership_is_validated():
    svc, _ = service()
    owner = actor("acct-a", "sess-a", "lobby-a")
    svc.create_lobby("lobby-a", owner)
    presence_actor = actor("acct-a", "sess-a", "acct-a")
    first = svc.update_presence(
        presence_actor,
        expected_revision=0,
        state=PresenceState.IN_LOBBY,
        lobby_id="lobby-a",
    )
    assert first.revision == 1
    with pytest.raises(MatchmakingStateError, match="stale_presence_revision"):
        svc.update_presence(presence_actor, expected_revision=0, state=PresenceState.ONLINE)

    stranger = actor("acct-b", "sess-b", "acct-b")
    with pytest.raises(MatchmakingAuthorizationError, match="lobby_membership_required"):
        svc.update_presence(
            stranger,
            expected_revision=0,
            state=PresenceState.IN_LOBBY,
            lobby_id="lobby-a",
        )


def test_match_presence_requires_active_reservation():
    svc, clock = service()
    first, _ = submit_pair(svc, prefix="m")
    reservation = svc.run_matchmaking(reservation_ttl_ms=500)[0]
    who = actor(first.account_id, first.session_id, first.account_id)
    presence = svc.update_presence(
        who,
        expected_revision=0,
        state=PresenceState.IN_MATCH,
        match_id=reservation.match_id,
    )
    assert presence.match_id == reservation.match_id

    clock.value += 500
    with pytest.raises(MatchmakingAuthorizationError, match="match_reservation_required"):
        svc.update_presence(
            who,
            expected_revision=1,
            state=PresenceState.IN_MATCH,
            match_id=reservation.match_id,
        )


def test_reconnect_grant_is_short_lived_actor_session_match_and_reservation_bound():
    svc, clock = service(max_reconnect_ttl_ms=2_000)
    first, _ = submit_pair(svc, prefix="q")
    reservation = svc.run_matchmaking(reservation_ttl_ms=3_000)[0]
    who = actor(first.account_id, first.session_id, reservation.reservation_id)
    grant = svc.issue_reconnect(reservation.reservation_id, who, ttl_ms=1_000)
    assert grant.match_id == reservation.match_id
    assert svc.validate_reconnect(grant.grant_id, who) == grant

    wrong_session = actor(first.account_id, "sess-other", reservation.reservation_id)
    with pytest.raises(MatchmakingAuthorizationError, match="reconnect_actor_mismatch"):
        svc.validate_reconnect(grant.grant_id, wrong_session)

    wrong_account = actor("acct-evil", "sess-evil", reservation.reservation_id)
    with pytest.raises(MatchmakingAuthorizationError, match="reconnect_actor_mismatch"):
        svc.validate_reconnect(grant.grant_id, wrong_account)

    clock.value += 1_000
    with pytest.raises(MatchmakingStateError, match="reconnect_expired"):
        svc.validate_reconnect(grant.grant_id, who)


def test_reconnect_never_outlives_reservation():
    svc, clock = service(max_reconnect_ttl_ms=10_000)
    first, _ = submit_pair(svc, prefix="z")
    reservation = svc.run_matchmaking(reservation_ttl_ms=500)[0]
    who = actor(first.account_id, first.session_id, reservation.reservation_id)
    grant = svc.issue_reconnect(reservation.reservation_id, who, ttl_ms=5_000)
    assert grant.expires_at_ms == reservation.expires_at_ms
    clock.value = reservation.expires_at_ms
    with pytest.raises(MatchmakingStateError):
        svc.validate_reconnect(grant.grant_id, who)
