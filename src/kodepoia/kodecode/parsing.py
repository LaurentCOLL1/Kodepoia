from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Iterable


class TreeSitterUnavailable(RuntimeError):
    """Raised when the requested Tree-sitter runtime or grammar is unavailable."""


@dataclass(frozen=True, slots=True)
class LanguageProviderSpec:
    language_id: str
    module_name: str
    factory_name: str
    extensions: tuple[str, ...]
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LanguageCapability:
    language_id: str
    module_name: str
    factory_name: str
    extensions: tuple[str, ...]
    aliases: tuple[str, ...]
    available: bool
    compatible: bool
    runtime_version: str | None
    runtime_abi_min: int | None
    runtime_abi_max: int | None
    grammar_name: str | None
    grammar_abi: int | None
    grammar_semantic_version: str | None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class SyntaxNodeSnapshot:
    node_type: str
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    end_point: tuple[int, int]
    named: bool
    is_error: bool
    is_missing: bool
    has_error: bool


@dataclass(frozen=True, slots=True)
class ChangedRangeSnapshot:
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    end_point: tuple[int, int]


@dataclass(slots=True)
class ParseDocument:
    language_id: str
    source: bytes
    tree: Any


@dataclass(frozen=True, slots=True)
class ParseSummary:
    language_id: str
    byte_length: int
    root_type: str
    has_error: bool
    error_nodes: int
    missing_nodes: int
    extracted_nodes: int
    nodes: tuple[SyntaxNodeSnapshot, ...]


@dataclass(frozen=True, slots=True)
class IncrementalParseResult:
    document: ParseDocument
    changed_ranges: tuple[ChangedRangeSnapshot, ...]


DEFAULT_LANGUAGE_SPECS = (
    LanguageProviderSpec(
        language_id="python",
        module_name="tree_sitter_python",
        factory_name="language",
        extensions=(".py", ".pyi"),
        aliases=("py",),
    ),
    LanguageProviderSpec(
        language_id="javascript",
        module_name="tree_sitter_javascript",
        factory_name="language",
        extensions=(".js", ".jsx", ".mjs", ".cjs"),
        aliases=("js", "jsx"),
    ),
    LanguageProviderSpec(
        language_id="typescript",
        module_name="tree_sitter_typescript",
        factory_name="language_typescript",
        extensions=(".ts", ".mts", ".cts"),
        aliases=("ts",),
    ),
    LanguageProviderSpec(
        language_id="tsx",
        module_name="tree_sitter_typescript",
        factory_name="language_tsx",
        extensions=(".tsx",),
    ),
    LanguageProviderSpec(
        language_id="gdscript",
        module_name="tree_sitter_gdscript",
        factory_name="language",
        extensions=(".gd",),
        aliases=("gd",),
    ),
)


class TreeSitterLanguageRegistry:
    """Provider-based Tree-sitter registry with explicit ABI compatibility checks.

    Grammar modules are imported lazily. Kodepoia can therefore start without the
    optional ``code`` extra, report missing capabilities cleanly, and register
    future language providers without changing the parser core.
    """

    def __init__(self, specs: Iterable[LanguageProviderSpec] | None = None) -> None:
        self._specs: dict[str, LanguageProviderSpec] = {}
        self._aliases: dict[str, str] = {}
        self._extensions: dict[str, str] = {}
        selected = DEFAULT_LANGUAGE_SPECS if specs is None else tuple(specs)
        for spec in selected:
            self.register(spec)

    def register(self, spec: LanguageProviderSpec) -> None:
        language_id = spec.language_id.strip().lower()
        if not language_id:
            raise ValueError("language_id cannot be empty")
        if language_id in self._specs:
            raise ValueError(f"Tree-sitter language already registered: {language_id}")
        if not spec.module_name.strip() or not spec.factory_name.strip():
            raise ValueError("module_name and factory_name cannot be empty")

        aliases = tuple(alias.strip().lower() for alias in spec.aliases if alias.strip())
        extensions = tuple(self._normalize_extension(item) for item in spec.extensions)
        if not extensions:
            raise ValueError("At least one file extension is required")

        for alias in (language_id, *aliases):
            owner = self._aliases.get(alias)
            if owner is not None:
                raise ValueError(f"Tree-sitter alias collision: {alias} already belongs to {owner}")
        for extension in extensions:
            owner = self._extensions.get(extension)
            if owner is not None:
                raise ValueError(
                    f"Tree-sitter extension collision: {extension} already belongs to {owner}"
                )

        normalized = LanguageProviderSpec(
            language_id=language_id,
            module_name=spec.module_name.strip(),
            factory_name=spec.factory_name.strip(),
            extensions=extensions,
            aliases=aliases,
        )
        self._specs[language_id] = normalized
        for alias in (language_id, *aliases):
            self._aliases[alias] = language_id
        for extension in extensions:
            self._extensions[extension] = language_id

    def specs(self) -> tuple[LanguageProviderSpec, ...]:
        return tuple(self._specs.values())

    def resolve_id(self, language: str) -> str:
        normalized = language.strip().lower()
        resolved = self._aliases.get(normalized)
        if resolved is None:
            raise KeyError(f"Unknown Tree-sitter language: {language}")
        return resolved

    def detect_path(self, path: str | Path) -> str | None:
        suffix = Path(path).suffix.lower()
        return self._extensions.get(suffix) if suffix else None

    def capability(self, language: str) -> LanguageCapability:
        language_id = self.resolve_id(language)
        spec = self._specs[language_id]
        try:
            runtime = import_module("tree_sitter")
        except ImportError as exc:
            return self._missing_capability(spec, f"tree-sitter runtime unavailable: {exc}")

        runtime_version = str(getattr(runtime, "__version__", "unknown"))
        runtime_min = int(getattr(runtime, "MIN_COMPATIBLE_LANGUAGE_VERSION", 0))
        runtime_max = int(getattr(runtime, "LANGUAGE_VERSION", 0))
        try:
            provider_spec = find_spec(spec.module_name)
        except (ImportError, ModuleNotFoundError) as exc:
            provider_spec = None
            provider_error = str(exc)
        else:
            provider_error = None

        if provider_spec is None:
            detail = provider_error or f"grammar provider not installed: {spec.module_name}"
            return LanguageCapability(
                language_id=spec.language_id,
                module_name=spec.module_name,
                factory_name=spec.factory_name,
                extensions=spec.extensions,
                aliases=spec.aliases,
                available=False,
                compatible=False,
                runtime_version=runtime_version,
                runtime_abi_min=runtime_min,
                runtime_abi_max=runtime_max,
                grammar_name=None,
                grammar_abi=None,
                grammar_semantic_version=None,
                error=detail,
            )

        try:
            tree_language = self._load_tree_language(spec, runtime)
            grammar_abi = int(tree_language.abi_version)
            compatible = runtime_min <= grammar_abi <= runtime_max
            error = None if compatible else (
                f"grammar ABI {grammar_abi} is outside supported range {runtime_min}..{runtime_max}"
            )
            semantic = getattr(tree_language, "semantic_version", None)
            return LanguageCapability(
                language_id=spec.language_id,
                module_name=spec.module_name,
                factory_name=spec.factory_name,
                extensions=spec.extensions,
                aliases=spec.aliases,
                available=True,
                compatible=compatible,
                runtime_version=runtime_version,
                runtime_abi_min=runtime_min,
                runtime_abi_max=runtime_max,
                grammar_name=getattr(tree_language, "name", None),
                grammar_abi=grammar_abi,
                grammar_semantic_version=str(semantic) if semantic is not None else None,
                error=error,
            )
        except (AttributeError, ImportError, TypeError, ValueError) as exc:
            return LanguageCapability(
                language_id=spec.language_id,
                module_name=spec.module_name,
                factory_name=spec.factory_name,
                extensions=spec.extensions,
                aliases=spec.aliases,
                available=True,
                compatible=False,
                runtime_version=runtime_version,
                runtime_abi_min=runtime_min,
                runtime_abi_max=runtime_max,
                grammar_name=None,
                grammar_abi=None,
                grammar_semantic_version=None,
                error=str(exc),
            )

    def capabilities(self) -> tuple[LanguageCapability, ...]:
        return tuple(self.capability(spec.language_id) for spec in self._specs.values())

    def load(self, language: str) -> Any:
        language_id = self.resolve_id(language)
        spec = self._specs[language_id]
        try:
            runtime = import_module("tree_sitter")
        except ImportError as exc:
            raise TreeSitterUnavailable("Install Kodepoia with the 'code' extra") from exc

        capability = self.capability(language_id)
        if not capability.available or not capability.compatible:
            raise TreeSitterUnavailable(capability.error or f"Language unavailable: {language_id}")
        return self._load_tree_language(spec, runtime)

    @staticmethod
    def _load_tree_language(spec: LanguageProviderSpec, runtime: Any) -> Any:
        provider = import_module(spec.module_name)
        factory = getattr(provider, spec.factory_name)
        raw_language = factory()
        language_type = runtime.Language
        if isinstance(raw_language, language_type):
            return raw_language
        return language_type(raw_language)

    @staticmethod
    def _missing_capability(spec: LanguageProviderSpec, error: str) -> LanguageCapability:
        return LanguageCapability(
            language_id=spec.language_id,
            module_name=spec.module_name,
            factory_name=spec.factory_name,
            extensions=spec.extensions,
            aliases=spec.aliases,
            available=False,
            compatible=False,
            runtime_version=None,
            runtime_abi_min=None,
            runtime_abi_max=None,
            grammar_name=None,
            grammar_abi=None,
            grammar_semantic_version=None,
            error=error,
        )

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        normalized = extension.strip().lower()
        if not normalized:
            raise ValueError("File extension cannot be empty")
        return normalized if normalized.startswith(".") else f".{normalized}"


class TreeSitterParserService:
    """Tree-sitter parser façade supporting tolerant and incremental parsing."""

    def __init__(self, registry: TreeSitterLanguageRegistry | None = None) -> None:
        self.registry = registry or TreeSitterLanguageRegistry()

    def parse(self, source: bytes | str, language: str) -> ParseDocument:
        source_bytes = source.encode("utf-8") if isinstance(source, str) else bytes(source)
        parser = self._new_parser(language)
        tree = parser.parse(source_bytes)
        if tree is None:
            raise RuntimeError("Tree-sitter parser returned no tree")
        return ParseDocument(
            language_id=self.registry.resolve_id(language),
            source=source_bytes,
            tree=tree,
        )

    def session(self, source: bytes | str, language: str) -> IncrementalParseSession:
        return IncrementalParseSession(self, source, language)

    def summarize(
        self,
        document: ParseDocument,
        *,
        max_nodes: int = 200,
        named_only: bool = True,
    ) -> ParseSummary:
        nodes = self.extract_nodes(document, max_nodes=max_nodes, named_only=named_only)
        return ParseSummary(
            language_id=document.language_id,
            byte_length=len(document.source),
            root_type=str(document.tree.root_node.type),
            has_error=bool(document.tree.root_node.has_error),
            error_nodes=sum(1 for node in nodes if node.is_error),
            missing_nodes=sum(1 for node in nodes if node.is_missing),
            extracted_nodes=len(nodes),
            nodes=nodes,
        )

    def extract_nodes(
        self,
        document: ParseDocument,
        *,
        max_nodes: int = 200,
        named_only: bool = True,
    ) -> tuple[SyntaxNodeSnapshot, ...]:
        if max_nodes < 1:
            raise ValueError("max_nodes must be positive")

        root = document.tree.root_node
        stack = [root]
        snapshots: list[SyntaxNodeSnapshot] = []
        while stack and len(snapshots) < max_nodes:
            node = stack.pop()
            named = bool(node.is_named)
            if not named_only or named:
                snapshots.append(
                    SyntaxNodeSnapshot(
                        node_type=str(node.type),
                        start_byte=int(node.start_byte),
                        end_byte=int(node.end_byte),
                        start_point=(int(node.start_point.row), int(node.start_point.column)),
                        end_point=(int(node.end_point.row), int(node.end_point.column)),
                        named=named,
                        is_error=bool(node.is_error),
                        is_missing=bool(node.is_missing),
                        has_error=bool(node.has_error),
                    )
                )
            children = node.named_children if named_only else node.children
            stack.extend(reversed(children))
        return tuple(snapshots)

    def _new_parser(self, language: str) -> Any:
        try:
            runtime = import_module("tree_sitter")
        except ImportError as exc:
            raise TreeSitterUnavailable("Install Kodepoia with the 'code' extra") from exc
        tree_language = self.registry.load(language)
        return runtime.Parser(tree_language)


class IncrementalParseSession:
    """Stateful parse session using Tree.edit + Parser.parse(old_tree=...)."""

    def __init__(
        self,
        service: TreeSitterParserService,
        source: bytes | str,
        language: str,
    ) -> None:
        self.service = service
        self.language_id = service.registry.resolve_id(language)
        self.source = source.encode("utf-8") if isinstance(source, str) else bytes(source)
        self.parser = service._new_parser(self.language_id)
        tree = self.parser.parse(self.source)
        if tree is None:
            raise RuntimeError("Tree-sitter parser returned no tree")
        self.tree = tree

    @property
    def document(self) -> ParseDocument:
        return ParseDocument(self.language_id, self.source, self.tree)

    def apply_edit(
        self,
        *,
        start_byte: int,
        old_end_byte: int,
        replacement: bytes | str,
    ) -> IncrementalParseResult:
        if start_byte < 0 or old_end_byte < start_byte or old_end_byte > len(self.source):
            raise ValueError("Invalid byte edit range")

        replacement_bytes = replacement.encode("utf-8") if isinstance(replacement, str) else bytes(replacement)
        old_source = self.source
        new_source = old_source[:start_byte] + replacement_bytes + old_source[old_end_byte:]
        new_end_byte = start_byte + len(replacement_bytes)

        old_tree = self.tree
        old_tree.edit(
            start_byte=start_byte,
            old_end_byte=old_end_byte,
            new_end_byte=new_end_byte,
            start_point=_point_for_byte(old_source, start_byte),
            old_end_point=_point_for_byte(old_source, old_end_byte),
            new_end_point=_point_for_byte(new_source, new_end_byte),
        )
        new_tree = self.parser.parse(new_source, old_tree=old_tree)
        if new_tree is None:
            raise RuntimeError("Tree-sitter incremental parse returned no tree")

        changed = tuple(_range_snapshot(item) for item in old_tree.changed_ranges(new_tree))
        self.source = new_source
        self.tree = new_tree
        return IncrementalParseResult(
            document=ParseDocument(self.language_id, new_source, new_tree),
            changed_ranges=changed,
        )


def _point_for_byte(source: bytes, offset: int) -> tuple[int, int]:
    prefix = source[:offset]
    row = prefix.count(b"\n")
    last_newline = prefix.rfind(b"\n")
    column = offset if last_newline < 0 else offset - last_newline - 1
    return row, column


def _range_snapshot(value: Any) -> ChangedRangeSnapshot:
    return ChangedRangeSnapshot(
        start_byte=int(value.start_byte),
        end_byte=int(value.end_byte),
        start_point=(int(value.start_point.row), int(value.start_point.column)),
        end_point=(int(value.end_point.row), int(value.end_point.column)),
    )
