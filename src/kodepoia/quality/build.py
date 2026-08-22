from __future__ import annotations

import hashlib
import json
import re
import tarfile
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.health import HealthDimension, HealthMetric, HealthStatus
from kodepoia.quality.tests import TestCaseResult, TestCaseStatus


_SCHEMA_VERSION = 1
_SHA40_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE_KEY_RE = re.compile(
    r"(?:password|passwd|secret|token|authorization|api[_-]?key|access[_-]?key|private[_-]?key)",
    re.IGNORECASE,
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_INLINE_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key|access[_-]?key)\s*[:=]\s*[^\s,;]+"
)


class BuildArtifactKind(StrEnum):
    WHEEL = "wheel"
    SDIST = "sdist"
    OTHER = "other"


class BuildStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def redact_sensitive(value: Any, *, key: str = "") -> Any:
    if key and _SENSITIVE_KEY_RE.search(key):
        return "<redacted>"
    if isinstance(value, Mapping):
        return {str(item_key): redact_sensitive(item_value, key=str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, str):
        redacted = _BEARER_RE.sub("Bearer <redacted>", value)
        redacted = _INLINE_SECRET_RE.sub(lambda match: f"{match.group(1)}=<redacted>", redacted)
        return redacted
    return value


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _evidence_hash(payload: Mapping[str, Any]) -> str:
    return _sha256_bytes(_canonical_json(payload).encode("utf-8"))


def _validate_sha256(value: str, field_name: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True)
class BuildArtifact:
    name: str
    kind: BuildArtifactKind
    size_bytes: int
    sha256: str
    validated: bool
    validation: str = ""

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name or Path(name).name != name or "/" in name or "\\" in name:
            raise ValueError("build artifact name must be a file name")
        if self.size_bytes < 0:
            raise ValueError("artifact size must be non-negative")
        _validate_sha256(self.sha256, "artifact sha256")
        object.__setattr__(self, "name", name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "validated": self.validated,
            "validation": self.validation,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BuildArtifact":
        return cls(
            name=str(payload["name"]),
            kind=BuildArtifactKind(str(payload["kind"])),
            size_bytes=int(payload["size_bytes"]),
            sha256=str(payload["sha256"]),
            validated=bool(payload["validated"]),
            validation=str(payload.get("validation", "")),
        )


def _artifact_kind(path: Path) -> BuildArtifactKind:
    lower = path.name.lower()
    if lower.endswith(".whl"):
        return BuildArtifactKind.WHEEL
    if lower.endswith(".tar.gz") or lower.endswith(".zip"):
        return BuildArtifactKind.SDIST
    return BuildArtifactKind.OTHER


def _validate_wheel(path: Path) -> tuple[bool, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
    except (OSError, zipfile.BadZipFile) as exc:
        return False, f"invalid wheel archive: {exc}"
    has_package = any(name.startswith("kodepoia/") for name in names)
    has_metadata = any(name.endswith(".dist-info/METADATA") for name in names)
    if not has_package or not has_metadata:
        return False, "wheel must contain kodepoia package and dist-info/METADATA"
    return True, "wheel archive structure validated"


def _validate_sdist(path: Path) -> tuple[bool, str]:
    try:
        if path.name.lower().endswith(".zip"):
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
        else:
            with tarfile.open(path, "r:*") as archive:
                names = archive.getnames()
    except (OSError, tarfile.TarError, zipfile.BadZipFile) as exc:
        return False, f"invalid sdist archive: {exc}"
    has_pyproject = any(name.endswith("/pyproject.toml") or name == "pyproject.toml" for name in names)
    has_package = any(
        name.endswith("/src/kodepoia/__init__.py") or name == "src/kodepoia/__init__.py"
        for name in names
    )
    if not has_pyproject or not has_package:
        return False, "sdist must contain pyproject.toml and src/kodepoia/__init__.py"
    return True, "sdist archive structure validated"


def collect_python_artifacts(project_root: str | Path) -> tuple[BuildArtifact, ...]:
    root = Path(project_root).resolve(strict=False)
    boundary = WorkspaceBoundary(root)
    dist = boundary.resolve("dist", must_exist=True)
    if not dist.is_dir():
        raise FileNotFoundError(f"dist directory not found: {dist}")
    artifacts: list[BuildArtifact] = []
    for path in sorted(item for item in dist.iterdir() if item.is_file()):
        kind = _artifact_kind(path)
        if kind is BuildArtifactKind.WHEEL:
            validated, validation = _validate_wheel(path)
        elif kind is BuildArtifactKind.SDIST:
            validated, validation = _validate_sdist(path)
        else:
            validated, validation = False, "unrecognized package artifact"
        artifacts.append(
            BuildArtifact(
                name=path.name,
                kind=kind,
                size_bytes=path.stat().st_size,
                sha256=_sha256_file(path),
                validated=validated,
                validation=validation,
            )
        )
    return tuple(artifacts)


def hash_source_inputs(project_root: str | Path) -> str:
    root = Path(project_root).resolve(strict=False)
    boundary = WorkspaceBoundary(root)
    candidates: list[Path] = []
    for relative in ("pyproject.toml", "README.md"):
        path = boundary.resolve(relative, must_exist=True)
        candidates.append(path)
    source_root = boundary.resolve("src", must_exist=True)
    candidates.extend(sorted(path for path in source_root.rglob("*") if path.is_file()))
    digest = hashlib.sha256()
    for path in sorted(candidates, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def dependency_input_digests(project_root: str | Path) -> dict[str, str]:
    root = Path(project_root).resolve(strict=False)
    boundary = WorkspaceBoundary(root)
    path = boundary.resolve("pyproject.toml", must_exist=True)
    return {"pyproject.toml": _sha256_file(path)}


@dataclass(frozen=True, slots=True)
class BuildManifest:
    generated_at: str
    source_sha: str
    platform: str
    python_version: str
    build_backend: str
    source_digest_sha256: str
    dependency_inputs: Mapping[str, str]
    artifacts: tuple[BuildArtifact, ...]
    metadata: Mapping[str, Any]
    status: BuildStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported build manifest schema version")
        generated = datetime.fromisoformat(self.generated_at.replace("Z", "+00:00"))
        if generated.tzinfo is None:
            raise ValueError("build manifest timestamp must include timezone")
        if not _SHA40_RE.fullmatch(self.source_sha):
            raise ValueError("source_sha must be a 40-character Git SHA")
        if not self.platform.strip() or not self.python_version.strip() or not self.build_backend.strip():
            raise ValueError("platform, python_version and build_backend must be non-empty")
        _validate_sha256(self.source_digest_sha256, "source digest")
        for name, digest in self.dependency_inputs.items():
            if not str(name).strip():
                raise ValueError("dependency input names must be non-empty")
            _validate_sha256(str(digest), "dependency input digest")
        names = [artifact.name for artifact in self.artifacts]
        if len(names) != len(set(names)):
            raise ValueError("artifact names must be unique")
        expected = self.derive_status(self.artifacts)
        if self.status is not expected:
            raise ValueError("build manifest status does not match artifact evidence")
        redacted = redact_sensitive(dict(self.metadata))
        if dict(self.metadata) != redacted:
            raise ValueError("build metadata contains unredacted sensitive values")
        object.__setattr__(self, "dependency_inputs", dict(sorted(self.dependency_inputs.items())))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @staticmethod
    def derive_status(artifacts: Iterable[BuildArtifact]) -> BuildStatus:
        values = tuple(artifacts)
        if not values:
            return BuildStatus.UNKNOWN
        required = {BuildArtifactKind.WHEEL, BuildArtifactKind.SDIST}
        by_kind = {artifact.kind: artifact for artifact in values if artifact.kind in required}
        if set(by_kind) != required:
            return BuildStatus.FAIL
        if any(not by_kind[kind].validated for kind in required):
            return BuildStatus.FAIL
        return BuildStatus.PASS

    @property
    def artifact_counts(self) -> dict[str, int]:
        return {
            kind.value: sum(artifact.kind is kind for artifact in self.artifacts)
            for kind in BuildArtifactKind
        } | {"total": len(self.artifacts)}

    @property
    def blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for kind in (BuildArtifactKind.WHEEL, BuildArtifactKind.SDIST):
            matches = [artifact for artifact in self.artifacts if artifact.kind is kind]
            if not matches:
                blockers.append(f"missing:{kind.value}")
            elif not matches[0].validated:
                blockers.append(f"invalid:{kind.value}")
        return tuple(blockers)

    def _evidence_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_sha": self.source_sha.lower(),
            "platform": self.platform,
            "python_version": self.python_version,
            "build_backend": self.build_backend,
            "source_digest_sha256": self.source_digest_sha256,
            "dependency_inputs": dict(sorted(self.dependency_inputs.items())),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "metadata": dict(self.metadata),
            "status": self.status.value,
            "artifact_counts": self.artifact_counts,
            "blockers": list(self.blockers),
        }

    def validate(self) -> None:
        self.__post_init__()
        expected = _evidence_hash(self._evidence_payload())
        if self.evidence_sha256 != expected:
            raise ValueError("build manifest evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._evidence_payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        *,
        project_root: str | Path,
        source_sha: str,
        platform: str,
        python_version: str,
        artifacts: Iterable[BuildArtifact],
        metadata: Mapping[str, Any] | None = None,
        generated_at: str | None = None,
        build_backend: str = "hatchling.build",
    ) -> "BuildManifest":
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        artifact_tuple = tuple(artifacts)
        source_digest = hash_source_inputs(project_root)
        dependencies = dependency_input_digests(project_root)
        clean_metadata = redact_sensitive(dict(metadata or {}))
        status = cls.derive_status(artifact_tuple)
        provisional = cls(
            timestamp,
            source_sha.lower(),
            platform,
            python_version,
            build_backend,
            source_digest,
            dependencies,
            artifact_tuple,
            clean_metadata,
            status,
            "",
        )
        digest = _evidence_hash(provisional._evidence_payload())
        manifest = cls(
            timestamp,
            source_sha.lower(),
            platform,
            python_version,
            build_backend,
            source_digest,
            dependencies,
            artifact_tuple,
            clean_metadata,
            status,
            digest,
        )
        manifest.validate()
        return manifest

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BuildManifest":
        manifest = cls(
            generated_at=str(payload["generated_at"]),
            source_sha=str(payload["source_sha"]),
            platform=str(payload["platform"]),
            python_version=str(payload["python_version"]),
            build_backend=str(payload["build_backend"]),
            source_digest_sha256=str(payload["source_digest_sha256"]),
            dependency_inputs=dict(payload.get("dependency_inputs") or {}),
            artifacts=tuple(BuildArtifact.from_dict(item) for item in payload["artifacts"]),
            metadata=dict(payload.get("metadata") or {}),
            status=BuildStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if dict(payload.get("artifact_counts") or {}) != manifest.artifact_counts:
            raise ValueError("serialized artifact counts do not match evidence")
        if tuple(payload.get("blockers") or ()) != manifest.blockers:
            raise ValueError("serialized build blockers do not match evidence")
        manifest.validate()
        return manifest

    @classmethod
    def load(cls, path: Path) -> "BuildManifest":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("build manifest must be a JSON object")
        return cls.from_dict(payload)


class KodeBuild:
    @staticmethod
    def collect(
        project_root: str | Path,
        *,
        source_sha: str,
        platform: str,
        python_version: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> BuildManifest:
        artifacts = collect_python_artifacts(project_root)
        return BuildManifest.build(
            project_root=project_root,
            source_sha=source_sha,
            platform=platform,
            python_version=python_version,
            artifacts=artifacts,
            metadata=metadata,
        )

    @staticmethod
    def to_health_metric(manifest: BuildManifest) -> HealthMetric:
        if manifest.status is BuildStatus.PASS:
            return HealthMetric(
                HealthDimension.BUILD,
                HealthStatus.PASS,
                100.0,
                "Python wheel and sdist validated",
                "KodeBuild",
                False,
                {"platform": manifest.platform, "source_sha": manifest.source_sha},
            )
        if manifest.status is BuildStatus.UNKNOWN:
            return HealthMetric(
                HealthDimension.BUILD,
                HealthStatus.UNKNOWN,
                None,
                "Build artifact evidence is unavailable",
                "KodeBuild",
                False,
                {"platform": manifest.platform, "source_sha": manifest.source_sha},
            )
        return HealthMetric(
            HealthDimension.BUILD,
            HealthStatus.FAIL,
            0.0,
            "Required Python build artifacts are missing or invalid",
            "KodeBuild",
            True,
            {"platform": manifest.platform, "source_sha": manifest.source_sha, "blockers": list(manifest.blockers)},
        )

    @staticmethod
    def to_test_cases(manifest: BuildManifest) -> tuple[TestCaseResult, ...]:
        cases: list[TestCaseResult] = []
        for kind in (BuildArtifactKind.WHEEL, BuildArtifactKind.SDIST):
            matches = [artifact for artifact in manifest.artifacts if artifact.kind is kind]
            passed = bool(matches and matches[0].validated)
            artifact = matches[0] if matches else None
            cases.append(
                TestCaseResult(
                    id=f"build:{manifest.platform}:{kind.value}",
                    status=TestCaseStatus.PASS if passed else TestCaseStatus.FAIL,
                    duration_s=0.0,
                    message=(artifact.validation if artifact else f"missing {kind.value}"),
                    source="KodeBuild",
                    details={
                        "source_sha": manifest.source_sha,
                        "artifact": artifact.name if artifact else None,
                        "sha256": artifact.sha256 if artifact else None,
                    },
                )
            )
        return tuple(cases)


@dataclass(frozen=True, slots=True)
class BuildStore:
    project_root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_root", self.project_root.resolve(strict=False))

    @property
    def boundary(self) -> WorkspaceBoundary:
        return WorkspaceBoundary(self.project_root)

    @property
    def metadata_root(self) -> Path:
        return self.boundary.resolve(".kodepoia", must_exist=True)

    @staticmethod
    def _safe(value: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-")
        if not safe:
            raise ValueError("platform does not produce a safe path")
        return safe

    @staticmethod
    def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def save(self, manifest: BuildManifest, *, snapshot: bool = True) -> tuple[Path, Path | None]:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")
        root = self.boundary.resolve(f".kodepoia/releases/{self._safe(manifest.platform)}")
        root.mkdir(parents=True, exist_ok=True)
        payload = manifest.to_dict()
        latest = root / "latest.json"
        self._write_json(latest, payload)
        snapshot_path: Path | None = None
        if snapshot:
            parsed = datetime.fromisoformat(manifest.generated_at.replace("Z", "+00:00")).astimezone(UTC)
            snapshot_path = root / f"build-{parsed.strftime('%Y%m%dT%H%M%S%fZ')}.json"
            self._write_json(snapshot_path, payload)
        return latest, snapshot_path

    def load_latest(self, platform: str) -> BuildManifest:
        root = self.boundary.resolve(f".kodepoia/releases/{self._safe(platform)}")
        return BuildManifest.load(root / "latest.json")
