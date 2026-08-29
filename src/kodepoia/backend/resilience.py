from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence, TypeVar

from .contracts import BackendEnvironmentKind, canonical_json_bytes, canonical_sha256

_T = TypeVar("_T")


class ResiliencePolicyError(ValueError):
    pass


class ResilienceStateError(RuntimeError):
    pass


class ResilienceCapacityError(ResilienceStateError):
    pass


class DependencyState(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class ServiceHealthState(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class FailureAction(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    TIMEOUT = "timeout"


def _stable_id(value: str, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or not value
        or len(value) > 191
        or any(not (char.isalnum() or char in "._-") for char in value)
    ):
        raise ResiliencePolicyError(f"{field} must be a stable identifier")
    return value


def _positive_int(value: int, *, field: str, maximum: int = 2**31 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ResiliencePolicyError(f"{field} must be an integer in [1, {maximum}]")
    return value


def _non_negative_int(value: int, *, field: str, maximum: int = 2**63 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ResiliencePolicyError(f"{field} must be an integer in [0, {maximum}]")
    return value


def _bounded_float(value: float, *, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ResiliencePolicyError(f"{field} must be finite")
    normalized = float(value)
    if not minimum <= normalized <= maximum:
        raise ResiliencePolicyError(f"{field} must be in [{minimum}, {maximum}]")
    return normalized


def _freeze_mapping(value: Mapping[str, Any], *, field: str, max_bytes: int = 64 * 1024) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ResiliencePolicyError(f"{field} must be a mapping")
    normalized = {str(key): item for key, item in value.items()}
    encoded = canonical_json_bytes(normalized)
    if len(encoded) > max_bytes:
        raise ResiliencePolicyError(f"{field} exceeds {max_bytes} bytes")
    return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class DependencyHealth:
    dependency_id: str
    state: DependencyState
    required: bool = True
    latency_ms: float | None = None
    error_rate: float | None = None
    detail_code: str = "ok"

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependency_id", _stable_id(self.dependency_id, field="dependency_id"))
        object.__setattr__(self, "detail_code", _stable_id(self.detail_code, field="detail_code"))
        if not isinstance(self.state, DependencyState):
            raise ResiliencePolicyError("state must be DependencyState")
        if not isinstance(self.required, bool):
            raise ResiliencePolicyError("required must be boolean")
        if self.latency_ms is not None:
            object.__setattr__(
                self,
                "latency_ms",
                _bounded_float(self.latency_ms, field="latency_ms", minimum=0.0, maximum=86_400_000.0),
            )
        if self.error_rate is not None:
            object.__setattr__(
                self,
                "error_rate",
                _bounded_float(self.error_rate, field="error_rate", minimum=0.0, maximum=1.0),
            )

    def canonical(self) -> dict[str, Any]:
        return {
            "dependency_id": self.dependency_id,
            "state": self.state.value,
            "required": self.required,
            "latency_ms": self.latency_ms,
            "error_rate": self.error_rate,
            "detail_code": self.detail_code,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ServiceHealthSnapshot:
    service_id: str
    environment: BackendEnvironmentKind
    state: ServiceHealthState
    dependencies: tuple[DependencyHealth, ...]
    generated_at_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "service_id", _stable_id(self.service_id, field="service_id"))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise ResiliencePolicyError("environment must be BackendEnvironmentKind")
        if not isinstance(self.state, ServiceHealthState):
            raise ResiliencePolicyError("state must be ServiceHealthState")
        object.__setattr__(self, "generated_at_ms", _non_negative_int(self.generated_at_ms, field="generated_at_ms"))
        if not isinstance(self.dependencies, tuple):
            raise ResiliencePolicyError("dependencies must be tuple")
        if any(not isinstance(item, DependencyHealth) for item in self.dependencies):
            raise ResiliencePolicyError("dependencies contain invalid item")
        ids = [item.dependency_id for item in self.dependencies]
        if len(ids) != len(set(ids)):
            raise ResiliencePolicyError("duplicate dependency health")
        object.__setattr__(self, "dependencies", tuple(sorted(self.dependencies, key=lambda item: item.dependency_id)))
        if self.state is not self.derive_state(self.dependencies):
            raise ResiliencePolicyError("service state does not match dependency evidence")

    @staticmethod
    def derive_state(dependencies: Sequence[DependencyHealth]) -> ServiceHealthState:
        if any(
            item.required and item.state in {DependencyState.UNAVAILABLE, DependencyState.FAILED}
            for item in dependencies
        ):
            return ServiceHealthState.UNAVAILABLE
        if any(item.state is not DependencyState.READY for item in dependencies):
            return ServiceHealthState.DEGRADED
        return ServiceHealthState.READY

    @classmethod
    def from_dependencies(
        cls,
        *,
        service_id: str,
        environment: BackendEnvironmentKind,
        dependencies: Sequence[DependencyHealth],
        generated_at_ms: int,
    ) -> "ServiceHealthSnapshot":
        values = tuple(dependencies)
        return cls(
            service_id=service_id,
            environment=environment,
            state=cls.derive_state(values),
            dependencies=values,
            generated_at_ms=generated_at_ms,
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "environment": self.environment.value,
            "state": self.state.value,
            "dependencies": [item.canonical() for item in self.dependencies],
            "generated_at_ms": self.generated_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class OtelServiceObservation:
    service_name: str
    request_count: int
    error_count: int
    p95_latency_ms: float
    max_p95_latency_ms: float
    max_error_rate: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "service_name", _stable_id(self.service_name, field="service_name"))
        object.__setattr__(self, "request_count", _non_negative_int(self.request_count, field="request_count"))
        object.__setattr__(self, "error_count", _non_negative_int(self.error_count, field="error_count"))
        if self.error_count > self.request_count:
            raise ResiliencePolicyError("error_count cannot exceed request_count")
        object.__setattr__(
            self,
            "p95_latency_ms",
            _bounded_float(self.p95_latency_ms, field="p95_latency_ms", minimum=0.0, maximum=86_400_000.0),
        )
        object.__setattr__(
            self,
            "max_p95_latency_ms",
            _bounded_float(
                self.max_p95_latency_ms,
                field="max_p95_latency_ms",
                minimum=0.001,
                maximum=86_400_000.0,
            ),
        )
        object.__setattr__(
            self,
            "max_error_rate",
            _bounded_float(self.max_error_rate, field="max_error_rate", minimum=0.0, maximum=1.0),
        )

    @property
    def error_rate(self) -> float:
        return 0.0 if self.request_count == 0 else self.error_count / self.request_count

    def dependency_health(self, *, required: bool = True) -> DependencyHealth:
        if self.request_count == 0:
            state = DependencyState.DEGRADED
            detail = "no_samples"
        elif self.error_rate > self.max_error_rate or self.p95_latency_ms > self.max_p95_latency_ms:
            state = DependencyState.DEGRADED
            detail = "budget_exceeded"
        else:
            state = DependencyState.READY
            detail = "within_budget"
        return DependencyHealth(
            dependency_id=self.service_name,
            state=state,
            required=required,
            latency_ms=self.p95_latency_ms,
            error_rate=round(self.error_rate, 8),
            detail_code=detail,
        )


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_ms: int = 50
    max_delay_ms: int = 2_000
    jitter_ratio: float = 1.0
    attempt_timeout_ms: int = 1_000
    total_timeout_ms: int = 5_000

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_attempts", _positive_int(self.max_attempts, field="max_attempts", maximum=9))
        object.__setattr__(
            self, "base_delay_ms", _positive_int(self.base_delay_ms, field="base_delay_ms", maximum=60_000)
        )
        object.__setattr__(
            self, "max_delay_ms", _positive_int(self.max_delay_ms, field="max_delay_ms", maximum=600_000)
        )
        if self.max_delay_ms < self.base_delay_ms:
            raise ResiliencePolicyError("max_delay_ms cannot be below base_delay_ms")
        object.__setattr__(
            self,
            "jitter_ratio",
            _bounded_float(self.jitter_ratio, field="jitter_ratio", minimum=0.0, maximum=1.0),
        )
        object.__setattr__(
            self,
            "attempt_timeout_ms",
            _positive_int(self.attempt_timeout_ms, field="attempt_timeout_ms", maximum=600_000),
        )
        object.__setattr__(
            self,
            "total_timeout_ms",
            _positive_int(self.total_timeout_ms, field="total_timeout_ms", maximum=3_600_000),
        )
        if self.worst_case_duration_ms() > self.total_timeout_ms:
            raise ResiliencePolicyError("retry policy worst-case duration exceeds total_timeout_ms")

    def worst_case_duration_ms(self) -> int:
        delays = sum(
            min(self.max_delay_ms, self.base_delay_ms * (2 ** max(0, attempt - 1)))
            for attempt in range(1, self.max_attempts)
        )
        return (self.max_attempts * self.attempt_timeout_ms) + delays

    def delay_ms(self, operation_id: str, attempt: int) -> int:
        _stable_id(operation_id, field="operation_id")
        attempt = _positive_int(attempt, field="attempt", maximum=self.max_attempts)
        ceiling = min(self.max_delay_ms, self.base_delay_ms * (2 ** max(0, attempt - 1)))
        if self.jitter_ratio == 0.0:
            return ceiling
        digest = hashlib.sha256(f"{operation_id}:{attempt}".encode("utf-8")).digest()
        unit = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
        floor = ceiling * (1.0 - self.jitter_ratio)
        return int(round(floor + ((ceiling - floor) * unit)))


@dataclass(frozen=True, slots=True)
class RetryEvidence:
    operation_id: str
    attempts: int
    succeeded: bool
    delays_ms: tuple[int, ...]
    terminal_code: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_id", _stable_id(self.operation_id, field="operation_id"))
        object.__setattr__(self, "attempts", _positive_int(self.attempts, field="attempts", maximum=64))
        object.__setattr__(self, "terminal_code", _stable_id(self.terminal_code, field="terminal_code"))
        if len(self.delays_ms) != max(0, self.attempts - 1):
            raise ResiliencePolicyError("retry delay count must equal attempts - 1")
        if any(_non_negative_int(item, field="retry_delay_ms", maximum=600_000) != item for item in self.delays_ms):
            raise ResiliencePolicyError("invalid retry delay")

    def canonical(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "attempts": self.attempts,
            "succeeded": self.succeeded,
            "delays_ms": list(self.delays_ms),
            "terminal_code": self.terminal_code,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        recovery_timeout_ms: int = 5_000,
        half_open_successes: int = 1,
    ) -> None:
        self.failure_threshold = _positive_int(failure_threshold, field="failure_threshold", maximum=1000)
        self.recovery_timeout_ms = _positive_int(
            recovery_timeout_ms, field="recovery_timeout_ms", maximum=86_400_000
        )
        self.half_open_successes = _positive_int(
            half_open_successes, field="half_open_successes", maximum=1000
        )
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at_ms: int | None = None

    def allow(self, now_ms: int) -> bool:
        now_ms = _non_negative_int(now_ms, field="now_ms")
        if self.state is CircuitState.OPEN:
            assert self.opened_at_ms is not None
            if now_ms - self.opened_at_ms >= self.recovery_timeout_ms:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        return True

    def record_success(self) -> None:
        if self.state is CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_successes:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.opened_at_ms = None
            return
        self.failure_count = 0

    def record_failure(self, now_ms: int) -> None:
        now_ms = _non_negative_int(now_ms, field="now_ms")
        if self.state is CircuitState.HALF_OPEN:
            self._open(now_ms)
            return
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self._open(now_ms)

    def _open(self, now_ms: int) -> None:
        self.state = CircuitState.OPEN
        self.opened_at_ms = now_ms
        self.success_count = 0


class TokenBucketRateLimiter:
    def __init__(self, *, capacity: int, refill_per_second: float, clock_ms: Callable[[], int]) -> None:
        self.capacity = _positive_int(capacity, field="capacity", maximum=1_000_000)
        self.refill_per_second = _bounded_float(
            refill_per_second, field="refill_per_second", minimum=0.001, maximum=1_000_000.0
        )
        self.clock_ms = clock_ms
        self.tokens = float(self.capacity)
        self.last_ms = _non_negative_int(clock_ms(), field="clock_ms")

    def allow(self, *, cost: int = 1) -> bool:
        cost = _positive_int(cost, field="cost", maximum=self.capacity)
        now = _non_negative_int(self.clock_ms(), field="clock_ms")
        elapsed = max(0, now - self.last_ms)
        self.tokens = min(self.capacity, self.tokens + (elapsed / 1000.0) * self.refill_per_second)
        self.last_ms = now
        if self.tokens + 1e-12 < cost:
            return False
        self.tokens -= cost
        return True


class Bulkhead:
    def __init__(self, *, max_concurrent: int) -> None:
        self.max_concurrent = _positive_int(max_concurrent, field="max_concurrent", maximum=1_000_000)
        self.active = 0

    def enter(self) -> None:
        if self.active >= self.max_concurrent:
            raise ResilienceCapacityError("bulkhead_capacity")
        self.active += 1

    def leave(self) -> None:
        if self.active <= 0:
            raise ResilienceStateError("bulkhead_underflow")
        self.active -= 1


class GracefulDrain:
    def __init__(self, *, max_active: int) -> None:
        self.max_active = _positive_int(max_active, field="max_active", maximum=1_000_000)
        self.active = 0
        self.accepting = True

    def enter(self) -> None:
        if not self.accepting:
            raise ResilienceStateError("service_draining")
        if self.active >= self.max_active:
            raise ResilienceCapacityError("active_request_capacity")
        self.active += 1

    def leave(self) -> None:
        if self.active <= 0:
            raise ResilienceStateError("active_request_underflow")
        self.active -= 1

    def begin(self) -> None:
        self.accepting = False

    @property
    def drained(self) -> bool:
        return not self.accepting and self.active == 0


@dataclass(frozen=True, slots=True)
class FailureRule:
    dependency_id: str
    invocation: int
    action: FailureAction

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependency_id", _stable_id(self.dependency_id, field="dependency_id"))
        object.__setattr__(self, "invocation", _positive_int(self.invocation, field="invocation", maximum=1_000_000))
        if not isinstance(self.action, FailureAction):
            raise ResiliencePolicyError("action must be FailureAction")


class FailureInjector:
    def __init__(self, rules: Sequence[FailureRule] = (), *, max_timeline_records: int = 256) -> None:
        keys = [(item.dependency_id, item.invocation) for item in rules]
        if len(keys) != len(set(keys)):
            raise ResiliencePolicyError("duplicate failure rule")
        self.rules = {(item.dependency_id, item.invocation): item.action for item in rules}
        self.max_timeline_records = _positive_int(
            max_timeline_records, field="max_timeline_records", maximum=1_000_000
        )
        self.counts: dict[str, int] = {}
        self.timeline: list[dict[str, Any]] = []
        self.dropped_timeline_records = 0

    def action_for(self, dependency_id: str) -> FailureAction:
        dependency_id = _stable_id(dependency_id, field="dependency_id")
        invocation = self.counts.get(dependency_id, 0) + 1
        self.counts[dependency_id] = invocation
        action = self.rules.get((dependency_id, invocation), FailureAction.PASS)
        record = {
            "dependency_id": dependency_id,
            "invocation": invocation,
            "action": action.value,
        }
        if len(self.timeline) >= self.max_timeline_records:
            self.timeline.pop(0)
            self.dropped_timeline_records += 1
        self.timeline.append(record)
        return action

    def timeline_digest(self) -> str:
        return canonical_sha256(self.timeline)


class ResilientExecutor:
    def __init__(
        self,
        *,
        clock_ms: Callable[[], int],
        sleeper_ms: Callable[[int], None] | None = None,
        failure_injector: FailureInjector | None = None,
    ) -> None:
        self.clock_ms = clock_ms
        self.sleeper_ms = sleeper_ms or (lambda _delay: None)
        self.failure_injector = failure_injector or FailureInjector()

    def run(
        self,
        *,
        operation_id: str,
        dependency_id: str,
        operation: Callable[[], _T],
        retry_policy: RetryPolicy,
        circuit: CircuitBreaker,
        rate_limiter: TokenBucketRateLimiter,
        bulkhead: Bulkhead,
        transient: Callable[[Exception], bool],
        idempotent: bool = True,
    ) -> tuple[_T, RetryEvidence]:
        operation_id = _stable_id(operation_id, field="operation_id")
        dependency_id = _stable_id(dependency_id, field="dependency_id")
        if not isinstance(idempotent, bool):
            raise ResiliencePolicyError("idempotent must be boolean")
        if retry_policy.max_attempts > 1 and not idempotent:
            raise ResiliencePolicyError("retries require an idempotent operation")
        delays: list[int] = []
        for attempt in range(1, retry_policy.max_attempts + 1):
            now = _non_negative_int(self.clock_ms(), field="clock_ms")
            if not rate_limiter.allow():
                raise ResilienceCapacityError("rate_limit")
            if not circuit.allow(now):
                raise ResilienceStateError("circuit_open")
            bulkhead.enter()
            try:
                action = self.failure_injector.action_for(dependency_id)
                if action is FailureAction.FAIL:
                    raise ConnectionError("injected_failure")
                if action is FailureAction.TIMEOUT:
                    raise TimeoutError("injected_timeout")
                result = operation()
            except Exception as exc:
                circuit.record_failure(now)
                if not transient(exc) or attempt >= retry_policy.max_attempts:
                    raise
                delay = retry_policy.delay_ms(operation_id, attempt)
                delays.append(delay)
                self.sleeper_ms(delay)
            else:
                circuit.record_success()
                return result, RetryEvidence(
                    operation_id=operation_id,
                    attempts=attempt,
                    succeeded=True,
                    delays_ms=tuple(delays),
                    terminal_code="ok",
                )
            finally:
                bulkhead.leave()
        raise AssertionError("unreachable")


@dataclass(frozen=True, slots=True)
class BackupArtifact:
    backup_id: str
    source_id: str
    environment: BackendEnvironmentKind
    created_at_ms: int
    schema_digest: str
    payload_sha256: str
    payload: bytes
    encrypted: bool
    provenance: str = "kodepoia_fixture"

    def __post_init__(self) -> None:
        for field in ("backup_id", "source_id", "provenance"):
            object.__setattr__(self, field, _stable_id(getattr(self, field), field=field))
        if not isinstance(self.environment, BackendEnvironmentKind):
            raise ResiliencePolicyError("environment must be BackendEnvironmentKind")
        object.__setattr__(self, "created_at_ms", _non_negative_int(self.created_at_ms, field="created_at_ms"))
        if not isinstance(self.schema_digest, str) or len(self.schema_digest) != 64:
            raise ResiliencePolicyError("schema_digest must be SHA-256")
        if not isinstance(self.payload_sha256, str) or len(self.payload_sha256) != 64:
            raise ResiliencePolicyError("payload_sha256 must be SHA-256")
        if hashlib.sha256(self.payload).hexdigest() != self.payload_sha256:
            raise ResiliencePolicyError("backup payload digest mismatch")
        if not isinstance(self.encrypted, bool):
            raise ResiliencePolicyError("encrypted must be boolean")

    @classmethod
    def create(
        cls,
        *,
        backup_id: str,
        source_id: str,
        environment: BackendEnvironmentKind,
        created_at_ms: int,
        schema_digest: str,
        payload: Mapping[str, Any],
        encrypted: bool = False,
        provenance: str = "kodepoia_fixture",
    ) -> "BackupArtifact":
        payload_bytes = canonical_json_bytes(payload)
        return cls(
            backup_id=backup_id,
            source_id=source_id,
            environment=environment,
            created_at_ms=created_at_ms,
            schema_digest=schema_digest,
            payload_sha256=hashlib.sha256(payload_bytes).hexdigest(),
            payload=payload_bytes,
            encrypted=encrypted,
            provenance=provenance,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "source_id": self.source_id,
            "environment": self.environment.value,
            "created_at_ms": self.created_at_ms,
            "schema_digest": self.schema_digest,
            "payload_sha256": self.payload_sha256,
            "payload_bytes": len(self.payload),
            "encrypted": self.encrypted,
            "provenance": self.provenance,
        }

    def digest(self) -> str:
        return canonical_sha256(self.metadata())


@dataclass(frozen=True, slots=True)
class DisasterRecoveryPolicy:
    max_rpo_ms: int
    max_rto_ms: int
    require_encrypted_backup: bool = False
    allowed_provenance: tuple[str, ...] = ("kodepoia_fixture",)

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_rpo_ms", _positive_int(self.max_rpo_ms, field="max_rpo_ms"))
        object.__setattr__(self, "max_rto_ms", _positive_int(self.max_rto_ms, field="max_rto_ms"))
        if not isinstance(self.require_encrypted_backup, bool):
            raise ResiliencePolicyError("require_encrypted_backup must be boolean")
        values = tuple(sorted({_stable_id(item, field="provenance") for item in self.allowed_provenance}))
        if not values:
            raise ResiliencePolicyError("allowed_provenance cannot be empty")
        object.__setattr__(self, "allowed_provenance", values)


@dataclass(frozen=True, slots=True)
class RestoreEvidence:
    backup_digest: str
    restored_payload_sha256: str
    rpo_ms: int
    rto_ms: int
    within_rpo: bool
    within_rto: bool
    isolated: bool
    provider_live_claim: bool = False

    def __post_init__(self) -> None:
        for value in (self.backup_digest, self.restored_payload_sha256):
            if not isinstance(value, str) or len(value) != 64:
                raise ResiliencePolicyError("restore digests must be SHA-256")
        object.__setattr__(self, "rpo_ms", _non_negative_int(self.rpo_ms, field="rpo_ms"))
        object.__setattr__(self, "rto_ms", _non_negative_int(self.rto_ms, field="rto_ms"))
        if not self.isolated:
            raise ResiliencePolicyError("restore evidence must come from an isolated target")
        if self.provider_live_claim:
            raise ResiliencePolicyError("core restore evidence cannot claim live provider state")

    @property
    def passed(self) -> bool:
        return self.within_rpo and self.within_rto and self.isolated and not self.provider_live_claim

    def canonical(self) -> dict[str, Any]:
        return {
            "backup_digest": self.backup_digest,
            "restored_payload_sha256": self.restored_payload_sha256,
            "rpo_ms": self.rpo_ms,
            "rto_ms": self.rto_ms,
            "within_rpo": self.within_rpo,
            "within_rto": self.within_rto,
            "isolated": self.isolated,
            "provider_live_claim": self.provider_live_claim,
            "passed": self.passed,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class IsolatedRestoreRunner:
    def __init__(self, *, clock_ms: Callable[[], int]) -> None:
        self.clock_ms = clock_ms

    def restore(
        self,
        artifact: BackupArtifact,
        *,
        policy: DisasterRecoveryPolicy,
        target_environment: BackendEnvironmentKind,
        restore_duration_ms: int,
    ) -> tuple[Mapping[str, Any], RestoreEvidence]:
        if artifact.provenance not in policy.allowed_provenance:
            raise ResiliencePolicyError("backup provenance is not allowed")
        if policy.require_encrypted_backup and not artifact.encrypted:
            raise ResiliencePolicyError("encrypted backup is required")
        if target_environment not in {BackendEnvironmentKind.LOCAL, BackendEnvironmentKind.TEST}:
            raise ResiliencePolicyError("core restore target must be LOCAL or TEST")
        restore_duration_ms = _non_negative_int(restore_duration_ms, field="restore_duration_ms")
        now = _non_negative_int(self.clock_ms(), field="clock_ms")
        if now < artifact.created_at_ms:
            raise ResilienceStateError("clock precedes backup creation")
        digest = hashlib.sha256(artifact.payload).hexdigest()
        if digest != artifact.payload_sha256:
            raise ResilienceStateError("backup payload failed integrity verification")
        raw = json.loads(artifact.payload.decode("utf-8"))
        if not isinstance(raw, dict):
            raise ResilienceStateError("backup payload must restore to an object")
        rpo_ms = now - artifact.created_at_ms
        evidence = RestoreEvidence(
            backup_digest=artifact.digest(),
            restored_payload_sha256=digest,
            rpo_ms=rpo_ms,
            rto_ms=restore_duration_ms,
            within_rpo=rpo_ms <= policy.max_rpo_ms,
            within_rto=restore_duration_ms <= policy.max_rto_ms,
            isolated=True,
        )
        return MappingProxyType(raw), evidence


@dataclass(frozen=True, slots=True)
class LoadProfile:
    profile_id: str
    request_count: int
    max_concurrency: int
    max_p95_latency_ms: float
    max_error_rate: float
    max_cpu_ms: float
    max_memory_mb: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _stable_id(self.profile_id, field="profile_id"))
        object.__setattr__(
            self, "request_count", _positive_int(self.request_count, field="request_count", maximum=10_000_000)
        )
        object.__setattr__(
            self, "max_concurrency", _positive_int(self.max_concurrency, field="max_concurrency", maximum=100_000)
        )
        for field in ("max_p95_latency_ms", "max_cpu_ms", "max_memory_mb"):
            object.__setattr__(
                self,
                field,
                _bounded_float(getattr(self, field), field=field, minimum=0.001, maximum=10**12),
            )
        object.__setattr__(
            self,
            "max_error_rate",
            _bounded_float(self.max_error_rate, field="max_error_rate", minimum=0.0, maximum=1.0),
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "request_count": self.request_count,
            "max_concurrency": self.max_concurrency,
            "max_p95_latency_ms": self.max_p95_latency_ms,
            "max_error_rate": self.max_error_rate,
            "max_cpu_ms": self.max_cpu_ms,
            "max_memory_mb": self.max_memory_mb,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LoadObservation:
    request_count: int
    peak_concurrency: int
    p95_latency_ms: float
    error_count: int
    cpu_ms: float
    memory_mb: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_count", _positive_int(self.request_count, field="request_count"))
        object.__setattr__(
            self, "peak_concurrency", _positive_int(self.peak_concurrency, field="peak_concurrency")
        )
        object.__setattr__(self, "error_count", _non_negative_int(self.error_count, field="error_count"))
        if self.error_count > self.request_count:
            raise ResiliencePolicyError("error_count cannot exceed request_count")
        for field in ("p95_latency_ms", "cpu_ms", "memory_mb"):
            object.__setattr__(
                self,
                field,
                _bounded_float(getattr(self, field), field=field, minimum=0.0, maximum=10**12),
            )

    @property
    def error_rate(self) -> float:
        return self.error_count / self.request_count


@dataclass(frozen=True, slots=True)
class LoadBudgetResult:
    profile_digest: str
    request_count_match: bool
    concurrency_ok: bool
    latency_ok: bool
    error_rate_ok: bool
    cpu_ok: bool
    memory_ok: bool

    @property
    def passed(self) -> bool:
        return all(
            (
                self.request_count_match,
                self.concurrency_ok,
                self.latency_ok,
                self.error_rate_ok,
                self.cpu_ok,
                self.memory_ok,
            )
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "profile_digest": self.profile_digest,
            "request_count_match": self.request_count_match,
            "concurrency_ok": self.concurrency_ok,
            "latency_ok": self.latency_ok,
            "error_rate_ok": self.error_rate_ok,
            "cpu_ok": self.cpu_ok,
            "memory_ok": self.memory_ok,
            "passed": self.passed,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


def evaluate_load(profile: LoadProfile, observation: LoadObservation) -> LoadBudgetResult:
    return LoadBudgetResult(
        profile_digest=profile.digest(),
        request_count_match=observation.request_count == profile.request_count,
        concurrency_ok=observation.peak_concurrency <= profile.max_concurrency,
        latency_ok=observation.p95_latency_ms <= profile.max_p95_latency_ms,
        error_rate_ok=observation.error_rate <= profile.max_error_rate,
        cpu_ok=observation.cpu_ms <= profile.max_cpu_ms,
        memory_ok=observation.memory_mb <= profile.max_memory_mb,
    )


@dataclass(frozen=True, slots=True)
class ServiceOperationsEvidence:
    health_digest: str
    retry_digest: str
    restore_digest: str
    load_digest: str
    failure_timeline_digest: str
    timeline_records: int
    dropped_timeline_records: int
    provider_live_claim: bool = False
    external_load_required: bool = False
    secrets_exposed: bool = False
    pii_exposed: bool = False
    raw_payloads_exposed: bool = False

    def __post_init__(self) -> None:
        for field in (
            "health_digest",
            "retry_digest",
            "restore_digest",
            "load_digest",
            "failure_timeline_digest",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or len(value) != 64:
                raise ResiliencePolicyError(f"{field} must be SHA-256")
        object.__setattr__(
            self, "timeline_records", _non_negative_int(self.timeline_records, field="timeline_records")
        )
        object.__setattr__(
            self,
            "dropped_timeline_records",
            _non_negative_int(self.dropped_timeline_records, field="dropped_timeline_records"),
        )
        if self.provider_live_claim:
            raise ResiliencePolicyError("core evidence cannot claim provider-live state")
        if any((self.secrets_exposed, self.pii_exposed, self.raw_payloads_exposed)):
            raise ResiliencePolicyError("core evidence must remain redacted")

    def canonical(self) -> dict[str, Any]:
        return {
            "health_digest": self.health_digest,
            "retry_digest": self.retry_digest,
            "restore_digest": self.restore_digest,
            "load_digest": self.load_digest,
            "failure_timeline_digest": self.failure_timeline_digest,
            "timeline_records": self.timeline_records,
            "dropped_timeline_records": self.dropped_timeline_records,
            "provider_live_claim": self.provider_live_claim,
            "external_load_required": self.external_load_required,
            "secrets_exposed": self.secrets_exposed,
            "pii_exposed": self.pii_exposed,
            "raw_payloads_exposed": self.raw_payloads_exposed,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())
