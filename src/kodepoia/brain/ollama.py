from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from kodepoia.brain.base import BrainMessage, BrainResponse
from kodepoia.exceptions import BrainUnavailable


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(f"{self.base_url}{path}", data=data, method=method, headers={"Content-Type": "application/json"} if data else {})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise BrainUnavailable(f"Ollama unavailable at {self.base_url}: {exc}") from exc

    def version(self) -> str:
        return str(self._request("GET", "/api/version").get("version", "unknown"))

    def list_models(self) -> list[str]:
        data = self._request("GET", "/api/tags")
        return [str(item.get("name")) for item in data.get("models", [])]

    def chat(self, model: str, messages: list[BrainMessage], *, tools: list[dict[str, Any]] | None = None, response_schema: dict[str, Any] | str | None = None, think: bool | str | None = None, keep_alive: str | int = "5m") -> BrainResponse:
        payload: dict[str, Any] = {"model": model, "messages": [{"role": msg.role, "content": msg.content} for msg in messages], "stream": False, "keep_alive": keep_alive}
        if tools:
            payload["tools"] = tools
        if response_schema is not None:
            payload["format"] = response_schema
        if think is not None:
            payload["think"] = think
        data = self._request("POST", "/api/chat", payload)
        message = data.get("message", {})
        metrics = {key: data.get(key) for key in ("total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration") if key in data}
        return BrainResponse(content=str(message.get("content", "")), model=str(data.get("model", model)), thinking=message.get("thinking"), tool_calls=tuple(message.get("tool_calls", [])), metrics=metrics)

    def embed(self, model: str, inputs: str | list[str], *, keep_alive: str | int = "5m") -> list[list[float]]:
        data = self._request("POST", "/api/embed", {"model": model, "input": inputs, "keep_alive": keep_alive})
        return [[float(value) for value in vector] for vector in data.get("embeddings", [])]

    def unload(self, model: str) -> None:
        self.chat(model, [BrainMessage("user", "")], keep_alive=0)
