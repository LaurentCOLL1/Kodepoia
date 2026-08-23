from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

from kodepoia.blender3d import (
    AnimationRunner,
    BlenderExecutableBoundary,
    BlenderRunner,
    GeometryRunner,
    RigRunner,
    default_known_candidates,
)
from kodepoia.core.sandbox import ProcessSandbox

SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")


def digest_document(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def make_runner(blender: Path, staging: Path) -> BlenderRunner:
    boundary = BlenderExecutableBoundary(allowed_roots=(blender.parent,), staging_root=staging)
    sandbox = ProcessSandbox(staging, allowed_executables={"blender", "blender.exe"})
    return BlenderRunner(boundary, sandbox)


def geometry_recipe() -> dict[str, object]:
    return {
        "version": 1,
        "recipe_id": "r10.7.local.bodies",
        "units": "METERS",
        "forward_axis": "-Z",
        "up_axis": "Y",
        "steps": [
            {"operation": "reset_scene", "params": {}},
            {"operation": "create_primitive", "params": {"object_id": "source_body", "primitive": "cube", "display_name": "R10.7 Source Body"}},
            {"operation": "create_primitive", "params": {"object_id": "target_body", "primitive": "cube", "display_name": "R10.7 Target Body"}},
            {"operation": "transform", "params": {"object_id": "target_body", "location": [3.0, 0.0, 0.0]}},
            {"operation": "recalculate_normals", "params": {"object_id": "source_body"}},
            {"operation": "recalculate_normals", "params": {"object_id": "target_body"}},
        ],
    }


def rig_profile(input_sha: str, *, rig_id: str, armature_id: str, mesh_id: str) -> dict[str, object]:
    return {
        "version": 1,
        "rig_id": rig_id,
        "armature_id": armature_id,
        "mode": "create",
        "input_blend_sha256": input_sha,
        "bones": [
            {
                "bone_id": "root",
                "display_name": "Root",
                "parent_id": None,
                "head": [0.0, -1.0, 0.0],
                "tail": [0.0, 1.0, 0.0],
                "deform": True,
                "connected": False,
            }
        ],
        "meshes": [{"mesh_id": mesh_id, "strategy": "nearest_deform_bone", "weights": []}],
        "influence": {
            "max_influences": 4,
            "allow_extended_influences": False,
            "normalization_tolerance": 0.0001,
            "tiny_weight_threshold": 0.00001,
            "require_deformation_probe": True,
        },
    }


def semantic_profile(input_sha: str, *, rig_id: str, armature_id: str) -> dict[str, object]:
    return {
        "rig_id": rig_id,
        "armature_id": armature_id,
        "input_blend_sha256": input_sha,
        "bones": [{"bone_id": "root", "actual_name": "root", "parent_id": None, "deform": True}],
    }


def animation_recipe(input_sha: str) -> dict[str, object]:
    return {
        "version": 1,
        "recipe_id": "r10.7.local.retarget",
        "input_blend_sha256": input_sha,
        "source_rig": semantic_profile(input_sha, rig_id="r10.7.local.source", armature_id="source_armature"),
        "target_rig": semantic_profile(input_sha, rig_id="r10.7.local.target", armature_id="target_armature"),
        "clip": {
            "clip_id": "r10.7.local.walk",
            "fps": 30.0,
            "frame_start": 1.0,
            "frame_end": 10.0,
            "loop": True,
            "root_motion": "keep",
            "channels": [
                {
                    "bone_id": "root",
                    "path": "location",
                    "keys": [
                        {"frame": 1.0, "value": [0.0, 0.0, 0.0]},
                        {"frame": 10.0, "value": [0.5, 0.0, 0.0]},
                    ],
                },
                {
                    "bone_id": "root",
                    "path": "rotation_quaternion",
                    "keys": [
                        {"frame": 1.0, "value": [1.0, 0.0, 0.0, 0.0]},
                        {"frame": 10.0, "value": [0.996194698, 0.0, 0.0, 0.087155743]},
                    ],
                },
            ],
        },
        "mappings": [
            {
                "source_bone_id": "root",
                "target_bone_id": "root",
                "copy_translation": True,
                "copy_rotation": True,
                "copy_scale": False,
            }
        ],
        "required_target_bones": ["root"],
        "translation_scale": 1.0,
        "max_keys": 32,
    }


def resolve_blender(explicit: str | None) -> Path:
    candidates = [Path(explicit)] if explicit else list(default_known_candidates())
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve(strict=True)
    raise SystemExit("Blender 5.2 executable not found; pass --blender with the exact blender.exe path")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded local Blender 5.2 animation/NLA acceptance for Kodepoia R10.7")
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

    with tempfile.TemporaryDirectory(prefix="kodepoia-r10-7-") as temp:
        root = Path(temp)
        probe_dir = root / "probe"
        geometry_dir = root / "geometry"
        source_rig_dir = root / "source_rig"
        target_rig_dir = root / "target_rig"
        animation_dir = root / "animation"

        probe = make_runner(blender, probe_dir).run_capability_probe(blender, source_sha=args.source_sha)
        if probe.get("status") != "pass":
            blockers.append("runtime_probe_failed")

        geometry = GeometryRunner(make_runner(blender, geometry_dir)).run(blender, geometry_recipe(), source_sha=args.source_sha)
        geometry_artifact = geometry.get("artifact") if isinstance(geometry.get("artifact"), dict) else {}
        geometry_sha = str(geometry_artifact.get("sha256", ""))
        geometry_path = geometry_dir / "geometry_output.blend"
        if geometry.get("status") != "pass" or not geometry_sha:
            blockers.append("geometry_fixture_failed")

        source_rig: dict[str, object] = {}
        source_rig_sha = ""
        if not blockers:
            source_rig_runner = RigRunner(make_runner(blender, source_rig_dir), input_root=geometry_dir)
            source_rig = source_rig_runner.run(
                blender,
                rig_profile(geometry_sha, rig_id="r10.7.local.source", armature_id="source_armature", mesh_id="source_body"),
                source_sha=args.source_sha,
                input_blend=geometry_path,
            )
            source_artifact = source_rig.get("artifact") if isinstance(source_rig.get("artifact"), dict) else {}
            source_rig_sha = str(source_artifact.get("sha256", ""))
            if source_rig.get("status") != "pass" or not source_rig_sha:
                blockers.append("source_rig_fixture_failed")

        target_rig: dict[str, object] = {}
        target_rig_sha = ""
        target_rig_path = source_rig_dir / "rig_output.blend"
        if not blockers:
            target_rig_runner = RigRunner(make_runner(blender, target_rig_dir), input_root=source_rig_dir)
            target_rig = target_rig_runner.run(
                blender,
                rig_profile(source_rig_sha, rig_id="r10.7.local.target", armature_id="target_armature", mesh_id="target_body"),
                source_sha=args.source_sha,
                input_blend=target_rig_path,
            )
            target_artifact = target_rig.get("artifact") if isinstance(target_rig.get("artifact"), dict) else {}
            target_rig_sha = str(target_artifact.get("sha256", ""))
            if target_rig.get("status") != "pass" or not target_rig_sha:
                blockers.append("target_rig_fixture_failed")

        animation: dict[str, object] = {}
        animation_path = target_rig_dir / "rig_output.blend"
        if not blockers:
            animation_runner = AnimationRunner(make_runner(blender, animation_dir), input_root=target_rig_dir)
            animation = animation_runner.run(
                blender,
                animation_recipe(target_rig_sha),
                source_sha=args.source_sha,
                input_blend=animation_path,
            )
            if animation.get("status") != "pass":
                blockers.append("animation_retarget_failed")

        runtime = probe.get("runtime") if isinstance(probe.get("runtime"), dict) else {}
        probe_facts = probe.get("probe") if isinstance(probe.get("probe"), dict) else {}
        blender_version = runtime.get("version")
        platform_name = runtime.get("platform")
        background = probe_facts.get("background")
        online_access = probe_facts.get("online_access")
        if not isinstance(blender_version, str) or not blender_version.startswith("5.2."):
            blockers.append("runtime_version_unconfirmed")
        if not isinstance(platform_name, str) or not platform_name:
            blockers.append("runtime_platform_unconfirmed")
        if background is not True:
            blockers.append("background_mode_unconfirmed")
        if online_access is not False:
            blockers.append("offline_mode_unconfirmed")

        report = animation.get("report") if isinstance(animation.get("report"), dict) else {}
        rules = report.get("rules") if isinstance(report.get("rules"), list) else []
        required_rules = {"mapping_coverage", "rest_direction_compatibility", "rest_length_compatibility", "key_budget", "nla_track_count", "nla_strip_count", "root_motion_policy"}
        passed_rules = {str(item.get("rule_id")) for item in rules if isinstance(item, dict) and item.get("state") == "PASS"}
        if not required_rules <= passed_rules:
            blockers.append("animation_rules_incomplete")

        animation_artifact = animation.get("artifact") if isinstance(animation.get("artifact"), dict) else {}
        evidence: dict[str, object] = {
            "schema": "kodepoia.r10_7_local_acceptance",
            "version": 1,
            "source_sha": args.source_sha,
            "status": "pass" if not blockers else "fail",
            "blockers": sorted(set(blockers)),
            "runtime": {
                "blender_version": blender_version,
                "platform": platform_name,
                "background": background,
                "online_access": online_access,
            },
            "geometry": {"status": geometry.get("status"), "artifact_sha256": geometry_sha},
            "source_rig": {"status": source_rig.get("status"), "artifact_sha256": source_rig_sha},
            "target_rig": {"status": target_rig.get("status"), "artifact_sha256": target_rig_sha},
            "animation": {
                "status": animation.get("status"),
                "recipe_digest": animation.get("recipe_digest"),
                "report_digest": animation.get("report_digest"),
                "artifact": animation_artifact,
                "passed_rules": sorted(passed_rules),
            },
        }
        evidence["evidence_digest"] = digest_document(evidence)
        output.write_text(json.dumps(evidence, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0 if not blockers else 17


if __name__ == "__main__":
    raise SystemExit(main())
