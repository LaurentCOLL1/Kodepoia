from pathlib import Path

progression_path = Path("src/kodepoia/backend/progression.py")
text = progression_path.read_text(encoding="utf-8")

old = '''def _int_value(value: int, *, field: str) -> int:\n    if isinstance(value, bool) or not isinstance(value, int) or not -(2**63) <= value <= 2**63 - 1:\n        raise ProgressionPolicyError(f"invalid_{field}")\n    return value\n\n\ndef _metadata'''
new = '''def _int_value(value: int, *, field: str) -> int:\n    if isinstance(value, bool) or not isinstance(value, int) or not -(2**63) <= value <= 2**63 - 1:\n        raise ProgressionPolicyError(f"invalid_{field}")\n    return value\n\n\ndef _server_now_ms(clock_ms: Callable[[], int]) -> int:\n    value = clock_ms()\n    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**63 - 1:\n        raise ProgressionPolicyError("invalid_server_clock")\n    return value\n\n\ndef _metadata'''
assert text.count(old) == 1, text.count(old)
text = text.replace(old, new)

old = '''    def __post_init__(self) -> None:\n        object.__setattr__(self, "stat_id", _stable_id(self.stat_id, field="stat_id"))\n        _positive_version(self.version)\n        _int_value(self.minimum, field="minimum")\n        _int_value(self.maximum, field="maximum")\n        if self.minimum > self.maximum:\n            raise ProgressionPolicyError("invalid_stat_bounds")\n'''
new = '''    def __post_init__(self) -> None:\n        object.__setattr__(self, "stat_id", _stable_id(self.stat_id, field="stat_id"))\n        _positive_version(self.version)\n        if not isinstance(self.aggregation, StatAggregation):\n            raise ProgressionPolicyError("invalid_stat_aggregation")\n        _int_value(self.minimum, field="minimum")\n        _int_value(self.maximum, field="maximum")\n        if self.minimum > self.maximum:\n            raise ProgressionPolicyError("invalid_stat_bounds")\n'''
assert text.count(old) == 1
text = text.replace(old, new)

old = '''        _positive_version(self.version)\n        _positive_version(self.stat_version, field="stat_version")\n        _int_value(self.threshold, field="threshold")\n        if not isinstance(self.hidden, bool):\n            raise ProgressionPolicyError("invalid_hidden")\n'''
new = '''        _positive_version(self.version)\n        _positive_version(self.stat_version, field="stat_version")\n        if not isinstance(self.threshold_mode, AchievementThreshold):\n            raise ProgressionPolicyError("invalid_threshold_mode")\n        _int_value(self.threshold, field="threshold")\n        if not isinstance(self.hidden, bool):\n            raise ProgressionPolicyError("invalid_hidden")\n'''
assert text.count(old) == 1
text = text.replace(old, new)

old = '''        _positive_version(self.version)\n        _positive_version(self.stat_version, field="stat_version")\n        if self.period_kind is LeaderboardPeriodKind.CLASSIC:\n'''
new = '''        _positive_version(self.version)\n        _positive_version(self.stat_version, field="stat_version")\n        if not isinstance(self.order, LeaderboardOrder):\n            raise ProgressionPolicyError("invalid_leaderboard_order")\n        if not isinstance(self.score_policy, LeaderboardScorePolicy):\n            raise ProgressionPolicyError("invalid_score_policy")\n        if not isinstance(self.tie_policy, LeaderboardTiePolicy):\n            raise ProgressionPolicyError("invalid_tie_policy")\n        if not isinstance(self.period_kind, LeaderboardPeriodKind):\n            raise ProgressionPolicyError("invalid_period_kind")\n        if self.period_kind is LeaderboardPeriodKind.CLASSIC:\n'''
assert text.count(old) == 1
text = text.replace(old, new)

old = '''    @staticmethod\n    def _better(definition: LeaderboardDefinition, candidate: int, previous: int) -> bool:\n        if definition.order is LeaderboardOrder.HIGHER_BETTER:\n            return candidate > previous\n        return candidate < previous\n\n    def _period_entry_count'''
new = '''    @staticmethod\n    def _better(definition: LeaderboardDefinition, candidate: int, previous: int) -> bool:\n        if definition.order is LeaderboardOrder.HIGHER_BETTER:\n            return candidate > previous\n        return candidate < previous\n\n    @staticmethod\n    def _leaderboard_candidate(\n        stat_definition: StatDefinition,\n        leaderboard: LeaderboardDefinition,\n        previous: LeaderboardScore | None,\n        input_value: int,\n        lifetime_value: int,\n    ) -> int:\n        if leaderboard.period_kind is LeaderboardPeriodKind.CLASSIC:\n            candidate = lifetime_value\n        elif previous is None:\n            candidate = input_value\n        elif stat_definition.aggregation is StatAggregation.SUM:\n            candidate = previous.score + input_value\n        elif stat_definition.aggregation is StatAggregation.MAX:\n            candidate = max(previous.score, input_value)\n        elif stat_definition.aggregation is StatAggregation.MIN:\n            candidate = min(previous.score, input_value)\n        else:\n            raise ProgressionPolicyError("unsupported_stat_aggregation")\n        if candidate < stat_definition.minimum or candidate > stat_definition.maximum:\n            raise ProgressionStateError("leaderboard_stat_bounds")\n        return candidate\n\n    def _period_entry_count'''
assert text.count(old) == 1
text = text.replace(old, new)

assert text.count("now_ms = int(self.clock_ms())") == 2
text = text.replace("now_ms = int(self.clock_ms())", "now_ms = _server_now_ms(self.clock_ms)")

old = '''            updated_leaderboards: list[str] = []\n            for leaderboard, period in affected_leaderboards:\n                score_key = (leaderboard.leaderboard_id, leaderboard.version, period.period_id, account_id)\n                previous = self._scores.get(score_key)\n                should_update = previous is None\n                if previous is not None:\n                    should_update = (\n                        leaderboard.score_policy is LeaderboardScorePolicy.FORCE_UPDATE\n                        or self._better(leaderboard, resulting, previous.score)\n                    )\n                if should_update:\n                    score = LeaderboardScore(\n                        leaderboard.leaderboard_id,\n                        leaderboard.version,\n                        period.period_id,\n                        account_id,\n                        resulting,\n                        sequence,\n                        now_ms,\n                    )\n'''
new = '''            updated_leaderboards: list[str] = []\n            for leaderboard, period in affected_leaderboards:\n                score_key = (leaderboard.leaderboard_id, leaderboard.version, period.period_id, account_id)\n                previous = self._scores.get(score_key)\n                candidate = self._leaderboard_candidate(\n                    definition, leaderboard, previous, value, resulting\n                )\n                should_update = previous is None\n                if previous is not None:\n                    should_update = (\n                        leaderboard.score_policy is LeaderboardScorePolicy.FORCE_UPDATE\n                        or self._better(leaderboard, candidate, previous.score)\n                    )\n                if should_update:\n                    score = LeaderboardScore(\n                        leaderboard.leaderboard_id,\n                        leaderboard.version,\n                        period.period_id,\n                        account_id,\n                        candidate,\n                        sequence,\n                        now_ms,\n                    )\n'''
assert text.count(old) == 1, text.count(old)
text = text.replace(old, new)

old = '''        leaderboard_id = _stable_id(leaderboard_id, field="leaderboard_id")\n        _positive_version(version)\n        self._authorize(actor, "progression.privacy", actor.account_id)\n'''
new = '''        leaderboard_id = _stable_id(leaderboard_id, field="leaderboard_id")\n        _positive_version(version)\n        if not isinstance(visibility, ProgressionVisibility):\n            raise ProgressionPolicyError("invalid_visibility")\n        self._authorize(actor, "progression.privacy", actor.account_id)\n'''
assert text.count(old) == 1
text = text.replace(old, new)

progression_path.write_text(text, encoding="utf-8")

init_path = Path("src/kodepoia/backend/__init__.py")
init = init_path.read_text(encoding="utf-8")
import_marker = '''from .postgres import (\n'''
progression_import = '''from .progression import (\n    AchievementDefinition,\n    AchievementProgressSnapshot,\n    AchievementThreshold,\n    AchievementUnlock,\n    InMemoryProgressionService,\n    LeaderboardDefinition,\n    LeaderboardOrder,\n    LeaderboardPeriod,\n    LeaderboardPeriodKind,\n    LeaderboardScore,\n    LeaderboardScorePolicy,\n    LeaderboardSnapshot,\n    LeaderboardTiePolicy,\n    ProgressionApplyResult,\n    ProgressionAuthorizationError,\n    ProgressionCapacityError,\n    ProgressionEvent,\n    ProgressionPolicyError,\n    ProgressionStateError,\n    ProgressionVisibility,\n    RankedLeaderboardEntry,\n    StatAggregation,\n    StatDefinition,\n    StatValue,\n)\n'''
assert progression_import not in init
assert init.count(import_marker) == 1
init = init.replace(import_marker, progression_import + import_marker)

all_marker = '''    "BACKEND_DNA_SERVICE_KINDS",\n'''
progression_all = '''    "AchievementDefinition",\n    "AchievementProgressSnapshot",\n    "AchievementThreshold",\n    "AchievementUnlock",\n    "InMemoryProgressionService",\n    "LeaderboardDefinition",\n    "LeaderboardOrder",\n    "LeaderboardPeriod",\n    "LeaderboardPeriodKind",\n    "LeaderboardScore",\n    "LeaderboardScorePolicy",\n    "LeaderboardSnapshot",\n    "LeaderboardTiePolicy",\n    "ProgressionApplyResult",\n    "ProgressionAuthorizationError",\n    "ProgressionCapacityError",\n    "ProgressionEvent",\n    "ProgressionPolicyError",\n    "ProgressionStateError",\n    "ProgressionVisibility",\n    "RankedLeaderboardEntry",\n    "StatAggregation",\n    "StatDefinition",\n    "StatValue",\n'''
assert '    "InMemoryProgressionService",\n' not in init
assert init.count(all_marker) == 1
init = init.replace(all_marker, progression_all + all_marker)
init_path.write_text(init, encoding="utf-8")
