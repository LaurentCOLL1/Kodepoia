from __future__ import annotations

import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.kodegodot.document import GodotNode, GodotTextDocumentParser

_PROPERTY = re.compile(r"^[A-Za-z_][A-Za-z0-9_./:-]{0,127}$")
_FORBIDDEN_PROPERTIES = {"script", "owner", "scene_file_path"}


@dataclass(frozen=True, slots=True)
class GodotSceneEditResult:
    path: str
    node: str
    parent: str | None
    property: str
    before_sha256: str
    after_sha256: str
    line: int


class GodotSceneEditor:
    """Guarded editor for an already-existing property on one unique TSCN node."""

    def __init__(self, root: Path, *, max_value_chars: int = 4096) -> None:
        self.root = root.resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.root)
        self.parser = GodotTextDocumentParser(self.root)
        self.max_value_chars = max_value_chars

    def set_existing_property(
        self,
        path: str,
        *,
        node: str,
        property_name: str,
        raw_value: str,
        expected_sha256: str,
        parent: str | None = None,
    ) -> GodotSceneEditResult:
        if not expected_sha256 or len(expected_sha256) != 64:
            raise ValueError("expected_sha256 is required and must be a SHA-256 hex digest")
        if not _PROPERTY.fullmatch(property_name):
            raise ValueError("Invalid Godot property name")
        if property_name in _FORBIDDEN_PROPERTIES:
            raise PermissionError(f"Direct editing of protected property is not allowed: {property_name}")
        if not raw_value or len(raw_value) > self.max_value_chars:
            raise ValueError(f"raw_value must contain 1..{self.max_value_chars} characters")
        if "\n" in raw_value or "\r" in raw_value or "\x00" in raw_value:
            raise ValueError("raw_value must be a single non-NUL line")

        target = self.boundary.resolve(path, must_exist=True)
        if target.suffix.lower() != ".tscn" or not target.is_file():
            raise ValueError("Safe scene property editing requires a .tscn file")

        original_bytes = target.read_bytes()
        before_hash = hashlib.sha256(original_bytes).hexdigest()
        if expected_sha256.lower() != before_hash:
            raise ValueError("Scene edit precondition failed: SHA-256 does not match expected_sha256")

        document = self.parser.parse(path)
        matches = [item for item in document.nodes if item.name == node and (parent is None or item.parent == parent)]
        if len(matches) != 1:
            raise ValueError(f"Scene edit requires exactly one matching node, found {len(matches)}")
        selected = matches[0]
        prop_matches = [item for item in selected.properties if item.name == property_name]
        if len(prop_matches) != 1:
            raise ValueError(f"Property must already exist exactly once on selected node, found {len(prop_matches)}")
        prop = prop_matches[0]

        text = original_bytes.decode("utf-8-sig")
        lines = text.splitlines(keepends=True)
        index = prop.line - 1
        if index < 0 or index >= len(lines):
            raise RuntimeError("Property provenance line is outside scene source")
        original_line = lines[index]
        line_body = original_line.rstrip("\r\n")
        newline = original_line[len(line_body):]
        if "=" not in line_body:
            raise RuntimeError("Property provenance line no longer contains an assignment")
        lhs, _rhs = line_body.split("=", 1)
        if lhs.strip() != property_name:
            raise RuntimeError("Property provenance no longer matches parsed property")
        lines[index] = f"{lhs.rstrip()} = {raw_value}{newline}"
        updated_bytes = "".join(lines).encode("utf-8")
        after_hash = hashlib.sha256(updated_bytes).hexdigest()
        self._atomic_write(target, updated_bytes)
        return GodotSceneEditResult(
            path=self.boundary.relative(target),
            node=selected.name or node,
            parent=selected.parent,
            property=property_name,
            before_sha256=before_hash,
            after_sha256=after_hash,
            line=prop.line,
        )

    @staticmethod
    def _atomic_write(target: Path, content: bytes) -> None:
        temp_path: Path | None = None
        original_mode = target.stat().st_mode
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=".kodepoia-godot-edit-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = Path(handle.name)
            os.chmod(temp_path, original_mode)
            os.replace(temp_path, target)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
