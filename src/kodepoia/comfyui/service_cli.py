from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from .errors import ComfyGovernanceError, ComfyProtocolError, ComfyUnavailableError
from .packs import ProductionWorkflowFamily
from .service import ComfyService


def _emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _invoke(operation: Callable[[ComfyService], Any]) -> int:
    service = ComfyService(Path.cwd())
    try:
        result = operation(service)
    except (ComfyGovernanceError, ComfyProtocolError, ComfyUnavailableError, KeyError, ValueError, OSError) as exc:
        _emit(
            {
                "state": "blocked" if isinstance(exc, ComfyGovernanceError) else "unavailable",
                "error_type": type(exc).__name__,
                "reason": str(exc),
            }
        )
        return 2
    _emit(result)
    if isinstance(result, dict) and result.get("state") in {
        "blocked", "unavailable", "unknown", "reject", "defer"
    }:
        return 2
    return 0


def _status(_args: argparse.Namespace) -> int:
    return _invoke(lambda service: service.status())


def _inventory(args: argparse.Namespace) -> int:
    return _invoke(lambda service: service.inventory(refresh=not args.cached))


def _workflows(args: argparse.Namespace) -> int:
    return _invoke(
        lambda service: service.workflows(
            refresh_inventory=args.refresh,
            model_selection=args.model,
        )
    )


def _validate(args: argparse.Namespace) -> int:
    return _invoke(
        lambda service: service.validate(
            args.family,
            model_selection=args.model,
            refresh_inventory=not args.cached,
        )
    )


def _run(args: argparse.Namespace) -> int:
    return _invoke(
        lambda service: service.run(
            args.family,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            width=args.width,
            height=args.height,
            output_count=args.output_count,
            seed=args.seed,
            steps=args.steps,
            cfg=args.cfg,
            model_selection=args.model,
            reserve_mib=args.reserve_mib,
            headroom_mib=args.headroom_mib,
        )
    )


def _run_status(args: argparse.Namespace) -> int:
    return _invoke(
        lambda service: service.run_status(args.run_id, reconcile=not args.no_reconcile)
    )


def _cancel(args: argparse.Namespace) -> int:
    return _invoke(lambda service: service.cancel(args.run_id))


def _vram(args: argparse.Namespace) -> int:
    return _invoke(
        lambda service: service.vram(
            family=args.family,
            reserve_mib=args.reserve_mib,
            headroom_mib=args.headroom_mib,
        )
    )


def _free_memory(_args: argparse.Namespace) -> int:
    return _invoke(lambda service: service.free_memory())


def _evidence(args: argparse.Namespace) -> int:
    return _invoke(lambda service: service.evidence(args.run_id))


def register_comfy_service_commands(
    commands: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    root = commands.add_parser(
        "comfy",
        help="Governed R9.10 ComfyUI workflow, run and VRAM operations",
    )
    sub = root.add_subparsers(dest="comfy_command", required=True)

    status = sub.add_parser("status", help="Show fixed-loopback protocol and capability status")
    status.set_defaults(func=_status)

    inventory = sub.add_parser("inventory", help="Capture or read the typed ComfyUI capability inventory")
    inventory.add_argument("--cached", action="store_true", help="read the last persisted snapshot only")
    inventory.set_defaults(func=_inventory)

    workflows = sub.add_parser("workflows", help="List only the four accepted R9.9 production packs")
    workflows.add_argument("--refresh", action="store_true", help="refresh capability inventory before compatibility checks")
    workflows.add_argument("--model", help="explicit checkpoint token when inventory resolution is ambiguous")
    workflows.set_defaults(func=_workflows)

    validate = sub.add_parser("validate", help="Validate one governed production workflow family")
    validate.add_argument("family", choices=[item.value for item in ProductionWorkflowFamily])
    validate.add_argument("--model", help="explicit checkpoint token when inventory resolution is ambiguous")
    validate.add_argument("--cached", action="store_true", help="validate against the persisted snapshot")
    validate.set_defaults(func=_validate)

    run = sub.add_parser("run", help="Submit one prevalidated R9.9 production workflow")
    run.add_argument("family", choices=[item.value for item in ProductionWorkflowFamily])
    run.add_argument("--prompt", required=True)
    run.add_argument("--negative-prompt", required=True)
    run.add_argument("--width", type=int, default=1024)
    run.add_argument("--height", type=int, default=1024)
    run.add_argument("--output-count", type=int, default=1)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--steps", type=int, default=24)
    run.add_argument("--cfg", type=float, default=7.0)
    run.add_argument("--model", help="explicit checkpoint token when inventory resolution is ambiguous")
    run.add_argument("--reserve-mib", type=int, default=512)
    run.add_argument("--headroom-mib", type=int, default=512)
    run.set_defaults(func=_run)

    run_status = sub.add_parser("run-status", help="Read and reconcile one persisted Kodepoia ComfyUI run")
    run_status.add_argument("run_id")
    run_status.add_argument("--no-reconcile", action="store_true", help="read persisted evidence without live queue/history reconciliation")
    run_status.set_defaults(func=_run_status)

    cancel = sub.add_parser("cancel", help="Request governed targeted cancellation for one Kodepoia run")
    cancel.add_argument("run_id")
    cancel.set_defaults(func=_cancel)

    vram = sub.add_parser("vram", help="Read typed VRAM telemetry and optional pack admission state")
    vram.add_argument("--family", choices=[item.value for item in ProductionWorkflowFamily])
    vram.add_argument("--reserve-mib", type=int, default=512)
    vram.add_argument("--headroom-mib", type=int, default=512)
    vram.set_defaults(func=_vram)

    free_memory = sub.add_parser("free-memory", help="Request accepted conservative ComfyUI model/memory cleanup")
    free_memory.set_defaults(func=_free_memory)

    evidence = sub.add_parser("evidence", help="Show persisted run, lifecycle, output and capability evidence")
    evidence.add_argument("run_id")
    evidence.set_defaults(func=_evidence)
