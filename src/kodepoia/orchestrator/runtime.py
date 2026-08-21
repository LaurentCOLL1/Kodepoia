from __future__ import annotations

from dataclasses import dataclass

from kodepoia.brain.base import BrainMessage, BrainResponse
from kodepoia.brain.ollama import OllamaClient
from kodepoia.core.audit import AuditLog
from kodepoia.intelligence.context import ContextBuilder, ContextItem
from kodepoia.intelligence.memory import MemoryStore
from kodepoia.models.router import KodeModelRouter, TaskProfile


@dataclass(slots=True)
class Orchestrator:
    brain: OllamaClient
    router: KodeModelRouter
    memory: MemoryStore
    audit: AuditLog
    context_builder: ContextBuilder

    def answer(
        self,
        user_text: str,
        task: TaskProfile,
        project_context: list[ContextItem] | None = None,
    ) -> BrainResponse:
        model = self.router.route(task)
        memory_items = [
            ContextItem(f"memory:{item.kind}", item.content, priority=item.importance)
            for item in self.memory.list(scope="project", limit=12)
        ]
        bundle = self.context_builder.build([*(project_context or []), *memory_items])
        prompt = user_text if not bundle.items else f"{bundle.render()}\n\n## User task\n{user_text}"
        self.audit.append("orchestrator", "chat", "user", "started", {"model": model.name})
        response = self.brain.chat(model.name, [BrainMessage("user", prompt)])
        self.audit.append("orchestrator", "chat", "brain", "completed", {"model": response.model})
        return response
