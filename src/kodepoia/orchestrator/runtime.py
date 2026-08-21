from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any

from kodepoia.brain.base import Brain, BrainMessage, BrainResponse
from kodepoia.core.audit import AuditLog
from kodepoia.exceptions import BrainUnavailable
from kodepoia.intelligence.context import ContextBuilder, ContextItem
from kodepoia.intelligence.memory import MemoryRecord, MemoryStore
from kodepoia.kodecode.executor import KodeCodeExecutor
from kodepoia.models.router import KodeModelRouter, ModelSpec, TaskProfile


@dataclass(slots=True)
class Orchestrator:
    brain: Brain
    router: KodeModelRouter
    memory: MemoryStore
    audit: AuditLog
    context_builder: ContextBuilder
    kodecode_executor: KodeCodeExecutor | None = None
    memory_scope: str = "project"
    semantic_memory_limit: int = 12

    def _retrieve_memory(self, user_text: str) -> tuple[list[MemoryRecord], str]:
        try:
            embedding_model = self.router.route(TaskProfile(needs_embeddings=True))
            vectors = self.brain.embed(embedding_model.name, user_text)
            if vectors:
                semantic = self.memory.semantic_search(
                    vectors[0],
                    scope=self.memory_scope,
                    limit=self.semantic_memory_limit,
                )
                if semantic:
                    return semantic, "semantic"
        except (AttributeError, BrainUnavailable, LookupError, ValueError):
            pass
        return (
            self.memory.list(scope=self.memory_scope, limit=self.semantic_memory_limit),
            "priority-fallback",
        )

    def _prepare(
        self,
        user_text: str,
        task: TaskProfile,
        project_context: list[ContextItem] | None,
    ) -> tuple[ModelSpec, str, str, int]:
        model = self.router.route(task)
        records, memory_mode = self._retrieve_memory(user_text)
        memory_items = [
            ContextItem(f"memory:{item.kind}", item.content, priority=item.importance)
            for item in records
        ]
        bundle = self.context_builder.build([*(project_context or []), *memory_items])
        prompt = user_text if not bundle.items else f"{bundle.render()}\n\n## User task\n{user_text}"
        return model, prompt, memory_mode, len(records)

    def tool_catalog(self) -> list[dict[str, Any]]:
        if self.kodecode_executor is None:
            return []
        return self.kodecode_executor.catalog()

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        actor: str = "brain",
        confirmed: bool = False,
    ) -> dict[str, Any]:
        if self.kodecode_executor is None:
            raise RuntimeError("KodeCode executor is not configured")
        result = self.kodecode_executor.invoke(
            tool_name,
            arguments,
            actor=actor,
            confirmed=confirmed,
        )
        return {
            "tool_name": result.tool_name,
            "result": result.result,
            "snapshot": result.snapshot,
        }

    def execute_tool_calls(
        self,
        response: BrainResponse,
        *,
        actor: str = "brain",
        confirmed_tools: Iterable[str] = (),
    ) -> list[dict[str, Any]]:
        confirmed = set(confirmed_tools)
        results: list[dict[str, Any]] = []
        for call in response.tool_calls:
            if not isinstance(call, dict):
                raise ValueError("Tool call must be an object")
            function = call.get("function", call)
            if not isinstance(function, dict):
                raise ValueError("Tool call function must be an object")
            name = function.get("name") or call.get("name")
            if not isinstance(name, str) or not name:
                raise ValueError("Tool call is missing a function name")
            arguments = function.get("arguments", call.get("arguments", {}))
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            if arguments is None:
                arguments = {}
            if not isinstance(arguments, dict):
                raise ValueError("Tool call arguments must be an object")
            results.append(
                self.execute_tool(
                    name,
                    arguments,
                    actor=actor,
                    confirmed=name in confirmed,
                )
            )
        return results

    def answer(
        self,
        user_text: str,
        task: TaskProfile,
        project_context: list[ContextItem] | None = None,
    ) -> BrainResponse:
        model, prompt, memory_mode, memory_count = self._prepare(
            user_text,
            task,
            project_context,
        )
        self.audit.append(
            "orchestrator",
            "chat",
            "user",
            "started",
            {"model": model.name, "memory_mode": memory_mode, "memory_count": memory_count},
        )
        tools = self.tool_catalog()
        if tools:
            response = self.brain.chat(model.name, [BrainMessage("user", prompt)], tools=tools)
        else:
            response = self.brain.chat(model.name, [BrainMessage("user", prompt)])
        self.audit.append(
            "orchestrator",
            "chat",
            "brain",
            "completed",
            {
                "model": response.model,
                "memory_mode": memory_mode,
                "tool_call_count": len(response.tool_calls),
            },
        )
        return response

    def stream_answer(
        self,
        user_text: str,
        task: TaskProfile,
        project_context: list[ContextItem] | None = None,
    ) -> Iterator[BrainResponse]:
        model, prompt, memory_mode, memory_count = self._prepare(
            user_text,
            task,
            project_context,
        )
        self.audit.append(
            "orchestrator",
            "chat-stream",
            "user",
            "started",
            {"model": model.name, "memory_mode": memory_mode, "memory_count": memory_count},
        )
        last_model = model.name
        tools = self.tool_catalog()
        try:
            stream = (
                self.brain.stream_chat(model.name, [BrainMessage("user", prompt)], tools=tools)
                if tools
                else self.brain.stream_chat(model.name, [BrainMessage("user", prompt)])
            )
            for chunk in stream:
                last_model = chunk.model
                yield chunk
        finally:
            self.audit.append(
                "orchestrator",
                "chat-stream",
                "brain",
                "completed",
                {"model": last_model, "memory_mode": memory_mode},
            )
