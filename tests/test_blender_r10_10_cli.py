from __future__ import annotations

import pytest

from kodepoia.cli import build_parser


def test_r10_10_cli_is_registered_with_bounded_defaults() -> None:
    parser = build_parser()
    args = parser.parse_args(["r10-gltf-accept", "--blender", "C:/Blender/blender.exe", "--godot", "C:/Godot/godot.exe", "--source-sha", "a" * 40])
    assert args.work_dir == ".kodepoia/blender/r10_10_work"
    assert args.output == ".kodepoia/blender/r10_10_local_acceptance.json"
    assert args.blender_timeout == 300.0
    assert args.godot_timeout == 300.0


def test_r10_10_cli_requires_both_real_runtime_paths() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["r10-gltf-accept", "--blender", "blender.exe", "--source-sha", "a" * 40])
