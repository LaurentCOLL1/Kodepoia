from __future__ import annotations

from typing import Any

from .errors import BlenderProtocolError
from .qa_contracts import BoundaryPolicy, MeshQAProfile, UVOverlapPolicy
from .serialization import canonical_sha256


def _count(objects: dict[str, Any], section: str, field: str) -> int:
    total = 0
    for record in objects.values():
        data = record.get(section, {})
        if isinstance(data, dict):
            value = data.get(field, 0)
            if isinstance(value, int) and not isinstance(value, bool):
                total += value
    return total


def evaluate_mesh_qa(profile: MeshQAProfile, measurements: dict[str, Any]) -> dict[str, Any]:
    if measurements.get("schema") != "kodepoia.blender.mesh_qa_measurements" or measurements.get("version") != 1:
        raise BlenderProtocolError("Unexpected Mesh QA measurement schema/version")
    if measurements.get("profile_digest") != profile.digest:
        raise BlenderProtocolError("Mesh QA measurement profile digest mismatch")
    if measurements.get("input_blend_sha256") != profile.input_blend_sha256:
        raise BlenderProtocolError("Mesh QA measurement input lineage mismatch")
    objects = measurements.get("objects")
    if not isinstance(objects, dict):
        raise BlenderProtocolError("Mesh QA measurements must contain an objects mapping")

    rules: list[dict[str, Any]] = []

    def add(rule_id: str, state: str, *, value: Any = None, limit: Any = None, applicable: bool = True, reason: str) -> None:
        if state not in {"PASS", "WARN", "BLOCK"}:
            raise BlenderProtocolError("Invalid Mesh QA rule state")
        rules.append({"rule_id": rule_id, "state": state, "applicable": applicable, "value": value, "limit": limit, "reason": reason})

    expected = set(profile.object_ids)
    found = set(objects)
    missing = sorted(expected - found)
    unexpected = sorted(found - expected)
    add("object_resolution", "BLOCK" if missing or unexpected else "PASS", value={"missing": missing, "unexpected": unexpected}, limit={"expected": sorted(expected)}, reason="Every governed object ID must resolve exactly once and no unrequested object may enter the report.")

    source_nonfinite = sum(1 for record in objects.values() if record.get("source", {}).get("finite_coordinates") is not True)
    eval_nonfinite = sum(1 for record in objects.values() if record.get("evaluated", {}).get("finite_coordinates") is not True)
    add("finite_coordinates_source", "BLOCK" if source_nonfinite else "PASS", value=source_nonfinite, limit=0, reason="Source coordinates must be finite.")
    add("finite_coordinates_evaluated", "BLOCK" if eval_nonfinite else "PASS", value=eval_nonfinite, limit=0, reason="Evaluated coordinates must be finite.")

    degenerate = _count(objects, "source", "degenerate_faces") + _count(objects, "evaluated", "degenerate_faces")
    add("degenerate_faces", "BLOCK" if degenerate else "PASS", value=degenerate, limit=0, reason="Faces at or below the profile area tolerance are not production-safe.")
    loose_vertices = max(_count(objects, "source", "loose_vertices"), _count(objects, "evaluated", "loose_vertices"))
    add("loose_vertices", "BLOCK" if loose_vertices > profile.budgets.max_loose_vertices else "PASS", value=loose_vertices, limit=profile.budgets.max_loose_vertices, reason="Loose-vertex count is bounded by the asset profile.")
    loose_edges = max(_count(objects, "source", "loose_edges"), _count(objects, "evaluated", "loose_edges"))
    add("loose_edges", "BLOCK" if loose_edges > profile.budgets.max_loose_edges else "PASS", value=loose_edges, limit=profile.budgets.max_loose_edges, reason="Wire/loose-edge count is bounded by the asset profile.")

    boundary_edges = max(_count(objects, "source", "boundary_edges"), _count(objects, "evaluated", "boundary_edges"))
    if boundary_edges == 0 or profile.boundary_policy is BoundaryPolicy.ALLOW:
        boundary_state = "PASS"
    elif profile.boundary_policy is BoundaryPolicy.WARN:
        boundary_state = "WARN"
    else:
        boundary_state = "BLOCK"
    add("boundary_edges", boundary_state, value=boundary_edges, limit=profile.boundary_policy.value, reason="Boundary edges are interpreted by explicit asset-class policy, never globally.")

    non_manifold = max(_count(objects, "source", "non_manifold_edges"), _count(objects, "evaluated", "non_manifold_edges"))
    add("non_manifold_edges", "BLOCK" if non_manifold > profile.budgets.max_non_manifold_edges else "PASS", value=non_manifold, limit=profile.budgets.max_non_manifold_edges, reason="Branching/non-manifold topology is budgeted explicitly.")
    winding = max(_count(objects, "source", "inconsistent_winding_edges"), _count(objects, "evaluated", "inconsistent_winding_edges"))
    add("face_winding", "BLOCK" if profile.require_consistent_winding and winding else "PASS", value=winding, limit=0 if profile.require_consistent_winding else None, applicable=profile.require_consistent_winding, reason="Manifold shared edges must have consistent face winding when required.")
    duplicates = max(_count(objects, "source", "duplicate_vertex_indicators"), _count(objects, "evaluated", "duplicate_vertex_indicators"))
    add("duplicate_vertex_indicators", "BLOCK" if duplicates > profile.budgets.max_duplicate_vertex_indicators else "PASS", value=duplicates, limit=profile.budgets.max_duplicate_vertex_indicators, reason="Coincident-vertex indicators use the profile's bounded spatial tolerance.")

    object_count = len(objects)
    eval_triangles = _count(objects, "evaluated", "triangles")
    materials = _count(objects, "source", "materials")
    textures = _count(objects, "source", "textures")
    shape_keys = _count(objects, "source", "shape_keys")
    add("object_budget", "BLOCK" if object_count > profile.budgets.max_objects else "PASS", value=object_count, limit=profile.budgets.max_objects, reason="Governed object count must remain within production budget.")
    add("triangle_budget", "BLOCK" if eval_triangles > profile.budgets.max_triangles else "PASS", value=eval_triangles, limit=profile.budgets.max_triangles, reason="Triangle budget uses evaluated geometry because that is what downstream export consumes.")
    add("material_budget", "BLOCK" if materials > profile.budgets.max_materials else "PASS", value=materials, limit=profile.budgets.max_materials, reason="Material-slot budget is measured on source objects.")
    add("texture_budget", "BLOCK" if textures > profile.budgets.max_textures else "PASS", value=textures, limit=profile.budgets.max_textures, reason="Referenced image-texture budget is measured from material node trees.")
    add("shape_key_budget", "BLOCK" if shape_keys > profile.budgets.max_shape_keys else "PASS", value=shape_keys, limit=profile.budgets.max_shape_keys, reason="Shape-key budget is explicit and bounded.")

    uv_layers = max((int(record.get("source", {}).get("uv_layer_count", 0)) for record in objects.values()), default=0)
    add("uv_layer_budget", "BLOCK" if uv_layers > profile.budgets.max_uv_layers else "PASS", value=uv_layers, limit=profile.budgets.max_uv_layers, reason="Per-object UV-layer count is bounded.")
    missing_uv = sum(1 for record in objects.values() if int(record.get("source", {}).get("uv_layer_count", 0)) == 0)
    add("required_uv", "BLOCK" if profile.require_uv and missing_uv else "PASS", value=missing_uv, limit=0 if profile.require_uv else None, applicable=profile.require_uv, reason="UV presence is required only by the explicit profile.")
    zero_uv = max(_count(objects, "source", "zero_area_uv_triangles"), _count(objects, "evaluated", "zero_area_uv_triangles"))
    add("zero_area_uv_triangles", "BLOCK" if zero_uv > profile.budgets.max_zero_area_uv_triangles else "PASS", value=zero_uv, limit=profile.budgets.max_zero_area_uv_triangles, reason="Degenerate UV triangles are bounded independently of geometric degeneracy.")

    overlap_records = [record.get("uv_overlap", {}) for record in objects.values()]
    overlap_measured = all(isinstance(item, dict) and item.get("status") == "measured" for item in overlap_records)
    overlap_pairs = sum(int(item.get("overlap_pairs", 0)) for item in overlap_records if isinstance(item, dict) and isinstance(item.get("overlap_pairs", 0), int))
    if profile.overlap_policy is UVOverlapPolicy.IGNORE:
        overlap_state, overlap_applicable = "PASS", False
    elif not overlap_measured:
        overlap_state, overlap_applicable = ("BLOCK" if profile.overlap_policy is UVOverlapPolicy.BLOCK else "WARN"), True
    elif overlap_pairs:
        overlap_state, overlap_applicable = ("BLOCK" if profile.overlap_policy is UVOverlapPolicy.BLOCK else "WARN"), True
    else:
        overlap_state, overlap_applicable = "PASS", True
    add("uv_overlap", overlap_state, value={"measured": overlap_measured, "pairs": overlap_pairs}, limit=profile.overlap_policy.value, applicable=overlap_applicable, reason="Overlap is never guessed: requested policies fail closed when authoritative measurement is unavailable.")

    transform_nonfinite = sum(1 for record in objects.values() if record.get("transform", {}).get("finite") is not True)
    scale_ratio = max((float(record.get("transform", {}).get("scale_ratio", 0.0)) for record in objects.values()), default=0.0)
    add("transform_finite", "BLOCK" if transform_nonfinite else "PASS", value=transform_nonfinite, limit=0, reason="Object transforms must contain only finite values.")
    add("scale_ratio", "BLOCK" if scale_ratio > profile.budgets.max_scale_ratio else "PASS", value=scale_ratio, limit=profile.budgets.max_scale_ratio, reason="Extreme non-uniform scale is bounded by the profile.")

    tangent_records = [item for record in objects.values() for item in record.get("normal_maps", []) if isinstance(item, dict)]
    tangent_failures = [item for item in tangent_records if item.get("tangent_status") != "pass"]
    add("normal_map_tangents", "BLOCK" if tangent_failures else "PASS", value={"required": len(tangent_records), "failed": len(tangent_failures)}, limit=0, applicable=bool(tangent_records), reason="Every tangent-space normal map requires a valid tangent basis on its declared UV map.")

    block_count = sum(1 for rule in rules if rule["state"] == "BLOCK")
    warn_count = sum(1 for rule in rules if rule["state"] == "WARN")
    pass_count = sum(1 for rule in rules if rule["state"] == "PASS")
    status = "block" if block_count else ("warn" if warn_count else "pass")
    report = {
        "schema": "kodepoia.blender.mesh_qa_report", "version": 1, "profile_id": profile.profile_id,
        "profile_digest": profile.digest, "input_blend_sha256": profile.input_blend_sha256,
        "asset_class": profile.asset_class.value, "status": status,
        "summary": {"pass": pass_count, "warn": warn_count, "block": block_count},
        "rules": rules, "objects": objects,
    }
    report["report_digest"] = canonical_sha256(report)
    return report
