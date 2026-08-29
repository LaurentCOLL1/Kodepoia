from __future__ import annotations

import kodepoia.backend as backend


def test_remote_config_public_backend_exports_are_available() -> None:
    expected = (
        "ActivationApproval",
        "ActivationPreview",
        "ConfigAuditRecord",
        "ConfigSnapshot",
        "EvaluationContext",
        "EvaluationErrorCode",
        "EvaluationReason",
        "EvaluationResult",
        "FeatureFlagDefinition",
        "FlagPrerequisite",
        "FlagValueType",
        "FlagVariant",
        "InMemoryRemoteConfigService",
        "OpenFeatureRemoteConfigAdapter",
        "RemoteConfigAuthorizationError",
        "RemoteConfigCapacityError",
        "RemoteConfigPolicyError",
        "RemoteConfigStateError",
        "RemoteConfigStateSnapshot",
        "RolloutAllocation",
        "RolloutPlan",
        "TargetingOperator",
        "TargetingRule",
    )
    for name in expected:
        assert hasattr(backend, name), name
        assert name in backend.__all__
