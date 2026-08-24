from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.assets import (
    AssetId,
    AssetKind,
    AssetRevision,
    AssetRole,
    AssetStatus,
    PreservationPolicy,
    ProvenanceRef,
    ReuseScope,
)
from kodepoia.blender3d import (
    OrganicAssetProfile,
    RigProfile,
    RigSemanticProfile,
    evaluate_organic_profile,
)
from kodepoia.blender3d.errors import BlenderBoundaryError

ROOT = Path(__file__).resolve().parents[1]


def revision(*, provenance: bool = True, seed: str = "organic") -> AssetRevision:
    content = f"r10.8-{seed}".encode()
    return AssetRevision.create(
        asset_id=AssetId.from_seed("r10.8", seed),
        role=AssetRole.SOURCE,
        kind=AssetKind.MODEL_3D,
        content_sha256=hashlib.sha256(content).hexdigest(),
        content_length=len(content),
        reuse_scope=ReuseScope.VAULT_LOCAL,
        preservation=PreservationPolicy.PINNED_SOURCE,
        provenance=(ProvenanceRef("local_fixture", f"fixtures/{seed}.blend"),) if provenance else (),
        status=AssetStatus.READY,
    )


def rig_profile(input_sha: str) -> RigProfile:
    return RigProfile.from_dict(
        {
            "version": 1,
            "rig_id": "fixture.rig",
            "armature_id": "fixture_armature",
            "mode": "create",
            "input_blend_sha256": input_sha,
            "bones": [
                {"bone_id": "root", "display_name": "Root", "parent_id": None, "head": [0.0, 0.0, 0.0], "tail": [0.0, 1.0, 0.0], "deform": True, "connected": False},
                {"bone_id": "spine", "display_name": "Spine", "parent_id": "root", "head": [0.0, 1.0, 0.0], "tail": [0.0, 2.0, 0.0], "deform": True, "connected": False},
                {"bone_id": "head", "display_name": "Head", "parent_id": "spine", "head": [0.0, 2.0, 0.0], "tail": [0.0, 3.0, 0.0], "deform": True, "connected": False},
                {"bone_id": "control", "display_name": "Control", "parent_id": "root", "head": [1.0, 0.0, 0.0], "tail": [1.0, 1.0, 0.0], "deform": False, "connected": False},
            ],
            "meshes": [{"mesh_id": "body", "strategy": "nearest_deform_bone", "weights": []}],
            "influence": {
                "max_influences": 4,
                "allow_extended_influences": False,
                "normalization_tolerance": 0.0001,
                "tiny_weight_threshold": 0.00001,
                "require_deformation_probe": True,
            },
        }
    )


def semantic_profile(input_sha: str) -> RigSemanticProfile:
    return RigSemanticProfile.from_dict(
        {
            "rig_id": "fixture.rig",
            "armature_id": "fixture_armature",
            "input_blend_sha256": input_sha,
            "bones": [
                {"bone_id": "root", "actual_name": "root", "parent_id": None, "deform": True},
                {"bone_id": "spine", "actual_name": "spine", "parent_id": "root", "deform": True},
                {"bone_id": "head", "actual_name": "head", "parent_id": "spine", "deform": True},
                {"bone_id": "control", "actual_name": "control", "parent_id": "root", "deform": False},
            ],
        }
    )


def profile_payload(asset: AssetRevision, rig: RigProfile, semantic: RigSemanticProfile, *, kind: str = "humanoid_biped") -> dict[str, object]:
    return {
        "version": 1,
        "profile_id": f"fixture.{kind}",
        "kind": kind,
        "asset": {
            "asset_id": str(asset.asset_id),
            "revision_id": str(asset.revision_id),
            "content_sha256": asset.content_sha256,
        },
        "coordinates": {"unit_scale_meters": 1.0, "forward_axis": "-Z", "up_axis": "Y"},
        "rig_id": rig.rig_id,
        "armature_id": rig.armature_id,
        "rig_profile_digest": rig.digest,
        "rig_semantic_digest": semantic.digest,
        "pieces": [
            {"piece_id": "body", "piece_type": "mesh", "object_id": "body_object", "mesh_id": "body", "required": True},
            {"piece_id": "skeleton", "piece_type": "armature", "object_id": "fixture_armature", "mesh_id": None, "required": True},
        ],
        "material_slots": [{"piece_id": "body", "slot_id": "skin", "actual_name": "Skin", "required": True}],
        "shape_keys": [{"piece_id": "body", "key_id": "expression.primary", "actual_name": "Expression_Primary", "required": True}],
        "semantic_zones": [{"zone_id": "core", "bone_ids": ["root", "spine", "head"], "piece_ids": ["body", "skeleton"]}],
        "required_deform_bones": ["root", "spine", "head"],
        "animation_bones": ["root", "spine", "head", "control"],
        "qa": {
            "exact_piece_inventory": True,
            "exact_material_slots": True,
            "exact_shape_keys": True,
            "max_unmapped_deform_bones": 0,
        },
    }


def inventory(profile: OrganicAssetProfile) -> dict[str, object]:
    return {
        "schema": "kodepoia.blender.organic_profile_inventory",
        "version": 1,
        "profile_digest": profile.digest,
        "asset_revision_id": profile.asset.revision_id,
        "coordinates": profile.coordinates.to_dict(),
        "rig_profile_digest": profile.rig_profile_digest,
        "rig_semantic_digest": profile.rig_semantic_digest,
        "pieces": [
            {"piece_id": "body", "piece_type": "mesh", "object_id": "body_object", "mesh_id": "body", "vertex_count": 8},
            {"piece_id": "skeleton", "piece_type": "armature", "object_id": "fixture_armature", "mesh_id": None},
        ],
        "material_slots": [{"piece_id": "body", "slot_id": "skin", "actual_name": "Skin"}],
        "shape_keys": [{"piece_id": "body", "key_id": "expression.primary", "actual_name": "Expression_Primary", "vertex_count": 8}],
    }


def fixture(*, kind: str = "humanoid_biped", provenance: bool = True):
    asset = revision(provenance=provenance, seed=kind)
    rig = rig_profile(asset.content_sha256)
    semantic = semantic_profile(asset.content_sha256)
    profile = OrganicAssetProfile.from_dict(profile_payload(asset, rig, semantic, kind=kind))
    return asset, rig, semantic, profile


@pytest.mark.parametrize("kind", ["humanoid_biped", "quadruped"])
def test_r10_8_required_profile_kinds_pass_synthetic_contract_fixture(kind: str) -> None:
    asset, rig, semantic, profile = fixture(kind=kind)
    report = evaluate_organic_profile(profile, inventory(profile), asset_revision=asset, rig_profile=rig, semantic_profile=semantic)
    assert report["status"] == "pass"
    assert report["summary"]["block"] == 0


def test_r10_8_profile_digest_roundtrip_and_schemas() -> None:
    asset, rig, semantic, profile = fixture()
    clone = OrganicAssetProfile.from_dict(json.loads(json.dumps(profile.to_dict())))
    assert clone.digest == profile.digest
    Draft202012Validator(json.loads((ROOT / "schemas/r10-organic-profile-v1.schema.json").read_text())).validate(profile.to_dict())
    evidence = inventory(profile)
    Draft202012Validator(json.loads((ROOT / "schemas/r10-organic-profile-inventory-v1.schema.json").read_text())).validate(evidence)
    report = evaluate_organic_profile(profile, evidence, asset_revision=asset, rig_profile=rig, semantic_profile=semantic)
    Draft202012Validator(json.loads((ROOT / "schemas/r10-organic-profile-report-v1.schema.json").read_text())).validate(report)


def test_r10_8_frozen_coordinate_basis_rejects_implicit_axis_conversion() -> None:
    asset = revision()
    rig = rig_profile(asset.content_sha256)
    semantic = semantic_profile(asset.content_sha256)
    payload = profile_payload(asset, rig, semantic)
    payload["coordinates"]["forward_axis"] = "X"  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="frozen -Z forward / Y up basis"):
        OrganicAssetProfile.from_dict(payload)


def test_r10_8_profile_never_duplicates_license_authority() -> None:
    _, _, _, profile = fixture()
    serialized = profile.to_dict()
    assert set(serialized["asset"]) == {"asset_id", "revision_id", "content_sha256"}
    assert "license" not in json.dumps(serialized).lower()


def test_r10_8_r8_provenance_and_exact_revision_are_fail_closed() -> None:
    asset, rig, semantic, profile = fixture(provenance=False)
    report = evaluate_organic_profile(profile, inventory(profile), asset_revision=asset, rig_profile=rig, semantic_profile=semantic)
    blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert "r8_governance_readiness" in blocked

    other = revision(seed="other")
    report = evaluate_organic_profile(profile, inventory(profile), asset_revision=other, rig_profile=rig, semantic_profile=semantic)
    blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert "r8_asset_revision_binding" in blocked


def test_r10_8_rig_and_semantic_identity_are_exact_not_fuzzy() -> None:
    asset, rig, semantic, _ = fixture()
    payload = profile_payload(asset, rig, semantic)
    payload["rig_semantic_digest"] = "0" * 64
    profile = OrganicAssetProfile.from_dict(payload)
    evidence = inventory(profile)
    report = evaluate_organic_profile(profile, evidence, asset_revision=asset, rig_profile=rig, semantic_profile=semantic)
    blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert "r10_7_semantic_rig_compatibility" in blocked


def test_r10_8_unknown_zone_and_animation_bones_block() -> None:
    asset, rig, semantic, _ = fixture()
    payload = profile_payload(asset, rig, semantic)
    payload["semantic_zones"][0]["bone_ids"].append("mystery")  # type: ignore[index]
    payload["animation_bones"].append("mystery")  # type: ignore[union-attr]
    profile = OrganicAssetProfile.from_dict(payload)
    report = evaluate_organic_profile(profile, inventory(profile), asset_revision=asset, rig_profile=rig, semantic_profile=semantic)
    blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert {"semantic_zone_bone_identity", "animation_bone_coverage"} <= blocked


def test_r10_8_shape_key_topology_mismatch_blocks() -> None:
    asset, rig, semantic, profile = fixture()
    evidence = inventory(profile)
    evidence["shape_keys"][0]["vertex_count"] = 7  # type: ignore[index]
    report = evaluate_organic_profile(profile, evidence, asset_revision=asset, rig_profile=rig, semantic_profile=semantic)
    blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert "shape_key_topology" in blocked


def test_r10_8_non_exact_optional_inventory_is_warn_not_silently_adopted() -> None:
    asset, rig, semantic, _ = fixture()
    payload = profile_payload(asset, rig, semantic)
    payload["qa"]["exact_shape_keys"] = False  # type: ignore[index]
    profile = OrganicAssetProfile.from_dict(payload)
    evidence = inventory(profile)
    evidence["shape_keys"].append({"piece_id": "body", "key_id": "optional.extra", "actual_name": "Optional_Extra", "vertex_count": 8})  # type: ignore[union-attr]
    report = evaluate_organic_profile(profile, evidence, asset_revision=asset, rig_profile=rig, semantic_profile=semantic)
    warning = next(item for item in report["rules"] if item["rule_id"] == "shape_key_inventory")
    assert warning["state"] == "WARN"
    assert report["status"] == "warn"


def test_r10_8_profile_contract_rejects_unknown_piece_references() -> None:
    asset = revision()
    rig = rig_profile(asset.content_sha256)
    semantic = semantic_profile(asset.content_sha256)
    payload = profile_payload(asset, rig, semantic)
    payload["shape_keys"][0]["piece_id"] = "missing"  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="non-mesh or unknown piece"):
        OrganicAssetProfile.from_dict(payload)


def test_r10_8_modules_have_no_dynamic_or_external_execution_surface() -> None:
    forbidden_imports = {"socket", "http", "urllib", "requests", "ftplib", "subprocess"}
    for relative in ("src/kodepoia/blender3d/profile_contracts.py", "src/kodepoia/blender3d/profile_validator.py"):
        source = (ROOT / relative).read_text()
        compile(source, relative, "exec")
        tree = ast.parse(source)
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        assert not imports & forbidden_imports
        lowered = source.lower()
        for token in ("exec(", "eval(", "os.system", "popen(", "bpy.ops.", "bpy.data."):
            assert token not in lowered
