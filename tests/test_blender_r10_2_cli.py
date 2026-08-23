from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.blender3d.blender_cli import _project_relative
from kodepoia.cli import build_parser


def test_r10_2_cli_registers_required_local_acceptance_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "r10-blender-accept",
            "--blender",
            "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe",
            "--source-sha",
            "a" * 40,
        ]
    )
    assert args.command == "r10-blender-accept"
    assert args.source_sha == "a" * 40
    assert args.work_dir == ".kodepoia/blender/r10_2_work"
    assert args.output == ".kodepoia/blender/r10_2_local_acceptance.json"
    assert args.timeout == 180.0
    assert callable(args.func)


def test_r10_2_cli_confines_project_relative_paths(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    assert _project_relative(root, ".kodepoia/blender/evidence.json", field="--output") == (
        root / ".kodepoia/blender/evidence.json"
    ).resolve()
    with pytest.raises(SystemExit, match="project-relative"):
        _project_relative(root, str((root / "absolute.json").resolve()), field="--output")
    with pytest.raises(SystemExit, match="escapes"):
        _project_relative(root, "../outside.json", field="--output")
