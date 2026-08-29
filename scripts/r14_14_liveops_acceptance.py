from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.content_delivery import ContentBundleDefinition, ContentManifest, ContentSignatureState
from kodepoia.backend.contracts import BackendEnvironmentKind, canonical_sha256
from kodepoia.backend.entitlements import (
    BillingEnvironment,
    BillingProductKind,
    BillingProvider,
    CatalogProductDefinition,
)
from kodepoia.backend.event_pipeline import EventFieldType, EventPrivacyClass, EventSchemaDefinition, EventSchemaField
from kodepoia.backend.liveops import (
    CatalogProductReference,
    ConfigSnapshotReference,
    ContentManifestReference,
    EventContractReference,
    InMemoryLiveOpsService,
    LiveOpsAudience,
    LiveOpsAuthorizationError,
    LiveOpsCampaignDefinition,
    LiveOpsCampaignState,
    LiveOpsCapacityError,
    LiveOpsPolicyError,
    LiveOpsRotation,
    LiveOpsScheduleWindow,
    LiveOpsSeasonDefinition,
    LiveOpsSeasonReference,
    LiveOpsStateError,
)
from kodepoia.backend.remote_config import (
    ConfigSnapshot,
    EvaluationContext,
    FeatureFlagDefinition,
    FlagValueType,
    FlagVariant,
    InMemoryRemoteConfigService,
    TargetingOperator,
    TargetingRule,
)

SAFE_CHANGE = canonical_sha256({"safe_change": "r14.14.acceptance"})
ACCEPTANCE_OBJECTS = (
    "campaign.autumn.1",
    "config.liveops.1",
    "config.other",
    "manifest.liveops.1",
    "product.liveops.1",
    "schema.liveops.1",
    "season.2026.autumn",
    BackendEnvironmentKind.TEST.value,
)


class Clock:
    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def actor(
    *,
    permissions: tuple[str, ...] = ("*",),
    objects: tuple[str, ...] = ACCEPTANCE_OBJECTS,
) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id="acceptance.operator",
        session_id="acceptance.session",
        permissions=permissions,
        authorized_object_ids=objects,
    )


def snapshot(*, snapshot_id: str = "config.liveops.1") -> ConfigSnapshot:
    flag = FeatureFlagDefinition(
        flag_id="liveops.audience",
        version=1,
        value_type=FlagValueType.STRING,
        variants=(FlagVariant("control", "control"), FlagVariant("eligible", "eligible")),
        default_variant="control",
        targeting_rules=(
            TargetingRule(
                rule_id="country.fr",
                field="country",
                operator=TargetingOperator.EQUALS,
                expected="FR",
                variant="eligible",
            ),
        ),
    )
    return ConfigSnapshot(
        snapshot_id=snapshot_id,
        revision=1,
        environment=BackendEnvironmentKind.TEST,
        flags=(flag,),
        created_at_ms=100,
    )


def manifest() -> ContentManifest:
    payload = b"r14.14-acceptance-content"
    bundle = ContentBundleDefinition(
        bundle_id="bundle.liveops.1",
        version=1,
        object_id="object.liveops.1",
        payload_name="liveops.json",
        media_type="application/json",
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        signature_state=ContentSignatureState.NOT_APPLICABLE,
    )
    return ContentManifest(
        manifest_id="manifest.liveops.1",
        revision=1,
        environment=BackendEnvironmentKind.TEST,
        bundles=(bundle,),
        min_client_version=1,
        max_client_version=10,
        schema_version=1,
        created_at_ms=100,
    )


def product(*, environment: BillingEnvironment = BillingEnvironment.TEST) -> CatalogProductDefinition:
    return CatalogProductDefinition(
        product_id="product.liveops.1",
        version=1,
        entitlement_id="entitlement.liveops.1",
        kind=BillingProductKind.DURABLE,
        provider=BillingProvider.GOOGLE_PLAY,
        environment=environment,
        provider_product_id="provider.product.liveops.1",
    )


def event_schema() -> EventSchemaDefinition:
    return EventSchemaDefinition(
        schema_id="schema.liveops.1",
        event_type="liveops.campaign.entered",
        version=1,
        environment=BackendEnvironmentKind.TEST,
        fields=(EventSchemaField("campaign_id", EventFieldType.STRING, privacy=EventPrivacyClass.INTERNAL),),
    )


def season() -> LiveOpsSeasonDefinition:
    return LiveOpsSeasonDefinition(
        season_id="season.2026.autumn",
        version=1,
        environment=BackendEnvironmentKind.TEST,
        schedule=LiveOpsScheduleWindow(1_000, 10_000, "Europe/Paris", "2026c"),
        created_at_ms=100,
    )


def campaign(
    season_definition: LiveOpsSeasonDefinition,
    config: ConfigSnapshot,
    content: ContentManifest,
    catalog: CatalogProductDefinition,
    event: EventSchemaDefinition,
) -> LiveOpsCampaignDefinition:
    config_ref = ConfigSnapshotReference.from_snapshot(config)
    content_ref = ContentManifestReference.from_manifest(content)
    return LiveOpsCampaignDefinition(
        campaign_id="campaign.autumn.1",
        version=1,
        season=LiveOpsSeasonReference.from_season(season_definition),
        environment=BackendEnvironmentKind.TEST,
        schedule=LiveOpsScheduleWindow(2_000, 8_000, "America/Edmonton", "2026c"),
        config_snapshot=config_ref,
        content_manifest=content_ref,
        catalog_products=(CatalogProductReference.from_product(catalog),),
        event_contracts=(EventContractReference.from_schema(event),),
        rotations=(
            LiveOpsRotation("rotation.a", 2_000, 4_000, content_manifest_digest=content_ref.digest),
            LiveOpsRotation("rotation.b", 4_000, 6_000, config_snapshot_digest=config_ref.digest),
        ),
        audience=LiveOpsAudience("liveops.audience", ("eligible",)),
        created_at_ms=100,
    )


def register_all(service: InMemoryLiveOpsService, who: AuthorityActorContext):
    season_definition = season()
    config = snapshot()
    content = manifest()
    catalog = product()
    event = event_schema()
    service.register_season(who, season_definition)
    service.register_config_snapshot(who, config)
    service.register_content_manifest(who, content)
    service.register_catalog_product(who, catalog)
    service.register_event_schema(who, event)
    definition = campaign(season_definition, config, content, catalog, event)
    service.register_campaign(who, definition)
    return season_definition, config, content, catalog, event, definition


def expected_exception(exc_type: type[BaseException], fn, text: str | None = None) -> bool:
    try:
        fn()
    except exc_type as exc:
        return text is None or text in str(exc)
    return False


def run(source_sha: str) -> dict[str, object]:
    if len(source_sha) != 40 or any(char not in "0123456789abcdef" for char in source_sha):
        raise ValueError("source_sha must be a lowercase 40-character Git SHA")

    checks: dict[str, bool] = {}
    who = actor()

    window = LiveOpsScheduleWindow(1_000, 2_000, "America/Edmonton", "2026c")
    checks["schedule_utc_timezone_metadata"] = (
        window.contains(1_000)
        and window.contains(1_999)
        and not window.contains(2_000)
        and window.display_tzid == "America/Edmonton"
        and window.tzdb_version == "2026c"
    )
    checks["unsafe_schedule_rejected"] = expected_exception(
        LiveOpsPolicyError,
        lambda: LiveOpsScheduleWindow(2_000, 2_000, "Europe/Paris", "2026c"),
        "schedule_end_must_follow_start",
    )

    identity_clock = Clock(1_500)
    identity_service = InMemoryLiveOpsService(clock_ms=identity_clock)
    season_definition = season()
    identity_service.register_season(who, season_definition)
    checks["immutable_season_identity"] = (
        identity_service.register_season(who, season_definition).digest() == season_definition.digest()
        and expected_exception(
            LiveOpsStateError,
            lambda: identity_service.register_season(
                who,
                replace(season_definition, schedule=LiveOpsScheduleWindow(1_000, 11_000, "Europe/Paris", "2026c")),
            ),
            "season_version_rebind",
        )
    )

    dependency_service = InMemoryLiveOpsService(clock_ms=Clock(1_500))
    s = season()
    cfg = snapshot()
    cnt = manifest()
    cat = product()
    evt = event_schema()
    definition = campaign(s, cfg, cnt, cat, evt)
    checks["missing_dependencies_fail_closed"] = expected_exception(
        LiveOpsStateError,
        lambda: dependency_service.register_campaign(who, definition),
        "season_not_found",
    )
    dependency_service.register_season(who, s)
    checks["exact_dependency_binding"] = expected_exception(
        LiveOpsStateError,
        lambda: dependency_service.register_campaign(who, definition),
        "config_dependency_unavailable",
    )
    checks["billing_environment_guard"] = expected_exception(
        LiveOpsPolicyError,
        lambda: campaign(s, cfg, cnt, product(environment=BillingEnvironment.PRODUCTION), evt),
        "nonproduction_campaign_rejects_production_billing",
    )

    stale_clock = Clock(1_500)
    stale_service = InMemoryLiveOpsService(clock_ms=stale_clock)
    *_stale_dependencies, stale_campaign = register_all(stale_service, who)
    stale_preview = stale_service.preview_campaign(who, campaign_id=stale_campaign.campaign_id, version=1)
    stale_clock.value = 2_500
    checks["stale_preview_rejected"] = expected_exception(
        LiveOpsStateError,
        lambda: stale_service.approve_campaign(
            who,
            preview=stale_preview,
            approval_id="approval.stale",
            safe_change_digest=SAFE_CHANGE,
        ),
        "stale_preview",
    )

    clock = Clock(2_500)
    service = InMemoryLiveOpsService(clock_ms=clock)
    season_definition, config, _content, _catalog, _event, definition = register_all(service, who)
    state_before_preview = service.state_snapshot().digest()
    first_preview = service.preview_campaign(who, campaign_id=definition.campaign_id, version=1)
    clock.value = 2_600
    second_preview = service.preview_campaign(who, campaign_id=definition.campaign_id, version=1)
    checks["preview_non_mutating"] = (
        first_preview.mutation_count == 0
        and second_preview.mutation_count == 0
        and service.state_snapshot().digest() == state_before_preview
    )
    checks["preview_digest_clock_stable"] = (
        first_preview.evaluated_at_ms != second_preview.evaluated_at_ms
        and first_preview.digest() == second_preview.digest()
    )

    approval = service.approve_campaign(
        who,
        preview=second_preview,
        approval_id="approval.liveops.1",
        safe_change_digest=SAFE_CHANGE,
    )
    clock.value = 2_700
    approval_retry = service.approve_campaign(
        who,
        preview=second_preview,
        approval_id="approval.liveops.1",
        safe_change_digest=SAFE_CHANGE,
    )
    checks["approval_safechange_idempotent"] = approval_retry == approval and approval.safe_change_digest == SAFE_CHANGE

    activation = service.activate_campaign(
        who,
        campaign_id=definition.campaign_id,
        version=1,
        activation_id="activation.liveops.1",
        approval=approval,
    )
    clock.value = 2_800
    activation_retry = service.activate_campaign(
        who,
        campaign_id=definition.campaign_id,
        version=1,
        activation_id="activation.liveops.1",
        approval=approval,
    )
    checks["activation_idempotent"] = activation_retry == activation and activation.state is LiveOpsCampaignState.ACTIVE
    checks["scheduler_replay_idempotent"] = (
        service.advance_campaign(who, campaign_id=definition.campaign_id, version=1)
        == service.advance_campaign(who, campaign_id=definition.campaign_id, version=1)
    )
    active_rotation = service.active_rotation(campaign_id=definition.campaign_id, version=1)
    checks["rotation_resolution"] = active_rotation is not None and active_rotation.rotation_id == "rotation.a"

    remote = InMemoryRemoteConfigService(clock_ms=clock)
    remote.register_snapshot(who, config)
    remote.activate_snapshot(who, environment=BackendEnvironmentKind.TEST, snapshot_id=config.snapshot_id)
    eligible = service.evaluate_audience(
        who,
        campaign_id=definition.campaign_id,
        version=1,
        remote_config=remote,
        context=EvaluationContext(targeting_key="subject.1", attributes={"country": "FR"}),
    )
    control = service.evaluate_audience(
        who,
        campaign_id=definition.campaign_id,
        version=1,
        remote_config=remote,
        context=EvaluationContext(targeting_key="subject.2", attributes={"country": "DE"}),
    )
    checks["remote_config_audience_targeting"] = eligible.eligible and eligible.variant == "eligible" and not control.eligible
    other = replace(snapshot(snapshot_id="config.other"), revision=2)
    remote_other = InMemoryRemoteConfigService(clock_ms=clock)
    remote_other.register_snapshot(who, other)
    remote_other.activate_snapshot(who, environment=BackendEnvironmentKind.TEST, snapshot_id=other.snapshot_id)
    checks["audience_snapshot_mismatch_rejected"] = expected_exception(
        LiveOpsStateError,
        lambda: service.evaluate_audience(
            who,
            campaign_id=definition.campaign_id,
            version=1,
            remote_config=remote_other,
            context=EvaluationContext(targeting_key="subject.3", attributes={"country": "FR"}),
        ),
        "audience_config_snapshot_mismatch",
    )

    paused = service.pause_campaign(who, campaign_id=definition.campaign_id, version=1)
    resumed = service.resume_campaign(who, campaign_id=definition.campaign_id, version=1)
    checks["pause_resume_explicit"] = paused.state is LiveOpsCampaignState.PAUSED and resumed.state is LiveOpsCampaignState.ACTIVE
    pause_only = actor(permissions=("liveops.campaign.pause",), objects=(definition.campaign_id,))
    clock.value = 8_000
    checks["pause_has_no_hidden_advance"] = (
        expected_exception(
            LiveOpsStateError,
            lambda: service.pause_campaign(pause_only, campaign_id=definition.campaign_id, version=1),
            "campaign_not_pausable",
        )
        and service.runtime(definition.campaign_id, 1).state is LiveOpsCampaignState.ACTIVE
    )
    expired = service.advance_campaign(who, campaign_id=definition.campaign_id, version=1)
    expired_retry = service.advance_campaign(who, campaign_id=definition.campaign_id, version=1)
    checks["expiry_idempotent"] = expired.state is LiveOpsCampaignState.EXPIRED and expired_retry == expired
    rolled = service.rollback_campaign(who, campaign_id=definition.campaign_id, version=1, reason="operator.rollback")
    checks["rollback_auditable"] = (
        rolled.state is LiveOpsCampaignState.ROLLED_BACK
        and rolled.rollback_reason == "operator.rollback"
        and any(item.action == "campaign_rolled_back" for item in service.audit_records())
    )
    killed = service.kill_campaign(who, campaign_id=definition.campaign_id, version=1)
    checks["kill_terminal_idempotent"] = (
        killed.state is LiveOpsCampaignState.KILLED
        and service.kill_campaign(who, campaign_id=definition.campaign_id, version=1) == killed
        and service.advance_campaign(who, campaign_id=definition.campaign_id, version=1) == killed
    )

    capacity_service = InMemoryLiveOpsService(clock_ms=Clock(1_500), max_trace_records=1)
    cs = season()
    ccfg = snapshot()
    ccnt = manifest()
    ccat = product()
    cevt = event_schema()
    capacity_service.register_season(who, cs)
    capacity_service.register_config_snapshot(who, ccfg)
    capacity_service.register_content_manifest(who, ccnt)
    capacity_service.register_catalog_product(who, ccat)
    capacity_service.register_event_schema(who, cevt)
    capacity_campaign = campaign(cs, ccfg, ccnt, ccat, cevt)
    checks["capacity_fail_closed"] = (
        expected_exception(LiveOpsCapacityError, lambda: capacity_service.register_campaign(who, capacity_campaign), "trace_capacity")
        and expected_exception(LiveOpsStateError, lambda: capacity_service.campaign(capacity_campaign.campaign_id, 1), "campaign_not_found")
    )

    denied = actor(permissions=("liveops.campaign.preview",), objects=(season_definition.season_id,))
    checks["authorization_fail_closed"] = expected_exception(
        LiveOpsAuthorizationError,
        lambda: InMemoryLiveOpsService(clock_ms=Clock(1_000)).register_season(denied, season_definition),
        "forbidden",
    )

    final_state = service.state_snapshot()
    rendered = json.dumps(
        {
            "season": season_definition.digest(),
            "campaign": definition.digest(),
            "preview": second_preview.digest(),
            "approval": approval.digest(),
            "activation": activation.digest(),
            "audience": eligible.digest(),
            "state": final_state.digest(),
        },
        sort_keys=True,
    ).lower()
    checks["redacted_evidence"] = "authorization" not in rendered and "password" not in rendered and "token" not in rendered

    if not all(checks.values()):
        failed = sorted(name for name, ok in checks.items() if not ok)
        raise AssertionError(f"R14.14 acceptance checks failed: {failed}")

    evidence = {
        "schema_version": 1,
        "source_sha": source_sha,
        "status": "pass",
        "checks": checks,
        "digests": {
            "season": season_definition.digest(),
            "campaign": definition.digest(),
            "preview": second_preview.digest(),
            "approval": approval.digest(),
            "activation": activation.digest(),
            "audience": eligible.digest(),
            "state": final_state.digest(),
            "dependencies": final_state.dependency_digest,
            "audit": final_state.audit_digest,
            "trace": final_state.trace_digest,
            "safe_change": SAFE_CHANGE,
        },
        "counts": {
            "seasons": len(final_state.season_digests),
            "campaigns": len(final_state.campaign_digests),
            "activations": len(final_state.activation_digests),
            "runtime_records": len(final_state.runtime_digests),
            "audit_records": len(service.audit_records()),
            "trace_records": len(service.trace()),
            "rotations": len(definition.rotations),
            "checks": len(checks),
        },
        "budgets": {
            "max_seasons": service.max_seasons,
            "max_campaigns": service.max_campaigns,
            "max_dependencies": service.max_dependencies,
            "max_activations": service.max_activations,
            "max_audit_records": service.max_audit_records,
            "max_trace_records": service.max_trace_records,
        },
        "time_authority": {
            "canonical": "utc",
            "season_display_tzid": season_definition.schedule.display_tzid,
            "campaign_display_tzid": definition.schedule.display_tzid,
            "tzdb_version": definition.schedule.tzdb_version,
        },
        "manual_state": "none",
        "provider_live_claim": False,
        "external_provider_required": False,
        "secrets_exposed": False,
        "pii_exposed": False,
        "raw_payloads_exposed": False,
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic R14.14 LiveOps acceptance evidence")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    evidence = run(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
