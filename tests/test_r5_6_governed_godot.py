from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.exceptions import PermissionDenied
from kodepoia.kodegodot import GodotServicePorts, GodotToolAPI
from kodepoia.kodegodot.acceptance import R5AcceptanceRunner
from kodepoia.kodegodot.executor import KodeGodotExecutor
from kodepoia.kodegodot.services import GodotEditorServices
from kodepoia.orchestrator.runtime import Orchestrator


class FakeRuntime:
    executable = "godot"


class FakeProcess:
    returncode = None

    def close(self) -> None:
        self.returncode = 0


class FakeSandbox:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Path]] = []

    def spawn_background(self, argv: list[str], *, cwd: Path, env: object = None) -> FakeProcess:
        del env
        self.calls.append((list(argv), cwd))
        return FakeProcess()


def _project(root: Path) -> None:
    (root / "project.godot").write_text('config_version=5\n', encoding="utf-8")
    (root / "main.tscn").write_text(
        '[gd_scene format=3]\n\n[node name="Root" type="Node2D"]\nprocess_mode = 0\n',
        encoding="utf-8",
    )


def _executor(root: Path, *, write: bool = True, execute: bool = True) -> KodeGodotExecutor:
    permissions = PermissionSet()
    permissions.grant(PermissionGrant(Capability.FILE_READ, roots=(root,)))
    if write:
        permissions.grant(PermissionGrant(Capability.FILE_WRITE, roots=(root,)))
    if execute:
        permissions.grant(PermissionGrant(Capability.PROCESS_EXECUTE, executables=("godot",)))
    return KodeGodotExecutor(
        root,
        guardian=KodeGuardian(permissions),
        audit=AuditLog(root / ".kodepoia" / "audit.jsonl"),
        safe_change=SafeChangeManager(root, root / ".kodepoia" / "snapshots"),
        api=GodotToolAPI(root, runtime=FakeRuntime()),
    )


def test_scene_write_is_snapshotted_and_audited(tmp_path: Path) -> None:
    _project(tmp_path)
    executor = _executor(tmp_path)
    scene = tmp_path / "main.tscn"
    sha = hashlib.sha256(scene.read_bytes()).hexdigest()
    result = executor.invoke(
        "kodegodot_scene_set_existing_property",
        {"path": "main.tscn", "node": "Root", "property": "process_mode", "raw_value": "3", "expected_sha256": sha},
    )
    assert result.snapshot is not None
    assert "process_mode = 3" in scene.read_text(encoding="utf-8")
    assert executor.audit.verify()


def test_import_requires_explicit_file_write_permission(tmp_path: Path) -> None:
    _project(tmp_path)
    executor = _executor(tmp_path, write=False)
    with pytest.raises(PermissionDenied):
        executor.invoke("kodegodot_import_project")


def test_godot_service_ports_follow_documented_safe_range() -> None:
    ports = GodotServicePorts(6005, 6006, 6007)
    assert (ports.lsp, ports.dap, ports.debug) == (6005, 6006, 6007)
    with pytest.raises(ValueError):
        GodotServicePorts(49152, 6006, 6007)
    with pytest.raises(ValueError):
        GodotServicePorts(6005, 6005, 6007)


def test_services_build_loopback_debug_server_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _project(tmp_path)
    sandbox = FakeSandbox()
    services = GodotEditorServices(tmp_path, sandbox=sandbox)

    def fake_lsp(*, timeout: float = 10.0):
        del timeout
        services.lsp = SimpleNamespace(initialized=True)
        return services.lsp

    def fake_dap(*, timeout: float = 10.0):
        del timeout
        services.dap = SimpleNamespace(initialized=True)
        return services.dap

    monkeypatch.setattr(services, "connect_lsp", fake_lsp)
    monkeypatch.setattr(services, "connect_dap", fake_dap)
    result = services.start(GodotServicePorts(), timeout=5)
    assert result["lsp_initialized"] is True
    assert result["dap_initialized"] is True
    assert result["log"] == ".kodepoia/logs/godot-services.log"
    assert sandbox.calls[0][0] == [
        "godot", "--headless", "--editor", "--path", ".",
        "--log-file", ".kodepoia/logs/godot-services.log",
        "--lsp-port", "6005", "--dap-port", "6006",
        "--debug-server", "tcp://127.0.0.1:6007",
    ]


def test_tool_schema_has_no_remote_host_or_arbitrary_command_surface(tmp_path: Path) -> None:
    _project(tmp_path)
    api = GodotToolAPI(tmp_path, runtime=FakeRuntime())
    schemas = {item["function"]["name"]: item["function"]["parameters"] for item in api.catalog()}
    service = schemas["kodegodot_services_start"]["properties"]
    assert service["debug_port"]["maximum"] == 49151
    assert {"host", "address", "argv", "args", "flags", "command", "cwd"}.isdisjoint(service)
    for params in schemas.values():
        assert params["additionalProperties"] is False


def test_orchestrator_routes_godot_executor_without_bypassing_it() -> None:
    class StubGodot:
        def catalog(self):
            return [{"type": "function", "function": {"name": "kodegodot_test", "parameters": {}}}]

        def supports(self, name: str) -> bool:
            return name == "kodegodot_test"

        def invoke(self, name: str, arguments: dict | None, *, actor: str, confirmed: bool):
            return SimpleNamespace(tool_name=name, result={"actor": actor, "confirmed": confirmed, "arguments": arguments}, snapshot=None)

    orchestrator = Orchestrator(None, None, None, None, None, kodegodot_executor=StubGodot())  # type: ignore[arg-type]
    result = orchestrator.execute_tool("kodegodot_test", {"x": 1}, actor="brain")
    assert result["result"]["arguments"] == {"x": 1}
    assert result["result"]["actor"] == "brain"


def test_acceptance_fixture_is_generated_below_local_kodepoia_state(tmp_path: Path) -> None:
    runner = R5AcceptanceRunner(tmp_path, executable="godot")
    assert runner.workspace == tmp_path / ".kodepoia" / "r5-acceptance" / "project"
    assert (runner.workspace / "project.godot").is_file()
    assert (runner.workspace / "main.gd").is_file()
    assert (runner.workspace / "main.tscn").is_file()
    assert (runner.workspace / "export_presets.cfg").is_file()
