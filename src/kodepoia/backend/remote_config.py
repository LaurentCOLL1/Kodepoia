from __future__ import annotations

import json
import math
import re
import threading
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Callable, Mapping, Sequence

from .authority import AuthorityActorContext
from .contracts import BackendEnvironmentKind, canonical_json_bytes, canonical_sha256

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,191}$")
_CONTEXT_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PII_CONTEXT_KEYS = frozenset(
    {
        "address",
        "authorization",
        "cookie",
        "email",
        "first_name",
        "full_name",
        "ip_address",
        "last_name",
        "password",
        "phone",
        "secret",
        "token",
    }
)


class RemoteConfigPolicyError(ValueError):
    pass


class RemoteConfigStateError(RuntimeError):
    pass


class RemoteConfigAuthorizationError(PermissionError):
    pass


class RemoteConfigCapacityError(RemoteConfigStateError):
    pass


class FlagValueType(StrEnum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    OBJECT = "object"


class TargetingOperator(StrEnum):
    EQUALS = "equals"
    ONE_OF = "one_of"
    STARTS_WITH = "starts_with"


class EvaluationReason(StrEnum):
    DEFAULT = "default"
    TARGETING_MATCH = "targeting_match"
    FRACTIONAL = "fractional"
    PREREQUISITE_FAILED = "prerequisite_failed"
    EXPIRED = "expired"
    KILL_SWITCH = "kill_switch"
    ERROR = "error"


class EvaluationErrorCode(StrEnum):
    TARGETING_KEY_MISSING = "targeting_key_missing"
    TYPE_MISMATCH = "type_mismatch"


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise RemoteConfigPolicyError(f"invalid_{field}")
    return value


def _context_key(value: str) -> str:
    if not isinstance(value, str) or _CONTEXT_KEY_RE.fullmatch(value) is None:
        raise RemoteConfigPolicyError("invalid_context_key")
    if value.lower() in _PII_CONTEXT_KEYS:
        raise RemoteConfigPolicyError("pii_context_key_forbidden")
    return value


def _positive_version(value: int, *, field: str = "version") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 2**31 - 1:
        raise RemoteConfigPolicyError(f"invalid_{field}")
    return value


def _timestamp(value: int | None, *, field: str, optional: bool = False) -> int | None:
    if optional and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**63 - 1:
        raise RemoteConfigPolicyError(f"invalid_{field}")
    return value


def _sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise RemoteConfigPolicyError(f"invalid_{field}")
    return value


def _server_now_ms(clock_ms: Callable[[], int]) -> int:
    value = clock_ms()
    checked = _timestamp(value, field="server_clock")
    assert isinstance(checked, int)
    return checked


def _canonical_json_copy(value: Any, *, field: str, max_bytes: int = 64 * 1024) -> Any:
    try:
        encoded = canonical_json_bytes(value)
    except ValueError as exc:
        raise RemoteConfigPolicyError(f"{field}_not_canonical_json") from exc
    if len(encoded) > max_bytes:
        raise RemoteConfigPolicyError(f"{field}_too_large")
    return json.loads(encoded.decode("utf-8"))


def _typed_value(value_type: FlagValueType, value: Any, *, field: str) -> Any:
    if not isinstance(value_type, FlagValueType):
        raise RemoteConfigPolicyError("invalid_value_type")
    if value_type is FlagValueType.BOOLEAN:
        if not isinstance(value, bool):
            raise RemoteConfigPolicyError(f"{field}_type_mismatch")
        return value
    if value_type is FlagValueType.INTEGER:
        if isinstance(value, bool) or not isinstance(value, int):
            raise RemoteConfigPolicyError(f"{field}_type_mismatch")
        return value
    if value_type is FlagValueType.NUMBER:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RemoteConfigPolicyError(f"{field}_type_mismatch")
        if isinstance(value, float) and not math.isfinite(value):
            raise RemoteConfigPolicyError(f"{field}_not_finite")
        return value
    if value_type is FlagValueType.STRING:
        if not isinstance(value, str):
            raise RemoteConfigPolicyError(f"{field}_type_mismatch")
        if len(value.encode("utf-8")) > 16 * 1024:
            raise RemoteConfigPolicyError(f"{field}_too_large")
        return value
    if value_type is FlagValueType.OBJECT:
        if not isinstance(value, (Mapping, list)):
            raise RemoteConfigPolicyError(f"{field}_type_mismatch")
        return _canonical_json_copy(value, field=field)
    raise RemoteConfigPolicyError("unsupported_value_type")


def _scalar_target_value(value: Any, *, field: str) -> bool | int | float | str:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RemoteConfigPolicyError(f"{field}_not_finite")
        return value
    if isinstance(value, str):
        if len(value.encode("utf-8")) > 4096:
            raise RemoteConfigPolicyError(f"{field}_too_large")
        return value
    raise RemoteConfigPolicyError(f"{field}_must_be_scalar")


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    targeting_key: str | None = None
    attributes: Mapping[str, Any] = None  # type: ignore[assignment]
    max_bytes: int = 8 * 1024

    def __post_init__(self) -> None:
        if self.targeting_key is not None:
            _stable_id(self.targeting_key, field="targeting_key")
        if isinstance(self.max_bytes, bool) or not isinstance(self.max_bytes, int) or not 256 <= self.max_bytes <= 64 * 1024:
            raise RemoteConfigPolicyError("invalid_context_budget")
        source = {} if self.attributes is None else self.attributes
        if not isinstance(source, Mapping):
            raise RemoteConfigPolicyError("context_attributes_must_be_mapping")
        normalized: dict[str, Any] = {}
        for key, value in source.items():
            checked = _context_key(key)
            normalized[checked] = _canonical_json_copy(value, field=f"context_{checked}", max_bytes=self.max_bytes)
        canonical = {
            "targeting_key_digest": (
                canonical_sha256({"targeting_key": self.targeting_key})
                if self.targeting_key is not None
                else None
            ),
            "attributes": normalized,
        }
        if len(canonical_json_bytes(canonical)) > self.max_bytes:
            raise RemoteConfigPolicyError("evaluation_context_too_large")
        object.__setattr__(self, "attributes", normalized)

    @property
    def targeting_key_digest(self) -> str | None:
        if self.targeting_key is None:
            return None
        return canonical_sha256({"targeting_key": self.targeting_key})

    def public_canonical(self) -> dict[str, Any]:
        return {
            "targeting_key_digest": self.targeting_key_digest,
            "attributes": dict(self.attributes),
        }

    def digest(self) -> str:
        return canonical_sha256(self.public_canonical())

    def value_for(self, field: str) -> Any:
        if field == "targeting_key":
            return self.targeting_key
        return self.attributes.get(field)


@dataclass(frozen=True, slots=True)
class FlagVariant:
    variant: str
    value: Any

    def __post_init__(self) -> None:
        object.__setattr__(self, "variant", _stable_id(self.variant, field="variant"))

    def canonical(self) -> dict[str, Any]:
        return {"variant": self.variant, "value": self.value}


@dataclass(frozen=True, slots=True)
class TargetingRule:
    rule_id: str
    field: str
    operator: TargetingOperator
    expected: Any
    variant: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", _stable_id(self.rule_id, field="rule_id"))
        if self.field != "targeting_key":
            object.__setattr__(self, "field", _context_key(self.field))
        if not isinstance(self.operator, TargetingOperator):
            raise RemoteConfigPolicyError("invalid_targeting_operator")
        object.__setattr__(self, "variant", _stable_id(self.variant, field="variant"))
        if self.operator is TargetingOperator.ONE_OF:
            if not isinstance(self.expected, Sequence) or isinstance(self.expected, (str, bytes, bytearray)):
                raise RemoteConfigPolicyError("one_of_expected_must_be_sequence")
            normalized = tuple(_scalar_target_value(item, field="targeting_expected") for item in self.expected)
            if not normalized or len(normalized) > 128:
                raise RemoteConfigPolicyError("invalid_one_of_expected")
            object.__setattr__(self, "expected", normalized)
        elif self.operator is TargetingOperator.STARTS_WITH:
            if not isinstance(self.expected, str) or not self.expected:
                raise RemoteConfigPolicyError("starts_with_expected_must_be_string")
            object.__setattr__(self, "expected", _scalar_target_value(self.expected, field="targeting_expected"))
        else:
            object.__setattr__(self, "expected", _scalar_target_value(self.expected, field="targeting_expected"))

    def matches(self, context: EvaluationContext) -> bool:
        actual = context.value_for(self.field)
        if self.operator is TargetingOperator.EQUALS:
            return actual == self.expected
        if self.operator is TargetingOperator.ONE_OF:
            return actual in self.expected
        if self.operator is TargetingOperator.STARTS_WITH:
            return isinstance(actual, str) and actual.startswith(self.expected)
        raise RemoteConfigStateError("unsupported_targeting_operator")

    def canonical(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "field": self.field,
            "operator": self.operator.value,
            "expected": list(self.expected) if isinstance(self.expected, tuple) else self.expected,
            "variant": self.variant,
        }


@dataclass(frozen=True, slots=True)
class RolloutAllocation:
    variant: str
    basis_points: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "variant", _stable_id(self.variant, field="variant"))
        if isinstance(self.basis_points, bool) or not isinstance(self.basis_points, int) or not 1 <= self.basis_points <= 10_000:
            raise RemoteConfigPolicyError("invalid_rollout_basis_points")

    def canonical(self) -> dict[str, Any]:
        return {"variant": self.variant, "basis_points": self.basis_points}


@dataclass(frozen=True, slots=True)
class RolloutPlan:
    rollout_id: str
    allocations: tuple[RolloutAllocation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "rollout_id", _stable_id(self.rollout_id, field="rollout_id"))
        allocations = tuple(self.allocations)
        if not allocations or len(allocations) > 64:
            raise RemoteConfigPolicyError("invalid_rollout_allocations")
        variants = [item.variant for item in allocations]
        if len(set(variants)) != len(variants):
            raise RemoteConfigPolicyError("duplicate_rollout_variant")
        if sum(item.basis_points for item in allocations) != 10_000:
            raise RemoteConfigPolicyError("rollout_must_total_10000_basis_points")
        object.__setattr__(self, "allocations", allocations)

    def canonical(self) -> dict[str, Any]:
        return {
            "rollout_id": self.rollout_id,
            "allocations": [item.canonical() for item in self.allocations],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class FlagPrerequisite:
    flag_id: str
    expected_variant: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "flag_id", _stable_id(self.flag_id, field="prerequisite_flag_id"))
        object.__setattr__(self, "expected_variant", _stable_id(self.expected_variant, field="expected_variant"))

    def canonical(self) -> dict[str, str]:
        return {"flag_id": self.flag_id, "expected_variant": self.expected_variant}


@dataclass(frozen=True, slots=True)
class FeatureFlagDefinition:
    flag_id: str
    version: int
    value_type: FlagValueType
    variants: tuple[FlagVariant, ...]
    default_variant: str
    targeting_rules: tuple[TargetingRule, ...] = ()
    rollout: RolloutPlan | None = None
    prerequisites: tuple[FlagPrerequisite, ...] = ()
    expires_at_ms: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "flag_id", _stable_id(self.flag_id, field="flag_id"))
        _positive_version(self.version)
        if not isinstance(self.value_type, FlagValueType):
            raise RemoteConfigPolicyError("invalid_value_type")
        variants = tuple(self.variants)
        if not variants or len(variants) > 128:
            raise RemoteConfigPolicyError("invalid_flag_variants")
        variant_names = [item.variant for item in variants]
        if len(set(variant_names)) != len(variant_names):
            raise RemoteConfigPolicyError("duplicate_flag_variant")
        normalized_variants = tuple(
            replace(item, value=_typed_value(self.value_type, item.value, field=f"variant_{item.variant}"))
            for item in variants
        )
        object.__setattr__(self, "variants", normalized_variants)
        object.__setattr__(self, "default_variant", _stable_id(self.default_variant, field="default_variant"))
        if self.default_variant not in set(variant_names):
            raise RemoteConfigPolicyError("default_variant_not_found")
        rules = tuple(self.targeting_rules)
        if len(rules) > 256:
            raise RemoteConfigPolicyError("too_many_targeting_rules")
        rule_ids = [rule.rule_id for rule in rules]
        if len(set(rule_ids)) != len(rule_ids):
            raise RemoteConfigPolicyError("duplicate_targeting_rule")
        if any(rule.variant not in set(variant_names) for rule in rules):
            raise RemoteConfigPolicyError("targeting_variant_not_found")
        object.__setattr__(self, "targeting_rules", rules)
        prerequisites = tuple(self.prerequisites)
        if len(prerequisites) > 64:
            raise RemoteConfigPolicyError("too_many_prerequisites")
        if len({item.flag_id for item in prerequisites}) != len(prerequisites):
            raise RemoteConfigPolicyError("duplicate_prerequisite")
        object.__setattr__(self, "prerequisites", prerequisites)
        if self.rollout is not None:
            if not isinstance(self.rollout, RolloutPlan):
                raise RemoteConfigPolicyError("invalid_rollout")
            if any(item.variant not in set(variant_names) for item in self.rollout.allocations):
                raise RemoteConfigPolicyError("rollout_variant_not_found")
        _timestamp(self.expires_at_ms, field="expires_at_ms", optional=True)

    def variant(self, name: str) -> FlagVariant:
        for item in self.variants:
            if item.variant == name:
                return item
        raise RemoteConfigStateError("variant_not_found")

    def canonical(self) -> dict[str, Any]:
        return {
            "flag_id": self.flag_id,
            "version": self.version,
            "value_type": self.value_type.value,
            "variants": [item.canonical() for item in self.variants],
            "default_variant": self.default_variant,
            "targeting_rules": [item.canonical() for item in self.targeting_rules],
            "rollout": self.rollout.canonical() if self.rollout is not None else None,
            "prerequisites": [item.canonical() for item in self.prerequisites],
            "expires_at_ms": self.expires_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ConfigSnapshot:
    snapshot_id: str
    revision: int
    environment: BackendEnvironmentKind
    flags: tuple[FeatureFlagDefinition, ...]
    created_at_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_id", _stable_id(self.snapshot_id, field="snapshot_id"))
        _positive_version(self.revision, field="revision")
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise RemoteConfigPolicyError("invalid_environment")
        flags = tuple(self.flags)
        if not flags:
            raise RemoteConfigPolicyError("snapshot_requires_flags")
        if len({item.flag_id for item in flags}) != len(flags):
            raise RemoteConfigPolicyError("duplicate_snapshot_flag")
        object.__setattr__(self, "flags", tuple(sorted(flags, key=lambda item: item.flag_id)))
        _timestamp(self.created_at_ms, field="created_at_ms")

    def flag(self, flag_id: str) -> FeatureFlagDefinition:
        for definition in self.flags:
            if definition.flag_id == flag_id:
                return definition
        raise RemoteConfigStateError("flag_not_found")

    def canonical(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "revision": self.revision,
            "environment": self.environment.value,
            "flags": [item.canonical() for item in self.flags],
            "created_at_ms": self.created_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ActivationPreview:
    preview_id: str
    environment: BackendEnvironmentKind
    from_snapshot_id: str | None
    to_snapshot_id: str
    from_snapshot_digest: str | None
    to_snapshot_digest: str
    changed_flags: tuple[str, ...]
    production_requires_approval: bool

    def canonical(self) -> dict[str, Any]:
        return {
            "preview_id": self.preview_id,
            "environment": self.environment.value,
            "from_snapshot_id": self.from_snapshot_id,
            "to_snapshot_id": self.to_snapshot_id,
            "from_snapshot_digest": self.from_snapshot_digest,
            "to_snapshot_digest": self.to_snapshot_digest,
            "changed_flags": list(self.changed_flags),
            "production_requires_approval": self.production_requires_approval,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ActivationApproval:
    approval_id: str
    environment: BackendEnvironmentKind
    preview_digest: str
    snapshot_digest: str
    approver_account_id: str
    safe_change_digest: str
    approved_at_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "approval_id", _stable_id(self.approval_id, field="approval_id"))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise RemoteConfigPolicyError("invalid_environment")
        object.__setattr__(self, "preview_digest", _sha256(self.preview_digest, field="preview_digest"))
        object.__setattr__(self, "snapshot_digest", _sha256(self.snapshot_digest, field="snapshot_digest"))
        object.__setattr__(
            self,
            "approver_account_id",
            _stable_id(self.approver_account_id, field="approver_account_id"),
        )
        object.__setattr__(self, "safe_change_digest", _sha256(self.safe_change_digest, field="safe_change_digest"))
        _timestamp(self.approved_at_ms, field="approved_at_ms")

    def canonical(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "environment": self.environment.value,
            "preview_digest": self.preview_digest,
            "snapshot_digest": self.snapshot_digest,
            "approver_account_id": self.approver_account_id,
            "safe_change_digest": self.safe_change_digest,
            "approved_at_ms": self.approved_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ConfigAuditRecord:
    sequence: int
    action: str
    actor_account_id: str
    environment: BackendEnvironmentKind
    snapshot_id: str | None
    preview_digest: str | None
    safe_change_digest: str | None
    recorded_at_ms: int

    def canonical(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "action": self.action,
            "actor_account_id": self.actor_account_id,
            "environment": self.environment.value,
            "snapshot_id": self.snapshot_id,
            "preview_digest": self.preview_digest,
            "safe_change_digest": self.safe_change_digest,
            "recorded_at_ms": self.recorded_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    flag_id: str
    snapshot_id: str
    environment: BackendEnvironmentKind
    variant: str
    value_type: FlagValueType
    value: Any
    reason: EvaluationReason
    context_digest: str
    evaluation_digest: str
    rollout_bucket: int | None = None
    error_code: EvaluationErrorCode | None = None

    def public_canonical(self) -> dict[str, Any]:
        return {
            "flag_id": self.flag_id,
            "snapshot_id": self.snapshot_id,
            "environment": self.environment.value,
            "variant": self.variant,
            "value_type": self.value_type.value,
            "value": self.value,
            "reason": self.reason.value,
            "context_digest": self.context_digest,
            "evaluation_digest": self.evaluation_digest,
            "rollout_bucket": self.rollout_bucket,
            "error_code": self.error_code.value if self.error_code is not None else None,
        }


@dataclass(frozen=True, slots=True)
class RemoteConfigStateSnapshot:
    active_snapshots: tuple[tuple[str, str], ...]
    registered_snapshot_digests: tuple[str, ...]
    kill_switches: tuple[tuple[str, str], ...]
    audit_digest: str
    trace_digest: str

    def canonical(self) -> dict[str, Any]:
        return {
            "active_snapshots": [list(item) for item in self.active_snapshots],
            "registered_snapshot_digests": list(self.registered_snapshot_digests),
            "kill_switches": [list(item) for item in self.kill_switches],
            "audit_digest": self.audit_digest,
            "trace_digest": self.trace_digest,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class InMemoryRemoteConfigService:
    def __init__(
        self,
        *,
        clock_ms: Callable[[], int],
        max_snapshots: int = 4_096,
        max_flags_per_snapshot: int = 4_096,
        max_evaluations: int = 1_000_000,
        max_audit_records: int = 100_000,
    ) -> None:
        for name, value in (
            ("max_snapshots", max_snapshots),
            ("max_flags_per_snapshot", max_flags_per_snapshot),
            ("max_evaluations", max_evaluations),
            ("max_audit_records", max_audit_records),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise RemoteConfigPolicyError(f"{name}_must_be_positive")
        self.clock_ms = clock_ms
        self.max_snapshots = max_snapshots
        self.max_flags_per_snapshot = max_flags_per_snapshot
        self.max_evaluations = max_evaluations
        self.max_audit_records = max_audit_records
        self._lock = threading.RLock()
        self._snapshots: dict[tuple[BackendEnvironmentKind, str], ConfigSnapshot] = {}
        self._active: dict[BackendEnvironmentKind, str] = {}
        self._kill_switches: set[tuple[BackendEnvironmentKind, str]] = set()
        self._approvals: dict[str, ActivationApproval] = {}
        self._audit: list[ConfigAuditRecord] = []
        self._trace: list[dict[str, Any]] = []
        self._sequence = 0
        self._evaluation_count = 0

    @staticmethod
    def _authorize(actor: AuthorityActorContext, permission: str, target_id: str) -> None:
        if not actor.can(permission, target_id):
            raise RemoteConfigAuthorizationError("forbidden")

    def _append_audit(
        self,
        *,
        actor: AuthorityActorContext,
        action: str,
        environment: BackendEnvironmentKind,
        snapshot_id: str | None = None,
        preview_digest: str | None = None,
        safe_change_digest: str | None = None,
    ) -> ConfigAuditRecord:
        if len(self._audit) >= self.max_audit_records:
            raise RemoteConfigCapacityError("audit_capacity")
        self._sequence += 1
        record = ConfigAuditRecord(
            sequence=self._sequence,
            action=_stable_id(action, field="audit_action"),
            actor_account_id=actor.account_id,
            environment=environment,
            snapshot_id=snapshot_id,
            preview_digest=preview_digest,
            safe_change_digest=safe_change_digest,
            recorded_at_ms=_server_now_ms(self.clock_ms),
        )
        self._audit.append(record)
        return record

    @staticmethod
    def _validate_snapshot_graph(snapshot: ConfigSnapshot, *, max_flags_per_snapshot: int) -> None:
        if len(snapshot.flags) > max_flags_per_snapshot:
            raise RemoteConfigCapacityError("flags_per_snapshot_capacity")
        by_id = {item.flag_id: item for item in snapshot.flags}
        for definition in snapshot.flags:
            for prerequisite in definition.prerequisites:
                target = by_id.get(prerequisite.flag_id)
                if target is None:
                    raise RemoteConfigPolicyError("prerequisite_flag_not_found")
                if prerequisite.expected_variant not in {item.variant for item in target.variants}:
                    raise RemoteConfigPolicyError("prerequisite_variant_not_found")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(flag_id: str) -> None:
            if flag_id in visiting:
                raise RemoteConfigPolicyError("prerequisite_cycle")
            if flag_id in visited:
                return
            visiting.add(flag_id)
            for prerequisite in by_id[flag_id].prerequisites:
                visit(prerequisite.flag_id)
            visiting.remove(flag_id)
            visited.add(flag_id)

        for flag_id in sorted(by_id):
            visit(flag_id)

    def register_snapshot(
        self,
        actor: AuthorityActorContext,
        snapshot: ConfigSnapshot,
    ) -> ConfigSnapshot:
        self._authorize(actor, "remote_config.snapshot.register", snapshot.snapshot_id)
        self._validate_snapshot_graph(snapshot, max_flags_per_snapshot=self.max_flags_per_snapshot)
        key = (snapshot.environment, snapshot.snapshot_id)
        with self._lock:
            existing = self._snapshots.get(key)
            if existing is not None:
                if existing != snapshot:
                    raise RemoteConfigStateError("snapshot_id_conflict")
                return existing
            if len(self._snapshots) >= self.max_snapshots:
                raise RemoteConfigCapacityError("snapshot_capacity")
            for (environment, _snapshot_id), other in self._snapshots.items():
                if environment is snapshot.environment and other.revision == snapshot.revision and other.digest() != snapshot.digest():
                    raise RemoteConfigStateError("snapshot_revision_conflict")
            self._snapshots[key] = snapshot
            self._trace.append(
                {
                    "event": "snapshot_registered",
                    "environment": snapshot.environment.value,
                    "snapshot_id": snapshot.snapshot_id,
                    "snapshot_digest": snapshot.digest(),
                }
            )
            return snapshot

    def snapshot(self, environment: BackendEnvironmentKind, snapshot_id: str) -> ConfigSnapshot:
        if not isinstance(environment, BackendEnvironmentKind):
            raise RemoteConfigPolicyError("invalid_environment")
        snapshot_id = _stable_id(snapshot_id, field="snapshot_id")
        try:
            return self._snapshots[(environment, snapshot_id)]
        except KeyError as exc:
            raise RemoteConfigStateError("snapshot_not_found") from exc

    def active_snapshot(self, environment: BackendEnvironmentKind) -> ConfigSnapshot:
        if not isinstance(environment, BackendEnvironmentKind):
            raise RemoteConfigPolicyError("invalid_environment")
        try:
            snapshot_id = self._active[environment]
        except KeyError as exc:
            raise RemoteConfigStateError("active_snapshot_not_found") from exc
        return self.snapshot(environment, snapshot_id)

    def preview_activation(
        self,
        actor: AuthorityActorContext,
        *,
        environment: BackendEnvironmentKind,
        snapshot_id: str,
    ) -> ActivationPreview:
        if not isinstance(environment, BackendEnvironmentKind):
            raise RemoteConfigPolicyError("invalid_environment")
        self._authorize(actor, "remote_config.preview", environment.value)
        target = self.snapshot(environment, snapshot_id)
        current_id = self._active.get(environment)
        current = self.snapshot(environment, current_id) if current_id is not None else None
        old_by_id = {} if current is None else {item.flag_id: item.digest() for item in current.flags}
        new_by_id = {item.flag_id: item.digest() for item in target.flags}
        changed = tuple(
            sorted(
                flag_id
                for flag_id in set(old_by_id) | set(new_by_id)
                if old_by_id.get(flag_id) != new_by_id.get(flag_id)
            )
        )
        seed = {
            "environment": environment.value,
            "from_snapshot_id": current.snapshot_id if current is not None else None,
            "from_snapshot_digest": current.digest() if current is not None else None,
            "to_snapshot_id": target.snapshot_id,
            "to_snapshot_digest": target.digest(),
            "changed_flags": list(changed),
        }
        preview_id = f"remote_config.preview.{canonical_sha256(seed)[:24]}"
        return ActivationPreview(
            preview_id=preview_id,
            environment=environment,
            from_snapshot_id=current.snapshot_id if current is not None else None,
            to_snapshot_id=target.snapshot_id,
            from_snapshot_digest=current.digest() if current is not None else None,
            to_snapshot_digest=target.digest(),
            changed_flags=changed,
            production_requires_approval=environment is BackendEnvironmentKind.PRODUCTION,
        )

    def approve_activation(
        self,
        actor: AuthorityActorContext,
        *,
        preview: ActivationPreview,
        approval_id: str,
        safe_change_digest: str,
    ) -> ActivationApproval:
        if not isinstance(preview, ActivationPreview):
            raise RemoteConfigPolicyError("invalid_activation_preview")
        approval_id = _stable_id(approval_id, field="approval_id")
        safe_change_digest = _sha256(safe_change_digest, field="safe_change_digest")
        self._authorize(actor, "remote_config.approve.production", preview.environment.value)
        current_preview = self.preview_activation(
            actor=actor,
            environment=preview.environment,
            snapshot_id=preview.to_snapshot_id,
        )
        if current_preview.digest() != preview.digest():
            raise RemoteConfigStateError("stale_activation_preview")
        approval = ActivationApproval(
            approval_id=approval_id,
            environment=preview.environment,
            preview_digest=preview.digest(),
            snapshot_digest=preview.to_snapshot_digest,
            approver_account_id=actor.account_id,
            safe_change_digest=safe_change_digest,
            approved_at_ms=_server_now_ms(self.clock_ms),
        )
        with self._lock:
            existing = self._approvals.get(approval_id)
            if existing is not None:
                if existing != approval:
                    raise RemoteConfigStateError("approval_id_conflict")
                return existing
            self._approvals[approval_id] = approval
            self._append_audit(
                actor=actor,
                action="activation_approved",
                environment=preview.environment,
                snapshot_id=preview.to_snapshot_id,
                preview_digest=preview.digest(),
                safe_change_digest=safe_change_digest,
            )
            return approval

    def _validate_production_approval(
        self,
        *,
        actor: AuthorityActorContext,
        preview: ActivationPreview,
        approval: ActivationApproval | None,
    ) -> ActivationApproval:
        if approval is None:
            raise RemoteConfigAuthorizationError("production_activation_requires_approval")
        stored = self._approvals.get(approval.approval_id)
        if stored != approval:
            raise RemoteConfigAuthorizationError("approval_not_registered")
        if approval.environment is not preview.environment:
            raise RemoteConfigAuthorizationError("approval_environment_mismatch")
        if approval.preview_digest != preview.digest() or approval.snapshot_digest != preview.to_snapshot_digest:
            raise RemoteConfigAuthorizationError("approval_target_mismatch")
        self._authorize(actor, "remote_config.snapshot.activate", preview.environment.value)
        return approval

    def activate_snapshot(
        self,
        actor: AuthorityActorContext,
        *,
        environment: BackendEnvironmentKind,
        snapshot_id: str,
        approval: ActivationApproval | None = None,
    ) -> ConfigSnapshot:
        if not isinstance(environment, BackendEnvironmentKind):
            raise RemoteConfigPolicyError("invalid_environment")
        self._authorize(actor, "remote_config.snapshot.activate", environment.value)
        preview = self.preview_activation(actor, environment=environment, snapshot_id=snapshot_id)
        safe_change_digest: str | None = None
        if environment is BackendEnvironmentKind.PRODUCTION:
            checked = self._validate_production_approval(actor=actor, preview=preview, approval=approval)
            safe_change_digest = checked.safe_change_digest
        target = self.snapshot(environment, snapshot_id)
        with self._lock:
            self._active[environment] = target.snapshot_id
            self._append_audit(
                actor=actor,
                action="snapshot_activated",
                environment=environment,
                snapshot_id=target.snapshot_id,
                preview_digest=preview.digest(),
                safe_change_digest=safe_change_digest,
            )
            self._trace.append(
                {
                    "event": "snapshot_activated",
                    "environment": environment.value,
                    "snapshot_id": target.snapshot_id,
                    "snapshot_digest": target.digest(),
                    "preview_digest": preview.digest(),
                    "safe_change_digest": safe_change_digest,
                }
            )
            return target

    def rollback(
        self,
        actor: AuthorityActorContext,
        *,
        environment: BackendEnvironmentKind,
        snapshot_id: str,
        approval: ActivationApproval | None = None,
    ) -> ConfigSnapshot:
        if not isinstance(environment, BackendEnvironmentKind):
            raise RemoteConfigPolicyError("invalid_environment")
        self._authorize(actor, "remote_config.rollback", environment.value)
        current = self.active_snapshot(environment)
        target = self.snapshot(environment, snapshot_id)
        if current.snapshot_id == target.snapshot_id:
            return current
        preview = self.preview_activation(actor, environment=environment, snapshot_id=snapshot_id)
        safe_change_digest: str | None = None
        if environment is BackendEnvironmentKind.PRODUCTION:
            checked = self._validate_production_approval(actor=actor, preview=preview, approval=approval)
            safe_change_digest = checked.safe_change_digest
        with self._lock:
            self._active[environment] = target.snapshot_id
            self._append_audit(
                actor=actor,
                action="snapshot_rolled_back",
                environment=environment,
                snapshot_id=target.snapshot_id,
                preview_digest=preview.digest(),
                safe_change_digest=safe_change_digest,
            )
            self._trace.append(
                {
                    "event": "snapshot_rolled_back",
                    "environment": environment.value,
                    "from_snapshot_id": current.snapshot_id,
                    "snapshot_id": target.snapshot_id,
                    "snapshot_digest": target.digest(),
                    "preview_digest": preview.digest(),
                    "safe_change_digest": safe_change_digest,
                }
            )
            return target

    def set_kill_switch(
        self,
        actor: AuthorityActorContext,
        *,
        environment: BackendEnvironmentKind,
        flag_id: str,
        enabled: bool,
    ) -> None:
        if not isinstance(environment, BackendEnvironmentKind):
            raise RemoteConfigPolicyError("invalid_environment")
        flag_id = _stable_id(flag_id, field="flag_id")
        if not isinstance(enabled, bool):
            raise RemoteConfigPolicyError("kill_switch_enabled_must_be_boolean")
        self._authorize(actor, "remote_config.kill_switch", flag_id)
        active = self.active_snapshot(environment)
        active.flag(flag_id)
        key = (environment, flag_id)
        with self._lock:
            if enabled:
                self._kill_switches.add(key)
            else:
                self._kill_switches.discard(key)
            self._append_audit(
                actor=actor,
                action="kill_switch_enabled" if enabled else "kill_switch_disabled",
                environment=environment,
                snapshot_id=active.snapshot_id,
            )
            self._trace.append(
                {
                    "event": "kill_switch_changed",
                    "environment": environment.value,
                    "flag_id": flag_id,
                    "enabled": enabled,
                }
            )

    @staticmethod
    def _rollout_bucket(definition: FeatureFlagDefinition, context: EvaluationContext) -> int:
        assert definition.rollout is not None
        if context.targeting_key is None:
            raise RemoteConfigStateError("targeting_key_missing")
        digest = canonical_sha256(
            {
                "flag_id": definition.flag_id,
                "rollout_id": definition.rollout.rollout_id,
                "targeting_key": context.targeting_key,
            }
        )
        return int(digest[:16], 16) % 10_000

    @staticmethod
    def _rollout_variant(definition: FeatureFlagDefinition, bucket: int) -> str:
        assert definition.rollout is not None
        cursor = 0
        for allocation in definition.rollout.allocations:
            cursor += allocation.basis_points
            if bucket < cursor:
                return allocation.variant
        raise RemoteConfigStateError("rollout_bucket_unassigned")

    def _result(
        self,
        *,
        snapshot: ConfigSnapshot,
        definition: FeatureFlagDefinition,
        context: EvaluationContext,
        variant: str,
        reason: EvaluationReason,
        rollout_bucket: int | None = None,
        error_code: EvaluationErrorCode | None = None,
    ) -> EvaluationResult:
        value = definition.variant(variant).value
        seed = {
            "snapshot_digest": snapshot.digest(),
            "flag_digest": definition.digest(),
            "context_digest": context.digest(),
            "variant": variant,
            "reason": reason.value,
            "rollout_bucket": rollout_bucket,
            "error_code": error_code.value if error_code is not None else None,
        }
        return EvaluationResult(
            flag_id=definition.flag_id,
            snapshot_id=snapshot.snapshot_id,
            environment=snapshot.environment,
            variant=variant,
            value_type=definition.value_type,
            value=value,
            reason=reason,
            context_digest=context.digest(),
            evaluation_digest=canonical_sha256(seed),
            rollout_bucket=rollout_bucket,
            error_code=error_code,
        )

    def _evaluate_definition(
        self,
        *,
        snapshot: ConfigSnapshot,
        definition: FeatureFlagDefinition,
        context: EvaluationContext,
        visiting: set[str],
    ) -> EvaluationResult:
        if definition.flag_id in visiting:
            raise RemoteConfigStateError("prerequisite_cycle")
        visiting.add(definition.flag_id)
        try:
            now_ms = _server_now_ms(self.clock_ms)
            if (snapshot.environment, definition.flag_id) in self._kill_switches:
                return self._result(
                    snapshot=snapshot,
                    definition=definition,
                    context=context,
                    variant=definition.default_variant,
                    reason=EvaluationReason.KILL_SWITCH,
                )
            if definition.expires_at_ms is not None and now_ms >= definition.expires_at_ms:
                return self._result(
                    snapshot=snapshot,
                    definition=definition,
                    context=context,
                    variant=definition.default_variant,
                    reason=EvaluationReason.EXPIRED,
                )
            for prerequisite in definition.prerequisites:
                prerequisite_definition = snapshot.flag(prerequisite.flag_id)
                prerequisite_result = self._evaluate_definition(
                    snapshot=snapshot,
                    definition=prerequisite_definition,
                    context=context,
                    visiting=visiting,
                )
                if prerequisite_result.variant != prerequisite.expected_variant:
                    return self._result(
                        snapshot=snapshot,
                        definition=definition,
                        context=context,
                        variant=definition.default_variant,
                        reason=EvaluationReason.PREREQUISITE_FAILED,
                    )
            for rule in definition.targeting_rules:
                if rule.matches(context):
                    return self._result(
                        snapshot=snapshot,
                        definition=definition,
                        context=context,
                        variant=rule.variant,
                        reason=EvaluationReason.TARGETING_MATCH,
                    )
            if definition.rollout is not None:
                if context.targeting_key is None:
                    return self._result(
                        snapshot=snapshot,
                        definition=definition,
                        context=context,
                        variant=definition.default_variant,
                        reason=EvaluationReason.ERROR,
                        error_code=EvaluationErrorCode.TARGETING_KEY_MISSING,
                    )
                bucket = self._rollout_bucket(definition, context)
                return self._result(
                    snapshot=snapshot,
                    definition=definition,
                    context=context,
                    variant=self._rollout_variant(definition, bucket),
                    reason=EvaluationReason.FRACTIONAL,
                    rollout_bucket=bucket,
                )
            return self._result(
                snapshot=snapshot,
                definition=definition,
                context=context,
                variant=definition.default_variant,
                reason=EvaluationReason.DEFAULT,
            )
        finally:
            visiting.remove(definition.flag_id)

    def evaluate(
        self,
        actor: AuthorityActorContext,
        *,
        environment: BackendEnvironmentKind,
        flag_id: str,
        context: EvaluationContext,
    ) -> EvaluationResult:
        if not isinstance(environment, BackendEnvironmentKind):
            raise RemoteConfigPolicyError("invalid_environment")
        flag_id = _stable_id(flag_id, field="flag_id")
        if not isinstance(context, EvaluationContext):
            raise RemoteConfigPolicyError("invalid_evaluation_context")
        self._authorize(actor, "remote_config.evaluate", flag_id)
        with self._lock:
            if self._evaluation_count >= self.max_evaluations:
                raise RemoteConfigCapacityError("evaluation_capacity")
            snapshot = self.active_snapshot(environment)
            definition = snapshot.flag(flag_id)
            result = self._evaluate_definition(
                snapshot=snapshot,
                definition=definition,
                context=context,
                visiting=set(),
            )
            self._evaluation_count += 1
            self._trace.append(
                {
                    "event": "flag_evaluated",
                    "environment": environment.value,
                    "snapshot_id": snapshot.snapshot_id,
                    "flag_id": flag_id,
                    "variant": result.variant,
                    "reason": result.reason.value,
                    "context_digest": result.context_digest,
                    "evaluation_digest": result.evaluation_digest,
                    "rollout_bucket": result.rollout_bucket,
                    "error_code": result.error_code.value if result.error_code is not None else None,
                }
            )
            return result

    def audit_records(self) -> tuple[ConfigAuditRecord, ...]:
        with self._lock:
            return tuple(self._audit)

    def trace(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            return tuple(dict(item) for item in self._trace)

    def state_snapshot(self) -> RemoteConfigStateSnapshot:
        with self._lock:
            active = tuple(sorted((environment.value, snapshot_id) for environment, snapshot_id in self._active.items()))
            digests = tuple(sorted(snapshot.digest() for snapshot in self._snapshots.values()))
            kill_switches = tuple(sorted((environment.value, flag_id) for environment, flag_id in self._kill_switches))
            audit_digest = canonical_sha256([record.canonical() for record in self._audit])
            trace_digest = canonical_sha256(list(self._trace))
            return RemoteConfigStateSnapshot(
                active_snapshots=active,
                registered_snapshot_digests=digests,
                kill_switches=kill_switches,
                audit_digest=audit_digest,
                trace_digest=trace_digest,
            )


class OpenFeatureRemoteConfigAdapter:
    """Small provider-neutral evaluation boundary inspired by stable OpenFeature concepts."""

    def __init__(
        self,
        *,
        service: InMemoryRemoteConfigService,
        actor: AuthorityActorContext,
        environment: BackendEnvironmentKind,
    ) -> None:
        self.service = service
        self.actor = actor
        self.environment = environment

    def _typed_value(
        self,
        *,
        flag_key: str,
        default: Any,
        expected_type: FlagValueType,
        context: EvaluationContext,
    ) -> Any:
        try:
            result = self.service.evaluate(
                self.actor,
                environment=self.environment,
                flag_id=flag_key,
                context=context,
            )
        except (RemoteConfigPolicyError, RemoteConfigStateError, RemoteConfigAuthorizationError, RemoteConfigCapacityError):
            return default
        if result.value_type is not expected_type:
            return default
        return result.value

    def get_boolean_value(self, flag_key: str, default: bool, context: EvaluationContext) -> bool:
        if not isinstance(default, bool):
            raise RemoteConfigPolicyError("boolean_default_type_mismatch")
        return bool(
            self._typed_value(
                flag_key=flag_key,
                default=default,
                expected_type=FlagValueType.BOOLEAN,
                context=context,
            )
        )

    def get_integer_value(self, flag_key: str, default: int, context: EvaluationContext) -> int:
        if isinstance(default, bool) or not isinstance(default, int):
            raise RemoteConfigPolicyError("integer_default_type_mismatch")
        value = self._typed_value(
            flag_key=flag_key,
            default=default,
            expected_type=FlagValueType.INTEGER,
            context=context,
        )
        return int(value)

    def get_number_value(self, flag_key: str, default: float, context: EvaluationContext) -> float:
        if isinstance(default, bool) or not isinstance(default, (int, float)):
            raise RemoteConfigPolicyError("number_default_type_mismatch")
        value = self._typed_value(
            flag_key=flag_key,
            default=default,
            expected_type=FlagValueType.NUMBER,
            context=context,
        )
        return float(value)

    def get_string_value(self, flag_key: str, default: str, context: EvaluationContext) -> str:
        if not isinstance(default, str):
            raise RemoteConfigPolicyError("string_default_type_mismatch")
        value = self._typed_value(
            flag_key=flag_key,
            default=default,
            expected_type=FlagValueType.STRING,
            context=context,
        )
        return str(value)

    def get_object_value(self, flag_key: str, default: Any, context: EvaluationContext) -> Any:
        default_copy = _typed_value(FlagValueType.OBJECT, default, field="object_default")
        value = self._typed_value(
            flag_key=flag_key,
            default=default_copy,
            expected_type=FlagValueType.OBJECT,
            context=context,
        )
        return _canonical_json_copy(value, field="object_result")
