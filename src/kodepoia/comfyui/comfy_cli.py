from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .client import ComfyUIClient
from .r9_8_acceptance import (
    R98AcceptanceRequest,
    write_r98_evidence,
)
from .r9_8_wire_client import run_r98_wire_compatible_acceptance
from .serialization import make_envelope
from .service_cli import register_comfy_service_commands


def _confined_output(path_text: str) -> Path:
    requested = Path(path_text)
    if requested.is_absolute():
        raise SystemExit("comfy evidence output must be relative to the current workspace")
    root = Path.cwd().resolve(strict=False)
    destination = (root / requested).resolve(strict=False)
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise SystemExit("comfy evidence output must remain inside the current workspace") from exc
    return destination


def _write_atomic_json(destination: Path, document: dict[str, object]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(destination)


def _probe(args: argparse.Namespace) -> int:
    client = ComfyUIClient(args.endpoint)
    snapshot = client.probe()
    document = make_envelope(
        schema="kodepoia.comfy-protocol-probe",
        version=1,
        payload=snapshot.canonical(),
    )
    destination = _confined_output(args.output)
    _write_atomic_json(destination, document)
    print(
        json.dumps(
            {
                "output": str(destination),
                "ready": snapshot.ready,
                "probe": document,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if snapshot.ready else 2


def _parse_assignment(value: str, *, json_value: bool) -> tuple[str, Any]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected NAME=VALUE")
    name, raw = value.split("=", 1)
    if not name or len(name) > 128:
        raise argparse.ArgumentTypeError("assignment name must contain 1-128 characters")
    if not json_value:
        if not raw or len(raw) > 1024:
            raise argparse.ArgumentTypeError("assignment value must contain 1-1024 characters")
        return name, raw
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON scalar: {exc}") from exc
    if isinstance(parsed, (dict, list)):
        raise argparse.ArgumentTypeError("R9.8 CLI accepts JSON scalar assignments only")
    return name, parsed


def _model_assignment(value: str) -> tuple[str, str]:
    key, parsed = _parse_assignment(value, json_value=False)
    return key, str(parsed)


def _json_assignment(value: str) -> tuple[str, Any]:
    return _parse_assignment(value, json_value=True)


def _r9_local_vram_acceptance(args: argparse.Namespace) -> int:
    request = R98AcceptanceRequest(
        candidate_head=args.candidate_head,
        endpoint=args.endpoint,
        workflow_root=Path(args.workflow_root),
        workflow_file=args.workflow_file,
        model_selections=tuple(args.model or ()),
        parameters=tuple(args.param or ()),
        input_bindings=tuple(args.input or ()),
        estimate_mib=args.estimate_mib,
        reserve_mib=args.reserve_mib,
        headroom_mib=args.headroom_mib,
        total_limit_mib=args.total_limit_mib,
        device_index=args.device_index,
        ollama_url=args.ollama_url,
        approved_ollama_unloads=tuple(args.allow_ollama_unload or ()),
        restore_ollama=bool(args.restore_ollama),
        max_wait_seconds=float(args.max_wait_seconds),
        poll_interval_seconds=float(args.poll_interval_seconds),
    )
    evidence = run_r98_wire_compatible_acceptance(Path.cwd(), request)
    destination = write_r98_evidence(Path.cwd(), args.output, evidence)
    payload = {
        "R9_8_local_vram_acceptance": evidence.status.upper(),
        "output": str(destination),
        "candidate_head": evidence.candidate_head,
        "comfyui_version": evidence.comfyui_version,
        "device": evidence.device,
        "ollama_state": evidence.ollama_state,
        "workflow_definition_id": evidence.workflow_definition_id,
        "run_id": evidence.run_id,
        "output_sha256": evidence.output_sha256,
        "output_length": evidence.output_length,
        "audit_valid": evidence.resource_audit_valid and evidence.lifecycle_audit_valid,
        "evidence_digest_sha256": evidence.evidence_digest_sha256,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if evidence.status == "pass" else 2


def register_comfy_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    probe = commands.add_parser(
        "comfy-probe",
        help="Probe the fixed loopback ComfyUI R9.2 protocol surface",
    )
    probe.add_argument("--endpoint", default="http://127.0.0.1:8188")
    probe.add_argument(
        "--output",
        default=".kodepoia/evidence/r9-2-comfy-probe.json",
        help="workspace-relative versioned protocol evidence output",
    )
    probe.set_defaults(func=_probe)

    r98 = commands.add_parser(
        "r9-local-vram-acceptance",
        help="Run the REQUIRED exact-head R9.8 local ComfyUI/GPU acceptance gate",
    )
    r98.add_argument("--candidate-head", required=True, help="exact 40-char R9.8 candidate Git SHA")
    r98.add_argument("--endpoint", default="http://127.0.0.1:8188")
    r98.add_argument("--workflow-root", required=True, help="workspace-confined R9.4 workflow catalog directory")
    r98.add_argument("--workflow-file", required=True, help="explicit safe workflow definition JSON basename")
    r98.add_argument(
        "--model",
        action="append",
        type=_model_assignment,
        default=[],
        metavar="REQUIREMENT=TOKEN",
        help="explicit R9.4 model selection; repeat as needed",
    )
    r98.add_argument(
        "--param",
        action="append",
        type=_json_assignment,
        default=[],
        metavar="NAME=JSON",
        help="explicit declared workflow scalar parameter; repeat as needed",
    )
    r98.add_argument(
        "--input",
        action="append",
        type=_json_assignment,
        default=[],
        metavar="NAME=JSON",
        help="explicit declared workflow scalar input binding; repeat as needed",
    )
    r98.add_argument("--estimate-mib", type=int, required=True)
    r98.add_argument("--reserve-mib", type=int, default=512)
    r98.add_argument("--headroom-mib", type=int, default=512)
    r98.add_argument("--total-limit-mib", type=int)
    r98.add_argument("--device-index", type=int, default=0)
    r98.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    r98.add_argument(
        "--allow-ollama-unload",
        action="append",
        default=[],
        metavar="MODEL",
        help="explicitly authorize unloading this already-running Ollama model only",
    )
    r98.add_argument(
        "--restore-ollama",
        action="store_true",
        help="after terminal cleanup, restore only Ollama models unloaded by this gate",
    )
    r98.add_argument("--max-wait-seconds", type=float, default=300.0)
    r98.add_argument("--poll-interval-seconds", type=float, default=0.25)
    r98.add_argument(
        "--output",
        default=".kodepoia/evidence/r9-8-local-vram.json",
        help="workspace-relative R9.8 evidence output",
    )
    r98.set_defaults(func=_r9_local_vram_acceptance)

    register_comfy_service_commands(commands)
