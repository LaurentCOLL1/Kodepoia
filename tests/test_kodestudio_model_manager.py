from pathlib import Path

import pytest

from kodepoia.kodestudio.model_manager import (
    DEFAULT_OLLAMA_BASE_URL,
    OllamaModelManager,
    preferred_model,
    saved_model_roles,
    saved_ollama_base_url,
)
from kodepoia.kodestudio.preferences import ApplicationPreferences


class FakeOllamaClient:
    instances = []

    def __init__(self, base_url=DEFAULT_OLLAMA_BASE_URL, timeout=120.0):
        self.base_url = base_url
        self.timeout = timeout
        self.pulled = []
        self.deleted = []
        type(self).instances.append(self)

    def version(self):
        return "0.test"

    def list_models(self):
        return ["qwen3.5:9b", "granite4.1:3b"]

    def pull_model(self, model, *, timeout=3600.0):
        self.pulled.append((model, timeout))
        return {"status": "success"}

    def delete_model(self, model):
        self.deleted.append(model)


def test_default_endpoint_and_saved_endpoint(tmp_path: Path) -> None:
    preferences = ApplicationPreferences(tmp_path / "settings.json")
    manager = OllamaModelManager(preferences, client_factory=FakeOllamaClient)
    assert saved_ollama_base_url(preferences) == DEFAULT_OLLAMA_BASE_URL
    assert manager.set_base_url("http://localhost:11434/") == "http://localhost:11434"
    assert saved_ollama_base_url(preferences) == "http://localhost:11434"
    with pytest.raises(ValueError, match="http:// or https://"):
        manager.set_base_url("localhost:11434")


def test_snapshot_and_role_preferences(tmp_path: Path) -> None:
    preferences = ApplicationPreferences(tmp_path / "settings.json")
    manager = OllamaModelManager(preferences, client_factory=FakeOllamaClient)
    snapshot = manager.snapshot()
    assert snapshot["version"] == "0.test"
    assert snapshot["models"] == ["granite4.1:3b", "qwen3.5:9b"]

    manager.save_roles({"fast": "granite4.1:3b", "core": "qwen3.5:9b", "other": "ignored"})
    assert saved_model_roles(preferences) == {
        "fast": "granite4.1:3b",
        "core": "qwen3.5:9b",
    }
    assert preferred_model(preferences, "CORE") == "qwen3.5:9b"


def test_install_and_delete_delegate_to_ollama(tmp_path: Path) -> None:
    FakeOllamaClient.instances.clear()
    preferences = ApplicationPreferences(tmp_path / "settings.json")
    manager = OllamaModelManager(preferences, client_factory=FakeOllamaClient)

    manager.install("qwen3.5:4b")
    install_client = FakeOllamaClient.instances[-1]
    assert install_client.pulled == [("qwen3.5:4b", 3600.0)]

    manager.delete("qwen3.5:4b")
    delete_client = FakeOllamaClient.instances[-1]
    assert delete_client.deleted == ["qwen3.5:4b"]
