from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from kodepoia.kodecode.parsing import TreeSitterLanguageRegistry, TreeSitterParserService
from kodepoia.kodecode.workspace import WorkspaceBoundary

_SYMBOL_TYPES: dict[str, dict[str, str]] = {
    "python": {
        "function_definition": "function",
        "class_definition": "class",
    },
    "javascript": {
        "function_declaration": "function",
        "class_declaration": "class",
        "method_definition": "method",
    },
    "typescript": {
        "function_declaration": "function",
        "class_declaration": "class",
        "method_definition": "method",
        "interface_declaration": "interface",
        "type_alias_declaration": "type",
    },
    "tsx": {
        "function_declaration": "function",
        "class_declaration": "class",
        "method_definition": "method",
        "interface_declaration": "interface",
        "type_alias_declaration": "type",
    },
}
_CALL_TYPES = {"python": {"call"}, "javascript": {"call_expression"}, "typescript": {"call_expression"}, "tsx": {"call_expression"}}
_IMPORT_TYPES = {
    "python": {"import_statement", "import_from_statement"},
    "javascript": {"import_statement", "export_statement"},
    "typescript": {"import_statement", "export_statement"},
    "tsx": {"import_statement", "export_statement"},
}
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_JS_MODULE = re.compile(r"(?:from\s+)?[\"']([^\"']+)[\"']")


@dataclass(frozen=True, slots=True)
class SymbolNode:
    symbol_id: str
    name: str
    qualified_name: str
    kind: str
    language_id: str
    path: str
    start_byte: int
    end_byte: int


@dataclass(frozen=True, slots=True)
class CallEdge:
    edge_id: str
    source_id: str
    target_id: str | None
    target_name: str
    path: str
    start_byte: int


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    edge_id: str
    source_file_id: str
    module: str
    path: str
    start_byte: int


@dataclass(frozen=True, slots=True)
class FileGraph:
    path: str
    file_id: str
    language_id: str
    sha256: str
    symbols: tuple[SymbolNode, ...]
    calls: tuple[CallEdge, ...]
    dependencies: tuple[DependencyEdge, ...]


@dataclass(frozen=True, slots=True)
class GraphSnapshot:
    files: tuple[FileGraph, ...]
    symbols: tuple[SymbolNode, ...]
    calls: tuple[CallEdge, ...]
    dependencies: tuple[DependencyEdge, ...]


@dataclass(frozen=True, slots=True)
class GraphRefreshResult:
    changed_files: tuple[str, ...]
    skipped_files: tuple[str, ...]
    snapshot: GraphSnapshot


class CodeGraphIndex:
    """Incremental Tree-sitter-backed symbol/call/dependency index."""

    def __init__(
        self,
        boundary: WorkspaceBoundary,
        *,
        registry: TreeSitterLanguageRegistry | None = None,
        max_file_bytes: int = 2_000_000,
    ) -> None:
        self.boundary = boundary
        self.registry = registry or TreeSitterLanguageRegistry()
        self.parser = TreeSitterParserService(self.registry)
        self.max_file_bytes = max_file_bytes
        self._files: dict[str, FileGraph] = {}

    def refresh(self, paths: Iterable[str]) -> GraphRefreshResult:
        unique = tuple(dict.fromkeys(str(item) for item in paths))
        if not unique:
            raise ValueError("At least one graph path is required")
        if len(unique) > 200:
            raise ValueError("Graph refresh accepts at most 200 files")

        changed: list[str] = []
        skipped: list[str] = []
        for requested in unique:
            target = self.boundary.resolve(requested, must_exist=True)
            if not target.is_file():
                raise IsADirectoryError(requested)
            size = target.stat().st_size
            if size > self.max_file_bytes:
                raise ValueError(f"File exceeds graph limit ({size} > {self.max_file_bytes}): {requested}")
            relative = self.boundary.relative(target)
            language_id = self.registry.detect_path(relative)
            if language_id is None:
                raise ValueError(f"Cannot detect graph language for: {relative}")
            capability = self.registry.capability(language_id)
            if not capability.available or not capability.compatible:
                raise ValueError(capability.error or f"Tree-sitter language unavailable: {language_id}")
            source = target.read_bytes()
            digest = hashlib.sha256(source).hexdigest()
            existing = self._files.get(relative)
            if existing is not None and existing.sha256 == digest:
                skipped.append(relative)
                continue
            self._files[relative] = self._build_file(relative, source, digest, language_id)
            changed.append(relative)

        return GraphRefreshResult(tuple(changed), tuple(skipped), self.snapshot())

    def snapshot(self) -> GraphSnapshot:
        files = tuple(self._files[path] for path in sorted(self._files))
        symbols = tuple(symbol for item in files for symbol in item.symbols)
        symbol_by_name: dict[str, list[str]] = {}
        for symbol in symbols:
            symbol_by_name.setdefault(symbol.name, []).append(symbol.symbol_id)

        resolved_calls: list[CallEdge] = []
        for item in files:
            for edge in item.calls:
                candidates = symbol_by_name.get(edge.target_name, [])
                target_id = candidates[0] if len(candidates) == 1 else None
                resolved_calls.append(
                    CallEdge(
                        edge_id=edge.edge_id,
                        source_id=edge.source_id,
                        target_id=target_id,
                        target_name=edge.target_name,
                        path=edge.path,
                        start_byte=edge.start_byte,
                    )
                )
        dependencies = tuple(edge for item in files for edge in item.dependencies)
        return GraphSnapshot(files, symbols, tuple(resolved_calls), dependencies)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self.snapshot())

    def _build_file(self, path: str, source: bytes, digest: str, language_id: str) -> FileGraph:
        document = self.parser.parse(source, language_id)
        root = document.tree.root_node
        file_id = _stable_id("file", path)
        symbols: list[SymbolNode] = []
        raw_calls: list[CallEdge] = []
        dependencies: list[DependencyEdge] = []
        symbol_stack: list[SymbolNode] = []
        call_ordinals: dict[tuple[str, str], int] = {}
        dependency_ordinals: dict[str, int] = {}

        def walk(node: Any) -> None:
            node_type = str(node.type)
            symbol_types = _SYMBOL_TYPES.get(language_id, {})
            entered_symbol: SymbolNode | None = None
            if node_type in symbol_types:
                name_node = node.child_by_field_name("name")
                if name_node is not None:
                    name = _text(source, name_node).strip()
                    parent_qualified = symbol_stack[-1].qualified_name if symbol_stack else ""
                    qualified = f"{parent_qualified}.{name}" if parent_qualified else name
                    entered_symbol = SymbolNode(
                        symbol_id=_stable_id("symbol", path, symbol_types[node_type], qualified),
                        name=name,
                        qualified_name=qualified,
                        kind=symbol_types[node_type],
                        language_id=language_id,
                        path=path,
                        start_byte=int(node.start_byte),
                        end_byte=int(node.end_byte),
                    )
                    symbols.append(entered_symbol)
                    symbol_stack.append(entered_symbol)

            if node_type in _CALL_TYPES.get(language_id, set()):
                target = node.child_by_field_name("function")
                if target is None and node.named_children:
                    target = node.named_children[0]
                target_name = _call_name(_text(source, target)) if target is not None else ""
                if target_name:
                    source_id = symbol_stack[-1].symbol_id if symbol_stack else file_id
                    key = (source_id, target_name)
                    ordinal = call_ordinals.get(key, 0)
                    call_ordinals[key] = ordinal + 1
                    raw_calls.append(
                        CallEdge(
                            edge_id=_stable_id("call", source_id, target_name, str(ordinal)),
                            source_id=source_id,
                            target_id=None,
                            target_name=target_name,
                            path=path,
                            start_byte=int(node.start_byte),
                        )
                    )

            if node_type in _IMPORT_TYPES.get(language_id, set()):
                for module in _modules(language_id, _text(source, node)):
                    ordinal = dependency_ordinals.get(module, 0)
                    dependency_ordinals[module] = ordinal + 1
                    dependencies.append(
                        DependencyEdge(
                            edge_id=_stable_id("dependency", file_id, module, str(ordinal)),
                            source_file_id=file_id,
                            module=module,
                            path=path,
                            start_byte=int(node.start_byte),
                        )
                    )

            for child in node.named_children:
                walk(child)
            if entered_symbol is not None:
                symbol_stack.pop()

        walk(root)
        return FileGraph(
            path=path,
            file_id=file_id,
            language_id=language_id,
            sha256=digest,
            symbols=tuple(symbols),
            calls=tuple(raw_calls),
            dependencies=tuple(dependencies),
        )


class GraphTool:
    """Workspace-scoped structured access to the incremental graph index."""

    def __init__(self, boundary: WorkspaceBoundary) -> None:
        self.index = CodeGraphIndex(boundary)

    def refresh(self, paths: Iterable[str]) -> dict[str, Any]:
        return asdict(self.index.refresh(paths))

    def snapshot(self) -> dict[str, Any]:
        return self.index.as_dict()


def _stable_id(kind: str, *parts: str) -> str:
    payload = "\x1f".join((kind, *parts)).encode("utf-8")
    return f"{kind}:{hashlib.sha256(payload).hexdigest()[:24]}"


def _text(source: bytes, node: Any) -> str:
    return source[int(node.start_byte):int(node.end_byte)].decode("utf-8", errors="replace")


def _call_name(text: str) -> str:
    matches = _IDENTIFIER.findall(text)
    return matches[-1] if matches else ""


def _modules(language_id: str, text: str) -> tuple[str, ...]:
    stripped = text.strip()
    if language_id == "python":
        if stripped.startswith("from "):
            head = stripped[5:].split(" import ", 1)[0].strip()
            return (head,) if head else ()
        if stripped.startswith("import "):
            raw = stripped[7:]
            names = []
            for item in raw.split(","):
                name = item.strip().split(" as ", 1)[0].strip()
                if name:
                    names.append(name)
            return tuple(names)
        return ()
    match = _JS_MODULE.search(stripped)
    return (match.group(1),) if match else ()
