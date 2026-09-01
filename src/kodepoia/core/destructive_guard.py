from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import TypeVar

from kodepoia.core.guardian import ActionType
from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.core.permissions import Capability, PermissionSet
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.core.trust import ContentAuthority, TrustMetadata, TrustOrigin
from kodepoia.exceptions import PermissionDenied

T = TypeVar("T")


class ImpactLevel(IntEnum):
    READ_ONLY = 0
    REVERSIBLE_MUTATION = 10
    HIGH_IMPACT = 20
    DESTRUCTIVE = 30
    UNKNOWN = 99


class DestructiveDecisionKind(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class MutationState(StrEnum):
    SNAPSHOTTED = "snapshotted"
    POSSIBLE_MUTATION = "possible_mutation"
    COMPLETE = "complete"
    RECOVERY_REQUIRED = "recovery_required"


@dataclass(frozen=True, slots=True)
class TypedCommand:
    executable: str
    args: tuple[str, ...] = ()
    shell: bool = False

    def __post_init__(self) -> None:
        executable = self.executable.strip()
        if not executable:
            raise ValueError("typed command executable is required")
        if self.shell:
            raise ValueError("free-form shell execution is forbidden")
        if any("\x00" in part for part in (executable, *self.args)):
            raise ValueError("NUL bytes are forbidden in typed commands")
        object.__setattr__(self, "executable", executable)


@dataclass(frozen=True, slots=True)
class ActionIntent:
    action: ActionType
    actor: str
    target: str
    scope: tuple[str, ...]
    impact: ImpactLevel
    capability: Capability
    bounded: bool
    tool_id: str = ""
    provider_id: str = ""
    operation: str = ""
    command: TypedCommand | None = None

    def __post_init__(self) -> None:
        actor, target = self.actor.strip(), self.target.strip()
        scope = tuple(sorted({item.strip() for item in self.scope if item.strip()}))
        if not actor or not target or not scope:
            raise ValueError("actor, target, and explicit scope are required")
        object.__setattr__(self, "actor", actor)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "operation", self.operation.strip() or self.action.value)

    @property
    def digest(self) -> str:
        command = None
        if self.command is not None:
            command = {
                "executable": self.command.executable,
                "args": list(self.command.args),
                "shell": self.command.shell,
            }
        payload = {
            "action": self.action.value,
            "actor": self.actor,
            "target": self.target,
            "scope": list(self.scope),
            "impact": int(self.impact),
            "capability": self.capability.value,
            "bounded": self.bounded,
            "tool_id": self.tool_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "command": command,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class BoundApproval:
    approval_id: str
    intent_digest: str
    actor: str
    issuer_provenance: str
    policy_digest: str


@dataclass(frozen=True, slots=True)
class DelegationContext:
    delegation_id: str
    parent_intent_digest: str
    delegated_actor: str
    capabilities: frozenset[Capability]
    targets: frozenset[str]
    tools: frozenset[str]
    providers: frozenset[str]


@dataclass(frozen=True, slots=True)
class DestructiveDecision:
    kind: DestructiveDecisionKind
    reason: str
    intent_digest: str
    snapshot_required: bool = False


@dataclass(slots=True)
class MutationSession:
    intent_digest: str
    target: Path
    snapshot_path: Path | None
    state: MutationState


class DestructiveActionGuard:
    """Exact, one-shot authority boundary for dangerous/high-impact side effects."""

    def __init__(
        self,
        permissions: PermissionSet,
        *,
        project_root: Path,
        snapshot_root: Path,
        policy_digest: str,
        kill_switch: KillSwitch = GLOBAL_KILL_SWITCH,
    ) -> None:
        self.permissions = permissions
        self.project_root = project_root.resolve(strict=False)
        self.safe_change = SafeChangeManager(self.project_root, snapshot_root)
        self.policy_digest = self._digest(policy_digest, "policy_digest")
        self.kill_switch = kill_switch
        self._issued: dict[str, BoundApproval] = {}
        self._consumed: set[str] = set()
        self._delegations: dict[str, DelegationContext] = {}
        self._sequence = 0

    @staticmethod
    def _digest(value: str, label: str) -> str:
        value = value.strip().lower()
        if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
            raise ValueError(f"{label} must be a lowercase SHA-256 digest")
        return value

    @staticmethod
    def _can_approve(metadata: TrustMetadata) -> bool:
        return (
            metadata.origin is TrustOrigin.SYSTEM
            and metadata.authority is ContentAuthority.POLICY
        ) or (
            metadata.origin is TrustOrigin.USER
            and metadata.authority is ContentAuthority.USER_INTENT
        )

    @staticmethod
    def _needs_approval(intent: ActionIntent) -> bool:
        return intent.impact >= ImpactLevel.HIGH_IMPACT or intent.action in {
            ActionType.DELETE,
            ActionType.INSTALL,
            ActionType.SECRET_WRITE,
        }

    @staticmethod
    def _deny(intent: ActionIntent, reason: str) -> DestructiveDecision:
        return DestructiveDecision(DestructiveDecisionKind.DENY, reason, intent.digest)

    def issue_approval(self, intent: ActionIntent, *, issuer: TrustMetadata) -> BoundApproval:
        if not self._can_approve(issuer):
            raise PermissionError("untrusted/data-only content cannot grant destructive authority")
        if intent.impact is ImpactLevel.UNKNOWN or not intent.bounded:
            raise PermissionError("unknown or unbounded impact cannot be approved")
        self._sequence += 1
        material = "\x1f".join(
            (self.policy_digest, intent.digest, intent.actor, issuer.provenance_id, str(self._sequence))
        )
        approval = BoundApproval(
            hashlib.sha256(material.encode()).hexdigest(),
            intent.digest,
            intent.actor,
            issuer.provenance_id,
            self.policy_digest,
        )
        self._issued[approval.approval_id] = approval
        return approval

    def invalidate_approvals(self, *, new_policy_digest: str | None = None) -> None:
        if new_policy_digest is not None:
            self.policy_digest = self._digest(new_policy_digest, "policy_digest")
        self._issued.clear()
        self._consumed.clear()
        self._delegations.clear()

    def issue_delegation(
        self,
        parent: ActionIntent,
        decision: DestructiveDecision,
        *,
        delegated_actor: str,
        capabilities: frozenset[Capability],
        targets: frozenset[str],
        tools: frozenset[str] = frozenset(),
        providers: frozenset[str] = frozenset(),
    ) -> DelegationContext:
        if decision.kind is not DestructiveDecisionKind.ALLOW or decision.intent_digest != parent.digest:
            raise PermissionError("delegation requires exact-parent ALLOW")
        actor = delegated_actor.strip()
        if not actor or not capabilities or not targets:
            raise ValueError("delegation actor, capabilities, and targets must be explicit")
        payload = json.dumps(
            {
                "parent": parent.digest,
                "actor": actor,
                "capabilities": sorted(item.value for item in capabilities),
                "targets": sorted(targets),
                "tools": sorted(tools),
                "providers": sorted(providers),
                "sequence": self._sequence,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        context = DelegationContext(
            hashlib.sha256(payload.encode()).hexdigest(),
            parent.digest,
            actor,
            capabilities,
            targets,
            tools,
            providers,
        )
        self._delegations[context.delegation_id] = context
        return context

    def _delegation_error(
        self, intent: ActionIntent, delegation: DelegationContext | None
    ) -> str | None:
        if delegation is None:
            return None
        if self._delegations.get(delegation.delegation_id) != delegation:
            return "unknown/forged delegation denied"
        if intent.actor != delegation.delegated_actor:
            return "delegated actor substitution denied"
        if intent.capability not in delegation.capabilities:
            return "delegated capability escalation denied"
        if intent.target not in delegation.targets:
            return "delegated target substitution denied"
        if intent.tool_id and intent.tool_id not in delegation.tools:
            return "delegated tool substitution denied"
        if intent.provider_id and intent.provider_id not in delegation.providers:
            return "delegated provider substitution denied"
        return None

    def authorize(
        self,
        intent: ActionIntent,
        *,
        approval: BoundApproval | None = None,
        delegation: DelegationContext | None = None,
    ) -> DestructiveDecision:
        if self.kill_switch.triggered:
            return self._deny(intent, "KillSwitch is active")
        if intent.impact is ImpactLevel.UNKNOWN:
            return self._deny(intent, "unknown impact fails closed")
        if intent.impact is not ImpactLevel.READ_ONLY and not intent.bounded:
            return self._deny(intent, "unbounded mutation impact fails closed")
        if error := self._delegation_error(intent, delegation):
            return self._deny(intent, error)

        path = None
        if intent.capability in {Capability.FILE_READ, Capability.FILE_WRITE, Capability.FILE_DELETE}:
            path = Path(intent.target)
        executable = intent.command.executable if intent.command else None
        if intent.command and intent.capability is not Capability.PROCESS_EXECUTE:
            return self._deny(intent, "typed command requires process.execute")
        try:
            self.permissions.require(intent.capability, path=path, executable=executable)
        except (PermissionDenied, ValueError) as exc:
            return self._deny(intent, f"least-privilege check failed: {exc}")

        snapshot = intent.impact >= ImpactLevel.REVERSIBLE_MUTATION
        if not self._needs_approval(intent):
            return DestructiveDecision(
                DestructiveDecisionKind.ALLOW,
                "bounded least-privilege action allowed",
                intent.digest,
                snapshot,
            )
        if approval is None:
            return self._deny(intent, "exact bound approval is required")
        issued = self._issued.get(approval.approval_id)
        if issued != approval or approval.approval_id in self._consumed:
            return self._deny(intent, "approval is unknown, stale, forged, or already consumed")
        if approval.policy_digest != self.policy_digest:
            return self._deny(intent, "approval policy drift denied")
        if approval.intent_digest != intent.digest or approval.actor != intent.actor:
            return self._deny(intent, "approval does not match exact material intent")
        self._consumed.add(approval.approval_id)
        return DestructiveDecision(
            DestructiveDecisionKind.ALLOW,
            "exact one-shot bound approval accepted",
            intent.digest,
            True,
        )

    def begin_mutation(self, intent: ActionIntent, decision: DestructiveDecision) -> MutationSession:
        if decision.kind is not DestructiveDecisionKind.ALLOW or decision.intent_digest != intent.digest:
            raise PermissionError("mutation requires exact-intent ALLOW")
        if intent.impact is ImpactLevel.READ_ONLY:
            raise ValueError("read-only intent cannot mutate")
        target = self.safe_change.ensure_inside_project(Path(intent.target))
        snapshot = self.safe_change.snapshot([target]) if decision.snapshot_required else None
        return MutationSession(intent.digest, target, snapshot, MutationState.SNAPSHOTTED)

    def execute_bounded(
        self,
        intent: ActionIntent,
        decision: DestructiveDecision,
        mutate: Callable[[], T],
    ) -> tuple[T | None, MutationSession]:
        session = self.begin_mutation(intent, decision)
        if self.kill_switch.triggered:
            session.state = MutationState.RECOVERY_REQUIRED
            return None, session
        session.state = MutationState.POSSIBLE_MUTATION
        try:
            result = mutate()
        except Exception:
            session.state = MutationState.RECOVERY_REQUIRED
            raise
        session.state = (
            MutationState.RECOVERY_REQUIRED if self.kill_switch.triggered else MutationState.COMPLETE
        )
        return result, session
