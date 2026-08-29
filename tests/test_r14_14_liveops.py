from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.content_delivery import (
    ContentBundleDefinition,
    ContentManifest,
    ContentSignatureState,
)
from kodepoia.backend.contracts import BackendEnvironmentKind, canonical_sha256
from kodepoia.backend.entitlements import (
    BillingEnvironment,
    BillingProductKind,
    BillingProvider,
    CatalogProductDefinition,
)
from kodepoia.backend.event_pipeline import (
    EventFieldType,
    EventPrivacyClass,
    EventSchemaDefinition,
    EventSchemaField,
)
from kodepoia.backend.liveops import (
    CatalogProductReference,
    ConfigSnapshotReference,
    ContentManifestReference,
    EventContractReference,
    InMemoryLiveOpsService,
    LiveOpsActivationRecord,
    LiveOpsApproval,
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


SAFE_CHANGE = canonical_sha256({"safe_change": "r14.14"})


class Clock:
    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


@pytest.fixture
def actor() -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id="operator.1",
        session_id="session.1",
        permissions=("*",),
        authorized_object_ids=(
            "season.2026.autumn",
            "config.liveops.1",
            "config.other",
            "manifest.liveops.1",
            "product.liveops.1",
            "schema.liveops.1",
            "campaign.autumn.1",
            "campaign.one",
            "campaign.two",
            "test",
            "production",
            "liveops.audience",
        ),
    )


def _config_snapshot(*, environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST) -> ConfigSnapshot:
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
        snapshot_id="config.liveops.1",
        revision=1,
        environment=environment,
        flags=(flag,),
        created_at_ms=100,
    )


def _manifest(*, environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST) -> ContentManifest:
    payload = b"r14.14-content"
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
        environment=environment,
        bundles=(bundle,),
        min_client_version=1,
        max_client_version=10,
        schema_version=1,
        created_at_ms=100,
    )


def _product(*, environment: BillingEnvironment = BillingEnvironment.TEST, product_id: str = "product.liveops.1") -> CatalogProductDefinition:
    return CatalogProductDefinition(
        product_id=product_id,
        version=1,
        entitlement_id="entitlement.liveops.1",
        kind=BillingProductKind.DURABLE,
        provider=BillingProvider.GOOGLE_PLAY,
        environment=environment,
        provider_product_id=f"provider.{product_id}",
    )


def _event_schema(*, environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST) -> EventSchemaDefinition:
    return EventSchemaDefinition(
        schema_id="schema.liveops.1",
        event_type="liveops.campaign.entered",
        version=1,
        environment=environment,
        fields=(
            EventSchemaField(
                name="campaign_id",
                value_type=EventFieldType.STRING,
                privacy=EventPrivacyClass.INTERNAL,
            ),
        ),
    )


def _season(*, environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST) -> LiveOpsSeasonDefinition:
    return LiveOpsSeasonDefinition(
        season_id="season.2026.autumn",
        version=1,
        environment=environment,
        schedule=LiveOpsScheduleWindow(
            start_at_utc_ms=1_000,
            end_at_utc_ms=10_000,
            display_tzid="Europe/Paris",
            tzdb_version="2026c",
        ),
        created_at_ms=100,
    )


def _register_dependencies(
    service: InMemoryLiveOpsService,
    actor: AuthorityActorContext,
    *,
    environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST,
    billing_environment: BillingEnvironment = BillingEnvironment.TEST,
) -> tuple[LiveOpsSeasonDefinition, ConfigSnapshot, ContentManifest, CatalogProductDefinition, EventSchemaDefinition]:
    season = _season(environment=environment)
    snapshot = _config_snapshot(environment=environment)
    manifest = _manifest(environment=environment)
    product = _product(environment=billing_environment)
    event = _event_schema(environment=environment)
    service.register_season(actor, season)
    service.register_config_snapshot(actor, snapshot)
    service.register_content_manifest(actor, manifest)
    service.register_catalog_product(actor, product)
    service.register_event_schema(actor, event)
    return season, snapshot, manifest, product, event


def _campaign(
    season: LiveOpsSeasonDefinition,
    snapshot: ConfigSnapshot,
    manifest: ContentManifest,
    product: CatalogProductDefinition,
    event: EventSchemaDefinition,
    *,
    campaign_id: str = "campaign.autumn.1",
    environment: BackendEnvironmentKind = BackendEnvironmentKind.TEST,
    start_at_utc_ms: int = 2_000,
    end_at_utc_ms: int = 8_000,
    audience: LiveOpsAudience | None = None,
    rotations: tuple[LiveOpsRotation, ...] = (),
) -> LiveOpsCampaignDefinition:
    return LiveOpsCampaignDefinition(
        campaign_id=campaign_id,
        version=1,
        season=LiveOpsSeasonReference.from_season(season),
        environment=environment,
        schedule=LiveOpsScheduleWindow(
            start_at_utc_ms=start_at_utc_ms,
            end_at_utc_ms=end_at_utc_ms,
            display_tzid="America/Edmonton",
            tzdb_version="2026c",
        ),
        config_snapshot=ConfigSnapshotReference.from_snapshot(snapshot),
        content_manifest=ContentManifestReference.from_manifest(manifest),
        catalog_products=(CatalogProductReference.from_product(product),),
        event_contracts=(EventContractReference.from_schema(event),),
        rotations=rotations,
        audience=audience,
        created_at_ms=100,
    )


def _registered_campaign(
    clock: Clock,
    actor: AuthorityActorContext,
    *,
    start_at_utc_ms: int = 2_000,
    end_at_utc_ms: int = 8_000,
    audience: LiveOpsAudience | None = None,
    rotations: tuple[LiveOpsRotation, ...] = (),
) -> tuple[InMemoryLiveOpsService, LiveOpsCampaignDefinition, ConfigSnapshot]:
    service = InMemoryLiveOpsService(clock_ms=clock)
    season, snapshot, manifest, product, event = _register_dependencies(service, actor)
    campaign = _campaign(
        season,
        snapshot,
        manifest,
        product,
        event,
        start_at_utc_ms=start_at_utc_ms,
        end_at_utc_ms=end_at_utc_ms,
        audience=audience,
        rotations=rotations,
    )
    service.register_campaign(actor, campaign)
    return service, campaign, snapshot


def _approved(
    service: InMemoryLiveOpsService,
    actor: AuthorityActorContext,
    campaign: LiveOpsCampaignDefinition,
    *,
    approval_id: str = "approval.liveops.1",
) -> LiveOpsApproval:
    preview = service.preview_campaign(actor, campaign_id=campaign.campaign_id, version=campaign.version)
    return service.approve_campaign(
        actor,
        preview=preview,
        approval_id=approval_id,
        safe_change_digest=SAFE_CHANGE,
    )


def test_schedule_uses_utc_authority_and_preserves_versioned_display_timezone() -> None:
    window = LiveOpsScheduleWindow(1_000, 2_000, "America/Edmonton", "2026c")
    assert window.contains(1_000)
    assert window.contains(1_999)
    assert not window.contains(2_000)
    assert window.display_tzid == "America/Edmonton"
    assert window.tzdb_version == "2026c"
    with pytest.raises(LiveOpsPolicyError, match="schedule_end_must_follow_start"):
        LiveOpsScheduleWindow(1_000, 1_000, "UTC", "2026c")


def test_season_is_immutable_versioned_authority(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service = InMemoryLiveOpsService(clock_ms=clock)
    season = _season()
    assert service.register_season(actor, season) == season
    assert service.register_season(actor, season) == season
    rebound = replace(season, schedule=LiveOpsScheduleWindow(1_000, 11_000, "Europe/Paris", "2026c"))
    with pytest.raises(LiveOpsStateError, match="season_version_rebind"):
        service.register_season(actor, rebound)


def test_campaign_requires_registered_exact_dependencies_and_season(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service = InMemoryLiveOpsService(clock_ms=clock)
    season = _season()
    snapshot = _config_snapshot()
    manifest = _manifest()
    product = _product()
    event = _event_schema()
    campaign = _campaign(season, snapshot, manifest, product, event)
    with pytest.raises(LiveOpsStateError, match="season_not_found"):
        service.register_campaign(actor, campaign)
    service.register_season(actor, season)
    with pytest.raises(LiveOpsStateError, match="config_dependency_unavailable"):
        service.register_campaign(actor, campaign)


def test_campaign_window_must_be_contained_by_exact_season(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service = InMemoryLiveOpsService(clock_ms=clock)
    season, snapshot, manifest, product, event = _register_dependencies(service, actor)
    outside = _campaign(season, snapshot, manifest, product, event, start_at_utc_ms=900, end_at_utc_ms=8_000)
    with pytest.raises(LiveOpsStateError, match="campaign_outside_season_schedule"):
        service.register_campaign(actor, outside)


def test_backend_and_billing_environment_isolation_is_fail_closed() -> None:
    season = _season(environment=BackendEnvironmentKind.TEST)
    snapshot = _config_snapshot(environment=BackendEnvironmentKind.TEST)
    manifest = _manifest(environment=BackendEnvironmentKind.TEST)
    event = _event_schema(environment=BackendEnvironmentKind.TEST)
    production_product = _product(environment=BillingEnvironment.PRODUCTION)
    with pytest.raises(LiveOpsPolicyError, match="nonproduction_campaign_rejects_production_billing"):
        _campaign(season, snapshot, manifest, production_product, event)

    prod_season = _season(environment=BackendEnvironmentKind.PRODUCTION)
    prod_snapshot = _config_snapshot(environment=BackendEnvironmentKind.PRODUCTION)
    prod_manifest = _manifest(environment=BackendEnvironmentKind.PRODUCTION)
    prod_event = _event_schema(environment=BackendEnvironmentKind.PRODUCTION)
    test_product = _product(environment=BillingEnvironment.TEST)
    with pytest.raises(LiveOpsPolicyError, match="production_campaign_requires_production_billing"):
        _campaign(
            prod_season,
            prod_snapshot,
            prod_manifest,
            test_product,
            prod_event,
            environment=BackendEnvironmentKind.PRODUCTION,
        )


def test_preview_is_non_mutating_and_binding_digest_is_clock_stable(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service, campaign, _snapshot = _registered_campaign(clock, actor)
    before = service.state_snapshot().digest()
    first = service.preview_campaign(actor, campaign_id=campaign.campaign_id, version=1)
    clock.value = 1_700
    second = service.preview_campaign(actor, campaign_id=campaign.campaign_id, version=1)
    assert first.mutation_count == 0 == second.mutation_count
    assert first.evaluated_at_ms != second.evaluated_at_ms
    assert first.digest() == second.digest()
    assert service.state_snapshot().digest() == before


def test_preview_becomes_stale_when_schedule_state_changes(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service, campaign, _snapshot = _registered_campaign(clock, actor)
    preview = service.preview_campaign(actor, campaign_id=campaign.campaign_id, version=1)
    assert preview.expected_state is LiveOpsCampaignState.SCHEDULED
    clock.value = 2_500
    with pytest.raises(LiveOpsStateError, match="stale_preview"):
        service.approve_campaign(
            actor,
            preview=preview,
            approval_id="approval.stale",
            safe_change_digest=SAFE_CHANGE,
        )


def test_approval_binds_preview_campaign_and_safechange_idempotently(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service, campaign, _snapshot = _registered_campaign(clock, actor)
    preview = service.preview_campaign(actor, campaign_id=campaign.campaign_id, version=1)
    first = service.approve_campaign(actor, preview=preview, approval_id="approval.same", safe_change_digest=SAFE_CHANGE)
    clock.value = 1_600
    second = service.approve_campaign(actor, preview=preview, approval_id="approval.same", safe_change_digest=SAFE_CHANGE)
    assert second == first
    with pytest.raises(LiveOpsStateError, match="approval_id_rebind"):
        service.approve_campaign(
            actor,
            preview=preview,
            approval_id="approval.same",
            safe_change_digest=canonical_sha256({"other": True}),
        )


def test_activation_requires_registered_approval(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service, campaign, _snapshot = _registered_campaign(clock, actor)
    with pytest.raises(LiveOpsAuthorizationError, match="activation_requires_approval"):
        service.activate_campaign(
            actor,
            campaign_id=campaign.campaign_id,
            version=1,
            activation_id="activation.noapproval",
            approval=None,  # type: ignore[arg-type]
        )


def test_activation_id_is_idempotent_across_clock_changes(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service, campaign, _snapshot = _registered_campaign(clock, actor)
    approval = _approved(service, actor, campaign)
    first = service.activate_campaign(
        actor,
        campaign_id=campaign.campaign_id,
        version=1,
        activation_id="activation.same",
        approval=approval,
    )
    assert first.state is LiveOpsCampaignState.SCHEDULED
    clock.value = 2_500
    second = service.activate_campaign(
        actor,
        campaign_id=campaign.campaign_id,
        version=1,
        activation_id="activation.same",
        approval=approval,
    )
    assert second == first
    assert service.runtime(campaign.campaign_id, 1).state is LiveOpsCampaignState.SCHEDULED


def test_activation_id_rebind_is_rejected(actor: AuthorityActorContext) -> None:
    clock = Clock(2_500)
    service = InMemoryLiveOpsService(clock_ms=clock)
    season, snapshot, manifest, product, event = _register_dependencies(service, actor)
    first_campaign = _campaign(season, snapshot, manifest, product, event, campaign_id="campaign.one")
    second_campaign = _campaign(season, snapshot, manifest, product, event, campaign_id="campaign.two")
    service.register_campaign(actor, first_campaign)
    service.register_campaign(actor, second_campaign)
    first_approval = _approved(service, actor, first_campaign, approval_id="approval.one")
    second_approval = _approved(service, actor, second_campaign, approval_id="approval.two")
    service.activate_campaign(actor, campaign_id="campaign.one", version=1, activation_id="activation.shared", approval=first_approval)
    with pytest.raises(LiveOpsStateError, match="activation_id_rebind"):
        service.activate_campaign(actor, campaign_id="campaign.two", version=1, activation_id="activation.shared", approval=second_approval)


def test_scheduler_advances_active_then_expires(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service, campaign, _snapshot = _registered_campaign(clock, actor)
    approval = _approved(service, actor, campaign)
    service.activate_campaign(actor, campaign_id=campaign.campaign_id, version=1, activation_id="activation.schedule", approval=approval)
    clock.value = 2_000
    assert service.advance_campaign(actor, campaign_id=campaign.campaign_id, version=1).state is LiveOpsCampaignState.ACTIVE
    clock.value = 8_000
    assert service.advance_campaign(actor, campaign_id=campaign.campaign_id, version=1).state is LiveOpsCampaignState.EXPIRED
    assert service.advance_campaign(actor, campaign_id=campaign.campaign_id, version=1).state is LiveOpsCampaignState.EXPIRED


def test_pause_resume_and_rollback_are_explicit(actor: AuthorityActorContext) -> None:
    clock = Clock(2_500)
    service, campaign, _snapshot = _registered_campaign(clock, actor)
    approval = _approved(service, actor, campaign)
    service.activate_campaign(actor, campaign_id=campaign.campaign_id, version=1, activation_id="activation.pause", approval=approval)
    assert service.pause_campaign(actor, campaign_id=campaign.campaign_id, version=1).state is LiveOpsCampaignState.PAUSED
    assert service.resume_campaign(actor, campaign_id=campaign.campaign_id, version=1).state is LiveOpsCampaignState.ACTIVE
    rolled = service.rollback_campaign(actor, campaign_id=campaign.campaign_id, version=1, reason="operator.rollback")
    assert rolled.state is LiveOpsCampaignState.ROLLED_BACK
    assert rolled.rollback_reason == "operator.rollback"
    assert service.rollback_campaign(actor, campaign_id=campaign.campaign_id, version=1, reason="other.reason") == rolled


def test_kill_is_explicit_terminal_state(actor: AuthorityActorContext) -> None:
    clock = Clock(2_500)
    service, campaign, _snapshot = _registered_campaign(clock, actor)
    approval = _approved(service, actor, campaign)
    service.activate_campaign(actor, campaign_id=campaign.campaign_id, version=1, activation_id="activation.kill", approval=approval)
    killed = service.kill_campaign(actor, campaign_id=campaign.campaign_id, version=1)
    assert killed.state is LiveOpsCampaignState.KILLED
    assert service.kill_campaign(actor, campaign_id=campaign.campaign_id, version=1) == killed
    assert service.advance_campaign(actor, campaign_id=campaign.campaign_id, version=1) == killed


def test_rotations_are_bounded_nonoverlapping_and_queryable(actor: AuthorityActorContext) -> None:
    clock = Clock(2_500)
    service = InMemoryLiveOpsService(clock_ms=clock)
    season, snapshot, manifest, product, event = _register_dependencies(service, actor)
    manifest_ref = ContentManifestReference.from_manifest(manifest)
    snapshot_ref = ConfigSnapshotReference.from_snapshot(snapshot)
    rotations = (
        LiveOpsRotation("rotation.a", 2_000, 4_000, content_manifest_digest=manifest_ref.digest),
        LiveOpsRotation("rotation.b", 4_000, 6_000, config_snapshot_digest=snapshot_ref.digest),
    )
    campaign = _campaign(season, snapshot, manifest, product, event, rotations=rotations)
    service.register_campaign(actor, campaign)
    assert service.active_rotation(campaign_id=campaign.campaign_id, version=1).rotation_id == "rotation.a"
    clock.value = 4_500
    assert service.active_rotation(campaign_id=campaign.campaign_id, version=1).rotation_id == "rotation.b"
    with pytest.raises(LiveOpsPolicyError, match="rotation_overlap"):
        _campaign(
            season,
            snapshot,
            manifest,
            product,
            event,
            rotations=(
                LiveOpsRotation("rotation.x", 2_000, 5_000, content_manifest_digest=manifest_ref.digest),
                LiveOpsRotation("rotation.y", 4_000, 6_000, config_snapshot_digest=snapshot_ref.digest),
            ),
        )


def test_capacity_failure_does_not_partially_register_campaign(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service = InMemoryLiveOpsService(clock_ms=clock, max_trace_records=1)
    season, snapshot, manifest, product, event = _register_dependencies(service, actor)
    campaign = _campaign(season, snapshot, manifest, product, event)
    with pytest.raises(LiveOpsCapacityError, match="trace_capacity"):
        service.register_campaign(actor, campaign)
    with pytest.raises(LiveOpsStateError, match="campaign_not_found"):
        service.campaign(campaign.campaign_id, 1)


def test_function_and_object_authorization_are_both_required(actor: AuthorityActorContext) -> None:
    clock = Clock(1_500)
    service = InMemoryLiveOpsService(clock_ms=clock)
    season = _season()
    denied_function = AuthorityActorContext(
        account_id="operator.2",
        session_id="session.2",
        permissions=("liveops.campaign.register",),
        authorized_object_ids=(season.season_id,),
    )
    with pytest.raises(LiveOpsAuthorizationError, match="forbidden"):
        service.register_season(denied_function, season)
    denied_object = AuthorityActorContext(
        account_id="operator.3",
        session_id="session.3",
        permissions=("liveops.season.register",),
        authorized_object_ids=("other.season",),
    )
    with pytest.raises(LiveOpsAuthorizationError, match="forbidden"):
        service.register_season(denied_object, season)
    assert service.register_season(actor, season) == season


def test_audience_targeting_delegates_to_active_remote_config_snapshot(actor: AuthorityActorContext) -> None:
    clock = Clock(2_500)
    audience = LiveOpsAudience(flag_id="liveops.audience", allowed_variants=("eligible",))
    service, campaign, snapshot = _registered_campaign(clock, actor, audience=audience)
    remote = InMemoryRemoteConfigService(clock_ms=clock)
    remote.register_snapshot(actor, snapshot)
    remote.activate_snapshot(actor, environment=BackendEnvironmentKind.TEST, snapshot_id=snapshot.snapshot_id)

    eligible = service.evaluate_audience(
        actor,
        campaign_id=campaign.campaign_id,
        version=1,
        remote_config=remote,
        context=EvaluationContext(targeting_key="user.1", attributes={"country": "FR"}),
    )
    control = service.evaluate_audience(
        actor,
        campaign_id=campaign.campaign_id,
        version=1,
        remote_config=remote,
        context=EvaluationContext(targeting_key="user.2", attributes={"country": "DE"}),
    )
    assert eligible.eligible is True
    assert eligible.variant == "eligible"
    assert control.eligible is False
    assert control.variant == "control"
    assert eligible.context_digest != canonical_sha256({"targeting_key": "user.1"})


def test_audience_rejects_different_active_snapshot(actor: AuthorityActorContext) -> None:
    clock = Clock(2_500)
    audience = LiveOpsAudience(flag_id="liveops.audience", allowed_variants=("eligible",))
    service, campaign, _snapshot = _registered_campaign(clock, actor, audience=audience)
    other = replace(_config_snapshot(), snapshot_id="config.other", revision=2)
    remote = InMemoryRemoteConfigService(clock_ms=clock)
    remote.register_snapshot(actor, other)
    remote.activate_snapshot(actor, environment=BackendEnvironmentKind.TEST, snapshot_id=other.snapshot_id)
    with pytest.raises(LiveOpsStateError, match="audience_config_snapshot_mismatch"):
        service.evaluate_audience(
            actor,
            campaign_id=campaign.campaign_id,
            version=1,
            remote_config=remote,
            context=EvaluationContext(targeting_key="user.1", attributes={"country": "FR"}),
        )


def test_state_snapshot_binds_season_campaign_runtime_dependencies_and_audit(actor: AuthorityActorContext) -> None:
    clock = Clock(2_500)
    service, campaign, _snapshot = _registered_campaign(clock, actor)
    before = service.state_snapshot()
    assert len(before.season_digests) == 1
    assert len(before.campaign_digests) == 1
    approval = _approved(service, actor, campaign)
    activation: LiveOpsActivationRecord = service.activate_campaign(
        actor,
        campaign_id=campaign.campaign_id,
        version=1,
        activation_id="activation.snapshot",
        approval=approval,
    )
    after = service.state_snapshot()
    assert activation.digest() in after.activation_digests
    assert len(after.runtime_digests) == 1
    assert after.audit_digest != before.audit_digest
    assert after.trace_digest != before.trace_digest
