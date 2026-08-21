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


def fake_urlopen(request, timeout=0):
    if request.full_url.endswith("/api/version"):
        return FakeResponse(json.dumps({"version": "test"}).encode())
    if request.full_url.endswith("/api/tags"):
        return FakeResponse(json.dumps({"models": [{"name": "core"}]}).encode())
    if request.full_url.endswith("/api/embed"):
        return FakeResponse(json.dumps({"embeddings": [[0.1, 0.2]]}).encode())
    return FakeResponse(json.dumps({"model": "core", "message": {"content": "OK"}, "done": True}).encode())


@patch("urllib.request.urlopen", side_effect=fake_urlopen)
def test_ollama_api(mock_open) -> None:
    client = OllamaClient()
    assert client.version() == "test"
    assert client.list_models() == ["core"]
    assert client.chat("core", [BrainMessage("user", "Hi")]).content == "OK"
    assert client.embed("embed", "hello") == [[0.1, 0.2]]
