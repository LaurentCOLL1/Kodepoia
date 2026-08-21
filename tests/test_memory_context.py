from pathlib import Path

from kodepoia.intelligence.context import ContextBuilder, ContextItem
from kodepoia.intelligence.memory import MemoryStore


def test_memory_persists_and_semantic_searches(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite")
    store.add("project", "decision", "Godot 4.7", embedding=[1.0, 0.0], importance=0.9)
    store.add("project", "decision", "Use Blender", embedding=[0.0, 1.0], importance=0.8)
    results = store.semantic_search([0.9, 0.1], scope="project", limit=1)
    assert results[0].content == "Godot 4.7"
    store.close()


def test_context_budget_keeps_mandatory() -> None:
    builder = ContextBuilder(budget_tokens=5)
    mandatory = ContextItem("dna", "x" * 100, mandatory=True)
    optional = ContextItem("optional", "y" * 100, priority=1.0)
    bundle = builder.build([optional, mandatory])
    assert mandatory in bundle.items
    assert optional not in bundle.items
