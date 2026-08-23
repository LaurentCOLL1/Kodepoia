from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .client import ComfyUIClient
from .errors import ComfyError
from .packs import ProductionWorkflowFamily
from .r9_8_acceptance import R98AcceptanceRequest, write_r98_evidence
from .r9_8_wire_client import run_r98_wire_compatible_acceptance
from .serialization import make_envelope
from .service import ComfyService


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


def _print(document: Any) -> None:
    print(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True))


def _service(args: argparse.Namespace) -> ComfyService:
    return ComfyService(Path.cwd(), endpoint=args.endpoint)


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
    _print({"output": str(destination), "ready": snapshot.ready, "probe": document})
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
        raise argparse.ArgumentTypeError("Comfy CLI accepts JSON scalar assignments only")
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
    _print(payload)
    return 0 if evidence.status == "pass" else 2


def _comfy_status(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        status = service.status(args.run_id)
        _print(status.canonical())
        return 0 if status.ready else 2
    finally:
        service.close()


def _comfy_inventory(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        snapshot = service.inventory_snapshot()
        _print(snapshot.payload())
        return 0 if snapshot.state.value == "current" else 2
    finally:
        service.close()


def _workflow_list(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        _print({"workflow_families": list(service.workflow_families())})
        return 0
    finally:
        service.close()


def _workflow_validate(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        report = service.validate_workflow(
            args.family,
            model_selections={"checkpoint": args.model_checkpoint},
        )
        _print(report.canonical())
        return 0 if report.state.value == "compatible" else 2
    finally:
        service.close()


def _workflow_parameters(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "prompt": args.prompt,
        "negative_prompt": args.negative_prompt,
        "width": args.width,
        "height": args.height,
        "output_count": args.output_count,
        "seed": args.seed,
        "steps": args.steps,
        "cfg": args.cfg,
    }


def _workflow_run(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        result = service.run_workflow(
            args.family,
            parameters=_workflow_parameters(args),
            model_selections={"checkpoint": args.model_checkpoint},
            allow_memory_cleanup=bool(args.allow_memory_cleanup),
            reserve_mib=args.reserve_mib,
            headroom_mib=args.headroom_mib,
            device_index=args.device_index,
        )
        _print(result.canonical())
        return 0 if result.manifest.state.value == "succeeded" else 2
    except ComfyError as exc:
        _print({"status": "blocked", "reason": str(exc)})
        return 2
    finally:
        service.close()


def _run_status(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        manifest = service.run_status(args.run_id, reconcile=not args.no_reconcile)
        _print(manifest.payload())
        return 0 if manifest.state.value not in {"failed"} else 2
    finally:
        service.close()


def _cancel(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        manifest = service.cancel_run(args.run_id)
        _print(manifest.payload())
        return 0
    except ComfyError as exc:
        _print({"status": "blocked", "reason": str(exc)})
        return 2
    finally:
        service.close()


def _free_memory(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        evidence = service.free_memory(confirmed=bool(args.confirm))
        _print(evidence.canonical())
        return 0
    except ComfyError as exc:
        _print({"status": "blocked", "reason": str(exc)})
        return 2
    finally:
        service.close()


def _capture_outputs(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        evidence = service.capture_run_outputs(args.run_id)
        _print(evidence.payload())
        return 0 if evidence.state.value == "complete" else 2
    except (ComfyError, KeyError, ValueError) as exc:
        _print({"status": "blocked", "reason": str(exc)})
        return 2
    finally:
        service.close()


def _evidence(args: argparse.Namespace) -> int:
    service = _service(args)
    try:
        document = service.evidence(args.run_id)
        if args.output:
            destination = _confined_output(args.output)
            _write_atomic_json(destination, document)
            _print({"output": str(destination), "evidence": document})
        else:
            _print(document)
        return 0
    finally:
        service.close()


def _add_endpoint(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--endpoint", default="http://127.0.0.1:8188")


def _add_family(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--family", choices=[item.value for item in ProductionWorkflowFamily], required=True)


def register_comfy_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    probe = commands.add_parser("comfy-probe", help="Probe the fixed loopback ComfyUI R9.2 protocol surface")
    _add_endpoint(probe)
    probe.add_argument(
        "--output",
        default=".kodepoia/evidence/r9-2-comfy-probe.json",
        help="workspace-relative versioned protocol evidence output",
    )
    probe.set_defaults(func=_probe)

    status = commands.add_parser("comfy-status", help="Show governed local ComfyUI/capability/VRAM status as JSON")
    _add_endpoint(status)
    status.add_argument("--run-id")
    status.set_defaults(func=_comfy_status)

    inventory = commands.add_parser("comfy-inventory", help="Capture the governed node/model capability inventory")
    _add_endpoint(inventory)
    inventory.set_defaults(func=_comfy_inventory)

    listing = commands.add_parser("comfy-workflow-list", help="List versioned R9.9 production workflow families")
    _add_endpoint(listing)
    listing.set_defaults(func=_workflow_list)

    validate = commands.add_parser("comfy-workflow-validate", help="Validate one production workflow against current capability")
    _add_endpoint(validate)
    _add_family(validate)
    validate.add_argument("--model-checkpoint", required=True, help="explicit checkpoint inventory token")
    validate.set_defaults(func=_workflow_validate)

    run = commands.add_parser("comfy-workflow-run", help="Run one governed production workflow; raw workflow JSON is not accepted")
    _add_endpoint(run)
    _add_family(run)
    run.add_argument("--model-checkpoint", required=True, help="explicit checkpoint inventory token")
    run.add_argument("--prompt", required=True)
    run.add_argument("--negative-prompt", required=True)
    run.add_argument("--width", type=int, required=True)
    run.add_argument("--height", type=int, required=True)
    run.add_argument("--output-count", type=int, default=1)
    run.add_argument("--seed", type=int, required=True)
    run.add_argument("--steps", type=int, default=20)
    run.add_argument("--cfg", type=float, default=7.0)
    run.add_argument("--reserve-mib", type=int, default=512)
    run.add_argument("--headroom-mib", type=int, default=512)
    run.add_argument("--device-index", type=int, default=0)
    run.add_argument(
        "--allow-memory-cleanup",
        action="store_true",
        help="explicitly allow a bounded ComfyUI /free request only if admission is DEFER",
    )
    run.set_defaults(func=_workflow_run)

    run_status = commands.add_parser("comfy-run-status", help="Reconcile and print one persisted R9 run manifest")
    _add_endpoint(run_status)
    run_status.add_argument("--run-id", required=True)
    run_status.add_argument("--no-reconcile", action="store_true", help="read persisted manifest without network reconciliation")
    run_status.set_defaults(func=_run_status)

    cancel = commands.add_parser("comfy-cancel", help="Cancel one correlated run through governed R9 lifecycle semantics")
    _add_endpoint(cancel)
    cancel.add_argument("--run-id", required=True)
    cancel.set_defaults(func=_cancel)

    free_memory = commands.add_parser("comfy-free-memory", help="Request bounded ComfyUI model unload/free-memory and remeasure")
    _add_endpoint(free_memory)
    free_memory.add_argument("--confirm", action="store_true", help="required explicit confirmation for the memory-release request")
    free_memory.set_defaults(func=_free_memory)

    capture = commands.add_parser("comfy-capture-outputs", help="Promote reconciled successful outputs through the R8 Vault lineage bridge")
    _add_endpoint(capture)
    capture.add_argument("--run-id", required=True)
    capture.set_defaults(func=_capture_outputs)

    evidence = commands.add_parser("comfy-evidence", help="Emit machine-readable governed ComfyUI evidence")
    _add_endpoint(evidence)
    evidence.add_argument("--run-id")
    evidence.add_argument("--output", help="optional workspace-relative evidence JSON path")
    evidence.set_defaults(func=_evidence)

    r98 = commands.add_parser(
        "r9-local-vram-acceptance",
        help="Run the REQUIRED exact-head R9.8 local ComfyUI/GPU acceptance gate",
    )
    r98.add_argument("--candidate-head", required=True, help="exact 40-char R9.8 candidate Git SHA")
    _add_endpoint(r98)
    r98.add_argument("--workflow-root", required=True, help="workspace-confined R9.4 workflow catalog directory")
    r98.add_argument("--workflow-file", required=True, help="explicit safe workflow definition JSON basename")
    r98.add_argument("--model", action="append", type=_model_assignment, default=[], metavar="REQUIREMENT=TOKEN")
    r98.add_argument("--param", action="append", type=_json_assignment, default=[], metavar="NAME=JSON")
    r98.add_argument("--input", action="append", type=_json_assignment, default=[], metavar="NAME=JSON")
    r98.add_argument("--estimate-mib", type=int, required=True)
    r98.add_argument("--reserve-mib", type=int, default=512)
    r98.add_argument("--headroom-mib", type=int, default=512)
    r98.add_argument("--total-limit-mib", type=int)
    r98.add_argument("--device-index", type=int, default=0)
    r98.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    r98.add_argument("--allow-ollama-unload", action="append", default=[], metavar="MODEL")
    r98.add_argument("--restore-ollama", action="store_true")
    r98.add_argument("--max-wait-seconds", type=float, default=300.0)
    r98.add_argument("--poll-interval-seconds", type=float, default=0.25)
    r98.add_argument("--output", default=".kodepoia/evidence/r9-8-local-vram.json")
    r98.set_defaults(func=_r9_local_vram_acceptance)
