from __future__ import annotations

import argparse
import json

from kodepoia.media.workspace import R11WorkspaceService


UNSAFE_OPTION_TOKENS = frozenset({
    "--argv",
    "--command",
    "--executable",
    "--filter-graph",
    "--ffmpeg-args",
    "--model-path",
    "--raw-script",
    "--script",
    "--migration-code",
})


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _summary(args: argparse.Namespace) -> int:
    service: R11WorkspaceService = getattr(args, "_r11_service", R11WorkspaceService())
    _emit(service.summary_payload())
    return 0 if not service.summary_payload()["blockers"] else 2


def _status(args: argparse.Namespace) -> int:
    service: R11WorkspaceService = getattr(args, "_r11_service", R11WorkspaceService())
    _emit(service.status_payload(args.r11_group))
    return service.exit_code_for(args.r11_group)


def _typed_status(args: argparse.Namespace) -> int:
    service: R11WorkspaceService = getattr(args, "_r11_service", R11WorkspaceService())
    payload = service.status_payload(args.r11_group)
    payload["operation"] = args.r11_action
    _emit(payload)
    return service.exit_code_for(args.r11_group)


def register_r11_commands(commands: argparse._SubParsersAction) -> None:
    r11 = commands.add_parser(
        "r11",
        help="Governed Audio / Voice / Cinematics / Franchise workflows",
        description=(
            "Structured R11 workflows. Raw ffmpeg/Piper/Godot argv, scripts, model paths "
            "and migration code are intentionally not exposed."
        ),
    )
    top = r11.add_subparsers(dest="r11_scope", required=True)

    summary = top.add_parser("status", help="Show the complete governed R11 capability summary")
    summary.set_defaults(func=_summary)

    service = R11WorkspaceService()
    typed_extra_actions = {
        "synthesis": ("synthesis-status",),
        "cinematics": ("capture-status",),
    }
    for group in service.groups:
        parser = top.add_parser(group, help=f"Governed {service.capability(group).title} workflows")
        actions = parser.add_subparsers(dest="r11_action", required=True)
        status = actions.add_parser("status", help="Show accepted capability and evidence state")
        status.set_defaults(func=_status, r11_group=group)
        for action_name in typed_extra_actions.get(group, ()):
            action = actions.add_parser(action_name, help="Show governed runtime/evidence status")
            action.set_defaults(func=_typed_status, r11_group=group)


__all__ = ["UNSAFE_OPTION_TOKENS", "register_r11_commands"]
