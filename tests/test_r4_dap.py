from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from kodepoia.kodecode.api import KodeCodeToolAPI
from kodepoia.kodecode.dap import (
    DapSession,
    DebugAdapterSpec,
    DebugConfigurationSpec,
)


class ScriptedChannel:
    def __init__(self, incoming: list[dict[str, Any]]) -> None:
        self.incoming = list(incoming)
        self.sent: list[dict[str, Any]] = []
        self.closed = False

    def send(self, message: dict[str, Any]) -> None:
        self.sent.append(message)

    def receive(self, _timeout: float = 30.0) -> dict[str, Any]:
        if not self.incoming:
            raise AssertionError("No scripted DAP message remains")
        return self.incoming.pop(0)

    def close(self) -> None:
        self.closed = True


def response(request_seq: int, command: str, body: Any = None) -> dict[str, Any]:
    return {
        "seq": 100 + request_seq,
        "type": "response",
        "request_seq": request_seq,
        "success": True,
        "command": command,
        "body": body,
    }


def test_dap_lifecycle_breakpoints_stack_scopes_variables(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("x = 42\nprint(x)\n", encoding="utf-8")
    config = DebugConfigurationSpec("run-safe", "launch", {"program": str(source.resolve())})
    spec = DebugAdapterSpec("fake", ("fake-adapter",), configurations=(config,))
    channel = ScriptedChannel(
        [
            response(1, "initialize", {"supportsConfigurationDoneRequest": True}),
            {"seq": 200, "type": "event", "event": "initialized", "body": {}},
            response(2, "launch", {}),
            response(3, "setBreakpoints", {"breakpoints": [{"verified": True, "line": 2}]}),
            response(4, "configurationDone", {}),
            {
                "seq": 201,
                "type": "request",
                "command": "runInTerminal",
                "arguments": {"args": ["dangerous"]},
            },
            response(5, "threads", {"threads": [{"id": 1, "name": "main"}]}),
            response(
                7,
                "stackTrace",
                {"stackFrames": [{"id": 10, "name": "main", "line": 2, "column": 1}]},
            ),
            response(8, "scopes", {"scopes": [{"name": "Locals", "variablesReference": 20}]}),
            response(
                9,
                "variables",
                {"variables": [{"name": "x", "value": "42", "variablesReference": 0}]},
            ),
            response(10, "disconnect", {}),
        ]
    )
    session = DapSession(spec, tmp_path, channel)  # type: ignore[arg-type]

    capabilities = session.initialize()
    launched = session.start_configuration(config)
    breakpoints = session.set_breakpoints(source, [2])
    session.configuration_done()
    threads = session.threads()
    stack = session.stack_trace(1)
    scopes = session.scopes(10)
    variables = session.variables(20)
    session.disconnect()

    assert capabilities["supportsConfigurationDoneRequest"] is True
    assert launched == {}
    assert breakpoints["breakpoints"][0]["verified"] is True
    assert threads[0]["name"] == "main"
    assert stack[0]["id"] == 10
    assert scopes[0]["variablesReference"] == 20
    assert variables[0]["value"] == "42"
    assert channel.closed is True
    assert any(item.get("event") == "initialized" for item in session.events)

    rejected = next(
        item
        for item in channel.sent
        if item.get("type") == "response" and item.get("request_seq") == 201
    )
    assert rejected["success"] is False
    assert rejected["command"] == "runInTerminal"

    commands = [item["command"] for item in channel.sent if item.get("type") == "request"]
    assert commands == [
        "initialize",
        "launch",
        "setBreakpoints",
        "configurationDone",
        "threads",
        "stackTrace",
        "scopes",
        "variables",
        "disconnect",
    ]


def test_dap_source_must_remain_inside_workspace(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-r4-dap.py"
    outside.write_text("print('outside')\n", encoding="utf-8")
    spec = DebugAdapterSpec("fake", ("fake-adapter",))
    session = DapSession(spec, tmp_path, ScriptedChannel([]))  # type: ignore[arg-type]

    with pytest.raises(PermissionError, match="escapes workspace"):
        session.set_breakpoints(outside, [1])

    outside.unlink()


def test_structured_dap_api_hides_argv_and_launch_arguments(tmp_path: Path) -> None:
    config = DebugConfigurationSpec(
        "safe-run",
        "launch",
        {"program": "sample.py", "secretAdapterOption": "not-model-visible"},
    )
    adapter = DebugAdapterSpec(
        "python-debug",
        (sys.executable, "adapter.py"),
        configurations=(config,),
    )
    api = KodeCodeToolAPI(tmp_path, debug_adapters=(adapter,))
    catalog = {item["function"]["name"]: item for item in api.catalog()}

    configure_props = catalog["kodecode_dap_configure"]["function"]["parameters"]["properties"]
    start_props = catalog["kodecode_dap_start"]["function"]["parameters"]["properties"]
    assert set(configure_props) == {"adapter_id", "config_id"}
    assert set(start_props) == {"adapter_id"}
    assert "argv" not in start_props
    assert "arguments" not in configure_props

    capability = api.invoke("kodecode_dap_capabilities")[0]
    assert capability["adapter_id"] == "python-debug"
    assert capability["configurations"][0]["arguments"] == "<pre-registered>"


def test_debug_configuration_validation() -> None:
    with pytest.raises(ValueError, match="launch or attach"):
        DebugConfigurationSpec("bad", "shell", {})
    with pytest.raises(ValueError, match="Duplicate"):
        DebugAdapterSpec(
            "dup",
            ("adapter",),
            configurations=(
                DebugConfigurationSpec("same", "launch", {}),
                DebugConfigurationSpec("same", "attach", {}),
            ),
        )
