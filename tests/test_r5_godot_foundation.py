from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from kodepoia.core.sandbox import SandboxResult
from kodepoia.kodecode.workspace import WorkspaceViolation
from kodepoia.kodegodot import GodotProjectInspector, GodotRuntime, GodotToolAPI


class FakeRunner:
    def __init__(self, results: list[SandboxResult] | None = None) -> None:
        self.results = list(results or [])
        self.calls: list[tuple[list[str], Path | None, float]] = []

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        del env
        self.calls.append((list(argv), cwd, timeout))
        if self.results:
            return self.results.pop(0)
        return SandboxResult(0, "", "")


def _write_project(root: Path) -> None:
    (root / "project.godot").write_text(
        'config_version=5\n\n'
        '[application]\n'
        'config/name="Demo"\n'
        'run/main_scene="uid://abc123"\n'
        'config/features=PackedStringArray("4.7", "GL Compatibility")\n\n'
        '[rendering]\n'
        'renderer/rendering_method="gl_compatibility"\n'
        'renderer/rendering_method.mobile="gl_compatibility"\n',
        encoding="utf-8",
    )


def test_project_inspector_reads_metadata_without_evaluating_variants(tmp_path: Path) -> None:
    _write_project(tmp_path)
    (tmp_path / "main.gd").write_text("extends Node\n", encoding="utf-8")
    (tmp_path / "main.tscn").write_text('[gd_scene format=3]\n', encoding="utf-8")
    (tmp_path / "theme.tres").write_text('[gd_resource type="Theme" format=3]\n', encoding="utf-8")
    (tmp_path / "fx.gdshader").write_text("shader_type canvas_item;\n", encoding="utf-8")

    info = GodotProjectInspector(tmp_path).inspect()
    assert info.config_version == 5
    assert info.name == "Demo"
    assert info.main_scene == "uid://abc123"
    assert info.rendering_method == "gl_compatibility"
    assert info.features == ("4.7", "GL Compatibility")
    assert (info.scripts, info.scenes, info.resources, info.shaders) == (1, 1, 1, 1)


def test_runtime_version_accepts_only_target_family(tmp_path: Path) -> None:
    good = FakeRunner([SandboxResult(0, "4.7.stable.official.abcdef\n", "")])
    runtime = GodotRuntime(tmp_path, executable="godot", runner=good)
    info = runtime.require_47()
    assert info.major == 4 and info.minor == 7 and info.compatible_47

    bad = FakeRunner([SandboxResult(0, "4.6.4.stable.official\n", "")])
    with pytest.raises(RuntimeError, match="requires Godot 4.7.x"):
        GodotRuntime(tmp_path, executable="godot", runner=bad).require_47()


def test_runtime_builds_only_named_bounded_commands(tmp_path: Path) -> None:
    _write_project(tmp_path)
    (tmp_path / "main.gd").write_text("extends Node\n", encoding="utf-8")
    (tmp_path / "main.tscn").write_text('[gd_scene format=3]\n', encoding="utf-8")
    runner = FakeRunner()
    runtime = GodotRuntime(tmp_path, executable="godot", runner=runner)

    assert runtime.check_script("main.gd").ok
    assert runner.calls[-1][0] == [
        "godot", "--headless", "--path", ".", "--check-only", "--script", "main.gd"
    ]

    assert runtime.import_project(timeout=12).ok
    assert runner.calls[-1][0] == ["godot", "--headless", "--path", ".", "--import"]

    assert runtime.smoke_project(scene="main.tscn", quit_after=3).ok
    assert runner.calls[-1][0] == [
        "godot", "--headless", "--path", ".", "--quit-after", "3",
        "--scene", "res://main.tscn",
    ]


def test_runtime_rejects_workspace_escape_and_bad_bounds(tmp_path: Path) -> None:
    _write_project(tmp_path)
    runner = FakeRunner()
    runtime = GodotRuntime(tmp_path, runner=runner)

    with pytest.raises(WorkspaceViolation):
        runtime.check_script("../outside.gd")
    with pytest.raises(ValueError, match="quit_after"):
        runtime.smoke_project(quit_after=0)
    assert runner.calls == []


def test_tool_catalog_exposes_no_arbitrary_argv_or_flags(tmp_path: Path) -> None:
    _write_project(tmp_path)
    runner = FakeRunner([SandboxResult(0, "4.7.stable.official\n", "")])
    api = GodotToolAPI(tmp_path, runtime=GodotRuntime(tmp_path, runner=runner))
    catalog = api.catalog()
    names = {entry["function"]["name"] for entry in catalog}
    assert {
        "kodegodot_project_inspect",
        "kodegodot_document_parse",
        "kodegodot_document_dependencies",
        "kodegodot_engine_version",
        "kodegodot_check_script",
        "kodegodot_import_project",
        "kodegodot_smoke_project",
    } <= names
    for entry in catalog:
        properties = entry["function"]["parameters"]["properties"]
        assert "argv" not in properties
        assert "args" not in properties
        assert "flags" not in properties
        assert entry["function"]["parameters"]["additionalProperties"] is False

    version = api.invoke("kodegodot_engine_version")
    assert version["compatible_47"] is True
    assert asdict(GodotProjectInspector(tmp_path).inspect())["project_file"] == "project.godot"


def test_tool_timeout_is_bounded_even_without_json_schema_validator(tmp_path: Path) -> None:
    _write_project(tmp_path)
    api = GodotToolAPI(tmp_path, runtime=GodotRuntime(tmp_path, runner=FakeRunner()))
    with pytest.raises(ValueError, match="timeout"):
        api.invoke("kodegodot_import_project", {"timeout": 901})
