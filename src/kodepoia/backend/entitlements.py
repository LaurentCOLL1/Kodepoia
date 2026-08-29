from __future__ import annotations

import re
import threading
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Callable, Mapping, Protocol

from .authority import AuthorityActorContext
from .contracts import canonical_json_bytes, canonical_sha256

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,191}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EntitlementPolicyError(ValueError):
    pass


class EntitlementStateError(RuntimeError):
    pass


class EntitlementAuthorizationError(PermissionError):
    pass


class EntitlementCapacityError(EntitlementStateError):
    pass


class EntitlementVerificationError(EntitlementStateError):
    pass


class BillingProvider(StrEnum):
    GOOGLE_PLAY = "google_play"
    APPLE_APP_STORE = "apple_app_store"


class BillingEnvironment(StrEnum):
    TEST = "test"
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class BillingProductKind(StrEnum):
    DURABLE = "durable"
    CONSUMABLE = "consumable"
    SUBSCRIPTION = "subscription"


class ProviderPurchaseState(StrEnum):
    PENDING = "pending"
    PURCHASED = "purchased"
    GRACE = "grace"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REFUNDED = "refunded"
    REVOKED = "revoked"


class EntitlementAccessState(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    GRACE = "grace"
    EXPIRED = "expired"
    REVOKED = "revoked"


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise EntitlementPolicyError(f"invalid_{field}")
    return value


def _positive_version(value: int, *, field: str = "version") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value > 2**31 - 1:
        raise EntitlementPolicyError(f"invalid_{field}")
    return value


def _timestamp(value: int, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**63 - 1:
        raise EntitlementPolicyError(f"invalid_{field}")
    return value


def _server_now_ms(clock_ms: Callable[[], int]) -> int:
    return _timestamp(clock_ms(), field="server_clock")


def _nonempty_secret_locator(value: str) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 4096:
        raise EntitlementPolicyError("invalid_purchase_locator")
    return value


def _sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise EntitlementPolicyError(f"invalid_{field}")
    return value


@dataclass(frozen=True, slots=True)
class CatalogProductDefinition:
    product_id: str
    version: int
    entitlement_id: str
    kind: BillingProductKind
    provider: BillingProvider
    environment: BillingEnvironment
    provider_product_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "product_id", _stable_id(self.product_id, field="product_id"))
        object.__setattr__(self, "entitlement_id", _stable_id(self.entitlement_id, field="entitlement_id"))
        object.__setattr__(
            self,
            "provider_product_id",
            _stable_id(self.provider_product_id, field="provider_product_id"),
        )
        _positive_version(self.version)
        if not isinstance(self.kind, BillingProductKind):
            raise EntitlementPolicyError("invalid_product_kind")
        if not isinstance(self.provider, BillingProvider):
            raise EntitlementPolicyError("invalid_provider")
        if not isinstance(self.environment, BillingEnvironment):
            raise EntitlementPolicyError("invalid_environment")

    def canonical(self) -> dict[str, object]:
        return {
            "product_id": self.product_id,
            "version": self.version,
            "entitlement_id": self.entitlement_id,
            "kind": self.kind.value,
            "provider": self.provider.value,
            "environment": self.environment.value,
            "provider_product_id": self.provider_product_id,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ValidatedProviderNotification:
    provider: BillingProvider
    environment: BillingEnvironment
    message_id: str
    provider_product_id: str
    purchase_locator: str
    event_type: str
    signed_at_ms: int
    payload_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.provider, BillingProvider):
            raise EntitlementPolicyError("invalid_provider")
        if not isinstance(self.environment, BillingEnvironment):
            raise EntitlementPolicyError("invalid_environment")
        object.__setattr__(self, "message_id", _stable_id(self.message_id, field="message_id"))
        object.__setattr__(
            self,
            "provider_product_id",
            _stable_id(self.provider_product_id, field="provider_product_id"),
        )
        object.__setattr__(self, "event_type", _stable_id(self.event_type, field="event_type"))
        object.__setattr__(self, "purchase_locator", _nonempty_secret_locator(self.purchase_locator))
        _timestamp(self.signed_at_ms, field="signed_at_ms")
        object.__setattr__(self, "payload_digest", _sha256(self.payload_digest, field="payload_digest"))

    @property
    def purchase_locator_digest(self) -> str:
        return canonical_sha256({"purchase_locator": self.purchase_locator})

    def canonical_redacted(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "environment": self.environment.value,
            "message_id": self.message_id,
            "provider_product_id": self.provider_product_id,
            "purchase_locator_digest": self.purchase_locator_digest,
            "event_type": self.event_type,
            "signed_at_ms": self.signed_at_ms,
            "payload_digest": self.payload_digest,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical_redacted())


@dataclass(frozen=True, slots=True)
class ProviderPurchaseSnapshot:
    provider: BillingProvider
    environment: BillingEnvironment
    purchase_id: str
    provider_product_id: str
    state: ProviderPurchaseState
    effective_at_ms: int
    verified_at_ms: int
    provider_revision: int
    expires_at_ms: int | None = None
    source_digest: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider, BillingProvider):
            raise EntitlementPolicyError("invalid_provider")
        if not isinstance(self.environment, BillingEnvironment):
            raise EntitlementPolicyError("invalid_environment")
        object.__setattr__(self, "purchase_id", _stable_id(self.purchase_id, field="purchase_id"))
        object.__setattr__(
            self,
            "provider_product_id",
            _stable_id(self.provider_product_id, field="provider_product_id"),
        )
        if not isinstance(self.state, ProviderPurchaseState):
            raise EntitlementPolicyError("invalid_purchase_state")
        _timestamp(self.effective_at_ms, field="effective_at_ms")
        _timestamp(self.verified_at_ms, field="verified_at_ms")
        _positive_version(self.provider_revision, field="provider_revision")
        if self.expires_at_ms is not None:
            _timestamp(self.expires_at_ms, field="expires_at_ms")
        if self.source_digest is not None:
            object.__setattr__(self, "source_digest", _sha256(self.source_digest, field="source_digest"))

    def canonical(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "environment": self.environment.value,
            "purchase_id": self.purchase_id,
            "provider_product_id": self.provider_product_id,
            "state": self.state.value,
            "effective_at_ms": self.effective_at_ms,
            "verified_at_ms": self.verified_at_ms,
            "provider_revision": self.provider_revision,
            "expires_at_ms": self.expires_at_ms,
            "source_digest": self.source_digest,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class BillingProviderAdapter(Protocol):
    provider: BillingProvider
    environment: BillingEnvironment

    def validate_notification(self, envelope: Mapping[str, Any]) -> ValidatedProviderNotification:
        ...

    def fetch_purchase(self, purchase_locator: str) -> ProviderPurchaseSnapshot:
        ...


class FixtureBillingProviderAdapter:
    """Deterministic, network-free provider contract used for core/sandbox acceptance."""

    def __init__(
        self,
        *,
        provider: BillingProvider,
        environment: BillingEnvironment,
        notifications: Mapping[str, ValidatedProviderNotification],
        purchases: Mapping[str, ProviderPurchaseSnapshot],
        invalid_notification_ids: tuple[str, ...] = (),
        invalid_purchase_locators: tuple[str, ...] = (),
    ) -> None:
        if not isinstance(provider, BillingProvider):
            raise EntitlementPolicyError("invalid_provider")
        if not isinstance(environment, BillingEnvironment):
            raise EntitlementPolicyError("invalid_environment")
        self.provider = provider
        self.environment = environment
        self._notifications = dict(notifications)
        self._purchases = dict(purchases)
        self._invalid_notification_ids = frozenset(invalid_notification_ids)
        self._invalid_purchase_locators = frozenset(invalid_purchase_locators)
        self.notification_validation_count = 0
        self.purchase_fetch_count = 0
        for fixture_id, notification in self._notifications.items():
            _stable_id(fixture_id, field="fixture_id")
            if notification.provider is not provider or notification.environment is not environment:
                raise EntitlementPolicyError("fixture_notification_environment_mismatch")
        for locator, snapshot in self._purchases.items():
            _nonempty_secret_locator(locator)
            if snapshot.provider is not provider or snapshot.environment is not environment:
                raise EntitlementPolicyError("fixture_purchase_environment_mismatch")

    def validate_notification(self, envelope: Mapping[str, Any]) -> ValidatedProviderNotification:
        self.notification_validation_count += 1
        if not isinstance(envelope, Mapping) or set(envelope) != {"fixture_id"}:
            raise EntitlementVerificationError("invalid_notification_envelope")
        fixture_id = _stable_id(envelope["fixture_id"], field="fixture_id")  # type: ignore[arg-type]
        if fixture_id in self._invalid_notification_ids:
            raise EntitlementVerificationError("invalid_notification_signature")
        try:
            return self._notifications[fixture_id]
        except KeyError as exc:
            raise EntitlementVerificationError("unknown_notification") from exc

    def fetch_purchase(self, purchase_locator: str) -> ProviderPurchaseSnapshot:
        self.purchase_fetch_count += 1
        locator = _nonempty_secret_locator(purchase_locator)
        if locator in self._invalid_purchase_locators:
            raise EntitlementVerificationError("invalid_purchase_token")
        try:
            return self._purchases[locator]
        except KeyError as exc:
            raise EntitlementVerificationError("purchase_not_found") from exc

    def replace_purchase(self, purchase_locator: str, snapshot: ProviderPurchaseSnapshot) -> None:
        locator = _nonempty_secret_locator(purchase_locator)
        if snapshot.provider is not self.provider or snapshot.environment is not self.environment:
            raise EntitlementPolicyError("fixture_purchase_environment_mismatch")
        self._purchases[locator] = snapshot


@dataclass(frozen=True, slots=True)
class ProviderEventRecord:
    provider: BillingProvider
    environment: BillingEnvironment
    message_id: str
    account_id: str
    purchase_id: str
    product_id: str
    entitlement_id: str
    event_type: str
    signed_at_ms: int
    processed_at_ms: int
    payload_digest: str
    purchase_locator_digest: str
    purchase_snapshot_digest: str
    sequence: int
    stale: bool

    def canonical(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "environment": self.environment.value,
            "message_id": self.message_id,
            "account_id": self.account_id,
            "purchase_id": self.purchase_id,
            "product_id": self.product_id,
            "entitlement_id": self.entitlement_id,
            "event_type": self.event_type,
            "signed_at_ms": self.signed_at_ms,
            "processed_at_ms": self.processed_at_ms,
            "payload_digest": self.payload_digest,
            "purchase_locator_digest": self.purchase_locator_digest,
            "purchase_snapshot_digest": self.purchase_snapshot_digest,
            "sequence": self.sequence,
            "stale": self.stale,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class PurchaseRecord:
    account_id: str
    provider: BillingProvider
    environment: BillingEnvironment
    purchase_id: str
    product_id: str
    product_version: int
    entitlement_id: str
    kind: BillingProductKind
    provider_product_id: str
    purchase_locator_digest: str
    state: ProviderPurchaseState
    effective_at_ms: int
    verified_at_ms: int
    provider_revision: int
    expires_at_ms: int | None
    source_digest: str | None
    updated_sequence: int

    def canonical(self) -> dict[str, object]:
        return {
            "account_id": self.account_id,
            "provider": self.provider.value,
            "environment": self.environment.value,
            "purchase_id": self.purchase_id,
            "product_id": self.product_id,
            "product_version": self.product_version,
            "entitlement_id": self.entitlement_id,
            "kind": self.kind.value,
            "provider_product_id": self.provider_product_id,
            "purchase_locator_digest": self.purchase_locator_digest,
            "state": self.state.value,
            "effective_at_ms": self.effective_at_ms,
            "verified_at_ms": self.verified_at_ms,
            "provider_revision": self.provider_revision,
            "expires_at_ms": self.expires_at_ms,
            "source_digest": self.source_digest,
            "updated_sequence": self.updated_sequence,
        }


@dataclass(frozen=True, slots=True)
class EntitlementSnapshot:
    account_id: str
    entitlement_id: str
    state: EntitlementAccessState
    grants_access: bool
    source_purchase_id: str
    product_id: str
    provider: BillingProvider
    environment: BillingEnvironment
    effective_at_ms: int
    expires_at_ms: int | None

    def canonical(self) -> dict[str, object]:
        return {
            "account_id": self.account_id,
            "entitlement_id": self.entitlement_id,
            "state": self.state.value,
            "grants_access": self.grants_access,
            "source_purchase_id": self.source_purchase_id,
            "product_id": self.product_id,
            "provider": self.provider.value,
            "environment": self.environment.value,
            "effective_at_ms": self.effective_at_ms,
            "expires_at_ms": self.expires_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class EntitlementMutationResult:
    operation_id: str
    account_id: str
    purchase_id: str
    entitlement_id: str
    entitlement_state: EntitlementAccessState
    grants_access: bool
    sequence: int
    replayed: bool = False
    stale: bool = False
    reconciled: bool = False

    def canonical(self) -> dict[str, object]:
        return {
            "operation_id": self.operation_id,
            "account_id": self.account_id,
            "purchase_id": self.purchase_id,
            "entitlement_id": self.entitlement_id,
            "entitlement_state": self.entitlement_state.value,
            "grants_access": self.grants_access,
            "sequence": self.sequence,
            "replayed": self.replayed,
            "stale": self.stale,
            "reconciled": self.reconciled,
        }


@dataclass(frozen=True, slots=True)
class _ReplayRecord:
    request_digest: str
    result: EntitlementMutationResult


def _access_state(record: PurchaseRecord, now_ms: int) -> EntitlementAccessState:
    expired_by_clock = record.expires_at_ms is not None and now_ms >= record.expires_at_ms
    if record.state in (ProviderPurchaseState.REFUNDED, ProviderPurchaseState.REVOKED):
        return EntitlementAccessState.REVOKED
    if record.state is ProviderPurchaseState.EXPIRED or expired_by_clock:
        return EntitlementAccessState.EXPIRED
    if record.state is ProviderPurchaseState.PENDING:
        return EntitlementAccessState.PENDING
    if record.state is ProviderPurchaseState.GRACE:
        return EntitlementAccessState.GRACE
    if record.state is ProviderPurchaseState.CANCELED:
        return (
            EntitlementAccessState.ACTIVE
            if record.expires_at_ms is not None and now_ms < record.expires_at_ms
            else EntitlementAccessState.EXPIRED
        )
    if record.state is ProviderPurchaseState.PURCHASED:
        return EntitlementAccessState.ACTIVE
    raise EntitlementStateError("unsupported_purchase_state")


_ACCESS_PRIORITY = {
    EntitlementAccessState.REVOKED: 1,
    EntitlementAccessState.EXPIRED: 2,
    EntitlementAccessState.PENDING: 3,
    EntitlementAccessState.GRACE: 4,
    EntitlementAccessState.ACTIVE: 5,
}


class InMemoryEntitlementService:
    def __init__(
        self,
        *,
        clock_ms: Callable[[], int],
        max_catalog_versions: int = 4_096,
        max_provider_events: int = 100_000,
        max_purchases: int = 100_000,
        max_accounts: int = 100_000,
        max_reconciliations: int = 100_000,
    ) -> None:
        for name, value in (
            ("max_catalog_versions", max_catalog_versions),
            ("max_provider_events", max_provider_events),
            ("max_purchases", max_purchases),
            ("max_accounts", max_accounts),
            ("max_reconciliations", max_reconciliations),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise EntitlementPolicyError(f"{name}_must_be_positive")
        self.clock_ms = clock_ms
        self.max_catalog_versions = max_catalog_versions
        self.max_provider_events = max_provider_events
        self.max_purchases = max_purchases
        self.max_accounts = max_accounts
        self.max_reconciliations = max_reconciliations
        self._lock = threading.RLock()
        self._catalog: dict[tuple[str, int], CatalogProductDefinition] = {}
        self._active_catalog: dict[str, int] = {}
        self._adapters: dict[tuple[BillingProvider, BillingEnvironment], BillingProviderAdapter] = {}
        self._provider_events: dict[tuple[BillingProvider, BillingEnvironment, str], ProviderEventRecord] = {}
        self._event_replays: dict[tuple[BillingProvider, BillingEnvironment, str], _ReplayRecord] = {}
        self._reconciliation_replays: dict[
            tuple[BillingProvider, BillingEnvironment, str], _ReplayRecord
        ] = {}
        self._purchases: dict[tuple[BillingProvider, BillingEnvironment, str], PurchaseRecord] = {}
        self._purchase_accounts: dict[tuple[BillingProvider, BillingEnvironment, str], str] = {}
        self._accounts: set[str] = set()
        self._sequence = 0
        self._trace: list[dict[str, object]] = []

    @staticmethod
    def _authorize(actor: AuthorityActorContext, permission: str, target_id: str) -> None:
        if not actor.can(permission, target_id):
            raise EntitlementAuthorizationError("forbidden")

    def register_adapter(self, actor: AuthorityActorContext, adapter: BillingProviderAdapter) -> None:
        target_id = f"{adapter.provider.value}.{adapter.environment.value}"
        self._authorize(actor, "billing.configure", target_id)
        key = (adapter.provider, adapter.environment)
        with self._lock:
            existing = self._adapters.get(key)
            if existing is not None and existing is not adapter:
                raise EntitlementStateError("adapter_already_registered")
            self._adapters[key] = adapter
            self._trace.append(
                {
                    "event": "provider_adapter_registered",
                    "provider": adapter.provider.value,
                    "environment": adapter.environment.value,
                }
            )

    def register_product_definition(
        self,
        actor: AuthorityActorContext,
        definition: CatalogProductDefinition,
    ) -> CatalogProductDefinition:
        self._authorize(actor, "billing.catalog.define", definition.product_id)
        key = (definition.product_id, definition.version)
        with self._lock:
            if key not in self._catalog and len(self._catalog) >= self.max_catalog_versions:
                raise EntitlementCapacityError("catalog_capacity")
            existing = self._catalog.get(key)
            if existing is not None:
                if existing != definition:
                    raise EntitlementStateError("catalog_version_conflict")
                return existing
            self._ensure_mapping_available(definition, excluding_product_id=definition.product_id)
            self._catalog[key] = definition
            self._active_catalog.setdefault(definition.product_id, definition.version)
            self._trace.append({"event": "catalog_definition_registered", **definition.canonical()})
            return definition

    def _ensure_mapping_available(
        self,
        definition: CatalogProductDefinition,
        *,
        excluding_product_id: str,
    ) -> None:
        for product_id, version in self._active_catalog.items():
            if product_id == excluding_product_id:
                continue
            current = self._catalog[(product_id, version)]
            if (
                current.provider is definition.provider
                and current.environment is definition.environment
                and current.provider_product_id == definition.provider_product_id
            ):
                raise EntitlementStateError("provider_product_mapping_conflict")

    def activate_product_definition(
        self,
        actor: AuthorityActorContext,
        product_id: str,
        version: int,
    ) -> CatalogProductDefinition:
        product_id = _stable_id(product_id, field="product_id")
        _positive_version(version)
        self._authorize(actor, "billing.catalog.activate", product_id)
        key = (product_id, version)
        with self._lock:
            try:
                definition = self._catalog[key]
            except KeyError as exc:
                raise EntitlementStateError("catalog_definition_not_found") from exc
            self._ensure_mapping_available(definition, excluding_product_id=product_id)
            self._active_catalog[product_id] = version
            self._trace.append(
                {
                    "event": "catalog_definition_activated",
                    "product_id": product_id,
                    "version": version,
                }
            )
            return definition

    def _active_product_for_provider(
        self,
        provider: BillingProvider,
        environment: BillingEnvironment,
        provider_product_id: str,
    ) -> CatalogProductDefinition:
        with self._lock:
            matches: list[CatalogProductDefinition] = []
            for product_id, version in self._active_catalog.items():
                definition = self._catalog[(product_id, version)]
                if (
                    definition.provider is provider
                    and definition.environment is environment
                    and definition.provider_product_id == provider_product_id
                ):
                    matches.append(definition)
            if len(matches) != 1:
                if not matches:
                    raise EntitlementStateError("provider_product_not_mapped")
                raise EntitlementStateError("provider_product_mapping_ambiguous")
            return matches[0]

    def grant_from_client_receipt(self, *_args: object, **_kwargs: object) -> None:
        raise EntitlementAuthorizationError("client_receipt_grant_forbidden")

    def _adapter(
        self,
        provider: BillingProvider,
        environment: BillingEnvironment,
    ) -> BillingProviderAdapter:
        try:
            return self._adapters[(provider, environment)]
        except KeyError as exc:
            raise EntitlementStateError("provider_adapter_not_registered") from exc

    @staticmethod
    def _validate_snapshot_binding(
        notification: ValidatedProviderNotification,
        snapshot: ProviderPurchaseSnapshot,
    ) -> None:
        if snapshot.provider is not notification.provider:
            raise EntitlementVerificationError("provider_mismatch")
        if snapshot.environment is not notification.environment:
            raise EntitlementVerificationError("environment_mismatch")
        if snapshot.provider_product_id != notification.provider_product_id:
            raise EntitlementVerificationError("provider_product_mismatch")

    def ingest_notification(
        self,
        actor: AuthorityActorContext,
        *,
        provider: BillingProvider,
        environment: BillingEnvironment,
        account_id: str,
        envelope: Mapping[str, Any],
    ) -> EntitlementMutationResult:
        if not isinstance(provider, BillingProvider):
            raise EntitlementPolicyError("invalid_provider")
        if not isinstance(environment, BillingEnvironment):
            raise EntitlementPolicyError("invalid_environment")
        account_id = _stable_id(account_id, field="account_id")
        self._authorize(actor, "billing.notification.ingest", account_id)
        adapter = self._adapter(provider, environment)
        notification = adapter.validate_notification(envelope)
        if notification.provider is not provider or notification.environment is not environment:
            raise EntitlementVerificationError("notification_adapter_mismatch")
        notification_digest = canonical_sha256(
            {
                "notification": notification.canonical_redacted(),
                "account_id": account_id,
            }
        )
        event_key = (provider, environment, notification.message_id)
        with self._lock:
            replay = self._event_replays.get(event_key)
            if replay is not None:
                if replay.request_digest != notification_digest:
                    raise EntitlementStateError("message_id_conflict")
                return replace(replay.result, replayed=True)
        snapshot = adapter.fetch_purchase(notification.purchase_locator)
        self._validate_snapshot_binding(notification, snapshot)
        definition = self._active_product_for_provider(
            provider,
            environment,
            snapshot.provider_product_id,
        )
        return self._commit_verified(
            actor=actor,
            account_id=account_id,
            definition=definition,
            snapshot=snapshot,
            purchase_locator_digest=notification.purchase_locator_digest,
            operation_id=notification.message_id,
            request_digest=notification_digest,
            notification=notification,
            reconciled=False,
        )

    def reconcile_purchase(
        self,
        actor: AuthorityActorContext,
        *,
        provider: BillingProvider,
        environment: BillingEnvironment,
        account_id: str,
        purchase_locator: str,
        reconciliation_id: str,
    ) -> EntitlementMutationResult:
        if not isinstance(provider, BillingProvider):
            raise EntitlementPolicyError("invalid_provider")
        if not isinstance(environment, BillingEnvironment):
            raise EntitlementPolicyError("invalid_environment")
        account_id = _stable_id(account_id, field="account_id")
        reconciliation_id = _stable_id(reconciliation_id, field="reconciliation_id")
        purchase_locator = _nonempty_secret_locator(purchase_locator)
        self._authorize(actor, "billing.reconcile", account_id)
        locator_digest = canonical_sha256({"purchase_locator": purchase_locator})
        request_digest = canonical_sha256(
            {
                "provider": provider.value,
                "environment": environment.value,
                "account_id": account_id,
                "purchase_locator_digest": locator_digest,
                "reconciliation_id": reconciliation_id,
            }
        )
        replay_key = (provider, environment, reconciliation_id)
        with self._lock:
            replay = self._reconciliation_replays.get(replay_key)
            if replay is not None:
                if replay.request_digest != request_digest:
                    raise EntitlementStateError("reconciliation_id_conflict")
                return replace(replay.result, replayed=True, reconciled=True)
            if len(self._reconciliation_replays) >= self.max_reconciliations:
                raise EntitlementCapacityError("reconciliation_capacity")
        adapter = self._adapter(provider, environment)
        snapshot = adapter.fetch_purchase(purchase_locator)
        if snapshot.provider is not provider or snapshot.environment is not environment:
            raise EntitlementVerificationError("environment_mismatch")
        definition = self._active_product_for_provider(
            provider,
            environment,
            snapshot.provider_product_id,
        )
        result = self._commit_verified(
            actor=actor,
            account_id=account_id,
            definition=definition,
            snapshot=snapshot,
            purchase_locator_digest=locator_digest,
            operation_id=reconciliation_id,
            request_digest=request_digest,
            notification=None,
            reconciled=True,
        )
        with self._lock:
            self._reconciliation_replays[replay_key] = _ReplayRecord(
                request_digest,
                result,
            )
        return result

    def _commit_verified(
        self,
        *,
        actor: AuthorityActorContext,
        account_id: str,
        definition: CatalogProductDefinition,
        snapshot: ProviderPurchaseSnapshot,
        purchase_locator_digest: str,
        operation_id: str,
        request_digest: str,
        notification: ValidatedProviderNotification | None,
        reconciled: bool,
    ) -> EntitlementMutationResult:
        self._authorize(actor, "billing.entitlement.mutate", account_id)
        if (
            definition.kind is BillingProductKind.SUBSCRIPTION
            and snapshot.state
            in (
                ProviderPurchaseState.PURCHASED,
                ProviderPurchaseState.GRACE,
                ProviderPurchaseState.CANCELED,
            )
            and snapshot.expires_at_ms is None
        ):
            raise EntitlementVerificationError("subscription_expiry_required")
        now_ms = _server_now_ms(self.clock_ms)
        purchase_key = (snapshot.provider, snapshot.environment, snapshot.purchase_id)
        event_key = (
            (snapshot.provider, snapshot.environment, notification.message_id)
            if notification is not None
            else None
        )
        with self._lock:
            if notification is not None:
                existing_replay = self._event_replays.get(event_key)  # type: ignore[arg-type]
                if existing_replay is not None:
                    if existing_replay.request_digest != request_digest:
                        raise EntitlementStateError("message_id_conflict")
                    return replace(existing_replay.result, replayed=True)
                if len(self._provider_events) >= self.max_provider_events:
                    raise EntitlementCapacityError("provider_event_capacity")
            bound_account = self._purchase_accounts.get(purchase_key)
            if bound_account is not None and bound_account != account_id:
                raise EntitlementAuthorizationError("purchase_account_rebind_forbidden")
            existing = self._purchases.get(purchase_key)
            stale = False
            if existing is not None:
                if snapshot.provider_revision < existing.provider_revision:
                    stale = True
                elif snapshot.provider_revision == existing.provider_revision:
                    current_digest = canonical_sha256(
                        {
                            "state": existing.state.value,
                            "effective_at_ms": existing.effective_at_ms,
                            "expires_at_ms": existing.expires_at_ms,
                            "source_digest": existing.source_digest,
                        }
                    )
                    incoming_digest = canonical_sha256(
                        {
                            "state": snapshot.state.value,
                            "effective_at_ms": snapshot.effective_at_ms,
                            "expires_at_ms": snapshot.expires_at_ms,
                            "source_digest": snapshot.source_digest,
                        }
                    )
                    if current_digest != incoming_digest:
                        raise EntitlementStateError("provider_revision_conflict")
                    stale = True
                elif snapshot.effective_at_ms < existing.effective_at_ms:
                    stale = True
            if existing is None:
                if len(self._purchases) >= self.max_purchases:
                    raise EntitlementCapacityError("purchase_capacity")
                if account_id not in self._accounts and len(self._accounts) >= self.max_accounts:
                    raise EntitlementCapacityError("account_capacity")

            if stale:
                assert existing is not None
                candidate = existing
                sequence = existing.updated_sequence
            else:
                self._sequence += 1
                sequence = self._sequence
                candidate = PurchaseRecord(
                    account_id=account_id,
                    provider=snapshot.provider,
                    environment=snapshot.environment,
                    purchase_id=snapshot.purchase_id,
                    product_id=definition.product_id,
                    product_version=definition.version,
                    entitlement_id=definition.entitlement_id,
                    kind=definition.kind,
                    provider_product_id=definition.provider_product_id,
                    purchase_locator_digest=purchase_locator_digest,
                    state=snapshot.state,
                    effective_at_ms=snapshot.effective_at_ms,
                    verified_at_ms=snapshot.verified_at_ms,
                    provider_revision=snapshot.provider_revision,
                    expires_at_ms=snapshot.expires_at_ms,
                    source_digest=snapshot.source_digest,
                    updated_sequence=sequence,
                )
                self._purchases[purchase_key] = candidate
                self._purchase_accounts[purchase_key] = account_id
                self._accounts.add(account_id)

            entitlement = self._entitlement_for(account_id, definition.entitlement_id, now_ms=now_ms)
            if entitlement is None:
                raise EntitlementStateError("entitlement_projection_missing")
            result = EntitlementMutationResult(
                operation_id=operation_id,
                account_id=account_id,
                purchase_id=snapshot.purchase_id,
                entitlement_id=definition.entitlement_id,
                entitlement_state=entitlement.state,
                grants_access=entitlement.grants_access,
                sequence=sequence,
                stale=stale,
                reconciled=reconciled,
            )

            if notification is not None:
                record = ProviderEventRecord(
                    provider=snapshot.provider,
                    environment=snapshot.environment,
                    message_id=notification.message_id,
                    account_id=account_id,
                    purchase_id=snapshot.purchase_id,
                    product_id=definition.product_id,
                    entitlement_id=definition.entitlement_id,
                    event_type=notification.event_type,
                    signed_at_ms=notification.signed_at_ms,
                    processed_at_ms=now_ms,
                    payload_digest=notification.payload_digest,
                    purchase_locator_digest=purchase_locator_digest,
                    purchase_snapshot_digest=snapshot.digest(),
                    sequence=sequence,
                    stale=stale,
                )
                self._provider_events[event_key] = record  # type: ignore[index]
                self._event_replays[event_key] = _ReplayRecord(request_digest, result)  # type: ignore[index]
                self._trace.append({"event": "provider_notification_processed", **record.canonical()})
            else:
                self._trace.append(
                    {
                        "event": "purchase_reconciled",
                        "provider": snapshot.provider.value,
                        "environment": snapshot.environment.value,
                        "operation_id": operation_id,
                        "account_id": account_id,
                        "purchase_id": snapshot.purchase_id,
                        "sequence": sequence,
                        "stale": stale,
                    }
                )
            return result

    def _entitlement_for(
        self,
        account_id: str,
        entitlement_id: str,
        *,
        now_ms: int,
    ) -> EntitlementSnapshot | None:
        candidates: list[tuple[int, int, str, PurchaseRecord, EntitlementAccessState]] = []
        for record in self._purchases.values():
            if record.account_id != account_id or record.entitlement_id != entitlement_id:
                continue
            state = _access_state(record, now_ms)
            candidates.append(
                (
                    _ACCESS_PRIORITY[state],
                    record.effective_at_ms,
                    record.purchase_id,
                    record,
                    state,
                )
            )
        if not candidates:
            return None
        _, _, _, record, state = max(candidates, key=lambda item: (item[0], item[1], item[2]))
        return EntitlementSnapshot(
            account_id=account_id,
            entitlement_id=entitlement_id,
            state=state,
            grants_access=state in (EntitlementAccessState.ACTIVE, EntitlementAccessState.GRACE),
            source_purchase_id=record.purchase_id,
            product_id=record.product_id,
            provider=record.provider,
            environment=record.environment,
            effective_at_ms=record.effective_at_ms,
            expires_at_ms=record.expires_at_ms,
        )

    def entitlement(
        self,
        actor: AuthorityActorContext,
        *,
        account_id: str,
        entitlement_id: str,
    ) -> EntitlementSnapshot | None:
        account_id = _stable_id(account_id, field="account_id")
        entitlement_id = _stable_id(entitlement_id, field="entitlement_id")
        self._authorize(actor, "billing.entitlement.read", account_id)
        now_ms = _server_now_ms(self.clock_ms)
        with self._lock:
            return self._entitlement_for(account_id, entitlement_id, now_ms=now_ms)

    def purchase_records(self) -> tuple[PurchaseRecord, ...]:
        with self._lock:
            return tuple(
                sorted(
                    self._purchases.values(),
                    key=lambda item: (
                        item.provider.value,
                        item.environment.value,
                        item.purchase_id,
                    ),
                )
            )

    def provider_events(self) -> tuple[ProviderEventRecord, ...]:
        with self._lock:
            return tuple(
                sorted(
                    self._provider_events.values(),
                    key=lambda item: (
                        item.provider.value,
                        item.environment.value,
                        item.message_id,
                    ),
                )
            )

    def catalog_definitions(self) -> tuple[CatalogProductDefinition, ...]:
        with self._lock:
            return tuple(
                self._catalog[key]
                for key in sorted(self._catalog, key=lambda item: (item[0], item[1]))
            )

    def canonical_state(self) -> dict[str, object]:
        now_ms = _server_now_ms(self.clock_ms)
        with self._lock:
            entitlement_keys = sorted(
                {(record.account_id, record.entitlement_id) for record in self._purchases.values()}
            )
            entitlements = [
                snapshot.canonical()
                for account_id, entitlement_id in entitlement_keys
                if (
                    snapshot := self._entitlement_for(
                        account_id,
                        entitlement_id,
                        now_ms=now_ms,
                    )
                )
                is not None
            ]
            return {
                "catalog": [
                    self._catalog[key].canonical()
                    for key in sorted(self._catalog, key=lambda item: (item[0], item[1]))
                ],
                "active_catalog": dict(sorted(self._active_catalog.items())),
                "purchases": [record.canonical() for record in self.purchase_records()],
                "provider_events": [event.canonical() for event in self.provider_events()],
                "entitlements": entitlements,
                "sequence": self._sequence,
                "budgets": {
                    "max_catalog_versions": self.max_catalog_versions,
                    "max_provider_events": self.max_provider_events,
                    "max_purchases": self.max_purchases,
                    "max_accounts": self.max_accounts,
                    "max_reconciliations": self.max_reconciliations,
                },
            }

    def state_digest(self) -> str:
        return canonical_sha256(self.canonical_state())

    def trace(self) -> tuple[dict[str, object], ...]:
        with self._lock:
            return tuple(dict(item) for item in self._trace)

    def trace_digest(self) -> str:
        return canonical_sha256(list(self.trace()))

    def redacted_evidence(self) -> dict[str, object]:
        state = self.canonical_state()
        encoded = canonical_json_bytes(state)
        return {
            "state_digest": canonical_sha256(state),
            "trace_digest": self.trace_digest(),
            "catalog_count": len(self._catalog),
            "provider_event_count": len(self._provider_events),
            "purchase_count": len(self._purchases),
            "state_bytes": len(encoded),
            "provider_live_claim": False,
            "secrets_exposed": False,
        }
