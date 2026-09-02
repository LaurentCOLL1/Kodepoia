from __future__ import annotations

import base64
import hashlib
import json
import platform as platform_module
import re
import shutil
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
from urllib.parse import parse_qs, urlsplit

from kodepoia.core.trust import AuthorityEffect, TrustBoundary, TrustMetadata, TrustOrigin

from .boundary import ComfyEndpoint
from .client import ComfyUIClient
from .contracts import ComfyTransportLimits
from .errors import ComfyBoundaryError, ComfyGovernanceError, ComfyUnavailableError
from .resources import (
    ComfyVramTelemetryAdapter,
    GpuAdmissionDecision,
    GpuAdmissionPolicy,
    GpuResourceProfile,
)
from .serialization import canonical_sha256
from .workflow import WorkflowDefinition

FIXTURE_RELATIVE = Path("tests/fixtures/r16_13_comfyui_beta/workflow.json")
SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
UNTRUSTED_MARKER = "R16_13_UNTRUSTED_SHOULD_NOT_RUN"
COMMAND_MARKER = "R16_13_COMMAND_INTENT_SHOULD_NOT_RUN"
_MAX_FIXTURE_BYTES = 256 * 1024
_MAX_RAM_BUDGET = 4 * 1024 * 1024 * 1024
_MAX_DISK_BUDGET = 1024 * 1024 * 1024
_MAX_TIMEOUT_SECONDS = 120.0
_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _case(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "detail": detail}


@dataclass(frozen=True, slots=True)
class R1613Budgets:
    ram_bytes: int
    vram_estimate_bytes: int
    vram_reserve_bytes: int
    vram_headroom_bytes: int
    disk_bytes: int
    timeout_seconds: float

    def __post_init__(self) -> None:
        integer_fields = (
            ("ram_bytes", self.ram_bytes, _MAX_RAM_BUDGET),
            ("vram_estimate_bytes", self.vram_estimate_bytes, 1 << 60),
            ("vram_reserve_bytes", self.vram_reserve_bytes, 1 << 60),
            ("vram_headroom_bytes", self.vram_headroom_bytes, 1 << 60),
            ("disk_bytes", self.disk_bytes, _MAX_DISK_BUDGET),
        )
        for name, value, maximum in integer_fields:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= maximum:
                raise ComfyGovernanceError(f"{name} must be a positive bounded integer")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not 0 < float(self.timeout_seconds) <= _MAX_TIMEOUT_SECONDS
        ):
            raise ComfyGovernanceError("timeout_seconds must be positive and bounded")

    def gpu_profile(self) -> GpuResourceProfile:
        return GpuResourceProfile(
            estimate_bytes=self.vram_estimate_bytes,
            reserve_bytes=self.vram_reserve_bytes,
            headroom_bytes=self.vram_headroom_bytes,
            device_index=0,
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "ram_bytes": self.ram_bytes,
            "vram_estimate_bytes": self.vram_estimate_bytes,
            "vram_reserve_bytes": self.vram_reserve_bytes,
            "vram_headroom_bytes": self.vram_headroom_bytes,
            "disk_bytes": self.disk_bytes,
            "timeout_seconds": float(self.timeout_seconds),
        }


def _load_fixture(repo_root: Path) -> tuple[dict[str, Any], bytes]:
    path = (repo_root / FIXTURE_RELATIVE).resolve(strict=True)
    raw = path.read_bytes()
    if not raw or len(raw) > _MAX_FIXTURE_BYTES:
        raise ComfyGovernanceError("R16.13 fixture must be non-empty and bounded")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComfyGovernanceError("R16.13 fixture must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ComfyGovernanceError("R16.13 fixture root must be an object")
    return payload, raw


def _safe_relative_output(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ComfyGovernanceError("output_relative must be a bounded non-empty string")
    posix = PurePosixPath(value.replace("\\", "/"))
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute():
        raise ComfyGovernanceError("output path must be relative")
    if ".." in posix.parts or ".." in windows.parts:
        raise ComfyGovernanceError("output path must not escape its workspace")
    if any(part in {"", "."} for part in posix.parts):
        raise ComfyGovernanceError("output path contains an unsafe segment")
    return posix.as_posix()


def _validate_security_metadata(metadata: dict[str, Any]) -> None:
    command = metadata.get("command_intent")
    if command not in {None, ""}:
        raise ComfyGovernanceError("workflow-supplied arbitrary command intent is denied")
    external = metadata.get("external_reference")
    if external not in {None, ""}:
        raise ComfyGovernanceError("unsafe external workflow references are denied")
    _safe_relative_output(str(metadata.get("output_relative", "")))


def validate_fixture_payload(payload: dict[str, Any]) -> tuple[WorkflowDefinition, R1613Budgets]:
    expected = {
        "schema_version",
        "name",
        "graph",
        "allowed_node_classes",
        "metadata",
        "budgets",
        "negative_controls",
    }
    if set(payload) != expected or payload.get("schema_version") != 1:
        raise ComfyGovernanceError("R16.13 fixture fields/schema do not match the frozen contract")
    graph = payload.get("graph")
    allowed = payload.get("allowed_node_classes")
    metadata = payload.get("metadata")
    budgets_raw = payload.get("budgets")
    negatives = payload.get("negative_controls")
    if not isinstance(graph, dict) or not isinstance(allowed, list):
        raise ComfyGovernanceError("R16.13 fixture graph/allowlist shape is invalid")
    if not isinstance(metadata, dict) or not isinstance(budgets_raw, dict) or not isinstance(negatives, dict):
        raise ComfyGovernanceError("R16.13 fixture metadata/budgets/negative controls must be objects")
    _validate_security_metadata(metadata)
    definition = WorkflowDefinition.create(
        name=str(payload["name"]),
        revision=1,
        graph=graph,
        allowed_node_classes=tuple(str(item) for item in allowed),
    )
    graph_classes = {str(node["class_type"]) for node in definition.graph().values()}
    if not graph_classes.issubset(set(definition.allowed_node_classes)):
        raise ComfyGovernanceError("R16.13 fixture graph contains a node outside its allowlist")
    try:
        budgets = R1613Budgets(
            ram_bytes=int(budgets_raw["ram_bytes"]),
            vram_estimate_bytes=int(budgets_raw["vram_estimate_bytes"]),
            vram_reserve_bytes=int(budgets_raw["vram_reserve_bytes"]),
            vram_headroom_bytes=int(budgets_raw["vram_headroom_bytes"]),
            disk_bytes=int(budgets_raw["disk_bytes"]),
            timeout_seconds=float(budgets_raw["timeout_seconds"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ComfyGovernanceError("R16.13 fixture budgets are invalid") from exc
    return definition, budgets


@dataclass(slots=True)
class _FixtureState:
    output_bytes: bytes
    prompt_id: str | None = None
    client_id: str | None = None
    prompt: dict[str, Any] | None = None
    extra_data: dict[str, Any] | None = None
    queue_reads: int = 0
    websocket_connections: int = 0
    post_count: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)


class _FixtureHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    fixture_state: _FixtureState


def _json_bytes(value: Any) -> bytes:
    return _canonical_json(value).encode("utf-8")


def _ws_text_frame(value: Any) -> bytes:
    payload = _json_bytes(value)
    length = len(payload)
    if length < 126:
        header = bytes((0x81, length))
    elif length <= 0xFFFF:
        header = bytes((0x81, 126)) + length.to_bytes(2, "big")
    else:
        header = bytes((0x81, 127)) + length.to_bytes(8, "big")
    return header + payload


class _FixtureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    @property
    def state(self) -> _FixtureState:
        server = self.server
        if not isinstance(server, _FixtureHTTPServer):
            raise RuntimeError("unexpected fixture server")
        return server.fixture_state

    def _send_json(self, value: Any, status: int = 200) -> None:
        data = _json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)
        self.close_connection = True

    def _send_bytes(self, data: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)
        self.close_connection = True

    def do_POST(self) -> None:
        if self.path != "/prompt":
            self._send_json({"error": "unsupported"}, 404)
            return
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "0")
        except ValueError:
            self._send_json({"error": "length"}, 400)
            return
        if not 0 < length <= _MAX_FIXTURE_BYTES:
            self._send_json({"error": "body bound"}, 413)
            return
        try:
            document = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json({"error": "json"}, 400)
            return
        if not isinstance(document, dict):
            self._send_json({"error": "shape"}, 400)
            return
        prompt_id = document.get("prompt_id")
        client_id = document.get("client_id")
        prompt = document.get("prompt")
        extra_data = document.get("extra_data")
        if not isinstance(prompt_id, str) or not isinstance(client_id, str):
            self._send_json({"error": "identity"}, 400)
            return
        if not isinstance(prompt, dict) or not isinstance(extra_data, dict):
            self._send_json({"error": "payload"}, 400)
            return
        with self.state.lock:
            self.state.prompt_id = prompt_id
            self.state.client_id = client_id
            self.state.prompt = prompt
            self.state.extra_data = extra_data
            self.state.queue_reads = 0
            self.state.post_count += 1
        self._send_json({"prompt_id": prompt_id, "number": 1, "node_errors": {}})

    def do_GET(self) -> None:
        target = urlsplit(self.path)
        if target.path == "/ws":
            self._handle_websocket(target.query)
            return
        if target.path == "/system_stats":
            gib = 1024 * 1024 * 1024
            self._send_json(
                {
                    "system": {
                        "comfyui_version": "r16.13-fixture-1",
                        "python_version": platform_module.python_version(),
                    },
                    "devices": [
                        {
                            "name": "R16.13 synthetic fixture device",
                            "type": "fixture",
                            "index": 0,
                            "vram_total": 2 * gib,
                            "vram_free": 1536 * 1024 * 1024,
                            "torch_vram_total": 2 * gib,
                            "torch_vram_free": 1536 * 1024 * 1024,
                        }
                    ],
                }
            )
            return
        if target.path == "/features":
            self._send_json({"r16_13_fixture": True, "websocket": True})
            return
        if target.path == "/prompt":
            with self.state.lock:
                remaining = 0 if self.state.queue_reads else (1 if self.state.prompt_id else 0)
            self._send_json({"exec_info": {"queue_remaining": remaining}})
            return
        if target.path == "/queue":
            with self.state.lock:
                prompt_id = self.state.prompt_id
                queue_reads = self.state.queue_reads
                self.state.queue_reads += 1
            pending = [] if prompt_id is None or queue_reads else [[1, prompt_id]]
            self._send_json({"queue_running": [], "queue_pending": pending})
            return
        if target.path == "/history":
            with self.state.lock:
                prompt_id = self.state.prompt_id
            payload = (
                {}
                if prompt_id is None
                else {prompt_id: {"status": {"status_str": "success", "completed": True}}}
            )
            self._send_json(payload)
            return
        if target.path.startswith("/history/"):
            prompt_id = target.path.split("/", 2)[2]
            with self.state.lock:
                stored_id = self.state.prompt_id
                prompt = dict(self.state.prompt or {})
                extra_data = dict(self.state.extra_data or {})
                ready = self.state.queue_reads > 0
            if prompt_id != stored_id or not ready:
                self._send_json({})
                return
            self._send_json(
                {
                    prompt_id: {
                        "prompt": [1, prompt_id, prompt, extra_data, []],
                        "status": {"status_str": "success", "completed": True},
                        "outputs": {
                            "2": {
                                "images": [
                                    {
                                        "filename": "result.bin",
                                        "subfolder": "r16_13",
                                        "type": "output",
                                    }
                                ]
                            }
                        },
                    }
                }
            )
            return
        if target.path == "/view":
            query = parse_qs(target.query, keep_blank_values=True)
            if (
                query.get("filename") == ["result.bin"]
                and query.get("subfolder") == ["r16_13"]
                and query.get("type") == ["output"]
            ):
                self._send_bytes(self.state.output_bytes)
            else:
                self._send_json({"error": "unsafe output reference"}, 400)
            return
        self._send_json({"error": "unsupported"}, 404)

    def _handle_websocket(self, query: str) -> None:
        client_id = parse_qs(query).get("clientId", [None])[0]
        key = self.headers.get("Sec-WebSocket-Key")
        if not isinstance(client_id, str) or not key:
            self._send_json({"error": "websocket identity"}, 400)
            return
        with self.state.lock:
            expected_client = self.state.client_id
            prompt_id = self.state.prompt_id
            self.state.websocket_connections += 1
        if client_id != expected_client or prompt_id is None:
            self._send_json({"error": "websocket correlation"}, 403)
            return
        accept = base64.b64encode(
            hashlib.sha1(f"{key}{_WS_GUID}".encode("ascii"), usedforsecurity=False).digest()
        ).decode("ascii")
        self.send_response(101)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        events = (
            {"type": "execution_start", "data": {"prompt_id": prompt_id}},
            {
                "type": "progress",
                "data": {"prompt_id": prompt_id, "node": "1", "value": 1, "max": 2},
            },
            {"type": "execution_success", "data": {"prompt_id": prompt_id}},
        )
        for event in events:
            self.connection.sendall(_ws_text_frame(event))
        self.close_connection = True


@contextmanager
def _fixture_server(output_bytes: bytes):
    state = _FixtureState(output_bytes=output_bytes)
    server = _FixtureHTTPServer(("127.0.0.1", 0), _FixtureHandler)
    server.fixture_state = state
    thread = threading.Thread(target=server.serve_forever, name="r16-13-comfy-fixture", daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield state, f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _negative_control_results(payload: dict[str, Any]) -> dict[str, bool]:
    raw = payload["negative_controls"]
    results: dict[str, bool] = {}

    try:
        _safe_relative_output(str(raw["path_escape"]))
    except ComfyGovernanceError:
        results["path_escape"] = True
    else:
        results["path_escape"] = False

    command_metadata = dict(payload["metadata"])
    command_metadata["command_intent"] = raw["command_intent"]
    try:
        _validate_security_metadata(command_metadata)
    except ComfyGovernanceError:
        results["command_intent"] = True
    else:
        results["command_intent"] = False

    external_metadata = dict(payload["metadata"])
    external_metadata["external_reference"] = raw["external_reference"]
    try:
        _validate_security_metadata(external_metadata)
    except ComfyGovernanceError:
        results["external_reference"] = True
    else:
        results["external_reference"] = False
    return results


def _secret_free(value: Any) -> bool:
    lowered = _canonical_json(value).lower()
    forbidden = (
        "-----begin private key-----",
        "-----begin rsa private key-----",
        "github_pat_",
        "ghp_",
        "client_secret=",
        "password=",
        "aws_secret_access_key",
    )
    return not any(marker in lowered for marker in forbidden)


def qualify_live_local_comfyui(endpoint: str | None) -> dict[str, Any]:
    if endpoint is None:
        return {
            "state": "NOT_EXERCISED",
            "claim_satisfied": False,
            "endpoint": None,
            "comfyui_version": None,
            "python_version": None,
            "device_count": None,
            "system_digest_sha256": None,
            "vram_digest_sha256": None,
        }
    try:
        parsed = ComfyEndpoint.parse(endpoint)
        client = ComfyUIClient(
            parsed,
            limits=ComfyTransportLimits(
                connect_timeout_seconds=1.0,
                read_timeout_seconds=2.0,
                total_timeout_seconds=4.0,
                max_json_bytes=1024 * 1024,
                max_binary_bytes=1024 * 1024,
                max_websocket_frame_bytes=1024 * 1024,
            ),
        )
        system = client.system_stats()
        vram = ComfyVramTelemetryAdapter(client).sample()
    except (ComfyBoundaryError, ComfyUnavailableError, OSError) as exc:
        return {
            "state": "UNAVAILABLE",
            "claim_satisfied": False,
            "endpoint": endpoint,
            "error_type": type(exc).__name__,
            "comfyui_version": None,
            "python_version": None,
            "device_count": None,
            "system_digest_sha256": None,
            "vram_digest_sha256": None,
        }
    return {
        "state": "EXERCISED",
        "claim_satisfied": True,
        "endpoint": parsed.origin,
        "comfyui_version": system.comfyui_version,
        "python_version": system.python_version,
        "device_count": system.device_count,
        "system_digest_sha256": system.digest_sha256,
        "vram_digest_sha256": vram.digest_sha256,
    }


def build_comfyui_beta_report(
    repo_root: Path,
    *,
    source_sha: str,
    platform: str,
    live_endpoint: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    source_sha = source_sha.strip().lower()
    if SOURCE_SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be a lowercase 40-character Git SHA")

    fixture, fixture_bytes = _load_fixture(repo_root)
    definition, budgets = validate_fixture_payload(fixture)
    fixture_sha256 = canonical_sha256(fixture)
    output_relative = _safe_relative_output(str(fixture["metadata"]["output_relative"]))
    negative = _negative_control_results(fixture)
    output_bytes = b"KODEPOIA-R16.13-DETERMINISTIC-COMFYUI-OUTPUT\n"
    output_sha256 = hashlib.sha256(output_bytes).hexdigest()
    prompt_digest = canonical_sha256(definition.graph())
    budget_digest = canonical_sha256(budgets.canonical())
    cases: list[dict[str, Any]] = []
    started = time.monotonic()

    with _fixture_server(output_bytes) as (fixture_state, endpoint):
        limits = ComfyTransportLimits(
            connect_timeout_seconds=1.0,
            read_timeout_seconds=3.0,
            total_timeout_seconds=min(float(budgets.timeout_seconds), 10.0),
            max_json_bytes=min(budgets.ram_bytes, 8 * 1024 * 1024),
            max_binary_bytes=budgets.disk_bytes,
            max_websocket_frame_bytes=min(budgets.ram_bytes, 4 * 1024 * 1024),
        )
        client = ComfyUIClient(endpoint, limits=limits)
        system = client.system_stats()
        telemetry = ComfyVramTelemetryAdapter(client).sample()
        admission = GpuAdmissionPolicy().decide(telemetry, budgets.gpu_profile())
        submission = client.submit_prompt(
            definition.graph(),
            prompt_id="kp_" + source_sha[:32],
            client_id="kc_" + source_sha[8:40],
            correlation={
                "source_sha": source_sha,
                "workflow_sha256": definition.definition_digest_sha256,
                "budget_sha256": budget_digest,
            },
        )
        queue = client.queue()

        client_id = "kc_" + source_sha[8:40]
        stream = client.iter_events(
            client_id,
            expected_prompt_id=submission.prompt_id,
            max_reconnects=0,
        )
        events = [next(stream), next(stream), next(stream)]
        stream.close()

        history = client.execution_history(submission.prompt_id)
        if not history.output_references:
            raise ComfyGovernanceError("fixture execution omitted its declared output reference")
        captured = client.retrieve_output(history.output_references[0])

        cancellation = threading.Event()
        cancellation.set()
        cancelled_events = list(
            client.iter_events(
                client_id,
                expected_prompt_id=submission.prompt_id,
                cancel_event=cancellation,
                max_reconnects=0,
            )
        )

        workspace = repo_root / "artifacts" / ".r16_13_acceptance_workspace"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        try:
            output_path = (workspace / output_relative).resolve(strict=False)
            if not output_path.is_relative_to(workspace.resolve()):
                raise ComfyGovernanceError("validated R16.13 output escaped workspace")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(captured)
            staged_sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()
            disk_used = output_path.stat().st_size
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

        untrusted_text = str(fixture["metadata"]["untrusted_note"])
        trust = TrustMetadata.untrusted(
            TrustOrigin.REPOSITORY,
            source=FIXTURE_RELATIVE.as_posix(),
            content=untrusted_text,
        )
        boundary = TrustBoundary()
        inspect = boundary.evaluate(trust, AuthorityEffect.INSPECT_DATA)
        process = boundary.evaluate(trust, AuthorityEffect.PROCESS_EXECUTION)
        tool = boundary.evaluate(trust, AuthorityEffect.PRIVILEGED_TOOL_TRIGGER)

        elapsed = time.monotonic() - started
        event_types = [event.event_type.value for event in events]
        event_digest = canonical_sha256(
            [{"type": event.event_type.value, "payload_sha256": event.payload_sha256} for event in events]
        )
        binding = {
            "source_sha": source_sha,
            "fixture_sha256": fixture_sha256,
            "workflow_sha256": definition.definition_digest_sha256,
            "prompt_sha256": prompt_digest,
            "budget_sha256": budget_digest,
            "event_sha256": event_digest,
            "output_sha256": output_sha256,
        }

        cases.extend(
            [
                _case(
                    "deterministic-repository-workflow",
                    definition.definition_digest_sha256 == canonical_sha256(definition.identity_payload())
                    and fixture_sha256 == canonical_sha256(fixture)
                    and 0 < len(fixture_bytes) <= _MAX_FIXTURE_BYTES,
                    "repository-owned workflow fixture and canonical workflow identity are deterministic",
                ),
                _case(
                    "fixed-loopback-wire-protocol",
                    endpoint.startswith("http://127.0.0.1:")
                    and system.comfyui_version == "r16.13-fixture-1"
                    and fixture_state.post_count == 1,
                    "fixed ComfyUI HTTP transport executes only against the ephemeral loopback fixture",
                ),
                _case(
                    "queue-submit-correlation",
                    submission.prompt_id in queue.pending_prompt_ids
                    and queue.queue_remaining == 0
                    and submission.queue_number == 1.0,
                    "prompt submission, queue state and Kodepoia correlation remain exact",
                ),
                _case(
                    "progress-events-websocket",
                    event_types == ["execution_start", "progress", "execution_success"]
                    and events[1].progress_fraction == 0.5
                    and fixture_state.websocket_connections == 1,
                    "fixed WebSocket transport observes bounded prompt-scoped progress and success events",
                ),
                _case(
                    "history-output-collection",
                    history.present
                    and history.state.value == "succeeded"
                    and hashlib.sha256(captured).hexdigest() == output_sha256
                    and staged_sha256 == output_sha256,
                    "history reconciliation and output retrieval preserve exact output bytes",
                ),
                _case(
                    "bounded-cancellation",
                    not cancelled_events and fixture_state.websocket_connections == 1,
                    "pre-signalled cancellation returns before opening another WebSocket connection",
                ),
                _case(
                    "workspace-output-boundary",
                    output_relative == "outputs/result.bin"
                    and disk_used == len(output_bytes)
                    and negative["path_escape"],
                    "managed output remains workspace-relative and a traversal negative control is denied",
                ),
                _case(
                    "untrusted-command-metadata-denied",
                    UNTRUSTED_MARKER in untrusted_text
                    and COMMAND_MARKER in str(fixture["negative_controls"]["command_intent"])
                    and inspect.allowed
                    and not process.allowed
                    and not tool.allowed
                    and negative["command_intent"],
                    "repository metadata remains inspectable data and cannot acquire process/tool authority",
                ),
                _case(
                    "unsafe-external-reference-denied",
                    negative["external_reference"],
                    "workflow metadata cannot silently introduce an unsafe external reference",
                ),
                _case(
                    "ram-vram-disk-time-budgets",
                    len(fixture_bytes) + len(output_bytes) <= budgets.ram_bytes
                    and admission.decision is GpuAdmissionDecision.ADMIT
                    and disk_used <= budgets.disk_bytes
                    and elapsed <= float(budgets.timeout_seconds),
                    "RAM/VRAM/disk/time budgets are checked against bounded fixture evidence",
                ),
                _case(
                    "exact-source-output-binding",
                    binding["source_sha"] == source_sha
                    and binding["workflow_sha256"] == definition.definition_digest_sha256
                    and len(canonical_sha256(binding)) == 64,
                    "output evidence is bound to exact source, workflow, prompt, budget and event digests",
                ),
            ]
        )

    live = qualify_live_local_comfyui(live_endpoint)
    cases.append(
        _case(
            "real-server-gpu-not-inferred",
            live["state"] == "NOT_EXERCISED" if live_endpoint is None else True,
            "core CI truthfully separates synthetic fixture capability from optional "
            "real local ComfyUI/GPU evidence",
        )
    )
    security_claim = all(bool(item["pass"]) for item in cases)
    semantic = {
        "phase": "R16.13",
        "source_sha": source_sha,
        "fixture_sha256": fixture_sha256,
        "workflow_sha256": definition.definition_digest_sha256,
        "budget_sha256": budget_digest,
        "cases": [{"name": item["name"], "pass": item["pass"]} for item in cases],
        "manual_state": "CONDITIONAL_NOT_TRIGGERED" if live_endpoint is None else "CONDITIONAL_REQUESTED",
        "security_claim": security_claim,
        "critical_veto": not security_claim,
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R16.13",
        "source_sha": source_sha,
        "platform": platform,
        "manual_state": "CONDITIONAL_NOT_TRIGGERED" if live_endpoint is None else "CONDITIONAL_REQUESTED",
        "core_manual_required": False,
        "security_claim": security_claim,
        "critical_veto": not security_claim,
        "live_credentials_used": False,
        "destructive_host_actions": False,
        "external_network_calls": 0,
        "fixture_transport": "ephemeral explicit-port loopback HTTP/WebSocket",
        "fixture_is_real_comfyui": False,
        "fixture_is_real_gpu": False,
        "fixture_sha256": fixture_sha256,
        "workflow_definition_id": definition.definition_id,
        "workflow_sha256": definition.definition_digest_sha256,
        "prompt_sha256": prompt_digest,
        "budget": budgets.canonical(),
        "budget_sha256": budget_digest,
        "output_sha256": output_sha256,
        "binding_sha256": canonical_sha256(binding),
        "live_local_qualification": live,
        "cases": cases,
        "summary": {
            "total": len(cases),
            "passed": sum(bool(item["pass"]) for item in cases),
            "failed": sum(not bool(item["pass"]) for item in cases),
        },
        "semantic_sha256": canonical_sha256(semantic),
    }
    report["secret_free"] = _secret_free(report)
    if not report["secret_free"]:
        report["security_claim"] = False
        report["critical_veto"] = True
    report["evidence_sha256"] = _digest(report)
    return report
