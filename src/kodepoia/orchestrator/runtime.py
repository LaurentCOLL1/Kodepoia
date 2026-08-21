from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from kodepoia.brain.base import Brain, BrainMessage, BrainResponse
from kodepoia.core.audit import AuditLog
from kodepoia.exceptions import BrainUnavailable
from kodepoia.intelligence.context import ContextBuilder, ContextItem
from kodepoia.intelligence.memory import MemoryRecord, MemoryStore
from kodepoia.models.router import KodeModelRouter, ModelSpec, TaskProfile


@dataclass(slots=True)
class Orchestrator:
    brain: Brain
    router: KodeModelRouter
    memory: MemoryStore
    audit: AuditLog
    context_builder: ContextBuilder
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
        response = self.brain.chat(model.name, [BrainMessage("user", prompt)])
        self.audit.append(
            "orchestrator",
            "chat",
            "brain",
            "completed",
            {"model": response.model, "memory_mode": memory_mode},
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
        try:
            for chunk in self.brain.stream_chat(model.name, [BrainMessage("user", prompt)]):
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
