from __future__ import annotations

from pathlib import Path

import pytest
import tree_sitter

from kodepoia.kodecode.api import KodeCodeToolAPI
from kodepoia.kodecode.parser_tool import ParserTool
from kodepoia.kodecode.parsing import (
    LanguageProviderSpec,
    TreeSitterLanguageRegistry,
    TreeSitterParserService,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary


def test_registry_detects_packaged_and_godot_languages() -> None:
    registry = TreeSitterLanguageRegistry()

    assert registry.detect_path("tool.py") == "python"
    assert registry.detect_path("tool.jsx") == "javascript"
    assert registry.detect_path("tool.ts") == "typescript"
    assert registry.detect_path("tool.tsx") == "tsx"
    assert registry.detect_path("player.gd") == "gdscript"
    assert registry.resolve_id("py") == "python"
    assert registry.resolve_id("GD") == "gdscript"


def test_registry_can_add_provider_and_rejects_collisions() -> None:
    registry = TreeSitterLanguageRegistry([])
    registry.register(
        LanguageProviderSpec(
            language_id="demo",
            module_name="tree_sitter_demo",
            factory_name="language",
            extensions=("demo",),
            aliases=("dm",),
        )
    )

    assert registry.detect_path("sample.demo") == "demo"
    assert registry.resolve_id("DM") == "demo"
    assert registry.specs()[0].extensions == (".demo",)

    with pytest.raises(ValueError, match="alias collision"):
        registry.register(
            LanguageProviderSpec(
                language_id="other",
                module_name="tree_sitter_other",
                factory_name="language",
                extensions=(".other",),
                aliases=("dm",),
            )
        )


def test_packaged_grammars_are_available_and_abi_compatible() -> None:
    registry = TreeSitterLanguageRegistry()

    for language_id in ("python", "javascript", "typescript", "tsx"):
        capability = registry.capability(language_id)
        assert capability.available is True
        assert capability.compatible is True
        assert capability.runtime_version == tree_sitter.__version__
        assert capability.runtime_abi_min == tree_sitter.MIN_COMPATIBLE_LANGUAGE_VERSION
        assert capability.runtime_abi_max == tree_sitter.LANGUAGE_VERSION
        assert capability.grammar_abi is not None
        assert tree_sitter.MIN_COMPATIBLE_LANGUAGE_VERSION <= capability.grammar_abi
        assert capability.grammar_abi <= tree_sitter.LANGUAGE_VERSION
        assert capability.error is None


@pytest.mark.parametrize(
    ("language_id", "source", "root_type"),
    [
        ("python", b"def answer():\n    return 42\n", "module"),
        ("javascript", b"function answer() { return 42; }\n", "program"),
        ("typescript", b"function answer(): number { return 42; }\n", "program"),
        ("tsx", b"const view = <div>42</div>;\n", "program"),
    ],
)
def test_packaged_grammars_parse_real_source(
    language_id: str,
    source: bytes,
    root_type: str,
) -> None:
    document = TreeSitterParserService().parse(source, language_id)

    assert document.tree.root_node.type == root_type
    assert document.tree.root_node.has_error is False


def test_gdscript_capability_is_discoverable_without_being_mandatory() -> None:
    capability = TreeSitterLanguageRegistry().capability("gdscript")

    assert capability.language_id == "gdscript"
    assert capability.module_name == "tree_sitter_gdscript"
    if capability.available:
        assert capability.compatible is True
    else:
        assert capability.compatible is False
        assert capability.error is not None


def test_parser_handles_valid_and_malformed_python() -> None:
    service = TreeSitterParserService()

    valid = service.parse("def add(a: int, b: int) -> int:\n    return a + b\n", "python")
    valid_summary = service.summarize(valid)
    assert valid_summary.root_type == "module"
    assert valid_summary.has_error is False
    assert any(node.node_type == "function_definition" for node in valid_summary.nodes)

    malformed = service.parse("def broken(:\n    return 1\n", "python")
    malformed_summary = service.summarize(malformed)
    assert malformed_summary.root_type == "module"
    assert malformed_summary.has_error is True
    assert malformed_summary.extracted_nodes > 0
    assert any(node.has_error or node.is_error or node.is_missing for node in malformed_summary.nodes)


def test_incremental_session_updates_tree_and_reports_changed_ranges() -> None:
    service = TreeSitterParserService()
    session = service.session(b"value = 1\n", "python")

    result = session.apply_edit(start_byte=8, old_end_byte=9, replacement=b"2 + 3")

    assert result.document.source == b"value = 2 + 3\n"
    assert result.document.tree.root_node.has_error is False
    assert result.changed_ranges
    assert any(item.start_byte <= 8 < item.end_byte for item in result.changed_ranges)


def test_parser_tool_is_workspace_scoped_and_auto_detects_language(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("class Demo:\n    pass\n", encoding="utf-8")
    tool = ParserTool(WorkspaceBoundary(tmp_path))

    result = tool.parse_file("sample.py")

    assert result["path"] == "sample.py"
    assert result["language_id"] == "python"
    assert result["root_type"] == "module"
    assert result["has_error"] is False

    with pytest.raises(ValueError, match="max_nodes"):
        tool.parse_file("sample.py", max_nodes=2001)


def test_structured_api_exposes_parser_capabilities_and_parse(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("answer = 42\n", encoding="utf-8")
    api = KodeCodeToolAPI(tmp_path)

    names = {item["function"]["name"] for item in api.catalog()}
    assert "kodecode_parser_capabilities" in names
    assert "kodecode_parser_parse" in names

    capabilities = api.invoke("kodecode_parser_capabilities")
    python_capability = next(item for item in capabilities if item["language_id"] == "python")
    assert python_capability["available"] is True
    assert python_capability["compatible"] is True

    parsed = api.invoke("kodecode_parser_parse", {"path": "sample.py", "max_nodes": 50})
    assert parsed["language_id"] == "python"
    assert parsed["has_error"] is False
    assert parsed["extracted_nodes"] > 0
