from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Iterable

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.exceptions import PermissionDenied, PolicyDenied
from kodepoia.kodecode.api import KodeCodeToolAPI
from kodepoia.kodecode.graph_api import GraphToolAPI


class ToolEffect(StrEnum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


@dataclass(frozen=True, slots=True)
class ToolPolicy:
    effect: ToolEffect
    action: ActionType
    target_arg: str | None = None
    snapshot_arg: str | None = None


@dataclass(frozen=True, slots=True)
class ToolExecutionResult:
    tool_name: str
    result: Any
    snapshot: str | None = None


_READ = ToolPolicy(ToolEffect.READ, ActionType.READ)
_EXECUTE = ToolPolicy(ToolEffect.EXECUTE, ActionType.EXECUTE)


DEFAULT_TOOL_POLICIES: dict[str, ToolPolicy] = {
    "kodecode_files_list": _READ,
    "kodecode_files_read": ToolPolicy(ToolEffect.READ, ActionType.READ, target_arg="path"),
    "kodecode_search": _READ,
    "kodecode_patch_replace_once": ToolPolicy(
        ToolEffect.WRITE,
        ActionType.WRITE,
        target_arg="path",
        snapshot_arg="path",
    ),
    "kodecode_git_worktree_list": _READ,
    "kodecode_git_worktree_add": _EXECUTE,
    "kodecode_git_worktree_remove": _EXECUTE,
    "kodecode_parser_capabilities": _READ,
    "kodecode_parser_parse": ToolPolicy(ToolEffect.READ, ActionType.READ, target_arg="path"),
    "kodecode_lsp_capabilities": _READ,
    "kodecode_lsp_start": _EXECUTE,
    "kodecode_lsp_stop": _EXECUTE,
    "kodecode_lsp_symbols": ToolPolicy(ToolEffect.READ, ActionType.READ, target_arg="path"),
    "kodecode_lsp_definition": ToolPolicy(ToolEffect.READ, ActionType.READ, target_arg="path"),
    "kodecode_lsp_references": ToolPolicy(ToolEffect.READ, ActionType.READ, target_arg="path"),
    "kodecode_lsp_diagnostics": ToolPolicy(ToolEffect.READ, ActionType.READ, target_arg="path"),
    "kodecode_dap_capabilities": _READ,
    "kodecode_dap_start": _EXECUTE,
    "kodecode_dap_configure": _EXECUTE,
    "kodecode_dap_configuration_done": _EXECUTE,
    "kodecode_dap_set_breakpoints": _EXECUTE,
    "kodecode_dap_threads": _READ,
    "kodecode_dap_stack": _READ,
    "kodecode_dap_scopes": _READ,
    "kodecode_dap_variables": _READ,
    "kodecode_dap_stop": _EXECUTE,
    "kodecode_graph_refresh": _READ,
    "kodecode_graph_symbols": _READ,
    "kodecode_graph_calls": _READ,
    "kodecode_graph_dependencies": _READ,
}


class KodeCodeExecutor:
    """Guardian-governed structured execution boundary for all R4 KodeCode tools.

    The executor composes tool providers but never exposes arbitrary filesystem
    or process execution. Every tool name must have an explicit policy entry.
    """

    def __init__(
        self,
        root: Path,
        *,
        guardian: KodeGuardian,
        audit: AuditLog,
        safe_change: SafeChangeManager,
        base_api: KodeCodeToolAPI | None = None,
        graph_api: GraphToolAPI | None = None,
        policies: dict[str, ToolPolicy] | None = None,
    ) -> None:
        self.root = root.resolve(strict=False)
        self.guardian = guardian
        self.audit = audit
        self.safe_change = safe_change
        self.base_api = base_api or KodeCodeToolAPI(self.root)
        self.graph_api = graph_api or GraphToolAPI(self.root)
        self.policies = dict(policies or DEFAULT_TOOL_POLICIES)
        self._providers: dict[str, Callable[[str, dict[str, Any]], Any]] = {}
        self._catalog: list[dict[str, Any]] = []
        self._register_provider(self.base_api)
        self._register_provider(self.graph_api)
        tool_names = set(self._providers)
        missing = sorted(tool_names - self.policies.keys())
        if missing:
            raise RuntimeError(f"KodeCode tools missing explicit policy: {', '.join(missing)}")

    def _register_provider(self, provider: Any) -> None:
        catalog = provider.catalog()
        for schema in catalog:
            name = str(schema["function"]["name"])
            if name in self._providers:
                raise RuntimeError(f"Duplicate KodeCode tool name: {name}")
            self._providers[name] = provider.invoke
            self._catalog.append(schema)

    def catalog(self) -> list[dict[str, Any]]:
        return list(self._catalog)

    def policy(self, tool_name: str) -> ToolPolicy:
        if tool_name not in self._providers:
            raise KeyError(f"Unknown KodeCode tool: {tool_name}")
        return self.policies[tool_name]

    def invoke(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        actor: str = "brain",
        confirmed: bool = False,
    ) -> ToolExecutionResult:
        if tool_name not in self._providers:
            raise KeyError(f"Unknown KodeCode tool: {tool_name}")
        args = dict(arguments or {})
        policy = self.policies[tool_name]
        target = self._target(policy, args)
        request = ActionRequest(
            action=policy.action,
            actor=actor,
            target=str(target) if target is not None else "",
            project_root=self.root,
            sandboxed=policy.effect is ToolEffect.EXECUTE,
            metadata={"tool_name": tool_name, "effect": policy.effect.value},
        )

        try:
            decision = self.guardian.authorize(request, confirmed=confirmed)
        except PermissionDenied as exc:
            self.audit.append(
                "kodecode",
                tool_name,
                actor,
                "permission-denied",
                {"effect": policy.effect.value, "arg_keys": sorted(args), "error": str(exc)},
            )
            raise

        if decision.kind is DecisionKind.DENY:
            self.audit.append(
                "kodecode",
                tool_name,
                actor,
                "denied",
                {"effect": policy.effect.value, "reason": decision.reason, "arg_keys": sorted(args)},
            )
            raise PolicyDenied(decision.reason)
        if decision.kind is DecisionKind.CONFIRM:
            self.audit.append(
                "kodecode",
                tool_name,
                actor,
                "confirmation-required",
                {"effect": policy.effect.value, "reason": decision.reason, "arg_keys": sorted(args)},
            )
            raise PolicyDenied(f"Explicit confirmation required: {decision.reason}")

        snapshot_text: str | None = None
        if decision.snapshot_required:
            if policy.snapshot_arg is None:
                raise RuntimeError(f"Snapshot-required tool has no snapshot target policy: {tool_name}")
            snapshot_target = self._resolve_argument_path(args, policy.snapshot_arg, must_exist=True)
            snapshot = self.safe_change.snapshot([snapshot_target])
            snapshot_text = str(snapshot)

        self.audit.append(
            "kodecode",
            tool_name,
            actor,
            "authorized",
            {
                "effect": policy.effect.value,
                "risk": int(decision.risk),
                "arg_keys": sorted(args),
                "snapshot": snapshot_text,
            },
        )
        try:
            result = self._providers[tool_name](tool_name, args)
        except Exception as exc:
            self.audit.append(
                "kodecode",
                tool_name,
                actor,
                "failed",
                {"effect": policy.effect.value, "error_type": type(exc).__name__},
            )
            raise
        self.audit.append(
            "kodecode",
            tool_name,
            actor,
            "completed",
            {"effect": policy.effect.value, "snapshot": snapshot_text},
        )
        return ToolExecutionResult(tool_name, result, snapshot_text)

    def _target(self, policy: ToolPolicy, args: dict[str, Any]) -> Path | None:
        if policy.target_arg is None or policy.target_arg not in args:
            return None
        return self._resolve_argument_path(args, policy.target_arg, must_exist=False)

    def _resolve_argument_path(
        self,
        args: dict[str, Any],
        key: str,
        *,
        must_exist: bool,
    ) -> Path:
        raw = str(args[key])
        boundary = self.base_api.boundary
        return boundary.resolve(raw, must_exist=must_exist)
