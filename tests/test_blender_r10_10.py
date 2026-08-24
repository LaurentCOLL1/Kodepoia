from __future__ import annotations

import ast
import json
import struct
from pathlib import Path

import jsonschema
import pytest

from kodepoia.assets.contracts import AssetId, AssetKind, AssetRevision, AssetRole, AssetStatus, PreservationPolicy, ProvenanceRef, ReuseScope
from kodepoia.blender3d.errors import BlenderBoundaryError, BlenderProtocolError
from kodepoia.blender3d.gltf_bootstrap import GLTF_ACCEPTANCE_BOOTSTRAP_SOURCE, GLTF_EXPORT_BOOTSTRAP_SOURCE
from kodepoia.blender3d.gltf_contracts import GltfExportProfile, make_gltf_export_revision
from kodepoia.blender3d.gltf_godot_fixture import GODOT_VALIDATOR_SCRIPT_SOURCE
from kodepoia.blender3d.gltf_runner import validate_local_acceptance_evidence
from kodepoia.blender3d.gltf_validator import evaluate_roundtrip, parse_glb_bytes, parse_gltf_json_bytes
from kodepoia.blender3d.serialization import canonical_sha256


def _glb(document: dict[str, object], binary: bytes = b"\x00\x00\x00\x00") -> bytes:
    raw_json = json.dumps(document, separators=(",", ":")).encode("utf-8")
    raw_json += b" " * ((4 - len(raw_json) % 4) % 4)
    binary += b"\x00" * ((4 - len(binary) % 4) % 4)
    chunks = struct.pack("<II", len(raw_json), 0x4E4F534A) + raw_json
    if binary:
        chunks += struct.pack("<II", len(binary), 0x004E4942) + binary
    total = 12 + len(chunks)
    return struct.pack("<4sII", b"glTF", 2, total) + chunks


def _static_doc() -> dict[str, object]:
    return {
        "asset": {"version": "2.0", "generator": "Kodepoia fixture"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}],
        "materials": [{"name": "Mat"}],
        "accessors": [{"componentType": 5126, "count": 3, "type": "VEC3"}],
        "buffers": [{"byteLength": 4}],
    }


def _source_revision() -> AssetRevision:
    asset = AssetId.from_seed("r10.10-test", "source")
    return AssetRevision.create(
        asset_id=asset, role=AssetRole.SOURCE, kind=AssetKind.MODEL_3D,
        content_sha256="1" * 64, content_length=123, reuse_scope=ReuseScope.PROJECT_ONLY,
        preservation=PreservationPolicy.PINNED_SOURCE,
        provenance=(ProvenanceRef("fixture", "r10.10"),), status=AssetStatus.READY,
    )


def _profile_payload(*, skinned: bool = False) -> tuple[dict[str, object], AssetRevision]:
    source = _source_revision()
    output = AssetId.from_seed("r10.10-test", "output-skinned" if skinned else "output-static")
    payload: dict[str, object] = {
        "version": 1, "profile_id": "fixture.skinned" if skinned else "fixture.static",
        "input_blend_sha256": source.content_sha256, "source_asset_id": str(source.asset_id),
        "source_revision_id": str(source.revision_id), "source_content_sha256": source.content_sha256,
        "output_asset_id": str(output), "asset_mode": "skinned" if skinned else "static", "container": "GLB",
        "scope": "selected", "source_object_ids": ["body", "rig"] if skinned else ["mesh"],
        "mesh_qa_digest": "2" * 64, "pbr_profile_digest": "3" * 64,
        "rig_profile_digest": "4" * 64 if skinned else None,
        "animation_report_digest": "5" * 64 if skinned else None, "lod_manifest_digest": None,
        "export_normals": True, "export_tangents": True, "export_uvs": True, "export_materials": True,
        "export_skins": skinned, "export_morphs": skinned, "export_animations": skinned,
        "deform_bones_only": skinned, "max_influences": 4, "required_uv_sets": ["UVMap"],
        "required_materials": ["BodyMat"] if skinned else ["Mat"],
        "required_bones": ["Root", "Child"] if skinned else [],
        "required_shape_keys": ["Smile"] if skinned else [], "required_animations": ["Wave"] if skinned else [],
        "allowed_extensions": [], "max_output_bytes": 16 * 1024 * 1024, "unit_scale_meters": 1.0, "export_y_up": True,
    }
    return payload, source


def test_glb_parser_accepts_bounded_static_document() -> None:
    document, facts = parse_glb_bytes(_glb(_static_doc()), max_bytes=1_000_000)
    assert document["asset"]["version"] == "2.0"
    assert facts.mesh_count == 1 and facts.material_count == 1 and facts.total_bytes > 12


@pytest.mark.parametrize("mutator", ["magic", "length", "version"])
def test_glb_parser_blocks_header_spoofing(mutator: str) -> None:
    data = bytearray(_glb(_static_doc()))
    if mutator == "magic": data[0:4] = b"BAD!"
    elif mutator == "length": struct.pack_into("<I", data, 8, len(data) + 4)
    else: struct.pack_into("<I", data, 4, 1)
    with pytest.raises(BlenderProtocolError): parse_glb_bytes(bytes(data), max_bytes=1_000_000)


def test_gltf_json_blocks_remote_external_uri() -> None:
    document = _static_doc(); document["buffers"] = [{"uri": "https://example.invalid/a.bin", "byteLength": 4}]
    with pytest.raises(BlenderProtocolError): parse_gltf_json_bytes(json.dumps(document).encode(), max_bytes=1_000_000)


def test_profile_is_strict_and_binds_r8_source() -> None:
    payload, source = _profile_payload(); profile = GltfExportProfile.from_dict(payload)
    assert profile.source_revision_id == str(source.revision_id)
    assert profile.digest == canonical_sha256(profile.to_dict())
    bad = dict(payload); bad["allowed_extensions"] = ["VENDOR_model_exec"]
    with pytest.raises(BlenderBoundaryError): GltfExportProfile.from_dict(bad)


def test_profile_blocks_source_overwrite_and_invalid_skin_claim() -> None:
    payload, _ = _profile_payload(); bad = dict(payload); bad["output_asset_id"] = payload["source_asset_id"]
    with pytest.raises(BlenderBoundaryError): GltfExportProfile.from_dict(bad)
    bad2 = dict(payload); bad2["asset_mode"] = "skinned"
    with pytest.raises(BlenderBoundaryError): GltfExportProfile.from_dict(bad2)


def test_roundtrip_static_passes_and_missing_skin_bone_blocks() -> None:
    static_payload, _ = _profile_payload(); static_profile = GltfExportProfile.from_dict(static_payload)
    facts = {"mesh_count": 1, "material_names": ["Mat"], "uv_layer_names": ["UVMap"], "bone_names": [], "shape_key_names": [], "animation_names": []}
    assert evaluate_roundtrip(static_profile, facts, facts, _static_doc())["status"] == "pass"
    skinned_payload, _ = _profile_payload(skinned=True); profile = GltfExportProfile.from_dict(skinned_payload)
    imported = {"mesh_count": 1, "material_names": ["BodyMat"], "uv_layer_names": ["UVMap"], "bone_names": ["Root"], "shape_key_names": ["Smile"], "animation_names": ["Wave"]}
    document = _static_doc(); document["nodes"] = [{"mesh": 0, "skin": 0}, {}, {}]; document["skins"] = [{"joints": [1, 2]}]
    document["animations"] = [{"samplers": [{"input": 0, "output": 0}], "channels": [{"sampler": 0, "target": {"node": 1, "path": "rotation"}}], "name": "Wave"}]
    blocked = evaluate_roundtrip(profile, imported, imported, document)
    assert blocked["status"] == "block" and "skin_bones" in blocked["blockers"]


def test_glb_promotion_creates_deterministic_r8_export_lineage() -> None:
    payload, source = _profile_payload(); profile = GltfExportProfile.from_dict(payload)
    first = make_gltf_export_revision(profile, output_sha256="a" * 64, output_length=321, source_revision=source, manifest_digest="b" * 64)
    second = make_gltf_export_revision(profile, output_sha256="a" * 64, output_length=321, source_revision=source, manifest_digest="b" * 64)
    assert first.revision_id == second.revision_id and first.role is AssetRole.DERIVED and first.kind is AssetKind.MODEL_3D
    assert first.lineage[0].relation == "gltf_export"


def test_bootstraps_are_static_offline_owned_code() -> None:
    forbidden_modules = {"subprocess", "socket", "requests", "urllib", "http", "ftplib"}
    for source in (GLTF_EXPORT_BOOTSTRAP_SOURCE, GLTF_ACCEPTANCE_BOOTSTRAP_SOURCE):
        tree = ast.parse(source); imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module: imports.add(node.module.split(".")[0])
        assert not imports & forbidden_modules
        assert "exec(" not in source and "eval(" not in source and "url_open" not in source
    assert "use_scripts=False" in GLTF_EXPORT_BOOTSTRAP_SOURCE


def test_acceptance_bootstrap_uses_blender_52_principled_and_layered_action_contracts() -> None:
    source = GLTF_ACCEPTANCE_BOOTSTRAP_SOURCE
    assert 'bsdf.inputs["Metallic"]' in source
    assert 'bsdf.inputs["Metallic IOR Level"]' not in source
    assert "action.slots.new" in source
    assert 'layer.strips.new(type="KEYFRAME")' in source
    assert "channelbag.fcurves.new" in source
    assert "animation_data.action_slot = slot" in source
    assert "pose.keyframe_insert" not in source


def test_godot_acceptance_script_is_fixed_and_semantic() -> None:
    assert "KODEPOIA_R10_10_GODOT_PASS" in GODOT_VALIDATOR_SCRIPT_SOURCE
    assert "Skeleton3D" in GODOT_VALIDATOR_SCRIPT_SOURCE and "AnimationPlayer" in GODOT_VALIDATOR_SCRIPT_SOURCE
    assert "OS.execute" not in GODOT_VALIDATOR_SCRIPT_SOURCE and "HTTPRequest" not in GODOT_VALIDATOR_SCRIPT_SOURCE


def _pass_evidence() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "kodepoia.r10.gltf_local_acceptance", "version": 1, "source_sha": "c" * 40,
        "status": "pass", "blockers": [], "policy_version": "r10.10-local-v1",
        "platform": {"system": "windows", "machine": "AMD64"},
        "blender": {"version": "5.2.0", "background": True, "online_access": False, "executable_sha256": "d" * 64, "process": {"returncode": 0}},
        "fixtures": {
            "static": {"artifact": {"path": "static.glb", "sha256": "e" * 64, "bytes": 100}, "gltf": {"mesh_count": 1}, "roundtrip": {}},
            "rigged": {"artifact": {"path": "rigged.glb", "sha256": "f" * 64, "bytes": 200}, "gltf": {"mesh_count": 1, "skin_count": 1}, "roundtrip": {}},
        },
        "godot": {"version": {"raw": "4.7.stable", "major": 4, "minor": 7, "patch": 0, "compatible_47": True}, "executable_sha256": "1" * 64,
                  "import": {"returncode": 0, "timed_out": False, "cancelled": False},
                  "semantic_smoke": {"returncode": 0, "timed_out": False, "cancelled": False, "pass_marker": True}},
    }
    payload["evidence_digest"] = canonical_sha256(payload)
    return payload


def test_local_acceptance_evidence_verifier_is_fail_closed() -> None:
    payload = _pass_evidence(); validate_local_acceptance_evidence(payload, expected_source_sha="c" * 40)
    tampered = json.loads(json.dumps(payload)); tampered["godot"]["semantic_smoke"]["pass_marker"] = False
    with pytest.raises(BlenderProtocolError): validate_local_acceptance_evidence(tampered, expected_source_sha="c" * 40)


def test_r10_10_schemas_accept_profile_and_local_evidence() -> None:
    root = Path(__file__).resolve().parents[1]; payload, _ = _profile_payload()
    profile_schema = json.loads((root / "schemas/r10-gltf-export-profile-v1.schema.json").read_text(encoding="utf-8"))
    evidence_schema = json.loads((root / "schemas/r10-gltf-local-acceptance-v1.schema.json").read_text(encoding="utf-8"))
    manifest_schema = json.loads((root / "schemas/r10-gltf-export-manifest-v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(payload, profile_schema); jsonschema.validate(_pass_evidence(), evidence_schema)
    assert manifest_schema["$id"].endswith("r10-gltf-export-manifest-v1.schema.json")
