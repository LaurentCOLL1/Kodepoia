from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any

import pytest

from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.kodecode.api import KodeCodeToolAPI
from kodepoia.kodecode.lsp import LanguageServerSpec, LspSession
from kodepoia.kodecode.protocol import ContentLengthJsonStream, ProtocolError


class ScriptedChannel:
    def __init__(self, incoming: list[dict[str, Any]]) -> None:
        self.incoming = list(incoming)
        self.sent: list[dict[str, Any]] = []
        self.closed = False

    def send(self, message: dict[str, Any]) -> None:
        self.sent.append(message)

    def receive(self, _timeout: float = 30.0) -> dict[str, Any]:
        if not self.incoming:
            raise AssertionError("No scripted LSP message remains")
        return self.incoming.pop(0)

    def close(self) -> None:
        self.closed = True


def test_content_length_json_stream_round_trip() -> None:
    output = io.BytesIO()
    writer = ContentLengthJsonStream(io.BytesIO(), output)
    writer.write({"jsonrpc": "2.0", "id": 1, "result": {"value": "é"}})

    reader = ContentLengthJsonStream(io.BytesIO(output.getvalue()), io.BytesIO())
    message = reader.read()

    assert message["jsonrpc"] == "2.0"
    assert message["result"]["value"] == "é"


def test_content_length_json_stream_rejects_missing_length() -> None:
    reader = ContentLengthJsonStream(io.BytesIO(b"Other: 1\r\n\r\n{}"), io.BytesIO())
    with pytest.raises(ProtocolError, match="Content-Length"):
        reader.read()


def test_lsp_session_lifecycle_navigation_and_diagnostics(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("def answer():\n    return 42\n", encoding="utf-8")
    uri = source.resolve().as_uri()
    channel = ScriptedChannel(
        [
            {
                "jsonrpc": "2.0",
                "id": 99,
                "method": "workspace/configuration",
                "params": {"items": []},
            },
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"capabilities": {"documentSymbolProvider": True}},
            },
            {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {
                    "uri": uri,
                    "diagnostics": [{"severity": 2, "message": "demo warning"}],
                },
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "result": [{"name": "answer", "kind": 12}],
            },
            {"jsonrpc": "2.0", "id": 3, "result": {"uri": uri, "range": {}}},
            {"jsonrpc": "2.0", "id": 4, "result": [{"uri": uri, "range": {}}]},
            {"jsonrpc": "2.0", "id": 5, "result": None},
        ]
    )
    spec = LanguageServerSpec("fake-python", "python", ("fake-ls",))
    session = LspSession(spec, tmp_path, channel)  # type: ignore[arg-type]

    initialized = session.initialize()
    symbols = session.document_symbols(source)
    definition = session.definition(source, 0, 4)
    references = session.references(source, 0, 4)
    diagnostics = session.diagnostics(source)
    session.close()

    assert initialized["capabilities"]["documentSymbolProvider"] is True
    assert symbols[0]["name"] == "answer"
    assert definition["uri"] == uri
    assert references[0]["uri"] == uri
    assert diagnostics[0]["message"] == "demo warning"
    assert channel.closed is True
    methods = [message.get("method") for message in channel.sent if "method" in message]
    assert methods == [
        "initialize",
        "workspace/configuration",
        "initialized",
        "textDocument/didOpen",
        "textDocument/documentSymbol",
        "textDocument/definition",
        "textDocument/references",
        "shutdown",
        "exit",
    ]
    server_response = next(message for message in channel.sent if message.get("id") == 99)
    assert server_response["result"] == []


def test_process_sandbox_spawn_piped_is_allowlisted_and_bidirectional(tmp_path: Path) -> None:
    executable = Path(sys.executable).name
    sandbox = ProcessSandbox(tmp_path, allowed_executables={executable})
    process = sandbox.spawn_piped(
        (
            sys.executable,
            "-u",
            "-c",
            "import sys; data=sys.stdin.buffer.readline(); sys.stdout.buffer.write(data); sys.stdout.flush()",
        )
    )
    try:
        process.stdin.write(b"ping\n")
        process.stdin.flush()
        assert process.stdout.readline() == b"ping\n"
    finally:
        process.close()

    with pytest.raises(PermissionError, match="allowlisted"):
        sandbox.spawn_piped(("definitely-not-allowed",))


def test_structured_api_exposes_lsp_without_arbitrary_argv(tmp_path: Path) -> None:
    spec = LanguageServerSpec("fake", "python", (sys.executable, "fake_server.py"))
    api = KodeCodeToolAPI(tmp_path, language_servers=(spec,))
    catalog = {item["function"]["name"]: item for item in api.catalog()}

    assert "kodecode_lsp_start" in catalog
    assert "argv" not in catalog["kodecode_lsp_start"]["function"]["parameters"]["properties"]
    capabilities = api.invoke("kodecode_lsp_capabilities")
    assert capabilities[0]["server_id"] == "fake"
    assert capabilities[0]["running"] is False
