from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.assets import AssetId, AssetKind, AssetRevision, AssetRole, AssetStatus, PreservationPolicy, ProvenanceRef, ReuseScope
from kodepoia.blender3d import BlenderExecutableBoundary, LODProfile, LODRunner, evaluate_lod_measurements, make_lod_variant_revision, validate_lod_source_revision
from kodepoia.blender3d.errors import BlenderBoundaryError
from kodepoia.blender3d.lod_bootstrap import LOD_BOOTSTRAP_SOURCE
from kodepoia.blender3d.runner import BlenderRunner, RunnerProcessResult
from kodepoia.core.sandbox import ProcessSandbox

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "9" * 40


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_revision(content: bytes = b"r10.9-source") -> AssetRevision:
    return AssetRevision.create(asset_id=AssetId.from_seed("r10.9", "source"), role=AssetRole.SOURCE, kind=AssetKind.MODEL_3D, content_sha256=digest(content), content_length=len(content), reuse_scope=ReuseScope.VAULT_LOCAL, preservation=PreservationPolicy.PINNED_SOURCE, provenance=(ProvenanceRef("local", "fixtures/r10.9.blend"),), status=AssetStatus.READY)


def profile(revision: AssetRevision, *, mode: str = "static", shape_policy: str = "block_if_present") -> dict[str, object]:
    return {"version": 1, "profile_id": "fixture.lod", "input_blend_sha256": revision.content_sha256, "source_asset_id": str(revision.asset_id), "source_revision_id": str(revision.revision_id), "source_content_sha256": revision.content_sha256, "source_object_id": "body", "asset_mode": mode, "mesh_qa_profile_digest": "a" * 64, "rig_profile_digest": "b" * 64 if mode == "skinned" else None, "ratio_tolerance": 0.06, "tiers": [{"tier_id": "lod1", "output_asset_id": str(AssetId.from_seed("r10.9", "lod1")), "ratio": 0.5, "min_triangles": 450, "max_triangles": 550}, {"tier_id": "lod2", "output_asset_id": str(AssetId.from_seed("r10.9", "lod2")), "ratio": 0.25, "min_triangles": 225, "max_triangles": 275}], "preservation": {"preserve_material_slots": True, "preserve_uv_layers": True, "preserve_normals": True, "shape_keys": shape_policy, "required_vertex_groups": ["root"] if mode == "skinned" else [], "max_extent_relative_error": 0.05, "max_surface_area_relative_error": 0.1, "max_weight_sum_error": 0.001, "max_influences": 4}}


def measurements(parsed: LODProfile, *, shapes: list[str] | None = None, override: dict[str, object] | None = None) -> dict[str, object]:
    groups = ["root"] if parsed.asset_mode.value == "skinned" else []
    source = {"triangle_count": 1000, "material_slots": ["Body"], "uv_layers": ["UVMap"], "shape_keys": shapes or [], "vertex_groups": groups, "bounds_extent": [2.0, 1.0, 4.0], "surface_area": 100.0, "invalid_normal_count": 0, "zero_weight_vertices": 0, "max_influences": 1 if groups else 0, "max_weight_sum_error": 0.0}
    tiers = {"lod1": {"triangle_count": 500, "material_slots": ["Body"], "uv_layers": ["UVMap"], "shape_keys": [], "vertex_groups": groups, "bounds_extent": [1.98, 1.0, 3.98], "surface_area": 97.0, "invalid_normal_count": 0, "zero_weight_vertices": 0, "max_influences": 1 if groups else 0, "max_weight_sum_error": 0.0}, "lod2": {"triangle_count": 250, "material_slots": ["Body"], "uv_layers": ["UVMap"], "shape_keys": [], "vertex_groups": groups, "bounds_extent": [1.96, 0.99, 3.95], "surface_area": 94.0, "invalid_normal_count": 0, "zero_weight_vertices": 0, "max_influences": 1 if groups else 0, "max_weight_sum_error": 0.0}}
    if override:
        for tier_id, values in override.items():
            if tier_id in tiers and isinstance(values, dict):
                tiers[tier_id].update(values)
    return {"schema": "kodepoia.blender.lod_measurements", "version": 1, "profile_digest": parsed.digest, "input_blend_sha256": parsed.input_blend_sha256, "source": source, "tiers": tiers}


def test_r10_9_profile_contract_is_deterministic_and_schema_valid() -> None:
    revision = source_revision(); parsed = LODProfile.from_dict(profile(revision))
    assert [tier.ratio for tier in parsed.tiers] == [0.5, 0.25]
    assert parsed.digest == LODProfile.from_dict(json.loads(json.dumps(parsed.to_dict()))).digest
    Draft202012Validator(json.loads((ROOT / "schemas/r10-lod-profile-v1.schema.json").read_text())).validate(parsed.to_dict())


def test_r10_9_profile_rejects_bad_order_and_missing_skinned_rig() -> None:
    revision = source_revision(); bad = profile(revision); bad["tiers"] = list(reversed(bad["tiers"]))  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="strictly descending"): LODProfile.from_dict(bad)
    bad = profile(revision, mode="skinned"); bad["rig_profile_digest"] = None
    with pytest.raises(BlenderBoundaryError, match="require rig_profile_digest"): LODProfile.from_dict(bad)
    bad = profile(revision); bad["tiers"][0]["output_asset_id"] = str(revision.asset_id)  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="overwrite"): LODProfile.from_dict(bad)


def test_r10_9_r8_source_binding_and_variant_lineage_are_exact() -> None:
    revision = source_revision(); parsed = LODProfile.from_dict(profile(revision)); validate_lod_source_revision(parsed, revision)
    first = make_lod_variant_revision(parsed, parsed.tiers[0], output_sha256="c" * 64, output_length=12, source_revision=revision); second = make_lod_variant_revision(parsed, parsed.tiers[0], output_sha256="c" * 64, output_length=12, source_revision=revision)
    assert first.revision_id == second.revision_id and first.role is AssetRole.DERIVED and first.lineage[0].relation == "lod_variant" and first.lineage[0].input_revision_id == revision.revision_id


def test_r10_9_source_binding_blocks_provenance_mismatch() -> None:
    revision = source_revision(); parsed = LODProfile.from_dict(profile(revision)); ungoverned = AssetRevision.create(asset_id=revision.asset_id, role=revision.role, kind=revision.kind, content_sha256=revision.content_sha256, content_length=revision.content_length, reuse_scope=revision.reuse_scope, preservation=revision.preservation, provenance=(), status=revision.status)
    with pytest.raises(BlenderBoundaryError, match="provenance"): validate_lod_source_revision(LODProfile.from_dict({**parsed.to_dict(), "source_revision_id": str(ungoverned.revision_id)}), ungoverned)


def test_r10_9_static_and_skinned_clean_measurements_pass() -> None:
    for mode in ("static", "skinned"):
        revision = source_revision(mode.encode()); parsed = LODProfile.from_dict(profile(revision, mode=mode)); report = evaluate_lod_measurements(parsed, measurements(parsed))
        assert report["status"] == "pass" and report["summary"]["block"] == 0
        Draft202012Validator(json.loads((ROOT / "schemas/r10-lod-report-v1.schema.json").read_text())).validate(report)


def test_r10_9_preservation_failures_block_promotion() -> None:
    revision = source_revision(); parsed = LODProfile.from_dict(profile(revision)); report = evaluate_lod_measurements(parsed, measurements(parsed, override={"lod1": {"triangle_count": 700, "material_slots": ["Wrong"], "uv_layers": [], "invalid_normal_count": 1, "bounds_extent": [1.0, 1.0, 4.0], "surface_area": 70.0}})); blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert {"triangle_budget", "ratio_target", "material_slot_identity", "uv_layer_identity", "normal_validity", "extent_preservation", "surface_area_preservation"} <= blocked


def test_r10_9_skinned_weight_failures_block() -> None:
    revision = source_revision(); parsed = LODProfile.from_dict(profile(revision, mode="skinned")); report = evaluate_lod_measurements(parsed, measurements(parsed, override={"lod1": {"vertex_groups": [], "zero_weight_vertices": 3, "max_influences": 6, "max_weight_sum_error": 0.25}})); blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert {"skin_group_identity", "zero_weight_vertices", "weight_normalization", "influence_budget"} <= blocked


def test_r10_9_shape_key_policy_is_fail_closed_or_explicit_warn() -> None:
    revision = source_revision(); blocked = LODProfile.from_dict(profile(revision)); report = evaluate_lod_measurements(blocked, measurements(blocked, shapes=["Basis", "Smile"])); assert next(item for item in report["rules"] if item["rule_id"] == "source_shape_key_policy")["state"] == "BLOCK"
    explicit = LODProfile.from_dict(profile(revision, shape_policy="drop_explicit")); report = evaluate_lod_measurements(explicit, measurements(explicit, shapes=["Basis", "Smile"])); assert report["status"] == "warn" and next(item for item in report["rules"] if item["rule_id"] == "shape_key_inventory")["state"] == "WARN"


def make_runner(tmp_path: Path, *, tamper: bool = False) -> tuple[LODRunner, Path, Path, AssetRevision]:
    install, inputs, work = tmp_path / "install", tmp_path / "inputs", tmp_path / "work"
    for item in (install, inputs, work): item.mkdir(parents=True, exist_ok=False)
    executable = install / ("blender.exe" if os.name == "nt" else "blender"); executable.write_bytes(b"fake-r10.9"); content = b"r10.9-runner-source"; source = inputs / "source.blend"; source.write_bytes(content); revision = source_revision(content); boundary = BlenderExecutableBoundary(allowed_roots=(install,), staging_root=work); sandbox = ProcessSandbox(work, allowed_executables={"blender", "blender.exe"})
    class Fake(BlenderRunner):
        def _run_process(self, argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
            job = json.loads((cwd / "lod_job.json").read_text()); parsed = LODProfile.from_dict(job["profile"]); records = []
            for tier in parsed.tiers:
                payload = ("derived-" + tier.tier_id).encode(); filename = "lod_" + tier.tier_id + ".blend"; (cwd / filename).write_bytes(payload); records.append({"tier_id": tier.tier_id, "filename": filename, "bytes": len(payload), "sha256": digest(payload)})
            result = {**measurements(parsed), "status": "pass", "blockers": [], "input_file_sha256": parsed.input_blend_sha256, "artifacts": records}
            if tamper: result["profile_digest"] = "0" * 64
            (cwd / "lod_result.json").write_text(json.dumps(result), encoding="utf-8"); return RunnerProcessResult(0, "KODEPOIA_R10_9_RESULT=pass\n", "")
    return LODRunner(Fake(boundary, sandbox), input_root=inputs), executable, source, revision


def test_r10_9_runner_emits_verified_variants_and_preserves_input(tmp_path: Path) -> None:
    runner, executable, source, revision = make_runner(tmp_path); manifest = runner.run(executable, profile(revision), source_sha=SOURCE_SHA, input_blend=source, source_revision=revision)
    assert manifest["status"] == "pass" and manifest["blockers"] == [] and set(manifest["variant_revisions"]) == {"lod1", "lod2"} and all(item["role"] == "derived" for item in manifest["variant_revisions"].values()) and digest(source.read_bytes()) == revision.content_sha256
    Draft202012Validator(json.loads((ROOT / "schemas/r10-lod-manifest-v1.schema.json").read_text())).validate(manifest)


def test_r10_9_runner_blocks_result_tamper_and_no_variants(tmp_path: Path) -> None:
    runner, executable, source, revision = make_runner(tmp_path, tamper=True); manifest = runner.run(executable, profile(revision), source_sha=SOURCE_SHA, input_blend=source, source_revision=revision)
    assert manifest["status"] == "block" and "profile_digest_mismatch" in manifest["blockers"] and manifest["variant_revisions"] == {}


def test_r10_9_bootstrap_surface_is_fixed_offline_decimate_only() -> None:
    compile(LOD_BOOTSTRAP_SOURCE, "lod_bootstrap.py", "exec"); tree = ast.parse(LOD_BOOTSTRAP_SOURCE); forbidden = {"socket", "http", "urllib", "requests", "ftplib", "subprocess"}; imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module: imports.add(node.module.split(".")[0])
    assert not imports & forbidden
    lowered = LOD_BOOTSTRAP_SOURCE.lower()
    for token in ("exec(", "eval(", "bpy.ops.wm.url_open", "bpy.data.texts", "driver_add"): assert token not in lowered
    assert 'type="decimate"' in lowered and 'modifier.decimate_type = "collapse"' in lowered and "modifier_apply" in lowered and "shape_key_clear" in lowered and "use_scripts=false" in lowered
