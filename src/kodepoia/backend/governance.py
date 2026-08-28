from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.core.audit import AuditLog
from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.core.permissions import Capability, PermissionSet
from kodepoia.exceptions import PermissionDenied

from .boundary import BackendBoundaryError
from .contracts import canonical_sha256


class BackendOperationKind(StrEnum):
    PROBE = "probe"
    CONNECT = "connect"
    DEPLOY = "deploy"
    MIGRATE = "migrate"
    MUTATE = "mutate"
    PROMOTE = "promote"
    ROLLBACK = "rollback"


class BackendOperationRisk(StrEnum):
    PASSIVE = "passive"
    NETWORK_ACTIVE = "network_active"
    MUTATING = "mutating"
    DESTRUCTIVE = "destructive"


_OPERATION_RISK: dict[BackendOperationKind, BackendOperationRisk] = {
    BackendOperationKind.PROBE: BackendOperationRisk.NETWORK_ACTIVE,
    BackendOperationKind.CONNECT: BackendOperationRisk.NETWORK_ACTIVE,
    BackendOperationKind.DEPLOY: BackendOperationRisk.MUTATING,
    BackendOperationKind.MIGRATE: BackendOperationRisk.MUTATING,
    BackendOperationKind.MUTATE: BackendOperationRisk.MUTATING,
    BackendOperationKind.PROMOTE: BackendOperationRisk.MUTATING,
    BackendOperationKind.ROLLBACK: BackendOperationRisk.DESTRUCTIVE,
}


def _stable_id(value: str, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > 128
        or not value[0].isalnum()
        or any(not (char.isalnum() or char in "._-") for char in value)
    ):
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _sha256(value: str, *, field: str, optional: bool = False) -> str:
    if optional and value == "":
        return value
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ValueError(f"{field} must be lowercase SHA-256")
    return value


@dataclass(frozen=True, slots=True)
class BackendOperationIntent:
    operation_id: str
    operation_kind: BackendOperationKind
    environment_id: str
    service_id: str
    endpoint_id: str
    request_digest: str
    expected_environment_digest: str

    def __post_init__(self) -> None:
        _stable_id(self.operation_id, field="operation_id")
        _stable_id(self.environment_id, field="environment_id")
        _stable_id(self.service_id, field="service_id")
        _stable_id(self.endpoint_id, field="endpoint_id")
        _sha256(self.request_digest, field="request_digest")
        _sha256(self.expected_environment_digest, field="expected_environment_digest")

    @property
    def risk(self) -> BackendOperationRisk:
        return _OPERATION_RISK[self.operation_kind]

    @property
    def required_capability(self) -> Capability:
        return Capability.NETWORK

    def canonical(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation_kind": self.operation_kind.value,
            "risk": self.risk.value,
            "environment_id": self.environment_id,
            "service_id": self.service_id,
            "endpoint_id": self.endpoint_id,
            "request_digest": self.request_digest,
            "expected_environment_digest": self.expected_environment_digest,
            "required_capability": self.required_capability.value,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class BackendProviderRequest:
    request_id: str
    provider_id: str
    operation_intent_digest: str
    endpoint_digest: str
    payload_digest: str = ""
    idempotency_key_digest: str = ""

    def __post_init__(self) -> None:
        _stable_id(self.request_id, field="request_id")
        _stable_id(self.provider_id, field="provider_id")
        _sha256(self.operation_intent_digest, field="operation_intent_digest")
        _sha256(self.endpoint_digest, field="endpoint_digest")
        _sha256(self.payload_digest, field="payload_digest", optional=True)
        _sha256(self.idempotency_key_digest, field="idempotency_key_digest", optional=True)

    def canonical(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "operation_intent_digest": self.operation_intent_digest,
            "endpoint_digest": self.endpoint_digest,
            "payload_digest": self.payload_digest,
            "idempotency_key_digest": self.idempotency_key_digest,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class BackendGovernanceAuthorization:
    authorization_id: str
    operation_intent_digest: str
    permission_capability: str
    audit_event_hash: str
    outcome: str = "allowed"

    def __post_init__(self) -> None:
        _stable_id(self.authorization_id, field="authorization_id")
        _sha256(self.operation_intent_digest, field="operation_intent_digest")
        _stable_id(self.permission_capability, field="permission_capability")
        _sha256(self.audit_event_hash, field="audit_event_hash")
        if self.outcome != "allowed":
            raise ValueError("governance authorization outcome must be allowed")

    def canonical(self) -> dict[str, Any]:
        return {
            "authorization_id": self.authorization_id,
            "operation_intent_digest": self.operation_intent_digest,
            "permission_capability": self.permission_capability,
            "audit_event_hash": self.audit_event_hash,
            "outcome": self.outcome,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


class BackendGovernanceBoundary:
    """R14 adapter over accepted R1 PermissionSet, AuditLog and KillSwitch controls."""

    def __init__(
        self,
        *,
        permissions: PermissionSet,
        audit_log: AuditLog,
        actor: str = "kodepoia.backend",
        kill_switch: KillSwitch | None = None,
    ) -> None:
        self._permissions = permissions
        self._audit_log = audit_log
        self._actor = _stable_id(actor, field="actor")
        self._kill_switch = kill_switch or GLOBAL_KILL_SWITCH

    def authorize(self, intent: BackendOperationIntent) -> BackendGovernanceAuthorization:
        details = {
            "operation_id": intent.operation_id,
            "operation_intent_digest": intent.digest(),
            "environment_id": intent.environment_id,
            "service_id": intent.service_id,
            "endpoint_id": intent.endpoint_id,
            "risk": intent.risk.value,
            "required_capability": intent.required_capability.value,
        }

        if self._kill_switch.triggered:
            self._audit_log.append(
                category="backend",
                action=intent.operation_kind.value,
                actor=self._actor,
                outcome="blocked_kill_switch",
                details=details,
            )
            raise BackendBoundaryError("global kill switch is active")

        try:
            self._permissions.require(intent.required_capability)
        except PermissionDenied as exc:
            self._audit_log.append(
                category="backend",
                action=intent.operation_kind.value,
                actor=self._actor,
                outcome="denied_permission",
                details=details,
            )
            raise BackendBoundaryError("required backend capability is not granted") from exc

        event = self._audit_log.append(
            category="backend",
            action=intent.operation_kind.value,
            actor=self._actor,
            outcome="allowed",
            details=details,
        )
        seed = {
            "operation_intent_digest": intent.digest(),
            "permission_capability": intent.required_capability.value,
            "audit_event_hash": event.event_hash,
            "outcome": "allowed",
        }
        return BackendGovernanceAuthorization(
            authorization_id=f"governance.auth.{canonical_sha256(seed)[:24]}",
            operation_intent_digest=intent.digest(),
            permission_capability=intent.required_capability.value,
            audit_event_hash=event.event_hash,
        )
