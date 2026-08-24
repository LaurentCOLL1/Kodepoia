from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.cli import build_parser


def _evidence_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    evidence_dir = root / "docs" / "roadmap"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "R10_10_LOCAL_ACCEPTANCE.json").write_text(
        json.dumps(
            {
                "schema": "kodepoia.r10.gltf_local_acceptance",
                "version": 1,
                "source_sha": "8" * 40,
                "status": "pass",
                "blockers": [],
                "blender": {
                    "version": "5.2.0 LTS",
                    "background": True,
                    "online_access": False,
                },
                "godot": {"version": {"raw": "4.7.2.stable"}},
            }
        ),
        encoding="utf-8",
    )
    return root


def test_blender3d_cli_registers_bounded_service_commands() -> None:
    parser = build_parser()
    for argv, operation in (
        (["blender3d", "status"], "status"),
        (["blender3d", "capabilities"], "capabilities"),
        (["blender3d", "geometry", "--id", "demo.cube"], "geometry"),
        (["blender3d", "qa", "--id", "mesh.qa"], "qa"),
        (["blender3d", "rig", "--id", "rig.demo"], "rig"),
        (["blender3d", "animation", "--id", "anim.demo"], "animation"),
        (["blender3d", "lod", "--id", "lod.demo"], "lod"),
        (["blender3d", "export", "--id", "export.demo"], "export"),
        (["blender3d", "evidence", "--id", "r10.10"], "evidence"),
        (
            ["blender3d", "inspect", "--kind", "qa", "--id", "mesh.qa"],
            "inspect",
        ),
    ):
        args = parser.parse_args(argv)
        assert args.blender_operation == operation


@pytest.mark.parametrize(
    "argv",
    [
        ["blender3d", "status", "--python", "bad.py"],
        ["blender3d", "status", "--expr", "print(1)"],
        ["blender3d", "status", "--executable", "blender.exe"],
        ["blender3d", "qa", "--id", "mesh.qa", "--path", "C:\\tmp\\x.json"],
        ["blender3d", "qa", "--id", "mesh.qa", "--argv", "--background"],
        ["blender3d", "evidence", "--id", "r10.99"],
    ],
)
def test_blender3d_cli_rejects_raw_process_python_and_path_surfaces(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(argv)


def test_blender3d_cli_status_uses_service_and_prints_structured_result(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    root = _evidence_root(tmp_path)
    monkeypatch.chdir(root)
    args = build_parser().parse_args(["blender3d", "status"])
    assert args.func(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation"] == "status"
    assert payload["state"] == "ready"
    assert payload["payload"]["runtime_evidence"]["blender_version"] == "5.2.0 LTS"


def test_blender3d_cli_missing_managed_record_is_explicit_not_fabricated(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    root = _evidence_root(tmp_path)
    monkeypatch.chdir(root)
    args = build_parser().parse_args(["blender3d", "qa", "--id", "missing.qa"])
    assert args.func(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["state"] == "missing"
    assert payload["reason"] == "managed_report_missing"
