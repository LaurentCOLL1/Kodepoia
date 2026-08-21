import io
import json
from unittest.mock import patch

from kodepoia.brain.base import BrainMessage
from kodepoia.brain.ollama import OllamaClient


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False


REQUEST_PAYLOADS: list[dict] = []
REQUEST_TIMEOUTS: list[float] = []


def fake_urlopen(request, timeout=0):
    REQUEST_TIMEOUTS.append(timeout)
    if request.full_url.endswith("/api/version"):
        return FakeResponse(json.dumps({"version": "test"}).encode())
    if request.full_url.endswith("/api/tags"):
        return FakeResponse(json.dumps({"models": [{"name": "core"}]}).encode())
    if request.full_url.endswith("/api/show"):
        return FakeResponse(
            json.dumps(
                {
                    "capabilities": ["completion", "tools", "thinking"],
                    "details": {"family": "qwen35", "parameter_size": "9B"},
                }
            ).encode()
        )
    if request.full_url.endswith("/api/embed"):
        return FakeResponse(json.dumps({"embeddings": [[0.1, 0.2]]}).encode())
    if request.full_url.endswith("/api/chat"):
        REQUEST_PAYLOADS.append(json.loads(request.data.decode("utf-8")))
    return FakeResponse(
        json.dumps(
            {
                "model": "core",
                "message": {"content": "OK"},
                "done": True,
                "done_reason": "stop",
                "total_duration": 2_100_000_000,
                "load_duration": 2_000_000_000,
            }
        ).encode()
    )


@patch("urllib.request.urlopen", side_effect=fake_urlopen)
def test_ollama_api(mock_open) -> None:
    REQUEST_PAYLOADS.clear()
    REQUEST_TIMEOUTS.clear()
    client = OllamaClient()
    assert client.version() == "test"
    assert client.list_models() == ["core"]
    response = client.chat(
        "core",
        [BrainMessage("user", "Hi")],
        options={"seed": 101, "temperature": 0.0, "num_predict": 256},
    )
    assert response.content == "OK"
    assert response.metrics["done_reason"] == "stop"
    assert REQUEST_PAYLOADS[-1]["options"] == {
        "seed": 101,
        "temperature": 0.0,
        "num_predict": 256,
    }
    preload = client.preload("core", keep_alive="2m", timeout=240.0)
    assert preload["load_duration"] == 2_000_000_000
    assert REQUEST_PAYLOADS[-1] == {
        "model": "core",
        "stream": False,
        "keep_alive": "2m",
    }
    assert REQUEST_TIMEOUTS[-1] == 240.0
    assert client.embed("embed", "hello") == [[0.1, 0.2]]
    assert client.model_capabilities("core") == {"completion", "tools", "thinking"}
    assert client.show_model("core")["details"]["family"] == "qwen35"
