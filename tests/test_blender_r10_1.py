from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.blender3d import (
    BlenderBoundaryError,
    BlenderExecutableBoundary,
    BlenderJobRecipe,
    BlenderJobState,
    BlenderOperation,
    BlenderRuntimeIdentity,
    BlenderRuntimePolicy,
    BlenderVersion,
    can_transition_job_state,
    canonical_sha256,
    make_envelope,
    validate_environment_overrides,
)

ROOT = Path(__file__).resolve().parents[1]


def test_r10_1_runtime_policy_targets_blender_5_2_lts() -> None:
    policy = BlenderRuntimePolicy()
    assert policy.supports(BlenderVersion.parse("5.2.0"))
    assert policy.supports(BlenderVersion.parse("5.2.7 LTS"))
    assert not policy.supports(BlenderVersion.parse("5.1.9"))
    assert not policy.supports(BlenderVersion.parse("5.3.0"))
    assert not policy.supports(BlenderVersion.parse("4.5.12"))


def test_r10_1_job_state_machine_is_fail_closed() -> None:
    assert can_transition_job_state(BlenderJobState.PLANNED, BlenderJobState.STAGED)
    assert can_transition_job_state(BlenderJobState.STAGED, BlenderJobState.RUNNING)
    assert can_transition_job_state(BlenderJobState.RUNNING, BlenderJobState.SUCCEEDED)
    assert not can_transition_job_state(BlenderJobState.SUCCEEDED, BlenderJobState.RUNNING)
    assert not can_transition_job_state(BlenderJobState.PLANNED, BlenderJobState.SUCCEEDED)


def test_r10_1_recipe_identity_is_deterministic_and_rejects_escape_keys() -> None:
    recipe = BlenderJobRecipe(
        BlenderOperation.INSPECT_ASSET,
        parameters=(("detail_level", 2), ("include_materials", True)),
        input_revision_ids=("rev-b", "rev-a", "rev-a"),
    )
    first = canonical_sha256(recipe.canonical())
    second = canonical_sha256(recipe.canonical())
    assert first == second
    assert recipe.input_revision_ids == ("rev-a", "rev-b")
    with pytest.raises(ValueError, match="Forbidden"):
        BlenderJobRecipe(BlenderOperation.INSPECT_ASSET, parameters=(("python", "print(1)"),))
    with pytest.raises(ValueError, match="Forbidden"):
        BlenderJobRecipe(BlenderOperation.INSPECT_ASSET, parameters=(("argv", "--python-expr"),))


def test_r10_1_runtime_identity_is_canonical() -> None:
    identity = BlenderRuntimeIdentity(
        executable="/opt/blender/blender",
        version=BlenderVersion(5, 2, 1),
        platform="linux-x86_64",
        capabilities=("gltf", "bpy", "gltf"),
    )
    assert identity.capabilities == ("bpy", "gltf")
    assert identity.canonical()["version"] == "5.2.1"


def test_r10_1_executable_and_script_boundary_builds_fixed_argv(tmp_path: Path) -> None:
    install = tmp_path / "install"
    stage = tmp_path / "stage"
    install.mkdir()
    stage.mkdir()
    executable = install / ("blender.exe" if __import__("os").name == "nt" else "blender")
    executable.write_bytes(b"fixture")
    script = stage / "job.py"
    script.write_text("# generated fixture\n", encoding="utf-8")
    boundary = BlenderExecutableBoundary(allowed_roots=(install,), staging_root=stage)
    argv = boundary.build_job_argv(executable, script)
    assert argv[1:] == (
        "--background",
        "--factory-startup",
        "--disable-autoexec",
        "--offline-mode",
        "--python-exit-code",
        "17",
        "--python",
        str(script.resolve()),
    )
    assert "--python-expr" not in argv
    assert "--python-text" not in argv
    assert "--python-use-system-env" not in argv


def test_r10_1_boundary_rejects_path_escape_and_wrong_executable_name(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    stage = tmp_path / "stage"
    allowed.mkdir()
    outside.mkdir()
    stage.mkdir()
    outside_blender = outside / "blender"
    outside_blender.write_bytes(b"fixture")
    wrong_name = allowed / "python"
    wrong_name.write_bytes(b"fixture")
    boundary = BlenderExecutableBoundary(allowed_roots=(allowed,), staging_root=stage)
    with pytest.raises(BlenderBoundaryError, match="escapes"):
        boundary.validate_candidate(outside_blender)
    with pytest.raises(BlenderBoundaryError, match="Unexpected"):
        boundary.validate_candidate(wrong_name)


def test_r10_1_environment_rejects_python_and_blender_injection() -> None:
    assert validate_environment_overrides({"KODEPOIA_RUN_ID": "run-1"}) == {"KODEPOIA_RUN_ID": "run-1"}
    for key in ("PYTHONPATH", "PYTHONHOME", "BLENDER_USER_SCRIPTS", "PATH"):
        with pytest.raises(BlenderBoundaryError):
            validate_environment_overrides({key: "evil"})


def test_r10_1_schema_roots_validate_representative_documents() -> None:
    recipe = BlenderJobRecipe(BlenderOperation.VALIDATE_MESH, parameters=(("strict", True),))
    documents = {
        "r10-blender-job-v1.schema.json": make_envelope(
            schema="kodepoia.blender.job", version=1, payload=recipe.canonical()
        ),
        "r10-blender-capability-v1.schema.json": make_envelope(
            schema="kodepoia.blender.capability",
            version=1,
            payload=BlenderRuntimeIdentity(
                executable="/opt/blender/blender",
                version=BlenderVersion(5, 2, 0),
                platform="linux-x86_64",
                capabilities=("bpy",),
            ).canonical(),
        ),
        "r10-blender-qa-v1.schema.json": make_envelope(schema="kodepoia.blender.qa", version=1, payload={}),
        "r10-blender-export-v1.schema.json": make_envelope(
            schema="kodepoia.blender.export", version=1, payload={}
        ),
        "r10-blender-local-acceptance-v1.schema.json": make_envelope(
            schema="kodepoia.blender.local_acceptance", version=1, payload={}
        ),
    }
    for filename, document in documents.items():
        schema = json.loads((ROOT / "schemas" / filename).read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(document)


def test_r10_1_boundary_module_does_not_launch_processes() -> None:
    source = (ROOT / "src/kodepoia/blender3d/boundary.py").read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert ".run(" not in source
    assert "Popen" not in source
