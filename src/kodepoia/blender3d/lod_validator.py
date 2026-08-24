from __future__ import annotations

import math
from typing import Any

from .errors import BlenderProtocolError
from .lod_contracts import LODAssetMode, LODProfile, ShapeKeyLODPolicy
from .serialization import canonical_sha256


def _names(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise BlenderProtocolError("LOD inventory name list is malformed")
    return tuple(value)


def _metric(record: dict[str, Any], name: str) -> float:
    value = record.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BlenderProtocolError(f"LOD metric {name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise BlenderProtocolError(f"LOD metric {name} must be finite")
    return result


def _extent(record: dict[str, Any]) -> tuple[float, float, float]:
    value = record.get("bounds_extent")
    if not isinstance(value, list) or len(value) != 3:
        raise BlenderProtocolError("bounds_extent must contain three numbers")
    result = tuple(float(item) for item in value)
    if not all(math.isfinite(item) and item >= 0.0 for item in result):
        raise BlenderProtocolError("bounds_extent contains an invalid value")
    return result


def _relative_error(current: float, reference: float) -> float:
    if abs(reference) <= 1e-12:
        return 0.0 if abs(current) <= 1e-12 else 1.0
    return abs(current - reference) / abs(reference)


def evaluate_lod_measurements(profile: LODProfile, measurements: dict[str, Any]) -> dict[str, Any]:
    if measurements.get("schema") != "kodepoia.blender.lod_measurements" or measurements.get("version") != 1:
        raise BlenderProtocolError("Unexpected LOD measurement schema/version")
    if measurements.get("profile_digest") != profile.digest:
        raise BlenderProtocolError("LOD measurement profile digest mismatch")
    if measurements.get("input_blend_sha256") != profile.input_blend_sha256:
        raise BlenderProtocolError("LOD measurement input lineage mismatch")
    source = measurements.get("source")
    tiers = measurements.get("tiers")
    if not isinstance(source, dict) or not isinstance(tiers, dict):
        raise BlenderProtocolError("LOD measurements require source/tiers objects")

    rules: list[dict[str, Any]] = []

    def add(rule_id: str, state: str, value: Any, limit: Any, reason: str, *, tier_id: str | None = None) -> None:
        if state not in {"PASS", "WARN", "BLOCK"}:
            raise BlenderProtocolError("invalid LOD rule state")
        record = {"rule_id": rule_id, "state": state, "value": value, "limit": limit, "reason": reason}
        if tier_id is not None:
            record["tier_id"] = tier_id
        rules.append(record)

    source_triangles = int(_metric(source, "triangle_count"))
    if source_triangles <= 0:
        raise BlenderProtocolError("source triangle_count must be positive")
    source_materials = _names(source.get("material_slots"))
    source_uvs = _names(source.get("uv_layers"))
    source_shapes = _names(source.get("shape_keys"))
    source_groups = _names(source.get("vertex_groups"))
    source_extent = _extent(source)
    source_area = _metric(source, "surface_area")
    source_invalid_normals = int(_metric(source, "invalid_normal_count"))

    expected_tiers = {item.tier_id: item for item in profile.tiers}
    actual_ids = set(tiers)
    add("tier_identity", "BLOCK" if actual_ids != set(expected_tiers) else "PASS", {"missing": sorted(set(expected_tiers) - actual_ids), "unexpected": sorted(actual_ids - set(expected_tiers))}, sorted(expected_tiers), "LOD tier identities must match the governed profile exactly.")

    if profile.preservation.shape_keys is ShapeKeyLODPolicy.BLOCK_IF_PRESENT:
        add("source_shape_key_policy", "BLOCK" if source_shapes else "PASS", list(source_shapes), [], "Topology-changing decimation is blocked when source Shape Keys are present.")
    else:
        add("source_shape_key_policy", "WARN" if source_shapes else "PASS", list(source_shapes), "explicit_drop", "Shape Key removal is visible and requires explicit drop policy.")

    previous_triangles = source_triangles
    for tier in profile.tiers:
        record = tiers.get(tier.tier_id)
        if not isinstance(record, dict):
            continue
        triangles = int(_metric(record, "triangle_count"))
        material_slots = _names(record.get("material_slots"))
        uv_layers = _names(record.get("uv_layers"))
        shape_keys = _names(record.get("shape_keys"))
        vertex_groups = _names(record.get("vertex_groups"))
        extent = _extent(record)
        area = _metric(record, "surface_area")
        invalid_normals = int(_metric(record, "invalid_normal_count"))
        zero_weight = int(_metric(record, "zero_weight_vertices"))
        max_influences = int(_metric(record, "max_influences"))
        weight_error = _metric(record, "max_weight_sum_error")
        actual_ratio = triangles / source_triangles

        add("triangle_budget", "BLOCK" if not tier.min_triangles <= triangles <= tier.max_triangles else "PASS", triangles, [tier.min_triangles, tier.max_triangles], "Every tier must stay inside its explicit triangle budget.", tier_id=tier.tier_id)
        add("ratio_target", "BLOCK" if abs(actual_ratio - tier.ratio) > profile.ratio_tolerance else "PASS", actual_ratio, {"target": tier.ratio, "tolerance": profile.ratio_tolerance}, "Observed triangle ratio must stay within the governed tolerance.", tier_id=tier.tier_id)
        add("monotonic_reduction", "BLOCK" if triangles >= previous_triangles else "PASS", triangles, f"<{previous_triangles}", "Each successive tier must reduce triangle count.", tier_id=tier.tier_id)
        previous_triangles = triangles

        if profile.preservation.preserve_material_slots:
            add("material_slot_identity", "BLOCK" if material_slots != source_materials else "PASS", list(material_slots), list(source_materials), "Material slot order and identity must survive LOD generation.", tier_id=tier.tier_id)
        if profile.preservation.preserve_uv_layers:
            add("uv_layer_identity", "BLOCK" if uv_layers != source_uvs else "PASS", list(uv_layers), list(source_uvs), "UV layer identity must survive LOD generation.", tier_id=tier.tier_id)
        if profile.preservation.preserve_normals:
            add("normal_validity", "BLOCK" if invalid_normals or source_invalid_normals else "PASS", invalid_normals, 0, "LOD output must not introduce invalid normals.", tier_id=tier.tier_id)

        if profile.preservation.shape_keys is ShapeKeyLODPolicy.BLOCK_IF_PRESENT:
            add("shape_key_inventory", "BLOCK" if shape_keys else "PASS", list(shape_keys), [], "Accepted topology-changing LOD tiers may not carry incompatible Shape Keys.", tier_id=tier.tier_id)
        else:
            add("shape_key_inventory", "BLOCK" if shape_keys else ("WARN" if source_shapes else "PASS"), list(shape_keys), [], "Explicit Shape Key drop must leave no stale keys on the derived mesh.", tier_id=tier.tier_id)

        extent_error = max((_relative_error(current, reference) for current, reference in zip(extent, source_extent)), default=0.0)
        add("extent_preservation", "BLOCK" if extent_error > profile.preservation.max_extent_relative_error else "PASS", extent_error, profile.preservation.max_extent_relative_error, "Axis-aligned extent drift is a bounded silhouette proxy.", tier_id=tier.tier_id)
        area_error = _relative_error(area, source_area)
        add("surface_area_preservation", "BLOCK" if area_error > profile.preservation.max_surface_area_relative_error else "PASS", area_error, profile.preservation.max_surface_area_relative_error, "Surface-area drift is a bounded geometric preservation proxy.", tier_id=tier.tier_id)

        if profile.asset_mode is LODAssetMode.SKINNED:
            missing_groups = sorted(set(profile.preservation.required_vertex_groups) - set(vertex_groups))
            add("skin_group_identity", "BLOCK" if missing_groups else "PASS", missing_groups, [], "All governed deform vertex groups must survive decimation.", tier_id=tier.tier_id)
            add("zero_weight_vertices", "BLOCK" if zero_weight else "PASS", zero_weight, 0, "Skinned LOD tiers may not introduce unweighted vertices.", tier_id=tier.tier_id)
            add("weight_normalization", "BLOCK" if weight_error > profile.preservation.max_weight_sum_error else "PASS", weight_error, profile.preservation.max_weight_sum_error, "Skinned LOD weights must remain normalized within tolerance.", tier_id=tier.tier_id)
            add("influence_budget", "BLOCK" if max_influences > profile.preservation.max_influences else "PASS", max_influences, profile.preservation.max_influences, "Skinned LOD influence count must remain within the governed budget.", tier_id=tier.tier_id)
        else:
            add("static_skin_absence", "BLOCK" if vertex_groups else "PASS", list(vertex_groups), [], "Static LOD fixtures must not silently gain skin groups.", tier_id=tier.tier_id)

    block_count = sum(item["state"] == "BLOCK" for item in rules)
    warn_count = sum(item["state"] == "WARN" for item in rules)
    report: dict[str, Any] = {"schema": "kodepoia.blender.lod_report", "version": 1, "profile_id": profile.profile_id, "profile_digest": profile.digest, "input_blend_sha256": profile.input_blend_sha256, "status": "block" if block_count else ("warn" if warn_count else "pass"), "summary": {"pass": sum(item["state"] == "PASS" for item in rules), "warn": warn_count, "block": block_count}, "rules": rules, "source": source, "tiers": tiers}
    report["report_digest"] = canonical_sha256(report)
    return report
