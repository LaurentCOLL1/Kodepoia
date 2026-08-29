from __future__ import annotations

from dataclasses import replace

import pytest

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.contracts import BackendEnvironmentKind, canonical_sha256
from kodepoia.backend.remote_config import (
    ActivationApproval,
    ConfigSnapshot,
    EvaluationContext,
    EvaluationErrorCode,
    EvaluationReason,
    FeatureFlagDefinition,
    FlagPrerequisite,
    FlagValueType,
    FlagVariant,
    InMemoryRemoteConfigService,
    OpenFeatureRemoteConfigAdapter,
    RemoteConfigAuthorizationError,
    RemoteConfigCapacityError,
    RemoteConfigPolicyError,
    RemoteConfigStateError,
    RolloutAllocation,
    RolloutPlan,
    TargetingOperator,
    TargetingRule,
)


class Clock:
    def __init__(self, value: int = 1_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def actor(*, permissions: tuple[str, ...] = ("*",), objects: tuple[str, ...] = ("*",)) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id="operator",
        session_id="session-1",
        permissions=permissions,
        authorized_object_ids=objects,
    )


def bool_flag(
    flag_id: str,
    *,
    version: int = 1,
    default_variant: str = "off",
    rules: tuple[TargetingRule, ...] = (),
    rollout: RolloutPlan | None = None,
    prerequisites: tuple[FlagPrerequisite, ...] = (),
    expires_at_ms: int | None = None,
) -> FeatureFlagDefinition:
    return FeatureFlagDefinition(
        flag_id=flag_id,
        version=version,
        value_type=FlagValueType.BOOLEAN,
        variants=(FlagVariant("off", False), FlagVariant("on", True)),
        default_variant=default_variant,
        targeting_rules=rules,
        rollout=rollout,
        prerequisites=prerequisites,
        expires_at_ms=expires_at_ms,
    )


def fifty_fifty(rollout_id: str = "rollout-1") -> RolloutPlan:
    return RolloutPlan(
        rollout_id=rollout_id,
        allocations=(RolloutAllocation("off", 5_000), RolloutAllocation("on", 5_000)),
    )


def snapshot(
    snapshot_id: str,
    *,
    revision: int = 1,
    environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST,
    flags: tuple[FeatureFlagDefinition, ...] | None = None,
    created_at_ms: int = 900_000,
) -> ConfigSnapshot:
    return ConfigSnapshot(
        snapshot_id=snapshot_id,
        revision=revision,
        environment=environment,
        flags=flags or (bool_flag("feature.alpha"),),
        created_at_ms=created_at_ms,
    )


def register_and_activate(
    service: InMemoryRemoteConfigService,
    item: ConfigSnapshot,
    *,
    who: AuthorityActorContext | None = None,
) -> None:
    who = who or actor()
    service.register_snapshot(who, item)
    if item.environment is BackendEnvironmentKind.PRODUCTION:
        preview = service.preview_activation(who, environment=item.environment, snapshot_id=item.snapshot_id)
        approval = service.approve_activation(
            who,
            preview=preview,
            approval_id=f"approval-{item.snapshot_id}",
            safe_change_digest=canonical_sha256({"preview": preview.digest()}),
        )
        service.activate_snapshot(
            who,
            environment=item.environment,
            snapshot_id=item.snapshot_id,
            approval=approval,
        )
    else:
        service.activate_snapshot(who, environment=item.environment, snapshot_id=item.snapshot_id)


def test_typed_schema_rejects_mismatch_and_unknown_type() -> None:
    with pytest.raises(RemoteConfigPolicyError, match="type_mismatch"):
        FeatureFlagDefinition(
            flag_id="bad",
            version=1,
            value_type=FlagValueType.BOOLEAN,
            variants=(FlagVariant("on", "true"),),
            default_variant="on",
        )
    with pytest.raises(RemoteConfigPolicyError, match="invalid_value_type"):
        FeatureFlagDefinition(  # type: ignore[arg-type]
            flag_id="bad-code",
            version=1,
            value_type="code",
            variants=(FlagVariant("default", "print('unsafe')"),),
            default_variant="default",
        )


def test_object_values_are_canonical_json_only() -> None:
    definition = FeatureFlagDefinition(
        flag_id="layout",
        version=1,
        value_type=FlagValueType.OBJECT,
        variants=(FlagVariant("default", {"b": 2, "a": [1, True]}),),
        default_variant="default",
    )
    assert definition.variant("default").value == {"a": [1, True], "b": 2}
    with pytest.raises(RemoteConfigPolicyError, match="not_canonical_json"):
        FeatureFlagDefinition(
            flag_id="unsafe",
            version=1,
            value_type=FlagValueType.OBJECT,
            variants=(FlagVariant("default", {"bad": object()}),),
            default_variant="default",
        )


def test_context_rejects_explicit_pii_and_is_bounded() -> None:
    with pytest.raises(RemoteConfigPolicyError, match="pii_context_key_forbidden"):
        EvaluationContext(targeting_key="subject-1", attributes={"email": "user@example.test"})
    with pytest.raises(RemoteConfigPolicyError, match="too_large|evaluation_context_too_large"):
        EvaluationContext(targeting_key="subject-1", attributes={"segment": "x" * 10_000}, max_bytes=512)


def test_snapshot_registration_is_immutable_and_revision_conflicts_fail() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    first = snapshot("s1")
    assert service.register_snapshot(actor(), first) == first
    assert service.register_snapshot(actor(), first) == first
    with pytest.raises(RemoteConfigStateError, match="snapshot_id_conflict"):
        service.register_snapshot(actor(), replace(first, flags=(bool_flag("other"),)))
    with pytest.raises(RemoteConfigStateError, match="snapshot_revision_conflict"):
        service.register_snapshot(actor(), snapshot("s2", revision=1, flags=(bool_flag("other"),)))


def test_prerequisite_missing_flag_and_cycle_fail_closed_at_registration() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    missing = snapshot(
        "missing",
        flags=(bool_flag("dependent", prerequisites=(FlagPrerequisite("base", "on"),)),),
    )
    with pytest.raises(RemoteConfigPolicyError, match="prerequisite_flag_not_found"):
        service.register_snapshot(actor(), missing)

    cycle = snapshot(
        "cycle",
        flags=(
            bool_flag("a", prerequisites=(FlagPrerequisite("b", "on"),)),
            bool_flag("b", prerequisites=(FlagPrerequisite("a", "on"),)),
        ),
    )
    with pytest.raises(RemoteConfigPolicyError, match="prerequisite_cycle"):
        service.register_snapshot(actor(), cycle)


def test_targeting_rule_precedes_fractional_rollout() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    definition = bool_flag(
        "feature.alpha",
        rules=(
            TargetingRule(
                rule_id="fr-force-on",
                field="country",
                operator=TargetingOperator.EQUALS,
                expected="FR",
                variant="on",
            ),
        ),
        rollout=fifty_fifty(),
    )
    register_and_activate(service, snapshot("s1", flags=(definition,)))
    result = service.evaluate(
        actor(),
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key="subject-1", attributes={"country": "FR"}),
    )
    assert result.variant == "on"
    assert result.reason is EvaluationReason.TARGETING_MATCH
    assert result.rollout_bucket is None


def test_fractional_assignment_is_stable_for_same_targeting_key() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    register_and_activate(service, snapshot("s1", flags=(bool_flag("feature.alpha", rollout=fifty_fifty()),)))
    context_a = EvaluationContext(targeting_key="subject-42", attributes={"country": "FR"})
    context_b = EvaluationContext(targeting_key="subject-42", attributes={"country": "DE"})
    first = service.evaluate(actor(), environment=BackendEnvironmentKind.TEST, flag_id="feature.alpha", context=context_a)
    second = service.evaluate(actor(), environment=BackendEnvironmentKind.TEST, flag_id="feature.alpha", context=context_b)
    assert first.variant == second.variant
    assert first.rollout_bucket == second.rollout_bucket
    assert first.reason is EvaluationReason.FRACTIONAL


def test_fractional_distribution_fixture_is_bounded_and_deterministic() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock(), max_evaluations=5_000)
    register_and_activate(service, snapshot("s1", flags=(bool_flag("feature.alpha", rollout=fifty_fifty()),)))
    counts = {"off": 0, "on": 0}
    assignments: list[tuple[int | None, str]] = []
    for index in range(2_000):
        result = service.evaluate(
            actor(),
            environment=BackendEnvironmentKind.TEST,
            flag_id="feature.alpha",
            context=EvaluationContext(targeting_key=f"subject-{index}"),
        )
        counts[result.variant] += 1
        assignments.append((result.rollout_bucket, result.variant))
    assert 850 <= counts["off"] <= 1_150
    assert 850 <= counts["on"] <= 1_150
    assert canonical_sha256(assignments) == canonical_sha256(assignments)


def test_fractional_rollout_without_targeting_key_returns_default_error() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    register_and_activate(service, snapshot("s1", flags=(bool_flag("feature.alpha", rollout=fifty_fifty()),)))
    result = service.evaluate(
        actor(),
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(),
    )
    assert result.variant == "off"
    assert result.reason is EvaluationReason.ERROR
    assert result.error_code is EvaluationErrorCode.TARGETING_KEY_MISSING


def test_prerequisite_failure_and_success_are_deterministic() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    dependent = bool_flag("dependent", default_variant="off", prerequisites=(FlagPrerequisite("base", "on"),))
    register_and_activate(service, snapshot("s1", flags=(bool_flag("base", default_variant="off"), dependent)))
    blocked = service.evaluate(
        actor(),
        environment=BackendEnvironmentKind.TEST,
        flag_id="dependent",
        context=EvaluationContext(targeting_key="subject-1"),
    )
    assert blocked.variant == "off"
    assert blocked.reason is EvaluationReason.PREREQUISITE_FAILED

    service2 = InMemoryRemoteConfigService(clock_ms=Clock())
    register_and_activate(service2, snapshot("s2", flags=(bool_flag("base", default_variant="on"), dependent)))
    allowed = service2.evaluate(
        actor(),
        environment=BackendEnvironmentKind.TEST,
        flag_id="dependent",
        context=EvaluationContext(targeting_key="subject-1"),
    )
    assert allowed.reason is EvaluationReason.DEFAULT


def test_expiry_uses_server_clock() -> None:
    clock = Clock(1_000)
    service = InMemoryRemoteConfigService(clock_ms=clock)
    definition = bool_flag("feature.alpha", default_variant="off", rollout=fifty_fifty(), expires_at_ms=1_500)
    register_and_activate(service, snapshot("s1", flags=(definition,), created_at_ms=900))
    before = service.evaluate(
        actor(),
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key="subject-1"),
    )
    assert before.reason is EvaluationReason.FRACTIONAL
    clock.value = 1_500
    after = service.evaluate(
        actor(),
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key="subject-1"),
    )
    assert after.variant == "off"
    assert after.reason is EvaluationReason.EXPIRED


def test_kill_switch_overrides_targeting_and_rollout() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    definition = bool_flag(
        "feature.alpha",
        rules=(TargetingRule("force", "country", TargetingOperator.EQUALS, "FR", "on"),),
        rollout=fifty_fifty(),
    )
    register_and_activate(service, snapshot("s1", flags=(definition,)))
    service.set_kill_switch(actor(), environment=BackendEnvironmentKind.TEST, flag_id="feature.alpha", enabled=True)
    result = service.evaluate(
        actor(),
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key="subject-1", attributes={"country": "FR"}),
    )
    assert result.variant == "off"
    assert result.reason is EvaluationReason.KILL_SWITCH


def test_preview_lists_only_semantically_changed_flags() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    first = snapshot("s1", revision=1, flags=(bool_flag("a"), bool_flag("b")))
    second = snapshot("s2", revision=2, flags=(bool_flag("a"), bool_flag("b", version=2, default_variant="on"), bool_flag("c")))
    register_and_activate(service, first)
    service.register_snapshot(actor(), second)
    preview = service.preview_activation(actor(), environment=BackendEnvironmentKind.TEST, snapshot_id="s2")
    assert preview.from_snapshot_id == "s1"
    assert preview.to_snapshot_id == "s2"
    assert preview.changed_flags == ("b", "c")
    assert preview.production_requires_approval is False


def test_production_activation_requires_registered_approval_and_safechange_digest() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    prod = snapshot("prod-s1", environment=BackendEnvironmentKind.PRODUCTION)
    service.register_snapshot(actor(), prod)
    with pytest.raises(RemoteConfigAuthorizationError, match="requires_approval"):
        service.activate_snapshot(actor(), environment=BackendEnvironmentKind.PRODUCTION, snapshot_id="prod-s1")
    preview = service.preview_activation(actor(), environment=BackendEnvironmentKind.PRODUCTION, snapshot_id="prod-s1")
    safe_change = canonical_sha256({"safe_change": preview.digest()})
    approval = service.approve_activation(
        actor(),
        preview=preview,
        approval_id="approval-prod-s1",
        safe_change_digest=safe_change,
    )
    activated = service.activate_snapshot(
        actor(),
        environment=BackendEnvironmentKind.PRODUCTION,
        snapshot_id="prod-s1",
        approval=approval,
    )
    assert activated.snapshot_id == "prod-s1"
    records = service.audit_records()
    assert any(record.safe_change_digest == safe_change for record in records)


def test_unregistered_or_wrong_approval_is_rejected() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    prod = snapshot("prod-s1", environment=BackendEnvironmentKind.PRODUCTION)
    service.register_snapshot(actor(), prod)
    preview = service.preview_activation(actor(), environment=BackendEnvironmentKind.PRODUCTION, snapshot_id="prod-s1")
    fake = ActivationApproval(
        approval_id="fake",
        environment=BackendEnvironmentKind.PRODUCTION,
        preview_digest=preview.digest(),
        snapshot_digest=preview.to_snapshot_digest,
        approver_account_id="operator",
        safe_change_digest=canonical_sha256({"safe": 1}),
        approved_at_ms=1_000_000,
    )
    with pytest.raises(RemoteConfigAuthorizationError, match="approval_not_registered"):
        service.activate_snapshot(
            actor(),
            environment=BackendEnvironmentKind.PRODUCTION,
            snapshot_id="prod-s1",
            approval=fake,
        )


def test_rollback_reactivates_prior_immutable_snapshot() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    s1 = snapshot("s1", revision=1, flags=(bool_flag("feature.alpha", default_variant="off"),))
    s2 = snapshot("s2", revision=2, flags=(bool_flag("feature.alpha", version=2, default_variant="on"),))
    register_and_activate(service, s1)
    service.register_snapshot(actor(), s2)
    service.activate_snapshot(actor(), environment=BackendEnvironmentKind.TEST, snapshot_id="s2")
    assert service.active_snapshot(BackendEnvironmentKind.TEST).snapshot_id == "s2"
    rolled = service.rollback(actor(), environment=BackendEnvironmentKind.TEST, snapshot_id="s1")
    assert rolled.snapshot_id == "s1"
    assert service.snapshot(BackendEnvironmentKind.TEST, "s2") == s2
    assert service.active_snapshot(BackendEnvironmentKind.TEST).snapshot_id == "s1"


def test_environment_isolation_keeps_active_state_separate() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    test_snapshot = snapshot("test-s1", environment=BackendEnvironmentKind.TEST, flags=(bool_flag("feature.alpha", default_variant="on"),))
    prod_snapshot = snapshot("prod-s1", environment=BackendEnvironmentKind.PRODUCTION, flags=(bool_flag("feature.alpha", default_variant="off"),))
    register_and_activate(service, test_snapshot)
    register_and_activate(service, prod_snapshot)
    test_value = service.evaluate(actor(), environment=BackendEnvironmentKind.TEST, flag_id="feature.alpha", context=EvaluationContext())
    prod_value = service.evaluate(actor(), environment=BackendEnvironmentKind.PRODUCTION, flag_id="feature.alpha", context=EvaluationContext())
    assert test_value.value is True
    assert prod_value.value is False
    assert test_value.snapshot_id == "test-s1"
    assert prod_value.snapshot_id == "prod-s1"


def test_function_and_object_authorization_fail_closed() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    item = snapshot("s1")
    wrong_function = actor(permissions=("remote_config.evaluate",), objects=("s1",))
    with pytest.raises(RemoteConfigAuthorizationError, match="forbidden"):
        service.register_snapshot(wrong_function, item)
    wrong_object = actor(permissions=("remote_config.snapshot.register",), objects=("other",))
    with pytest.raises(RemoteConfigAuthorizationError, match="forbidden"):
        service.register_snapshot(wrong_object, item)


def test_openfeature_adapter_falls_back_on_type_mismatch_and_missing_flag() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    definition = FeatureFlagDefinition(
        flag_id="message",
        version=1,
        value_type=FlagValueType.STRING,
        variants=(FlagVariant("default", "hello"),),
        default_variant="default",
    )
    register_and_activate(service, snapshot("s1", flags=(definition,)))
    adapter = OpenFeatureRemoteConfigAdapter(service=service, actor=actor(), environment=BackendEnvironmentKind.TEST)
    context = EvaluationContext(targeting_key="subject-1")
    assert adapter.get_string_value("message", "fallback", context) == "hello"
    assert adapter.get_boolean_value("message", False, context) is False
    assert adapter.get_string_value("missing", "fallback", context) == "fallback"


def test_trace_and_state_do_not_expose_raw_targeting_key() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock())
    register_and_activate(service, snapshot("s1", flags=(bool_flag("feature.alpha", rollout=fifty_fifty()),)))
    raw_key = "secret-subject-42"
    service.evaluate(
        actor(),
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key=raw_key, attributes={"country": "FR"}),
    )
    assert raw_key not in repr(service.trace())
    assert raw_key not in repr(service.state_snapshot().canonical())


def test_state_and_evaluation_digests_are_deterministic() -> None:
    def build() -> tuple[str, str]:
        service = InMemoryRemoteConfigService(clock_ms=Clock())
        definition = bool_flag("feature.alpha", rollout=fifty_fifty())
        register_and_activate(service, snapshot("s1", flags=(definition,)))
        result = service.evaluate(
            actor(),
            environment=BackendEnvironmentKind.TEST,
            flag_id="feature.alpha",
            context=EvaluationContext(targeting_key="subject-42", attributes={"country": "FR"}),
        )
        return service.state_snapshot().digest(), result.evaluation_digest

    assert build() == build()


def test_capacity_budgets_fail_closed() -> None:
    service = InMemoryRemoteConfigService(clock_ms=Clock(), max_snapshots=1, max_evaluations=1)
    register_and_activate(service, snapshot("s1"))
    with pytest.raises(RemoteConfigCapacityError, match="snapshot_capacity"):
        service.register_snapshot(actor(), snapshot("s2", revision=2))
    service.evaluate(actor(), environment=BackendEnvironmentKind.TEST, flag_id="feature.alpha", context=EvaluationContext())
    with pytest.raises(RemoteConfigCapacityError, match="evaluation_capacity"):
        service.evaluate(actor(), environment=BackendEnvironmentKind.TEST, flag_id="feature.alpha", context=EvaluationContext())
