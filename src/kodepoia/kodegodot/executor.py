from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.core.permissions import Capability
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.exceptions import PermissionDenied, PolicyDenied
from kodepoia.kodegodot.api import GodotToolAPI


@dataclass(frozen=True, slots=True)
class GodotToolPolicy:
    action: ActionType
    target_arg: str | None = None
    snapshot_arg: str | None = None
    extra_capabilities: tuple[Capability, ...] = ()
    extra_write_root: str | None = None


@dataclass(frozen=True, slots=True)
class GodotToolExecutionResult:
    tool_name: str
    result: Any
    snapshot: str | None = None


_READ = GodotToolPolicy(ActionType.READ)
_EXECUTE = GodotToolPolicy(ActionType.EXECUTE)


DEFAULT_GODOT_POLICIES: dict[str, GodotToolPolicy] = {
    "kodegodot_project_inspect": _READ,
    "kodegodot_document_parse": GodotToolPolicy(ActionType.READ, target_arg="path"),
    "kodegodot_document_dependencies": GodotToolPolicy(ActionType.READ, target_arg="path"),
    "kodegodot_scene_analyze": GodotToolPolicy(ActionType.READ, target_arg="path"),
    "kodegodot_scene_set_existing_property": GodotToolPolicy(ActionType.WRITE, target_arg="path", snapshot_arg="path"),
    "kodegodot_gdscript_inspect": GodotToolPolicy(ActionType.READ, target_arg="path"),
    "kodegodot_engine_version": _EXECUTE,
    "kodegodot_check_script": GodotToolPolicy(ActionType.EXECUTE, target_arg="path", extra_capabilities=(Capability.FILE_READ,)),
    "kodegodot_import_project": GodotToolPolicy(ActionType.EXECUTE, extra_capabilities=(Capability.FILE_WRITE,), extra_write_root=".godot"),
    "kodegodot_smoke_project": _EXECUTE,
    "kodegodot_export_presets": _READ,
    "kodegodot_export_project": GodotToolPolicy(ActionType.EXECUTE, extra_capabilities=(Capability.FILE_WRITE,), extra_write_root=".kodepoia/exports"),
    "kodegodot_capture_movie": GodotToolPolicy(ActionType.EXECUTE, target_arg="scene", extra_capabilities=(Capability.FILE_READ, Capability.FILE_WRITE), extra_write_root=".kodepoia/captures"),
    "kodegodot_benchmark_scene": _EXECUTE,
    "kodegodot_services_start": _EXECUTE,
    "kodegodot_services_stop": _EXECUTE,
    "kodegodot_lsp_symbols": GodotToolPolicy(ActionType.EXECUTE, target_arg="path", extra_capabilities=(Capability.FILE_READ,)),
    "kodegodot_lsp_diagnostics": GodotToolPolicy(ActionType.EXECUTE, target_arg="path", extra_capabilities=(Capability.FILE_READ,)),
    "kodegodot_dap_initialize": _EXECUTE,
    "kodegodot_dap_launch_project": _EXECUTE,
    "kodegodot_dap_threads": _EXECUTE,
}


class KodeGodotExecutor:
    """Guardian/permissions/snapshot/audit boundary for all KodeGodot tools."""

    def __init__(
        self,
        root: Path,
        *,
        guardian: KodeGuardian,
        audit: AuditLog,
        safe_change: SafeChangeManager,
        api: GodotToolAPI | None = None,
        policies: dict[str, GodotToolPolicy] | None = None,
    ) -> None:
        self.root = root.resolve(strict=False)
        self.guardian = guardian
        self.audit = audit
        self.safe_change = safe_change
        self.api = api or GodotToolAPI(self.root)
        self.policies = dict(policies or DEFAULT_GODOT_POLICIES)
        self._catalog = self.api.catalog()
        self._names = {str(item["function"]["name"]) for item in self._catalog}
        missing = sorted(self._names - self.policies.keys())
        if missing:
            raise RuntimeError(f"KodeGodot tools missing explicit policy: {', '.join(missing)}")

    def catalog(self) -> list[dict[str, Any]]:
        return list(self._catalog)

    def supports(self, tool_name: str) -> bool:
        return tool_name in self._names

    def invoke(self, tool_name: str, arguments: dict[str, Any] | None = None, *, actor: str = "brain", confirmed: bool = False) -> GodotToolExecutionResult:
        if tool_name not in self._names:
            raise KeyError(f"Unknown KodeGodot tool: {tool_name}")
        args = dict(arguments or {})
        policy = self.policies[tool_name]
        target = self._resolve_target(policy, args)
        executable = Path(self.api.runtime.executable).name if policy.action is ActionType.EXECUTE else None
        request = ActionRequest(
            action=policy.action,
            actor=actor,
            target=str(target) if target is not None else "",
            project_root=self.root,
            sandboxed=policy.action is ActionType.EXECUTE,
            metadata={"tool_name": tool_name, "executable": executable or ""},
        )
        try:
            decision = self.guardian.authorize(request, confirmed=confirmed)
            self._require_extra(policy, target)
        except PermissionDenied as exc:
            self.audit.append("kodegodot", tool_name, actor, "permission-denied", {"arg_keys": sorted(args), "error": str(exc)})
            raise
        if decision.kind is DecisionKind.DENY:
            self.audit.append("kodegodot", tool_name, actor, "denied", {"reason": decision.reason, "arg_keys": sorted(args)})
            raise PolicyDenied(decision.reason)
        if decision.kind is DecisionKind.CONFIRM:
            self.audit.append("kodegodot", tool_name, actor, "confirmation-required", {"reason": decision.reason, "arg_keys": sorted(args)})
            raise PolicyDenied(f"Explicit confirmation required: {decision.reason}")

        snapshot_text: str | None = None
        if decision.snapshot_required:
            if policy.snapshot_arg is None:
                raise RuntimeError(f"Snapshot-required Godot tool has no snapshot target: {tool_name}")
            snapshot_target = self.api.documents.boundary.resolve(str(args[policy.snapshot_arg]), must_exist=True)
            snapshot_text = str(self.safe_change.snapshot([snapshot_target]))

        self.audit.append("kodegodot", tool_name, actor, "authorized", {"arg_keys": sorted(args), "snapshot": snapshot_text})
        try:
            result = self.api.invoke(tool_name, args)
        except Exception as exc:
            self.audit.append("kodegodot", tool_name, actor, "failed", {"error_type": type(exc).__name__})
            raise
        self.audit.append("kodegodot", tool_name, actor, "completed", {"snapshot": snapshot_text})
        return GodotToolExecutionResult(tool_name, result, snapshot_text)

    def _resolve_target(self, policy: GodotToolPolicy, args: dict[str, Any]) -> Path | None:
        if policy.target_arg is None or args.get(policy.target_arg) is None:
            return None
        return self.api.documents.boundary.resolve(str(args[policy.target_arg]), must_exist=True)

    def _require_extra(self, policy: GodotToolPolicy, target: Path | None) -> None:
        for capability in policy.extra_capabilities:
            path: Path | None = None
            if capability is Capability.FILE_READ:
                path = target or self.root
            elif capability is Capability.FILE_WRITE:
                path = self.root / (policy.extra_write_root or ".")
            self.guardian.permissions.require(capability, path=path)
