from kodepoia.brain.ollama import OllamaClient


class RecordingOllamaClient(OllamaClient):
    def __init__(self):
        super().__init__()
        self.requests = []

    def _request(self, method, path, payload=None, *, timeout=None):
        self.requests.append((method, path, payload, timeout))
        return {"status": "success"}


def test_pull_model_uses_non_streaming_api() -> None:
    client = RecordingOllamaClient()
    result = client.pull_model("qwen3.5:4b", timeout=42.0)
    assert result == {"status": "success"}
    assert client.requests == [
        ("POST", "/api/pull", {"model": "qwen3.5:4b", "stream": False}, 42.0)
    ]


def test_delete_model_uses_delete_api() -> None:
    client = RecordingOllamaClient()
    client.delete_model("qwen3.5:4b", timeout=17.0)
    assert client.requests == [("DELETE", "/api/delete", {"model": "qwen3.5:4b"}, 17.0)]
