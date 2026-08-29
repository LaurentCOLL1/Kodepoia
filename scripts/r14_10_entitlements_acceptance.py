from __future__ import annotations

import argparse
import json
from pathlib import Path

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
    EntitlementStateError,
    EntitlementVerificationError,
    FixtureBillingProviderAdapter,
    InMemoryEntitlementService,
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
            "google_play.production",
            "apple_app_store.sandbox",
            "premium-sub",
            "premium-apple",
            "tiny",
        ),
    )


def actor(
    account_id: str,
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


def notification(
    fixture_id: str,
    *,
    message_id: str,
    locator: str,
    product_id: str,
    provider: BillingProvider,
    environment: BillingEnvironment = BillingEnvironment.SANDBOX,
    event_type: str = "purchase_changed",
    signed_at_ms: int = 1_000,
) -> ValidatedProviderNotification:
    return ValidatedProviderNotification(
        provider,
        environment,
        message_id,
        product_id,
        locator,
        event_type,
        signed_at_ms,
        canonical_sha256(
            {
                "fixture_id": fixture_id,
                "message_id": message_id,
                "provider": provider.value,
                "environment": environment.value,
            }
        ),
    )


def purchase(
    *,
    provider: BillingProvider,
    purchase_id: str,
    product_id: str,
    state: ProviderPurchaseState,
    revision: int,
    effective_at_ms: int,
    verified_at_ms: int,
    expires_at_ms: int | None = None,
    environment: BillingEnvironment = BillingEnvironment.SANDBOX,
    source: str,
) -> ProviderPurchaseSnapshot:
    return ProviderPurchaseSnapshot(
        provider,
        environment,
        purchase_id,
        product_id,
        state,
        effective_at_ms,
        verified_at_ms,
        revision,
        expires_at_ms,
        canonical_sha256({"source": source}),
    )


def ingest(
    service: InMemoryEntitlementService,
    fixture_id: str,
    *,
    account_id: str,
    provider: BillingProvider,
    environment: BillingEnvironment = BillingEnvironment.SANDBOX,
):
    return service.ingest_notification(
        actor(account_id),
        provider=provider,
        environment=environment,
        account_id=account_id,
        envelope={"fixture_id": fixture_id},
    )


def run(source_sha: str) -> dict:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise SystemExit("source SHA must be lowercase 40-character Git SHA")

    clock = Clock(1_000)
    service = InMemoryEntitlementService(
        clock_ms=clock,
        max_catalog_versions=32,
        max_provider_events=128,
        max_purchases=32,
        max_accounts=32,
        max_reconciliations=64,
    )

    google_notifications = {
        "invalid-signature": notification(
            "invalid-signature",
            message_id="google-msg-invalid-signature",
            locator="GOOGLE_BAD_SIGNATURE_TOKEN",
            product_id="premium.monthly",
            provider=BillingProvider.GOOGLE_PLAY,
        ),
        "bad-token": notification(
            "bad-token",
            message_id="google-msg-bad-token",
            locator="GOOGLE_BAD_PURCHASE_TOKEN",
            product_id="premium.monthly",
            provider=BillingProvider.GOOGLE_PLAY,
        ),
        "pending": notification(
            "pending",
            message_id="google-msg-pending",
            locator="GOOGLE_PURCHASE_TOKEN_SECRET",
            product_id="premium.monthly",
            provider=BillingProvider.GOOGLE_PLAY,
            signed_at_ms=900,
        ),
        "active": notification(
            "active",
            message_id="google-msg-active",
            locator="GOOGLE_PURCHASE_TOKEN_SECRET",
            product_id="premium.monthly",
            provider=BillingProvider.GOOGLE_PLAY,
            signed_at_ms=1_000,
        ),
        "old": notification(
            "old",
            message_id="google-msg-old",
            locator="GOOGLE_PURCHASE_TOKEN_SECRET",
            product_id="premium.monthly",
            provider=BillingProvider.GOOGLE_PLAY,
            signed_at_ms=800,
        ),
        "other-account": notification(
            "other-account",
            message_id="google-msg-other-account",
            locator="GOOGLE_PURCHASE_TOKEN_SECRET",
            product_id="premium.monthly",
            provider=BillingProvider.GOOGLE_PLAY,
            signed_at_ms=1_010,
        ),
        "expiry": notification(
            "expiry",
            message_id="google-msg-expiry",
            locator="GOOGLE_EXPIRY_TOKEN_SECRET",
            product_id="premium.monthly",
            provider=BillingProvider.GOOGLE_PLAY,
            signed_at_ms=1_000,
        ),
    }
    google_adapter = FixtureBillingProviderAdapter(
        provider=BillingProvider.GOOGLE_PLAY,
        environment=BillingEnvironment.SANDBOX,
        notifications=google_notifications,
        purchases={
            "GOOGLE_PURCHASE_TOKEN_SECRET": purchase(
                provider=BillingProvider.GOOGLE_PLAY,
                purchase_id="google-purchase-1",
                product_id="premium.monthly",
                state=ProviderPurchaseState.PENDING,
                revision=1,
                effective_at_ms=900,
                verified_at_ms=950,
                expires_at_ms=2_000,
                source="google-pending",
            ),
            "GOOGLE_EXPIRY_TOKEN_SECRET": purchase(
                provider=BillingProvider.GOOGLE_PLAY,
                purchase_id="google-purchase-expiry",
                product_id="premium.monthly",
                state=ProviderPurchaseState.PURCHASED,
                revision=1,
                effective_at_ms=950,
                verified_at_ms=1_000,
                expires_at_ms=1_100,
                source="google-expiry",
            ),
        },
        invalid_notification_ids=("invalid-signature",),
        invalid_purchase_locators=("GOOGLE_BAD_PURCHASE_TOKEN",),
    )
    service.register_adapter(admin(), google_adapter)
    service.register_product_definition(
        admin(),
        CatalogProductDefinition(
            "premium-sub",
            1,
            "premium-access",
            BillingProductKind.SUBSCRIPTION,
            BillingProvider.GOOGLE_PLAY,
            BillingEnvironment.SANDBOX,
            "premium.monthly",
        ),
    )

    immutable_catalog_ok = False
    try:
        service.register_product_definition(
            admin(),
            CatalogProductDefinition(
                "premium-sub",
                1,
                "other-access",
                BillingProductKind.SUBSCRIPTION,
                BillingProvider.GOOGLE_PLAY,
                BillingEnvironment.SANDBOX,
                "premium.monthly",
            ),
        )
    except EntitlementStateError as exc:
        immutable_catalog_ok = str(exc) == "catalog_version_conflict"

    direct_client_receipt_ok = False
    try:
        service.grant_from_client_receipt("acct-a", "GOOGLE_PURCHASE_TOKEN_SECRET")
    except EntitlementAuthorizationError as exc:
        direct_client_receipt_ok = str(exc) == "client_receipt_grant_forbidden"

    invalid_signature_ok = False
    before_invalid = (service.provider_events(), service.purchase_records())
    try:
        ingest(
            service,
            "invalid-signature",
            account_id="acct-a",
            provider=BillingProvider.GOOGLE_PLAY,
        )
    except EntitlementVerificationError as exc:
        invalid_signature_ok = (
            str(exc) == "invalid_notification_signature"
            and before_invalid == (service.provider_events(), service.purchase_records())
        )

    invalid_token_ok = False
    try:
        ingest(
            service,
            "bad-token",
            account_id="acct-a",
            provider=BillingProvider.GOOGLE_PLAY,
        )
    except EntitlementVerificationError as exc:
        invalid_token_ok = (
            str(exc) == "invalid_purchase_token"
            and len(service.provider_events()) == 0
            and len(service.purchase_records()) == 0
        )

    pending = ingest(
        service,
        "pending",
        account_id="acct-a",
        provider=BillingProvider.GOOGLE_PLAY,
    )
    pending_no_grant_ok = (
        pending.entitlement_state is EntitlementAccessState.PENDING
        and pending.grants_access is False
    )

    google_adapter.replace_purchase(
        "GOOGLE_PURCHASE_TOKEN_SECRET",
        purchase(
            provider=BillingProvider.GOOGLE_PLAY,
            purchase_id="google-purchase-1",
            product_id="premium.monthly",
            state=ProviderPurchaseState.PURCHASED,
            revision=2,
            effective_at_ms=1_000,
            verified_at_ms=1_000,
            expires_at_ms=2_000,
            source="google-active",
        ),
    )
    active = ingest(
        service,
        "active",
        account_id="acct-a",
        provider=BillingProvider.GOOGLE_PLAY,
    )
    verified_grant_ok = (
        active.entitlement_state is EntitlementAccessState.ACTIVE
        and active.grants_access is True
    )

    replay_state = service.state_digest()
    fetches_before_replay = google_adapter.purchase_fetch_count
    replay = ingest(
        service,
        "active",
        account_id="acct-a",
        provider=BillingProvider.GOOGLE_PLAY,
    )
    duplicate_message_ok = (
        replay.replayed
        and replay.sequence == active.sequence
        and service.state_digest() == replay_state
        and google_adapter.purchase_fetch_count == fetches_before_replay
    )

    message_account_rebind_ok = False
    try:
        ingest(
            service,
            "active",
            account_id="acct-b",
            provider=BillingProvider.GOOGLE_PLAY,
        )
    except EntitlementStateError as exc:
        message_account_rebind_ok = str(exc) == "message_id_conflict"

    purchase_account_rebind_ok = False
    try:
        ingest(
            service,
            "other-account",
            account_id="acct-b",
            provider=BillingProvider.GOOGLE_PLAY,
        )
    except EntitlementAuthorizationError as exc:
        purchase_account_rebind_ok = str(exc) == "purchase_account_rebind_forbidden"

    google_adapter.replace_purchase(
        "GOOGLE_PURCHASE_TOKEN_SECRET",
        purchase(
            provider=BillingProvider.GOOGLE_PLAY,
            purchase_id="google-purchase-1",
            product_id="premium.monthly",
            state=ProviderPurchaseState.PENDING,
            revision=1,
            effective_at_ms=800,
            verified_at_ms=900,
            expires_at_ms=2_000,
            source="google-old",
        ),
    )
    stale = ingest(
        service,
        "old",
        account_id="acct-a",
        provider=BillingProvider.GOOGLE_PLAY,
    )
    out_of_order_ok = (
        stale.stale
        and stale.grants_access
        and service.purchase_records()[0].provider_revision == 2
    )

    google_adapter.replace_purchase(
        "GOOGLE_PURCHASE_TOKEN_SECRET",
        purchase(
            provider=BillingProvider.GOOGLE_PLAY,
            purchase_id="google-purchase-1",
            product_id="premium.monthly",
            state=ProviderPurchaseState.REVOKED,
            revision=3,
            effective_at_ms=1_050,
            verified_at_ms=1_060,
            expires_at_ms=2_000,
            source="google-revoked",
        ),
    )
    reconcile = service.reconcile_purchase(
        actor("acct-a"),
        provider=BillingProvider.GOOGLE_PLAY,
        environment=BillingEnvironment.SANDBOX,
        account_id="acct-a",
        purchase_locator="GOOGLE_PURCHASE_TOKEN_SECRET",
        reconciliation_id="reconcile-google-1",
    )
    reconciliation_ok = (
        reconcile.reconciled
        and reconcile.entitlement_state is EntitlementAccessState.REVOKED
        and reconcile.grants_access is False
    )
    reconcile_state = service.state_digest()
    reconcile_replay = service.reconcile_purchase(
        actor("acct-a"),
        provider=BillingProvider.GOOGLE_PLAY,
        environment=BillingEnvironment.SANDBOX,
        account_id="acct-a",
        purchase_locator="GOOGLE_PURCHASE_TOKEN_SECRET",
        reconciliation_id="reconcile-google-1",
    )
    reconciliation_replay_ok = (
        reconcile_replay.replayed
        and reconcile_replay.reconciled
        and service.state_digest() == reconcile_state
    )

    expiry = ingest(
        service,
        "expiry",
        account_id="acct-expiry",
        provider=BillingProvider.GOOGLE_PLAY,
    )
    clock.value = 1_100
    expiry_snapshot = service.entitlement(
        actor("acct-expiry"),
        account_id="acct-expiry",
        entitlement_id="premium-access",
    )
    server_clock_expiry_ok = (
        expiry.grants_access
        and expiry_snapshot is not None
        and expiry_snapshot.state is EntitlementAccessState.EXPIRED
        and expiry_snapshot.grants_access is False
    )

    environment_isolation_ok = False
    try:
        service.ingest_notification(
            actor("acct-a"),
            provider=BillingProvider.GOOGLE_PLAY,
            environment=BillingEnvironment.PRODUCTION,
            account_id="acct-a",
            envelope={"fixture_id": "active"},
        )
    except EntitlementStateError as exc:
        environment_isolation_ok = str(exc) == "provider_adapter_not_registered"

    apple_locator = "APPLE_JWS_TRANSACTION_LOCATOR_SECRET"
    apple_message = "4f668af1-0a58-4b9a-a861-4b9c84b21c1f"
    apple_adapter = FixtureBillingProviderAdapter(
        provider=BillingProvider.APPLE_APP_STORE,
        environment=BillingEnvironment.SANDBOX,
        notifications={
            "apple-renew": notification(
                "apple-renew",
                message_id=apple_message,
                locator=apple_locator,
                product_id="com.kodepoia.premium",
                provider=BillingProvider.APPLE_APP_STORE,
                event_type="DID_RENEW",
                signed_at_ms=1_090,
            )
        },
        purchases={
            apple_locator: purchase(
                provider=BillingProvider.APPLE_APP_STORE,
                purchase_id="200000000000001",
                product_id="com.kodepoia.premium",
                state=ProviderPurchaseState.PURCHASED,
                revision=1,
                effective_at_ms=1_080,
                verified_at_ms=1_090,
                source="apple-purchased",
            )
        },
    )
    service.register_adapter(admin(), apple_adapter)
    service.register_product_definition(
        admin(),
        CatalogProductDefinition(
            "premium-apple",
            1,
            "apple-premium-access",
            BillingProductKind.DURABLE,
            BillingProvider.APPLE_APP_STORE,
            BillingEnvironment.SANDBOX,
            "com.kodepoia.premium",
        ),
    )
    apple = ingest(
        service,
        "apple-renew",
        account_id="acct-apple",
        provider=BillingProvider.APPLE_APP_STORE,
    )
    apple_v2_contract_ok = (
        apple.grants_access
        and any(event.message_id == apple_message for event in service.provider_events())
    )

    object_authorization_ok = False
    wrong_object = actor(
        "acct-object",
        "billing.notification.ingest",
        "billing.entitlement.mutate",
        objects=("someone-else",),
    )
    try:
        service.ingest_notification(
            wrong_object,
            provider=BillingProvider.GOOGLE_PLAY,
            environment=BillingEnvironment.SANDBOX,
            account_id="acct-object",
            envelope={"fixture_id": "active"},
        )
    except EntitlementAuthorizationError as exc:
        object_authorization_ok = str(exc) == "forbidden"

    function_authorization_ok = False
    try:
        service.ingest_notification(
            actor("acct-function", "billing.entitlement.read"),
            provider=BillingProvider.GOOGLE_PLAY,
            environment=BillingEnvironment.SANDBOX,
            account_id="acct-function",
            envelope={"fixture_id": "active"},
        )
    except EntitlementAuthorizationError as exc:
        function_authorization_ok = str(exc) == "forbidden"

    tiny_clock = Clock(1_000)
    tiny = InMemoryEntitlementService(
        clock_ms=tiny_clock,
        max_catalog_versions=2,
        max_provider_events=1,
        max_purchases=2,
        max_accounts=2,
        max_reconciliations=2,
    )
    tiny_adapter = FixtureBillingProviderAdapter(
        provider=BillingProvider.GOOGLE_PLAY,
        environment=BillingEnvironment.SANDBOX,
        notifications={
            "one": notification(
                "one",
                message_id="tiny-msg-1",
                locator="TINY_TOKEN",
                product_id="tiny.sku",
                provider=BillingProvider.GOOGLE_PLAY,
            ),
            "two": notification(
                "two",
                message_id="tiny-msg-2",
                locator="TINY_TOKEN",
                product_id="tiny.sku",
                provider=BillingProvider.GOOGLE_PLAY,
            ),
        },
        purchases={
            "TINY_TOKEN": purchase(
                provider=BillingProvider.GOOGLE_PLAY,
                purchase_id="tiny-purchase",
                product_id="tiny.sku",
                state=ProviderPurchaseState.PURCHASED,
                revision=1,
                effective_at_ms=900,
                verified_at_ms=950,
                source="tiny",
            )
        },
    )
    tiny.register_adapter(admin(), tiny_adapter)
    tiny.register_product_definition(
        admin(),
        CatalogProductDefinition(
            "tiny",
            1,
            "tiny-access",
            BillingProductKind.DURABLE,
            BillingProvider.GOOGLE_PLAY,
            BillingEnvironment.SANDBOX,
            "tiny.sku",
        ),
    )
    ingest(
        tiny,
        "one",
        account_id="tiny-acct",
        provider=BillingProvider.GOOGLE_PLAY,
    )
    bounded_capacity_ok = False
    try:
        ingest(
            tiny,
            "two",
            account_id="tiny-acct",
            provider=BillingProvider.GOOGLE_PLAY,
        )
    except EntitlementCapacityError as exc:
        bounded_capacity_ok = str(exc) == "provider_event_capacity"

    redacted_blob = json.dumps(
        {
            "state": service.canonical_state(),
            "trace": service.trace(),
            "evidence": service.redacted_evidence(),
        },
        sort_keys=True,
    )
    evidence_flags = service.redacted_evidence()
    redaction_ok = all(
        secret not in redacted_blob
        for secret in (
            "GOOGLE_PURCHASE_TOKEN_SECRET",
            "GOOGLE_EXPIRY_TOKEN_SECRET",
            "GOOGLE_BAD_PURCHASE_TOKEN",
            apple_locator,
        )
    ) and evidence_flags["provider_live_claim"] is False and evidence_flags["secrets_exposed"] is False

    checks = {
        "client_receipt_grant_rejected": direct_client_receipt_ok,
        "invalid_notification_signature_rejected": invalid_signature_ok,
        "invalid_purchase_token_rejected": invalid_token_ok,
        "pending_purchase_no_grant": pending_no_grant_ok,
        "verified_provider_state_grants": verified_grant_ok,
        "duplicate_message_mutation_free": duplicate_message_ok,
        "message_account_rebind_rejected": message_account_rebind_ok,
        "purchase_account_rebind_rejected": purchase_account_rebind_ok,
        "out_of_order_no_regression": out_of_order_ok,
        "reconciliation_converges": reconciliation_ok,
        "reconciliation_replay_idempotent": reconciliation_replay_ok,
        "server_clock_expiry": server_clock_expiry_ok,
        "environment_isolation": environment_isolation_ok,
        "apple_v2_contract": apple_v2_contract_ok,
        "immutable_catalog_version": immutable_catalog_ok,
        "object_authorization": object_authorization_ok,
        "function_authorization": function_authorization_ok,
        "bounded_capacity": bounded_capacity_ok,
        "redacted_evidence": redaction_ok,
    }
    if not all(checks.values()):
        raise SystemExit(
            f"R14.10 acceptance checks failed: {[name for name, ok in checks.items() if not ok]}"
        )

    final_google = service.entitlement(
        actor("acct-a"),
        account_id="acct-a",
        entitlement_id="premium-access",
    )
    final_apple = service.entitlement(
        actor("acct-apple"),
        account_id="acct-apple",
        entitlement_id="apple-premium-access",
    )
    assert final_google is not None and final_apple is not None

    return {
        "status": "pass",
        "source_sha": source_sha,
        "checks": checks,
        "catalog_digest": canonical_sha256(
            [definition.canonical() for definition in service.catalog_definitions()]
        ),
        "state_digest": service.state_digest(),
        "trace_digest": service.trace_digest(),
        "provider_event_digest": canonical_sha256(
            [event.canonical() for event in service.provider_events()]
        ),
        "google_entitlement_digest": final_google.digest(),
        "apple_entitlement_digest": final_apple.digest(),
        "provider_event_count": len(service.provider_events()),
        "purchase_count": len(service.purchase_records()),
        "catalog_count": len(service.catalog_definitions()),
        "budgets": {
            "max_catalog_versions": service.max_catalog_versions,
            "max_provider_events": service.max_provider_events,
            "max_purchases": service.max_purchases,
            "max_accounts": service.max_accounts,
            "max_reconciliations": service.max_reconciliations,
        },
        "external_reference_posture": [
            "Google RTDN is change notification only; complete purchase status is re-queried through Google Play Developer API",
            "Google RTDN messageId is a provider-message deduplication key and purchase verification remains backend-authoritative",
            "Apple App Store Server Notifications V2 signedPayload is JWS and notificationUUID is used for duplicate suppression",
            "Apple signedDate provides notification snapshot ordering; provider-live production proof is outside core acceptance",
        ],
        "manual_state": "conditional_not_triggered",
        "provider_live_claim": False,
        "secrets_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = run(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
