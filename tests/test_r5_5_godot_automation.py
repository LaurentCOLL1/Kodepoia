from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.core.sandbox import SandboxResult
from kodepoia.kodegodot import GodotExportPresetInspector, GodotRuntime, GodotToolAPI


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Path | None, float]] = []

    def run(self, argv: list[str], *, cwd: Path | None = None, timeout: float = 60.0, env=None) -> SandboxResult:
        del env
        self.calls.append((list(argv), cwd, timeout))
        return SandboxResult(0, "", "")


def _fixture(root: Path) -> None:
    (root / "project.godot").write_text("config_version=5\n", encoding="utf-8")
    (root / "main.tscn").write_text('[gd_scene format=3]\n[node name="Root" type="Node"]\n', encoding="utf-8")
    (root / "export_presets.cfg").write_text(
        '[preset.0]\nname="Windows Desktop"\nplatform="Windows Desktop"\nrunnable=true\n\n'
        '[preset.0.options]\ncustom_template/debug=""\n',
        encoding="utf-8",
    )


def test_export_preset_inspector_reads_only_preset_metadata(tmp_path: Path) -> None:
    _fixture(tmp_path)
    presets = GodotExportPresetInspector(tmp_path).presets()
    assert len(presets) == 1
    assert presets[0].name == "Windows Desktop"
    assert presets[0].platform == "Windows Desktop"
    assert presets[0].runnable is True


def test_runtime_builds_confined_export_and_movie_commands(tmp_path: Path) -> None:
    _fixture(tmp_path)
    runner = FakeRunner()
    runtime = GodotRuntime(tmp_path, executable="godot", runner=runner)

    result = runtime.export_project(preset="Windows Desktop", output_name="demo.exe", mode="release", timeout=30)
    assert result.ok
    assert runner.calls[-1][0] == [
        "godot", "--headless", "--path", ".", "--export-release", "Windows Desktop", ".kodepoia/exports/demo.exe"
    ]

    result = runtime.capture_movie(scene="main.tscn", output_name="smoke.avi", frames=90, fps=30, timeout=30)
    assert result.ok
    # Movie Maker needs a real renderer; --headless would select the dummy
    # RenderingServer and cannot produce valid frame textures.
    assert runner.calls[-1][0] == [
        "godot", "--path", ".", "--write-movie", ".kodepoia/captures/smoke.avi",
        "--fixed-fps", "30", "--quit-after", "90", "--scene", "res://main.tscn",
    ]


def test_runtime_rejects_unknown_preset_and_output_path_escape(tmp_path: Path) -> None:
    _fixture(tmp_path)
    runner = FakeRunner()
    runtime = GodotRuntime(tmp_path, runner=runner)
    with pytest.raises(ValueError, match="preset"):
        runtime.export_project(preset="Missing", output_name="demo.exe")
    with pytest.raises(ValueError, match="simple file name"):
        runtime.export_project(preset="Windows Desktop", output_name="../demo.exe")
    with pytest.raises(ValueError, match=".avi"):
        runtime.capture_movie(scene="main.tscn", output_name="movie.mp4")
    assert runner.calls == []


def test_benchmark_is_bounded_and_returns_invocation(tmp_path: Path) -> None:
    _fixture(tmp_path)
    runtime = GodotRuntime(tmp_path, runner=FakeRunner())
    result = runtime.benchmark_scene(scene="main.tscn", frames=12, timeout=30)
    assert result.frames == 12
    assert result.elapsed_seconds > 0
    assert result.effective_fps > 0
    assert result.invocation.ok
    with pytest.raises(ValueError, match="benchmark frames"):
        runtime.benchmark_scene(frames=0)


def test_tool_catalog_has_named_automation_only(tmp_path: Path) -> None:
    _fixture(tmp_path)
    api = GodotToolAPI(tmp_path, runtime=GodotRuntime(tmp_path, runner=FakeRunner()))
    catalog = {entry["function"]["name"]: entry for entry in api.catalog()}
    assert {"kodegodot_export_presets", "kodegodot_export_project", "kodegodot_capture_movie", "kodegodot_benchmark_scene"} <= set(catalog)
    for name in ("kodegodot_export_project", "kodegodot_capture_movie"):
        props = catalog[name]["function"]["parameters"]["properties"]
        assert "output_path" not in props
        assert "argv" not in props
        assert catalog[name]["function"]["parameters"]["additionalProperties"] is False
