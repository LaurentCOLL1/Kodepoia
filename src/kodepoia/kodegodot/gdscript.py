from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from kodepoia.kodecode.workspace import WorkspaceBoundary

_CLASS = re.compile(r"^\s*class_name\s+([A-Za-z_][A-Za-z0-9_]*)")
_EXTENDS = re.compile(r"^\s*extends\s+(.+?)\s*$")
_SIGNAL = re.compile(r"^\s*signal\s+([A-Za-z_][A-Za-z0-9_]*)")
_FUNC = re.compile(r"^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*(?:->\s*([^:]+))?\s*:")
_VAR = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*(var|const)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*([^=]+?))?\s*(?::=|=|$)")


@dataclass(frozen=True, slots=True)
class GDScriptFunction:
    name: str
    parameters: str
    return_type: str | None
    line: int


@dataclass(frozen=True, slots=True)
class GDScriptVariable:
    kind: str
    name: str
    declared_type: str | None
    line: int


@dataclass(frozen=True, slots=True)
class GDScriptInfo:
    path: str
    class_name: str | None
    extends: str | None
    signals: tuple[str, ...]
    functions: tuple[GDScriptFunction, ...]
    variables: tuple[GDScriptVariable, ...]
    typed_function_ratio: float
    typed_variable_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GDScriptInspector:
    """Non-executing structural inspector; Godot/LSP remains diagnostic authority."""

    def __init__(self, root: Path, *, max_bytes: int = 2 * 1024 * 1024) -> None:
        self.root = root.resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.root)
        self.max_bytes = max_bytes

    def inspect(self, path: str) -> GDScriptInfo:
        target = self.boundary.resolve(path, must_exist=True)
        if target.suffix.lower() != ".gd" or not target.is_file():
            raise ValueError("GDScript .gd file required")
        if target.stat().st_size > self.max_bytes:
            raise ValueError(f"GDScript exceeds {self.max_bytes} bytes")
        return self.inspect_text(target.read_text(encoding="utf-8-sig"), path=self.boundary.relative(target))

    def inspect_text(self, text: str, *, path: str = "<memory>") -> GDScriptInfo:
        class_name: str | None = None
        extends: str | None = None
        signals: list[str] = []
        functions: list[GDScriptFunction] = []
        variables: list[GDScriptVariable] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            if class_name is None and (match := _CLASS.match(line)):
                class_name = match.group(1)
            if extends is None and (match := _EXTENDS.match(line)):
                extends = match.group(1).strip()
            if match := _SIGNAL.match(line):
                signals.append(match.group(1))
            if match := _FUNC.match(line):
                functions.append(
                    GDScriptFunction(
                        match.group(1),
                        match.group(2).strip(),
                        match.group(3).strip() if match.group(3) else None,
                        line_no,
                    )
                )
            if match := _VAR.match(line):
                variables.append(
                    GDScriptVariable(
                        match.group(1),
                        match.group(2),
                        match.group(3).strip() if match.group(3) else None,
                        line_no,
                    )
                )
        typed_functions = sum(item.return_type is not None for item in functions)
        typed_variables = sum(item.declared_type is not None for item in variables)
        return GDScriptInfo(
            path=path,
            class_name=class_name,
            extends=extends,
            signals=tuple(signals),
            functions=tuple(functions),
            variables=tuple(variables),
            typed_function_ratio=typed_functions / len(functions) if functions else 1.0,
            typed_variable_ratio=typed_variables / len(variables) if variables else 1.0,
        )
