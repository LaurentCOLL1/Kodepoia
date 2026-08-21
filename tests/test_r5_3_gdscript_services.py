from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.kodegodot import GDScriptInspector, GodotEditorServices, GodotServicePorts, GodotToolAPI


SCRIPT = '''class_name PlayerController
extends CharacterBody3D

signal died
var speed: float = 5.0
var health = 100
const MAX_HEALTH: int = 100

func _ready() -> void:
    pass

func damage(amount: int):
    health -= amount
'''


class FakeProcess:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeSandbox:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Path | None]] = []
        self.process = FakeProcess()

    def spawn_piped(self, argv: list[str], *, cwd: Path | None = None, env=None):
        del env
        self.calls.append((list(argv), cwd))
        return self.process


def test_gdscript_inspector_reports_structure_and_typing(tmp_path: Path) -> None:
    (tmp_path / "player.gd").write_text(SCRIPT, encoding="utf-8")
    info = GDScriptInspector(tmp_path).inspect("player.gd")
    assert info.class_name == "PlayerController"
    assert info.extends == "CharacterBody3D"
    assert info.signals == ("died",)
    assert [item.name for item in info.functions] == ["_ready", "damage"]
    assert info.functions[0].return_type == "void"
    assert info.functions[1].return_type is None
    assert {item.name: item.declared_type for item in info.variables} == {
        "speed": "float",
        "health": None,
        "MAX_HEALTH": "int",
    }
    assert info.typed_function_ratio == 0.5
    assert info.typed_variable_ratio == pytest.approx(2 / 3)


def test_service_ports_are_bounded_and_distinct() -> None:
    assert GodotServicePorts().lsp == 6005
    assert GodotServicePorts().dap == 6006
    with pytest.raises(ValueError):
        GodotServicePorts(80, 6006)
    with pytest.raises(ValueError):
        GodotServicePorts(6005, 6005)


def test_services_construct_only_managed_loopback_godot_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "project.godot").write_text("config_version=5\n", encoding="utf-8")
    sandbox = FakeSandbox()
    services = GodotEditorServices(tmp_path, executable="godot", sandbox=sandbox)  # type: ignore[arg-type]
    monkeypatch.setattr(GodotEditorServices, "_wait_loopback", staticmethod(lambda port, deadline: None))
    result = services.start(GodotServicePorts(6105, 6106), timeout=5)
    assert result["started"] is True
    assert sandbox.calls[0][0] == [
        "godot", "--headless", "--editor", "--path", ".",
        "--lsp-port", "6105", "--dap-port", "6106",
    ]
    services.close()
    assert sandbox.process.closed is True


def test_godot_tool_catalog_never_exposes_remote_host_or_arbitrary_launch_fields(tmp_path: Path) -> None:
    (tmp_path / "project.godot").write_text("config_version=5\n", encoding="utf-8")
    api = GodotToolAPI(tmp_path)
    catalog = api.catalog()
    names = {entry["function"]["name"] for entry in catalog}
    assert {
        "kodegodot_gdscript_inspect",
        "kodegodot_services_start",
        "kodegodot_services_stop",
        "kodegodot_lsp_symbols",
        "kodegodot_lsp_diagnostics",
        "kodegodot_dap_initialize",
        "kodegodot_dap_launch_project",
        "kodegodot_dap_threads",
    } <= names
    forbidden = {"host", "hostname", "argv", "args", "flags", "program", "command", "cwd"}
    for entry in catalog:
        params = entry["function"]["parameters"]
        assert params["additionalProperties"] is False
        assert forbidden.isdisjoint(params["properties"])
