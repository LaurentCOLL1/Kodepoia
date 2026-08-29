from __future__ import annotations

import json
import threading

import pytest

from kodepoia.backend import InMemoryEntitlementService
from kodepoia.backend.authority import AuthorityActorContext
from kodepoia.backend.contracts import canonical_sha256
from kodepoia.backend.entitlements import (
    BillingEnvironment,
    BillingProductKind,
    BillingProvider,
    CatalogProductDefinition,
    EntitlementAccessState,
    EntitlementAuthorizationError,
    EntitlementCapacityError,
    EntitlementPolicyError,
    EntitlementStateError,
    EntitlementVerificationError,
    FixtureBillingProviderAdapter,
    ProviderPurchaseSnapshot,
    ProviderPurchaseState,
    ValidatedProviderNotification,
)


class Clock:
    def __init__(self, value: int = 1_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def admin() -> AuthorityActorContext:
    return AuthorityActorContext(
        "ops",
        "sess-ops",
        ("*",),
        (
            "google_play.sandbox",
            "google_play.test",
            "google_play.production",
            "apple_app_store.sandbox",
            "apple_app_store.test",
            "apple_app_store.production",
            "premium",
            "premium-v2",
            "premium-two",
            "subscription",
            "other",
        ),
    )


def billing_actor(
    account_id: str = "acct-a",
    *permissions: str,
    objects: tuple[str, ...] | None = None,
) -> AuthorityActorContext:
    return AuthorityActorContext(
        account_id,
        f"sess-{account_id}",
        permissions
        or (
            "billing.notification.ingest",
            "billing.entitlement.mutate",
            "billing.entitlement.read",
            "billing.reconcile",
        ),
        objects or (account_id,),
    )


def note(
    fixture_id: str,
    *,
    message_id: str | None = None,
    locator: str = "TOKEN_SECRET_A",
    product: str = "premium.sku",
    provider: BillingProvider = BillingProvider.GOOGLE_PLAY,
    environment: BillingEnvironment = BillingEnvironment.SANDBOX,
    event_type: str = "purchase_changed",
    signed_at_ms: int = 900,
) -> ValidatedProviderNotification:
    return ValidatedProviderNotification(
        provider,
        environment,
        message_id or fixture_id,
        product,
        locator,
        event_type,
        signed_at_ms,
        canonical_sha256({"fixture_id": fixture_id, "message_id": message_id or fixture_id}),
    )


def purchase(
    *,
    purchase_id: str = "purchase-1",
    product: str = "premium.sku",
    state: ProviderPurchaseState = ProviderPurchaseState.PURCHASED,
    provider: BillingProvider = BillingProvider.GOOGLE_PLAY,
    environment: BillingEnvironment = BillingEnvironment.SANDBOX,
    effective_at_ms: int = 900,
    verified_at_ms: int = 950,
    revision: int = 1,
    expires_at_ms: int | None = None,
    source: str = "snapshot-1",
) -> ProviderPurchaseSnapshot:
    return ProviderPurchaseSnapshot(
        provider,
        environment,
        purchase_id,
        product,
        state,
        effective_at_ms,
        verified_at_ms,
        revision,
        expires_at_ms,
        canonical_sha256({"source": source}),
    )


def configured_service(
    *,
    notifications: dict[str, ValidatedProviderNotification] | None = None,
    purchases: dict[str, ProviderPurchaseSnapshot] | None = None,
    product_id: str = "premium",
    entitlement_id: str = "premium-access",
    provider_product_id: str = "premium.sku",
    kind: BillingProductKind = BillingProductKind.DURABLE,
    provider: BillingProvider = BillingProvider.GOOGLE_PLAY,
    environment: BillingEnvironment = BillingEnvironment.SANDBOX,
    invalid_notification_ids: tuple[str, ...] = (),
    invalid_purchase_locators: tuple[str, ...] = (),
    clock: Clock | None = None,
    **service_kwargs,
) -> tuple[InMemoryEntitlementService, FixtureBillingProviderAdapter, Clock]:
    clock = clock or Clock()
    svc = InMemoryEntitlementService(clock_ms=clock, **service_kwargs)
    adapter = FixtureBillingProviderAdapter(
        provider=provider,
        environment=environment,
        notifications=notifications or {"n1": note("n1", provider=provider, environment=environment, product=provider_product_id)},
        purchases=purchases or {"TOKEN_SECRET_A": purchase(provider=provider, environment=environment, product=provider_product_id)},
        invalid_notification_ids=invalid_notification_ids,
        invalid_purchase_locators=invalid_purchase_locators,
    )
    svc.register_adapter(admin(), adapter)
    svc.register_product_definition(
        admin(),
        CatalogProductDefinition(
            product_id,
            1,
            entitlement_id,
            kind,
            provider,
            environment,
            provider_product_id,
        ),
    )
    return svc, adapter, clock


def ingest(
    svc: InMemoryEntitlementService,
    fixture_id: str = "n1",
    *,
    account_id: str = "acct-a",
    provider: BillingProvider = BillingProvider.GOOGLE_PLAY,
    environment: BillingEnvironment = BillingEnvironment.SANDBOX,
):
    return svc.ingest_notification(
        billing_actor(account_id),
        provider=provider,
        environment=environment,
        account_id=account_id,
        envelope={"fixture_id": fixture_id},
    )


def test_backend_package_exports_entitlement_service():
    svc = InMemoryEntitlementService(clock_ms=lambda: 1)
    assert isinstance(svc, InMemoryEntitlementService)


def test_catalog_definition_is_immutable_and_activation_can_rollback():
    svc, _, _ = configured_service()
    v1 = CatalogProductDefinition(
        "premium",
        1,
        "premium-access",
        BillingProductKind.DURABLE,
        BillingProvider.GOOGLE_PLAY,
        BillingEnvironment.SANDBOX,
        "premium.sku",
    )
    assert svc.register_product_definition(admin(), v1) == v1
    with pytest.raises(EntitlementStateError, match="catalog_version_conflict"):
        svc.register_product_definition(
            admin(),
            CatalogProductDefinition(
                "premium",
                1,
                "different-access",
                BillingProductKind.DURABLE,
                BillingProvider.GOOGLE_PLAY,
                BillingEnvironment.SANDBOX,
                "premium.sku",
            ),
        )
    v2 = CatalogProductDefinition(
        "premium",
        2,
        "premium-access",
        BillingProductKind.DURABLE,
        BillingProvider.GOOGLE_PLAY,
        BillingEnvironment.SANDBOX,
        "premium.sku",
    )
    svc.register_product_definition(admin(), v2)
    assert svc.activate_product_definition(admin(), "premium", 2).version == 2
    assert svc.activate_product_definition(admin(), "premium", 1).version == 1


def test_active_provider_product_mapping_cannot_be_ambiguous():
    svc, _, _ = configured_service()
    with pytest.raises(EntitlementStateError, match="provider_product_mapping_conflict"):
        svc.register_product_definition(
            admin(),
            CatalogProductDefinition(
                "premium-two",
                1,
                "other-access",
                BillingProductKind.DURABLE,
                BillingProvider.GOOGLE_PLAY,
                BillingEnvironment.SANDBOX,
                "premium.sku",
            ),
        )


def test_invalid_enum_contracts_fail_closed():
    with pytest.raises(EntitlementPolicyError, match="invalid_product_kind"):
        CatalogProductDefinition(
            "premium",
            1,
            "premium-access",
            "durable",  # type: ignore[arg-type]
            BillingProvider.GOOGLE_PLAY,
            BillingEnvironment.SANDBOX,
            "premium.sku",
        )
    with pytest.raises(EntitlementPolicyError, match="invalid_purchase_state"):
        ProviderPurchaseSnapshot(
            BillingProvider.GOOGLE_PLAY,
            BillingEnvironment.SANDBOX,
            "purchase-1",
            "premium.sku",
            "purchased",  # type: ignore[arg-type]
            1,
            1,
            1,
        )


def test_function_and_object_authorization_are_both_required():
    svc, _, _ = configured_service()
    wrong_object = billing_actor(
        "acct-a",
        "billing.notification.ingest",
        "billing.entitlement.mutate",
        objects=("acct-b",),
    )
    with pytest.raises(EntitlementAuthorizationError, match="forbidden"):
        svc.ingest_notification(
            wrong_object,
            provider=BillingProvider.GOOGLE_PLAY,
            environment=BillingEnvironment.SANDBOX,
            account_id="acct-a",
            envelope={"fixture_id": "n1"},
        )
    read_only = billing_actor("acct-a", "billing.entitlement.read")
    with pytest.raises(EntitlementAuthorizationError, match="forbidden"):
        svc.ingest_notification(
            read_only,
            provider=BillingProvider.GOOGLE_PLAY,
            environment=BillingEnvironment.SANDBOX,
            account_id="acct-a",
            envelope={"fixture_id": "n1"},
        )


def test_client_receipt_can_never_directly_grant_entitlement():
    svc, _, _ = configured_service()
    with pytest.raises(EntitlementAuthorizationError, match="client_receipt_grant_forbidden"):
        svc.grant_from_client_receipt("acct-a", "TOKEN_SECRET_A")


def test_invalid_notification_signature_never_queries_purchase_or_mutates():
    svc, adapter, _ = configured_service(invalid_notification_ids=("n1",))
    with pytest.raises(EntitlementVerificationError, match="invalid_notification_signature"):
        ingest(svc)
    assert adapter.purchase_fetch_count == 0
    assert svc.provider_events() == ()
    assert svc.purchase_records() == ()


def test_invalid_purchase_token_never_grants_or_records_event():
    svc, _, _ = configured_service(invalid_purchase_locators=("TOKEN_SECRET_A",))
    with pytest.raises(EntitlementVerificationError, match="invalid_purchase_token"):
        ingest(svc)
    assert svc.provider_events() == ()
    assert svc.purchase_records() == ()


def test_verified_provider_state_is_required_before_grant():
    svc, adapter, _ = configured_service()
    result = ingest(svc)
    assert adapter.purchase_fetch_count == 1
    assert result.grants_access is True
    assert result.entitlement_state is EntitlementAccessState.ACTIVE
    assert len(svc.provider_events()) == 1
    assert len(svc.purchase_records()) == 1


def test_pending_purchase_does_not_grant_access():
    svc, _, _ = configured_service(
        purchases={"TOKEN_SECRET_A": purchase(state=ProviderPurchaseState.PENDING)}
    )
    result = ingest(svc)
    assert result.entitlement_state is EntitlementAccessState.PENDING
    assert result.grants_access is False


def test_pending_to_purchased_transition_grants_after_reverification():
    notifications = {
        "pending": note("pending", message_id="msg-pending"),
        "purchased": note("purchased", message_id="msg-purchased", signed_at_ms=1_100),
    }
    svc, adapter, _ = configured_service(
        notifications=notifications,
        purchases={"TOKEN_SECRET_A": purchase(state=ProviderPurchaseState.PENDING, revision=1)},
    )
    assert ingest(svc, "pending").grants_access is False
    adapter.replace_purchase(
        "TOKEN_SECRET_A",
        purchase(
            state=ProviderPurchaseState.PURCHASED,
            revision=2,
            effective_at_ms=1_050,
            verified_at_ms=1_100,
            source="snapshot-2",
        ),
    )
    result = ingest(svc, "purchased")
    assert result.grants_access is True
    assert result.entitlement_state is EntitlementAccessState.ACTIVE


def test_duplicate_message_is_mutation_free_and_skips_second_provider_fetch():
    svc, adapter, _ = configured_service()
    first = ingest(svc)
    state_before = svc.state_digest()
    fetches_before = adapter.purchase_fetch_count
    replay = ingest(svc)
    assert replay.replayed is True
    assert replay.sequence == first.sequence
    assert svc.state_digest() == state_before
    assert adapter.purchase_fetch_count == fetches_before
    assert len(svc.provider_events()) == 1


def test_message_id_rebind_to_another_account_is_rejected():
    svc, _, _ = configured_service()
    ingest(svc, account_id="acct-a")
    with pytest.raises(EntitlementStateError, match="message_id_conflict"):
        ingest(svc, account_id="acct-b")
    assert {record.account_id for record in svc.purchase_records()} == {"acct-a"}


def test_verified_purchase_identity_cannot_rebind_to_another_account():
    notifications = {
        "n1": note("n1", message_id="msg-a"),
        "n2": note("n2", message_id="msg-b"),
    }
    svc, _, _ = configured_service(notifications=notifications)
    ingest(svc, "n1", account_id="acct-a")
    with pytest.raises(EntitlementAuthorizationError, match="purchase_account_rebind_forbidden"):
        ingest(svc, "n2", account_id="acct-b")


def test_out_of_order_provider_snapshot_cannot_regress_newer_state():
    notifications = {
        "new": note("new", message_id="msg-new", signed_at_ms=2_000),
        "old": note("old", message_id="msg-old", signed_at_ms=1_000),
    }
    svc, adapter, _ = configured_service(
        notifications=notifications,
        purchases={
            "TOKEN_SECRET_A": purchase(
                state=ProviderPurchaseState.PURCHASED,
                revision=2,
                effective_at_ms=1_900,
                verified_at_ms=2_000,
                source="new",
            )
        },
    )
    assert ingest(svc, "new").grants_access is True
    adapter.replace_purchase(
        "TOKEN_SECRET_A",
        purchase(
            state=ProviderPurchaseState.PENDING,
            revision=1,
            effective_at_ms=900,
            verified_at_ms=1_000,
            source="old",
        ),
    )
    stale = ingest(svc, "old")
    assert stale.stale is True
    assert stale.grants_access is True
    assert svc.purchase_records()[0].provider_revision == 2


def test_same_provider_revision_with_different_state_is_conflict():
    notifications = {
        "a": note("a", message_id="msg-a"),
        "b": note("b", message_id="msg-b", signed_at_ms=1_100),
    }
    svc, adapter, _ = configured_service(notifications=notifications)
    ingest(svc, "a")
    adapter.replace_purchase(
        "TOKEN_SECRET_A",
        purchase(
            state=ProviderPurchaseState.REFUNDED,
            revision=1,
            effective_at_ms=900,
            verified_at_ms=1_100,
            source="conflicting",
        ),
    )
    with pytest.raises(EntitlementStateError, match="provider_revision_conflict"):
        ingest(svc, "b")


@pytest.mark.parametrize("state", [ProviderPurchaseState.REFUNDED, ProviderPurchaseState.REVOKED])
def test_refund_or_revocation_removes_access(state: ProviderPurchaseState):
    notifications = {
        "buy": note("buy", message_id="msg-buy"),
        "remove": note("remove", message_id="msg-remove", signed_at_ms=1_200),
    }
    svc, adapter, _ = configured_service(notifications=notifications)
    assert ingest(svc, "buy").grants_access is True
    adapter.replace_purchase(
        "TOKEN_SECRET_A",
        purchase(
            state=state,
            revision=2,
            effective_at_ms=1_150,
            verified_at_ms=1_200,
            source=state.value,
        ),
    )
    result = ingest(svc, "remove")
    assert result.entitlement_state is EntitlementAccessState.REVOKED
    assert result.grants_access is False


def test_subscription_expiry_is_server_clock_authoritative():
    clock = Clock(1_000)
    svc, _, _ = configured_service(
        kind=BillingProductKind.SUBSCRIPTION,
        product_id="subscription",
        entitlement_id="subscription-access",
        provider_product_id="subscription.sku",
        notifications={"n1": note("n1", product="subscription.sku")},
        purchases={
            "TOKEN_SECRET_A": purchase(
                product="subscription.sku",
                expires_at_ms=1_500,
            )
        },
        clock=clock,
    )
    assert ingest(svc).grants_access is True
    clock.value = 1_500
    snapshot = svc.entitlement(
        billing_actor("acct-a"),
        account_id="acct-a",
        entitlement_id="subscription-access",
    )
    assert snapshot is not None
    assert snapshot.state is EntitlementAccessState.EXPIRED
    assert snapshot.grants_access is False


def test_grace_state_grants_access_until_expiry():
    clock = Clock(1_000)
    svc, _, _ = configured_service(
        kind=BillingProductKind.SUBSCRIPTION,
        product_id="subscription",
        entitlement_id="subscription-access",
        provider_product_id="subscription.sku",
        notifications={"n1": note("n1", product="subscription.sku")},
        purchases={
            "TOKEN_SECRET_A": purchase(
                product="subscription.sku",
                state=ProviderPurchaseState.GRACE,
                expires_at_ms=1_500,
            )
        },
        clock=clock,
    )
    result = ingest(svc)
    assert result.entitlement_state is EntitlementAccessState.GRACE
    assert result.grants_access is True


def test_canceled_subscription_keeps_access_only_until_expiry():
    clock = Clock(1_000)
    svc, _, _ = configured_service(
        kind=BillingProductKind.SUBSCRIPTION,
        product_id="subscription",
        entitlement_id="subscription-access",
        provider_product_id="subscription.sku",
        notifications={"n1": note("n1", product="subscription.sku")},
        purchases={
            "TOKEN_SECRET_A": purchase(
                product="subscription.sku",
                state=ProviderPurchaseState.CANCELED,
                expires_at_ms=1_500,
            )
        },
        clock=clock,
    )
    assert ingest(svc).grants_access is True
    clock.value = 1_500
    snapshot = svc.entitlement(
        billing_actor("acct-a"),
        account_id="acct-a",
        entitlement_id="subscription-access",
    )
    assert snapshot is not None and snapshot.grants_access is False


def test_subscription_state_without_expiry_fails_closed():
    svc, _, _ = configured_service(
        kind=BillingProductKind.SUBSCRIPTION,
        product_id="subscription",
        entitlement_id="subscription-access",
        provider_product_id="subscription.sku",
        notifications={"n1": note("n1", product="subscription.sku")},
        purchases={
            "TOKEN_SECRET_A": purchase(product="subscription.sku", expires_at_ms=None)
        },
    )
    with pytest.raises(EntitlementVerificationError, match="subscription_expiry_required"):
        ingest(svc)
    assert svc.purchase_records() == ()


def test_environment_isolation_rejects_unregistered_production_path():
    svc, _, _ = configured_service()
    with pytest.raises(EntitlementStateError, match="provider_adapter_not_registered"):
        ingest(svc, environment=BillingEnvironment.PRODUCTION)


def test_notification_product_must_match_verified_purchase():
    svc, _, _ = configured_service(
        notifications={"n1": note("n1", product="premium.sku")},
        purchases={"TOKEN_SECRET_A": purchase(product="other.sku")},
    )
    with pytest.raises(EntitlementVerificationError, match="provider_product_mismatch"):
        ingest(svc)


def test_reconciliation_converges_without_notification_and_is_idempotent():
    notifications = {"buy": note("buy", message_id="msg-buy")}
    svc, adapter, _ = configured_service(notifications=notifications)
    assert ingest(svc, "buy").grants_access is True
    adapter.replace_purchase(
        "TOKEN_SECRET_A",
        purchase(
            state=ProviderPurchaseState.REVOKED,
            revision=2,
            effective_at_ms=1_100,
            verified_at_ms=1_150,
            source="reconcile-revoked",
        ),
    )
    fetches_before = adapter.purchase_fetch_count
    result = svc.reconcile_purchase(
        billing_actor("acct-a"),
        provider=BillingProvider.GOOGLE_PLAY,
        environment=BillingEnvironment.SANDBOX,
        account_id="acct-a",
        purchase_locator="TOKEN_SECRET_A",
        reconciliation_id="reconcile-1",
    )
    assert result.reconciled is True
    assert result.entitlement_state is EntitlementAccessState.REVOKED
    replay = svc.reconcile_purchase(
        billing_actor("acct-a"),
        provider=BillingProvider.GOOGLE_PLAY,
        environment=BillingEnvironment.SANDBOX,
        account_id="acct-a",
        purchase_locator="TOKEN_SECRET_A",
        reconciliation_id="reconcile-1",
    )
    assert replay.replayed is True
    assert adapter.purchase_fetch_count == fetches_before + 1


def test_reconciliation_id_cannot_rebind_request():
    purchases = {
        "TOKEN_SECRET_A": purchase(purchase_id="purchase-1"),
        "TOKEN_SECRET_B": purchase(purchase_id="purchase-2", source="purchase-2"),
    }
    svc, _, _ = configured_service(purchases=purchases)
    svc.reconcile_purchase(
        billing_actor("acct-a"),
        provider=BillingProvider.GOOGLE_PLAY,
        environment=BillingEnvironment.SANDBOX,
        account_id="acct-a",
        purchase_locator="TOKEN_SECRET_A",
        reconciliation_id="same-reconcile",
    )
    with pytest.raises(EntitlementStateError, match="reconciliation_id_conflict"):
        svc.reconcile_purchase(
            billing_actor("acct-a"),
            provider=BillingProvider.GOOGLE_PLAY,
            environment=BillingEnvironment.SANDBOX,
            account_id="acct-a",
            purchase_locator="TOKEN_SECRET_B",
            reconciliation_id="same-reconcile",
        )


def test_catalog_capacity_is_bounded():
    svc, _, _ = configured_service(max_catalog_versions=1)
    with pytest.raises(EntitlementCapacityError, match="catalog_capacity"):
        svc.register_product_definition(
            admin(),
            CatalogProductDefinition(
                "premium",
                2,
                "premium-access",
                BillingProductKind.DURABLE,
                BillingProvider.GOOGLE_PLAY,
                BillingEnvironment.SANDBOX,
                "premium.sku",
            ),
        )


def test_provider_event_capacity_is_bounded():
    notifications = {
        "a": note("a", message_id="msg-a"),
        "b": note("b", message_id="msg-b"),
    }
    svc, _, _ = configured_service(
        notifications=notifications,
        max_provider_events=1,
    )
    ingest(svc, "a")
    with pytest.raises(EntitlementCapacityError, match="provider_event_capacity"):
        ingest(svc, "b")


def test_purchase_capacity_is_bounded():
    notifications = {
        "a": note("a", message_id="msg-a", locator="TOKEN_SECRET_A"),
        "b": note("b", message_id="msg-b", locator="TOKEN_SECRET_B"),
    }
    purchases = {
        "TOKEN_SECRET_A": purchase(purchase_id="purchase-1"),
        "TOKEN_SECRET_B": purchase(purchase_id="purchase-2", source="p2"),
    }
    svc, _, _ = configured_service(
        notifications=notifications,
        purchases=purchases,
        max_purchases=1,
    )
    ingest(svc, "a")
    with pytest.raises(EntitlementCapacityError, match="purchase_capacity"):
        ingest(svc, "b")


def test_account_capacity_is_bounded():
    notifications = {
        "a": note("a", message_id="msg-a", locator="TOKEN_SECRET_A"),
        "b": note("b", message_id="msg-b", locator="TOKEN_SECRET_B"),
    }
    purchases = {
        "TOKEN_SECRET_A": purchase(purchase_id="purchase-1"),
        "TOKEN_SECRET_B": purchase(purchase_id="purchase-2", source="p2"),
    }
    svc, _, _ = configured_service(
        notifications=notifications,
        purchases=purchases,
        max_accounts=1,
    )
    ingest(svc, "a", account_id="acct-a")
    with pytest.raises(EntitlementCapacityError, match="account_capacity"):
        ingest(svc, "b", account_id="acct-b")


def test_invalid_server_clock_fails_before_service_mutation():
    clock = Clock(-1)
    svc, _, _ = configured_service(clock=clock)
    with pytest.raises(EntitlementPolicyError, match="invalid_server_clock"):
        ingest(svc)
    assert svc.provider_events() == ()
    assert svc.purchase_records() == ()


def test_purchase_locator_is_absent_from_state_trace_and_evidence():
    secret = "SUPER_SECRET_PURCHASE_TOKEN_987"
    svc, _, _ = configured_service(
        notifications={"n1": note("n1", locator=secret)},
        purchases={secret: purchase()},
    )
    ingest(svc)
    blob = json.dumps(
        {
            "state": svc.canonical_state(),
            "trace": svc.trace(),
            "evidence": svc.redacted_evidence(),
        },
        sort_keys=True,
    )
    assert secret not in blob
    assert "provider_live_claim" in blob
    assert svc.redacted_evidence()["provider_live_claim"] is False
    assert svc.redacted_evidence()["secrets_exposed"] is False


def test_deterministic_state_and_trace_digests():
    first, _, _ = configured_service()
    second, _, _ = configured_service()
    ingest(first)
    ingest(second)
    assert first.state_digest() == second.state_digest()
    assert first.trace_digest() == second.trace_digest()


def test_concurrent_duplicate_notification_commits_once():
    svc, _, _ = configured_service()
    results = []
    errors = []

    def worker() -> None:
        try:
            results.append(ingest(svc))
        except BaseException as exc:  # pragma: no cover - diagnostic collection
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert len(results) == 4
    assert len(svc.provider_events()) == 1
    assert len(svc.purchase_records()) == 1
    assert sum(result.replayed for result in results) >= 3


def test_apple_notification_contract_uses_same_authoritative_boundary():
    provider = BillingProvider.APPLE_APP_STORE
    environment = BillingEnvironment.SANDBOX
    notification = note(
        "apple-n1",
        message_id="4f668af1-0a58-4b9a-a861-4b9c84b21c1f",
        locator="APPLE_JWS_TRANSACTION_LOCATOR",
        product="com.kodepoia.premium",
        provider=provider,
        environment=environment,
        event_type="DID_RENEW",
    )
    snapshot = purchase(
        purchase_id="200000000000001",
        product="com.kodepoia.premium",
        provider=provider,
        environment=environment,
    )
    svc, _, _ = configured_service(
        provider=provider,
        environment=environment,
        notifications={"apple-n1": notification},
        purchases={"APPLE_JWS_TRANSACTION_LOCATOR": snapshot},
        provider_product_id="com.kodepoia.premium",
    )
    result = ingest(
        svc,
        "apple-n1",
        provider=provider,
        environment=environment,
    )
    assert result.grants_access is True
    assert svc.provider_events()[0].message_id == notification.message_id
