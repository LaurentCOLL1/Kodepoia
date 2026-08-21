from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.kodecode.graph_api import GraphToolAPI
from kodepoia.kodecode.graphs import CodeGraphIndex
from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation


def test_graph_index_builds_symbols_calls_dependencies_and_stable_ids(tmp_path: Path) -> None:
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    a.write_text(
        "import os\nfrom pkg.mod import thing\n\ndef helper():\n    return 1\n\ndef main():\n    return helper()\n",
        encoding="utf-8",
    )
    b.write_text("def other():\n    return 2\n", encoding="utf-8")

    index = CodeGraphIndex(WorkspaceBoundary(tmp_path))
    first = index.refresh(["a.py", "b.py"])

    assert first.changed_files == ("a.py", "b.py")
    assert first.skipped_files == ()
    symbols = {item.qualified_name: item for item in first.snapshot.symbols}
    assert {"helper", "main", "other"} <= set(symbols)
    helper_id = symbols["helper"].symbol_id
    main_id = symbols["main"].symbol_id
    call = next(item for item in first.snapshot.calls if item.target_name == "helper")
    assert call.source_id == main_id
    assert call.target_id == helper_id
    modules = {item.module for item in first.snapshot.dependencies}
    assert {"os", "pkg.mod"} <= modules

    second = index.refresh(["a.py", "b.py"])
    assert second.changed_files == ()
    assert second.skipped_files == ("a.py", "b.py")

    a.write_text(
        "import os\nfrom pkg.mod import thing\n\ndef helper():\n    return 42\n\ndef main():\n    return helper()\n",
        encoding="utf-8",
    )
    third = index.refresh(["a.py"])
    assert third.changed_files == ("a.py",)
    symbols_after = {item.qualified_name: item for item in third.snapshot.symbols}
    assert symbols_after["helper"].symbol_id == helper_id
    assert symbols_after["main"].symbol_id == main_id
    assert symbols_after["helper"].path == "a.py"
    assert symbols_after["helper"].start_byte >= 0


def test_graph_call_stays_unresolved_when_target_name_is_ambiguous(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("def helper():\n    return 2\n", encoding="utf-8")
    (tmp_path / "c.py").write_text("def run():\n    return helper()\n", encoding="utf-8")

    index = CodeGraphIndex(WorkspaceBoundary(tmp_path))
    snapshot = index.refresh(["a.py", "b.py", "c.py"]).snapshot
    edge = next(item for item in snapshot.calls if item.target_name == "helper")
    assert edge.target_id is None


def test_graph_api_is_bounded_and_workspace_scoped(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("import json\n\ndef answer():\n    return 42\n", encoding="utf-8")
    api = GraphToolAPI(tmp_path)
    names = {item["function"]["name"] for item in api.catalog()}
    assert names == {
        "kodecode_graph_refresh",
        "kodecode_graph_symbols",
        "kodecode_graph_calls",
        "kodecode_graph_dependencies",
    }

    result = api.invoke("kodecode_graph_refresh", {"paths": ["sample.py"]})
    assert result["changed_files"] == ("sample.py",)
    symbols = api.invoke("kodecode_graph_symbols", {"name": "answer", "max_results": 10})
    assert symbols[0]["name"] == "answer"
    dependencies = api.invoke("kodecode_graph_dependencies", {"name": "json"})
    assert dependencies[0]["module"] == "json"

    with pytest.raises(ValueError, match="max_results"):
        api.invoke("kodecode_graph_symbols", {"max_results": 501})
    with pytest.raises(WorkspaceViolation):
        api.invoke("kodecode_graph_refresh", {"paths": ["../outside.py"]})
