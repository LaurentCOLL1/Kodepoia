from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from kodepoia.blender3d import BlenderExecutableBoundary, BlenderRunner, GeometryRunner, RigRunner, default_known_candidates
from kodepoia.core.sandbox import ProcessSandbox

SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")


def digest_document(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def runtime_evidence(probe: dict[str, Any]) -> tuple[dict[str, object], list[str]]:
    runtime = probe.get("runtime") if isinstance(probe.get("runtime"), dict) else {}
    probe_facts = probe.get("probe") if isinstance(probe.get("probe"), dict) else {}
    evidence: dict[str, object] = {
        "blender_version": runtime.get("version"),
        "platform": runtime.get("platform"),
        "background": probe_facts.get("background"),
        "online_access": probe_facts.get("online_access"),
    }
    blockers: list[str] = []
    version = evidence["blender_version"]
    platform = evidence["platform"]
    if not isinstance(version, str) or not version.startswith("5.2."):
        blockers.append("runtime_version_missing_or_invalid")
    if not isinstance(platform, str) or not platform:
        blockers.append("runtime_platform_missing")
    if evidence["background"] is not True:
        blockers.append("runtime_background_not_confirmed")
    if evidence["online_access"] is not False:
        blockers.append("runtime_offline_not_confirmed")
    return evidence, blockers


def make_runner(blender: Path, staging: Path) -> BlenderRunner:
    boundary = BlenderExecutableBoundary(allowed_roots=(blender.parent,), staging_root=staging)
    sandbox = ProcessSandbox(staging, allowed_executables={"blender", "blender.exe"})
    return BlenderRunner(boundary, sandbox)


def geometry_recipe() -> dict[str, object]:
    return {"version":1,"recipe_id":"r10.6.local.body","units":"METERS","forward_axis":"-Z","up_axis":"Y","steps":[{"operation":"reset_scene","params":{}},{"operation":"create_primitive","params":{"object_id":"body","primitive":"cube","display_name":"R10.6 Local Body"}},{"operation":"recalculate_normals","params":{"object_id":"body"}}]}


def rig_profile(input_sha: str) -> dict[str, object]:
    return {"version":1,"rig_id":"r10.6.local.rig","armature_id":"local_armature","mode":"create","input_blend_sha256":input_sha,"bones":[{"bone_id":"root","display_name":"Root","parent_id":None,"head":[0.0,-1.0,0.0],"tail":[0.0,1.0,0.0],"deform":True,"connected":False}],"meshes":[{"mesh_id":"body","strategy":"nearest_deform_bone","weights":[]}],"influence":{"max_influences":4,"allow_extended_influences":False,"normalization_tolerance":0.0001,"tiny_weight_threshold":0.00001,"require_deformation_probe":True}}


def resolve_blender(explicit: str | None) -> Path:
    candidates = [Path(explicit)] if explicit else list(default_known_candidates())
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve(strict=True)
    raise SystemExit("Blender 5.2 executable not found; pass --blender with the exact blender.exe path")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded local Blender 5.2 acceptance for Kodepoia R10.6")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--blender")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not SOURCE_RE.fullmatch(args.source_sha):
        raise SystemExit("--source-sha must be the exact lowercase 40-character candidate SHA")
    blender = resolve_blender(args.blender)
    output = Path(args.output).resolve(strict=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    with tempfile.TemporaryDirectory(prefix="kodepoia-r10-6-") as temp:
        root = Path(temp)
        probe_dir, geometry_dir, rig_dir = root / "probe", root / "geometry", root / "rig"
        probe = make_runner(blender, probe_dir).run_capability_probe(blender, source_sha=args.source_sha)
        if probe.get("status") != "pass": blockers.append("runtime_probe_failed")
        runtime, runtime_blockers = runtime_evidence(probe)
        blockers.extend(runtime_blockers)
        geometry_runner = GeometryRunner(make_runner(blender, geometry_dir))
        geometry = geometry_runner.run(blender, geometry_recipe(), source_sha=args.source_sha)
        if geometry.get("status") != "pass" or not isinstance(geometry.get("artifact"), dict): blockers.append("geometry_fixture_failed")
        artifact = geometry.get("artifact") if isinstance(geometry.get("artifact"), dict) else {}
        geometry_path = geometry_dir / "geometry_output.blend"
        input_sha = str(artifact.get("sha256", ""))
        rig_manifest: dict[str, object] = {}
        if not blockers:
            rig_runner = RigRunner(make_runner(blender, rig_dir), input_root=geometry_dir)
            rig_manifest = rig_runner.run(blender, rig_profile(input_sha), source_sha=args.source_sha, input_blend=geometry_path)
            if rig_manifest.get("status") != "pass": blockers.append("rig_probe_failed")
            report = rig_manifest.get("report")
            if not isinstance(report, dict): blockers.append("rig_report_missing")
            else:
                probe_rule = next((item for item in report.get("rules", []) if isinstance(item, dict) and item.get("rule_id") == "deformation_probe"), None)
                if not isinstance(probe_rule, dict) or probe_rule.get("state") != "PASS": blockers.append("deformation_probe_failed")
        evidence: dict[str, object] = {"schema":"kodepoia.r10_6_local_acceptance","version":1,"source_sha":args.source_sha,"status":"pass" if not blockers else "fail","blockers":sorted(set(blockers)),"runtime":runtime,"fixture":{"recipe_id":"r10.6.local.body","blend_sha256":input_sha,"geometry_status":geometry.get("status")},"rig":{"rig_id":"r10.6.local.rig","status":rig_manifest.get("status"),"profile_digest":rig_manifest.get("profile_digest"),"report_digest":rig_manifest.get("report_digest"),"artifact":rig_manifest.get("artifact")}}
        evidence["evidence_digest"] = digest_document(evidence)
        output.write_text(json.dumps(evidence, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0 if not blockers else 17


if __name__ == "__main__":
    raise SystemExit(main())
