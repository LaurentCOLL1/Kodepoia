from __future__ import annotations

import re
import threading
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Callable, Mapping

from .authority import AuthorityActorContext
from .contracts import canonical_json_bytes, canonical_sha256

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_RESERVED_EVENT_FIELDS = frozenset(
    {
        "achievement_id",
        "event_sequence",
        "leaderboard_id",
        "rank",
        "score",
        "server_time_ms",
        "unlocked",
    }
)


class ProgressionPolicyError(ValueError):
    pass


class ProgressionStateError(RuntimeError):
    pass


class ProgressionAuthorizationError(PermissionError):
    pass


class ProgressionCapacityError(ProgressionStateError):
    pass


class StatAggregation(StrEnum):
    SUM = "sum"
    MAX = "max"
    MIN = "min"


class AchievementThreshold(StrEnum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"


class LeaderboardOrder(StrEnum):
    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"


class LeaderboardScorePolicy(StrEnum):
    KEEP_BEST = "keep_best"
    FORCE_UPDATE = "force_update"


class LeaderboardTiePolicy(StrEnum):
    SHARED_RANK = "shared_rank"
    ORDINAL = "ordinal"


class LeaderboardPeriodKind(StrEnum):
    CLASSIC = "classic"
    RECURRING = "recurring"


class ProgressionVisibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ProgressionPolicyError(f"invalid_{field}")
    return value


def _positive_version(value: int, *, field: str = "version") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value > 2**31 - 1:
        raise ProgressionPolicyError(f"invalid_{field}")
    return value


def _int_value(value: int, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not -(2**63) <= value <= 2**63 - 1:
        raise ProgressionPolicyError(f"invalid_{field}")
    return value


def _server_now_ms(clock_ms: Callable[[], int]) -> int:
    value = clock_ms()
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**63 - 1:
        raise ProgressionPolicyError("invalid_server_clock")
    return value


def _metadata(value: Mapping[str, Any] | None, *, max_bytes: int) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ProgressionPolicyError("metadata_must_be_mapping")
    normalized = dict(value)

    def reject_reserved(item: Any, path: str = "metadata") -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                if not isinstance(key, str):
                    raise ProgressionPolicyError("metadata_keys_must_be_strings")
                if key in _RESERVED_EVENT_FIELDS:
                    raise ProgressionPolicyError(f"reserved_event_field:{path}.{key}")
                reject_reserved(nested, f"{path}.{key}")
        elif isinstance(item, (list, tuple)):
            for index, nested in enumerate(item):
                reject_reserved(nested, f"{path}[{index}]")

    reject_reserved(normalized)
    try:
        encoded = canonical_json_bytes(normalized)
    except (TypeError, ValueError) as exc:
        raise ProgressionPolicyError("metadata_must_be_canonical_json") from exc
    if len(encoded) > max_bytes:
        raise ProgressionPolicyError("metadata_too_large")
    return normalized


@dataclass(frozen=True, slots=True)
class StatDefinition:
    stat_id: str
    version: int
    aggregation: StatAggregation
    minimum: int = -(2**63)
    maximum: int = 2**63 - 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "stat_id", _stable_id(self.stat_id, field="stat_id"))
        _positive_version(self.version)
        if not isinstance(self.aggregation, StatAggregation):
            raise ProgressionPolicyError("invalid_stat_aggregation")
        _int_value(self.minimum, field="minimum")
        _int_value(self.maximum, field="maximum")
        if self.minimum > self.maximum:
            raise ProgressionPolicyError("invalid_stat_bounds")

    def canonical(self) -> dict[str, object]:
        return {
            "stat_id": self.stat_id,
            "version": self.version,
            "aggregation": self.aggregation.value,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class AchievementDefinition:
    achievement_id: str
    version: int
    stat_id: str
    stat_version: int
    threshold: int
    threshold_mode: AchievementThreshold = AchievementThreshold.AT_LEAST
    hidden: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "achievement_id", _stable_id(self.achievement_id, field="achievement_id"))
        object.__setattr__(self, "stat_id", _stable_id(self.stat_id, field="stat_id"))
        _positive_version(self.version)
        _positive_version(self.stat_version, field="stat_version")
        if not isinstance(self.threshold_mode, AchievementThreshold):
            raise ProgressionPolicyError("invalid_threshold_mode")
        _int_value(self.threshold, field="threshold")
        if not isinstance(self.hidden, bool):
            raise ProgressionPolicyError("invalid_hidden")

    def canonical(self) -> dict[str, object]:
        return {
            "achievement_id": self.achievement_id,
            "version": self.version,
            "stat_id": self.stat_id,
            "stat_version": self.stat_version,
            "threshold": self.threshold,
            "threshold_mode": self.threshold_mode.value,
            "hidden": self.hidden,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LeaderboardPeriod:
    leaderboard_id: str
    definition_version: int
    period_id: str
    index: int | None
    starts_at_ms: int | None
    ends_at_ms: int | None

    def canonical(self) -> dict[str, object]:
        return {
            "leaderboard_id": self.leaderboard_id,
            "definition_version": self.definition_version,
            "period_id": self.period_id,
            "index": self.index,
            "starts_at_ms": self.starts_at_ms,
            "ends_at_ms": self.ends_at_ms,
        }


@dataclass(frozen=True, slots=True)
class LeaderboardDefinition:
    leaderboard_id: str
    version: int
    stat_id: str
    stat_version: int
    order: LeaderboardOrder = LeaderboardOrder.HIGHER_BETTER
    score_policy: LeaderboardScorePolicy = LeaderboardScorePolicy.KEEP_BEST
    tie_policy: LeaderboardTiePolicy = LeaderboardTiePolicy.SHARED_RANK
    period_kind: LeaderboardPeriodKind = LeaderboardPeriodKind.CLASSIC
    starts_at_ms: int | None = None
    period_ms: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "leaderboard_id", _stable_id(self.leaderboard_id, field="leaderboard_id"))
        object.__setattr__(self, "stat_id", _stable_id(self.stat_id, field="stat_id"))
        _positive_version(self.version)
        _positive_version(self.stat_version, field="stat_version")
        if not isinstance(self.order, LeaderboardOrder):
            raise ProgressionPolicyError("invalid_leaderboard_order")
        if not isinstance(self.score_policy, LeaderboardScorePolicy):
            raise ProgressionPolicyError("invalid_score_policy")
        if not isinstance(self.tie_policy, LeaderboardTiePolicy):
            raise ProgressionPolicyError("invalid_tie_policy")
        if not isinstance(self.period_kind, LeaderboardPeriodKind):
            raise ProgressionPolicyError("invalid_period_kind")
        if self.period_kind is LeaderboardPeriodKind.CLASSIC:
            if self.starts_at_ms is not None or self.period_ms is not None:
                raise ProgressionPolicyError("classic_period_fields_forbidden")
        else:
            if (
                isinstance(self.starts_at_ms, bool)
                or not isinstance(self.starts_at_ms, int)
                or self.starts_at_ms < 0
            ):
                raise ProgressionPolicyError("recurring_start_required")
            if isinstance(self.period_ms, bool) or not isinstance(self.period_ms, int) or self.period_ms <= 0:
                raise ProgressionPolicyError("recurring_period_required")

    def canonical(self) -> dict[str, object]:
        return {
            "leaderboard_id": self.leaderboard_id,
            "version": self.version,
            "stat_id": self.stat_id,
            "stat_version": self.stat_version,
            "order": self.order.value,
            "score_policy": self.score_policy.value,
            "tie_policy": self.tie_policy.value,
            "period_kind": self.period_kind.value,
            "starts_at_ms": self.starts_at_ms,
            "period_ms": self.period_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())

    def period_for(self, now_ms: int) -> LeaderboardPeriod | None:
        if self.period_kind is LeaderboardPeriodKind.CLASSIC:
            return LeaderboardPeriod(
                self.leaderboard_id,
                self.version,
                "classic",
                None,
                None,
                None,
            )
        assert self.starts_at_ms is not None and self.period_ms is not None
        if now_ms < self.starts_at_ms:
            return None
        index = (now_ms - self.starts_at_ms) // self.period_ms
        start = self.starts_at_ms + index * self.period_ms
        return LeaderboardPeriod(
            self.leaderboard_id,
            self.version,
            f"period-{index:08d}",
            index,
            start,
            start + self.period_ms,
        )

    def period_at_index(self, index: int) -> LeaderboardPeriod:
        if self.period_kind is LeaderboardPeriodKind.CLASSIC:
            if index != 0:
                raise ProgressionStateError("classic_period_index")
            return self.period_for(0)  # type: ignore[return-value]
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise ProgressionPolicyError("invalid_period_index")
        assert self.starts_at_ms is not None and self.period_ms is not None
        start = self.starts_at_ms + index * self.period_ms
        return LeaderboardPeriod(
            self.leaderboard_id,
            self.version,
            f"period-{index:08d}",
            index,
            start,
            start + self.period_ms,
        )


@dataclass(frozen=True, slots=True)
class StatValue:
    account_id: str
    stat_id: str
    stat_version: int
    value: int
    updated_sequence: int
    updated_at_ms: int

    def canonical(self) -> dict[str, object]:
        return {
            "account_id": self.account_id,
            "stat_id": self.stat_id,
            "stat_version": self.stat_version,
            "value": self.value,
            "updated_sequence": self.updated_sequence,
            "updated_at_ms": self.updated_at_ms,
        }


@dataclass(frozen=True, slots=True)
class ProgressionEvent:
    event_id: str
    account_id: str
    stat_id: str
    stat_version: int
    input_value: int
    resulting_value: int
    sequence: int
    applied_at_ms: int
    metadata: Mapping[str, Any]

    def canonical(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "account_id": self.account_id,
            "stat_id": self.stat_id,
            "stat_version": self.stat_version,
            "input_value": self.input_value,
            "resulting_value": self.resulting_value,
            "sequence": self.sequence,
            "applied_at_ms": self.applied_at_ms,
            "metadata": dict(self.metadata),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class AchievementUnlock:
    account_id: str
    achievement_id: str
    definition_version: int
    unlocked_sequence: int
    unlocked_at_ms: int

    def canonical(self) -> dict[str, object]:
        return {
            "account_id": self.account_id,
            "achievement_id": self.achievement_id,
            "definition_version": self.definition_version,
            "unlocked_sequence": self.unlocked_sequence,
            "unlocked_at_ms": self.unlocked_at_ms,
        }


@dataclass(frozen=True, slots=True)
class AchievementProgressSnapshot:
    account_id: str
    achievement_id: str
    definition_version: int
    stat_value: int | None
    threshold: int
    threshold_mode: AchievementThreshold
    unlocked: bool

    def canonical(self) -> dict[str, object]:
        return {
            "account_id": self.account_id,
            "achievement_id": self.achievement_id,
            "definition_version": self.definition_version,
            "stat_value": self.stat_value,
            "threshold": self.threshold,
            "threshold_mode": self.threshold_mode.value,
            "unlocked": self.unlocked,
        }


@dataclass(frozen=True, slots=True)
class LeaderboardScore:
    leaderboard_id: str
    definition_version: int
    period_id: str
    account_id: str
    score: int
    achieved_sequence: int
    achieved_at_ms: int

    def canonical(self) -> dict[str, object]:
        return {
            "leaderboard_id": self.leaderboard_id,
            "definition_version": self.definition_version,
            "period_id": self.period_id,
            "account_id": self.account_id,
            "score": self.score,
            "achieved_sequence": self.achieved_sequence,
            "achieved_at_ms": self.achieved_at_ms,
        }


@dataclass(frozen=True, slots=True)
class RankedLeaderboardEntry:
    rank: int
    account_id: str
    score: int
    achieved_sequence: int
    visibility: ProgressionVisibility

    def canonical(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "account_id": self.account_id,
            "score": self.score,
            "achieved_sequence": self.achieved_sequence,
            "visibility": self.visibility.value,
        }


@dataclass(frozen=True, slots=True)
class LeaderboardSnapshot:
    snapshot_id: str
    leaderboard_id: str
    definition_version: int
    period: LeaderboardPeriod
    generated_at_ms: int
    entries: tuple[RankedLeaderboardEntry, ...]

    def canonical(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "leaderboard_id": self.leaderboard_id,
            "definition_version": self.definition_version,
            "period": self.period.canonical(),
            "generated_at_ms": self.generated_at_ms,
            "entries": [entry.canonical() for entry in self.entries],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ProgressionApplyResult:
    event_id: str
    sequence: int
    resulting_stat_value: int
    unlocked_achievement_ids: tuple[str, ...]
    updated_leaderboard_ids: tuple[str, ...]
    replayed: bool = False

    def canonical(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "resulting_stat_value": self.resulting_stat_value,
            "unlocked_achievement_ids": list(self.unlocked_achievement_ids),
            "updated_leaderboard_ids": list(self.updated_leaderboard_ids),
            "replayed": self.replayed,
        }


@dataclass(frozen=True, slots=True)
class _IdempotencyRecord:
    request_digest: str
    result: ProgressionApplyResult


@dataclass(frozen=True, slots=True)
class _EventRecord:
    payload_digest: str
    result: ProgressionApplyResult


class InMemoryProgressionService:
    def __init__(
        self,
        *,
        clock_ms: Callable[[], int],
        max_events: int = 100_000,
        max_accounts: int = 100_000,
        max_definition_versions: int = 4_096,
        max_entries_per_leaderboard_period: int = 100_000,
        max_metadata_bytes: int = 4_096,
    ) -> None:
        for name, value in (
            ("max_events", max_events),
            ("max_accounts", max_accounts),
            ("max_definition_versions", max_definition_versions),
            ("max_entries_per_leaderboard_period", max_entries_per_leaderboard_period),
            ("max_metadata_bytes", max_metadata_bytes),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ProgressionPolicyError(f"{name}_must_be_positive")
        self.clock_ms = clock_ms
        self.max_events = max_events
        self.max_accounts = max_accounts
        self.max_definition_versions = max_definition_versions
        self.max_entries_per_leaderboard_period = max_entries_per_leaderboard_period
        self.max_metadata_bytes = max_metadata_bytes
        self._lock = threading.RLock()
        self._stats: dict[tuple[str, int], StatDefinition] = {}
        self._achievements: dict[tuple[str, int], AchievementDefinition] = {}
        self._leaderboards: dict[tuple[str, int], LeaderboardDefinition] = {}
        self._active_stats: dict[str, int] = {}
        self._active_achievements: dict[str, int] = {}
        self._active_leaderboards: dict[str, int] = {}
        self._values: dict[tuple[str, str, int], StatValue] = {}
        self._events: dict[str, ProgressionEvent] = {}
        self._event_records: dict[str, _EventRecord] = {}
        self._idempotency: dict[tuple[str, str], _IdempotencyRecord] = {}
        self._unlocks: dict[tuple[str, str, int], AchievementUnlock] = {}
        self._scores: dict[tuple[str, int, str, str], LeaderboardScore] = {}
        self._visibility: dict[tuple[str, int, str], ProgressionVisibility] = {}
        self._accounts: set[str] = set()
        self._sequence = 0
        self._trace: list[dict[str, object]] = []

    @staticmethod
    def _authorize(actor: AuthorityActorContext, permission: str, target_id: str) -> None:
        if not actor.can(permission, target_id):
            raise ProgressionAuthorizationError("forbidden")

    @staticmethod
    def _can_read_private(actor: AuthorityActorContext) -> bool:
        return "*" in actor.permissions or "progression.read_private" in actor.permissions

    def _definition_count(self) -> int:
        return len(self._stats) + len(self._achievements) + len(self._leaderboards)

    def _check_definition_capacity(self, key: tuple[str, int], target: Mapping[tuple[str, int], object]) -> None:
        if key not in target and self._definition_count() >= self.max_definition_versions:
            raise ProgressionCapacityError("definition_capacity")

    def register_stat_definition(self, actor: AuthorityActorContext, definition: StatDefinition) -> StatDefinition:
        self._authorize(actor, "progression.define", definition.stat_id)
        key = (definition.stat_id, definition.version)
        with self._lock:
            self._check_definition_capacity(key, self._stats)
            existing = self._stats.get(key)
            if existing is not None:
                if existing != definition:
                    raise ProgressionStateError("definition_version_conflict")
                return existing
            self._stats[key] = definition
            self._active_stats.setdefault(definition.stat_id, definition.version)
            self._trace.append({"event": "stat_definition_registered", **definition.canonical()})
            return definition

    def register_achievement_definition(
        self, actor: AuthorityActorContext, definition: AchievementDefinition
    ) -> AchievementDefinition:
        self._authorize(actor, "progression.define", definition.achievement_id)
        key = (definition.achievement_id, definition.version)
        with self._lock:
            if (definition.stat_id, definition.stat_version) not in self._stats:
                raise ProgressionStateError("stat_definition_not_found")
            self._check_definition_capacity(key, self._achievements)
            existing = self._achievements.get(key)
            if existing is not None:
                if existing != definition:
                    raise ProgressionStateError("definition_version_conflict")
                return existing
            self._achievements[key] = definition
            self._active_achievements.setdefault(definition.achievement_id, definition.version)
            self._trace.append({"event": "achievement_definition_registered", **definition.canonical()})
            return definition

    def register_leaderboard_definition(
        self, actor: AuthorityActorContext, definition: LeaderboardDefinition
    ) -> LeaderboardDefinition:
        self._authorize(actor, "progression.define", definition.leaderboard_id)
        key = (definition.leaderboard_id, definition.version)
        with self._lock:
            if (definition.stat_id, definition.stat_version) not in self._stats:
                raise ProgressionStateError("stat_definition_not_found")
            self._check_definition_capacity(key, self._leaderboards)
            existing = self._leaderboards.get(key)
            if existing is not None:
                if existing != definition:
                    raise ProgressionStateError("definition_version_conflict")
                return existing
            self._leaderboards[key] = definition
            self._active_leaderboards.setdefault(definition.leaderboard_id, definition.version)
            self._trace.append({"event": "leaderboard_definition_registered", **definition.canonical()})
            return definition

    def _activate(
        self,
        actor: AuthorityActorContext,
        definition_id: str,
        version: int,
        definitions: Mapping[tuple[str, int], object],
        active: dict[str, int],
        event_name: str,
    ) -> None:
        definition_id = _stable_id(definition_id, field="definition_id")
        _positive_version(version)
        self._authorize(actor, "progression.define", definition_id)
        with self._lock:
            if (definition_id, version) not in definitions:
                raise ProgressionStateError("definition_not_found")
            if active.get(definition_id) == version:
                return
            active[definition_id] = version
            self._trace.append({"event": event_name, "definition_id": definition_id, "version": version})

    def activate_stat_definition(self, actor: AuthorityActorContext, stat_id: str, version: int) -> None:
        self._activate(actor, stat_id, version, self._stats, self._active_stats, "stat_definition_activated")

    def activate_achievement_definition(
        self, actor: AuthorityActorContext, achievement_id: str, version: int
    ) -> None:
        self._activate(
            actor,
            achievement_id,
            version,
            self._achievements,
            self._active_achievements,
            "achievement_definition_activated",
        )

    def activate_leaderboard_definition(
        self, actor: AuthorityActorContext, leaderboard_id: str, version: int
    ) -> None:
        self._activate(
            actor,
            leaderboard_id,
            version,
            self._leaderboards,
            self._active_leaderboards,
            "leaderboard_definition_activated",
        )

    def _active_achievement_definitions(self) -> tuple[AchievementDefinition, ...]:
        return tuple(
            self._achievements[(achievement_id, version)]
            for achievement_id, version in sorted(self._active_achievements.items())
        )

    def _active_leaderboard_definitions(self) -> tuple[LeaderboardDefinition, ...]:
        return tuple(
            self._leaderboards[(leaderboard_id, version)]
            for leaderboard_id, version in sorted(self._active_leaderboards.items())
        )

    @staticmethod
    def _aggregate(definition: StatDefinition, current: StatValue | None, input_value: int) -> int:
        if definition.aggregation is StatAggregation.SUM:
            result = (current.value if current is not None else 0) + input_value
        elif definition.aggregation is StatAggregation.MAX:
            result = input_value if current is None else max(current.value, input_value)
        elif definition.aggregation is StatAggregation.MIN:
            result = input_value if current is None else min(current.value, input_value)
        else:
            raise ProgressionPolicyError("unsupported_stat_aggregation")
        if result < definition.minimum or result > definition.maximum:
            raise ProgressionStateError("stat_bounds")
        return result

    @staticmethod
    def _better(definition: LeaderboardDefinition, candidate: int, previous: int) -> bool:
        if definition.order is LeaderboardOrder.HIGHER_BETTER:
            return candidate > previous
        return candidate < previous

    @staticmethod
    def _leaderboard_candidate(
        stat_definition: StatDefinition,
        leaderboard: LeaderboardDefinition,
        previous: LeaderboardScore | None,
        input_value: int,
        lifetime_value: int,
    ) -> int:
        if leaderboard.period_kind is LeaderboardPeriodKind.CLASSIC:
            candidate = lifetime_value
        elif previous is None:
            candidate = input_value
        elif stat_definition.aggregation is StatAggregation.SUM:
            candidate = previous.score + input_value
        elif stat_definition.aggregation is StatAggregation.MAX:
            candidate = max(previous.score, input_value)
        elif stat_definition.aggregation is StatAggregation.MIN:
            candidate = min(previous.score, input_value)
        else:
            raise ProgressionPolicyError("unsupported_stat_aggregation")
        if candidate < stat_definition.minimum or candidate > stat_definition.maximum:
            raise ProgressionStateError("leaderboard_stat_bounds")
        return candidate

    def _period_entry_count(self, leaderboard_id: str, version: int, period_id: str) -> int:
        return sum(
            key[0] == leaderboard_id and key[1] == version and key[2] == period_id
            for key in self._scores
        )

    def apply_stat_event(
        self,
        actor: AuthorityActorContext,
        *,
        event_id: str,
        account_id: str,
        stat_id: str,
        stat_version: int,
        value: int,
        idempotency_key: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProgressionApplyResult:
        event_id = _stable_id(event_id, field="event_id")
        account_id = _stable_id(account_id, field="account_id")
        stat_id = _stable_id(stat_id, field="stat_id")
        idempotency_key = _stable_id(idempotency_key, field="idempotency_key")
        _positive_version(stat_version, field="stat_version")
        value = _int_value(value, field="value")
        normalized_metadata = _metadata(metadata, max_bytes=self.max_metadata_bytes)
        self._authorize(actor, "progression.apply", account_id)
        event_payload = {
            "account_id": account_id,
            "stat_id": stat_id,
            "stat_version": stat_version,
            "value": value,
            "metadata": normalized_metadata,
        }
        payload_digest = canonical_sha256(event_payload)
        request_digest = canonical_sha256({"event_id": event_id, **event_payload})

        with self._lock:
            existing_event = self._event_records.get(event_id)
            if existing_event is not None:
                if existing_event.payload_digest != payload_digest:
                    raise ProgressionStateError("event_id_conflict")
                return replace(existing_event.result, replayed=True)
            idem_key = (account_id, idempotency_key)
            existing_idem = self._idempotency.get(idem_key)
            if existing_idem is not None:
                if existing_idem.request_digest != request_digest:
                    raise ProgressionStateError("idempotency_conflict")
                return replace(existing_idem.result, replayed=True)

            definition = self._stats.get((stat_id, stat_version))
            if definition is None:
                raise ProgressionStateError("stat_definition_not_found")
            if self._active_stats.get(stat_id) != stat_version:
                raise ProgressionStateError("inactive_stat_definition")
            if len(self._events) >= self.max_events:
                raise ProgressionCapacityError("event_capacity")
            if account_id not in self._accounts and len(self._accounts) >= self.max_accounts:
                raise ProgressionCapacityError("account_capacity")

            now_ms = _server_now_ms(self.clock_ms)
            value_key = (account_id, stat_id, stat_version)
            current = self._values.get(value_key)
            resulting = self._aggregate(definition, current, value)

            affected_leaderboards: list[tuple[LeaderboardDefinition, LeaderboardPeriod]] = []
            for leaderboard in self._active_leaderboard_definitions():
                if leaderboard.stat_id != stat_id or leaderboard.stat_version != stat_version:
                    continue
                period = leaderboard.period_for(now_ms)
                if period is None:
                    continue
                score_key = (leaderboard.leaderboard_id, leaderboard.version, period.period_id, account_id)
                if score_key not in self._scores:
                    if (
                        self._period_entry_count(leaderboard.leaderboard_id, leaderboard.version, period.period_id)
                        >= self.max_entries_per_leaderboard_period
                    ):
                        raise ProgressionCapacityError("leaderboard_entry_capacity")
                affected_leaderboards.append((leaderboard, period))

            self._sequence += 1
            sequence = self._sequence
            stat_value = StatValue(account_id, stat_id, stat_version, resulting, sequence, now_ms)
            event = ProgressionEvent(
                event_id,
                account_id,
                stat_id,
                stat_version,
                value,
                resulting,
                sequence,
                now_ms,
                normalized_metadata,
            )
            self._values[value_key] = stat_value
            self._events[event_id] = event
            self._accounts.add(account_id)

            unlocked: list[str] = []
            for achievement in self._active_achievement_definitions():
                if achievement.stat_id != stat_id or achievement.stat_version != stat_version:
                    continue
                meets = (
                    resulting >= achievement.threshold
                    if achievement.threshold_mode is AchievementThreshold.AT_LEAST
                    else resulting <= achievement.threshold
                )
                unlock_key = (account_id, achievement.achievement_id, achievement.version)
                if meets and unlock_key not in self._unlocks:
                    unlock = AchievementUnlock(
                        account_id,
                        achievement.achievement_id,
                        achievement.version,
                        sequence,
                        now_ms,
                    )
                    self._unlocks[unlock_key] = unlock
                    unlocked.append(achievement.achievement_id)
                    self._trace.append({"event": "achievement_unlocked", **unlock.canonical()})

            updated_leaderboards: list[str] = []
            for leaderboard, period in affected_leaderboards:
                score_key = (leaderboard.leaderboard_id, leaderboard.version, period.period_id, account_id)
                previous = self._scores.get(score_key)
                candidate = self._leaderboard_candidate(
                    definition, leaderboard, previous, value, resulting
                )
                should_update = previous is None
                if previous is not None:
                    should_update = (
                        leaderboard.score_policy is LeaderboardScorePolicy.FORCE_UPDATE
                        or self._better(leaderboard, candidate, previous.score)
                    )
                if should_update:
                    score = LeaderboardScore(
                        leaderboard.leaderboard_id,
                        leaderboard.version,
                        period.period_id,
                        account_id,
                        candidate,
                        sequence,
                        now_ms,
                    )
                    self._scores[score_key] = score
                    updated_leaderboards.append(leaderboard.leaderboard_id)
                    self._trace.append({"event": "leaderboard_score_updated", **score.canonical()})

            result = ProgressionApplyResult(
                event_id,
                sequence,
                resulting,
                tuple(unlocked),
                tuple(updated_leaderboards),
            )
            self._event_records[event_id] = _EventRecord(payload_digest, result)
            self._idempotency[idem_key] = _IdempotencyRecord(request_digest, result)
            self._trace.append({"event": "progression_event_applied", **event.canonical()})
            return result

    def submit_client_score(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise ProgressionAuthorizationError("direct_client_score_write_forbidden")

    def set_visibility(
        self,
        actor: AuthorityActorContext,
        *,
        leaderboard_id: str,
        version: int,
        visibility: ProgressionVisibility,
    ) -> ProgressionVisibility:
        leaderboard_id = _stable_id(leaderboard_id, field="leaderboard_id")
        _positive_version(version)
        if not isinstance(visibility, ProgressionVisibility):
            raise ProgressionPolicyError("invalid_visibility")
        self._authorize(actor, "progression.privacy", actor.account_id)
        with self._lock:
            if (leaderboard_id, version) not in self._leaderboards:
                raise ProgressionStateError("leaderboard_definition_not_found")
            key = (leaderboard_id, version, actor.account_id)
            previous = self._visibility.get(key, ProgressionVisibility.PUBLIC)
            if previous is visibility:
                return visibility
            self._visibility[key] = visibility
            self._trace.append(
                {
                    "event": "leaderboard_visibility_changed",
                    "leaderboard_id": leaderboard_id,
                    "definition_version": version,
                    "account_id": actor.account_id,
                    "visibility": visibility.value,
                }
            )
            return visibility

    def stat_value(
        self, actor: AuthorityActorContext, account_id: str, stat_id: str, version: int
    ) -> StatValue | None:
        account_id = _stable_id(account_id, field="account_id")
        stat_id = _stable_id(stat_id, field="stat_id")
        _positive_version(version)
        self._authorize(actor, "progression.read", account_id)
        with self._lock:
            return self._values.get((account_id, stat_id, version))

    def achievement_progress(
        self,
        actor: AuthorityActorContext,
        account_id: str,
        achievement_id: str,
        version: int,
    ) -> AchievementProgressSnapshot:
        account_id = _stable_id(account_id, field="account_id")
        achievement_id = _stable_id(achievement_id, field="achievement_id")
        _positive_version(version)
        self._authorize(actor, "progression.read", account_id)
        with self._lock:
            definition = self._achievements.get((achievement_id, version))
            if definition is None:
                raise ProgressionStateError("achievement_definition_not_found")
            value = self._values.get((account_id, definition.stat_id, definition.stat_version))
            unlocked = (account_id, achievement_id, version) in self._unlocks
            return AchievementProgressSnapshot(
                account_id,
                achievement_id,
                version,
                value.value if value is not None else None,
                definition.threshold,
                definition.threshold_mode,
                unlocked,
            )

    def achievement_unlock(
        self,
        actor: AuthorityActorContext,
        account_id: str,
        achievement_id: str,
        version: int,
    ) -> AchievementUnlock | None:
        account_id = _stable_id(account_id, field="account_id")
        achievement_id = _stable_id(achievement_id, field="achievement_id")
        _positive_version(version)
        self._authorize(actor, "progression.read", account_id)
        with self._lock:
            return self._unlocks.get((account_id, achievement_id, version))

    def _leaderboard_period(
        self,
        definition: LeaderboardDefinition,
        now_ms: int,
        period_index: int | None,
    ) -> LeaderboardPeriod:
        if period_index is None:
            period = definition.period_for(now_ms)
            if period is None:
                raise ProgressionStateError("leaderboard_not_started")
            return period
        period = definition.period_at_index(period_index)
        if period.starts_at_ms is not None and period.starts_at_ms > now_ms:
            raise ProgressionStateError("future_leaderboard_period")
        return period

    def ranking_snapshot(
        self,
        actor: AuthorityActorContext,
        leaderboard_id: str,
        version: int,
        *,
        period_index: int | None = None,
    ) -> LeaderboardSnapshot:
        leaderboard_id = _stable_id(leaderboard_id, field="leaderboard_id")
        _positive_version(version)
        self._authorize(actor, "progression.read", leaderboard_id)
        with self._lock:
            definition = self._leaderboards.get((leaderboard_id, version))
            if definition is None:
                raise ProgressionStateError("leaderboard_definition_not_found")
            now_ms = _server_now_ms(self.clock_ms)
            period = self._leaderboard_period(definition, now_ms, period_index)
            scores = [
                score
                for key, score in self._scores.items()
                if key[0] == leaderboard_id and key[1] == version and key[2] == period.period_id
            ]
            visible: list[tuple[LeaderboardScore, ProgressionVisibility]] = []
            for score in scores:
                visibility = self._visibility.get(
                    (leaderboard_id, version, score.account_id),
                    ProgressionVisibility.PUBLIC,
                )
                if (
                    visibility is ProgressionVisibility.PRIVATE
                    and score.account_id != actor.account_id
                    and not self._can_read_private(actor)
                ):
                    continue
                visible.append((score, visibility))
            if definition.order is LeaderboardOrder.HIGHER_BETTER:
                visible.sort(key=lambda item: (-item[0].score, item[0].account_id))
            else:
                visible.sort(key=lambda item: (item[0].score, item[0].account_id))

            ranked: list[RankedLeaderboardEntry] = []
            previous_score: int | None = None
            previous_rank = 0
            for index, (score, visibility) in enumerate(visible, start=1):
                if definition.tie_policy is LeaderboardTiePolicy.SHARED_RANK and score.score == previous_score:
                    rank = previous_rank
                else:
                    rank = index
                ranked.append(
                    RankedLeaderboardEntry(
                        rank,
                        score.account_id,
                        score.score,
                        score.achieved_sequence,
                        visibility,
                    )
                )
                previous_score = score.score
                previous_rank = rank

            snapshot_payload = {
                "leaderboard_id": leaderboard_id,
                "definition_version": version,
                "period": period.canonical(),
                "generated_at_ms": now_ms,
                "entries": [entry.canonical() for entry in ranked],
            }
            snapshot_id = f"ranking-{canonical_sha256(snapshot_payload)[:24]}"
            return LeaderboardSnapshot(
                snapshot_id,
                leaderboard_id,
                version,
                period,
                now_ms,
                tuple(ranked),
            )

    def definition_digest(self) -> str:
        with self._lock:
            return canonical_sha256(
                {
                    "stats": [self._stats[key].canonical() for key in sorted(self._stats)],
                    "achievements": [self._achievements[key].canonical() for key in sorted(self._achievements)],
                    "leaderboards": [self._leaderboards[key].canonical() for key in sorted(self._leaderboards)],
                    "active": {
                        "stats": dict(sorted(self._active_stats.items())),
                        "achievements": dict(sorted(self._active_achievements.items())),
                        "leaderboards": dict(sorted(self._active_leaderboards.items())),
                    },
                }
            )

    def canonical_state(self) -> Mapping[str, object]:
        with self._lock:
            return {
                "definitions": {
                    "stats": [self._stats[key].canonical() for key in sorted(self._stats)],
                    "achievements": [self._achievements[key].canonical() for key in sorted(self._achievements)],
                    "leaderboards": [self._leaderboards[key].canonical() for key in sorted(self._leaderboards)],
                    "active_stats": dict(sorted(self._active_stats.items())),
                    "active_achievements": dict(sorted(self._active_achievements.items())),
                    "active_leaderboards": dict(sorted(self._active_leaderboards.items())),
                },
                "values": [self._values[key].canonical() for key in sorted(self._values)],
                "events": [self._events[key].canonical() for key in sorted(self._events)],
                "unlocks": [self._unlocks[key].canonical() for key in sorted(self._unlocks)],
                "scores": [self._scores[key].canonical() for key in sorted(self._scores)],
                "visibility": [
                    {
                        "leaderboard_id": key[0],
                        "definition_version": key[1],
                        "account_id": key[2],
                        "visibility": self._visibility[key].value,
                    }
                    for key in sorted(self._visibility)
                ],
                "sequence": self._sequence,
            }

    def state_digest(self) -> str:
        return canonical_sha256(self.canonical_state())

    def trace_digest(self) -> str:
        with self._lock:
            return canonical_sha256({"trace": list(self._trace)})

    def events(self) -> tuple[ProgressionEvent, ...]:
        with self._lock:
            return tuple(sorted(self._events.values(), key=lambda item: item.sequence))

    def unlocks(self) -> tuple[AchievementUnlock, ...]:
        with self._lock:
            return tuple(
                self._unlocks[key]
                for key in sorted(self._unlocks)
            )
