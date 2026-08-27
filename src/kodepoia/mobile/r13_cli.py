from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.mobile.workspace import (
    MobileWorkspaceOperation,
    MobileWorkspaceService,
    MobileWorkspaceState,
)


EXIT_OK = 0
EXIT_BLOCKED = 2
EXIT_CANCELLED = 130


def _run_workspace(args: argparse.Namespace) -> int:
    operation = MobileWorkspaceOperation(args.r13_operation)
    service = MobileWorkspaceService(Path(args.project))
    result = service.execute(operation)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    if result.state is MobileWorkspaceState.CANCELLED:
        return EXIT_CANCELLED
    return EXIT_OK if result.ok else EXIT_BLOCKED


def register_r13_commands(commands: argparse._SubParsersAction) -> None:
    r13 = commands.add_parser(
        "r13",
        help="Governed mobile, DeviceLab, compliance and release workspace intents for R13.",
    )
    sub = r13.add_subparsers(dest="r13_operation", required=True)
    for operation in MobileWorkspaceOperation:
        command = sub.add_parser(
            operation.value,
            help=f"Run the governed R13 {operation.value} intent.",
        )
        command.add_argument(
            "--project",
            default=".",
            help=(
                "Kodepoia project root. Raw executable, argv, Gradle/Xcode setting, "
                "signing material, device shell command and store-token inputs are not accepted."
            ),
        )
        command.set_defaults(func=_run_workspace)


__all__ = ["EXIT_BLOCKED", "EXIT_CANCELLED", "EXIT_OK", "register_r13_commands"]
