from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kodepoia.intelligence.research.contracts import ResearchArtifact, ResearchReport, ResearchRequest
from kodepoia.intelligence.research.evidence import EvidenceRevision
from kodepoia.kodecode.workspace import WorkspaceBoundary


@dataclass(frozen=True, slots=True)
class ResearchStore:
    """Persist typed research evidence strictly below an initialized project's `.kodepoia/` root."""

    project_root: Path
    _boundary: WorkspaceBoundary = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        root = self.project_root.resolve(strict=False)
        object.__setattr__(self, "project_root", root)
        object.__setattr__(self, "_boundary", WorkspaceBoundary(root))

    @property
    def metadata_root(self) -> Path:
        return self._boundary.resolve(".kodepoia")

    @property
    def research_root(self) -> Path:
        return self._boundary.resolve(".kodepoia/research")

    def _require_initialized_project(self) -> None:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    @staticmethod
    def _read_object(path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Research document must be a JSON object: {path.name}")
        return payload

    def _typed_path(self, category: str, identifier: str) -> Path:
        if len(identifier) != 64 or any(character not in "0123456789abcdef" for character in identifier):
            raise ValueError("Research store identifiers must be lowercase SHA-256 hex digests")
        return self._boundary.resolve(f".kodepoia/research/{category}/{identifier}.json")

    def save_request(self, request: ResearchRequest) -> Path:
        self._require_initialized_project()
        path = self._typed_path("requests", request.request_id)
        self._write_json(path, request.to_dict())
        return path

    def load_request(self, request_id: str) -> ResearchRequest:
        self._require_initialized_project()
        return ResearchRequest.from_dict(self._read_object(self._typed_path("requests", request_id)))

    def has_artifact(self, artifact_id: str) -> bool:
        self._require_initialized_project()
        return self._typed_path("artifacts", artifact_id).is_file()

    def save_evidence_revision(self, revision: EvidenceRevision) -> Path:
        self._require_initialized_project()
        path = self._typed_path("evidence_revisions", revision.revision_id)
        if path.is_file():
            stored = EvidenceRevision.from_dict(self._read_object(path))
            if stored.to_dict() != revision.to_dict():
                raise ValueError("Evidence revision ID collision")
            return path
        self._write_json(path, revision.to_dict())
        return path

    def load_evidence_revision(self, revision_id: str) -> EvidenceRevision:
        self._require_initialized_project()
        return EvidenceRevision.from_dict(
            self._read_object(self._typed_path("evidence_revisions", revision_id))
        )

    def list_evidence_revisions(self) -> tuple[EvidenceRevision, ...]:
        self._require_initialized_project()
        directory = self._boundary.resolve(".kodepoia/research/evidence_revisions")
        if not directory.is_dir():
            return ()
        revisions = [
            self.load_evidence_revision(path.stem)
            for path in sorted(directory.iterdir(), key=lambda item: item.name)
            if path.is_file() and path.suffix == ".json"
        ]
        return tuple(sorted(revisions, key=lambda item: (item.retrieved_at, item.revision_id)))

    def save_artifact(self, artifact: ResearchArtifact) -> Path:
        self._require_initialized_project()
        path = self._typed_path("artifacts", artifact.artifact_id)
        if path.is_file():
            previous = ResearchArtifact.from_dict(self._read_object(path))
            self.save_evidence_revision(EvidenceRevision.from_artifact(previous))
        self._write_json(path, artifact.to_dict())
        self.save_evidence_revision(EvidenceRevision.from_artifact(artifact))
        return path

    def load_artifact(self, artifact_id: str) -> ResearchArtifact:
        self._require_initialized_project()
        return ResearchArtifact.from_dict(self._read_object(self._typed_path("artifacts", artifact_id)))

    def save_report(self, report: ResearchReport) -> Path:
        self._require_initialized_project()
        path = self._typed_path("reports", report.digest_sha256)
        self._write_json(path, report.to_dict())
        latest = self._boundary.resolve(".kodepoia/research/latest.json")
        self._write_json(latest, report.to_dict())
        return path

    def load_report(self, digest_sha256: str) -> ResearchReport:
        self._require_initialized_project()
        return ResearchReport.from_dict(
            self._read_object(self._typed_path("reports", digest_sha256))
        )

    def load_latest_report(self) -> ResearchReport:
        self._require_initialized_project()
        path = self._boundary.resolve(".kodepoia/research/latest.json", must_exist=True)
        return ResearchReport.from_dict(self._read_object(path))
