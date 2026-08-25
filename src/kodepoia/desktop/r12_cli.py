from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.desktop.workspace import DesktopWorkspaceOperation, DesktopWorkspaceService


EXIT_OK = 0
EXIT_BLOCKED = 2


def _run_workspace(args: argparse.Namespace) -> int:
    operation = DesktopWorkspaceOperation(args.r12_operation)
    service = DesktopWorkspaceService(Path(args.project))
    result = service.execute(operation)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return EXIT_OK if result.ok else EXIT_BLOCKED


def register_r12_commands(commands: argparse._SubParsersAction) -> None:
    r12 = commands.add_parser(
        "r12",
        help="Governed desktop workspace operations for R12.",
    )
    sub = r12.add_subparsers(dest="r12_operation", required=True)
    for operation in DesktopWorkspaceOperation:
        command = sub.add_parser(
            operation.value,
            help=f"Run the governed desktop {operation.value} intent.",
        )
        command.add_argument(
            "--project",
            default=".",
            help="Kodepoia project root. No executable, argv or script input is accepted.",
        )
        command.set_defaults(func=_run_workspace)
