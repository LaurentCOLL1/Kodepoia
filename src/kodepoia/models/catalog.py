from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$")


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable model identifier")
    return value


def _sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be lowercase SHA-256 hex")
    return value


def _safe_relative(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"{field} must be a non-empty POSIX-style relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{field} must stay inside the Kodepoia models root")
    return path.as_posix()


@dataclass(frozen=True, slots=True)
class ModelFileIdentity:
    role: str
    path: str
    sha256: str
    max_bytes: int | None = None

    def __post_init__(self) -> None:
        _stable_id(self.role, field="role")
        object.__setattr__(self, "path", _safe_relative(self.path, field="path"))
        _sha256(self.sha256, field="sha256")
        if self.max_bytes is not None and (isinstance(self.max_bytes, bool) or not isinstance(self.max_bytes, int) or self.max_bytes <= 0):
            raise ValueError("max_bytes must be a positive integer when provided")

    def canonical(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "path": self.path,
            "sha256": self.sha256,
            "max_bytes": self.max_bytes,
        }


@dataclass(frozen=True, slots=True)
class LocalModelManifest:
    model_id: str
    purpose: str
    backend: str
    license_id: str
    provenance_id: str
    allowed_uses: tuple[str, ...]
    files: tuple[ModelFileIdentity, ...]
    locale: str | None = None
    role: str | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        _stable_id(self.model_id, field="model_id")
        _stable_id(self.purpose, field="purpose")
        _stable_id(self.backend, field="backend")
        _stable_id(self.license_id, field="license_id")
        _stable_id(self.provenance_id, field="provenance_id")
        if not self.allowed_uses or any(not isinstance(item, str) or not item for item in self.allowed_uses):
            raise ValueError("allowed_uses must contain at least one non-empty use")
        if not self.files:
            raise ValueError("model manifest must declare at least one payload file")
        roles = [item.role for item in self.files]
        if len(roles) != len(set(roles)):
            raise ValueError("model file roles must be unique")
        if self.role is not None:
            _stable_id(self.role, field="model role")
        if self.source is not None and not isinstance(self.source, str):
            raise ValueError("source must be text when provided")

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "LocalModelManifest":
        if document.get("schema_version") != 1:
            raise ValueError("unsupported local model manifest schema_version")
        files_raw = document.get("files")
        if not isinstance(files_raw, list):
            raise ValueError("files must be a list")
        files = tuple(
            ModelFileIdentity(
                role=item["role"],
                path=item["path"],
                sha256=item["sha256"],
                max_bytes=item.get("max_bytes"),
            )
            for item in files_raw
            if isinstance(item, dict)
        )
        if len(files) != len(files_raw):
            raise ValueError("every model file entry must be an object")
        allowed = document.get("allowed_uses")
        if not isinstance(allowed, list):
            raise ValueError("allowed_uses must be a list")
        return cls(
            model_id=document["model_id"],
            purpose=document["purpose"],
            backend=document["backend"],
            license_id=document["license_id"],
            provenance_id=document["provenance_id"],
            allowed_uses=tuple(allowed),
            files=files,
            locale=document.get("locale"),
            role=document.get("role"),
            source=document.get("source"),
        )

    def file(self, role: str) -> ModelFileIdentity:
        for item in self.files:
            if item.role == role:
                return item
        raise KeyError(role)

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "model_id": self.model_id,
            "purpose": self.purpose,
            "backend": self.backend,
            "license_id": self.license_id,
            "provenance_id": self.provenance_id,
            "allowed_uses": list(self.allowed_uses),
            "locale": self.locale,
            "role": self.role,
            "source": self.source,
            "files": [item.canonical() for item in self.files],
        }


class KodeModelRegistry:
    """Repository-local model catalog. Payload bytes stay local and are SHA-bound by tracked manifests."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = Path(repo_root).resolve(strict=True)
        self.models_root = (self.repo_root / "models").resolve(strict=False)
        if self.repo_root not in self.models_root.parents:
            raise ValueError("models root must remain inside the repository")
        self.index_path = self.models_root / "registry" / "models.json"

    def _resolve_models_relative(self, relative: str, *, must_exist: bool = False) -> Path:
        safe = _safe_relative(relative, field="model path")
        candidate = (self.models_root / Path(*PurePosixPath(safe).parts)).resolve(strict=False)
        if candidate != self.models_root and self.models_root not in candidate.parents:
            raise ValueError("model path escapes Kodepoia models root")
        if must_exist and not candidate.exists():
            raise FileNotFoundError(candidate)
        return candidate

    def _index(self) -> dict[str, str]:
        document = json.loads(self.index_path.read_text(encoding="utf-8"))
        if document.get("schema_version") != 1:
            raise ValueError("unsupported KodeModelRegistry index schema_version")
        entries = document.get("entries")
        if not isinstance(entries, list):
            raise ValueError("model registry entries must be a list")
        result: dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("model registry entry must be an object")
            model_id = _stable_id(entry.get("model_id"), field="model_id")
            manifest = _safe_relative(entry.get("manifest"), field="manifest")
            if model_id in result:
                raise ValueError(f"duplicate model id: {model_id}")
            result[model_id] = manifest
        return result

    def model_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._index()))

    def manifest_path(self, model_id: str) -> Path:
        _stable_id(model_id, field="model_id")
        entries = self._index()
        try:
            relative = entries[model_id]
        except KeyError as exc:
            raise KeyError(f"unregistered model: {model_id}") from exc
        return self._resolve_models_relative(relative, must_exist=True)

    def manifest(self, model_id: str) -> LocalModelManifest:
        path = self.manifest_path(model_id)
        document = json.loads(path.read_text(encoding="utf-8"))
        manifest = LocalModelManifest.from_document(document)
        if manifest.model_id != model_id:
            raise ValueError("registry model_id does not match manifest model_id")
        return manifest

    def resolve_file(self, model_id: str, role: str, *, verify: bool = True) -> Path:
        manifest_path = self.manifest_path(model_id)
        manifest = self.manifest(model_id)
        identity = manifest.file(role)
        candidate = (manifest_path.parent / Path(*PurePosixPath(identity.path).parts)).resolve(strict=False)
        if candidate != self.models_root and self.models_root not in candidate.parents:
            raise ValueError("model payload escapes Kodepoia models root")
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        if identity.max_bytes is not None and candidate.stat().st_size > identity.max_bytes:
            raise ValueError(f"model payload exceeds byte budget: {role}")
        if verify:
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if digest != identity.sha256:
                raise ValueError(f"model payload SHA-256 mismatch: {role}")
        return candidate
