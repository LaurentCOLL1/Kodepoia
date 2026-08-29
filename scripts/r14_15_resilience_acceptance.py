from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from kodepoia.backend.contracts import BackendEnvironmentKind
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
    ResilientExecutor,
    RetryPolicy,
    ServiceHealthSnapshot,
    ServiceHealthState,
    ServiceOperationsEvidence,
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


def _source_sha(value: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError("source SHA must be lowercase 40-hex")
    return value


def build_evidence(source_sha: str) -> dict[str, object]:
    source_sha = _source_sha(source_sha)
    checks: dict[str, bool] = {}

    required_ready = DependencyHealth("postgres", DependencyState.READY, required=True, latency_ms=8, error_rate=0)
    optional_down = DependencyHealth(
        "content",
        DependencyState.UNAVAILABLE,
        required=False,
        latency_ms=250,
        error_rate=1,
        detail_code="fixture_outage",
    )
    required_down = DependencyHealth(
        "events",
        DependencyState.FAILED,
        required=True,
        latency_ms=500,
        error_rate=1,
        detail_code="fixture_failure",
    )
    degraded = ServiceHealthSnapshot.from_dependencies(
        service_id="backend",
        environment=BackendEnvironmentKind.TEST,
        dependencies=(required_ready, optional_down),
        generated_at_ms=1_000,
    )
    unavailable = ServiceHealthSnapshot.from_dependencies(
        service_id="backend",
        environment=BackendEnvironmentKind.TEST,
        dependencies=(required_ready, required_down),
        generated_at_ms=1_001,
    )
    otel = OtelServiceObservation(
        service_name="matchmaking",
        request_count=100,
        error_count=1,
        p95_latency_ms=70,
        max_p95_latency_ms=100,
        max_error_rate=0.02,
    ).dependency_health()
    checks["optional_dependency_degrades"] = degraded.state is ServiceHealthState.DEGRADED
    checks["required_dependency_outage_unavailable"] = unavailable.state is ServiceHealthState.UNAVAILABLE
    checks["otel_service_budget_ready"] = otel.state is DependencyState.READY and otel.error_rate == 0.01

    clock = Clock(2_000)
    slept: list[int] = []
    injector = FailureInjector(
        (
            FailureRule("postgres", 1, FailureAction.TIMEOUT),
            FailureRule("postgres", 2, FailureAction.FAIL),
        ),
        max_timeline_records=8,
    )
    retry_policy = RetryPolicy(
        max_attempts=3,
        base_delay_ms=25,
        max_delay_ms=100,
        jitter_ratio=1.0,
        attempt_timeout_ms=100,
        total_timeout_ms=400,
    )
    circuit = CircuitBreaker(failure_threshold=5, recovery_timeout_ms=100)
    limiter = TokenBucketRateLimiter(capacity=8, refill_per_second=1, clock_ms=clock)
    bulkhead = Bulkhead(max_concurrent=1)
    result, retry = ResilientExecutor(
        clock_ms=clock,
        sleeper_ms=slept.append,
        failure_injector=injector,
    ).run(
        operation_id="postgres-read",
        dependency_id="postgres",
        operation=lambda: "accepted",
        retry_policy=retry_policy,
        circuit=circuit,
        rate_limiter=limiter,
        bulkhead=bulkhead,
        transient=lambda exc: isinstance(exc, (TimeoutError, ConnectionError)),
    )
    checks["retry_transient_recovers"] = result == "accepted" and retry.attempts == 3
    checks["retry_delays_bounded"] = (
        tuple(slept) == retry.delays_ms
        and retry_policy.worst_case_duration_ms() <= retry_policy.total_timeout_ms
        and all(delay <= retry_policy.max_delay_ms for delay in retry.delays_ms)
    )
    checks["retry_jitter_deterministic"] = retry_policy.delay_ms("postgres-read", 1) == retry_policy.delay_ms(
        "postgres-read", 1
    )
    try:
        ResilientExecutor(clock_ms=clock).run(
            operation_id="purchase",
            dependency_id="billing",
            operation=lambda: "invalid",
            retry_policy=RetryPolicy(),
            circuit=CircuitBreaker(),
            rate_limiter=TokenBucketRateLimiter(capacity=4, refill_per_second=1, clock_ms=clock),
            bulkhead=Bulkhead(max_concurrent=1),
            transient=lambda _exc: True,
            idempotent=False,
        )
    except ResiliencePolicyError:
        checks["non_idempotent_retry_rejected"] = True
    else:
        checks["non_idempotent_retry_rejected"] = False

    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_ms=100)
    breaker.record_failure(0)
    breaker.record_failure(1)
    opened = breaker.state is CircuitState.OPEN and breaker.allow(100) is False
    half_open = breaker.allow(101) is True and breaker.state is CircuitState.HALF_OPEN
    breaker.record_success()
    checks["circuit_opens"] = opened
    checks["circuit_recovers"] = half_open and breaker.state is CircuitState.CLOSED

    rate_clock = Clock(0)
    one_token = TokenBucketRateLimiter(capacity=1, refill_per_second=0.001, clock_ms=rate_clock)
    checks["rate_limit_blocks"] = one_token.allow() and not one_token.allow()

    bulk = Bulkhead(max_concurrent=1)
    bulk.enter()
    try:
        bulk.enter()
    except ResilienceCapacityError:
        checks["bulkhead_blocks"] = True
    else:
        checks["bulkhead_blocks"] = False
    finally:
        bulk.leave()

    drain = GracefulDrain(max_active=2)
    drain.enter()
    drain.begin()
    try:
        drain.enter()
    except Exception:
        blocked_new = True
    else:
        blocked_new = False
    drain.leave()
    checks["graceful_drain"] = blocked_new and drain.drained

    schema_digest = hashlib.sha256(b"r14.15-fixture-schema").hexdigest()
    restore_clock = Clock(10_000)
    backup = BackupArtifact.create(
        backup_id="r14.15-backup",
        source_id="postgres-fixture",
        environment=BackendEnvironmentKind.TEST,
        created_at_ms=9_900,
        schema_digest=schema_digest,
        payload={
            "authority": {"revision": 7, "value": "accepted"},
            "events": [{"sequence": 1}, {"sequence": 2}],
        },
        encrypted=True,
    )
    restore_policy = DisasterRecoveryPolicy(
        max_rpo_ms=250,
        max_rto_ms=100,
        require_encrypted_backup=True,
    )
    restored, restore = IsolatedRestoreRunner(clock_ms=restore_clock).restore(
        backup,
        policy=restore_policy,
        target_environment=BackendEnvironmentKind.TEST,
        restore_duration_ms=40,
    )
    checks["backup_integrity_verified"] = hashlib.sha256(backup.payload).hexdigest() == backup.payload_sha256
    checks["restore_payload_matches"] = restored["authority"]["revision"] == 7
    checks["restore_isolated"] = restore.isolated
    checks["rpo_bounded"] = restore.within_rpo and restore.rpo_ms == 100
    checks["rto_bounded"] = restore.within_rto and restore.rto_ms == 40

    foreign = BackupArtifact.create(
        backup_id="foreign",
        source_id="postgres",
        environment=BackendEnvironmentKind.TEST,
        created_at_ms=9_900,
        schema_digest=schema_digest,
        payload={"unsafe": False},
        provenance="foreign_dump",
    )
    try:
        IsolatedRestoreRunner(clock_ms=restore_clock).restore(
            foreign,
            policy=restore_policy,
            target_environment=BackendEnvironmentKind.TEST,
            restore_duration_ms=1,
        )
    except ResiliencePolicyError:
        checks["untrusted_backup_rejected"] = True
    else:
        checks["untrusted_backup_rejected"] = False

    try:
        IsolatedRestoreRunner(clock_ms=restore_clock).restore(
            backup,
            policy=restore_policy,
            target_environment=BackendEnvironmentKind.PRODUCTION,
            restore_duration_ms=1,
        )
    except ResiliencePolicyError:
        checks["production_restore_forbidden"] = True
    else:
        checks["production_restore_forbidden"] = False

    profile = LoadProfile(
        profile_id="ci-bounded",
        request_count=200,
        max_concurrency=8,
        max_p95_latency_ms=120,
        max_error_rate=0.01,
        max_cpu_ms=800,
        max_memory_mb=256,
    )
    observation = LoadObservation(
        request_count=200,
        peak_concurrency=6,
        p95_latency_ms=92,
        error_count=1,
        cpu_ms=620,
        memory_mb=180,
    )
    load = evaluate_load(profile, observation)
    checks["load_budget_pass"] = load.passed
    bad_load = evaluate_load(
        profile,
        LoadObservation(
            request_count=200,
            peak_concurrency=9,
            p95_latency_ms=121,
            error_count=3,
            cpu_ms=801,
            memory_mb=257,
        ),
    )
    checks["load_budget_failure_detected"] = not bad_load.passed

    bounded = FailureInjector(max_timeline_records=2)
    for _ in range(4):
        bounded.action_for("content")
    checks["failure_timeline_bounded"] = len(bounded.timeline) == 2 and bounded.dropped_timeline_records == 2

    operations = ServiceOperationsEvidence(
        health_digest=degraded.digest(),
        retry_digest=retry.digest(),
        restore_digest=restore.digest(),
        load_digest=load.digest(),
        failure_timeline_digest=injector.timeline_digest(),
        timeline_records=len(injector.timeline),
        dropped_timeline_records=injector.dropped_timeline_records,
    )
    checks["evidence_redacted"] = not any(
        (
            operations.secrets_exposed,
            operations.pii_exposed,
            operations.raw_payloads_exposed,
            operations.provider_live_claim,
        )
    )
    checks["no_external_load_claim"] = operations.external_load_required is False

    status = "pass" if checks and all(checks.values()) else "fail"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "source_sha": source_sha,
        "status": status,
        "manual_state": "conditional_not_triggered",
        "provider_live_claim": False,
        "external_load_required": False,
        "secrets_exposed": False,
        "pii_exposed": False,
        "raw_payloads_exposed": False,
        "checks": checks,
        "health": {
            "degraded_digest": degraded.digest(),
            "unavailable_digest": unavailable.digest(),
            "otel_dependency_digest": otel.digest(),
            "dependency_count": len(degraded.dependencies),
        },
        "retry": {
            "digest": retry.digest(),
            "attempts": retry.attempts,
            "delays_ms": list(retry.delays_ms),
            "worst_case_duration_ms": retry_policy.worst_case_duration_ms(),
            "total_timeout_ms": retry_policy.total_timeout_ms,
        },
        "restore": {
            "digest": restore.digest(),
            "backup_digest": backup.digest(),
            "payload_sha256": backup.payload_sha256,
            "rpo_ms": restore.rpo_ms,
            "rto_ms": restore.rto_ms,
            "isolated": restore.isolated,
            "encrypted": backup.encrypted,
            "provenance": backup.provenance,
        },
        "load": {
            "profile_digest": profile.digest(),
            "result_digest": load.digest(),
            "request_count": observation.request_count,
            "peak_concurrency": observation.peak_concurrency,
            "p95_latency_ms": observation.p95_latency_ms,
            "error_rate": observation.error_rate,
            "cpu_ms": observation.cpu_ms,
            "memory_mb": observation.memory_mb,
            "profile_scoped_only": True,
        },
        "failure_injection": {
            "timeline_digest": injector.timeline_digest(),
            "timeline_records": len(injector.timeline),
            "dropped_timeline_records": injector.dropped_timeline_records,
            "bounded_fixture_timeline_digest": bounded.timeline_digest(),
        },
        "operations_digest": operations.digest(),
        "compatibility": {
            "postgresql_backup_scope": "fixture_restore_only",
            "postgresql_pitr_claim": False,
            "otel_semantic_conventions": "service.name-compatible observation",
            "internet_scale_claim": False,
            "multi_region_claim": False,
        },
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    evidence = build_evidence(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if evidence["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
