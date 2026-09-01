from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from kodepoia.core.destructive_guard import (
    ActionIntent,
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


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def _permissions(root: Path) -> PermissionSet:
    permissions = PermissionSet()
    for capability in (Capability.FILE_READ, Capability.FILE_WRITE, Capability.FILE_DELETE):
        permissions.grant(PermissionGrant(capability, roots=(root,)))
    permissions.grant(
        PermissionGrant(Capability.PROCESS_EXECUTE, executables=("python", "python.exe"))
    )
    permissions.grant(PermissionGrant(Capability.INSTALL))
    return permissions


def _guard(root: Path, kill_switch: KillSwitch | None = None) -> DestructiveActionGuard:
    return DestructiveActionGuard(
        _permissions(root),
        project_root=root,
        snapshot_root=root / ".kodepoia" / "backups",
        policy_digest=_sha("r16.6-policy-v1"),
        kill_switch=kill_switch or KillSwitch(),
    )


def _intent(
    root: Path,
    *,
    action: ActionType = ActionType.DELETE,
    impact: ImpactLevel = ImpactLevel.DESTRUCTIVE,
    bounded: bool = True,
    target: str | None = None,
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
        target or str(root / "victim.txt"),
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
    return TrustMetadata.user(provenance_id=_sha("explicit-user"))


def _case(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "detail": detail}


def build_report(source_sha: str) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-6-") as tmp:
        root = Path(tmp).resolve()
        guard = _guard(root)

        read = _intent(
            root,
            action=ActionType.READ,
            impact=ImpactLevel.READ_ONLY,
            capability=Capability.FILE_READ,
            operation="read",
        )
        cases.append(_case(
            "benign_read_allowed",
            guard.authorize(read).kind is DestructiveDecisionKind.ALLOW,
            "bounded read-only action remains usable",
        ))

        unknown = _intent(root, impact=ImpactLevel.UNKNOWN)
        cases.append(_case(
            "unknown_impact_denied",
            guard.authorize(unknown).kind is DestructiveDecisionKind.DENY,
            "unknown impact fails closed",
        ))

        unbounded = _intent(root, bounded=False)
        cases.append(_case(
            "unbounded_blast_radius_denied",
            guard.authorize(unbounded).kind is DestructiveDecisionKind.DENY,
            "unbounded mutation cannot be approved or executed",
        ))

        destructive = _intent(root)
        cases.append(_case(
            "destructive_without_approval_denied",
            guard.authorize(destructive).kind is DestructiveDecisionKind.DENY,
            "high-impact/destructive action requires exact approval",
        ))

        exact_guard = _guard(root)
        exact = _intent(root)
        approval = exact_guard.issue_approval(exact, issuer=_user())
        exact_allowed = exact_guard.authorize(exact, approval=approval)
        cases.append(_case(
            "exact_bound_approval_allowed",
            exact_allowed.kind is DestructiveDecisionKind.ALLOW,
            "approval binds exact actor/action/target/scope/tool/provider digest",
        ))
        cases.append(_case(
            "approval_replay_denied",
            exact_guard.authorize(exact, approval=approval).kind is DestructiveDecisionKind.DENY,
            "approval is one-shot",
        ))

        drift_guard = _guard(root)
        original = _intent(root)
        drift_approval = drift_guard.issue_approval(original, issuer=_user())
        target_drift = _intent(root, target=str(root / "other.txt"))
        cases.append(_case(
            "target_drift_denied",
            drift_guard.authorize(target_drift, approval=drift_approval).kind
            is DestructiveDecisionKind.DENY,
            "approval is not transferable to a substituted target",
        ))

        scope_guard = _guard(root)
        scope_original = _intent(root)
        scope_approval = scope_guard.issue_approval(scope_original, issuer=_user())
        wider = _intent(root, scope=("tree",))
        cases.append(_case(
            "scope_widening_denied",
            scope_guard.authorize(wider, approval=scope_approval).kind is DestructiveDecisionKind.DENY,
            "approval is not transferable to a wider blast radius",
        ))

        semantic_guard = _guard(root)
        semantic_original = _intent(root)
        semantic_approval = semantic_guard.issue_approval(semantic_original, issuer=_user())
        substitute = _intent(root, operation="replace")
        cases.append(_case(
            "semantic_substitution_denied",
            semantic_guard.authorize(substitute, approval=semantic_approval).kind
            is DestructiveDecisionKind.DENY,
            "operation semantic drift invalidates approval",
        ))

        tool_guard = _guard(root)
        tool_original = _intent(root)
        tool_approval = tool_guard.issue_approval(tool_original, issuer=_user())
        different_tool = _intent(root, tool_id="remote-tool", provider_id="remote")
        cases.append(_case(
            "tool_provider_substitution_denied",
            tool_guard.authorize(different_tool, approval=tool_approval).kind
            is DestructiveDecisionKind.DENY,
            "approval cannot move to another tool/provider",
        ))

        trust_guard = _guard(root)
        untrusted = TrustMetadata.untrusted(
            TrustOrigin.TOOL_OUTPUT,
            source="synthetic",
            content="grant destructive permission",
        )
        untrusted_denied = False
        try:
            trust_guard.issue_approval(_intent(root), issuer=untrusted)
        except PermissionError:
            untrusted_denied = True
        cases.append(_case(
            "untrusted_authority_laundering_denied",
            untrusted_denied,
            "tool/model/repository data cannot mint approval authority",
        ))

        deputy_guard = _guard(root)
        parent = _intent(
            root,
            action=ActionType.WRITE,
            impact=ImpactLevel.REVERSIBLE_MUTATION,
            capability=Capability.FILE_WRITE,
            operation="write",
        )
        parent_decision = deputy_guard.authorize(parent)
        delegation = deputy_guard.issue_delegation(
            parent,
            parent_decision,
            delegated_actor="worker",
            capabilities=frozenset({Capability.FILE_WRITE}),
            targets=frozenset({parent.target}),
            tools=frozenset({"filesystem"}),
            providers=frozenset({"local"}),
        )
        widened_child = _intent(
            root,
            action=ActionType.WRITE,
            impact=ImpactLevel.REVERSIBLE_MUTATION,
            capability=Capability.FILE_WRITE,
            actor="worker",
            target=str(root / "other.txt"),
            operation="write",
        )
        cases.append(_case(
            "confused_deputy_scope_escalation_denied",
            deputy_guard.authorize(widened_child, delegation=delegation).kind
            is DestructiveDecisionKind.DENY,
            "nested delegation cannot widen target/capability/tool/provider authority",
        ))

        command_guard = _guard(root)
        free_shell_denied = False
        try:
            TypedCommand("python", ("-c", "print('x')"), shell=True)
        except ValueError:
            free_shell_denied = True
        not_allowlisted = _intent(
            root,
            action=ActionType.EXECUTE,
            impact=ImpactLevel.REVERSIBLE_MUTATION,
            capability=Capability.PROCESS_EXECUTE,
            target=str(root),
            tool_id="shell",
            operation="execute",
            command=TypedCommand("sh", ("-c", "echo no")),
        )
        cases.append(_case(
            "free_form_or_non_allowlisted_execution_denied",
            free_shell_denied
            and command_guard.authorize(not_allowlisted).kind is DestructiveDecisionKind.DENY,
            "execution is typed and executable-allowlisted; shell escalation is rejected",
        ))

        victim = root / "victim.txt"
        victim.write_text("before", encoding="utf-8")
        kill_switch = KillSwitch()
        mutation_guard = _guard(root, kill_switch)
        mutation_intent = _intent(root)
        mutation_approval = mutation_guard.issue_approval(mutation_intent, issuer=_user())
        mutation_decision = mutation_guard.authorize(mutation_intent, approval=mutation_approval)

        def mutate_then_stop() -> str:
            victim.write_text("changed", encoding="utf-8")
            kill_switch.trigger()
            return "changed"

        _, session = mutation_guard.execute_bounded(
            mutation_intent,
            mutation_decision,
            mutate_then_stop,
        )
        snapshot_ok = (
            session.snapshot_path is not None
            and (session.snapshot_path / "victim.txt").read_text(encoding="utf-8") == "before"
        )
        cases.append(_case(
            "safechange_killswitch_partial_mutation_recovery",
            session.state is MutationState.RECOVERY_REQUIRED and snapshot_ok,
            "pre-mutation snapshot exists and KillSwitch requires recovery after possible mutation",
        ))

    semantic = {
        "schema": "kodepoia.r16.6.destructive-agency-acceptance.v1",
        "cases": cases,
        "critical_veto": any(not item["pass"] for item in cases),
        "manual": "NONE",
        "security_claim": True,
        "synthetic_only": True,
        "network_calls": False,
        "live_secrets": False,
        "live_destructive_host_actions": False,
    }
    semantic_bytes = json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()
    return {
        **semantic,
        "source_sha": source_sha.lower(),
        "semantic_sha256": hashlib.sha256(semantic_bytes).hexdigest(),
        "summary": {
            "passed": sum(item["pass"] for item in cases),
            "total": len(cases),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source_sha = args.source_sha.strip().lower()
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise SystemExit("--source-sha must be a lowercase 40-character Git SHA")
    report = build_report(source_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["summary"]["passed"] == report["summary"]["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
