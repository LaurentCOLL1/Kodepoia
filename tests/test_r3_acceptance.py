from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kodepoia.brain.base import BrainMessage, BrainResponse
from kodepoia.brain.ollama import OllamaClient
from kodepoia.cli import _require_loopback_url
from kodepoia.core.audit import AuditLog
from kodepoia.intelligence.context import ContextBuilder
from kodepoia.intelligence.memory import MemoryStore
from kodepoia.models.router import KodeModelRouter, ModelRegistry, ModelRole, ModelSpec, TaskProfile
from kodepoia.orchestrator.runtime import Orchestrator


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False


class OllamaFixture:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def urlopen(self, request, timeout=0):
        if request.full_url.endswith("/api/version"):
            return FakeResponse(json.dumps({"version": "acceptance"}).encode())
        if request.full_url.endswith("/api/tags"):
            return FakeResponse(json.dumps({"models": [{"name": "core"}, {"name": "embed"}]}).encode())
        if request.full_url.endswith("/api/ps"):
            return FakeResponse(json.dumps({"models": [{"name": "core", "size_vram": 1234}]}).encode())
        if request.full_url.endswith("/api/embed"):
            return FakeResponse(json.dumps({"embeddings": [[1.0, 0.0]]}).encode())
        if request.full_url.endswith("/api/chat"):
            payload = json.loads(request.data.decode("utf-8"))
            self.payloads.append(payload)
            if payload["stream"]:
                chunks = (
                    json.dumps({"model": "core", "message": {"content": "hel"}, "done": False})
                    + "\n"
                    + json.dumps(
                        {
                            "model": "core",
                            "message": {"content": "lo"},
                            "done": True,
                            "eval_count": 2,
                            "eval_duration": 1_000_000_000,
                        }
                    )
                    + "\n"
                )
                return FakeResponse(chunks.encode())
            return FakeResponse(
                json.dumps(
                    {
                        "model": "core",
                        "message": {
                            "content": '{"status":"ok"}',
                            "thinking": "done",
                            "tool_calls": [{"function": {"name": "demo", "arguments": {}}}],
                        },
                        "done": True,
                    }
                ).encode()
            )
        raise AssertionError(request.full_url)


def test_ollama_capability_payloads_streaming_images_and_unload() -> None:
    fixture = OllamaFixture()
    tool = {
        "type": "function",
        "function": {
            "name": "demo",
            "description": "demo",
            "parameters": {"type": "object", "properties": {}},
        },
    }
    schema = {
        "type": "object",
        "properties": {"status": {"type": "string"}},
        "required": ["status"],
    }

    with patch("urllib.request.urlopen", side_effect=fixture.urlopen):
        client = OllamaClient()
        response = client.chat(
            "core",
            [BrainMessage("user", "hello", images=("BASE64_IMAGE",))],
            tools=[tool],
            response_schema=schema,
            think=True,
            keep_alive="1m",
        )
        assert response.tool_calls
        payload = fixture.payloads[-1]
        assert payload["stream"] is False
        assert payload["tools"] == [tool]
        assert payload["format"] == schema
        assert payload["think"] is True
        assert payload["keep_alive"] == "1m"
        assert payload["messages"][0]["images"] == ["BASE64_IMAGE"]

        chunks = list(client.stream_chat("core", [BrainMessage("user", "stream")]))
        assert [chunk.content for chunk in chunks] == ["hel", "lo"]
        assert chunks[0].done is False
        assert chunks[-1].done is True

        assert client.running_models()[0]["size_vram"] == 1234
        client.unload("core")
        assert fixture.payloads[-1]["keep_alive"] == 0


class SemanticBrain:
    def __init__(self) -> None:
        self.last_prompt = ""

    def embed(self, model, inputs, **kwargs):
        assert model == "embed"
        return [[1.0, 0.0]]

    def chat(self, model, messages, **kwargs):
        self.last_prompt = messages[0].content
        return BrainResponse("answer", model)

    def stream_chat(self, model, messages, **kwargs):
        self.last_prompt = messages[0].content
        yield BrainResponse("a", model, done=False)
        yield BrainResponse("b", model, done=True)


def test_orchestrator_uses_semantic_memory_and_streams(tmp_path: Path) -> None:
    memory = MemoryStore(tmp_path / "memory.sqlite")
    memory.add("project", "decision", "Use Godot 4.7", embedding=[1.0, 0.0], importance=0.9)
    memory.add("project", "decision", "Unrelated Blender note", embedding=[0.0, 1.0], importance=0.8)
    registry = ModelRegistry(
        [
            ModelSpec("core", ModelRole.CORE, 7000, supports_tools=True, supports_structured=True),
            ModelSpec("embed", ModelRole.EMBED, 1000),
        ]
    )
    brain = SemanticBrain()
    orchestrator = Orchestrator(
        brain=brain,
        router=KodeModelRouter(registry),
        memory=memory,
        audit=AuditLog(tmp_path / "audit.jsonl"),
        context_builder=ContextBuilder(4000),
        semantic_memory_limit=1,
    )

    result = orchestrator.answer("Which engine are we using?", TaskProfile())
    assert result.content == "answer"
    assert "Use Godot 4.7" in brain.last_prompt
    assert "Unrelated Blender note" not in brain.last_prompt

    chunks = list(orchestrator.stream_answer("Repeat the engine", TaskProfile()))
    assert [item.content for item in chunks] == ["a", "b"]
    memory.close()


def test_router_requires_declared_tool_and_structured_capabilities() -> None:
    registry = ModelRegistry(
        [
            ModelSpec("plain", ModelRole.CORE, 4000),
            ModelSpec("capable", ModelRole.CODER, 6000, supports_tools=True, supports_structured=True),
        ]
    )
    router = KodeModelRouter(registry)
    selected = router.route(TaskProfile(needs_tools=True, needs_structured=True))
    assert selected.name == "capable"


def test_r3_acceptance_requires_loopback_ollama() -> None:
    _require_loopback_url("http://127.0.0.1:11434")
    _require_loopback_url("http://localhost:11434")
    _require_loopback_url("http://[::1]:11434")
    with pytest.raises(SystemExit):
        _require_loopback_url("https://example.com:11434")
