from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kodepoia.intelligence.research.cache import (
    CACHE_SCHEMA_VERSION,
    CachedArtifactReference,
    ResearchCacheStore,
    ResearchResultManifest,
)
from kodepoia.intelligence.research.contracts import ResearchReport
from kodepoia.intelligence.research.orchestration import ResearchContextSummary
from kodepoia.intelligence.research.store import ResearchStore
from kodepoia.kodecode.workspace import WorkspaceBoundary


def validate_cached_report(manifest: ResearchResultManifest, report: ResearchReport) -> None:
    if report.digest_sha256 != manifest.report_digest:
        raise ValueError("Cached research report digest does not match result manifest")
    if report.request.request_id != manifest.request_id:
        raise ValueError("Cached research report request does not match result manifest provenance")
    observed = tuple(
        sorted(
            (
                artifact.artifact_id,
                artifact.source.source_id,
                artifact.content_sha256,
                artifact.retrieved_at,
                artifact.freshness.value,
                artifact.trust.value,
                artifact.guarded.suspicious,
            )
            for artifact in report.artifacts
        )
    )
    declared = tuple(
        sorted(
            (
                ref.artifact_id,
                ref.source_id,
                ref.content_sha256,
                ref.original_retrieved_at,
                ref.original_freshness.value,
                ref.trust.value,
                ref.suspicious,
            )
            for ref in manifest.artifact_refs
        )
    )
    if observed != declared:
        raise ValueError("Cached research report artifacts do not match result manifest evidence")


def load_cached_report(
    cache_store: ResearchCacheStore,
    research_store: ResearchStore,
    cache_key: str,
) -> tuple[ResearchResultManifest, ResearchReport]:
    manifest = cache_store.load_latest_result(cache_key)
    report = research_store.load_report(manifest.report_digest)
    validate_cached_report(manifest, report)
    return manifest, report


def references_from_report(report: ResearchReport) -> tuple[CachedArtifactReference, ...]:
    return tuple(CachedArtifactReference.from_artifact(artifact) for artifact in report.artifacts)


@dataclass(frozen=True, slots=True)
class ResearchContextStore:
    project_root: Path
    _boundary: WorkspaceBoundary = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        object.__setattr__(self, "project_root", root)
        object.__setattr__(self, "_boundary", WorkspaceBoundary(root))

    @property
    def metadata_root(self) -> Path:
        return self._boundary.resolve(".kodepoia")

    def _require_initialized_project(self) -> None:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")

    def _path(self, summary_id: str) -> Path:
        if len(summary_id) != 64 or any(character not in "0123456789abcdef" for character in summary_id):
            raise ValueError("Research context summary ID must be lowercase SHA-256")
        return self._boundary.resolve(f".kodepoia/research/context/{summary_id}.json")

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def save(self, summary: ResearchContextSummary) -> Path:
        self._require_initialized_project()
        path = self._path(summary.summary_id)
        self._write(path, summary.to_dict())
        return path

    def load(self, summary_id: str) -> ResearchContextSummary:
        self._require_initialized_project()
        payload = json.loads(self._path(summary_id).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Research context summary must be a JSON object")
        if int(payload.get("schema_version", 0)) != CACHE_SCHEMA_VERSION:
            raise ValueError("Unsupported research context summary schema version")
        return ResearchContextSummary.from_dict(payload)
