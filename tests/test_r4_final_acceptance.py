from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pytest

from kodepoia.brain.base import BrainMessage, BrainResponse
from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.exceptions import PermissionDenied
from kodepoia.intelligence.context import ContextBuilder
from kodepoia.intelligence.memory import MemoryStore
from kodepoia.kodecode.executor import DEFAULT_TOOL_POLICIES, KodeCodeExecutor
from kodepoia.models.router import KodeModelRouter, ModelRegistry, ModelRole, ModelSpec, TaskProfile
from kodepoia.orchestrator.runtime import Orchestrator


def _permissions(root: Path, *capabilities: Capability) -> PermissionSet:
    result = PermissionSet()
    for capability in capabilities:
        roots = (root,) if capability in {Capability.FILE_READ, Capability.FILE_WRITE, Capability.FILE_DELETE} else ()
        result.grant(PermissionGrant(capability, roots=roots))
    return result


def _executor(root: Path, *capabilities: Capability) -> tuple[KodeCodeExecutor, AuditLog]:
    audit = AuditLog(root / ".kodepoia" / "audit" / "r4.jsonl")
    guardian = KodeGuardian(_permissions(root, *capabilities))
    safe_change = SafeChangeManager(root, root / ".kodepoia" / "snapshots")
    return KodeCodeExecutor(root, guardian=guardian, audit=audit, safe_change=safe_change), audit


def test_executor_requires_explicit_policy_for_every_catalog_tool(tmp_path: Path) -> None:
    executor, _audit = _executor(
        tmp_path,
        Capability.FILE_READ,
        Capability.FILE_WRITE,
        Capability.PROCESS_EXECUTE,
    )
    names = {item["function"]["name"] for item in executor.catalog()}
    assert names == set(executor._providers)
    assert names <= set(DEFAULT_TOOL_POLICIES)
    assert "kodecode_files_read" in names
    assert "kodecode_graph_refresh" in names
    assert "kodecode_lsp_start" in names
    assert "kodecode_dap_start" in names


def test_patch_requires_permission_snapshots_old_content_and_audits(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    denied, denied_audit = _executor(tmp_path, Capability.FILE_READ)
    with pytest.raises(PermissionDenied):
        denied.invoke(
            "kodecode_patch_replace_once",
            {"path": "sample.py", "old_text": "VALUE = 1", "new_text": "VALUE = 2"},
        )
    assert source.read_text(encoding="utf-8") == "VALUE = 1\n"
    assert denied_audit.verify() is True

    executor, audit = _executor(tmp_path, Capability.FILE_READ, Capability.FILE_WRITE)
    result = executor.invoke(
        "kodecode_patch_replace_once",
        {"path": "sample.py", "old_text": "VALUE = 1", "new_text": "VALUE = 2"},
    )
    assert source.read_text(encoding="utf-8") == "VALUE = 2\n"
    assert result.snapshot is not None
    snapshot_file = Path(result.snapshot) / "sample.py"
    assert snapshot_file.read_text(encoding="utf-8") == "VALUE = 1\n"
    assert audit.verify() is True
    events = [json.loads(line) for line in audit.path.read_text(encoding="utf-8").splitlines()]
    outcomes = [item["outcome"] for item in events if item["action"] == "kodecode_patch_replace_once"]
    assert "authorized" in outcomes
    assert "completed" in outcomes


def test_execute_tools_are_denied_without_process_permission(tmp_path: Path) -> None:
    executor, audit = _executor(tmp_path, Capability.FILE_READ)
    with pytest.raises(PermissionDenied):
        executor.invoke("kodecode_git_worktree_add", {"name": "blocked"})
    assert audit.verify() is True


def test_repository_scale_kodecode_acceptance_flow(tmp_path: Path) -> None:
    paths: list[str] = []
    for index in range(30):
        path = tmp_path / f"module_{index}.py"
        dependency = "" if index == 0 else f"from module_{index - 1} import func_{index - 1}\n"
        call = "return 0" if index == 0 else f"return func_{index - 1}() + 1"
        path.write_text(
            f"{dependency}\ndef func_{index}():\n    {call}\n",
            encoding="utf-8",
        )
        paths.append(path.name)

    executor, audit = _executor(tmp_path, Capability.FILE_READ, Capability.FILE_WRITE)

    read = executor.invoke("kodecode_files_read", {"path": "module_29.py"}).result
    assert "func_29" in read["content"]

    search = executor.invoke(
        "kodecode_search",
        {"query": "def func_", "paths": ["."], "max_results": 100},
    ).result
    assert len(search) == 30

    parsed = executor.invoke(
        "kodecode_parser_parse",
        {"path": "module_29.py", "max_nodes": 200},
    ).result
    assert parsed["language_id"] == "python"
    assert parsed["has_error"] is False

    refreshed = executor.invoke("kodecode_graph_refresh", {"paths": paths}).result
    assert len(refreshed["changed_files"]) == 30
    assert refreshed["skipped_files"] == ()

    symbols = executor.invoke(
        "kodecode_graph_symbols",
        {"name": "func_", "max_results": 100},
    ).result
    assert len(symbols) == 30
    symbol_29_before = next(item for item in symbols if item["name"] == "func_29")

    calls = executor.invoke(
        "kodecode_graph_calls",
        {"name": "func_28", "max_results": 10},
    ).result
    assert len(calls) == 1
    assert calls[0]["target_id"] is not None

    dependencies = executor.invoke(
        "kodecode_graph_dependencies",
        {"name": "module_28", "max_results": 10},
    ).result
    assert dependencies[0]["module"] == "module_28"

    second = executor.invoke("kodecode_graph_refresh", {"paths": paths}).result
    assert len(second["skipped_files"]) == 30

    patch = executor.invoke(
        "kodecode_patch_replace_once",
        {"path": "module_29.py", "old_text": "+ 1", "new_text": "+ 2"},
    )
    assert patch.snapshot is not None
    changed = executor.invoke("kodecode_graph_refresh", {"paths": ["module_29.py"]}).result
    assert changed["changed_files"] == ("module_29.py",)
    symbols_after = executor.invoke(
        "kodecode_graph_symbols",
        {"name": "func_29", "max_results": 10},
    ).result
    assert symbols_after[0]["symbol_id"] == symbol_29_before["symbol_id"]
    assert audit.verify() is True


class _ToolCallingBrain:
    def __init__(self) -> None:
        self.last_tools: list[dict[str, Any]] = []

    def embed(self, _model: str, _inputs: str | list[str], **_kwargs: Any) -> list[list[float]]:
        return []

    def chat(self, model: str, _messages: list[BrainMessage], **kwargs: Any) -> BrainResponse:
        self.last_tools = list(kwargs.get("tools", []))
        return BrainResponse(
            content="",
            model=model,
            tool_calls=(
                {
                    "function": {
                        "name": "kodecode_files_read",
                        "arguments": {"path": "hello.py"},
                    }
                },
            ),
        )

    def stream_chat(
        self,
        model: str,
        messages: list[BrainMessage],
        **kwargs: Any,
    ) -> Iterable[BrainResponse]:
        yield self.chat(model, messages, **kwargs)


def test_orchestrator_supplies_catalog_and_executes_brain_tool_calls(tmp_path: Path) -> None:
    (tmp_path / "hello.py").write_text("print('hello')\n", encoding="utf-8")
    executor, audit = _executor(tmp_path, Capability.FILE_READ)
    brain = _ToolCallingBrain()
    registry = ModelRegistry(
        [ModelSpec("core-test", ModelRole.CORE, supports_tools=True, supports_structured=True)]
    )
    orchestrator = Orchestrator(
        brain=brain,
        router=KodeModelRouter(registry),
        memory=MemoryStore(tmp_path / ".kodepoia" / "memory.db"),
        audit=audit,
        context_builder=ContextBuilder(),
        kodecode_executor=executor,
    )

    response = orchestrator.answer("Read hello.py", TaskProfile(needs_tools=True))
    tool_names = {item["function"]["name"] for item in brain.last_tools}
    assert "kodecode_files_read" in tool_names
    assert "kodecode_graph_symbols" in tool_names

    results = orchestrator.execute_tool_calls(response)
    assert results[0]["tool_name"] == "kodecode_files_read"
    assert results[0]["result"]["content"] == "print('hello')\n"
    assert audit.verify() is True
