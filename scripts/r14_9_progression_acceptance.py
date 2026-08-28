from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.progression import (
    AchievementDefinition,
    InMemoryProgressionService,
    LeaderboardDefinition,
    LeaderboardOrder,
    LeaderboardPeriodKind,
    LeaderboardScorePolicy,
    LeaderboardTiePolicy,
    ProgressionAuthorizationError,
    ProgressionCapacityError,
    ProgressionStateError,
    ProgressionVisibility,
    StatAggregation,
    StatDefinition,
)


class Clock:
    def __init__(self, value: int = 1_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def actor(account_id: str, *permissions: str, objects: tuple[str, ...] | None = None) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id,
        f"sess-{account_id}",
        permissions or ("*",),
        objects or (account_id,),
    )


def admin() -> AuthorityActorContext:
    return AuthorityActorContext("ops", "sess-ops", ("*",), ("*",))


def viewer(account_id: str = "viewer", *, private: bool = False) -> AuthorityActorContext:
    permissions = ("progression.read", "progression.read_private") if private else ("progression.read",)
    return actor(account_id, *permissions, objects=(account_id, "classic", "recurring", "fastest"))


def apply(
    svc: InMemoryProgressionService,
    account_id: str,
    stat_id: str,
    value: int,
    *,
    event_id: str,
    idempotency_key: str | None = None,
):
    return svc.apply_stat_event(
        actor(account_id),
        event_id=event_id,
        account_id=account_id,
        stat_id=stat_id,
        stat_version=1,
        value=value,
        idempotency_key=idempotency_key or event_id,
        metadata={"source": "authoritative-fixture"},
    )


def run(source_sha: str) -> dict:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise SystemExit("source SHA must be lowercase 40-character Git SHA")

    clock = Clock()
    svc = InMemoryProgressionService(
        clock_ms=clock,
        max_events=128,
        max_accounts=32,
        max_definition_versions=32,
        max_entries_per_leaderboard_period=32,
        max_metadata_bytes=1024,
    )

    points = StatDefinition("points", 1, StatAggregation.SUM, 0, 1_000_000)
    svc.register_stat_definition(admin(), points)
    svc.register_achievement_definition(
        admin(), AchievementDefinition("score-10", 1, "points", 1, 10)
    )
    svc.register_leaderboard_definition(
        admin(),
        LeaderboardDefinition(
            "classic",
            1,
            "points",
            1,
            LeaderboardOrder.HIGHER_BETTER,
            LeaderboardScorePolicy.KEEP_BEST,
            LeaderboardTiePolicy.SHARED_RANK,
        ),
    )
    svc.register_leaderboard_definition(
        admin(),
        LeaderboardDefinition(
            "recurring",
            1,
            "points",
            1,
            LeaderboardOrder.HIGHER_BETTER,
            LeaderboardScorePolicy.FORCE_UPDATE,
            LeaderboardTiePolicy.SHARED_RANK,
            LeaderboardPeriodKind.RECURRING,
            1_000,
            100,
        ),
    )
    svc.register_stat_definition(admin(), StatDefinition("time-ms", 1, StatAggregation.MIN, 0, 1_000_000))
    svc.register_leaderboard_definition(
        admin(),
        LeaderboardDefinition(
            "fastest",
            1,
            "time-ms",
            1,
            LeaderboardOrder.LOWER_BETTER,
            LeaderboardScorePolicy.KEEP_BEST,
            LeaderboardTiePolicy.ORDINAL,
        ),
    )

    immutable_definition_ok = False
    try:
        svc.register_stat_definition(admin(), StatDefinition("points", 1, StatAggregation.MAX, 0, 1_000_000))
    except ProgressionStateError as exc:
        immutable_definition_ok = str(exc) == "definition_version_conflict"

    first_b = apply(svc, "acct-b", "points", 10, event_id="points-b-1")
    first_a = apply(svc, "acct-a", "points", 10, event_id="points-a-1", idempotency_key="idem-a-1")
    authoritative_event_ok = (
        first_a.resulting_stat_value == 10
        and first_a.unlocked_achievement_ids == ("score-10",)
        and first_b.resulting_stat_value == 10
    )

    replay_state = svc.state_digest()
    replay = apply(svc, "acct-a", "points", 10, event_id="points-a-1", idempotency_key="idem-a-1")
    idempotent_replay_ok = replay.replayed and replay.sequence == first_a.sequence and svc.state_digest() == replay_state

    idempotency_rebind_ok = False
    try:
        apply(svc, "acct-a", "points", 1, event_id="points-a-rebind", idempotency_key="idem-a-1")
    except ProgressionStateError as exc:
        idempotency_rebind_ok = str(exc) == "idempotency_conflict"

    event_id_rebind_ok = False
    try:
        apply(svc, "acct-a", "points", 1, event_id="points-a-1", idempotency_key="other-idem")
    except ProgressionStateError as exc:
        event_id_rebind_ok = str(exc) == "event_id_conflict"

    direct_client_score_ok = False
    try:
        svc.submit_client_score("classic", "acct-a", 999_999)
    except ProgressionAuthorizationError as exc:
        direct_client_score_ok = str(exc) == "direct_client_score_write_forbidden"

    clock.value = 1_050
    second_a = apply(svc, "acct-a", "points", 1, event_id="points-a-2")
    unlock_idempotent_ok = second_a.unlocked_achievement_ids == () and len(svc.unlocks()) == 2

    classic_snapshot = svc.ranking_snapshot(viewer(), "classic", 1)
    higher_shared_tie_ok = [(entry.rank, entry.account_id, entry.score) for entry in classic_snapshot.entries] == [
        (1, "acct-a", 11),
        (2, "acct-b", 10),
    ]

    apply(svc, "acct-b", "time-ms", 40, event_id="time-b")
    apply(svc, "acct-a", "time-ms", 30, event_id="time-a")
    lower_snapshot = svc.ranking_snapshot(viewer(), "fastest", 1)
    lower_order_ok = [(entry.rank, entry.account_id, entry.score) for entry in lower_snapshot.entries] == [
        (1, "acct-a", 30),
        (2, "acct-b", 40),
    ]

    recurring_period0 = svc.ranking_snapshot(viewer(), "recurring", 1, period_index=0)
    period0_score = next(entry.score for entry in recurring_period0.entries if entry.account_id == "acct-a")
    clock.value = 1_100
    rollover = apply(svc, "acct-a", "points", 2, event_id="points-a-p1")
    recurring_period1 = svc.ranking_snapshot(viewer(), "recurring", 1)
    period1_score = next(entry.score for entry in recurring_period1.entries if entry.account_id == "acct-a")
    recurring_rollover_ok = (
        period0_score == 11
        and rollover.resulting_stat_value == 13
        and recurring_period1.period.index == 1
        and period1_score == 2
    )

    period_boundary_ok = False
    try:
        svc.ranking_snapshot(viewer(), "recurring", 1, period_index=2)
    except ProgressionStateError as exc:
        period_boundary_ok = str(exc) == "future_leaderboard_period"

    svc.set_visibility(
        actor("acct-b", "progression.privacy"),
        leaderboard_id="classic",
        version=1,
        visibility=ProgressionVisibility.PRIVATE,
    )
    public_after_privacy = svc.ranking_snapshot(viewer("acct-a"), "classic", 1)
    privileged_after_privacy = svc.ranking_snapshot(viewer("moderator", private=True), "classic", 1)
    privacy_filter_ok = (
        [entry.account_id for entry in public_after_privacy.entries] == ["acct-a"]
        and [entry.account_id for entry in privileged_after_privacy.entries] == ["acct-a", "acct-b"]
        and public_after_privacy.entries[0].rank == 1
    )

    object_authorization_ok = False
    wrong_object = actor("acct-a", "progression.apply", objects=("acct-other",))
    try:
        svc.apply_stat_event(
            wrong_object,
            event_id="forbidden-object",
            account_id="acct-a",
            stat_id="points",
            stat_version=1,
            value=1,
            idempotency_key="forbidden-object",
        )
    except ProgressionAuthorizationError as exc:
        object_authorization_ok = str(exc) == "forbidden"

    function_authorization_ok = False
    try:
        svc.apply_stat_event(
            actor("acct-a", "progression.read"),
            event_id="forbidden-function",
            account_id="acct-a",
            stat_id="points",
            stat_version=1,
            value=1,
            idempotency_key="forbidden-function",
        )
    except ProgressionAuthorizationError as exc:
        function_authorization_ok = str(exc) == "forbidden"

    tiny = InMemoryProgressionService(clock_ms=clock, max_events=1)
    tiny.register_stat_definition(admin(), StatDefinition("tiny", 1, StatAggregation.SUM))
    tiny.apply_stat_event(
        actor("tiny-a"), event_id="tiny-1", account_id="tiny-a", stat_id="tiny",
        stat_version=1, value=1, idempotency_key="tiny-1"
    )
    bounded_capacity_ok = False
    try:
        tiny.apply_stat_event(
            actor("tiny-a"), event_id="tiny-2", account_id="tiny-a", stat_id="tiny",
            stat_version=1, value=1, idempotency_key="tiny-2"
        )
    except ProgressionCapacityError as exc:
        bounded_capacity_ok = str(exc) == "event_capacity"

    checks = {
        "authoritative_event": authoritative_event_ok,
        "direct_client_score_rejected": direct_client_score_ok,
        "idempotent_replay": idempotent_replay_ok,
        "idempotency_rebind_rejected": idempotency_rebind_ok,
        "event_id_rebind_rejected": event_id_rebind_ok,
        "immutable_definition_version": immutable_definition_ok,
        "unlock_idempotent": unlock_idempotent_ok,
        "higher_order_deterministic": higher_shared_tie_ok,
        "lower_order_deterministic": lower_order_ok,
        "recurring_rollover_no_lifetime_bleed": recurring_rollover_ok,
        "period_boundary_server_clock": period_boundary_ok,
        "privacy_filter": privacy_filter_ok,
        "object_authorization": object_authorization_ok,
        "function_authorization": function_authorization_ok,
        "bounded_capacity": bounded_capacity_ok,
    }
    if not all(checks.values()):
        raise SystemExit(f"R14.9 acceptance checks failed: {[name for name, ok in checks.items() if not ok]}")

    return {
        "status": "pass",
        "source_sha": source_sha,
        "checks": checks,
        "definition_digest": svc.definition_digest(),
        "state_digest": svc.state_digest(),
        "trace_digest": svc.trace_digest(),
        "classic_snapshot_digest": privileged_after_privacy.digest(),
        "lower_snapshot_digest": lower_snapshot.digest(),
        "recurring_period0_snapshot_digest": recurring_period0.digest(),
        "recurring_period1_snapshot_digest": recurring_period1.digest(),
        "event_count": len(svc.events()),
        "unlock_count": len(svc.unlocks()),
        "budgets": {
            "max_events": svc.max_events,
            "max_accounts": svc.max_accounts,
            "max_definition_versions": svc.max_definition_versions,
            "max_entries_per_leaderboard_period": svc.max_entries_per_leaderboard_period,
            "max_metadata_bytes": svc.max_metadata_bytes,
        },
        "external_reference_posture": [
            "Steamworks onlytrustedwrites secure-backend leaderboard semantics as comparison evidence only",
            "Apple Game Center classic/recurring reset and score-order semantics as comparison evidence only",
            "Provider-specific publication is outside provider-neutral R14.9 core acceptance",
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
