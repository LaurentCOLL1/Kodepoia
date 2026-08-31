from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any

from kodepoia.core.permissions import Capability, PermissionSet
from kodepoia.core.trust import AuthorityEffect, TrustBoundary, TrustMetadata


class RiskLevel(IntEnum):
    LOW = 10
    MEDIUM = 20
    HIGH = 30
    CRITICAL = 40


class DecisionKind(StrEnum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"


class ActionType(StrEnum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    INSTALL = "install"
    NETWORK = "network"
    SECRET_READ = "secret_read"
    SECRET_WRITE = "secret_write"


@dataclass(frozen=True, slots=True)
class ActionRequest:
    action: ActionType
    actor: str
    target: str = ""
    project_root: Path | None = None
    downloaded: bool = False
    destructive_count: int = 0
    sandboxed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GuardianDecision:
    kind: DecisionKind
    risk: RiskLevel
    reason: str
    required_capability: Capability | None = None
    snapshot_required: bool = False


class GuardianPolicy:
    """Deterministic baseline policy. LLM output can never override it."""

    def evaluate(self, request: ActionRequest) -> GuardianDecision:
        if request.action is ActionType.SECRET_READ:
            return GuardianDecision(
                DecisionKind.DENY,
                RiskLevel.CRITICAL,
                "Raw secret reads are forbidden; use delegated secret operations.",
                Capability.SECRET_READ,
            )
        if request.action is ActionType.READ:
            return GuardianDecision(
                DecisionKind.ALLOW,
                RiskLevel.LOW,
                "Read-only project access.",
                Capability.FILE_READ,
            )
        if request.action is ActionType.WRITE:
            return GuardianDecision(
                DecisionKind.ALLOW,
                RiskLevel.MEDIUM,
                "Project write allowed with audit and safe-change snapshot policy.",
                Capability.FILE_WRITE,
                snapshot_required=True,
            )
        if request.action is ActionType.DELETE:
            if request.destructive_count >= 10:
                return GuardianDecision(
                    DecisionKind.CONFIRM,
                    RiskLevel.CRITICAL,
                    "Bulk deletion requires explicit confirmation and snapshot.",
                    Capability.FILE_DELETE,
                    snapshot_required=True,
                )
            return GuardianDecision(
                DecisionKind.CONFIRM,
                RiskLevel.HIGH,
                "Deletion requires explicit confirmation.",
                Capability.FILE_DELETE,
                snapshot_required=True,
            )
        if request.action is ActionType.EXECUTE:
            if request.downloaded and not request.sandboxed:
                return GuardianDecision(
                    DecisionKind.DENY,
                    RiskLevel.CRITICAL,
                    "Downloaded code cannot execute outside KodeSandbox.",
                    Capability.PROCESS_EXECUTE,
                )
            risk = RiskLevel.HIGH if request.downloaded else RiskLevel.MEDIUM
            kind = DecisionKind.CONFIRM if request.downloaded else DecisionKind.ALLOW
            return GuardianDecision(
                kind,
                risk,
                "Process execution is constrained by KodeSandbox.",
                Capability.PROCESS_EXECUTE,
            )
        if request.action is ActionType.INSTALL:
            return GuardianDecision(
                DecisionKind.CONFIRM,
                RiskLevel.HIGH,
                "Package/tool installation requires explicit approval.",
                Capability.INSTALL,
                snapshot_required=True,
            )
        if request.action is ActionType.NETWORK:
            return GuardianDecision(
                DecisionKind.ALLOW,
                RiskLevel.MEDIUM,
                "Network access is permission-scoped.",
                Capability.NETWORK,
            )
        if request.action is ActionType.SECRET_WRITE:
            return GuardianDecision(
                DecisionKind.CONFIRM,
                RiskLevel.HIGH,
                "Storing a secret requires explicit approval.",
                Capability.SECRET_WRITE,
            )
        return GuardianDecision(DecisionKind.DENY, RiskLevel.CRITICAL, "Unknown action type.")


_CONTENT_EFFECTS = {
    ActionType.READ: AuthorityEffect.INSPECT_DATA,
    ActionType.WRITE: AuthorityEffect.FILESYSTEM_SCOPE_WIDEN,
    ActionType.DELETE: AuthorityEffect.FILESYSTEM_SCOPE_WIDEN,
    ActionType.EXECUTE: AuthorityEffect.PROCESS_EXECUTION,
    ActionType.INSTALL: AuthorityEffect.PRIVILEGED_TOOL_TRIGGER,
    ActionType.NETWORK: AuthorityEffect.NETWORK_SCOPE_WIDEN,
    ActionType.SECRET_READ: AuthorityEffect.SECRET_ACCESS,
    ActionType.SECRET_WRITE: AuthorityEffect.SECRET_ACCESS,
}


class KodeGuardian:
    def __init__(self, permissions: PermissionSet, policy: GuardianPolicy | None = None) -> None:
        self.permissions = permissions
        self.policy = policy or GuardianPolicy()
        self.trust_boundary = TrustBoundary()

    def _content_authority_decision(self, request: ActionRequest) -> GuardianDecision | None:
        if request.metadata.get("content_driven") is not True:
            return None
        raw_trust = request.metadata.get("trust")
        try:
            trust = TrustMetadata.from_mapping(
                raw_trust if isinstance(raw_trust, Mapping) else None
            )
        except (TypeError, ValueError) as exc:
            return GuardianDecision(
                DecisionKind.DENY,
                RiskLevel.CRITICAL,
                f"Content-driven authority denied: {exc}",
            )
        effects = [_CONTENT_EFFECTS[request.action]]
        if request.metadata.get("suppress_confirmation") is True:
            effects.append(AuthorityEffect.SUPPRESS_CONFIRMATION)
        if request.metadata.get("grant_permission") is True:
            effects.append(AuthorityEffect.PERMISSION_GRANT)
        if request.metadata.get("rewrite_authority") is True:
            effects.append(AuthorityEffect.ROADMAP_AUTHORITY)
        for effect in effects:
            trust_decision = self.trust_boundary.evaluate(trust, effect)
            if not trust_decision.allowed:
                return GuardianDecision(
                    DecisionKind.DENY,
                    RiskLevel.CRITICAL,
                    f"Content-driven authority denied ({effect.value}): {trust_decision.reason}",
                )
        return None

    def authorize(self, request: ActionRequest, *, confirmed: bool = False) -> GuardianDecision:
        trust_denial = self._content_authority_decision(request)
        if trust_denial is not None:
            return trust_denial
        decision = self.policy.evaluate(request)
        if decision.required_capability is not None and decision.kind is not DecisionKind.DENY:
            path = (
                Path(request.target)
                if request.target
                and decision.required_capability
                in {Capability.FILE_READ, Capability.FILE_WRITE, Capability.FILE_DELETE}
                else None
            )
            executable = (
                request.metadata.get("executable")
                if decision.required_capability is Capability.PROCESS_EXECUTE
                else None
            )
            self.permissions.require(
                decision.required_capability,
                path=path,
                executable=executable,
            )
        if decision.kind is DecisionKind.CONFIRM and confirmed:
            return GuardianDecision(
                DecisionKind.ALLOW,
                decision.risk,
                f"Confirmed: {decision.reason}",
                decision.required_capability,
                decision.snapshot_required,
            )
        return decision
