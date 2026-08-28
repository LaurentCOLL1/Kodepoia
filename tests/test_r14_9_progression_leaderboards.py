from __future__ import annotations

import threading

import pytest

from kodepoia.backend import InMemoryProgressionService
from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.progression import (
    AchievementDefinition,
    AchievementThreshold,
    LeaderboardDefinition,
    LeaderboardOrder,
    LeaderboardPeriodKind,
    LeaderboardScorePolicy,
    LeaderboardTiePolicy,
    ProgressionAuthorizationError,
    ProgressionCapacityError,
    ProgressionPolicyError,
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


def admin() -> AuthorityActorContext:
    return AuthorityActorContext("ops", "sess-ops", ("*",), ("points", "ach", "board", "time-ms", "classic", "recurring", "fastest", "other", "missing", "tiny", "score-10"))


def actor(
    account_id: str,
    *permissions: str,
    objects: tuple[str, ...] | None = None,
) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id,
        f"sess-{account_id}",
        permissions or ("*",),
        objects or (account_id,),
    )


def service(**kwargs) -> tuple[InMemoryProgressionService, Clock]:
    clock = Clock()
    return InMemoryProgressionService(clock_ms=clock, **kwargs), clock


def register_stat(
    svc: InMemoryProgressionService,
    *,
    stat_id: str = "points",
    version: int = 1,
    aggregation: StatAggregation = StatAggregation.SUM,
    minimum: int = -1_000_000,
    maximum: int = 1_000_000,
) -> StatDefinition:
    definition = StatDefinition(stat_id, version, aggregation, minimum, maximum)
    return svc.register_stat_definition(admin(), definition)


def register_bundle(
    svc: InMemoryProgressionService,
    *,
    stat_id: str = "points",
    aggregation: StatAggregation = StatAggregation.SUM,
    achievement: bool = True,
    achievement_threshold: int = 10,
    achievement_mode: AchievementThreshold = AchievementThreshold.AT_LEAST,
    leaderboard_id: str = "board",
    order: LeaderboardOrder = LeaderboardOrder.HIGHER_BETTER,
    score_policy: LeaderboardScorePolicy = LeaderboardScorePolicy.KEEP_BEST,
    tie_policy: LeaderboardTiePolicy = LeaderboardTiePolicy.SHARED_RANK,
    period_kind: LeaderboardPeriodKind = LeaderboardPeriodKind.CLASSIC,
    starts_at_ms: int | None = None,
    period_ms: int | None = None,
) -> None:
    register_stat(svc, stat_id=stat_id, aggregation=aggregation)
    if achievement:
        svc.register_achievement_definition(
            admin(),
            AchievementDefinition(
                "ach",
                1,
                stat_id,
                1,
                achievement_threshold,
                achievement_mode,
            ),
        )
    svc.register_leaderboard_definition(
        admin(),
        LeaderboardDefinition(
            leaderboard_id,
            1,
            stat_id,
            1,
            order,
            score_policy,
            tie_policy,
            period_kind,
            starts_at_ms,
            period_ms,
        ),
    )


def apply(
    svc: InMemoryProgressionService,
    account_id: str,
    value: int,
    *,
    event_id: str,
    idem: str | None = None,
    stat_id: str = "points",
    metadata=None,
):
    return svc.apply_stat_event(
        actor(account_id),
        event_id=event_id,
        account_id=account_id,
        stat_id=stat_id,
        stat_version=1,
        value=value,
        idempotency_key=idem or event_id,
        metadata=metadata,
    )


def board_viewer(account_id: str = "viewer", *permissions: str) -> AuthorityActorContext:
    return actor(
        account_id,
        *(permissions or ("progression.read",)),
        objects=(account_id, "board"),
    )


def test_backend_package_exports_progression_service():
    svc, _ = service()
    assert isinstance(svc, InMemoryProgressionService)


def test_definition_version_is_immutable_and_activation_supports_rollback():
    svc, _ = service()
    v1 = register_stat(svc, version=1)
    assert svc.register_stat_definition(admin(), v1) is v1
    with pytest.raises(ProgressionStateError, match="definition_version_conflict"):
        svc.register_stat_definition(
            admin(), StatDefinition("points", 1, StatAggregation.MAX, -1_000_000, 1_000_000)
        )
    register_stat(svc, version=2)
    svc.activate_stat_definition(admin(), "points", 2)
    with pytest.raises(ProgressionStateError, match="inactive_stat_definition"):
        svc.apply_stat_event(
            actor("acct-a"),
            event_id="old-version",
            account_id="acct-a",
            stat_id="points",
            stat_version=1,
            value=1,
            idempotency_key="old-version",
        )
    svc.activate_stat_definition(admin(), "points", 1)
    assert apply(svc, "acct-a", 1, event_id="rolled-back").resulting_stat_value == 1


def test_definition_references_existing_stat_version():
    svc, _ = service()
    with pytest.raises(ProgressionStateError, match="stat_definition_not_found"):
        svc.register_achievement_definition(
            admin(), AchievementDefinition("ach", 1, "missing", 1, 10)
        )
    with pytest.raises(ProgressionStateError, match="stat_definition_not_found"):
        svc.register_leaderboard_definition(
            admin(), LeaderboardDefinition("board", 1, "missing", 1)
        )


def test_invalid_enum_contracts_fail_closed():
    with pytest.raises(ProgressionPolicyError, match="invalid_stat_aggregation"):
        StatDefinition("points", 1, "sum")  # type: ignore[arg-type]
    with pytest.raises(ProgressionPolicyError, match="invalid_threshold_mode"):
        AchievementDefinition("ach", 1, "points", 1, 10, "at_least")  # type: ignore[arg-type]
    with pytest.raises(ProgressionPolicyError, match="invalid_leaderboard_order"):
        LeaderboardDefinition("board", 1, "points", 1, order="higher_better")  # type: ignore[arg-type]


def test_invalid_server_clock_is_rejected_before_mutation():
    svc = InMemoryProgressionService(clock_ms=lambda: -1)
    register_stat(svc)
    before = svc.state_digest()
    with pytest.raises(ProgressionPolicyError, match="invalid_server_clock"):
        apply(svc, "acct-a", 1, event_id="clock")
    assert svc.state_digest() == before


def test_function_and_object_authorization_are_both_required():
    svc, _ = service()
    register_stat(svc)
    wrong_object = actor("acct-a", "progression.apply", objects=("acct-b",))
    with pytest.raises(ProgressionAuthorizationError, match="forbidden"):
        svc.apply_stat_event(
            wrong_object,
            event_id="wrong-object",
            account_id="acct-a",
            stat_id="points",
            stat_version=1,
            value=1,
            idempotency_key="wrong-object",
        )
    read_only = actor("acct-a", "progression.read")
    with pytest.raises(ProgressionAuthorizationError, match="forbidden"):
        svc.apply_stat_event(
            read_only,
            event_id="wrong-function",
            account_id="acct-a",
            stat_id="points",
            stat_version=1,
            value=1,
            idempotency_key="wrong-function",
        )


def test_direct_client_score_write_is_always_forbidden():
    svc, _ = service()
    with pytest.raises(ProgressionAuthorizationError, match="direct_client_score_write_forbidden"):
        svc.submit_client_score("board", "acct-a", 999999)


def test_idempotent_replay_is_mutation_free():
    svc, _ = service()
    register_bundle(svc)
    first = apply(svc, "acct-a", 10, event_id="event-1", idem="idem-1")
    before = svc.state_digest()
    replay = apply(svc, "acct-a", 10, event_id="event-1", idem="idem-1")
    assert replay.replayed is True
    assert replay.sequence == first.sequence
    assert svc.state_digest() == before
    assert len(svc.events()) == 1
    assert len(svc.unlocks()) == 1


def test_idempotency_rebind_and_event_id_rebind_fail_closed():
    svc, _ = service()
    register_stat(svc)
    apply(svc, "acct-a", 1, event_id="event-1", idem="idem")
    with pytest.raises(ProgressionStateError, match="idempotency_conflict"):
        apply(svc, "acct-a", 2, event_id="event-2", idem="idem")
    with pytest.raises(ProgressionStateError, match="event_id_conflict"):
        apply(svc, "acct-a", 2, event_id="event-1", idem="other-idem")
    assert len(svc.events()) == 1


def test_reserved_metadata_fields_are_rejected_recursively():
    svc, _ = service()
    register_stat(svc)
    before = svc.state_digest()
    with pytest.raises(ProgressionPolicyError, match="reserved_event_field"):
        apply(
            svc,
            "acct-a",
            1,
            event_id="forged",
            metadata={"nested": [{"server_time_ms": 999999999}]},
        )
    assert svc.state_digest() == before


def test_stat_bounds_fail_before_event_commit():
    svc, _ = service()
    register_stat(svc, minimum=0, maximum=5)
    before = svc.state_digest()
    with pytest.raises(ProgressionStateError, match="stat_bounds"):
        apply(svc, "acct-a", 6, event_id="too-large")
    assert svc.state_digest() == before
    assert svc.events() == ()


def test_achievement_unlock_is_terminal_and_idempotent():
    svc, _ = service()
    register_bundle(svc, achievement_threshold=10)
    first = apply(svc, "acct-a", 4, event_id="a1")
    assert first.unlocked_achievement_ids == ()
    second = apply(svc, "acct-a", 6, event_id="a2")
    assert second.unlocked_achievement_ids == ("ach",)
    unlock = svc.achievement_unlock(actor("acct-a", "progression.read"), "acct-a", "ach", 1)
    assert unlock is not None and unlock.unlocked_sequence == second.sequence
    third = apply(svc, "acct-a", 10, event_id="a3")
    assert third.unlocked_achievement_ids == ()
    assert len(svc.unlocks()) == 1


def test_at_most_achievement_works_with_authoritative_min_stat():
    svc, _ = service()
    register_bundle(
        svc,
        aggregation=StatAggregation.MIN,
        achievement_threshold=3,
        achievement_mode=AchievementThreshold.AT_MOST,
    )
    assert apply(svc, "acct-a", 8, event_id="m1").unlocked_achievement_ids == ()
    assert apply(svc, "acct-a", 3, event_id="m2").unlocked_achievement_ids == ("ach",)


def test_classic_keep_best_does_not_replace_better_score():
    svc, _ = service()
    register_bundle(svc, achievement=False, score_policy=LeaderboardScorePolicy.KEEP_BEST)
    apply(svc, "acct-a", 10, event_id="k1")
    apply(svc, "acct-a", -5, event_id="k2")
    snapshot = svc.ranking_snapshot(board_viewer(), "board", 1)
    assert [(e.account_id, e.score) for e in snapshot.entries] == [("acct-a", 10)]


def test_force_update_tracks_latest_authoritative_classic_stat():
    svc, _ = service()
    register_bundle(svc, achievement=False, score_policy=LeaderboardScorePolicy.FORCE_UPDATE)
    apply(svc, "acct-a", 10, event_id="f1")
    apply(svc, "acct-a", -5, event_id="f2")
    snapshot = svc.ranking_snapshot(board_viewer(), "board", 1)
    assert snapshot.entries[0].score == 5


def test_higher_better_shared_ties_are_deterministic():
    svc, _ = service()
    register_bundle(svc, achievement=False, tie_policy=LeaderboardTiePolicy.SHARED_RANK)
    apply(svc, "acct-b", 10, event_id="b")
    apply(svc, "acct-a", 10, event_id="a")
    apply(svc, "acct-c", 5, event_id="c")
    snapshot = svc.ranking_snapshot(board_viewer(), "board", 1)
    assert [(e.rank, e.account_id, e.score) for e in snapshot.entries] == [
        (1, "acct-a", 10),
        (1, "acct-b", 10),
        (3, "acct-c", 5),
    ]


def test_lower_better_ordinal_ranking_is_deterministic():
    svc, _ = service()
    register_bundle(
        svc,
        aggregation=StatAggregation.MIN,
        achievement=False,
        order=LeaderboardOrder.LOWER_BETTER,
        tie_policy=LeaderboardTiePolicy.ORDINAL,
    )
    apply(svc, "acct-b", 5, event_id="b")
    apply(svc, "acct-a", 5, event_id="a")
    apply(svc, "acct-c", 9, event_id="c")
    snapshot = svc.ranking_snapshot(board_viewer(), "board", 1)
    assert [(e.rank, e.account_id, e.score) for e in snapshot.entries] == [
        (1, "acct-a", 5),
        (2, "acct-b", 5),
        (3, "acct-c", 9),
    ]


def test_recurring_sum_leaderboard_resets_period_local_score_without_lifetime_bleed():
    svc, clock = service()
    register_bundle(
        svc,
        achievement=False,
        period_kind=LeaderboardPeriodKind.RECURRING,
        starts_at_ms=1_000,
        period_ms=100,
        score_policy=LeaderboardScorePolicy.FORCE_UPDATE,
    )
    apply(svc, "acct-a", 7, event_id="p0-1")
    clock.value = 1_050
    apply(svc, "acct-a", 3, event_id="p0-2")
    assert svc.ranking_snapshot(board_viewer(), "board", 1, period_index=0).entries[0].score == 10

    clock.value = 1_100
    result = apply(svc, "acct-a", 2, event_id="p1-1")
    assert result.resulting_stat_value == 12
    current = svc.ranking_snapshot(board_viewer(), "board", 1)
    assert current.period.index == 1
    assert current.entries[0].score == 2
    assert svc.ranking_snapshot(board_viewer(), "board", 1, period_index=0).entries[0].score == 10


def test_recurring_max_leaderboard_does_not_carry_previous_period_best():
    svc, clock = service()
    register_bundle(
        svc,
        aggregation=StatAggregation.MAX,
        achievement=False,
        period_kind=LeaderboardPeriodKind.RECURRING,
        starts_at_ms=1_000,
        period_ms=100,
    )
    apply(svc, "acct-a", 100, event_id="max-p0")
    clock.value = 1_100
    result = apply(svc, "acct-a", 50, event_id="max-p1")
    assert result.resulting_stat_value == 100
    assert svc.ranking_snapshot(board_viewer(), "board", 1).entries[0].score == 50


def test_recurring_period_boundary_and_future_period_query_are_server_clock_driven():
    svc, clock = service()
    register_bundle(
        svc,
        achievement=False,
        period_kind=LeaderboardPeriodKind.RECURRING,
        starts_at_ms=1_000,
        period_ms=100,
    )
    clock.value = 1_099
    apply(svc, "acct-a", 1, event_id="before-boundary")
    assert svc.ranking_snapshot(board_viewer(), "board", 1).period.index == 0
    with pytest.raises(ProgressionStateError, match="future_leaderboard_period"):
        svc.ranking_snapshot(board_viewer(), "board", 1, period_index=1)
    clock.value = 1_100
    assert svc.ranking_snapshot(board_viewer(), "board", 1).period.index == 1


def test_private_entries_are_filtered_without_leaking_rank_gaps():
    svc, _ = service()
    register_bundle(svc, achievement=False)
    apply(svc, "acct-a", 20, event_id="a")
    apply(svc, "acct-b", 10, event_id="b")
    svc.set_visibility(
        actor("acct-b", "progression.privacy"),
        leaderboard_id="board",
        version=1,
        visibility=ProgressionVisibility.PRIVATE,
    )
    public = svc.ranking_snapshot(board_viewer("acct-a"), "board", 1)
    assert [(e.rank, e.account_id) for e in public.entries] == [(1, "acct-a")]

    owner = svc.ranking_snapshot(board_viewer("acct-b"), "board", 1)
    assert [e.account_id for e in owner.entries] == ["acct-a", "acct-b"]

    privileged = svc.ranking_snapshot(
        board_viewer("moderator", "progression.read", "progression.read_private"),
        "board",
        1,
    )
    assert [e.account_id for e in privileged.entries] == ["acct-a", "acct-b"]


def test_invalid_visibility_contract_is_rejected():
    svc, _ = service()
    register_bundle(svc, achievement=False)
    with pytest.raises(ProgressionPolicyError, match="invalid_visibility"):
        svc.set_visibility(
            actor("acct-a", "progression.privacy"),
            leaderboard_id="board",
            version=1,
            visibility="private",  # type: ignore[arg-type]
        )


def test_event_account_and_definition_capacities_are_bounded():
    event_svc, _ = service(max_events=1)
    register_stat(event_svc)
    apply(event_svc, "acct-a", 1, event_id="one")
    before = event_svc.state_digest()
    with pytest.raises(ProgressionCapacityError, match="event_capacity"):
        apply(event_svc, "acct-a", 1, event_id="two")
    assert event_svc.state_digest() == before

    account_svc, _ = service(max_accounts=1)
    register_stat(account_svc)
    apply(account_svc, "acct-a", 1, event_id="a")
    before = account_svc.state_digest()
    with pytest.raises(ProgressionCapacityError, match="account_capacity"):
        apply(account_svc, "acct-b", 1, event_id="b")
    assert account_svc.state_digest() == before

    definition_svc, _ = service(max_definition_versions=1)
    register_stat(definition_svc)
    with pytest.raises(ProgressionCapacityError, match="definition_capacity"):
        definition_svc.register_stat_definition(
            admin(), StatDefinition("other", 1, StatAggregation.SUM)
        )


def test_leaderboard_entry_capacity_fails_before_progression_event_commit():
    svc, _ = service(max_entries_per_leaderboard_period=1)
    register_bundle(svc, achievement=False)
    apply(svc, "acct-a", 1, event_id="a")
    before = svc.state_digest()
    with pytest.raises(ProgressionCapacityError, match="leaderboard_entry_capacity"):
        apply(svc, "acct-b", 1, event_id="b")
    assert svc.state_digest() == before
    assert [event.account_id for event in svc.events()] == ["acct-a"]


def test_concurrent_duplicate_event_commits_once_and_replays_once():
    svc, _ = service()
    register_bundle(svc)
    barrier = threading.Barrier(3)
    results = []
    errors = []

    def writer() -> None:
        try:
            barrier.wait()
            results.append(apply(svc, "acct-a", 10, event_id="same", idem="same-idem"))
        except BaseException as exc:  # pragma: no cover - diagnostic capture
            errors.append(exc)

    threads = [threading.Thread(target=writer) for _ in range(2)]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len(results) == 2
    assert sorted(result.replayed for result in results) == [False, True]
    assert len(svc.events()) == 1
    assert len(svc.unlocks()) == 1


def test_equivalent_authoritative_runs_have_identical_digests_and_snapshots():
    def build():
        svc, clock = service()
        register_bundle(
            svc,
            achievement_threshold=5,
            period_kind=LeaderboardPeriodKind.RECURRING,
            starts_at_ms=1_000,
            period_ms=100,
            score_policy=LeaderboardScorePolicy.FORCE_UPDATE,
        )
        apply(svc, "acct-b", 4, event_id="b1")
        apply(svc, "acct-a", 5, event_id="a1")
        clock.value = 1_100
        apply(svc, "acct-a", 2, event_id="a2")
        snapshot = svc.ranking_snapshot(board_viewer(), "board", 1)
        return svc, snapshot

    left, left_snapshot = build()
    right, right_snapshot = build()
    assert left.definition_digest() == right.definition_digest()
    assert left.state_digest() == right.state_digest()
    assert left.trace_digest() == right.trace_digest()
    assert left_snapshot.digest() == right_snapshot.digest()
