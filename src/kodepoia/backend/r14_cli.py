from __future__ import annotations

import argparse
from pathlib import Path

from .contracts import BackendEnvironmentKind
from .liveops_ux import (
    BackendLiveOpsUXService,
    LiveOpsMode,
    LiveOpsOperation,
    LiveOpsUXPolicyError,
    LiveOpsUXRequest,
    stable_liveops_json,
)


def build_liveops_service(project_root: Path) -> BackendLiveOpsUXService:
    """Integration seam for a richer authorized R14 domain port."""

    return BackendLiveOpsUXService.for_project(project_root)


def _emit(payload: dict[str, object]) -> int:
    print(stable_liveops_json(payload))
    return 0 if payload.get("status", "ok") == "ok" else 2


def _execute(args: argparse.Namespace) -> int:
    service = build_liveops_service(Path(args.project_root))
    try:
        request = LiveOpsUXRequest(
            operation=LiveOpsOperation(args.operation),
            environment=BackendEnvironmentKind(args.environment),
            mode=LiveOpsMode(args.mode),
            action=args.action,
            resource_id=getattr(args, "resource_id", None),
            confirmed=bool(getattr(args, "confirm", False)),
        )
        return _emit(service.execute(request))
    except LiveOpsUXPolicyError as exc:
        return _emit(
            {
                "schema": "kodepoia.r14.liveops-ux.v1",
                "status": "blocked",
                "reason": "policy_error",
                "detail": str(exc),
                "redacted": True,
            }
        )


def _catalog(args: argparse.Namespace) -> int:
    payload = build_liveops_service(Path(args.project_root)).catalog()
    payload["status"] = "ok"
    return _emit(payload)


def _add_context(parser: argparse.ArgumentParser, *, environment: bool = True) -> None:
    parser.add_argument("--project-root", default=".")
    if environment:
        parser.add_argument(
            "--environment",
            choices=[item.value for item in BackendEnvironmentKind],
            default=BackendEnvironmentKind.LOCAL.value,
        )


def _wire(
    parser: argparse.ArgumentParser,
    *,
    operation: LiveOpsOperation,
    mode: LiveOpsMode,
    action: str,
    resource: bool = False,
    confirm: bool = False,
) -> None:
    _add_context(parser)
    if resource:
        parser.add_argument("--resource-id", required=True)
    if confirm:
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="explicit user confirmation; domain authorization is still required",
        )
    parser.set_defaults(
        func=_execute,
        operation=operation.value,
        mode=mode.value,
        action=action,
    )


def register_r14_backend_commands(commands: argparse._SubParsersAction) -> None:
    root = commands.add_parser(
        "backend-liveops",
        help="governed R14 backend/LiveOps inspection, preview and authorized mutation UX",
    )
    sub = root.add_subparsers(dest="backend_liveops_command", required=True)

    catalog = sub.add_parser("catalog", help="show stable operations and safety defaults")
    _add_context(catalog, environment=False)
    catalog.set_defaults(func=_catalog)

    profile = sub.add_parser("profile", help="inspect backend profile and authority scope")
    _wire(
        profile,
        operation=LiveOpsOperation.BACKEND_PROFILE,
        mode=LiveOpsMode.INSPECT,
        action="show",
    )

    stack = sub.add_parser("stack", help="local/test backend stack status/start/stop")
    stack_sub = stack.add_subparsers(dest="stack_action", required=True)
    stack_status = stack_sub.add_parser("status")
    _wire(
        stack_status,
        operation=LiveOpsOperation.LOCAL_STACK,
        mode=LiveOpsMode.INSPECT,
        action="status",
    )
    for action in ("start", "stop"):
        parser = stack_sub.add_parser(action)
        _wire(
            parser,
            operation=LiveOpsOperation.LOCAL_STACK,
            mode=LiveOpsMode.APPLY,
            action=action,
            confirm=True,
        )

    migration = sub.add_parser("migration", help="database migration preview/apply")
    migration_sub = migration.add_subparsers(dest="migration_action", required=True)
    migration_plan = migration_sub.add_parser("preview")
    _wire(
        migration_plan,
        operation=LiveOpsOperation.MIGRATION,
        mode=LiveOpsMode.PREVIEW,
        action="plan",
        resource=True,
    )
    migration_apply = migration_sub.add_parser("apply")
    _wire(
        migration_apply,
        operation=LiveOpsOperation.MIGRATION,
        mode=LiveOpsMode.APPLY,
        action="apply",
        resource=True,
        confirm=True,
    )

    provider = sub.add_parser("provider-status", help="inspect provider capability truthfully")
    _wire(
        provider,
        operation=LiveOpsOperation.PROVIDER_CAPABILITY,
        mode=LiveOpsMode.INSPECT,
        action="show",
    )

    inspect = sub.add_parser("inspect", help="inspect lobby/save/progression state")
    inspect.add_argument("domain", choices=("lobby", "save", "progression"))
    inspect.add_argument("--resource-id", required=True)
    _add_context(inspect)

    def inspect_handler(args: argparse.Namespace) -> int:
        operation = {
            "lobby": LiveOpsOperation.LOBBY_INSPECT,
            "save": LiveOpsOperation.SAVE_INSPECT,
            "progression": LiveOpsOperation.PROGRESSION_INSPECT,
        }[args.domain]
        args.operation = operation.value
        args.mode = LiveOpsMode.INSPECT.value
        args.action = "show"
        return _execute(args)

    inspect.set_defaults(func=inspect_handler)

    entitlement = sub.add_parser(
        "entitlement-preview",
        help="preview entitlement reconciliation without mutating state",
    )
    _wire(
        entitlement,
        operation=LiveOpsOperation.ENTITLEMENT_RECONCILE,
        mode=LiveOpsMode.PREVIEW,
        action="show",
        resource=True,
    )

    change = sub.add_parser("change", help="preview/rollout/rollback config, content or campaign")
    change.add_argument("domain", choices=("config", "content", "campaign"))
    change.add_argument("action", choices=("preview", "rollout", "rollback"))
    change.add_argument("--resource-id", required=True)
    change.add_argument("--confirm", action="store_true")
    _add_context(change)

    def change_handler(args: argparse.Namespace) -> int:
        args.operation = {
            "config": LiveOpsOperation.REMOTE_CONFIG,
            "content": LiveOpsOperation.CONTENT,
            "campaign": LiveOpsOperation.CAMPAIGN,
        }[args.domain].value
        args.mode = {
            "preview": LiveOpsMode.PREVIEW,
            "rollout": LiveOpsMode.APPLY,
            "rollback": LiveOpsMode.ROLLBACK,
        }[args.action].value
        return _execute(args)

    change.set_defaults(func=change_handler)

    replay = sub.add_parser("replay-preview", help="preview governed event replay")
    _wire(
        replay,
        operation=LiveOpsOperation.EVENT_REPLAY,
        mode=LiveOpsMode.PREVIEW,
        action="show",
        resource=True,
    )

    report = sub.add_parser("report", help="inspect health/load/backup reports")
    report.add_argument("kind", choices=("health", "load", "backup"))
    _add_context(report)

    def report_handler(args: argparse.Namespace) -> int:
        args.operation = {
            "health": LiveOpsOperation.HEALTH_REPORT,
            "load": LiveOpsOperation.LOAD_REPORT,
            "backup": LiveOpsOperation.BACKUP_REPORT,
        }[args.kind].value
        args.mode = LiveOpsMode.INSPECT.value
        args.action = "show"
        return _execute(args)

    report.set_defaults(func=report_handler)
