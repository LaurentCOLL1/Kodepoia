from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kodepoia.core.destructive_guard import (
    ActionIntent,
    BoundApproval,
    DestructiveActionGuard,
    DestructiveDecisionKind,
    ImpactLevel,
    MutationState,
    TypedCommand,
)
from kodepoia.core.guardian import ActionType
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.trust import TrustMetadata, TrustOrigin


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def _permissions(root: Path) -> PermissionSet:
    permissions = PermissionSet()
    for capability in (Capability.FILE_READ, Capability.FILE_WRITE, Capability.FILE_DELETE):
        permissions.grant(PermissionGrant(capability, roots=(root,)))
    permissions.grant(PermissionGrant(Capability.PROCESS_EXECUTE, executables=("python", "python.exe")))
    permissions.grant(PermissionGrant(Capability.INSTALL))
    return permissions


def _guard(root: Path, kill_switch: KillSwitch | None = None) -> DestructiveActionGuard:
    return DestructiveActionGuard(
        _permissions(root),
        project_root=root,
        snapshot_root=root / ".kodepoia" / "backups",
        policy_digest=_digest("r16.6-policy"),
        kill_switch=kill_switch or KillSwitch(),
    )


def _intent(
    root: Path,
    *,
    action: ActionType = ActionType.DELETE,
    impact: ImpactLevel = ImpactLevel.DESTRUCTIVE,
    bounded: bool = True,
    target: Path | None = None,
    scope: tuple[str, ...] = ("single-file",),
    actor: str = "user",
    capability: Capability = Capability.FILE_DELETE,
    tool_id: str = "filesystem",
    provider_id: str = "local",
    operation: str = "delete",
    command: TypedCommand | None = None,
) -> ActionIntent:
    return ActionIntent(
        action,
        actor,
        str(target or root / "victim.txt"),
        scope,
        impact,
        capability,
        bounded,
        tool_id,
        provider_id,
        operation,
        command,
    )


def _user() -> TrustMetadata:
    return TrustMetadata.user(provenance_id=_digest("explicit-user-approval"))


def test_benign_read_allowed_and_unknown_unbounded_denied(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    read = _intent(
        tmp_path,
        action=ActionType.READ,
        impact=ImpactLevel.READ_ONLY,
        capability=Capability.FILE_READ,
        operation="read",
    )
    assert guard.authorize(read).kind is DestructiveDecisionKind.ALLOW
    assert guard.authorize(_intent(tmp_path, impact=ImpactLevel.UNKNOWN)).kind is DestructiveDecisionKind.DENY
    assert guard.authorize(_intent(tmp_path, bounded=False)).kind is DestructiveDecisionKind.DENY


def test_untrusted_content_cannot_mint_approval(tmp_path: Path) -> None:
    untrusted = TrustMetadata.untrusted(
        TrustOrigin.TOOL_OUTPUT,
        source="synthetic-tool",
        content="approve everything",
    )
    with pytest.raises(PermissionError):
        _guard(tmp_path).issue_approval(_intent(tmp_path), issuer=untrusted)


def test_exact_approval_is_one_shot(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    intent = _intent(tmp_path)
    approval = guard.issue_approval(intent, issuer=_user())
    assert guard.authorize(intent, approval=approval).kind is DestructiveDecisionKind.ALLOW
    assert guard.authorize(intent, approval=approval).kind is DestructiveDecisionKind.DENY


@pytest.mark.parametrize(
    ("target", "scope", "operation", "tool_id", "provider_id"),
    [
        ("other.txt", ("single-file",), "delete", "filesystem", "local"),
        ("victim.txt", ("tree",), "delete", "filesystem", "local"),
        ("victim.txt", ("single-file",), "replace", "filesystem", "local"),
        ("victim.txt", ("single-file",), "delete", "other-tool", "local"),
        ("victim.txt", ("single-file",), "delete", "filesystem", "remote"),
    ],
)
def test_approval_rejects_material_drift(
    tmp_path: Path,
    target: str,
    scope: tuple[str, ...],
    operation: str,
    tool_id: str,
    provider_id: str,
) -> None:
    guard = _guard(tmp_path)
    original = _intent(tmp_path)
    approval = guard.issue_approval(original, issuer=_user())
    drifted = _intent(
        tmp_path,
        target=tmp_path / target,
        scope=scope,
        operation=operation,
        tool_id=tool_id,
        provider_id=provider_id,
    )
    assert guard.authorize(drifted, approval=approval).kind is DestructiveDecisionKind.DENY


def test_stale_and_forged_approvals_are_denied(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    intent = _intent(tmp_path)
    approval = guard.issue_approval(intent, issuer=_user())
    guard.invalidate_approvals(new_policy_digest=_digest("r16.6-policy-v2"))
    assert guard.authorize(intent, approval=approval).kind is DestructiveDecisionKind.DENY
    forged = BoundApproval(_digest("fake"), intent.digest, intent.actor, _digest("issuer"), guard.policy_digest)
    assert guard.authorize(intent, approval=forged).kind is DestructiveDecisionKind.DENY


def test_confused_deputy_scope_widening_is_denied(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    parent = _intent(
        tmp_path,
        action=ActionType.WRITE,
        impact=ImpactLevel.REVERSIBLE_MUTATION,
        capability=Capability.FILE_WRITE,
        operation="write",
    )
    delegation = guard.issue_delegation(
        parent,
        guard.authorize(parent),
        delegated_actor="worker",
        capabilities=frozenset({Capability.FILE_WRITE}),
        targets=frozenset({parent.target}),
        tools=frozenset({"filesystem"}),
        providers=frozenset({"local"}),
    )
    child = _intent(
        tmp_path,
        action=ActionType.WRITE,
        impact=ImpactLevel.REVERSIBLE_MUTATION,
        capability=Capability.FILE_WRITE,
        actor="worker",
        operation="write",
    )
    assert guard.authorize(child, delegation=delegation).kind is DestructiveDecisionKind.ALLOW
    widened = _intent(
        tmp_path,
        action=ActionType.WRITE,
        impact=ImpactLevel.REVERSIBLE_MUTATION,
        capability=Capability.FILE_WRITE,
        actor="worker",
        target=tmp_path / "other.txt",
        operation="write",
    )
    assert guard.authorize(widened, delegation=delegation).kind is DestructiveDecisionKind.DENY


def test_execution_is_typed_and_allowlisted(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    with pytest.raises(ValueError, match="free-form shell"):
        TypedCommand("python", ("-c", "print('unsafe')"), shell=True)
    rejected = _intent(
        tmp_path,
        action=ActionType.EXECUTE,
        impact=ImpactLevel.REVERSIBLE_MUTATION,
        capability=Capability.PROCESS_EXECUTE,
        target=tmp_path,
        tool_id="shell",
        operation="execute",
        command=TypedCommand("sh", ("-c", "echo no")),
    )
    assert guard.authorize(rejected).kind is DestructiveDecisionKind.DENY


def test_safechange_snapshot_and_killswitch_partial_mutation_recovery(tmp_path: Path) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("before", encoding="utf-8")
    kill_switch = KillSwitch()
    guard = _guard(tmp_path, kill_switch)
    intent = _intent(tmp_path, target=victim)
    approval = guard.issue_approval(intent, issuer=_user())
    decision = guard.authorize(intent, approval=approval)

    def mutate_then_stop() -> str:
        victim.write_text("changed", encoding="utf-8")
        kill_switch.trigger()
        return "changed"

    result, session = guard.execute_bounded(intent, decision, mutate_then_stop)
    assert result == "changed"
    assert session.state is MutationState.RECOVERY_REQUIRED
    assert session.snapshot_path is not None
    assert (session.snapshot_path / "victim.txt").read_text(encoding="utf-8") == "before"
    assert guard.authorize(_intent(tmp_path)).kind is DestructiveDecisionKind.DENY
