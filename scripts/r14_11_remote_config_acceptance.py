from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.contracts import BackendEnvironmentKind, canonical_sha256
from kodepoia.backend.remote_config import (
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

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


DEFAULT_AUTHORIZED_OBJECTS = (
    "base.enabled",
    "cycle",
    "cycle.a",
    "cycle.b",
    "feature.alpha",
    "feature.expiring",
    "message.banner",
    "prod-v1",
    "production",
    "test",
    "test-v1",
    "test-v2",
    "tiny.flag",
    "tiny-v1",
    "tiny-v2",
    "unauthorized",
    "unauthorized.flag",
)


class Clock:
    def __init__(self, value: int = 1_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def _actor(
    *,
    account_id: str = "operator",
    permissions: tuple[str, ...] = ("*",),
    objects: tuple[str, ...] = DEFAULT_AUTHORIZED_OBJECTS,
) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id=account_id,
        session_id=f"session-{account_id}",
        permissions=permissions,
        authorized_object_ids=objects,
    )


def _rollout(rollout_id: str) -> RolloutPlan:
    return RolloutPlan(
        rollout_id=rollout_id,
        allocations=(RolloutAllocation("off", 5_000), RolloutAllocation("on", 5_000)),
    )


def _bool_flag(
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


def _snapshot(
    snapshot_id: str,
    *,
    revision: int,
    environment: BackendEnvironmentKind,
    flags: tuple[FeatureFlagDefinition, ...],
    created_at_ms: int,
) -> ConfigSnapshot:
    return ConfigSnapshot(
        snapshot_id=snapshot_id,
        revision=revision,
        environment=environment,
        flags=flags,
        created_at_ms=created_at_ms,
    )


def _expect(exc_type: type[BaseException], expected_text: str, action: Any) -> bool:
    try:
        action()
    except exc_type as exc:
        return expected_text in str(exc)
    return False


def build_evidence(source_sha: str) -> dict[str, Any]:
    if _SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be lowercase 40-character Git SHA")

    clock = Clock()
    service = InMemoryRemoteConfigService(
        clock_ms=clock,
        max_snapshots=32,
        max_flags_per_snapshot=32,
        max_evaluations=5_000,
        max_audit_records=128,
    )
    operator = _actor()

    base_on = _bool_flag("base.enabled", default_variant="on")
    feature_v1 = _bool_flag(
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
        rollout=_rollout("alpha-rollout-v1"),
        prerequisites=(FlagPrerequisite("base.enabled", "on"),),
    )
    expiring = _bool_flag(
        "feature.expiring",
        rollout=_rollout("expiring-rollout"),
        expires_at_ms=1_100_000,
    )
    message = FeatureFlagDefinition(
        flag_id="message.banner",
        version=1,
        value_type=FlagValueType.STRING,
        variants=(FlagVariant("default", "hello"),),
        default_variant="default",
    )
    test_v1 = _snapshot(
        "test-v1",
        revision=1,
        environment=BackendEnvironmentKind.TEST,
        flags=(base_on, feature_v1, expiring, message),
        created_at_ms=900_000,
    )
    service.register_snapshot(operator, test_v1)
    service.activate_snapshot(operator, environment=BackendEnvironmentKind.TEST, snapshot_id="test-v1")

    typed_schema = _expect(
        RemoteConfigPolicyError,
        "type_mismatch",
        lambda: FeatureFlagDefinition(
            flag_id="bad",
            version=1,
            value_type=FlagValueType.BOOLEAN,
            variants=(FlagVariant("default", "true"),),
            default_variant="default",
        ),
    )
    remote_code_type_rejected = _expect(
        RemoteConfigPolicyError,
        "invalid_value_type",
        lambda: FeatureFlagDefinition(  # type: ignore[arg-type]
            flag_id="bad-code",
            version=1,
            value_type="code",
            variants=(FlagVariant("default", "exec('unsafe')"),),
            default_variant="default",
        ),
    )
    immutable_snapshots = _expect(
        RemoteConfigStateError,
        "snapshot_id_conflict",
        lambda: service.register_snapshot(
            operator,
            _snapshot(
                "test-v1",
                revision=1,
                environment=BackendEnvironmentKind.TEST,
                flags=(_bool_flag("different"),),
                created_at_ms=900_000,
            ),
        ),
    )

    targeted = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key="target-fr", attributes={"country": "FR"}),
    )
    targeting_precedence = targeted.variant == "on" and targeted.reason is EvaluationReason.TARGETING_MATCH

    stable_a = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key="stable-target", attributes={"country": "DE"}),
    )
    stable_b = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key="stable-target", attributes={"country": "US"}),
    )
    stable_fractional = (
        stable_a.reason is EvaluationReason.FRACTIONAL
        and stable_a.variant == stable_b.variant
        and stable_a.rollout_bucket == stable_b.rollout_bucket
    )

    assignments: list[tuple[int | None, str]] = []
    counts = {"off": 0, "on": 0}
    for index in range(2_000):
        result = service.evaluate(
            operator,
            environment=BackendEnvironmentKind.TEST,
            flag_id="feature.alpha",
            context=EvaluationContext(targeting_key=f"distribution-{index}", attributes={"country": "DE"}),
        )
        counts[result.variant] += 1
        assignments.append((result.rollout_bucket, result.variant))
    bounded_distribution = 850 <= counts["off"] <= 1_150 and 850 <= counts["on"] <= 1_150

    missing_key = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(attributes={"country": "DE"}),
    )
    missing_targeting_key_fails_closed = (
        missing_key.variant == "off"
        and missing_key.reason is EvaluationReason.ERROR
        and missing_key.error_code is EvaluationErrorCode.TARGETING_KEY_MISSING
    )

    prerequisite_cycle_rejected = _expect(
        RemoteConfigPolicyError,
        "prerequisite_cycle",
        lambda: service.register_snapshot(
            operator,
            _snapshot(
                "cycle",
                revision=7,
                environment=BackendEnvironmentKind.TEST,
                flags=(
                    _bool_flag("cycle.a", prerequisites=(FlagPrerequisite("cycle.b", "on"),)),
                    _bool_flag("cycle.b", prerequisites=(FlagPrerequisite("cycle.a", "on"),)),
                ),
                created_at_ms=900_000,
            ),
        ),
    )

    base_off_v2 = _bool_flag("base.enabled", version=2, default_variant="off")
    feature_v2 = _bool_flag(
        "feature.alpha",
        version=2,
        rollout=_rollout("alpha-rollout-v2"),
        prerequisites=(FlagPrerequisite("base.enabled", "on"),),
    )
    expiring_v2 = _bool_flag(
        "feature.expiring",
        version=2,
        rollout=_rollout("expiring-rollout-v2"),
        expires_at_ms=1_100_000,
    )
    message_v2 = FeatureFlagDefinition(
        flag_id="message.banner",
        version=2,
        value_type=FlagValueType.STRING,
        variants=(FlagVariant("default", "hello-v2"),),
        default_variant="default",
    )
    test_v2 = _snapshot(
        "test-v2",
        revision=2,
        environment=BackendEnvironmentKind.TEST,
        flags=(base_off_v2, feature_v2, expiring_v2, message_v2),
        created_at_ms=950_000,
    )
    service.register_snapshot(operator, test_v2)
    preview_v2 = service.preview_activation(operator, environment=BackendEnvironmentKind.TEST, snapshot_id="test-v2")
    preview_dry_run = (
        preview_v2.from_snapshot_id == "test-v1"
        and preview_v2.to_snapshot_id == "test-v2"
        and set(preview_v2.changed_flags) == {"base.enabled", "feature.alpha", "feature.expiring", "message.banner"}
        and service.active_snapshot(BackendEnvironmentKind.TEST).snapshot_id == "test-v1"
    )
    service.activate_snapshot(operator, environment=BackendEnvironmentKind.TEST, snapshot_id="test-v2")
    prerequisite_result = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key="prereq-target", attributes={"country": "DE"}),
    )
    prerequisite_enforced = (
        prerequisite_result.variant == "off"
        and prerequisite_result.reason is EvaluationReason.PREREQUISITE_FAILED
    )

    rollback_preview = service.preview_activation(operator, environment=BackendEnvironmentKind.TEST, snapshot_id="test-v1")
    service.rollback(operator, environment=BackendEnvironmentKind.TEST, snapshot_id="test-v1")
    rollback_ok = service.active_snapshot(BackendEnvironmentKind.TEST).snapshot_id == "test-v1"

    pre_expiry = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.expiring",
        context=EvaluationContext(targeting_key="expiry-target"),
    )
    clock.value = 1_100_000
    post_expiry = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.expiring",
        context=EvaluationContext(targeting_key="expiry-target"),
    )
    expiry_server_clock = (
        pre_expiry.reason is EvaluationReason.FRACTIONAL
        and post_expiry.reason is EvaluationReason.EXPIRED
        and post_expiry.variant == "off"
    )
    clock.value = 1_000_000

    service.set_kill_switch(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        enabled=True,
    )
    kill_result = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key="kill-target", attributes={"country": "FR"}),
    )
    kill_switch = kill_result.reason is EvaluationReason.KILL_SWITCH and kill_result.variant == "off"
    service.set_kill_switch(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        enabled=False,
    )

    prod_flag = _bool_flag("feature.alpha", default_variant="off")
    prod_message = FeatureFlagDefinition(
        flag_id="message.banner",
        version=1,
        value_type=FlagValueType.STRING,
        variants=(FlagVariant("default", "prod"),),
        default_variant="default",
    )
    prod = _snapshot(
        "prod-v1",
        revision=1,
        environment=BackendEnvironmentKind.PRODUCTION,
        flags=(prod_flag, prod_message),
        created_at_ms=900_000,
    )
    service.register_snapshot(operator, prod)
    requires_approval = _expect(
        RemoteConfigAuthorizationError,
        "production_activation_requires_approval",
        lambda: service.activate_snapshot(
            operator,
            environment=BackendEnvironmentKind.PRODUCTION,
            snapshot_id="prod-v1",
        ),
    )
    prod_preview = service.preview_activation(
        operator,
        environment=BackendEnvironmentKind.PRODUCTION,
        snapshot_id="prod-v1",
    )
    safe_change_digest = canonical_sha256({"safe_change_plan": prod_preview.digest()})
    approval = service.approve_activation(
        operator,
        preview=prod_preview,
        approval_id="prod-approval-1",
        safe_change_digest=safe_change_digest,
    )
    service.activate_snapshot(
        operator,
        environment=BackendEnvironmentKind.PRODUCTION,
        snapshot_id="prod-v1",
        approval=approval,
    )
    production_approval_safechange = requires_approval and any(
        record.safe_change_digest == safe_change_digest for record in service.audit_records()
    )

    test_eval = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="message.banner",
        context=EvaluationContext(targeting_key="environment-target"),
    )
    prod_eval = service.evaluate(
        operator,
        environment=BackendEnvironmentKind.PRODUCTION,
        flag_id="message.banner",
        context=EvaluationContext(targeting_key="environment-target"),
    )
    environment_isolation = (
        test_eval.value == "hello"
        and prod_eval.value == "prod"
        and test_eval.snapshot_id == "test-v1"
        and prod_eval.snapshot_id == "prod-v1"
    )

    unauthorized = _actor(
        account_id="limited",
        permissions=("remote_config.snapshot.register",),
        objects=("wrong-object",),
    )
    object_function_authorization = _expect(
        RemoteConfigAuthorizationError,
        "forbidden",
        lambda: service.register_snapshot(
            unauthorized,
            _snapshot(
                "unauthorized",
                revision=8,
                environment=BackendEnvironmentKind.TEST,
                flags=(_bool_flag("unauthorized.flag"),),
                created_at_ms=900_000,
            ),
        ),
    )

    adapter = OpenFeatureRemoteConfigAdapter(
        service=service,
        actor=operator,
        environment=BackendEnvironmentKind.TEST,
    )
    adapter_context = EvaluationContext(targeting_key="adapter-target")
    openfeature_typed_fallback = (
        adapter.get_string_value("message.banner", "fallback", adapter_context) == "hello"
        and adapter.get_boolean_value("message.banner", False, adapter_context) is False
        and adapter.get_string_value("missing.flag", "fallback", adapter_context) == "fallback"
    )

    raw_target = "private-target-acceptance"
    service.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="feature.alpha",
        context=EvaluationContext(targeting_key=raw_target, attributes={"country": "DE"}),
    )
    pii_rejected = _expect(
        RemoteConfigPolicyError,
        "pii_context_key_forbidden",
        lambda: EvaluationContext(targeting_key="pii-target", attributes={"email": "private@example.test"}),
    )
    redacted_evidence = raw_target not in repr(service.trace()) and pii_rejected

    tiny = InMemoryRemoteConfigService(clock_ms=Clock(), max_snapshots=1, max_evaluations=1)
    tiny.register_snapshot(
        operator,
        _snapshot(
            "tiny-v1",
            revision=1,
            environment=BackendEnvironmentKind.TEST,
            flags=(_bool_flag("tiny.flag"),),
            created_at_ms=900_000,
        ),
    )
    tiny.activate_snapshot(operator, environment=BackendEnvironmentKind.TEST, snapshot_id="tiny-v1")
    capacity_snapshot = _expect(
        RemoteConfigCapacityError,
        "snapshot_capacity",
        lambda: tiny.register_snapshot(
            operator,
            _snapshot(
                "tiny-v2",
                revision=2,
                environment=BackendEnvironmentKind.TEST,
                flags=(_bool_flag("tiny.flag", version=2),),
                created_at_ms=900_001,
            ),
        ),
    )
    tiny.evaluate(
        operator,
        environment=BackendEnvironmentKind.TEST,
        flag_id="tiny.flag",
        context=EvaluationContext(),
    )
    capacity_eval = _expect(
        RemoteConfigCapacityError,
        "evaluation_capacity",
        lambda: tiny.evaluate(
            operator,
            environment=BackendEnvironmentKind.TEST,
            flag_id="tiny.flag",
            context=EvaluationContext(),
        ),
    )
    bounded_capacity = capacity_snapshot and capacity_eval

    state = service.state_snapshot()
    checks = {
        "typed_schema": typed_schema,
        "immutable_snapshots": immutable_snapshots,
        "targeting_precedence": targeting_precedence,
        "stable_fractional": stable_fractional,
        "bounded_distribution": bounded_distribution,
        "missing_targeting_key_fails_closed": missing_targeting_key_fails_closed,
        "prerequisite_cycle_rejected": prerequisite_cycle_rejected,
        "prerequisite_enforced": prerequisite_enforced,
        "expiry_server_clock": expiry_server_clock,
        "kill_switch": kill_switch,
        "preview_dry_run": preview_dry_run,
        "production_approval_safechange": production_approval_safechange,
        "rollback": rollback_ok,
        "environment_isolation": environment_isolation,
        "object_function_authorization": object_function_authorization,
        "openfeature_typed_fallback": openfeature_typed_fallback,
        "redacted_evidence": redacted_evidence,
        "bounded_capacity": bounded_capacity,
        "remote_code_type_rejected": remote_code_type_rejected,
    }
    if not all(checks.values()):
        failed = sorted(key for key, value in checks.items() if not value)
        raise AssertionError(f"R14.11 acceptance checks failed: {failed}")

    return {
        "schema_version": "r14.11-1",
        "source_sha": source_sha,
        "status": "pass",
        "manual_state": "none",
        "provider_live_claim": False,
        "secrets_exposed": False,
        "pii_exposed": False,
        "arbitrary_code_execution": False,
        "checks": checks,
        "snapshot_digest": test_v1.digest(),
        "state_digest": state.digest(),
        "trace_digest": state.trace_digest,
        "audit_digest": state.audit_digest,
        "evaluation_digests": {
            "targeted": targeted.evaluation_digest,
            "stable": stable_a.evaluation_digest,
            "prerequisite": prerequisite_result.evaluation_digest,
            "expired": post_expiry.evaluation_digest,
            "kill_switch": kill_result.evaluation_digest,
            "test_environment": test_eval.evaluation_digest,
            "production_environment": prod_eval.evaluation_digest,
        },
        "rollout_distribution": {
            "population": 2_000,
            "off": counts["off"],
            "on": counts["on"],
            "assignment_digest": canonical_sha256(assignments),
        },
        "rollback": {
            "from_snapshot": "test-v2",
            "to_snapshot": "test-v1",
            "active_after": service.active_snapshot(BackendEnvironmentKind.TEST).snapshot_id,
            "preview_digest": rollback_preview.digest(),
        },
        "budgets": {
            "max_snapshots": service.max_snapshots,
            "max_flags_per_snapshot": service.max_flags_per_snapshot,
            "max_evaluations": service.max_evaluations,
            "max_audit_records": service.max_audit_records,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic R14.11 remote config acceptance evidence")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    evidence = build_evidence(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
