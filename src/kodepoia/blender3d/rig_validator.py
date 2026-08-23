from __future__ import annotations

from typing import Any

from .errors import BlenderProtocolError
from .rig_contracts import RigProfile
from .serialization import canonical_sha256


def evaluate_rig_measurements(profile: RigProfile, measurements: dict[str, Any]) -> dict[str, Any]:
    if measurements.get("schema") != "kodepoia.blender.rig_measurements" or measurements.get("version") != 1:
        raise BlenderProtocolError("Unexpected rig measurement schema/version")
    if measurements.get("profile_digest") != profile.digest:
        raise BlenderProtocolError("Rig measurement profile digest mismatch")
    if measurements.get("input_blend_sha256") != profile.input_blend_sha256:
        raise BlenderProtocolError("Rig measurement input lineage mismatch")
    armature = measurements.get("armature")
    meshes = measurements.get("meshes")
    if not isinstance(armature, dict) or not isinstance(meshes, dict):
        raise BlenderProtocolError("Rig measurements require armature/meshes objects")

    rules: list[dict[str, Any]] = []
    def add(rule_id: str, state: str, value: Any, limit: Any, reason: str, *, applicable: bool = True) -> None:
        if state not in {"PASS", "WARN", "BLOCK"}:
            raise BlenderProtocolError("Invalid rig rule state")
        rules.append({"rule_id": rule_id, "state": state, "applicable": applicable, "value": value, "limit": limit, "reason": reason})

    expected_bones = {bone.bone_id: bone for bone in profile.bones}
    raw_bones = armature.get("bones")
    if not isinstance(raw_bones, list):
        raw_bones = []
    actual_bones = {str(item.get("bone_id")): item for item in raw_bones if isinstance(item, dict) and isinstance(item.get("bone_id"), str)}
    missing = sorted(set(expected_bones) - set(actual_bones))
    unexpected = sorted(set(actual_bones) - set(expected_bones))
    add("bone_identity", "BLOCK" if missing or unexpected else "PASS", {"missing": missing, "unexpected": unexpected}, sorted(expected_bones), "Stable semantic bone IDs must match the governed profile exactly.")
    hierarchy_errors: list[str] = []
    deform_errors: list[str] = []
    for bone_id, expected in expected_bones.items():
        actual = actual_bones.get(bone_id)
        if actual is None:
            continue
        if actual.get("parent_id") != expected.parent_id:
            hierarchy_errors.append(bone_id)
        if actual.get("deform") is not expected.deform:
            deform_errors.append(bone_id)
    add("bone_hierarchy", "BLOCK" if hierarchy_errors else "PASS", sorted(hierarchy_errors), [], "Bone parent relationships must match the canonical rest hierarchy.")
    add("deform_set", "BLOCK" if deform_errors else "PASS", sorted(deform_errors), list(profile.deform_bone_ids), "Exporter-facing deform/control distinction must match the profile.")

    expected_meshes = {mesh.mesh_id for mesh in profile.meshes}
    missing_meshes = sorted(expected_meshes - set(meshes))
    unexpected_meshes = sorted(set(meshes) - expected_meshes)
    add("mesh_identity", "BLOCK" if missing_meshes or unexpected_meshes else "PASS", {"missing": missing_meshes, "unexpected": unexpected_meshes}, sorted(expected_meshes), "Every governed skinned mesh must resolve exactly once.")

    totals = {"zero": 0, "invalid": 0, "control": 0, "bad_sum": 0, "over": 0, "tiny": 0, "orphan": 0, "unbound_modifier": 0, "unbound_parent": 0, "probe_fail": 0}
    max_influences = 0
    for mesh_id in sorted(expected_meshes):
        record = meshes.get(mesh_id)
        if not isinstance(record, dict):
            continue
        totals["zero"] += int(record.get("zero_weight_vertices", 0))
        totals["invalid"] += int(record.get("invalid_bone_references", 0))
        totals["control"] += int(record.get("control_bone_references", 0))
        totals["bad_sum"] += int(record.get("sum_outside_tolerance", 0))
        totals["over"] += int(record.get("influence_over_budget", 0))
        totals["tiny"] += int(record.get("tiny_weight_count", 0))
        totals["orphan"] += int(record.get("orphan_vertex_groups", 0))
        max_influences = max(max_influences, int(record.get("max_influences", 0)))
        if record.get("armature_modifier_bound") is not True:
            totals["unbound_modifier"] += 1
        if record.get("parent_bound") is not True:
            totals["unbound_parent"] += 1
        probe = record.get("deformation_probe", {})
        if profile.influence.require_deformation_probe and (not isinstance(probe, dict) or probe.get("status") != "pass"):
            totals["probe_fail"] += 1

    add("zero_weight_vertices", "BLOCK" if totals["zero"] else "PASS", totals["zero"], 0, "Every vertex must receive at least one positive deform-bone influence.")
    add("invalid_bone_references", "BLOCK" if totals["invalid"] else "PASS", totals["invalid"], 0, "Weights may reference only governed semantic bones.")
    add("control_bone_weights", "BLOCK" if totals["control"] else "PASS", totals["control"], 0, "Control-only bones may not carry deformation weights.")
    add("weight_normalization", "BLOCK" if totals["bad_sum"] else "PASS", totals["bad_sum"], profile.influence.normalization_tolerance, "Per-vertex deform weights must sum to one within tolerance.")
    add("influence_budget", "BLOCK" if totals["over"] else "PASS", {"over_vertices": totals["over"], "max_observed": max_influences}, profile.influence.max_influences, "Per-vertex influence count must respect the target profile; four is the default Godot-compatible budget.")
    add("tiny_weights", "WARN" if totals["tiny"] else "PASS", totals["tiny"], profile.influence.tiny_weight_threshold, "Positive weights below the pruning threshold are reported; generated explicit weights are pruned before binding.")
    add("orphan_vertex_groups", "WARN" if totals["orphan"] else "PASS", totals["orphan"], 0, "Vertex groups not mapped to governed rig bones are reported explicitly.")
    add("armature_modifier_binding", "BLOCK" if totals["unbound_modifier"] else "PASS", totals["unbound_modifier"], 0, "Each mesh must be bound to the governed armature modifier.")
    add("armature_parent_binding", "BLOCK" if totals["unbound_parent"] else "PASS", totals["unbound_parent"], 0, "Each governed skinned mesh must be parented to the governed armature with preserved world transform.")
    add("deformation_probe", "BLOCK" if totals["probe_fail"] else "PASS", totals["probe_fail"], 0, "A bounded deterministic pose probe must move weighted geometry when the profile requires deformation evidence.", applicable=profile.influence.require_deformation_probe)

    block_count = sum(1 for item in rules if item["state"] == "BLOCK")
    warn_count = sum(1 for item in rules if item["state"] == "WARN")
    report = {"schema": "kodepoia.blender.rig_report", "version": 1, "rig_id": profile.rig_id, "profile_digest": profile.digest, "input_blend_sha256": profile.input_blend_sha256, "status": "block" if block_count else ("warn" if warn_count else "pass"), "summary": {"pass": sum(1 for item in rules if item["state"] == "PASS"), "warn": warn_count, "block": block_count}, "rules": rules, "armature": armature, "meshes": meshes}
    report["report_digest"] = canonical_sha256(report)
    return report
