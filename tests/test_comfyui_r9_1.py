from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

from kodepoia.comfyui import (
    ComfyBoundaryError,
    ComfyEndpoint,
    ComfyHistoryReference,
    ComfyOutputReference,
    ComfyPromptReference,
    ComfyProtocolError,
    ComfyRunState,
    ComfyTransportLimits,
    ComfyVersionError,
    can_transition_run_state,
    canonical_json_bytes,
    canonical_sha256,
    is_terminal_run_state,
    make_envelope,
    parse_envelope,
)

ROOT = Path(__file__).resolve().parents[1]


def test_endpoint_normalizes_explicit_ipv4_and_ipv6_loopback() -> None:
    ipv4 = ComfyEndpoint.parse("http://127.0.0.1:8188/")
    assert ipv4.origin == "http://127.0.0.1:8188"
    assert ipv4.websocket_origin == "ws://127.0.0.1:8188"

    ipv6 = ComfyEndpoint.parse("https://[::1]:9443")
    assert ipv6.origin == "https://[::1]:9443"
    assert ipv6.websocket_origin == "wss://[::1]:9443"


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:8188",
        "http://0.0.0.0:8188",
        "http://192.168.1.5:8188",
        "http://8.8.8.8:8188",
        "http://127.0.0.2:8188",
        "ftp://127.0.0.1:8188",
        "http://127.0.0.1",
        "http://user:secret@127.0.0.1:8188",
        "http://127.0.0.1:8188/api",
        "http://127.0.0.1:8188/?x=1",
        "http://127.0.0.1:8188/#fragment",
        "http://127.0.0.1:99999",
    ],
)
def test_endpoint_rejects_non_origin_or_non_explicit_loopback(origin: str) -> None:
    with pytest.raises(ComfyBoundaryError):
        ComfyEndpoint.parse(origin)


def test_redirect_must_remain_on_exact_origin() -> None:
    endpoint = ComfyEndpoint.parse("http://127.0.0.1:8188")
    assert endpoint.validate_redirect("/history/abc") == "http://127.0.0.1:8188/history/abc"
    assert endpoint.validate_redirect("http://127.0.0.1:8188/queue") == "http://127.0.0.1:8188/queue"

    for location in (
        "http://127.0.0.1:8288/queue",
        "https://127.0.0.1:8188/queue",
        "http://192.168.1.5:8188/queue",
        "//8.8.8.8:8188/queue",
    ):
        with pytest.raises(ComfyBoundaryError):
            endpoint.validate_redirect(location)


def test_canonical_json_and_digest_are_deterministic() -> None:
    first = {"z": [3, 2, 1], "a": {"é": True}}
    second = {"a": {"é": True}, "z": [3, 2, 1]}
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert canonical_sha256(first) == canonical_sha256(second)
    assert len(canonical_sha256(first)) == 64

    with pytest.raises(ComfyProtocolError):
        canonical_json_bytes({"invalid": float("nan")})


def test_envelope_round_trip_is_strict_and_versioned() -> None:
    document = make_envelope(
        schema="kodepoia.comfy-run-manifest",
        version=1,
        payload={"run_id": "run-example", "state": "prepared"},
    )
    assert parse_envelope(document, expected_schema="kodepoia.comfy-run-manifest") == {
        "run_id": "run-example",
        "state": "prepared",
    }

    with pytest.raises(ComfyProtocolError):
        parse_envelope({**document, "extra": True}, expected_schema="kodepoia.comfy-run-manifest")
    with pytest.raises(ComfyProtocolError):
        parse_envelope(document, expected_schema="kodepoia.comfy-vram-evidence")
    with pytest.raises(ComfyVersionError):
        parse_envelope({**document, "version": 2}, expected_schema="kodepoia.comfy-run-manifest")


def test_run_state_transition_table_fails_closed() -> None:
    assert can_transition_run_state(ComfyRunState.PREPARED, ComfyRunState.QUEUED)
    assert can_transition_run_state(ComfyRunState.QUEUED, ComfyRunState.RUNNING)
    assert can_transition_run_state(ComfyRunState.RUNNING, ComfyRunState.SUCCEEDED)
    assert can_transition_run_state(ComfyRunState.RUNNING, ComfyRunState.CANCELLED)
    assert not can_transition_run_state(ComfyRunState.PREPARED, ComfyRunState.SUCCEEDED)
    assert not can_transition_run_state(ComfyRunState.SUCCEEDED, ComfyRunState.RUNNING)
    assert is_terminal_run_state(ComfyRunState.SUCCEEDED)
    assert is_terminal_run_state(ComfyRunState.FAILED)
    assert is_terminal_run_state(ComfyRunState.CANCELLED)
    assert not is_terminal_run_state(ComfyRunState.RUNNING)


def test_prompt_history_and_output_references_are_inert_bounded_evidence() -> None:
    prompt = ComfyPromptReference("prompt-123")
    history = ComfyHistoryReference.from_prompt(prompt)
    output = ComfyOutputReference(
        prompt_id=prompt.prompt_id,
        node_id="9",
        output_index=0,
        server_filename="image.png",
        server_subfolder="batch-a",
    )
    assert history.prompt_id == prompt.prompt_id
    assert output.canonical()["server_filename"] == "image.png"

    with pytest.raises(ValueError):
        ComfyPromptReference("")
    with pytest.raises(ValueError):
        ComfyPromptReference("bad\nidentifier")
    with pytest.raises(ValueError):
        ComfyOutputReference("p", "n", -1, "image.png")


def test_transport_limits_are_positive_finite_and_bounded() -> None:
    limits = ComfyTransportLimits()
    assert limits.max_json_bytes < limits.max_binary_bytes
    with pytest.raises(ValueError):
        ComfyTransportLimits(connect_timeout_seconds=0)
    with pytest.raises(ValueError):
        ComfyTransportLimits(read_timeout_seconds=float("inf"))
    with pytest.raises(ValueError):
        ComfyTransportLimits(max_json_bytes=True)


@pytest.mark.parametrize(
    ("filename", "schema_name"),
    [
        ("comfy-capability-snapshot-v1.schema.json", "kodepoia.comfy-capability-snapshot"),
        ("comfy-workflow-definition-v1.schema.json", "kodepoia.comfy-workflow-definition"),
        ("comfy-run-manifest-v1.schema.json", "kodepoia.comfy-run-manifest"),
        ("comfy-vram-evidence-v1.schema.json", "kodepoia.comfy-vram-evidence"),
    ],
)
def test_r9_schema_roots_validate_and_reject_root_tampering(filename: str, schema_name: str) -> None:
    schema = json.loads((ROOT / "schemas" / filename).read_text(encoding="utf-8"))
    document = make_envelope(schema=schema_name, version=1, payload={"fixture": True})
    validate(document, schema)

    with pytest.raises(ValidationError):
        validate({**document, "version": 2}, schema)
    with pytest.raises(ValidationError):
        validate({**document, "unexpected": "root"}, schema)


def test_r9_1_contracts_do_not_touch_network_or_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("R9.1 must not invoke network or subprocess surfaces")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)

    endpoint = ComfyEndpoint.parse("http://127.0.0.1:8188")
    prompt = ComfyPromptReference("prompt-offline")
    digest = canonical_sha256({"endpoint": endpoint.origin, "prompt": prompt.prompt_id})
    assert len(digest) == 64
