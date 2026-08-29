from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Mapping, Protocol

from .contracts import BackendEnvironmentKind


SCHEMA_ID = "kodepoia.r14.liveops-ux.v1"
_RESOURCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_FORBIDDEN_INPUT_KEYS = frozenset(
    {
        "api_key",
        "cmd",
        "command",
        "credential",
        "credentials",
        "dsn",
        "endpoint",
        "endpoint_url",
        "password",
        "private_key",
        "raw_command",
        "secret",
        "shell",
        "token",
        "url",
    }
)
_SECRET_OUTPUT_MARKERS = (
    "api_key",
    "authorization",
    "credential",
    "dsn",
    "password",
    "private_key",
    "secret",
    "token",
)


class LiveOpsUXPolicyError(ValueError):
    """Raised when untrusted UI/CLI input crosses an R14.16 safety boundary."""


class LiveOpsMode(StrEnum):
    INSPECT = "inspect"
    PREVIEW = "preview"
    APPLY = "apply"
    ROLLBACK = "rollback"


class LiveOpsOperation(StrEnum):
    BACKEND_PROFILE = "backend_profile"
    LOCAL_STACK = "local_stack"
    MIGRATION = "migration"
    PROVIDER_CAPABILITY = "provider_capability"
    LOBBY_INSPECT = "lobby_inspect"
    SAVE_INSPECT = "save_inspect"
    PROGRESSION_INSPECT = "progression_inspect"
    ENTITLEMENT_RECONCILE = "entitlement_reconcile"
    REMOTE_CONFIG = "remote_config"
    CONTENT = "content"
    CAMPAIGN = "campaign"
    EVENT_REPLAY = "event_replay"
    HEALTH_REPORT = "health_report"
    LOAD_REPORT = "load_report"
    BACKUP_REPORT = "backup_report"


@dataclass(frozen=True, slots=True)
class LiveOpsActionPolicy:
    modes: tuple[LiveOpsMode, ...]
    actions: tuple[str, ...] = ("show",)
    resource_required: bool = False
    confirmation_modes: frozenset[LiveOpsMode] = field(default_factory=frozenset)
    local_test_only_actions: frozenset[str] = field(default_factory=frozenset)

    def to_dict(self) -> dict[str, object]:
        return {
            "modes": [item.value for item in self.modes],
            "actions": list(self.actions),
            "resource_required": self.resource_required,
            "confirmation_modes": sorted(item.value for item in self.confirmation_modes),
            "local_test_only_actions": sorted(self.local_test_only_actions),
        }


POLICIES: dict[LiveOpsOperation, LiveOpsActionPolicy] = {
    LiveOpsOperation.BACKEND_PROFILE: LiveOpsActionPolicy((LiveOpsMode.INSPECT,)),
    LiveOpsOperation.LOCAL_STACK: LiveOpsActionPolicy(
        (LiveOpsMode.INSPECT, LiveOpsMode.APPLY),
        actions=("status", "start", "stop"),
        confirmation_modes=frozenset({LiveOpsMode.APPLY}),
        local_test_only_actions=frozenset({"start", "stop"}),
    ),
    LiveOpsOperation.MIGRATION: LiveOpsActionPolicy(
        (LiveOpsMode.PREVIEW, LiveOpsMode.APPLY),
        actions=("plan", "apply"),
        resource_required=True,
        confirmation_modes=frozenset({LiveOpsMode.APPLY}),
    ),
    LiveOpsOperation.PROVIDER_CAPABILITY: LiveOpsActionPolicy((LiveOpsMode.INSPECT,)),
    LiveOpsOperation.LOBBY_INSPECT: LiveOpsActionPolicy(
        (LiveOpsMode.INSPECT,), resource_required=True
    ),
    LiveOpsOperation.SAVE_INSPECT: LiveOpsActionPolicy(
        (LiveOpsMode.INSPECT,), resource_required=True
    ),
    LiveOpsOperation.PROGRESSION_INSPECT: LiveOpsActionPolicy(
        (LiveOpsMode.INSPECT,), resource_required=True
    ),
    LiveOpsOperation.ENTITLEMENT_RECONCILE: LiveOpsActionPolicy(
        (LiveOpsMode.PREVIEW,), resource_required=True
    ),
    LiveOpsOperation.REMOTE_CONFIG: LiveOpsActionPolicy(
        (LiveOpsMode.PREVIEW, LiveOpsMode.APPLY, LiveOpsMode.ROLLBACK),
        actions=("preview", "rollout", "rollback"),
        resource_required=True,
        confirmation_modes=frozenset({LiveOpsMode.APPLY, LiveOpsMode.ROLLBACK}),
    ),
    LiveOpsOperation.CONTENT: LiveOpsActionPolicy(
        (LiveOpsMode.PREVIEW, LiveOpsMode.APPLY, LiveOpsMode.ROLLBACK),
        actions=("preview", "rollout", "rollback"),
        resource_required=True,
        confirmation_modes=frozenset({LiveOpsMode.APPLY, LiveOpsMode.ROLLBACK}),
    ),
    LiveOpsOperation.CAMPAIGN: LiveOpsActionPolicy(
        (LiveOpsMode.PREVIEW, LiveOpsMode.APPLY, LiveOpsMode.ROLLBACK),
        actions=("preview", "rollout", "rollback"),
        resource_required=True,
        confirmation_modes=frozenset({LiveOpsMode.APPLY, LiveOpsMode.ROLLBACK}),
    ),
    LiveOpsOperation.EVENT_REPLAY: LiveOpsActionPolicy(
        (LiveOpsMode.PREVIEW,), resource_required=True
    ),
    LiveOpsOperation.HEALTH_REPORT: LiveOpsActionPolicy((LiveOpsMode.INSPECT,)),
    LiveOpsOperation.LOAD_REPORT: LiveOpsActionPolicy((LiveOpsMode.INSPECT,)),
    LiveOpsOperation.BACKUP_REPORT: LiveOpsActionPolicy((LiveOpsMode.INSPECT,)),
}


@dataclass(frozen=True, slots=True)
class LiveOpsUXRequest:
    operation: LiveOpsOperation
    environment: BackendEnvironmentKind = BackendEnvironmentKind.LOCAL
    mode: LiveOpsMode = LiveOpsMode.INSPECT
    action: str = "show"
    resource_id: str | None = None
    payload: Mapping[str, object] = field(default_factory=dict)
    confirmed: bool = False


class LiveOpsDomainPort(Protocol):
    """Structured R14 domain bridge; no raw command or endpoint escape hatch."""

    def authorize(self, request: LiveOpsUXRequest) -> bool:
        """Return authoritative mutation permission for this request."""

    def authorize_production(self, request: LiveOpsUXRequest) -> bool:
        """Return authoritative production-mutation permission."""

    def invoke(self, request: LiveOpsUXRequest) -> Mapping[str, object]:
        """Execute one typed domain operation and return structured data."""


class ProjectLiveOpsDomain:
    """Truthful project-local fallback when no richer R14 service is injected.

    It exposes read-only local facts and reports missing provider/domain bindings as
    UNAVAILABLE. Mutation authorization is deliberately false: a CLI/GUI control
    cannot self-grant server/domain authority.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve(strict=False)

    def authorize(self, request: LiveOpsUXRequest) -> bool:
        return request.mode in {LiveOpsMode.INSPECT, LiveOpsMode.PREVIEW}

    def authorize_production(self, request: LiveOpsUXRequest) -> bool:
        return False

    def invoke(self, request: LiveOpsUXRequest) -> Mapping[str, object]:
        if request.operation is LiveOpsOperation.BACKEND_PROFILE:
            return {
                "status": "ok",
                "project_root": str(self.project_root),
                "environment": request.environment.value,
                "authority_source": "project_local_read_only",
            }
        if request.operation in {
            LiveOpsOperation.LOCAL_STACK,
            LiveOpsOperation.HEALTH_REPORT,
        } and request.action in {"show", "status"}:
            ready = self.project_root / ".kodepoia" / "backend" / "run" / "ready.json"
            if not ready.is_file():
                return {
                    "status": "unavailable",
                    "reason": "local_backend_not_running",
                    "ready_file_present": False,
                }
            try:
                payload = json.loads(ready.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {
                    "status": "unavailable",
                    "reason": "local_backend_readiness_invalid",
                    "ready_file_present": True,
                }
            if not isinstance(payload, dict):
                return {
                    "status": "unavailable",
                    "reason": "local_backend_readiness_invalid",
                    "ready_file_present": True,
                }
            return {
                "status": "ok",
                "ready_file_present": True,
                "health": payload,
            }
        if request.operation is LiveOpsOperation.PROVIDER_CAPABILITY:
            return {
                "status": "unavailable",
                "reason": "provider_adapter_not_bound",
                "provider_live_claim": False,
            }
        if request.operation is LiveOpsOperation.LOAD_REPORT:
            return {
                "status": "unavailable",
                "reason": "load_report_not_bound",
                "external_load_claim": False,
            }
        if request.operation is LiveOpsOperation.BACKUP_REPORT:
            return {
                "status": "unavailable",
                "reason": "backup_report_not_bound",
                "production_pitr_claim": False,
            }
        return {
            "status": "unavailable",
            "reason": "domain_service_not_bound",
            "operation": request.operation.value,
        }


def _assert_safe_resource_id(resource_id: str | None, *, required: bool) -> None:
    if resource_id is None:
        if required:
            raise LiveOpsUXPolicyError("resource_id is required for this operation")
        return
    if "://" in resource_id or _RESOURCE_RE.fullmatch(resource_id) is None:
        raise LiveOpsUXPolicyError("resource_id contains forbidden endpoint syntax or characters")


def _assert_safe_input(value: object, *, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key).strip().lower()
            if name in _FORBIDDEN_INPUT_KEYS:
                raise LiveOpsUXPolicyError(f"forbidden raw input field: {path}.{name}")
            _assert_safe_input(item, path=f"{path}.{name}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_safe_input(item, path=f"{path}[{index}]")
        return
    if isinstance(value, str):
        if "://" in value or any(ord(char) < 32 for char in value):
            raise LiveOpsUXPolicyError(f"forbidden raw endpoint/control input at {path}")
        return
    if isinstance(value, (int, float, bool)) or value is None:
        return
    raise LiveOpsUXPolicyError(f"unsupported input type at {path}: {type(value).__name__}")


def _assert_action_mode(request: LiveOpsUXRequest) -> None:
    if request.operation is LiveOpsOperation.LOCAL_STACK:
        expected = LiveOpsMode.INSPECT if request.action == "status" else LiveOpsMode.APPLY
        if request.mode is not expected:
            raise LiveOpsUXPolicyError("local stack status is inspect-only; start/stop require apply mode")
    elif request.operation is LiveOpsOperation.MIGRATION:
        expected = LiveOpsMode.PREVIEW if request.action == "plan" else LiveOpsMode.APPLY
        if request.mode is not expected:
            raise LiveOpsUXPolicyError("migration plan requires preview mode and apply requires apply mode")
    elif request.operation in {
        LiveOpsOperation.REMOTE_CONFIG,
        LiveOpsOperation.CONTENT,
        LiveOpsOperation.CAMPAIGN,
    }:
        expected = {
            "preview": LiveOpsMode.PREVIEW,
            "rollout": LiveOpsMode.APPLY,
            "rollback": LiveOpsMode.ROLLBACK,
        }[request.action]
        if request.mode is not expected:
            raise LiveOpsUXPolicyError("change action and mode do not match")


def redact_liveops_value(value: object, *, key: str = "") -> object:
    lowered = key.lower()
    if key and any(marker in lowered for marker in _SECRET_OUTPUT_MARKERS):
        if lowered.endswith("_ref") or lowered.endswith("_reference"):
            return "<secret-ref>"
        return "<redacted>"
    if isinstance(value, Mapping):
        return {
            str(item_key): redact_liveops_value(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_liveops_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class BackendLiveOpsUXService:
    """Policy-preserving presentation service shared by CLI and KodeStudio."""

    def __init__(self, domain: LiveOpsDomainPort) -> None:
        self.domain = domain

    @classmethod
    def for_project(cls, project_root: Path) -> "BackendLiveOpsUXService":
        return cls(ProjectLiveOpsDomain(project_root))

    def catalog(self) -> dict[str, object]:
        return {
            "schema": SCHEMA_ID,
            "operations": {
                operation.value: POLICIES[operation].to_dict()
                for operation in LiveOpsOperation
            },
            "forbidden_input_fields": sorted(_FORBIDDEN_INPUT_KEYS),
            "defaults": {
                "migration": LiveOpsMode.PREVIEW.value,
                "event_replay": LiveOpsMode.PREVIEW.value,
                "remote_config": LiveOpsMode.PREVIEW.value,
                "content": LiveOpsMode.PREVIEW.value,
                "campaign": LiveOpsMode.PREVIEW.value,
            },
        }

    def execute(self, request: LiveOpsUXRequest) -> dict[str, object]:
        policy = POLICIES[request.operation]
        if request.mode not in policy.modes:
            raise LiveOpsUXPolicyError(
                f"mode {request.mode.value!r} is not allowed for {request.operation.value!r}"
            )
        if request.action not in policy.actions:
            raise LiveOpsUXPolicyError(
                f"action {request.action!r} is not allowed for {request.operation.value!r}"
            )
        _assert_action_mode(request)
        _assert_safe_resource_id(request.resource_id, required=policy.resource_required)
        _assert_safe_input(request.payload)

        if request.action in policy.local_test_only_actions and request.environment not in {
            BackendEnvironmentKind.LOCAL,
            BackendEnvironmentKind.TEST,
        }:
            return self._blocked(
                request,
                reason="local_stack_mutation_forbidden_outside_local_test",
            )
        if request.mode in policy.confirmation_modes and not request.confirmed:
            return self._blocked(request, reason="explicit_confirmation_required")
        if request.mode in {LiveOpsMode.APPLY, LiveOpsMode.ROLLBACK}:
            if not self.domain.authorize(request):
                return self._blocked(request, reason="domain_permission_denied")
            if (
                request.environment is BackendEnvironmentKind.PRODUCTION
                and not self.domain.authorize_production(request)
            ):
                return self._blocked(request, reason="production_authority_denied")

        domain_payload = redact_liveops_value(self.domain.invoke(request))
        domain_status = "ok"
        if isinstance(domain_payload, Mapping):
            candidate = domain_payload.get("status")
            if candidate in {"ok", "blocked", "unavailable", "error"}:
                domain_status = str(candidate)

        return {
            "schema": SCHEMA_ID,
            "status": domain_status,
            "operation": request.operation.value,
            "environment": request.environment.value,
            "mode": request.mode.value,
            "action": request.action,
            "resource_id": request.resource_id,
            "authority": {
                "confirmation_required": request.mode in policy.confirmation_modes,
                "confirmation_supplied": bool(request.confirmed),
                "mutation": request.mode in {LiveOpsMode.APPLY, LiveOpsMode.ROLLBACK},
            },
            "redacted": True,
            "result": domain_payload,
        }

    def _blocked(self, request: LiveOpsUXRequest, *, reason: str) -> dict[str, object]:
        return {
            "schema": SCHEMA_ID,
            "status": "blocked",
            "operation": request.operation.value,
            "environment": request.environment.value,
            "mode": request.mode.value,
            "action": request.action,
            "resource_id": request.resource_id,
            "authority": {
                "confirmation_supplied": bool(request.confirmed),
                "mutation": request.mode in {LiveOpsMode.APPLY, LiveOpsMode.ROLLBACK},
            },
            "redacted": True,
            "reason": reason,
            "result": {},
        }


def stable_liveops_json(payload: Mapping[str, object]) -> str:
    return json.dumps(
        redact_liveops_value(payload),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
