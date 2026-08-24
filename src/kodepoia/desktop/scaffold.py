from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Mapping

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import BackupManager
from kodepoia.core.safe_change import SafeChangeManager


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_NAMESPACE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_TOKEN = re.compile(r"\{\{(identifier|namespace|text|bool):([A-Za-z_][A-Za-z0-9_]*)\}\}")
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


class TemplateValueKind(StrEnum):
    IDENTIFIER = "identifier"
    NAMESPACE = "namespace"
    TEXT = "text"
    BOOL = "bool"


class FileOwnership(StrEnum):
    KODEPOIA = "kodepoia"
    USER = "user"


class PreviewAction(StrEnum):
    CREATE = "create"
    REPLACE = "replace"
    UNCHANGED = "unchanged"
    PRESERVE = "preserve"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class TemplateValue:
    kind: TemplateValueKind
    value: str | bool

    def render(self) -> str:
        if self.kind is TemplateValueKind.BOOL:
            if not isinstance(self.value, bool):
                raise ValueError("bool template values require a bool")
            return "true" if self.value else "false"
        if not isinstance(self.value, str):
            raise ValueError(f"{self.kind.value} template values require a string")
        value = _normalize_newlines(self.value)
        if "\x00" in value or "{{" in value or "}}" in value:
            raise ValueError("template values contain forbidden control/directive syntax")
        if self.kind is TemplateValueKind.IDENTIFIER and not _IDENTIFIER.fullmatch(value):
            raise ValueError(f"unsafe identifier: {value!r}")
        if self.kind is TemplateValueKind.NAMESPACE and not _NAMESPACE.fullmatch(value):
            raise ValueError(f"unsafe namespace: {value!r}")
        if self.kind is TemplateValueKind.TEXT and any(
            ord(ch) < 32 and ch not in "\n\t" for ch in value
        ):
            raise ValueError("text template value contains forbidden control characters")
        return value


@dataclass(frozen=True, slots=True)
class TemplateFile:
    path_template: str
    content_template: str
    ownership: FileOwnership = FileOwnership.KODEPOIA

    def to_dict(self) -> dict[str, str]:
        return {
            "path_template": self.path_template,
            "content_template": _normalize_newlines(self.content_template),
            "ownership": self.ownership.value,
        }


@dataclass(frozen=True, slots=True)
class DesktopTemplateManifest:
    schema_version: int
    template_id: str
    template_version: str
    files: tuple[TemplateFile, ...]

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported desktop template schema version")
        if not _IDENTIFIER.fullmatch(self.template_id):
            raise ValueError("template_id must be a safe identifier")
        if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,2}", self.template_version):
            raise ValueError("template_version must be numeric dotted form")
        if not self.files:
            raise ValueError("desktop template requires at least one file")
        seen: set[str] = set()
        for file in self.files:
            if file.path_template in seen:
                raise ValueError(f"duplicate template path: {file.path_template}")
            seen.add(file.path_template)
            _validate_template_path(file.path_template, allow_tokens=True)
            _validate_tokens(file.path_template)
            _validate_tokens(file.content_template)

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "template_id": self.template_id,
            "template_version": self.template_version,
            "files": [item.to_dict() for item in self.files],
        }

    def digest(self) -> str:
        return _sha256_bytes(_canonical_json(self.to_dict()))

    @classmethod
    def from_dict(cls, raw: object) -> "DesktopTemplateManifest":
        if not isinstance(raw, dict):
            raise ValueError("desktop template manifest must be a JSON object")
        allowed = {"schema_version", "template_id", "template_version", "files"}
        if set(raw) != allowed:
            raise ValueError("desktop template manifest has unknown or missing keys")
        files_raw = raw["files"]
        if not isinstance(files_raw, list):
            raise ValueError("desktop template files must be an array")
        files: list[TemplateFile] = []
        for item in files_raw:
            if not isinstance(item, dict):
                raise ValueError("desktop template file entry must be an object")
            if set(item) != {"path_template", "content_template", "ownership"}:
                raise ValueError("desktop template file entry has invalid keys")
            files.append(
                TemplateFile(
                    path_template=str(item["path_template"]),
                    content_template=str(item["content_template"]),
                    ownership=FileOwnership(str(item["ownership"])),
                )
            )
        manifest = cls(
            schema_version=int(raw["schema_version"]),
            template_id=str(raw["template_id"]),
            template_version=str(raw["template_version"]),
            files=tuple(files),
        )
        manifest.validate()
        return manifest

    @classmethod
    def load(cls, path: Path) -> "DesktopTemplateManifest":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


@dataclass(frozen=True, slots=True)
class ScaffoldLineage:
    dna_sha256: str
    product_sha256: str

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True)
class RenderedFile:
    path: str
    content: str
    sha256: str
    ownership: FileOwnership


@dataclass(frozen=True, slots=True)
class WorkspaceManifest:
    schema_version: int
    template_id: str
    template_version: str
    template_sha256: str
    dna_sha256: str
    product_sha256: str
    files: tuple[RenderedFile, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "template_id": self.template_id,
            "template_version": self.template_version,
            "template_sha256": self.template_sha256,
            "dna_sha256": self.dna_sha256,
            "product_sha256": self.product_sha256,
            "files": [
                {
                    "path": item.path,
                    "sha256": item.sha256,
                    "ownership": item.ownership.value,
                }
                for item in self.files
            ],
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.to_dict())

    def digest(self) -> str:
        return _sha256_bytes(self.canonical_bytes())


@dataclass(frozen=True, slots=True)
class PreviewItem:
    path: str
    action: PreviewAction
    current_sha256: str | None
    desired_sha256: str
    ownership: FileOwnership


@dataclass(frozen=True, slots=True)
class ScaffoldPreview:
    manifest: WorkspaceManifest
    items: tuple[PreviewItem, ...]

    @property
    def has_conflicts(self) -> bool:
        return any(item.action is PreviewAction.CONFLICT for item in self.items)

    @property
    def destructive(self) -> bool:
        return any(item.action is PreviewAction.REPLACE for item in self.items)


def _validate_tokens(value: str) -> None:
    stripped = _TOKEN.sub("", value)
    if "{{" in stripped or "}}" in stripped:
        raise ValueError("unsupported or malformed template directive")


def _validate_template_path(value: str, *, allow_tokens: bool = False) -> str:
    if not value or "\\" in value or "\x00" in value:
        raise ValueError("template path must be a non-empty POSIX relative path")
    check = _TOKEN.sub("X", value) if allow_tokens else value
    path = PurePosixPath(check)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe scaffold path: {value!r}")
    for part in path.parts:
        stem = part.split(".", 1)[0].upper()
        if stem in _WINDOWS_RESERVED or part.endswith((" ", ".")):
            raise ValueError(f"reserved scaffold path component: {part!r}")
        if any(ch in '<>:"|?*' for ch in part):
            raise ValueError(f"forbidden scaffold path character in {part!r}")
    return path.as_posix()


def _render_tokens(template: str, values: Mapping[str, TemplateValue]) -> str:
    def replace(match: re.Match[str]) -> str:
        expected_kind = TemplateValueKind(match.group(1))
        name = match.group(2)
        if name not in values:
            raise ValueError(f"missing template value: {name}")
        value = values[name]
        if value.kind is not expected_kind:
            raise ValueError(
                f"template value {name} requires {expected_kind.value}, got {value.kind.value}"
            )
        return value.render()

    _validate_tokens(template)
    rendered = _TOKEN.sub(replace, template)
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("template rendering left unresolved directives")
    return rendered


class DesktopScaffoldEngine:
    MANIFEST_PATH = ".kodepoia/desktop/workspace-manifest.json"

    def render(
        self,
        template: DesktopTemplateManifest,
        values: Mapping[str, TemplateValue],
        lineage: ScaffoldLineage,
    ) -> tuple[tuple[RenderedFile, ...], WorkspaceManifest]:
        template.validate()
        lineage.validate()
        rendered: list[RenderedFile] = []
        seen: set[str] = set()
        for item in template.files:
            path = _validate_template_path(_render_tokens(item.path_template, values))
            if path == self.MANIFEST_PATH or path in seen:
                raise ValueError(f"scaffold path collision: {path}")
            seen.add(path)
            content = _normalize_newlines(_render_tokens(item.content_template, values))
            encoded = content.encode("utf-8")
            rendered.append(
                RenderedFile(path, content, _sha256_bytes(encoded), item.ownership)
            )
        rendered.sort(key=lambda item: item.path)
        manifest = WorkspaceManifest(
            schema_version=1,
            template_id=template.template_id,
            template_version=template.template_version,
            template_sha256=template.digest(),
            dna_sha256=lineage.dna_sha256,
            product_sha256=lineage.product_sha256,
            files=tuple(rendered),
        )
        return tuple(rendered), manifest

    def preview(
        self,
        project_root: Path,
        template: DesktopTemplateManifest,
        values: Mapping[str, TemplateValue],
        lineage: ScaffoldLineage,
    ) -> ScaffoldPreview:
        root = project_root.resolve(strict=False)
        rendered, manifest = self.render(template, values, lineage)
        previous = self._previous_files(root)
        items: list[PreviewItem] = []
        for desired in rendered:
            target = self._inside(root, desired.path)
            if not target.exists():
                action = PreviewAction.CREATE
                current = None
            elif not target.is_file():
                action = PreviewAction.CONFLICT
                current = None
            else:
                current = _sha256_bytes(target.read_bytes())
                prior = previous.get(desired.path)
                if current == desired.sha256:
                    action = PreviewAction.UNCHANGED
                elif desired.ownership is FileOwnership.USER:
                    action = PreviewAction.PRESERVE
                elif (
                    prior is not None
                    and prior[0] is FileOwnership.KODEPOIA
                    and current == prior[1]
                ):
                    action = PreviewAction.REPLACE
                else:
                    action = PreviewAction.CONFLICT
            items.append(
                PreviewItem(desired.path, action, current, desired.sha256, desired.ownership)
            )
        return ScaffoldPreview(manifest, tuple(items))

    def apply(
        self,
        project_root: Path,
        preview: ScaffoldPreview,
        *,
        safe_change: SafeChangeManager | None = None,
        backup_manager: BackupManager | None = None,
        audit_log: AuditLog | None = None,
        actor: str = "kodepoia",
    ) -> WorkspaceManifest:
        root = project_root.resolve(strict=False)
        root.mkdir(parents=True, exist_ok=True)
        if preview.has_conflicts:
            raise FileExistsError("refusing scaffold apply with ownership/path conflicts")
        by_path = {item.path: item for item in preview.manifest.files}
        replace_paths = [
            self._inside(root, item.path)
            for item in preview.items
            if item.action is PreviewAction.REPLACE
        ]
        safe_snapshot: Path | None = None
        backup_path: Path | None = None
        if replace_paths:
            if safe_change is None or backup_manager is None:
                raise ValueError(
                    "destructive scaffold regeneration requires SafeChangeManager and BackupManager"
                )
            safe_snapshot = safe_change.snapshot(replace_paths)
            backup_path = backup_manager.create_archive(root, label="desktop-scaffold")
        for item in preview.items:
            if item.action in {PreviewAction.UNCHANGED, PreviewAction.PRESERVE}:
                continue
            desired = by_path[item.path]
            target = self._inside(root, item.path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(desired.content, encoding="utf-8", newline="\n")
        manifest_path = self._inside(root, self.MANIFEST_PATH)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(preview.manifest.canonical_bytes() + b"\n")
        if audit_log is not None:
            audit_log.append(
                "desktop.scaffold",
                "apply",
                actor,
                "success",
                {
                    "workspace_manifest_sha256": preview.manifest.digest(),
                    "template_sha256": preview.manifest.template_sha256,
                    "safe_snapshot": str(safe_snapshot) if safe_snapshot else None,
                    "backup": str(backup_path) if backup_path else None,
                    "actions": {
                        item.path: item.action.value for item in preview.items
                    },
                },
            )
        return preview.manifest

    def _previous_files(
        self, root: Path
    ) -> dict[str, tuple[FileOwnership, str]]:
        path = self._inside(root, self.MANIFEST_PATH)
        if not path.is_file():
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if raw.get("schema_version") != 1 or not isinstance(raw.get("files"), list):
                return {}
            result: dict[str, tuple[FileOwnership, str]] = {}
            for item in raw["files"]:
                relative = _validate_template_path(str(item["path"]))
                digest = str(item["sha256"])
                if not re.fullmatch(r"[0-9a-f]{64}", digest):
                    return {}
                result[relative] = (FileOwnership(item["ownership"]), digest)
            return result
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _inside(root: Path, relative: str) -> Path:
        relative = _validate_template_path(relative)
        target = (root / PurePosixPath(relative)).resolve(strict=False)
        if target != root and root not in target.parents:
            raise ValueError(f"scaffold path escapes project root: {relative}")
        return target
