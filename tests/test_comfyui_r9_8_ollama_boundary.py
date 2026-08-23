from __future__ import annotations

import pytest

from kodepoia.brain.ollama import OllamaClient
from kodepoia.comfyui.errors import ComfyGovernanceError
from kodepoia.comfyui.resources import OllamaMemoryAdapter


@pytest.mark.parametrize(
    "url",
    (
        "http://127.0.0.1:11434",
        "https://localhost:11434",
        "http://[::1]:11434",
    ),
)
def test_r98_ollama_boundary_accepts_explicit_port_loopback_origin(url: str) -> None:
    adapter = OllamaMemoryAdapter(OllamaClient(url))
    assert adapter.client.base_url == url


@pytest.mark.parametrize(
    "url",
    (
        "http://127.0.0.1",
        "http://localhost",
        "http://[::1]",
        "http://user:secret@127.0.0.1:11434",
        "http://127.0.0.1:11434/api",
        "http://127.0.0.1:11434?model=x",
        "http://127.0.0.1:11434#fragment",
        "http://192.168.1.10:11434",
        "http://example.com:11434",
        "ftp://127.0.0.1:11434",
        "http://127.0.0.1:99999",
    ),
)
def test_r98_ollama_boundary_rejects_ambiguous_or_non_loopback_url(url: str) -> None:
    with pytest.raises(ComfyGovernanceError):
        OllamaMemoryAdapter(OllamaClient(url))
