from __future__ import annotations

import kodepoia.backend as backend


def test_r14_15_resilience_exports_are_public() -> None:
    expected = {
        "BackupArtifact",
        "Bulkhead",
        "CircuitBreaker",
        "CircuitState",
        "DependencyHealth",
        "DependencyState",
        "DisasterRecoveryPolicy",
        "FailureAction",
        "FailureInjector",
        "FailureRule",
        "GracefulDrain",
        "IsolatedRestoreRunner",
        "LoadBudgetResult",
        "LoadObservation",
        "LoadProfile",
        "OtelServiceObservation",
        "ResilienceCapacityError",
        "ResiliencePolicyError",
        "ResilienceStateError",
        "ResilientExecutor",
        "RestoreEvidence",
        "RetryEvidence",
        "RetryPolicy",
        "ServiceHealthSnapshot",
        "ServiceHealthState",
        "ServiceOperationsEvidence",
        "TokenBucketRateLimiter",
        "evaluate_load",
    }
    missing = sorted(name for name in expected if not hasattr(backend, name))
    assert missing == []
    assert expected.issubset(set(backend.__all__))
