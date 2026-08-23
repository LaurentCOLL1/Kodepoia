from __future__ import annotations

import base64
import hashlib
import json
import socket
import struct
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from kodepoia.comfyui import (
    ComfyEventSequence,
    ComfyEventType,
    ComfyOutputReference,
    ComfyProtocolError,
    ComfyResourceError,
    ComfyRunState,
    ComfyTransportLimits,
    ComfyUIClient,
    ComfyUnavailableError,
    parse_event_frame,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "comfyui" / "r9_2_protocol.json"
_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class _Scenario:
    def __init__(self, fixture: dict[str, Any]) -> None:
        self.fixture = fixture
        self.overrides: dict[str, tuple[int, dict[str, str], bytes]] = {}
        self.delays: dict[str, float] = {}
        self.ws_connections: list[list[str | bytes | tuple[str, int]]] = []
        self.ws_connection_count = 0
        self.output_bytes = b"fixture-output-bytes"


class _Handler(BaseHTTPRequestHandler):
    scenario: _Scenario

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def do_GET(self) -> None:  # noqa: N802
        parts = urlsplit(self.path)
        if parts.path == "/ws":
            self._websocket(parts.query)
            return
        delay = self.scenario.delays.get(parts.path, 0.0)
        if delay:
            time.sleep(delay)
        override = self.scenario.overrides.get(parts.path)
        if override is not None:
            status, headers, body = override
            self._send(status, headers, body)
            return

        fixture = self.scenario.fixture
        if parts.path == "/system_stats":
            self._json(fixture["system_stats"])
        elif parts.path == "/features":
            self._json(fixture["features"])
        elif parts.path == "/prompt":
            self._json(fixture["prompt"])
        elif parts.path == "/queue":
            self._json(fixture["queue"])
        elif parts.path == "/history":
            self._json(fixture["history"])
        elif parts.path.startswith("/history/"):
            prompt_id = parts.path.removeprefix("/history/")
            item = fixture["history"].get(prompt_id)
            self._json({prompt_id: item} if item is not None else {})
        elif parts.path == "/view":
            query = parse_qs(parts.query, keep_blank_values=True)
            if query.get("type") not in (["output"], ["temp"]):
                self._send(400, {}, b"invalid type")
                return
            self._send(200, {"Content-Type": "application/octet-stream"}, self.scenario.output_bytes)
        elif parts.path == "/redirected-system":
            self._json(fixture["system_stats"])
        else:
            self._send(404, {}, b"missing")

    def _json(self, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self._send(200, {"Content-Type": "application/json"}, body)

    def _send(self, status: int, headers: dict[str, str], body: bytes) -> None:
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        if "Content-Length" not in headers:
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _websocket(self, query: str) -> None:
        parsed_query = parse_qs(query)
        if not parsed_query.get("clientId"):
            self._send(400, {}, b"missing client")
            return
        key = self.headers.get("Sec-WebSocket-Key")
        if key is None:
            self._send(400, {}, b"missing key")
            return
        accept = base64.b64encode(
            hashlib.sha1(f"{key}{_WS_GUID}".encode("ascii"), usedforsecurity=False).digest()
        ).decode("ascii")
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        self.wfile.flush()
        time.sleep(0.01)

        index = self.scenario.ws_connection_count
        self.scenario.ws_connection_count += 1
        frames = self.scenario.ws_connections[index] if index < len(self.scenario.ws_connections) else []
        for frame in frames:
            if isinstance(frame, tuple) and frame[0] == "oversize":
                length = frame[1]
                self.connection.sendall(bytes((0x81, 127)) + struct.pack("!Q", length))
                return
            if isinstance(frame, bytes):
                self.connection.sendall(_server_frame(frame, opcode=0x2))
            else:
                self.connection.sendall(_server_frame(frame.encode("utf-8"), opcode=0x1))
        self.close_connection = True


def _server_frame(payload: bytes, *, opcode: int) -> bytes:
    first = 0x80 | opcode
    length = len(payload)
    if length < 126:
        return bytes((first, length)) + payload
    if length <= 0xFFFF:
        return bytes((first, 126)) + struct.pack("!H", length) + payload
    return bytes((first, 127)) + struct.pack("!Q", length) + payload


@contextmanager
def _server(scenario: _Scenario):
    handler_type = type("ScenarioHandler", (_Handler,), {"scenario": scenario})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_type)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.fixture
def protocol_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixed_http_operations_probe_and_output(protocol_fixture: dict[str, Any]) -> None:
    scenario = _Scenario(protocol_fixture)
    with _server(scenario) as endpoint:
        client = ComfyUIClient(endpoint)
        system = client.system_stats()
        assert system.comfyui_version == "0.test"
        assert system.python_version == "3.12.test"
        assert system.device_count == 1

        queue = client.queue()
        assert queue.running_prompt_ids == ("prompt-running",)
        assert queue.pending_prompt_ids == ("prompt-pending",)
        assert queue.queue_remaining == 2

        history = client.history("prompt-success")
        assert history.present is True
        assert history.state is ComfyRunState.SUCCEEDED
        assert history.output_node_ids == ("9",)

        reference = ComfyOutputReference("prompt-success", "9", 0, "fixture.png")
        assert client.retrieve_output(reference) == scenario.output_bytes

        probe = client.probe()
        assert probe.endpoint == endpoint
        assert all(
            value.value == "current"
            for value in (probe.system, probe.features, probe.prompt_metadata, probe.queue, probe.history)
        )


def test_poll_reconciliation_never_manufactures_success(protocol_fixture: dict[str, Any]) -> None:
    scenario = _Scenario(protocol_fixture)
    with _server(scenario) as endpoint:
        client = ComfyUIClient(endpoint)
        assert client.reconcile_prompt_state("prompt-running") is ComfyRunState.RUNNING
        assert client.reconcile_prompt_state("prompt-pending") is ComfyRunState.QUEUED
        assert client.reconcile_prompt_state("prompt-success") is ComfyRunState.SUCCEEDED
        assert client.reconcile_prompt_state("prompt-failed") is ComfyRunState.FAILED
        assert client.reconcile_prompt_state("prompt-missing") is ComfyRunState.UNKNOWN


def test_http_redirect_error_malformed_timeout_and_size_bounds(protocol_fixture: dict[str, Any]) -> None:
    scenario = _Scenario(protocol_fixture)
    with _server(scenario) as endpoint:
        host, port_text = endpoint.rsplit(":", 1)
        port = int(port_text)
        client = ComfyUIClient(endpoint, limits=ComfyTransportLimits(read_timeout_seconds=0.05))

        scenario.overrides["/system_stats"] = (302, {"Location": "/redirected-system"}, b"")
        assert client.system_stats().device_count == 1

        scenario.overrides["/system_stats"] = (
            302,
            {"Location": f"{host}:{port + 1}/system_stats"},
            b"",
        )
        with pytest.raises(Exception, match="origin|loopback"):
            client.system_stats()

        scenario.overrides["/system_stats"] = (500, {}, b"server error")
        with pytest.raises(ComfyProtocolError, match="status 500"):
            client.system_stats()

        scenario.overrides["/system_stats"] = (200, {"Content-Type": "application/json"}, b"{")
        with pytest.raises(ComfyProtocolError, match="malformed"):
            client.system_stats()

        tiny_limits = ComfyTransportLimits(max_json_bytes=8)
        tiny_client = ComfyUIClient(endpoint, limits=tiny_limits)
        scenario.overrides["/system_stats"] = (200, {}, b'{"too":"large"}')
        with pytest.raises(ComfyResourceError, match="byte bound"):
            tiny_client.system_stats()

        scenario.overrides.pop("/system_stats", None)
        scenario.delays["/system_stats"] = 0.2
        with pytest.raises(ComfyUnavailableError, match="unavailable"):
            client.system_stats()


def test_event_parser_and_sequence_reject_mismatch_and_terminal_regression(
    protocol_fixture: dict[str, Any],
) -> None:
    frames = [json.dumps(item) for item in protocol_fixture["events"]]
    events = [parse_event_frame(frame, max_bytes=4096) for frame in frames]
    assert [event.event_type for event in events] == [
        ComfyEventType.EXECUTION_START,
        ComfyEventType.EXECUTION_CACHED,
        ComfyEventType.EXECUTING,
        ComfyEventType.PROGRESS,
        ComfyEventType.EXECUTED,
        ComfyEventType.EXECUTION_SUCCESS,
    ]
    assert events[3].progress_fraction == 0.25

    sequence = ComfyEventSequence("prompt-running")
    for event in events:
        sequence.observe(event)
    assert sequence.state is ComfyRunState.SUCCEEDED

    mismatch = parse_event_frame(
        json.dumps({"type": "executing", "data": {"prompt_id": "other", "node": "1"}}),
        max_bytes=4096,
    )
    with pytest.raises(ComfyProtocolError, match="prompt_id"):
        sequence.observe(mismatch)

    regression = parse_event_frame(
        json.dumps({"type": "progress", "data": {"prompt_id": "prompt-running", "value": 1, "max": 2}}),
        max_bytes=4096,
    )
    with pytest.raises(ComfyProtocolError, match="transition"):
        sequence.observe(regression)


def test_websocket_reconnect_binary_skip_and_bounded_retry(protocol_fixture: dict[str, Any]) -> None:
    scenario = _Scenario(protocol_fixture)
    start = json.dumps({"type": "execution_start", "data": {"prompt_id": "prompt-running"}})
    progress = json.dumps(
        {"type": "progress", "data": {"prompt_id": "prompt-running", "node": "2", "value": 2, "max": 4}}
    )
    success = json.dumps({"type": "execution_success", "data": {"prompt_id": "prompt-running"}})
    scenario.ws_connections = [[start], [b"preview", progress, success]]

    with _server(scenario) as endpoint:
        client = ComfyUIClient(endpoint)
        cancel = threading.Event()
        iterator = client.iter_events(
            "client-fixture",
            expected_prompt_id="prompt-running",
            cancel_event=cancel,
            max_reconnects=1,
            backoff_seconds=(0.0,),
        )
        assert next(iterator).event_type is ComfyEventType.EXECUTION_START
        assert next(iterator).event_type is ComfyEventType.PROGRESS
        assert next(iterator).event_type is ComfyEventType.EXECUTION_SUCCESS
        cancel.set()
        with pytest.raises(StopIteration):
            next(iterator)
        assert scenario.ws_connection_count == 2


def test_websocket_frame_length_is_rejected_before_payload_read(protocol_fixture: dict[str, Any]) -> None:
    scenario = _Scenario(protocol_fixture)
    scenario.ws_connections = [[("oversize", 4097)]]
    limits = ComfyTransportLimits(max_websocket_frame_bytes=4096)
    with _server(scenario) as endpoint:
        client = ComfyUIClient(endpoint, limits=limits)
        iterator = client.iter_events("client-size", max_reconnects=0)
        with pytest.raises(ComfyResourceError, match="frame exceeds"):
            next(iterator)


def test_malformed_and_oversized_event_payloads_fail_closed() -> None:
    with pytest.raises(ComfyProtocolError, match="valid UTF-8 JSON"):
        parse_event_frame("{", max_bytes=128)
    with pytest.raises(ComfyResourceError, match="byte bound"):
        parse_event_frame(json.dumps({"type": "status", "data": {"pad": "x" * 200}}), max_bytes=32)
    with pytest.raises(ComfyProtocolError, match="range"):
        parse_event_frame(
            json.dumps({"type": "progress", "data": {"value": 3, "max": 2}}),
            max_bytes=1024,
        )


def test_client_has_no_public_arbitrary_request_surface() -> None:
    public = {name for name in dir(ComfyUIClient) if not name.startswith("_")}
    assert "request" not in public
    assert "get" not in public
    assert "post" not in public
    assert "urlopen" not in public
    assert {
        "system_stats",
        "features",
        "prompt_metadata",
        "queue",
        "history",
        "history_index",
        "retrieve_output",
        "reconcile_prompt_state",
        "iter_events",
        "probe",
    } <= public


def test_fixture_digest_is_stable(protocol_fixture: dict[str, Any]) -> None:
    raw = FIXTURE_PATH.read_bytes()
    assert protocol_fixture["fixture_version"] == 1
    assert hashlib.sha256(raw).hexdigest() == "TO_BE_FILLED"
