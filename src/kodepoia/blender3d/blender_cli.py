from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox

from .boundary import BlenderExecutableBoundary
from .contracts import BlenderProcessLimits
from .errors import BlenderError
from .gltf_runner import GltfLocalAcceptanceRunner, write_gltf_local_evidence
from .runner import BlenderRunner, write_local_evidence
from .serialization import canonical_sha256
from .service import BlenderService, BlenderUXResult


def _project_relative(root: Path, value: str, *, field: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        raise SystemExit(f"{field} must be project-relative")
    resolved = (root / candidate).resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise SystemExit(f"{field} escapes the project root")
    return resolved


def _r10_blender_accept(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve(strict=False)
    executable = Path(args.blender).expanduser().resolve(strict=True)
    work = _project_relative(root, args.work_dir, field="--work-dir")
    output = _project_relative(root, args.output, field="--output")
    if work.exists() and any(work.iterdir()):
        raise SystemExit(
            "R10.2 work directory is not empty. Preserve failed evidence/logs first, "
            "then clean only that directory."
        )
    work.mkdir(parents=True, exist_ok=True)
    boundary = BlenderExecutableBoundary(allowed_roots=(executable.parent,), staging_root=work)
    sandbox = ProcessSandbox(work, allowed_executables={"blender", "blender.exe"})
    runner = BlenderRunner(boundary, sandbox, limits=BlenderProcessLimits(wall_time_seconds=args.timeout))
    try:
        evidence = runner.run_capability_probe(executable, source_sha=args.source_sha)
    except (BlenderError, OSError, ValueError) as exc:
        evidence = {
            "schema": "kodepoia.r10.local_blender_evidence",
            "version": 1,
            "source_sha": args.source_sha,
            "status": "fail",
            "blockers": ["acceptance_boundary_error"],
            "runtime": None,
            "command_policy": {"version": "r10.2-v1"},
            "probe": {},
            "artifacts": {},
            "process": {"error_type": type(exc).__name__},
        }
    destination = write_local_evidence(output, evidence, root=root)
    runtime = evidence.get("runtime") if isinstance(evidence.get("runtime"), dict) else {}
    artifacts = evidence.get("artifacts") if isinstance(evidence.get("artifacts"), dict) else {}
    glb = artifacts.get("glb") if isinstance(artifacts.get("glb"), dict) else {}
    summary = {
        "R10_2_local_acceptance": "COMPLETED",
        "status": evidence.get("status"),
        "blockers": evidence.get("blockers"),
        "source_sha": evidence.get("source_sha"),
        "blender_version": runtime.get("version"),
        "glb_sha256": glb.get("sha256"),
        "glb_bytes": glb.get("bytes"),
        "output": str(destination.relative_to(root)),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if evidence.get("status") == "pass" else 2


def _r10_gltf_accept(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve(strict=False)
    blender = Path(args.blender).expanduser().resolve(strict=True)
    godot = Path(args.godot).expanduser().resolve(strict=True)
    work = _project_relative(root, args.work_dir, field="--work-dir")
    output = _project_relative(root, args.output, field="--output")
    if work.exists() and any(work.iterdir()):
        raise SystemExit(
            "R10.10 work directory is not empty. Preserve its JSON/logs/artifacts and stop; "
            "clean only this documented directory before an intentional retry."
        )
    work.mkdir(parents=True, exist_ok=True)
    blender_work = work / "blender"
    blender_work.mkdir(parents=True, exist_ok=False)
    boundary = BlenderExecutableBoundary(allowed_roots=(blender.parent,), staging_root=blender_work)
    sandbox = ProcessSandbox(blender_work, allowed_executables={"blender", "blender.exe"})
    runner = BlenderRunner(
        boundary,
        sandbox,
        limits=BlenderProcessLimits(wall_time_seconds=args.blender_timeout),
    )
    acceptance = GltfLocalAcceptanceRunner(
        runner,
        acceptance_root=work,
        godot_timeout=args.godot_timeout,
    )
    try:
        evidence = acceptance.run(blender, godot, source_sha=args.source_sha)
    except (BlenderError, OSError, RuntimeError, ValueError) as exc:
        evidence = {
            "schema": "kodepoia.r10.gltf_local_acceptance",
            "version": 1,
            "source_sha": args.source_sha,
            "status": "fail",
            "blockers": ["acceptance_boundary_error"],
            "policy_version": "r10.10-local-v1",
            "platform": {},
            "blender": {"error_type": type(exc).__name__},
            "fixtures": {},
            "godot": {},
        }
        evidence["evidence_digest"] = canonical_sha256(evidence)
    destination = write_gltf_local_evidence(output, evidence, root=root)
    blender_info = evidence.get("blender") if isinstance(evidence.get("blender"), dict) else {}
    godot_info = evidence.get("godot") if isinstance(evidence.get("godot"), dict) else {}
    godot_version = godot_info.get("version") if isinstance(godot_info.get("version"), dict) else {}
    fixtures = evidence.get("fixtures") if isinstance(evidence.get("fixtures"), dict) else {}
    static = fixtures.get("static") if isinstance(fixtures.get("static"), dict) else {}
    rigged = fixtures.get("rigged") if isinstance(fixtures.get("rigged"), dict) else {}
    static_artifact = static.get("artifact") if isinstance(static.get("artifact"), dict) else {}
    rigged_artifact = rigged.get("artifact") if isinstance(rigged.get("artifact"), dict) else {}
    summary = {
        "R10_10_local_acceptance": "COMPLETED",
        "status": evidence.get("status"),
        "blockers": evidence.get("blockers"),
        "source_sha": evidence.get("source_sha"),
        "blender_version": blender_info.get("version"),
        "godot_version": godot_version.get("raw"),
        "static_glb_sha256": static_artifact.get("sha256"),
        "static_glb_bytes": static_artifact.get("bytes"),
        "rigged_glb_sha256": rigged_artifact.get("sha256"),
        "rigged_glb_bytes": rigged_artifact.get("bytes"),
        "evidence_digest": evidence.get("evidence_digest"),
        "output": str(destination.relative_to(root)),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if evidence.get("status") == "pass" else 2


def _print_service_result(result: BlenderUXResult) -> int:
    print(json.dumps(result.canonical(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.state.value in {"ready", "missing", "cancelled"} else 2


def _r10_blender_ux(args: argparse.Namespace) -> int:
    service = BlenderService(Path.cwd())
    operation = args.blender_operation
    if operation == "status":
        result = service.status()
    elif operation == "capabilities":
        result = service.capabilities()
    elif operation == "inspect":
        result = service.inspect(args.kind, args.id)
    elif operation == "geometry":
        result = service.validate_geometry(args.id)
    elif operation == "qa":
        result = service.qa(args.id)
    elif operation == "rig":
        result = service.rig(args.id)
    elif operation == "animation":
        result = service.animation(args.id)
    elif operation == "lod":
        result = service.lod(args.id)
    elif operation == "export":
        result = service.export(args.id)
    elif operation == "evidence":
        result = service.evidence(args.id)
    else:  # pragma: no cover - argparse choices prevent this
        raise SystemExit("Unsupported Blender / 3D UX operation")
    return _print_service_result(result)


def _register_ux_leaf(
    subcommands: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    *,
    help_text: str,
) -> argparse.ArgumentParser:
    parser = subcommands.add_parser(name, help=help_text)
    parser.add_argument("--id", required=True, help="stable managed Kodepoia record ID")
    parser.set_defaults(func=_r10_blender_ux, blender_operation=name)
    return parser


def register_blender_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    acceptance = commands.add_parser(
        "r10-blender-accept",
        help="run the REQUIRED R10.2 real Blender 5.2.x local acceptance probe",
    )
    acceptance.add_argument(
        "--blender",
        required=True,
        help="explicit path to a legitimate local Blender 5.2.x executable",
    )
    acceptance.add_argument("--source-sha", required=True, help="exact 40-character R10.2 candidate Git SHA")
    acceptance.add_argument(
        "--work-dir",
        default=".kodepoia/blender/r10_2_work",
        help="empty project-relative R10.2 temporary workspace",
    )
    acceptance.add_argument(
        "--output",
        default=".kodepoia/blender/r10_2_local_acceptance.json",
        help="project-relative canonical evidence JSON",
    )
    acceptance.add_argument("--timeout", type=float, default=180.0)
    acceptance.set_defaults(func=_r10_blender_accept)

    gltf_acceptance = commands.add_parser(
        "r10-gltf-accept",
        help="run the REQUIRED R10.10 real Blender 5.2.x + Godot 4.7 interoperability acceptance",
    )
    gltf_acceptance.add_argument(
        "--blender",
        required=True,
        help="explicit path to a legitimate local Blender 5.2.x executable",
    )
    gltf_acceptance.add_argument(
        "--godot",
        required=True,
        help="explicit path to the accepted local Godot 4.7.x executable",
    )
    gltf_acceptance.add_argument(
        "--source-sha",
        required=True,
        help="exact 40-character R10.10 candidate Git SHA",
    )
    gltf_acceptance.add_argument(
        "--work-dir",
        default=".kodepoia/blender/r10_10_work",
        help="empty project-relative R10.10 temporary workspace",
    )
    gltf_acceptance.add_argument(
        "--output",
        default=".kodepoia/blender/r10_10_local_acceptance.json",
        help="project-relative canonical R10.10 evidence JSON",
    )
    gltf_acceptance.add_argument("--blender-timeout", type=float, default=300.0)
    gltf_acceptance.add_argument("--godot-timeout", type=float, default=300.0)
    gltf_acceptance.set_defaults(func=_r10_gltf_accept)

    blender = commands.add_parser(
        "blender3d",
        help="governed R10.11 Blender / 3D service UX",
    )
    ux = blender.add_subparsers(dest="blender_operation", required=True)

    status = ux.add_parser("status", help="show accepted Blender / 3D runtime status")
    status.set_defaults(func=_r10_blender_ux, blender_operation="status")

    capabilities = ux.add_parser("capabilities", help="show accepted R10 capability inventory")
    capabilities.set_defaults(func=_r10_blender_ux, blender_operation="capabilities")

    inspect = ux.add_parser("inspect", help="inspect one service-managed R10 report")
    inspect.add_argument(
        "--kind",
        required=True,
        choices=("inspect", "qa", "rig", "animation", "lod", "export"),
    )
    inspect.add_argument("--id", required=True, help="stable managed Kodepoia record ID")
    inspect.set_defaults(func=_r10_blender_ux, blender_operation="inspect")

    _register_ux_leaf(ux, "geometry", help_text="validate one service-managed geometry recipe")
    _register_ux_leaf(ux, "qa", help_text="show one mesh/material QA report")
    _register_ux_leaf(ux, "rig", help_text="show one rig/skinning report")
    _register_ux_leaf(ux, "animation", help_text="show one animation/retarget report")
    _register_ux_leaf(ux, "lod", help_text="show one LOD report")
    _register_ux_leaf(ux, "export", help_text="show one GLB/glTF export report")

    evidence = ux.add_parser("evidence", help="show one allowlisted accepted R10 local evidence record")
    evidence.add_argument(
        "--id",
        required=True,
        choices=("r10.2", "r10.6", "r10.7", "r10.10"),
    )
    evidence.set_defaults(func=_r10_blender_ux, blender_operation="evidence")
