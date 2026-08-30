from __future__ import annotations

import argparse
from pathlib import Path

from .r15_ux import (
    R15ActionSpec,
    R15UXPolicyError,
    R15UXService,
    R15WorkflowMode,
    R15WorkflowRequest,
    stable_r15_json,
)


def build_r15_service(project_root: Path) -> R15UXService:
    """Integration seam for configured R15 backend-independent services."""

    return R15UXService.for_project(project_root)


def _emit(payload: dict[str, object]) -> int:
    print(stable_r15_json(payload))
    return 0 if payload.get("status") not in {"blocked", "error"} else 2


def _blocked(exc: Exception) -> int:
    return _emit(
        {
            "schema": R15UXService.schema,
            "status": "blocked",
            "reason": "policy_error",
            "detail": str(exc),
            "redacted": True,
        }
    )


def _catalog(args: argparse.Namespace) -> int:
    return _emit(build_r15_service(Path(args.project_root)).catalog())


def _status(args: argparse.Namespace) -> int:
    return _emit(build_r15_service(Path(args.project_root)).status())


def _evidence(args: argparse.Namespace) -> int:
    service = build_r15_service(Path(args.project_root))
    try:
        return _emit(service.export_evidence(Path(args.output)))
    except R15UXPolicyError as exc:
        return _blocked(exc)


def _workflow(args: argparse.Namespace) -> int:
    service = build_r15_service(Path(args.project_root))
    spec = service.action(args.r15_domain, args.r15_action)
    if spec.mutation:
        mode = spec.terminal_mode if bool(args.apply) else R15WorkflowMode.DRY_RUN
    else:
        mode = R15WorkflowMode.DRY_RUN if bool(args.dry_run) else R15WorkflowMode.INSPECT
    try:
        return _emit(
            service.execute(
                R15WorkflowRequest(
                    domain=spec.domain,
                    action=spec.action,
                    mode=mode,
                    identifier=getattr(args, "identifier", None),
                    confirmed=bool(getattr(args, "confirm", False)),
                )
            )
        )
    except R15UXPolicyError as exc:
        return _blocked(exc)


def _add_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", default=".")


def _wire_action(parser: argparse.ArgumentParser, spec: R15ActionSpec) -> None:
    _add_root(parser)
    if spec.identifier_required:
        parser.add_argument(
            "--id",
            dest="identifier",
            required=True,
            help="stable immutable/evidence identifier; raw content is not accepted",
        )
    else:
        parser.add_argument("--id", dest="identifier")
    if spec.mutation:
        parser.add_argument(
            "--apply",
            action="store_true",
            help=f"execute {spec.terminal_mode.value}; omission is a non-mutating dry-run",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="explicit user confirmation; backend authorization remains mandatory",
        )
    else:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="show the structured request without invoking the configured backend",
        )
    parser.set_defaults(
        func=_workflow,
        r15_domain=spec.domain,
        r15_action=spec.action,
    )


def register_r15_commands(commands: argparse._SubParsersAction) -> None:
    root = commands.add_parser(
        "r15",
        help="governed Experience / KodeBench / Tune status, dry-run and evidence workflows",
    )
    sub = root.add_subparsers(dest="r15_command", required=True)

    catalog = sub.add_parser("catalog", help="show the stable R15 UX capability catalog")
    _add_root(catalog)
    catalog.set_defaults(func=_catalog)

    status = sub.add_parser("status", help="show redacted persisted R15 evidence status")
    _add_root(status)
    status.set_defaults(func=_status)

    evidence = sub.add_parser("evidence", help="export redacted R15 UX status and capability evidence")
    _add_root(evidence)
    evidence.add_argument(
        "--output",
        default=".kodepoia/tuning/r15-ux-evidence.json",
        help="project-relative evidence path",
    )
    evidence.set_defaults(func=_evidence)

    by_domain: dict[str, list[R15ActionSpec]] = {}
    for spec in R15UXService.actions():
        by_domain.setdefault(spec.domain, []).append(spec)

    for domain, specs in by_domain.items():
        domain_parser = sub.add_parser(domain, help=f"governed {domain} workflows")
        actions = domain_parser.add_subparsers(dest=f"r15_{domain}_action", required=True)
        for spec in specs:
            action_parser = actions.add_parser(spec.action, help=spec.description)
            _wire_action(action_parser, spec)
