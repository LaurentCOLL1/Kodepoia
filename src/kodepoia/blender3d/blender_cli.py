from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox

from .boundary import BlenderExecutableBoundary
from .contracts import BlenderProcessLimits
from .errors import BlenderError
from .runner import BlenderRunner, write_local_evidence


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
            "R10.2 work directory is not empty. Preserve failed evidence/logs first, then clean only that directory."
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


def register_blender_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    acceptance = commands.add_parser(
        "r10-blender-accept",
        help="run the REQUIRED R10.2 real Blender 5.2.x local acceptance probe",
    )
    acceptance.add_argument("--blender", required=True, help="explicit path to a legitimate local Blender 5.2.x executable")
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
