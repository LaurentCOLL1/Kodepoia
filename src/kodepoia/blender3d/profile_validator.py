from __future__ import annotations

from typing import Any

from kodepoia.assets.contracts import AssetKind, AssetRevision, AssetStatus

from .animation_contracts import RigSemanticProfile
from .errors import BlenderProtocolError
from .profile_contracts import OrganicAssetProfile, ProfilePieceType
from .rig_contracts import RigProfile
from .serialization import canonical_sha256


def evaluate_organic_profile(
    profile: OrganicAssetProfile,
    inventory: dict[str, Any],
    *,
    asset_revision: AssetRevision,
    rig_profile: RigProfile,
    semantic_profile: RigSemanticProfile,
) -> dict[str, Any]:
    if inventory.get("schema") != "kodepoia.blender.organic_profile_inventory" or inventory.get("version") != 1:
        raise BlenderProtocolError("Unexpected organic profile inventory schema/version")
    if inventory.get("profile_digest") != profile.digest:
        raise BlenderProtocolError("Organic profile inventory digest mismatch")
    if inventory.get("asset_revision_id") != profile.asset.revision_id:
        raise BlenderProtocolError("Organic profile inventory asset revision mismatch")

    pieces_raw = inventory.get("pieces")
    slots_raw = inventory.get("material_slots")
    shapes_raw = inventory.get("shape_keys")
    if not isinstance(pieces_raw, list) or not isinstance(slots_raw, list) or not isinstance(shapes_raw, list):
        raise BlenderProtocolError("Organic profile inventory requires pieces/material_slots/shape_keys arrays")

    rules: list[dict[str, Any]] = []

    def add(rule_id: str, state: str, value: Any, limit: Any, reason: str) -> None:
        if state not in {"PASS", "WARN", "BLOCK"}:
            raise BlenderProtocolError("Invalid organic profile rule state")
        rules.append({"rule_id": rule_id, "state": state, "value": value, "limit": limit, "reason": reason})

    asset_identity_ok = (
        str(asset_revision.asset_id) == profile.asset.asset_id
        and str(asset_revision.revision_id) == profile.asset.revision_id
        and asset_revision.content_sha256 == profile.asset.content_sha256
    )
    add(
        "r8_asset_revision_binding",
        "PASS" if asset_identity_ok else "BLOCK",
        {
            "asset_id": str(asset_revision.asset_id),
            "revision_id": str(asset_revision.revision_id),
            "content_sha256": asset_revision.content_sha256,
        },
        profile.asset.to_dict(),
        "The organic profile must bind the exact canonical R8 asset revision; license authority remains in R8 governance.",
    )
    governance_ready = asset_revision.kind is AssetKind.MODEL_3D and bool(asset_revision.provenance) and asset_revision.status is AssetStatus.READY
    add(
        "r8_governance_readiness",
        "PASS" if governance_ready else "BLOCK",
        {
            "kind": asset_revision.kind.value,
            "provenance_count": len(asset_revision.provenance),
            "status": asset_revision.status.value,
        },
        {"kind": "model_3d", "provenance_min": 1, "status": "ready"},
        "Profile pipelines never replace R8 provenance/license governance; the bound model revision must be READY with provenance.",
    )

    rig_ok = (
        rig_profile.rig_id == profile.rig_id
        and rig_profile.armature_id == profile.armature_id
        and rig_profile.digest == profile.rig_profile_digest
    )
    add(
        "r10_6_rig_compatibility",
        "PASS" if rig_ok else "BLOCK",
        {"rig_id": rig_profile.rig_id, "armature_id": rig_profile.armature_id, "digest": rig_profile.digest},
        {"rig_id": profile.rig_id, "armature_id": profile.armature_id, "digest": profile.rig_profile_digest},
        "The profile must bind the exact governed R10.6 rig contract.",
    )

    semantic_ok = (
        semantic_profile.rig_id == profile.rig_id
        and semantic_profile.armature_id == profile.armature_id
        and semantic_profile.digest == profile.rig_semantic_digest
    )
    add(
        "r10_7_semantic_rig_compatibility",
        "PASS" if semantic_ok else "BLOCK",
        {"rig_id": semantic_profile.rig_id, "armature_id": semantic_profile.armature_id, "digest": semantic_profile.digest},
        {"rig_id": profile.rig_id, "armature_id": profile.armature_id, "digest": profile.rig_semantic_digest},
        "Animation/retarget compatibility is bound to the exact R10.7 semantic rig identity.",
    )

    rig_deform = set(rig_profile.deform_bone_ids)
    semantic_by_id = {bone.bone_id: bone for bone in semantic_profile.bones}
    required_deform_errors = sorted(
        bone_id for bone_id in profile.required_deform_bones
        if bone_id not in rig_deform or bone_id not in semantic_by_id or not semantic_by_id[bone_id].deform
    )
    add(
        "required_deform_bones",
        "BLOCK" if required_deform_errors else "PASS",
        required_deform_errors,
        [],
        "Required deform bones must exist as deforming semantic bones in both the R10.6 and R10.7 contracts.",
    )
    animation_missing = sorted(bone_id for bone_id in profile.animation_bones if bone_id not in semantic_by_id)
    add(
        "animation_bone_coverage",
        "BLOCK" if animation_missing else "PASS",
        animation_missing,
        [],
        "Every declared animation bone must resolve in the governed R10.7 semantic rig; no fuzzy matching is allowed.",
    )

    zone_bones = {bone_id for zone in profile.semantic_zones for bone_id in zone.bone_ids}
    unknown_zone_bones = sorted(zone_bones - set(semantic_by_id))
    add(
        "semantic_zone_bone_identity",
        "BLOCK" if unknown_zone_bones else "PASS",
        unknown_zone_bones,
        [],
        "Semantic zones may reference only stable R10.7 bone IDs.",
    )
    unmapped_deform = sorted(set(semantic_profile.deform_ids) - zone_bones)
    if len(unmapped_deform) > profile.qa.max_unmapped_deform_bones:
        unmapped_state = "BLOCK"
    elif unmapped_deform:
        unmapped_state = "WARN"
    else:
        unmapped_state = "PASS"
    add(
        "semantic_zone_deform_coverage",
        unmapped_state,
        unmapped_deform,
        profile.qa.max_unmapped_deform_bones,
        "Deforming semantic bones outside declared zones are explicit; the profile never guesses their role.",
    )

    expected_pieces = {item.piece_id: item for item in profile.pieces}
    actual_pieces = {
        str(item.get("piece_id")): item
        for item in pieces_raw
        if isinstance(item, dict) and isinstance(item.get("piece_id"), str)
    }
    missing_pieces = sorted(item.piece_id for item in profile.pieces if item.required and item.piece_id not in actual_pieces)
    unexpected_pieces = sorted(set(actual_pieces) - set(expected_pieces))
    mismatched_pieces: list[str] = []
    vertex_counts: dict[str, int] = {}
    for piece_id, expected in expected_pieces.items():
        actual = actual_pieces.get(piece_id)
        if actual is None:
            continue
        if (
            actual.get("piece_type") != expected.piece_type.value
            or actual.get("object_id") != expected.object_id
            or actual.get("mesh_id") != expected.mesh_id
        ):
            mismatched_pieces.append(piece_id)
        if expected.piece_type is ProfilePieceType.MESH:
            count = actual.get("vertex_count")
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                mismatched_pieces.append(piece_id)
            else:
                vertex_counts[piece_id] = count
    piece_problem = bool(missing_pieces or mismatched_pieces or (unexpected_pieces and profile.qa.exact_piece_inventory))
    piece_state = "BLOCK" if piece_problem else ("WARN" if unexpected_pieces else "PASS")
    add(
        "piece_inventory",
        piece_state,
        {"missing_required": missing_pieces, "unexpected": unexpected_pieces, "mismatched": sorted(set(mismatched_pieces))},
        {"exact": profile.qa.exact_piece_inventory},
        "Object/mesh/armature pieces are resolved by stable IDs; unexpected pieces are never silently adopted.",
    )

    expected_slots = {(item.piece_id, item.slot_id): item for item in profile.material_slots}
    actual_slots = {
        (str(item.get("piece_id")), str(item.get("slot_id"))): item
        for item in slots_raw
        if isinstance(item, dict) and isinstance(item.get("piece_id"), str) and isinstance(item.get("slot_id"), str)
    }
    missing_slots = sorted([list(key) for key, item in expected_slots.items() if item.required and key not in actual_slots])
    unexpected_slots = sorted([list(key) for key in set(actual_slots) - set(expected_slots)])
    mismatched_slots = sorted([
        list(key) for key, expected in expected_slots.items()
        if key in actual_slots and actual_slots[key].get("actual_name") != expected.actual_name
    ])
    slot_problem = bool(missing_slots or mismatched_slots or (unexpected_slots and profile.qa.exact_material_slots))
    slot_state = "BLOCK" if slot_problem else ("WARN" if unexpected_slots else "PASS")
    add(
        "material_slot_inventory",
        slot_state,
        {"missing_required": missing_slots, "unexpected": unexpected_slots, "mismatched": mismatched_slots},
        {"exact": profile.qa.exact_material_slots},
        "Material slots are explicit profile data and cannot be remapped by display-name heuristics.",
    )

    expected_shapes = {(item.piece_id, item.key_id): item for item in profile.shape_keys}
    actual_shapes = {
        (str(item.get("piece_id")), str(item.get("key_id"))): item
        for item in shapes_raw
        if isinstance(item, dict) and isinstance(item.get("piece_id"), str) and isinstance(item.get("key_id"), str)
    }
    missing_shapes = sorted([list(key) for key, item in expected_shapes.items() if item.required and key not in actual_shapes])
    unexpected_shapes = sorted([list(key) for key in set(actual_shapes) - set(expected_shapes)])
    mismatched_shapes: list[list[str]] = []
    topology_errors: list[list[str]] = []
    for key, expected in expected_shapes.items():
        actual = actual_shapes.get(key)
        if actual is None:
            continue
        if actual.get("actual_name") != expected.actual_name:
            mismatched_shapes.append(list(key))
        count = actual.get("vertex_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 1 or vertex_counts.get(expected.piece_id) != count:
            topology_errors.append(list(key))
    shape_problem = bool(missing_shapes or mismatched_shapes or (unexpected_shapes and profile.qa.exact_shape_keys))
    shape_state = "BLOCK" if shape_problem else ("WARN" if unexpected_shapes else "PASS")
    add(
        "shape_key_inventory",
        shape_state,
        {"missing_required": missing_shapes, "unexpected": unexpected_shapes, "mismatched": sorted(mismatched_shapes)},
        {"exact": profile.qa.exact_shape_keys},
        "Shape-key/morph inventory is stable by ID and actual Blender name; unknown morphs are never silently accepted.",
    )
    add(
        "shape_key_topology",
        "BLOCK" if topology_errors else "PASS",
        sorted(topology_errors),
        [],
        "Each declared shape key must retain the vertex count of its bound mesh; R10.8 never changes topology implicitly.",
    )

    coordinates = inventory.get("coordinates")
    coordinate_ok = isinstance(coordinates, dict) and coordinates == profile.coordinates.to_dict()
    add(
        "coordinate_basis",
        "PASS" if coordinate_ok else "BLOCK",
        coordinates,
        profile.coordinates.to_dict(),
        "Profiles use the frozen R10 meter / -Z forward / Y up basis.",
    )

    inventory_rig_ok = (
        inventory.get("rig_profile_digest") == profile.rig_profile_digest
        and inventory.get("rig_semantic_digest") == profile.rig_semantic_digest
    )
    add(
        "inventory_contract_binding",
        "PASS" if inventory_rig_ok else "BLOCK",
        {
            "rig_profile_digest": inventory.get("rig_profile_digest"),
            "rig_semantic_digest": inventory.get("rig_semantic_digest"),
        },
        {
            "rig_profile_digest": profile.rig_profile_digest,
            "rig_semantic_digest": profile.rig_semantic_digest,
        },
        "Synthetic or production inventory evidence is cryptographically bound to the exact rig contracts.",
    )

    block_count = sum(1 for item in rules if item["state"] == "BLOCK")
    warn_count = sum(1 for item in rules if item["state"] == "WARN")
    report = {
        "schema": "kodepoia.blender.organic_profile_report",
        "version": 1,
        "profile_id": profile.profile_id,
        "profile_kind": profile.kind.value,
        "profile_digest": profile.digest,
        "asset_revision_id": profile.asset.revision_id,
        "status": "block" if block_count else ("warn" if warn_count else "pass"),
        "summary": {
            "pass": sum(1 for item in rules if item["state"] == "PASS"),
            "warn": warn_count,
            "block": block_count,
        },
        "rules": rules,
    }
    report["report_digest"] = canonical_sha256(report)
    return report
