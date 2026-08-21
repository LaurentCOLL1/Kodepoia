from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from kodepoia.kodecode.workspace import WorkspaceBoundary

_HEADER_RE = re.compile(r"^\[(?P<kind>[A-Za-z0-9_]+)(?P<body>.*)\]$")
_ATTR_RE = re.compile(r'(?P<key>[A-Za-z0-9_./:-]+)=(?P<value>"(?:\\.|[^"\\])*"|[^\s]+)')


def _decode_header_value(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        body = value[1:-1]
        return bytes(body, "utf-8").decode("unicode_escape")
    return value


@dataclass(frozen=True, slots=True)
class GodotProperty:
    name: str
    raw_value: str
    line: int


@dataclass(frozen=True, slots=True)
class GodotSection:
    kind: str
    attributes: dict[str, str]
    properties: tuple[GodotProperty, ...]
    line: int


@dataclass(frozen=True, slots=True)
class GodotExternalResource:
    resource_type: str | None
    resource_id: str | None
    uid: str | None
    path: str | None
    line: int


@dataclass(frozen=True, slots=True)
class GodotSubResource:
    resource_type: str | None
    resource_id: str | None
    properties: tuple[GodotProperty, ...]
    line: int


@dataclass(frozen=True, slots=True)
class GodotNode:
    name: str | None
    node_type: str | None
    parent: str | None
    instance: str | None
    owner: str | None
    unique_name_in_owner: str | None
    properties: tuple[GodotProperty, ...]
    line: int


@dataclass(frozen=True, slots=True)
class GodotConnection:
    signal: str | None
    source: str | None
    target: str | None
    method: str | None
    flags: str | None
    line: int


@dataclass(frozen=True, slots=True)
class GodotTextDocument:
    path: str
    document_type: str
    format: int | None
    uid: str | None
    load_steps: int | None
    script_class: str | None
    external_resources: tuple[GodotExternalResource, ...] = ()
    sub_resources: tuple[GodotSubResource, ...] = ()
    nodes: tuple[GodotNode, ...] = ()
    connections: tuple[GodotConnection, ...] = ()
    sections: tuple[GodotSection, ...] = ()
    dependencies: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GodotTextDocumentParser:
    """Parse Godot 4 text scene/resource structure without evaluating Variant values."""

    def __init__(self, root: Path, *, max_bytes: int = 4 * 1024 * 1024) -> None:
        self.root = root.resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.root)
        self.max_bytes = max_bytes

    def parse(self, path: str) -> GodotTextDocument:
        resolved = self.boundary.resolve(path, must_exist=True)
        if resolved.suffix.lower() not in {".tscn", ".tres"}:
            raise ValueError("Godot text document must be .tscn or .tres")
        size = resolved.stat().st_size
        if size > self.max_bytes:
            raise ValueError(f"Godot text document exceeds {self.max_bytes} bytes")
        text = resolved.read_text(encoding="utf-8-sig")
        return self.parse_text(text, path=resolved.relative_to(self.root).as_posix())

    def parse_text(self, text: str, *, path: str = "<memory>") -> GodotTextDocument:
        sections: list[GodotSection] = []
        current_kind: str | None = None
        current_attrs: dict[str, str] = {}
        current_line = 0
        current_props: list[GodotProperty] = []

        def flush() -> None:
            nonlocal current_kind, current_attrs, current_line, current_props
            if current_kind is not None:
                sections.append(
                    GodotSection(
                        kind=current_kind,
                        attributes=dict(current_attrs),
                        properties=tuple(current_props),
                        line=current_line,
                    )
                )
            current_kind = None
            current_attrs = {}
            current_line = 0
            current_props = []

        for line_no, source_line in enumerate(text.splitlines(), start=1):
            stripped = source_line.strip()
            if not stripped or stripped.startswith(";"):
                continue
            header = _HEADER_RE.match(stripped)
            if header:
                flush()
                current_kind = header.group("kind")
                current_line = line_no
                current_attrs = {
                    match.group("key"): _decode_header_value(match.group("value"))
                    for match in _ATTR_RE.finditer(header.group("body"))
                }
                continue
            if current_kind is None:
                raise ValueError(f"Property before Godot document header at line {line_no}")
            if "=" in stripped:
                name, raw_value = stripped.split("=", 1)
                current_props.append(GodotProperty(name.strip(), raw_value.strip(), line_no))
        flush()

        if not sections or sections[0].kind not in {"gd_scene", "gd_resource"}:
            raise ValueError("Godot text document must start with [gd_scene] or [gd_resource]")
        descriptor = sections[0]
        fmt = self._as_int(descriptor.attributes.get("format"))
        if fmt is not None and fmt != 3:
            raise ValueError(f"Unsupported Godot text format: {fmt}; expected format=3")

        ext_resources: list[GodotExternalResource] = []
        sub_resources: list[GodotSubResource] = []
        nodes: list[GodotNode] = []
        connections: list[GodotConnection] = []
        dependencies: list[str] = []

        for section in sections[1:]:
            attrs = section.attributes
            if section.kind == "ext_resource":
                item = GodotExternalResource(
                    resource_type=attrs.get("type"),
                    resource_id=attrs.get("id"),
                    uid=attrs.get("uid"),
                    path=attrs.get("path"),
                    line=section.line,
                )
                ext_resources.append(item)
                if item.path:
                    dependencies.append(item.path)
            elif section.kind == "sub_resource":
                sub_resources.append(
                    GodotSubResource(attrs.get("type"), attrs.get("id"), section.properties, section.line)
                )
            elif section.kind == "node":
                nodes.append(
                    GodotNode(
                        name=attrs.get("name"),
                        node_type=attrs.get("type"),
                        parent=attrs.get("parent"),
                        instance=attrs.get("instance"),
                        owner=attrs.get("owner"),
                        unique_name_in_owner=attrs.get("unique_name_in_owner"),
                        properties=section.properties,
                        line=section.line,
                    )
                )
            elif section.kind == "connection":
                connections.append(
                    GodotConnection(
                        signal=attrs.get("signal"),
                        source=attrs.get("from"),
                        target=attrs.get("to"),
                        method=attrs.get("method"),
                        flags=attrs.get("flags"),
                        line=section.line,
                    )
                )

        return GodotTextDocument(
            path=path,
            document_type="scene" if descriptor.kind == "gd_scene" else "resource",
            format=fmt,
            uid=descriptor.attributes.get("uid"),
            load_steps=self._as_int(descriptor.attributes.get("load_steps")),
            script_class=descriptor.attributes.get("script_class"),
            external_resources=tuple(ext_resources),
            sub_resources=tuple(sub_resources),
            nodes=tuple(nodes),
            connections=tuple(connections),
            sections=tuple(sections),
            dependencies=tuple(dict.fromkeys(dependencies)),
        )

    @staticmethod
    def _as_int(value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None
