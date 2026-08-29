from __future__ import annotations

import re
import threading
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Callable

from .authority import AuthorityActorContext
from .content_delivery import ContentManifest
from .contracts import BackendEnvironmentKind, canonical_sha256
from .entitlements import BillingEnvironment, CatalogProductDefinition
from .event_pipeline import EventSchemaDefinition
from .remote_config import ConfigSnapshot, EvaluationContext, InMemoryRemoteConfigService

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_TZID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+/-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class LiveOpsPolicyError(ValueError):
    """Raised when a LiveOps definition is structurally unsafe."""


class LiveOpsStateError(RuntimeError):
    """Raised when a LiveOps transition would violate authoritative state."""


class LiveOpsAuthorizationError(PermissionError):
    """Raised when an actor lacks function or object authority."""


class LiveOpsCapacityError(LiveOpsStateError):
    """Raised when a bounded LiveOps store would exceed capacity."""


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise LiveOpsPolicyError(f"{field}_must_be_stable_id")
    return value


def _tzid(value: str) -> str:
    if not isinstance(value, str) or _TZID_RE.fullmatch(value) is None or ".." in value:
        raise LiveOpsPolicyError("display_tzid_invalid")
    return value


def _sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise LiveOpsPolicyError(f"{field}_must_be_sha256")
    return value


def _timestamp(value: int, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LiveOpsPolicyError(f"{field}_must_be_non_negative_integer")
    return value


def _positive_int(value: int, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise LiveOpsPolicyError(f"{field}_must_be_positive_integer")
    return value


def _server_now_ms(clock_ms: Callable[[], int]) -> int:
    return _timestamp(clock_ms(), field="server_time_ms")


def _environment(value: BackendEnvironmentKind) -> BackendEnvironmentKind:
    if not isinstance(value, BackendEnvironmentKind):
        raise LiveOpsPolicyError("invalid_environment")
    return value


class LiveOpsCampaignState(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    ROLLED_BACK = "rolled_back"
    KILLED = "killed"


@dataclass(frozen=True, slots=True)
class ConfigSnapshotReference:
    snapshot_id: str
    revision: int
    digest: str
    environment: BackendEnvironmentKind

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_id", _stable_id(self.snapshot_id, field="snapshot_id"))
        _positive_int(self.revision, field="snapshot_revision")
        object.__setattr__(self, "digest", _sha256(self.digest, field="snapshot_digest"))
        _environment(self.environment)

    @classmethod
    def from_snapshot(cls, snapshot: ConfigSnapshot) -> ConfigSnapshotReference:
        if not isinstance(snapshot, ConfigSnapshot):
            raise LiveOpsPolicyError("invalid_config_snapshot")
        return cls(snapshot.snapshot_id, snapshot.revision, snapshot.digest(), snapshot.environment)

    def canonical(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "revision": self.revision,
            "digest": self.digest,
            "environment": self.environment.value,
        }


@dataclass(frozen=True, slots=True)
class ContentManifestReference:
    manifest_id: str
    revision: int
    digest: str
    environment: BackendEnvironmentKind

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifest_id", _stable_id(self.manifest_id, field="manifest_id"))
        _positive_int(self.revision, field="manifest_revision")
        object.__setattr__(self, "digest", _sha256(self.digest, field="manifest_digest"))
        _environment(self.environment)

    @classmethod
    def from_manifest(cls, manifest: ContentManifest) -> ContentManifestReference:
        if not isinstance(manifest, ContentManifest):
            raise LiveOpsPolicyError("invalid_content_manifest")
        return cls(manifest.manifest_id, manifest.revision, manifest.digest(), manifest.environment)

    def canonical(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "revision": self.revision,
            "digest": self.digest,
            "environment": self.environment.value,
        }


@dataclass(frozen=True, slots=True)
class CatalogProductReference:
    product_id: str
    version: int
    entitlement_id: str
    digest: str
    billing_environment: BillingEnvironment

    def __post_init__(self) -> None:
        object.__setattr__(self, "product_id", _stable_id(self.product_id, field="product_id"))
        _positive_int(self.version, field="product_version")
        object.__setattr__(self, "entitlement_id", _stable_id(self.entitlement_id, field="entitlement_id"))
        object.__setattr__(self, "digest", _sha256(self.digest, field="product_digest"))
        if not isinstance(self.billing_environment, BillingEnvironment):
            raise LiveOpsPolicyError("invalid_billing_environment")

    @classmethod
    def from_product(cls, product: CatalogProductDefinition) -> CatalogProductReference:
        if not isinstance(product, CatalogProductDefinition):
            raise LiveOpsPolicyError("invalid_catalog_product")
        return cls(
            product.product_id,
            product.version,
            product.entitlement_id,
            product.digest(),
            product.environment,
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "version": self.version,
            "entitlement_id": self.entitlement_id,
            "digest": self.digest,
            "billing_environment": self.billing_environment.value,
        }


@dataclass(frozen=True, slots=True)
class EventContractReference:
    schema_id: str
    event_type: str
    version: int
    digest: str
    environment: BackendEnvironmentKind

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", _stable_id(self.schema_id, field="schema_id"))
        object.__setattr__(self, "event_type", _stable_id(self.event_type, field="event_type"))
        _positive_int(self.version, field="event_version")
        object.__setattr__(self, "digest", _sha256(self.digest, field="event_schema_digest"))
        _environment(self.environment)

    @classmethod
    def from_schema(cls, schema: EventSchemaDefinition) -> EventContractReference:
        if not isinstance(schema, EventSchemaDefinition):
            raise LiveOpsPolicyError("invalid_event_schema")
        return cls(schema.schema_id, schema.event_type, schema.version, schema.digest(), schema.environment)

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "event_type": self.event_type,
            "version": self.version,
            "digest": self.digest,
            "environment": self.environment.value,
        }


@dataclass(frozen=True, slots=True)
class LiveOpsScheduleWindow:
    start_at_utc_ms: int
    end_at_utc_ms: int
    display_tzid: str
    tzdb_version: str

    def __post_init__(self) -> None:
        _timestamp(self.start_at_utc_ms, field="start_at_utc_ms")
        _timestamp(self.end_at_utc_ms, field="end_at_utc_ms")
        if self.end_at_utc_ms <= self.start_at_utc_ms:
            raise LiveOpsPolicyError("schedule_end_must_follow_start")
        object.__setattr__(self, "display_tzid", _tzid(self.display_tzid))
        object.__setattr__(self, "tzdb_version", _stable_id(self.tzdb_version, field="tzdb_version"))

    def contains(self, instant_utc_ms: int) -> bool:
        instant_utc_ms = _timestamp(instant_utc_ms, field="instant_utc_ms")
        return self.start_at_utc_ms <= instant_utc_ms < self.end_at_utc_ms

    def canonical(self) -> dict[str, Any]:
        return {
            "start_at_utc_ms": self.start_at_utc_ms,
            "end_at_utc_ms": self.end_at_utc_ms,
            "display_tzid": self.display_tzid,
            "tzdb_version": self.tzdb_version,
        }


@dataclass(frozen=True, slots=True)
class LiveOpsSeasonDefinition:
    season_id: str
    version: int
    environment: BackendEnvironmentKind
    schedule: LiveOpsScheduleWindow
    created_at_ms: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "season_id", _stable_id(self.season_id, field="season_id"))
        _positive_int(self.version, field="season_version")
        _environment(self.environment)
        if not isinstance(self.schedule, LiveOpsScheduleWindow):
            raise LiveOpsPolicyError("invalid_season_schedule")
        _timestamp(self.created_at_ms, field="season_created_at_ms")

    def canonical(self) -> dict[str, Any]:
        return {
            "season_id": self.season_id,
            "version": self.version,
            "environment": self.environment.value,
            "schedule": self.schedule.canonical(),
            "created_at_ms": self.created_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LiveOpsSeasonReference:
    season_id: str
    version: int
    digest: str
    environment: BackendEnvironmentKind

    def __post_init__(self) -> None:
        object.__setattr__(self, "season_id", _stable_id(self.season_id, field="season_id"))
        _positive_int(self.version, field="season_version")
        object.__setattr__(self, "digest", _sha256(self.digest, field="season_digest"))
        _environment(self.environment)

    @classmethod
    def from_season(cls, season: LiveOpsSeasonDefinition) -> LiveOpsSeasonReference:
        if not isinstance(season, LiveOpsSeasonDefinition):
            raise LiveOpsPolicyError("invalid_season")
        return cls(season.season_id, season.version, season.digest(), season.environment)

    def canonical(self) -> dict[str, Any]:
        return {
            "season_id": self.season_id,
            "version": self.version,
            "digest": self.digest,
            "environment": self.environment.value,
        }


@dataclass(frozen=True, slots=True)
class LiveOpsAudience:
    flag_id: str
    allowed_variants: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "flag_id", _stable_id(self.flag_id, field="audience_flag_id"))
        variants = tuple(sorted({_stable_id(item, field="audience_variant") for item in self.allowed_variants}))
        if not variants:
            raise LiveOpsPolicyError("audience_requires_variant")
        object.__setattr__(self, "allowed_variants", variants)

    def canonical(self) -> dict[str, Any]:
        return {"flag_id": self.flag_id, "allowed_variants": list(self.allowed_variants)}


@dataclass(frozen=True, slots=True)
class LiveOpsRotation:
    rotation_id: str
    start_at_utc_ms: int
    end_at_utc_ms: int
    content_manifest_digest: str | None = None
    config_snapshot_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rotation_id", _stable_id(self.rotation_id, field="rotation_id"))
        _timestamp(self.start_at_utc_ms, field="rotation_start_at_utc_ms")
        _timestamp(self.end_at_utc_ms, field="rotation_end_at_utc_ms")
        if self.end_at_utc_ms <= self.start_at_utc_ms:
            raise LiveOpsPolicyError("rotation_end_must_follow_start")
        if self.content_manifest_digest is not None:
            object.__setattr__(self, "content_manifest_digest", _sha256(self.content_manifest_digest, field="rotation_manifest_digest"))
        if self.config_snapshot_digest is not None:
            object.__setattr__(self, "config_snapshot_digest", _sha256(self.config_snapshot_digest, field="rotation_snapshot_digest"))
        if self.content_manifest_digest is None and self.config_snapshot_digest is None:
            raise LiveOpsPolicyError("rotation_requires_dependency")

    def canonical(self) -> dict[str, Any]:
        return {
            "rotation_id": self.rotation_id,
            "start_at_utc_ms": self.start_at_utc_ms,
            "end_at_utc_ms": self.end_at_utc_ms,
            "content_manifest_digest": self.content_manifest_digest,
            "config_snapshot_digest": self.config_snapshot_digest,
        }


@dataclass(frozen=True, slots=True)
class LiveOpsCampaignDefinition:
    campaign_id: str
    version: int
    season: LiveOpsSeasonReference
    environment: BackendEnvironmentKind
    schedule: LiveOpsScheduleWindow
    config_snapshot: ConfigSnapshotReference
    content_manifest: ContentManifestReference
    catalog_products: tuple[CatalogProductReference, ...]
    event_contracts: tuple[EventContractReference, ...]
    rotations: tuple[LiveOpsRotation, ...] = ()
    audience: LiveOpsAudience | None = None
    created_at_ms: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "campaign_id", _stable_id(self.campaign_id, field="campaign_id"))
        _positive_int(self.version, field="campaign_version")
        if not isinstance(self.season, LiveOpsSeasonReference):
            raise LiveOpsPolicyError("invalid_season_reference")
        environment = _environment(self.environment)
        if not isinstance(self.schedule, LiveOpsScheduleWindow):
            raise LiveOpsPolicyError("invalid_schedule")
        if not isinstance(self.config_snapshot, ConfigSnapshotReference):
            raise LiveOpsPolicyError("invalid_config_snapshot_reference")
        if not isinstance(self.content_manifest, ContentManifestReference):
            raise LiveOpsPolicyError("invalid_content_manifest_reference")
        products = tuple(self.catalog_products)
        events = tuple(self.event_contracts)
        rotations = tuple(self.rotations)
        if not products:
            raise LiveOpsPolicyError("campaign_requires_catalog_product")
        if not events:
            raise LiveOpsPolicyError("campaign_requires_event_contract")
        if any(not isinstance(item, CatalogProductReference) for item in products):
            raise LiveOpsPolicyError("invalid_catalog_product_reference")
        if any(not isinstance(item, EventContractReference) for item in events):
            raise LiveOpsPolicyError("invalid_event_contract_reference")
        if any(not isinstance(item, LiveOpsRotation) for item in rotations):
            raise LiveOpsPolicyError("invalid_rotation")
        if self.audience is not None and not isinstance(self.audience, LiveOpsAudience):
            raise LiveOpsPolicyError("invalid_audience")
        backend_refs = (self.season, self.config_snapshot, self.content_manifest, *events)
        if any(item.environment is not environment for item in backend_refs):
            raise LiveOpsPolicyError("campaign_environment_mismatch")
        if environment is BackendEnvironmentKind.PRODUCTION:
            if any(item.billing_environment is not BillingEnvironment.PRODUCTION for item in products):
                raise LiveOpsPolicyError("production_campaign_requires_production_billing")
        elif any(item.billing_environment is BillingEnvironment.PRODUCTION for item in products):
            raise LiveOpsPolicyError("nonproduction_campaign_rejects_production_billing")
        if len({(item.product_id, item.version) for item in products}) != len(products):
            raise LiveOpsPolicyError("duplicate_catalog_product_reference")
        if len({(item.schema_id, item.version) for item in events}) != len(events):
            raise LiveOpsPolicyError("duplicate_event_contract_reference")
        manifest_digests = {self.content_manifest.digest}
        config_digests = {self.config_snapshot.digest}
        rotations = tuple(sorted(rotations, key=lambda item: (item.start_at_utc_ms, item.end_at_utc_ms, item.rotation_id)))
        previous_end: int | None = None
        seen_rotation_ids: set[str] = set()
        for rotation in rotations:
            if rotation.rotation_id in seen_rotation_ids:
                raise LiveOpsPolicyError("duplicate_rotation_id")
            seen_rotation_ids.add(rotation.rotation_id)
            if rotation.start_at_utc_ms < self.schedule.start_at_utc_ms or rotation.end_at_utc_ms > self.schedule.end_at_utc_ms:
                raise LiveOpsPolicyError("rotation_outside_campaign_schedule")
            if previous_end is not None and rotation.start_at_utc_ms < previous_end:
                raise LiveOpsPolicyError("rotation_overlap")
            previous_end = rotation.end_at_utc_ms
            if rotation.content_manifest_digest is not None and rotation.content_manifest_digest not in manifest_digests:
                raise LiveOpsPolicyError("rotation_manifest_not_campaign_dependency")
            if rotation.config_snapshot_digest is not None and rotation.config_snapshot_digest not in config_digests:
                raise LiveOpsPolicyError("rotation_snapshot_not_campaign_dependency")
        object.__setattr__(self, "catalog_products", tuple(sorted(products, key=lambda item: (item.product_id, item.version))))
        object.__setattr__(self, "event_contracts", tuple(sorted(events, key=lambda item: (item.schema_id, item.version))))
        object.__setattr__(self, "rotations", rotations)
        _timestamp(self.created_at_ms, field="created_at_ms")

    def canonical(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "version": self.version,
            "season": self.season.canonical(),
            "environment": self.environment.value,
            "schedule": self.schedule.canonical(),
            "config_snapshot": self.config_snapshot.canonical(),
            "content_manifest": self.content_manifest.canonical(),
            "catalog_products": [item.canonical() for item in self.catalog_products],
            "event_contracts": [item.canonical() for item in self.event_contracts],
            "rotations": [item.canonical() for item in self.rotations],
            "audience": self.audience.canonical() if self.audience is not None else None,
            "created_at_ms": self.created_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LiveOpsPreview:
    preview_id: str
    campaign_id: str
    campaign_version: int
    campaign_digest: str
    environment: BackendEnvironmentKind
    dependency_digest: str
    expected_state: LiveOpsCampaignState
    current_state: LiveOpsCampaignState
    evaluated_at_ms: int
    mutation_count: int = 0

    def binding_canonical(self) -> dict[str, Any]:
        return {
            "preview_id": self.preview_id,
            "campaign_id": self.campaign_id,
            "campaign_version": self.campaign_version,
            "campaign_digest": self.campaign_digest,
            "environment": self.environment.value,
            "dependency_digest": self.dependency_digest,
            "expected_state": self.expected_state.value,
            "current_state": self.current_state.value,
            "mutation_count": self.mutation_count,
        }

    def canonical(self) -> dict[str, Any]:
        payload = self.binding_canonical()
        payload["evaluated_at_ms"] = self.evaluated_at_ms
        return payload

    def digest(self) -> str:
        return canonical_sha256(self.binding_canonical())


@dataclass(frozen=True, slots=True)
class LiveOpsApproval:
    approval_id: str
    preview_digest: str
    campaign_digest: str
    safe_change_digest: str
    approver_account_id: str
    approved_at_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "approval_id", _stable_id(self.approval_id, field="approval_id"))
        object.__setattr__(self, "preview_digest", _sha256(self.preview_digest, field="preview_digest"))
        object.__setattr__(self, "campaign_digest", _sha256(self.campaign_digest, field="campaign_digest"))
        object.__setattr__(self, "safe_change_digest", _sha256(self.safe_change_digest, field="safe_change_digest"))
        object.__setattr__(self, "approver_account_id", _stable_id(self.approver_account_id, field="approver_account_id"))
        _timestamp(self.approved_at_ms, field="approved_at_ms")

    def canonical(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "preview_digest": self.preview_digest,
            "campaign_digest": self.campaign_digest,
            "safe_change_digest": self.safe_change_digest,
            "approver_account_id": self.approver_account_id,
            "approved_at_ms": self.approved_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LiveOpsActivationRecord:
    activation_id: str
    campaign_id: str
    campaign_version: int
    campaign_digest: str
    approval_digest: str
    state: LiveOpsCampaignState
    activated_at_ms: int
    safe_change_digest: str

    def canonical(self) -> dict[str, Any]:
        return {
            "activation_id": self.activation_id,
            "campaign_id": self.campaign_id,
            "campaign_version": self.campaign_version,
            "campaign_digest": self.campaign_digest,
            "approval_digest": self.approval_digest,
            "state": self.state.value,
            "activated_at_ms": self.activated_at_ms,
            "safe_change_digest": self.safe_change_digest,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LiveOpsRuntimeRecord:
    campaign_id: str
    campaign_version: int
    activation_id: str
    state: LiveOpsCampaignState
    updated_at_ms: int
    transition_sequence: int
    rollback_reason: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_version": self.campaign_version,
            "activation_id": self.activation_id,
            "state": self.state.value,
            "updated_at_ms": self.updated_at_ms,
            "transition_sequence": self.transition_sequence,
            "rollback_reason": self.rollback_reason,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LiveOpsAudienceResult:
    campaign_id: str
    flag_id: str | None
    eligible: bool
    context_digest: str
    evaluation_digest: str | None
    variant: str | None

    def canonical(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "flag_id": self.flag_id,
            "eligible": self.eligible,
            "context_digest": self.context_digest,
            "evaluation_digest": self.evaluation_digest,
            "variant": self.variant,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LiveOpsAuditRecord:
    sequence: int
    action: str
    actor_account_id: str
    campaign_id: str
    campaign_version: int
    state: LiveOpsCampaignState
    recorded_at_ms: int
    activation_id: str | None = None
    safe_change_digest: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "action": self.action,
            "actor_account_id": self.actor_account_id,
            "campaign_id": self.campaign_id,
            "campaign_version": self.campaign_version,
            "state": self.state.value,
            "recorded_at_ms": self.recorded_at_ms,
            "activation_id": self.activation_id,
            "safe_change_digest": self.safe_change_digest,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LiveOpsStateSnapshot:
    season_digests: tuple[str, ...]
    campaign_digests: tuple[str, ...]
    activation_digests: tuple[str, ...]
    runtime_digests: tuple[str, ...]
    dependency_digest: str
    audit_digest: str
    trace_digest: str

    def canonical(self) -> dict[str, Any]:
        return {
            "season_digests": list(self.season_digests),
            "campaign_digests": list(self.campaign_digests),
            "activation_digests": list(self.activation_digests),
            "runtime_digests": list(self.runtime_digests),
            "dependency_digest": self.dependency_digest,
            "audit_digest": self.audit_digest,
            "trace_digest": self.trace_digest,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class InMemoryLiveOpsService:
    """Deterministic provider-neutral LiveOps authority with explicit transitions."""

    def __init__(
        self,
        *,
        clock_ms: Callable[[], int],
        max_seasons: int = 1_024,
        max_campaigns: int = 4_096,
        max_dependencies: int = 16_384,
        max_activations: int = 16_384,
        max_audit_records: int = 100_000,
        max_trace_records: int = 200_000,
    ) -> None:
        for name, value in (
            ("max_seasons", max_seasons),
            ("max_campaigns", max_campaigns),
            ("max_dependencies", max_dependencies),
            ("max_activations", max_activations),
            ("max_audit_records", max_audit_records),
            ("max_trace_records", max_trace_records),
        ):
            _positive_int(value, field=name)
        self.clock_ms = clock_ms
        self.max_seasons = max_seasons
        self.max_campaigns = max_campaigns
        self.max_dependencies = max_dependencies
        self.max_activations = max_activations
        self.max_audit_records = max_audit_records
        self.max_trace_records = max_trace_records
        self._lock = threading.RLock()
        self._seasons: dict[tuple[str, int], LiveOpsSeasonDefinition] = {}
        self._campaigns: dict[tuple[str, int], LiveOpsCampaignDefinition] = {}
        self._config_dependencies: dict[tuple[BackendEnvironmentKind, str, int], str] = {}
        self._content_dependencies: dict[tuple[BackendEnvironmentKind, str, int], str] = {}
        self._catalog_dependencies: dict[tuple[BillingEnvironment, str, int], tuple[str, str]] = {}
        self._event_dependencies: dict[tuple[BackendEnvironmentKind, str, int], tuple[str, str]] = {}
        self._approvals: dict[str, LiveOpsApproval] = {}
        self._activations: dict[str, LiveOpsActivationRecord] = {}
        self._runtime: dict[tuple[str, int], LiveOpsRuntimeRecord] = {}
        self._audit: list[LiveOpsAuditRecord] = []
        self._trace: list[dict[str, Any]] = []
        self._sequence = 0

    @staticmethod
    def _authorize(actor: AuthorityActorContext, permission: str, target_id: str) -> None:
        if not isinstance(actor, AuthorityActorContext):
            raise LiveOpsPolicyError("invalid_actor")
        if not actor.can(permission, target_id):
            raise LiveOpsAuthorizationError("forbidden")

    def _dependency_count(self) -> int:
        return (
            len(self._config_dependencies)
            + len(self._content_dependencies)
            + len(self._catalog_dependencies)
            + len(self._event_dependencies)
        )

    def _reserve_dependency(self, *, existing: bool) -> None:
        if not existing and self._dependency_count() >= self.max_dependencies:
            raise LiveOpsCapacityError("dependency_capacity")

    def register_config_snapshot(self, actor: AuthorityActorContext, snapshot: ConfigSnapshot) -> ConfigSnapshotReference:
        if not isinstance(snapshot, ConfigSnapshot):
            raise LiveOpsPolicyError("invalid_config_snapshot")
        self._authorize(actor, "liveops.dependency.register", snapshot.snapshot_id)
        ref = ConfigSnapshotReference.from_snapshot(snapshot)
        key = (ref.environment, ref.snapshot_id, ref.revision)
        with self._lock:
            existing = self._config_dependencies.get(key)
            self._reserve_dependency(existing=existing is not None)
            if existing is not None and existing != ref.digest:
                raise LiveOpsStateError("config_dependency_rebind")
            self._config_dependencies[key] = ref.digest
            return ref

    def register_content_manifest(self, actor: AuthorityActorContext, manifest: ContentManifest) -> ContentManifestReference:
        if not isinstance(manifest, ContentManifest):
            raise LiveOpsPolicyError("invalid_content_manifest")
        self._authorize(actor, "liveops.dependency.register", manifest.manifest_id)
        ref = ContentManifestReference.from_manifest(manifest)
        key = (ref.environment, ref.manifest_id, ref.revision)
        with self._lock:
            existing = self._content_dependencies.get(key)
            self._reserve_dependency(existing=existing is not None)
            if existing is not None and existing != ref.digest:
                raise LiveOpsStateError("content_dependency_rebind")
            self._content_dependencies[key] = ref.digest
            return ref

    def register_catalog_product(self, actor: AuthorityActorContext, product: CatalogProductDefinition) -> CatalogProductReference:
        if not isinstance(product, CatalogProductDefinition):
            raise LiveOpsPolicyError("invalid_catalog_product")
        self._authorize(actor, "liveops.dependency.register", product.product_id)
        ref = CatalogProductReference.from_product(product)
        key = (ref.billing_environment, ref.product_id, ref.version)
        value = (ref.entitlement_id, ref.digest)
        with self._lock:
            existing = self._catalog_dependencies.get(key)
            self._reserve_dependency(existing=existing is not None)
            if existing is not None and existing != value:
                raise LiveOpsStateError("catalog_dependency_rebind")
            self._catalog_dependencies[key] = value
            return ref

    def register_event_schema(self, actor: AuthorityActorContext, schema: EventSchemaDefinition) -> EventContractReference:
        if not isinstance(schema, EventSchemaDefinition):
            raise LiveOpsPolicyError("invalid_event_schema")
        self._authorize(actor, "liveops.dependency.register", schema.schema_id)
        ref = EventContractReference.from_schema(schema)
        key = (ref.environment, ref.schema_id, ref.version)
        value = (ref.event_type, ref.digest)
        with self._lock:
            existing = self._event_dependencies.get(key)
            self._reserve_dependency(existing=existing is not None)
            if existing is not None and existing != value:
                raise LiveOpsStateError("event_dependency_rebind")
            self._event_dependencies[key] = value
            return ref

    def _validate_dependencies(self, campaign: LiveOpsCampaignDefinition) -> str:
        config_key = (campaign.environment, campaign.config_snapshot.snapshot_id, campaign.config_snapshot.revision)
        if self._config_dependencies.get(config_key) != campaign.config_snapshot.digest:
            raise LiveOpsStateError("config_dependency_unavailable")
        content_key = (campaign.environment, campaign.content_manifest.manifest_id, campaign.content_manifest.revision)
        if self._content_dependencies.get(content_key) != campaign.content_manifest.digest:
            raise LiveOpsStateError("content_dependency_unavailable")
        for product in campaign.catalog_products:
            key = (product.billing_environment, product.product_id, product.version)
            if self._catalog_dependencies.get(key) != (product.entitlement_id, product.digest):
                raise LiveOpsStateError("catalog_dependency_unavailable")
        for event in campaign.event_contracts:
            key = (campaign.environment, event.schema_id, event.version)
            if self._event_dependencies.get(key) != (event.event_type, event.digest):
                raise LiveOpsStateError("event_dependency_unavailable")
        payload = {
            "config": campaign.config_snapshot.canonical(),
            "content": campaign.content_manifest.canonical(),
            "catalog": [item.canonical() for item in campaign.catalog_products],
            "events": [item.canonical() for item in campaign.event_contracts],
        }
        return canonical_sha256(payload)

    def register_season(self, actor: AuthorityActorContext, season: LiveOpsSeasonDefinition) -> LiveOpsSeasonDefinition:
        if not isinstance(season, LiveOpsSeasonDefinition):
            raise LiveOpsPolicyError("invalid_season")
        self._authorize(actor, "liveops.season.register", season.season_id)
        key = (season.season_id, season.version)
        with self._lock:
            existing = self._seasons.get(key)
            if existing is not None:
                if existing != season:
                    raise LiveOpsStateError("season_version_rebind")
                return existing
            if len(self._seasons) >= self.max_seasons:
                raise LiveOpsCapacityError("season_capacity")
            if len(self._trace) >= self.max_trace_records:
                raise LiveOpsCapacityError("trace_capacity")
            self._seasons[key] = season
            self._append_trace(
                {
                    "event": "season_registered",
                    "season_id": season.season_id,
                    "season_version": season.version,
                    "season_digest": season.digest(),
                    "environment": season.environment.value,
                }
            )
            return season

    def season(self, season_id: str, version: int) -> LiveOpsSeasonDefinition:
        season_id = _stable_id(season_id, field="season_id")
        _positive_int(version, field="season_version")
        try:
            return self._seasons[(season_id, version)]
        except KeyError as exc:
            raise LiveOpsStateError("season_not_found") from exc

    def _validate_season(self, campaign: LiveOpsCampaignDefinition) -> str:
        season = self.season(campaign.season.season_id, campaign.season.version)
        if season.digest() != campaign.season.digest:
            raise LiveOpsStateError("season_dependency_unavailable")
        if season.environment is not campaign.environment:
            raise LiveOpsStateError("season_environment_mismatch")
        if (
            campaign.schedule.start_at_utc_ms < season.schedule.start_at_utc_ms
            or campaign.schedule.end_at_utc_ms > season.schedule.end_at_utc_ms
        ):
            raise LiveOpsStateError("campaign_outside_season_schedule")
        return season.digest()

    def register_campaign(self, actor: AuthorityActorContext, campaign: LiveOpsCampaignDefinition) -> LiveOpsCampaignDefinition:
        if not isinstance(campaign, LiveOpsCampaignDefinition):
            raise LiveOpsPolicyError("invalid_campaign")
        self._authorize(actor, "liveops.campaign.register", campaign.campaign_id)
        self._validate_season(campaign)
        self._validate_dependencies(campaign)
        key = (campaign.campaign_id, campaign.version)
        with self._lock:
            existing = self._campaigns.get(key)
            if existing is not None:
                if existing != campaign:
                    raise LiveOpsStateError("campaign_version_rebind")
                return existing
            if len(self._campaigns) >= self.max_campaigns:
                raise LiveOpsCapacityError("campaign_capacity")
            for (campaign_id, _version), other in self._campaigns.items():
                if campaign_id == campaign.campaign_id and other.version == campaign.version and other.digest() != campaign.digest():
                    raise LiveOpsStateError("campaign_version_rebind")
            if len(self._trace) >= self.max_trace_records:
                raise LiveOpsCapacityError("trace_capacity")
            self._campaigns[key] = campaign
            self._append_trace(
                {
                    "event": "campaign_registered",
                    "campaign_id": campaign.campaign_id,
                    "campaign_version": campaign.version,
                    "campaign_digest": campaign.digest(),
                    "environment": campaign.environment.value,
                }
            )
            return campaign

    def campaign(self, campaign_id: str, version: int) -> LiveOpsCampaignDefinition:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        _positive_int(version, field="campaign_version")
        try:
            return self._campaigns[(campaign_id, version)]
        except KeyError as exc:
            raise LiveOpsStateError("campaign_not_found") from exc

    def _current_state(self, campaign: LiveOpsCampaignDefinition) -> LiveOpsCampaignState:
        runtime = self._runtime.get((campaign.campaign_id, campaign.version))
        return LiveOpsCampaignState.DRAFT if runtime is None else runtime.state

    @staticmethod
    def _expected_state(campaign: LiveOpsCampaignDefinition, now_ms: int) -> LiveOpsCampaignState:
        if now_ms < campaign.schedule.start_at_utc_ms:
            return LiveOpsCampaignState.SCHEDULED
        if campaign.schedule.contains(now_ms):
            return LiveOpsCampaignState.ACTIVE
        return LiveOpsCampaignState.EXPIRED

    def _build_preview(self, campaign: LiveOpsCampaignDefinition) -> LiveOpsPreview:
        dependency_digest = self._validate_dependencies(campaign)
        now_ms = _server_now_ms(self.clock_ms)
        current_state = self._current_state(campaign)
        expected_state = self._expected_state(campaign, now_ms)
        binding_seed = {
            "campaign_digest": campaign.digest(),
            "dependency_digest": dependency_digest,
            "expected_state": expected_state.value,
            "current_state": current_state.value,
        }
        return LiveOpsPreview(
            preview_id=f"liveops.preview.{canonical_sha256(binding_seed)[:24]}",
            campaign_id=campaign.campaign_id,
            campaign_version=campaign.version,
            campaign_digest=campaign.digest(),
            environment=campaign.environment,
            dependency_digest=dependency_digest,
            expected_state=expected_state,
            current_state=current_state,
            evaluated_at_ms=now_ms,
            mutation_count=0,
        )

    def preview_campaign(self, actor: AuthorityActorContext, *, campaign_id: str, version: int) -> LiveOpsPreview:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        self._authorize(actor, "liveops.campaign.preview", campaign_id)
        return self._build_preview(self.campaign(campaign_id, version))

    def approve_campaign(
        self,
        actor: AuthorityActorContext,
        *,
        preview: LiveOpsPreview,
        approval_id: str,
        safe_change_digest: str,
    ) -> LiveOpsApproval:
        if not isinstance(preview, LiveOpsPreview):
            raise LiveOpsPolicyError("invalid_preview")
        approval_id = _stable_id(approval_id, field="approval_id")
        safe_change_digest = _sha256(safe_change_digest, field="safe_change_digest")
        self._authorize(actor, "liveops.campaign.approve", preview.campaign_id)
        campaign = self.campaign(preview.campaign_id, preview.campaign_version)
        current = self._build_preview(campaign)
        if current.digest() != preview.digest():
            raise LiveOpsStateError("stale_preview")
        with self._lock:
            existing = self._approvals.get(approval_id)
            if existing is not None:
                if (
                    existing.preview_digest != preview.digest()
                    or existing.campaign_digest != preview.campaign_digest
                    or existing.safe_change_digest != safe_change_digest
                    or existing.approver_account_id != actor.account_id
                ):
                    raise LiveOpsStateError("approval_id_rebind")
                return existing
            if len(self._audit) >= self.max_audit_records:
                raise LiveOpsCapacityError("audit_capacity")
            approval = LiveOpsApproval(
                approval_id=approval_id,
                preview_digest=preview.digest(),
                campaign_digest=preview.campaign_digest,
                safe_change_digest=safe_change_digest,
                approver_account_id=actor.account_id,
                approved_at_ms=_server_now_ms(self.clock_ms),
            )
            self._approvals[approval.approval_id] = approval
            self._append_audit(
                actor=actor,
                action="campaign_approved",
                campaign=campaign,
                state=LiveOpsCampaignState.APPROVED,
                safe_change_digest=approval.safe_change_digest,
            )
            return approval

    def _validated_approval(
        self,
        *,
        actor: AuthorityActorContext,
        campaign: LiveOpsCampaignDefinition,
        approval: LiveOpsApproval,
    ) -> tuple[LiveOpsApproval, LiveOpsPreview]:
        if not isinstance(approval, LiveOpsApproval):
            raise LiveOpsAuthorizationError("activation_requires_approval")
        stored = self._approvals.get(approval.approval_id)
        if stored != approval:
            raise LiveOpsAuthorizationError("approval_not_registered")
        preview = self._build_preview(campaign)
        if approval.preview_digest != preview.digest() or approval.campaign_digest != campaign.digest():
            raise LiveOpsAuthorizationError("approval_target_mismatch")
        return approval, preview

    def activate_campaign(
        self,
        actor: AuthorityActorContext,
        *,
        campaign_id: str,
        version: int,
        activation_id: str,
        approval: LiveOpsApproval,
    ) -> LiveOpsActivationRecord:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        activation_id = _stable_id(activation_id, field="activation_id")
        self._authorize(actor, "liveops.campaign.activate", campaign_id)
        campaign = self.campaign(campaign_id, version)
        with self._lock:
            existing = self._activations.get(activation_id)
            if existing is not None:
                if (
                    not isinstance(approval, LiveOpsApproval)
                    or self._approvals.get(approval.approval_id) != approval
                    or existing.campaign_id != campaign.campaign_id
                    or existing.campaign_version != campaign.version
                    or existing.campaign_digest != campaign.digest()
                    or existing.approval_digest != approval.digest()
                    or existing.safe_change_digest != approval.safe_change_digest
                ):
                    raise LiveOpsStateError("activation_id_rebind")
                return existing
        self._validate_dependencies(campaign)
        checked, _preview = self._validated_approval(actor=actor, campaign=campaign, approval=approval)
        now_ms = _server_now_ms(self.clock_ms)
        if now_ms >= campaign.schedule.end_at_utc_ms:
            raise LiveOpsStateError("campaign_window_expired")
        state = LiveOpsCampaignState.SCHEDULED if now_ms < campaign.schedule.start_at_utc_ms else LiveOpsCampaignState.ACTIVE
        record = LiveOpsActivationRecord(
            activation_id=activation_id,
            campaign_id=campaign.campaign_id,
            campaign_version=campaign.version,
            campaign_digest=campaign.digest(),
            approval_digest=checked.digest(),
            state=state,
            activated_at_ms=now_ms,
            safe_change_digest=checked.safe_change_digest,
        )
        with self._lock:
            if len(self._activations) >= self.max_activations:
                raise LiveOpsCapacityError("activation_capacity")
            if len(self._audit) >= self.max_audit_records:
                raise LiveOpsCapacityError("audit_capacity")
            if len(self._trace) >= self.max_trace_records:
                raise LiveOpsCapacityError("trace_capacity")
            key = (campaign.campaign_id, campaign.version)
            runtime = self._runtime.get(key)
            if runtime is not None and runtime.activation_id != activation_id and runtime.state not in {
                LiveOpsCampaignState.EXPIRED,
                LiveOpsCampaignState.ROLLED_BACK,
                LiveOpsCampaignState.KILLED,
            }:
                raise LiveOpsStateError("campaign_already_activated")
            self._activations[activation_id] = record
            self._runtime[key] = LiveOpsRuntimeRecord(
                campaign_id=campaign.campaign_id,
                campaign_version=campaign.version,
                activation_id=activation_id,
                state=state,
                updated_at_ms=now_ms,
                transition_sequence=1,
            )
            self._append_audit(
                actor=actor,
                action="campaign_scheduled" if state is LiveOpsCampaignState.SCHEDULED else "campaign_activated",
                campaign=campaign,
                state=state,
                activation_id=activation_id,
                safe_change_digest=checked.safe_change_digest,
            )
            self._append_trace(
                {
                    "event": "campaign_activation",
                    "campaign_id": campaign.campaign_id,
                    "campaign_version": campaign.version,
                    "activation_id": activation_id,
                    "state": state.value,
                    "campaign_digest": campaign.digest(),
                    "approval_digest": checked.digest(),
                    "safe_change_digest": checked.safe_change_digest,
                }
            )
            return record

    def runtime(self, campaign_id: str, version: int) -> LiveOpsRuntimeRecord:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        _positive_int(version, field="campaign_version")
        try:
            return self._runtime[(campaign_id, version)]
        except KeyError as exc:
            raise LiveOpsStateError("campaign_not_activated") from exc

    def _transition(
        self,
        *,
        actor: AuthorityActorContext,
        campaign: LiveOpsCampaignDefinition,
        state: LiveOpsCampaignState,
        action: str,
        rollback_reason: str | None = None,
    ) -> LiveOpsRuntimeRecord:
        key = (campaign.campaign_id, campaign.version)
        current = self.runtime(campaign.campaign_id, campaign.version)
        now_ms = _server_now_ms(self.clock_ms)
        if len(self._audit) >= self.max_audit_records:
            raise LiveOpsCapacityError("audit_capacity")
        if len(self._trace) >= self.max_trace_records:
            raise LiveOpsCapacityError("trace_capacity")
        next_record = replace(
            current,
            state=state,
            updated_at_ms=now_ms,
            transition_sequence=current.transition_sequence + 1,
            rollback_reason=rollback_reason,
        )
        self._runtime[key] = next_record
        activation = self._activations[current.activation_id]
        self._append_audit(
            actor=actor,
            action=action,
            campaign=campaign,
            state=state,
            activation_id=current.activation_id,
            safe_change_digest=activation.safe_change_digest,
        )
        self._append_trace(
            {
                "event": action,
                "campaign_id": campaign.campaign_id,
                "campaign_version": campaign.version,
                "activation_id": current.activation_id,
                "state": state.value,
                "transition_sequence": next_record.transition_sequence,
                "rollback_reason": rollback_reason,
            }
        )
        return next_record

    def _advance_campaign(
        self,
        actor: AuthorityActorContext,
        campaign: LiveOpsCampaignDefinition,
    ) -> LiveOpsRuntimeRecord:
        current = self.runtime(campaign.campaign_id, campaign.version)
        now_ms = _server_now_ms(self.clock_ms)
        if current.state in {LiveOpsCampaignState.ROLLED_BACK, LiveOpsCampaignState.KILLED, LiveOpsCampaignState.EXPIRED}:
            return current
        if now_ms >= campaign.schedule.end_at_utc_ms:
            return self._transition(actor=actor, campaign=campaign, state=LiveOpsCampaignState.EXPIRED, action="campaign_expired")
        if current.state is LiveOpsCampaignState.SCHEDULED and now_ms >= campaign.schedule.start_at_utc_ms:
            return self._transition(actor=actor, campaign=campaign, state=LiveOpsCampaignState.ACTIVE, action="campaign_activated")
        return current

    def advance_campaign(self, actor: AuthorityActorContext, *, campaign_id: str, version: int) -> LiveOpsRuntimeRecord:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        self._authorize(actor, "liveops.campaign.advance", campaign_id)
        return self._advance_campaign(actor, self.campaign(campaign_id, version))

    def pause_campaign(self, actor: AuthorityActorContext, *, campaign_id: str, version: int) -> LiveOpsRuntimeRecord:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        self._authorize(actor, "liveops.campaign.pause", campaign_id)
        campaign = self.campaign(campaign_id, version)
        current = self._advance_campaign(actor, campaign)
        if current.state not in {LiveOpsCampaignState.SCHEDULED, LiveOpsCampaignState.ACTIVE}:
            raise LiveOpsStateError("campaign_not_pausable")
        return self._transition(actor=actor, campaign=campaign, state=LiveOpsCampaignState.PAUSED, action="campaign_paused")

    def resume_campaign(self, actor: AuthorityActorContext, *, campaign_id: str, version: int) -> LiveOpsRuntimeRecord:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        self._authorize(actor, "liveops.campaign.resume", campaign_id)
        campaign = self.campaign(campaign_id, version)
        current = self.runtime(campaign_id, version)
        if current.state is not LiveOpsCampaignState.PAUSED:
            raise LiveOpsStateError("campaign_not_paused")
        now_ms = _server_now_ms(self.clock_ms)
        if now_ms >= campaign.schedule.end_at_utc_ms:
            return self._transition(actor=actor, campaign=campaign, state=LiveOpsCampaignState.EXPIRED, action="campaign_expired")
        state = LiveOpsCampaignState.SCHEDULED if now_ms < campaign.schedule.start_at_utc_ms else LiveOpsCampaignState.ACTIVE
        return self._transition(actor=actor, campaign=campaign, state=state, action="campaign_resumed")

    def rollback_campaign(
        self,
        actor: AuthorityActorContext,
        *,
        campaign_id: str,
        version: int,
        reason: str,
    ) -> LiveOpsRuntimeRecord:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        reason = _stable_id(reason, field="rollback_reason")
        self._authorize(actor, "liveops.campaign.rollback", campaign_id)
        campaign = self.campaign(campaign_id, version)
        current = self.runtime(campaign_id, version)
        if current.state in {LiveOpsCampaignState.ROLLED_BACK, LiveOpsCampaignState.KILLED}:
            return current
        return self._transition(
            actor=actor,
            campaign=campaign,
            state=LiveOpsCampaignState.ROLLED_BACK,
            action="campaign_rolled_back",
            rollback_reason=reason,
        )

    def kill_campaign(self, actor: AuthorityActorContext, *, campaign_id: str, version: int) -> LiveOpsRuntimeRecord:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        self._authorize(actor, "liveops.campaign.kill", campaign_id)
        campaign = self.campaign(campaign_id, version)
        current = self.runtime(campaign_id, version)
        if current.state is LiveOpsCampaignState.KILLED:
            return current
        return self._transition(actor=actor, campaign=campaign, state=LiveOpsCampaignState.KILLED, action="campaign_killed")

    def active_rotation(self, *, campaign_id: str, version: int, instant_utc_ms: int | None = None) -> LiveOpsRotation | None:
        campaign = self.campaign(campaign_id, version)
        instant = _server_now_ms(self.clock_ms) if instant_utc_ms is None else _timestamp(instant_utc_ms, field="instant_utc_ms")
        for rotation in campaign.rotations:
            if rotation.start_at_utc_ms <= instant < rotation.end_at_utc_ms:
                return rotation
        return None

    def evaluate_audience(
        self,
        actor: AuthorityActorContext,
        *,
        campaign_id: str,
        version: int,
        remote_config: InMemoryRemoteConfigService,
        context: EvaluationContext,
    ) -> LiveOpsAudienceResult:
        campaign_id = _stable_id(campaign_id, field="campaign_id")
        self._authorize(actor, "liveops.campaign.audience.evaluate", campaign_id)
        campaign = self.campaign(campaign_id, version)
        if not isinstance(remote_config, InMemoryRemoteConfigService):
            raise LiveOpsPolicyError("invalid_remote_config_service")
        if not isinstance(context, EvaluationContext):
            raise LiveOpsPolicyError("invalid_evaluation_context")
        snapshot = remote_config.active_snapshot(campaign.environment)
        if snapshot.snapshot_id != campaign.config_snapshot.snapshot_id or snapshot.digest() != campaign.config_snapshot.digest:
            raise LiveOpsStateError("audience_config_snapshot_mismatch")
        if campaign.audience is None:
            return LiveOpsAudienceResult(
                campaign_id=campaign.campaign_id,
                flag_id=None,
                eligible=True,
                context_digest=context.digest(),
                evaluation_digest=None,
                variant=None,
            )
        result = remote_config.evaluate(
            actor,
            environment=campaign.environment,
            flag_id=campaign.audience.flag_id,
            context=context,
        )
        return LiveOpsAudienceResult(
            campaign_id=campaign.campaign_id,
            flag_id=campaign.audience.flag_id,
            eligible=result.variant in campaign.audience.allowed_variants,
            context_digest=result.context_digest,
            evaluation_digest=result.evaluation_digest,
            variant=result.variant,
        )

    def _append_audit(
        self,
        *,
        actor: AuthorityActorContext,
        action: str,
        campaign: LiveOpsCampaignDefinition,
        state: LiveOpsCampaignState,
        activation_id: str | None = None,
        safe_change_digest: str | None = None,
    ) -> LiveOpsAuditRecord:
        if len(self._audit) >= self.max_audit_records:
            raise LiveOpsCapacityError("audit_capacity")
        self._sequence += 1
        record = LiveOpsAuditRecord(
            sequence=self._sequence,
            action=_stable_id(action, field="audit_action"),
            actor_account_id=actor.account_id,
            campaign_id=campaign.campaign_id,
            campaign_version=campaign.version,
            state=state,
            recorded_at_ms=_server_now_ms(self.clock_ms),
            activation_id=activation_id,
            safe_change_digest=safe_change_digest,
        )
        self._audit.append(record)
        return record

    def _append_trace(self, payload: dict[str, Any]) -> None:
        if len(self._trace) >= self.max_trace_records:
            raise LiveOpsCapacityError("trace_capacity")
        self._trace.append(dict(payload))

    def audit_records(self) -> tuple[LiveOpsAuditRecord, ...]:
        with self._lock:
            return tuple(self._audit)

    def trace(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            return tuple(dict(item) for item in self._trace)

    def state_snapshot(self) -> LiveOpsStateSnapshot:
        with self._lock:
            dependency_payload = {
                "config": sorted((env.value, identity, revision, digest) for (env, identity, revision), digest in self._config_dependencies.items()),
                "content": sorted((env.value, identity, revision, digest) for (env, identity, revision), digest in self._content_dependencies.items()),
                "catalog": sorted((billing_env.value, identity, version, entitlement, digest) for (billing_env, identity, version), (entitlement, digest) in self._catalog_dependencies.items()),
                "events": sorted((env.value, identity, version, event_type, digest) for (env, identity, version), (event_type, digest) in self._event_dependencies.items()),
            }
            return LiveOpsStateSnapshot(
                season_digests=tuple(sorted(item.digest() for item in self._seasons.values())),
                campaign_digests=tuple(sorted(item.digest() for item in self._campaigns.values())),
                activation_digests=tuple(sorted(item.digest() for item in self._activations.values())),
                runtime_digests=tuple(sorted(item.digest() for item in self._runtime.values())),
                dependency_digest=canonical_sha256(dependency_payload),
                audit_digest=canonical_sha256([item.canonical() for item in self._audit]),
                trace_digest=canonical_sha256(list(self._trace)),
            )
