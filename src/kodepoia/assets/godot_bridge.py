from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, Sequence

from kodepoia.assets.contracts import ProjectAssetReference
from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation

_IMPORTABLE_EXTENSIONS = {
    ".bmp",
    ".fbx",
    ".flac",
    ".glb",
    ".gltf",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".obj",
    ".ogg",
    ".otf",
    ".png",
    ".svg",
    ".tga",
    ".ttf",
    ".wav",
    ".webp",
    ".woff",
    ".woff2",
}
_GODOT_NATIVE_EXTENSIONS = {".gd", ".res", ".scn", ".tres", ".tscn"}
_GENERATED_ROOTS = {".godot", ".import"}


class GodotAssetClassification(StrEnum):
    SOURCE = "source"
    IMPORT_METADATA = "import_metadata"
    GENERATED_CACHE = "generated_cache"
    GODOT_NATIVE = "godot_native"
    PROJECT_CONFIG = "project_config"
    OTHER = "other"


class GodotRebuildState(StrEnum):
    READY = "ready"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class GodotImportSettingsEvidence:
    path: str
    sha256: str
    content_length: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "content_length": self.content_length,
        }


@dataclass(frozen=True, slots=True)
class GodotSourceEvidence:
    path: str
    sha256: str
    content_length: int
    asset_id: str | None = None
    revision_id: str | None = None
    import_settings: GodotImportSettingsEvidence | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "content_length": self.content_length,
            "asset_id": self.asset_id,
            "revision_id": self.revision_id,
            "import_settings": self.import_settings.to_dict() if self.import_settings is not None else None,
        }


@dataclass(frozen=True, slots=True)
class GodotPortabilityIssue:
    code: str
    path: str | None
    detail: str

    def to_dict(self) -> dict[str, str | None]:
        return {"code": self.code, "path": self.path, "detail": self.detail}


@dataclass(frozen=True, slots=True)
class GodotRebuildReport:
    state: GodotRebuildState
    engine_version: str | None
    project_sha256: str
    project_length: int
    sources: tuple[GodotSourceEvidence, ...]
    references: tuple[dict[str, str | None], ...]
    issues: tuple[GodotPortabilityIssue, ...]
    purged_cache_roots: tuple[str, ...]
    generated_cache_files: int
    import_returncode: int | None
    manifest_digest: str | None

    def manifest_payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "engine_version": self.engine_version,
            "project": {
                "path": "project.godot",
                "sha256": self.project_sha256,
                "content_length": self.project_length,
            },
            "sources": [item.to_dict() for item in self.sources],
            "references": [dict(item) for item in self.references],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "engine_version": self.engine_version,
            "project_sha256": self.project_sha256,
            "project_length": self.project_length,
            "sources": [item.to_dict() for item in self.sources],
            "references": [dict(item) for item in self.references],
            "issues": [item.to_dict() for item in self.issues],
            "purged_cache_roots": list(self.purged_cache_roots),
            "generated_cache_files": self.generated_cache_files,
            "import_returncode": self.import_returncode,
            "manifest_digest": self.manifest_digest,
        }


class GodotImportExecutor(Protocol):
    def invoke(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        actor: str = "brain",
        confirmed: bool = False,
    ) -> Any: ...


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _file_identity(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


class GodotAssetBridge:
    """R8 source/import bridge over the accepted structured R5 Godot executor."""

    def __init__(self, root: Path, executor: GodotImportExecutor) -> None:
        self.boundary = WorkspaceBoundary(root)
        self.executor = executor

    def classify(self, path: str) -> GodotAssetClassification:
        if not path or "\x00" in path:
            raise ValueError("Godot asset path must be a non-empty relative path")
        raw = Path(path)
        if raw.is_absolute():
            raise WorkspaceViolation(f"Absolute paths are not allowed: {raw}")
        normalized = raw.as_posix()
        first = normalized.split("/", 1)[0]
        if first in _GENERATED_ROOTS:
            return GodotAssetClassification.GENERATED_CACHE
        if normalized == "project.godot":
            return GodotAssetClassification.PROJECT_CONFIG
        if normalized.endswith(".import"):
            return GodotAssetClassification.IMPORT_METADATA
        if raw.suffix.lower() in _GODOT_NATIVE_EXTENSIONS:
            return GodotAssetClassification.GODOT_NATIVE
        if raw.suffix.lower() in _IMPORTABLE_EXTENSIONS:
            return GodotAssetClassification.SOURCE
        return GodotAssetClassification.OTHER

    def capture_source(
        self,
        path: str,
        *,
        reference: ProjectAssetReference | None = None,
    ) -> GodotSourceEvidence:
        classification = self.classify(path)
        if classification in {
            GodotAssetClassification.GENERATED_CACHE,
            GodotAssetClassification.IMPORT_METADATA,
        }:
            raise ValueError(f"Transient/import metadata cannot be captured as source: {path}")
        target = self.boundary.resolve(path, must_exist=True)
        if not target.is_file():
            raise ValueError(f"Godot source must be a regular file: {path}")
        relative = self.boundary.relative(target)
        if reference is not None and reference.target_path != relative:
            raise ValueError("ProjectAssetReference target_path does not match source path")
        sha256, content_length = _file_identity(target)
        sidecar_path = self.boundary.resolve(f"{relative}.import")
        settings: GodotImportSettingsEvidence | None = None
        if sidecar_path.is_file():
            settings_sha, settings_length = _file_identity(sidecar_path)
            settings = GodotImportSettingsEvidence(
                path=f"{relative}.import",
                sha256=settings_sha,
                content_length=settings_length,
            )
        return GodotSourceEvidence(
            path=relative,
            sha256=sha256,
            content_length=content_length,
            asset_id=str(reference.asset_id) if reference is not None else None,
            revision_id=str(reference.revision_id) if reference is not None else None,
            import_settings=settings,
        )

    def portability_diagnostics(
        self,
        references: Sequence[ProjectAssetReference],
    ) -> tuple[GodotPortabilityIssue, ...]:
        issues: list[GodotPortabilityIssue] = []
        for reference in references:
            target = reference.target_path
            if target is None:
                issues.append(
                    GodotPortabilityIssue(
                        "MISSING_TARGET_PATH",
                        None,
                        "Vault project reference has no materialized Godot target path.",
                    )
                )
                continue
            try:
                classification = self.classify(target)
                resolved = self.boundary.resolve(target)
            except (ValueError, WorkspaceViolation):
                issues.append(
                    GodotPortabilityIssue(
                        "INVALID_TARGET_PATH",
                        target,
                        "Vault project reference target is not workspace-confined.",
                    )
                )
                continue
            if classification is GodotAssetClassification.GENERATED_CACHE:
                issues.append(
                    GodotPortabilityIssue(
                        "GENERATED_CACHE_REFERENCE",
                        target,
                        "Transient Godot cache must not be a Vault source reference.",
                    )
                )
            elif not resolved.is_file():
                issues.append(
                    GodotPortabilityIssue(
                        "MISSING_MATERIALIZED_SOURCE",
                        target,
                        "Referenced Vault source is not materialized in the Godot project.",
                    )
                )
        return tuple(sorted(issues, key=lambda item: (item.code, item.path or "")))

    def purge_generated_cache(self) -> tuple[str, ...]:
        purged: list[str] = []
        for name in sorted(_GENERATED_ROOTS):
            lexical = self.boundary.root / name
            if lexical.is_symlink():
                raise PermissionError(f"Refusing to follow generated-cache symlink: {name}")
            if not lexical.exists():
                continue
            target = self.boundary.resolve(name, must_exist=True)
            if not target.is_dir():
                raise RuntimeError(f"Generated-cache root is not a directory: {name}")
            shutil.rmtree(target)
            purged.append(name)
        return tuple(purged)

    def rebuild(
        self,
        source_paths: Sequence[str],
        *,
        references: Sequence[ProjectAssetReference] = (),
        timeout: float = 300.0,
    ) -> GodotRebuildReport:
        if not 1.0 <= float(timeout) <= 900.0:
            raise ValueError("Godot rebuild timeout must be between 1 and 900 seconds")
        if not source_paths:
            raise ValueError("At least one Godot source path is required")

        project = self.boundary.resolve("project.godot", must_exist=True)
        if not project.is_file():
            raise FileNotFoundError("project.godot is not a file")
        project_sha, project_length = _file_identity(project)
        reference_by_path = self._reference_map(references)
        before = tuple(
            self.capture_source(path, reference=reference_by_path.get(self._normalize_path(path)))
            for path in source_paths
        )
        portability = self.portability_diagnostics(references)
        if portability:
            return self._report(
                state=GodotRebuildState.FAILED,
                engine_version=None,
                project_identity=(project_sha, project_length),
                sources=before,
                references=references,
                issues=portability,
            )

        try:
            version = self._invoke_result("kodegodot_engine_version")
        except (FileNotFoundError, OSError, RuntimeError) as exc:
            return self._report(
                state=GodotRebuildState.UNAVAILABLE,
                engine_version=None,
                project_identity=(project_sha, project_length),
                sources=before,
                references=references,
                issues=(
                    GodotPortabilityIssue(
                        "GODOT_UNAVAILABLE",
                        None,
                        f"Godot 4.7 capability unavailable: {type(exc).__name__}.",
                    ),
                ),
            )
        raw_version = str(version.get("raw", ""))
        if not bool(version.get("compatible_47")):
            return self._report(
                state=GodotRebuildState.UNAVAILABLE,
                engine_version=raw_version or None,
                project_identity=(project_sha, project_length),
                sources=before,
                references=references,
                issues=(
                    GodotPortabilityIssue(
                        "GODOT_INCOMPATIBLE",
                        None,
                        "Configured engine is not Godot 4.7.x.",
                    ),
                ),
            )

        purged = self.purge_generated_cache()
        try:
            invocation = self._invoke_result(
                "kodegodot_import_project",
                {"timeout": float(timeout)},
            )
        except Exception as exc:
            return self._report(
                state=GodotRebuildState.FAILED,
                engine_version=raw_version,
                project_identity=(project_sha, project_length),
                sources=before,
                references=references,
                issues=(
                    GodotPortabilityIssue(
                        "IMPORT_EXCEPTION",
                        None,
                        f"Structured Godot import failed: {type(exc).__name__}.",
                    ),
                ),
                purged=purged,
            )

        returncode = int(invocation.get("returncode", -1))
        if returncode != 0 or bool(invocation.get("timed_out")) or bool(invocation.get("cancelled")):
            return self._report(
                state=GodotRebuildState.FAILED,
                engine_version=raw_version,
                project_identity=(project_sha, project_length),
                sources=before,
                references=references,
                issues=(
                    GodotPortabilityIssue(
                        "IMPORT_FAILED",
                        None,
                        "Headless Godot import did not complete successfully.",
                    ),
                ),
                purged=purged,
                import_returncode=returncode,
            )

        after_project = _file_identity(project)
        issues: list[GodotPortabilityIssue] = []
        if after_project != (project_sha, project_length):
            issues.append(
                GodotPortabilityIssue(
                    "PROJECT_MUTATED",
                    "project.godot",
                    "Godot import changed project.godot unexpectedly.",
                )
            )

        after: list[GodotSourceEvidence] = []
        for prior in before:
            reference = reference_by_path.get(prior.path)
            current = self.capture_source(prior.path, reference=reference)
            after.append(current)
            if (current.sha256, current.content_length) != (prior.sha256, prior.content_length):
                issues.append(
                    GodotPortabilityIssue(
                        "SOURCE_MUTATED",
                        prior.path,
                        "Godot rebuild changed preserved source bytes.",
                    )
                )
            if Path(prior.path).suffix.lower() in _IMPORTABLE_EXTENSIONS and current.import_settings is None:
                issues.append(
                    GodotPortabilityIssue(
                        "MISSING_IMPORT_SIDECAR",
                        f"{prior.path}.import",
                        "Godot import completed without required import metadata.",
                    )
                )

        generated_count = self._generated_cache_file_count()
        if any(Path(item.path).suffix.lower() in _IMPORTABLE_EXTENSIONS for item in after) and generated_count == 0:
            issues.append(
                GodotPortabilityIssue(
                    "MISSING_GENERATED_CACHE",
                    ".godot",
                    "Godot import produced no generated cache files for importable sources.",
                )
            )

        state = GodotRebuildState.READY if not issues else GodotRebuildState.FAILED
        return self._report(
            state=state,
            engine_version=raw_version,
            project_identity=(project_sha, project_length),
            sources=tuple(after),
            references=references,
            issues=tuple(issues),
            purged=purged,
            generated_count=generated_count,
            import_returncode=returncode,
        )

    def _report(
        self,
        *,
        state: GodotRebuildState,
        engine_version: str | None,
        project_identity: tuple[str, int],
        sources: Sequence[GodotSourceEvidence],
        references: Sequence[ProjectAssetReference],
        issues: Sequence[GodotPortabilityIssue] = (),
        purged: tuple[str, ...] = (),
        generated_count: int = 0,
        import_returncode: int | None = None,
    ) -> GodotRebuildReport:
        normalized_sources = tuple(sorted(sources, key=lambda item: item.path))
        normalized_references = self._reference_payload(references)
        report = GodotRebuildReport(
            state=state,
            engine_version=engine_version,
            project_sha256=project_identity[0],
            project_length=project_identity[1],
            sources=normalized_sources,
            references=normalized_references,
            issues=tuple(sorted(issues, key=lambda item: (item.code, item.path or ""))),
            purged_cache_roots=purged,
            generated_cache_files=generated_count,
            import_returncode=import_returncode,
            manifest_digest=None,
        )
        digest = hashlib.sha256(_canonical_bytes(report.manifest_payload())).hexdigest()
        return GodotRebuildReport(
            state=report.state,
            engine_version=report.engine_version,
            project_sha256=report.project_sha256,
            project_length=report.project_length,
            sources=report.sources,
            references=report.references,
            issues=report.issues,
            purged_cache_roots=report.purged_cache_roots,
            generated_cache_files=report.generated_cache_files,
            import_returncode=report.import_returncode,
            manifest_digest=digest,
        )

    def _generated_cache_file_count(self) -> int:
        total = 0
        for name in sorted(_GENERATED_ROOTS):
            lexical = self.boundary.root / name
            if lexical.is_symlink():
                raise PermissionError(f"Refusing to follow generated-cache symlink: {name}")
            if not lexical.exists():
                continue
            root = self.boundary.resolve(name, must_exist=True)
            total += sum(1 for item in root.rglob("*") if item.is_file())
        return total

    def _invoke_result(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        wrapped = self.executor.invoke(tool_name, arguments or {})
        payload = getattr(wrapped, "result", wrapped)
        if not isinstance(payload, dict):
            raise TypeError(f"Structured Godot tool returned non-object payload: {tool_name}")
        return dict(payload)

    def _reference_map(
        self,
        references: Sequence[ProjectAssetReference],
    ) -> dict[str, ProjectAssetReference]:
        result: dict[str, ProjectAssetReference] = {}
        for reference in references:
            if reference.target_path is None:
                continue
            normalized = self._normalize_path(reference.target_path)
            if normalized in result and result[normalized] != reference:
                raise ValueError(f"Conflicting project references for {normalized}")
            result[normalized] = reference
        return result

    def _reference_payload(
        self,
        references: Sequence[ProjectAssetReference],
    ) -> tuple[dict[str, str | None], ...]:
        payload = [
            {
                "project_id": item.project_id,
                "asset_id": str(item.asset_id),
                "revision_id": str(item.revision_id),
                "target_path": self._normalize_path(item.target_path) if item.target_path is not None else None,
            }
            for item in references
        ]
        return tuple(
            sorted(
                payload,
                key=lambda item: (
                    item["project_id"] or "",
                    item["target_path"] or "",
                    item["revision_id"] or "",
                ),
            )
        )

    def _normalize_path(self, path: str) -> str:
        target = self.boundary.resolve(path)
        return self.boundary.relative(target)
