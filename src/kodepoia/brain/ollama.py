from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

from kodepoia.brain.base import BrainMessage, BrainResponse
from kodepoia.exceptions import BrainUnavailable


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _urlopen(self, request: urllib.request.Request, *, timeout: float | None = None):
        try:
            return urllib.request.urlopen(
                request,
                timeout=self.timeout if timeout is None else timeout,
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise BrainUnavailable(f"Ollama unavailable at {self.base_url}: {exc}") from exc

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if data else {},
        )
        try:
            with self._urlopen(request, timeout=timeout) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise BrainUnavailable(f"Invalid JSON returned by Ollama: {exc}") from exc
        if not isinstance(decoded, dict):
            raise BrainUnavailable("Ollama returned a non-object JSON response")
        return decoded

    @staticmethod
    def _messages(messages: list[BrainMessage]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for message in messages:
            item: dict[str, Any] = {"role": message.role, "content": message.content}
            if message.images:
                item["images"] = list(message.images)
            payload.append(item)
        return payload

    def _chat_payload(
        self,
        model: str,
        messages: list[BrainMessage],
        *,
        stream: bool,
        tools: list[dict[str, Any]] | None = None,
        response_schema: dict[str, Any] | str | None = None,
        think: bool | str | None = None,
        keep_alive: str | int = "5m",
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": self._messages(messages),
            "stream": stream,
            "keep_alive": keep_alive,
        }
        if tools:
            payload["tools"] = tools
        if response_schema is not None:
            payload["format"] = response_schema
        if think is not None:
            payload["think"] = think
        if options:
            payload["options"] = dict(options)
        return payload

    @staticmethod
    def _brain_response(data: dict[str, Any], fallback_model: str) -> BrainResponse:
        message = data.get("message", {})
        if not isinstance(message, dict):
            message = {}
        metrics = {
            key: data.get(key)
            for key in (
                "done_reason",
                "total_duration",
                "load_duration",
                "prompt_eval_count",
                "prompt_eval_duration",
                "eval_count",
                "eval_duration",
            )
            if key in data
        }
        return BrainResponse(
            content=str(message.get("content", "")),
            model=str(data.get("model", fallback_model)),
            thinking=message.get("thinking"),
            tool_calls=tuple(message.get("tool_calls", [])),
            metrics=metrics,
            done=bool(data.get("done", True)),
        )

    def version(self) -> str:
        return str(self._request("GET", "/api/version").get("version", "unknown"))

    def list_models(self) -> list[str]:
        data = self._request("GET", "/api/tags")
        return [str(item.get("name")) for item in data.get("models", [])]

    def show_model(self, model: str, *, verbose: bool = False) -> dict[str, Any]:
        """Return Ollama's local metadata/capabilities for one installed model."""
        return self._request("POST", "/api/show", {"model": model, "verbose": verbose})

    def model_capabilities(self, model: str) -> set[str]:
        data = self.show_model(model)
        return {str(value).lower() for value in data.get("capabilities", [])}

    def running_models(self) -> list[dict[str, Any]]:
        data = self._request("GET", "/api/ps")
        result: list[dict[str, Any]] = []
        for item in data.get("models", []):
            if isinstance(item, dict):
                result.append(dict(item))
        return result

    def preload(
        self,
        model: str,
        *,
        keep_alive: str | int = "2m",
        timeout: float = 240.0,
    ) -> dict[str, Any]:
        """Load a model without turning the cold-load cost into a scored task."""
        return self._request(
            "POST",
            "/api/chat",
            {
                "model": model,
                "stream": False,
                "keep_alive": keep_alive,
            },
            timeout=timeout,
        )

    def chat(
        self,
        model: str,
        messages: list[BrainMessage],
        *,
        tools: list[dict[str, Any]] | None = None,
        response_schema: dict[str, Any] | str | None = None,
        think: bool | str | None = None,
        keep_alive: str | int = "5m",
        options: dict[str, Any] | None = None,
    ) -> BrainResponse:
        payload = self._chat_payload(
            model,
            messages,
            stream=False,
            tools=tools,
            response_schema=response_schema,
            think=think,
            keep_alive=keep_alive,
            options=options,
        )
        return self._brain_response(self._request("POST", "/api/chat", payload), model)

    def stream_chat(
        self,
        model: str,
        messages: list[BrainMessage],
        *,
        tools: list[dict[str, Any]] | None = None,
        response_schema: dict[str, Any] | str | None = None,
        think: bool | str | None = None,
        keep_alive: str | int = "5m",
        options: dict[str, Any] | None = None,
    ) -> Iterator[BrainResponse]:
        payload = self._chat_payload(
            model,
            messages,
            stream=True,
            tools=tools,
            response_schema=response_schema,
            think=think,
            keep_alive=keep_alive,
            options=options,
        )
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with self._urlopen(request) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    if not isinstance(data, dict):
                        raise BrainUnavailable("Ollama stream returned a non-object JSON chunk")
                    yield self._brain_response(data, model)
        except json.JSONDecodeError as exc:
            raise BrainUnavailable(f"Invalid JSON in Ollama stream: {exc}") from exc

    def embed(
        self,
        model: str,
        inputs: str | list[str],
        *,
        keep_alive: str | int = "5m",
    ) -> list[list[float]]:
        data = self._request(
            "POST",
            "/api/embed",
            {"model": model, "input": inputs, "keep_alive": keep_alive},
        )
        return [[float(value) for value in vector] for vector in data.get("embeddings", [])]

    def unload(self, model: str) -> None:
        self.chat(model, [BrainMessage("user", "")], keep_alive=0)
