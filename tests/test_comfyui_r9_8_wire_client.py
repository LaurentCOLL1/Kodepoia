from __future__ import annotations

from typing import Any

import pytest

from kodepoia.comfyui import ComfyEndpoint
from kodepoia.comfyui.errors import ComfyProtocolError
from kodepoia.comfyui.r9_8_wire_client import (
    R98WireComfyUIClient,
    logical_prompt_id_to_wire,
    wire_prompt_id_to_logical,
)
from kodepoia.comfyui.serialization import canonical_sha256

LOGICAL = "kp_0123456789abcdef0123456789abcdef"
WIRE = "01234567-89ab-cdef-0123-456789abcdef"


class _HTTP:
    def __init__(self) -> None:
        self.posts: list[tuple[str, dict[str, Any]]] = []

    def post_json(self, path: str, document: dict[str, Any]) -> dict[str, Any]:
        self.posts.append((path, document))
        assert path == "/prompt"
        assert document["prompt_id"] == WIRE
        return {"prompt_id": WIRE, "number": 7, "node_errors": {}}

    def get_json(self, path: str) -> dict[str, Any]:
        if path == "/queue":
            return {
                "queue_running": [[0, WIRE, {}, {}, []]],
                "queue_pending": [],
            }
        if path == "/prompt":
            return {"exec_info": {"queue_remaining": 1}}
        if path == f"/history/{WIRE}":
            return {
                WIRE: {
                    "prompt": [
                        0,
                        WIRE,
                        {"1": {"class_type": "Fixture", "inputs": {}}},
                        {"kodepoia": {"run_id": "run_" + "a" * 32}},
                    ],
                    "status": {"status_str": "success", "completed": True},
                    "outputs": {
                        "7": {
                            "images": [
                                {
                                    "filename": "fixture.png",
                                    "subfolder": "",
                                    "type": "output",
                                }
                            ]
                        }
                    },
                }
            }
        raise AssertionError(path)


def _client() -> R98WireComfyUIClient:
    client = R98WireComfyUIClient(ComfyEndpoint.parse("http://127.0.0.1:8188"))
    client._http = _HTTP()  # type: ignore[assignment]
    return client


def test_logical_prompt_id_maps_to_canonical_uuid_and_back() -> None:
    assert logical_prompt_id_to_wire(LOGICAL) == WIRE
    assert wire_prompt_id_to_logical(WIRE) == LOGICAL


def test_wire_adapter_rejects_non_frozen_logical_prompt_id() -> None:
    with pytest.raises(ComfyProtocolError, match="kp_<32hex>"):
        logical_prompt_id_to_wire("not-a-kodepoia-prompt")


def test_submit_uses_uuid_on_wire_but_preserves_logical_identity() -> None:
    client = _client()
    submission = client.submit_prompt(
        {"1": {"class_type": "Fixture", "inputs": {}}},
        prompt_id=LOGICAL,
        client_id="kc_" + "b" * 32,
        correlation={"run_id": "run_" + "a" * 32},
    )
    assert submission.prompt_id == LOGICAL
    assert client._http.posts[0][1]["prompt_id"] == WIRE  # type: ignore[attr-defined]


def test_queue_maps_wire_uuid_back_to_logical_identity() -> None:
    client = _client()
    queue = client.queue()
    assert queue.running_prompt_ids == (LOGICAL,)
    assert queue.pending_prompt_ids == ()
    assert queue.digest_sha256 == canonical_sha256(
        {
            "queue": {
                "queue_running": [[0, WIRE, {}, {}, []]],
                "queue_pending": [],
            },
            "prompt": {"exec_info": {"queue_remaining": 1}},
        }
    )


def test_execution_history_queries_uuid_but_returns_logical_output_references() -> None:
    client = _client()
    history = client.execution_history(LOGICAL)
    assert history.prompt_id == LOGICAL
    assert history.present is True
    assert history.output_references
    assert all(item.prompt_id == LOGICAL for item in history.output_references)
