from __future__ import annotations

import hashlib

import pytest

from kodepoia.backend.contracts import BackendEnvironmentKind, canonical_json_bytes
from kodepoia.backend.resilience import (
    BackupArtifact,
    Bulkhead,
    CircuitBreaker,
    CircuitState,
    DependencyHealth,
    DependencyState,
    DisasterRecoveryPolicy,
    FailureAction,
    FailureInjector,
    FailureRule,
    GracefulDrain,
    IsolatedRestoreRunner,
    LoadObservation,
    LoadProfile,
    OtelServiceObservation,
    ResilienceCapacityError,
    ResiliencePolicyError,
    ResilienceStateError,
    ResilientExecutor,
    RetryPolicy,
    ServiceHealthSnapshot,
    ServiceHealthState,
    TokenBucketRateLimiter,
    evaluate_load,
)


class Clock:
    def __init__(self, value: int = 0) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value

    def advance(self, milliseconds: int) -> None:
        self.value += milliseconds


def test_dependency_health_aggregates_required_and_optional_states() -> None:
    ready = DependencyHealth("db", DependencyState.READY, required=True)
    optional_down = DependencyHealth("cdn", DependencyState.UNAVAILABLE, required=False)
    required_down = DependencyHealth("events", DependencyState.FAILED, required=True)

    degraded = ServiceHealthSnapshot.from_dependencies(
        service_id="api",
        environment=BackendEnvironmentKind.TEST,
        dependencies=(ready, optional_down),
        generated_at_ms=10,
    )
    unavailable = ServiceHealthSnapshot.from_dependencies(
        service_id="api",
        environment=BackendEnvironmentKind.TEST,
        dependencies=(ready, required_down),
        generated_at_ms=11,
    )

    assert degraded.state is ServiceHealthState.DEGRADED
    assert unavailable.state is ServiceHealthState.UNAVAILABLE
    assert degraded.digest() != unavailable.digest()


def test_service_health_rejects_false_ready_claim() -> None:
    dep = DependencyHealth("db", DependencyState.DEGRADED)
    with pytest.raises(ResiliencePolicyError, match="does not match"):
        ServiceHealthSnapshot(
            service_id="api",
            environment=BackendEnvironmentKind.TEST,
            state=ServiceHealthState.READY,
            dependencies=(dep,),
            generated_at_ms=0,
        )


def test_otel_observation_derives_health_without_payloads() -> None:
    healthy = OtelServiceObservation(
        service_name="matchmaking",
        request_count=100,
        error_count=1,
        p95_latency_ms=75,
        max_p95_latency_ms=100,
        max_error_rate=0.02,
    ).dependency_health()
    degraded = OtelServiceObservation(
        service_name="content",
        request_count=50,
        error_count=5,
        p95_latency_ms=110,
        max_p95_latency_ms=100,
        max_error_rate=0.02,
    ).dependency_health(required=False)

    assert healthy.state is DependencyState.READY
    assert healthy.error_rate == 0.01
    assert degraded.state is DependencyState.DEGRADED
    assert degraded.detail_code == "budget_exceeded"


def test_retry_policy_is_bounded_and_jitter_is_deterministic() -> None:
    policy = RetryPolicy(
        max_attempts=3,
        base_delay_ms=100,
        max_delay_ms=500,
        jitter_ratio=1.0,
        attempt_timeout_ms=500,
        total_timeout_ms=2_000,
    )
    first = policy.delay_ms("op", 1)
    assert 0 <= first <= 100
    assert first == policy.delay_ms("op", 1)
    assert policy.worst_case_duration_ms() == 1_800

    with pytest.raises(ResiliencePolicyError, match="worst-case"):
        RetryPolicy(
            max_attempts=3,
            base_delay_ms=100,
            max_delay_ms=500,
            attempt_timeout_ms=1_000,
            total_timeout_ms=3_000,
        )


def test_resilient_executor_retries_transient_idempotent_failure() -> None:
    clock = Clock(100)
    slept: list[int] = []
    injector = FailureInjector(
        (
            FailureRule("db", 1, FailureAction.TIMEOUT),
            FailureRule("db", 2, FailureAction.FAIL),
        )
    )
    executor = ResilientExecutor(
        clock_ms=clock,
        sleeper_ms=slept.append,
        failure_injector=injector,
    )
    limiter = TokenBucketRateLimiter(capacity=10, refill_per_second=1, clock_ms=clock)
    circuit = CircuitBreaker(failure_threshold=5, recovery_timeout_ms=1_000)
    bulkhead = Bulkhead(max_concurrent=1)
    policy = RetryPolicy(
        max_attempts=3,
        base_delay_ms=20,
        max_delay_ms=100,
        attempt_timeout_ms=100,
        total_timeout_ms=400,
    )

    result, evidence = executor.run(
        operation_id="db-read",
        dependency_id="db",
        operation=lambda: "ok",
        retry_policy=policy,
        circuit=circuit,
        rate_limiter=limiter,
        bulkhead=bulkhead,
        transient=lambda exc: isinstance(exc, (TimeoutError, ConnectionError)),
    )

    assert result == "ok"
    assert evidence.succeeded is True
    assert evidence.attempts == 3
    assert tuple(slept) == evidence.delays_ms
    assert len(injector.timeline) == 3
    assert bulkhead.active == 0


def test_retry_refuses_non_idempotent_operation() -> None:
    clock = Clock()
    executor = ResilientExecutor(clock_ms=clock)
    with pytest.raises(ResiliencePolicyError, match="idempotent"):
        executor.run(
            operation_id="purchase",
            dependency_id="billing",
            operation=lambda: "never",
            retry_policy=RetryPolicy(),
            circuit=CircuitBreaker(),
            rate_limiter=TokenBucketRateLimiter(capacity=5, refill_per_second=1, clock_ms=clock),
            bulkhead=Bulkhead(max_concurrent=1),
            transient=lambda exc: True,
            idempotent=False,
        )


def test_circuit_breaker_opens_then_half_opens_then_closes() -> None:
    circuit = CircuitBreaker(failure_threshold=2, recovery_timeout_ms=100, half_open_successes=1)
    circuit.record_failure(10)
    assert circuit.state is CircuitState.CLOSED
    circuit.record_failure(20)
    assert circuit.state is CircuitState.OPEN
    assert circuit.allow(119) is False
    assert circuit.allow(120) is True
    assert circuit.state is CircuitState.HALF_OPEN
    circuit.record_success()
    assert circuit.state is CircuitState.CLOSED


def test_circuit_half_open_failure_reopens() -> None:
    circuit = CircuitBreaker(failure_threshold=1, recovery_timeout_ms=10)
    circuit.record_failure(0)
    assert circuit.allow(10) is True
    circuit.record_failure(10)
    assert circuit.state is CircuitState.OPEN


def test_rate_limiter_refills_and_bounds_requests() -> None:
    clock = Clock(0)
    limiter = TokenBucketRateLimiter(capacity=2, refill_per_second=2, clock_ms=clock)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False
    clock.advance(500)
    assert limiter.allow() is True


def test_bulkhead_and_graceful_drain_fail_closed() -> None:
    bulkhead = Bulkhead(max_concurrent=1)
    bulkhead.enter()
    with pytest.raises(ResilienceCapacityError, match="bulkhead_capacity"):
        bulkhead.enter()
    bulkhead.leave()

    drain = GracefulDrain(max_active=2)
    drain.enter()
    drain.begin()
    with pytest.raises(ResilienceStateError, match="draining"):
        drain.enter()
    assert drain.drained is False
    drain.leave()
    assert drain.drained is True


def test_failure_timeline_is_bounded_and_digest_stable() -> None:
    injector = FailureInjector(max_timeline_records=2)
    assert injector.action_for("db") is FailureAction.PASS
    assert injector.action_for("db") is FailureAction.PASS
    assert injector.action_for("db") is FailureAction.PASS
    assert len(injector.timeline) == 2
    assert injector.dropped_timeline_records == 1
    assert len(injector.timeline_digest()) == 64


def test_backup_restore_verifies_hash_and_rpo_rto_in_isolated_test() -> None:
    clock = Clock(1_000)
    payload = {"accounts": [{"id": "a1", "revision": 3}], "events": [1, 2]}
    schema_digest = hashlib.sha256(b"schema").hexdigest()
    backup = BackupArtifact.create(
        backup_id="backup-1",
        source_id="postgres-fixture",
        environment=BackendEnvironmentKind.TEST,
        created_at_ms=900,
        schema_digest=schema_digest,
        payload=payload,
        encrypted=True,
    )
    policy = DisasterRecoveryPolicy(
        max_rpo_ms=200,
        max_rto_ms=50,
        require_encrypted_backup=True,
    )

    restored, evidence = IsolatedRestoreRunner(clock_ms=clock).restore(
        backup,
        policy=policy,
        target_environment=BackendEnvironmentKind.TEST,
        restore_duration_ms=25,
    )

    assert dict(restored) == payload
    assert evidence.passed is True
    assert evidence.rpo_ms == 100
    assert evidence.rto_ms == 25
    assert evidence.restored_payload_sha256 == hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def test_restore_rejects_untrusted_or_production_target() -> None:
    clock = Clock(1_000)
    digest = hashlib.sha256(b"schema").hexdigest()
    backup = BackupArtifact.create(
        backup_id="backup-x",
        source_id="db",
        environment=BackendEnvironmentKind.TEST,
        created_at_ms=900,
        schema_digest=digest,
        payload={"x": 1},
        provenance="foreign_dump",
    )
    runner = IsolatedRestoreRunner(clock_ms=clock)
    with pytest.raises(ResiliencePolicyError, match="provenance"):
        runner.restore(
            backup,
            policy=DisasterRecoveryPolicy(max_rpo_ms=200, max_rto_ms=50),
            target_environment=BackendEnvironmentKind.TEST,
            restore_duration_ms=10,
        )
    trusted = BackupArtifact.create(
        backup_id="backup-y",
        source_id="db",
        environment=BackendEnvironmentKind.TEST,
        created_at_ms=900,
        schema_digest=digest,
        payload={"x": 1},
    )
    with pytest.raises(ResiliencePolicyError, match="LOCAL or TEST"):
        runner.restore(
            trusted,
            policy=DisasterRecoveryPolicy(max_rpo_ms=200, max_rto_ms=50),
            target_environment=BackendEnvironmentKind.PRODUCTION,
            restore_duration_ms=10,
        )


def test_restore_detects_rpo_and_rto_budget_failure_without_faking_pass() -> None:
    clock = Clock(10_000)
    backup = BackupArtifact.create(
        backup_id="backup-old",
        source_id="db",
        environment=BackendEnvironmentKind.TEST,
        created_at_ms=0,
        schema_digest=hashlib.sha256(b"schema").hexdigest(),
        payload={"state": "accepted"},
    )
    _restored, evidence = IsolatedRestoreRunner(clock_ms=clock).restore(
        backup,
        policy=DisasterRecoveryPolicy(max_rpo_ms=100, max_rto_ms=50),
        target_environment=BackendEnvironmentKind.TEST,
        restore_duration_ms=75,
    )
    assert evidence.within_rpo is False
    assert evidence.within_rto is False
    assert evidence.passed is False


def test_load_budget_is_profile_evidence_not_universal_claim() -> None:
    profile = LoadProfile(
        profile_id="ci-small",
        request_count=100,
        max_concurrency=8,
        max_p95_latency_ms=120,
        max_error_rate=0.01,
        max_cpu_ms=500,
        max_memory_mb=256,
    )
    observation = LoadObservation(
        request_count=100,
        peak_concurrency=4,
        p95_latency_ms=90,
        error_count=1,
        cpu_ms=400,
        memory_mb=128,
    )
    result = evaluate_load(profile, observation)
    assert result.passed is True
    assert len(result.profile_digest) == 64

    bad = evaluate_load(
        profile,
        LoadObservation(
            request_count=100,
            peak_concurrency=9,
            p95_latency_ms=121,
            error_count=2,
            cpu_ms=501,
            memory_mb=257,
        ),
    )
    assert bad.passed is False
    assert bad.concurrency_ok is False
    assert bad.error_rate_ok is False


def test_executor_fails_fast_when_circuit_is_open() -> None:
    clock = Clock(0)
    circuit = CircuitBreaker(failure_threshold=1, recovery_timeout_ms=100)
    circuit.record_failure(0)
    executor = ResilientExecutor(clock_ms=clock)
    with pytest.raises(ResilienceStateError, match="circuit_open"):
        executor.run(
            operation_id="op",
            dependency_id="db",
            operation=lambda: "never",
            retry_policy=RetryPolicy(max_attempts=1, attempt_timeout_ms=10, total_timeout_ms=10),
            circuit=circuit,
            rate_limiter=TokenBucketRateLimiter(capacity=2, refill_per_second=1, clock_ms=clock),
            bulkhead=Bulkhead(max_concurrent=1),
            transient=lambda exc: True,
        )


def test_executor_rate_limit_prevents_retry_storm() -> None:
    clock = Clock(0)
    injector = FailureInjector((FailureRule("db", 1, FailureAction.FAIL),))
    executor = ResilientExecutor(clock_ms=clock, failure_injector=injector)
    with pytest.raises(ResilienceCapacityError, match="rate_limit"):
        executor.run(
            operation_id="op",
            dependency_id="db",
            operation=lambda: "never",
            retry_policy=RetryPolicy(
                max_attempts=2,
                base_delay_ms=1,
                max_delay_ms=1,
                attempt_timeout_ms=10,
                total_timeout_ms=21,
            ),
            circuit=CircuitBreaker(failure_threshold=5),
            rate_limiter=TokenBucketRateLimiter(capacity=1, refill_per_second=0.001, clock_ms=clock),
            bulkhead=Bulkhead(max_concurrent=1),
            transient=lambda exc: isinstance(exc, ConnectionError),
        )
