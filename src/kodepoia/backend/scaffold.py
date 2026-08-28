from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from kodepoia.core.secrets import KodeSecrets

from .contracts import canonical_json_bytes, canonical_sha256
from .local_config import BackendLocalConfig


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _inside(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("backend scaffold path must be safe and relative")
    target = (root / path).resolve(strict=False)
    if target != root and root not in target.parents:
        raise ValueError("backend scaffold path escapes workspace root")
    return target


@dataclass(frozen=True, slots=True)
class BackendRenderedFile:
    path: str
    sha256: str

    def canonical(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class BackendWorkspaceManifest:
    project_id: str
    config_sha256: str
    template_sha256: str
    files: tuple[BackendRenderedFile, ...]
    schema_version: int = 1
    template_id: str = "kodepoia_local_backend"
    template_version: str = "1.0"

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "template_id": self.template_id,
            "template_version": self.template_version,
            "project_id": self.project_id,
            "config_sha256": self.config_sha256,
            "template_sha256": self.template_sha256,
            "files": [item.canonical() for item in self.files],
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.canonical())

    def digest(self) -> str:
        return canonical_sha256(self.canonical())

    @classmethod
    def from_dict(cls, raw: object) -> "BackendWorkspaceManifest":
        if not isinstance(raw, dict):
            raise ValueError("backend workspace manifest must be an object")
        expected = {
            "schema_version",
            "template_id",
            "template_version",
            "project_id",
            "config_sha256",
            "template_sha256",
            "files",
        }
        if set(raw) != expected:
            raise ValueError("backend workspace manifest has unknown or missing keys")
        files_raw = raw["files"]
        if not isinstance(files_raw, list):
            raise ValueError("backend workspace files must be an array")
        files: list[BackendRenderedFile] = []
        for item in files_raw:
            if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
                raise ValueError("backend workspace file entry has invalid keys")
            files.append(BackendRenderedFile(path=str(item["path"]), sha256=str(item["sha256"])))
        manifest = cls(
            schema_version=int(raw["schema_version"]),
            template_id=str(raw["template_id"]),
            template_version=str(raw["template_version"]),
            project_id=str(raw["project_id"]),
            config_sha256=str(raw["config_sha256"]),
            template_sha256=str(raw["template_sha256"]),
            files=tuple(files),
        )
        if manifest.schema_version != 1 or manifest.template_id != "kodepoia_local_backend":
            raise ValueError("unsupported backend workspace manifest identity")
        for digest in (manifest.config_sha256, manifest.template_sha256, *(item.sha256 for item in manifest.files)):
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise ValueError("backend workspace manifest digests must be lowercase SHA-256")
        if tuple(sorted(manifest.files, key=lambda item: item.path)) != manifest.files:
            raise ValueError("backend workspace files must be sorted")
        return manifest


class BackendScaffoldEngine:
    RUNTIME_CONFIG_PATH = ".kodepoia/backend/runtime.json"
    MANIFEST_PATH = ".kodepoia/backend/workspace-manifest.json"
    README_PATH = "backend/README.md"
    TEMPLATE_DESCRIPTOR = {
        "template_id": "kodepoia_local_backend",
        "template_version": "1.0",
        "paths": [RUNTIME_CONFIG_PATH, README_PATH],
        "runtime_owner": "kodepoia.backend.local_fixture_server",
    }

    def render(self, config: BackendLocalConfig) -> tuple[dict[str, bytes], BackendWorkspaceManifest]:
        if not isinstance(config, BackendLocalConfig):
            raise ValueError("backend scaffold requires BackendLocalConfig")
        config_bytes = canonical_json_bytes(config.canonical()) + b"\n"
        services = ", ".join(item.value for item in config.services)
        readme = (
            "# Kodepoia local backend workspace\n\n"
            f"Project: `{config.project_id}`\n\n"
            f"Environment: `{config.environment.kind.value}`\n\n"
            f"Service intents: `{services}`\n\n"
            "This workspace is generated for local/test development only. "
            "The executable runtime remains repository-owned by Kodepoia; no provider, "
            "deployment script, credential or production endpoint is generated here.\n"
        ).encode("utf-8")
        rendered = {
            self.RUNTIME_CONFIG_PATH: config_bytes,
            self.README_PATH: readme,
        }
        files = tuple(
            BackendRenderedFile(path=path, sha256=_sha256_bytes(content))
            for path, content in sorted(rendered.items())
        )
        manifest = BackendWorkspaceManifest(
            project_id=config.project_id,
            config_sha256=config.digest(),
            template_sha256=canonical_sha256(self.TEMPLATE_DESCRIPTOR),
            files=files,
        )
        return rendered, manifest

    def generate(
        self,
        project_root: Path,
        config: BackendLocalConfig,
        *,
        secrets: KodeSecrets | None = None,
    ) -> BackendWorkspaceManifest:
        root = project_root.resolve(strict=False)
        root.mkdir(parents=True, exist_ok=True)
        if secrets is not None:
            config.assert_secret_boundary(secrets)
        rendered, manifest = self.render(config)
        rendered_with_manifest = dict(rendered)
        rendered_with_manifest[self.MANIFEST_PATH] = manifest.canonical_bytes() + b"\n"
        for relative, content in sorted(rendered_with_manifest.items()):
            target = _inside(root, relative)
            if target.exists():
                if not target.is_file() or target.read_bytes() != content:
                    raise FileExistsError(
                        f"backend scaffold refuses to overwrite divergent file: {relative}"
                    )
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return manifest

    def load_config(self, project_root: Path) -> BackendLocalConfig:
        root = project_root.resolve(strict=False)
        path = _inside(root, self.RUNTIME_CONFIG_PATH)
        return BackendLocalConfig.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_manifest(self, project_root: Path) -> BackendWorkspaceManifest:
        root = project_root.resolve(strict=False)
        path = _inside(root, self.MANIFEST_PATH)
        return BackendWorkspaceManifest.from_dict(json.loads(path.read_text(encoding="utf-8")))
