from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.blender3d import BlenderExecutableBoundary
from kodepoia.blender3d.probe_bootstrap import PROBE_BOOTSTRAP_SOURCE
from kodepoia.blender3d.runner import BlenderRunner, RunnerProcessResult
from kodepoia.core.sandbox import ProcessSandbox

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "a" * 40


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _make_runner(tmp_path: Path, result_factory):
    install = tmp_path / "install"
    work = tmp_path / "work"
    install.mkdir()
    work.mkdir()
    executable = install / ("blender.exe" if __import__("os").name == "nt" else "blender")
    executable.write_bytes(b"fake-blender-5.2")
    boundary = BlenderExecutableBoundary(allowed_roots=(install,), staging_root=work)
    sandbox = ProcessSandbox(work, allowed_executables={"blender", "blender.exe"})

    class FakeRunner(BlenderRunner):
        def _run_process(self, argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
            return result_factory(argv, cwd)

    return FakeRunner(boundary, sandbox), executable, work


def _success_result(_argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
    blend = b"blend-fixture"
    glb = b"glb-fixture"
    (cwd / "probe.blend").write_bytes(blend)
    (cwd / "probe.glb").write_bytes(glb)
    payload = {
        "schema": "kodepoia.blender.probe_result",
        "version": 1,
        "status": "pass",
        "blockers": [],
        "facts": {
            "blender_version": "5.2.0",
            "python_version": "3.11.9",
            "background": True,
            "online_access": False,
            "gltf_exporter_available": True,
            "bmesh_available": True,
            "object_count": 1,
            "mesh_count": 1,
            "vertex_count": 8,
            "face_count": 6,
            "bmesh_vertex_count": 8,
        },
        "artifacts": {
            "blend": {"filename": "probe.blend", "sha256": _sha(blend), "bytes": len(blend)},
            "glb": {"filename": "probe.glb", "sha256": _sha(glb), "bytes": len(glb)},
        },
    }
    (cwd / "probe_result.json").write_text(json.dumps(payload), encoding="utf-8")
    return RunnerProcessResult(0, "KODEPOIA_R10_2_RESULT=pass\n", "", stdout_bytes=34)


def test_r10_2_fake_probe_success_and_schema(tmp_path: Path) -> None:
    runner, executable, _work = _make_runner(tmp_path, _success_result)
    evidence = runner.run_capability_probe(executable, source_sha=SOURCE_SHA)
    assert evidence["status"] == "pass"
    assert evidence["blockers"] == []
    assert evidence["runtime"]["version"] == "5.2.0"
    assert evidence["probe"]["background"] is True
    assert evidence["probe"]["online_access"] is False
    assert evidence["artifacts"]["glb"]["sha256"] == _sha(b"glb-fixture")
    schema = json.loads((ROOT / "schemas/r10-local-blender-evidence-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(evidence)


@pytest.mark.parametrize(
    ("process", "expected"),
    [
        (RunnerProcessResult(9, "", "crash", stderr_bytes=5), "process_nonzero"),
        (RunnerProcessResult(-1, "", "", timed_out=True), "process_timed_out"),
        (RunnerProcessResult(-1, "", "", cancelled=True), "process_cancelled"),
        (RunnerProcessResult(0, "x", "", stdout_bytes=10, stdout_truncated=True), "stdout_limit_exceeded"),
    ],
)
def test_r10_2_process_failure_modes_are_not_pass(tmp_path: Path, process: RunnerProcessResult, expected: str) -> None:
    def factory(_argv: tuple[str, ...], _cwd: Path) -> RunnerProcessResult:
        return process

    runner, executable, _work = _make_runner(tmp_path, factory)
    evidence = runner.run_capability_probe(executable, source_sha=SOURCE_SHA)
    assert evidence["status"] == "fail"
    assert expected in evidence["blockers"]
    assert "result_invalid_or_missing" in evidence["blockers"]


def test_r10_2_malformed_result_is_blocked(tmp_path: Path) -> None:
    def factory(_argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
        (cwd / "probe_result.json").write_text("{not-json", encoding="utf-8")
        return RunnerProcessResult(0, "", "")

    runner, executable, _work = _make_runner(tmp_path, factory)
    evidence = runner.run_capability_probe(executable, source_sha=SOURCE_SHA)
    assert evidence["status"] == "fail"
    assert "result_invalid_or_missing" in evidence["blockers"]


def test_r10_2_artifact_path_spoof_is_blocked(tmp_path: Path) -> None:
    def factory(_argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
        blend = b"blend"
        glb = b"glb"
        (cwd / "probe.blend").write_bytes(blend)
        (cwd / "probe.glb").write_bytes(glb)
        payload = {
            "schema": "kodepoia.blender.probe_result",
            "version": 1,
            "status": "pass",
            "blockers": [],
            "facts": {
                "blender_version": "5.2.0",
                "python_version": "3.11.9",
                "background": True,
                "online_access": False,
                "gltf_exporter_available": True,
                "bmesh_available": True,
            },
            "artifacts": {
                "blend": {"filename": "../probe.blend", "sha256": _sha(blend), "bytes": len(blend)},
                "glb": {"filename": "probe.glb", "sha256": _sha(glb), "bytes": len(glb)},
            },
        }
        (cwd / "probe_result.json").write_text(json.dumps(payload), encoding="utf-8")
        return RunnerProcessResult(0, "", "")

    runner, executable, _work = _make_runner(tmp_path, factory)
    evidence = runner.run_capability_probe(executable, source_sha=SOURCE_SHA)
    assert evidence["status"] == "fail"
    assert "artifact_invalid_or_missing" in evidence["blockers"]


def test_r10_2_bootstrap_is_static_and_has_no_dynamic_code_or_network_surface() -> None:
    compile(PROBE_BOOTSTRAP_SOURCE, "probe_bootstrap.py", "exec")
    lowered = PROBE_BOOTSTRAP_SOURCE.lower()
    assert "exec(" not in lowered
    assert "eval(" not in lowered
    assert "subprocess" not in lowered
    assert "socket" not in lowered
    assert "urllib" not in lowered
    assert "requests" not in lowered
    assert "bpy.ops.export_scene.gltf" in PROBE_BOOTSTRAP_SOURCE


def test_r10_2_probe_result_schema_accepts_canonical_shape() -> None:
    schema = json.loads((ROOT / "schemas/r10-blender-probe-result-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(
        {
            "schema": "kodepoia.blender.probe_result",
            "version": 1,
            "status": "fail",
            "blockers": ["fixture"],
            "facts": {},
            "artifacts": {},
        }
    )
