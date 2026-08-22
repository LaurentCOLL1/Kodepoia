from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.tests import TestCaseResult, TestCaseStatus

_CASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SUPPORTED_MODES = {"L", "LA", "RGB", "RGBA"}


def _case_id(value: str) -> str:
    if not _CASE_ID.fullmatch(value):
        raise ValueError(
            "Visual case_id must use 1-128 letters, digits, dot, underscore or hyphen"
        )
    return value


def _timestamp(value: str | None = None) -> str:
    text = value or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Visual timestamp must include a timezone")
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class VisualStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class VisualMask:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.x < 0 or self.y < 0:
            raise ValueError("Visual mask coordinates cannot be negative")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Visual mask width and height must be positive")

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VisualMask:
        return cls(
            int(payload["x"]),
            int(payload["y"]),
            int(payload["width"]),
            int(payload["height"]),
        )


@dataclass(frozen=True, slots=True)
class VisualPolicy:
    pixel_delta_threshold: int = 0
    warn_changed_ratio: float = 0.001
    fail_changed_ratio: float = 0.01
    warn_perceptual_ratio: float = 0.05
    fail_perceptual_ratio: float = 0.15
    masks: tuple[VisualMask, ...] = ()

    def __post_init__(self) -> None:
        if not 0 <= self.pixel_delta_threshold <= 255:
            raise ValueError("pixel_delta_threshold must be between 0 and 255")
        values = {
            "warn_changed_ratio": self.warn_changed_ratio,
            "fail_changed_ratio": self.fail_changed_ratio,
            "warn_perceptual_ratio": self.warn_perceptual_ratio,
            "fail_perceptual_ratio": self.fail_perceptual_ratio,
        }
        for name, value in values.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.warn_changed_ratio > self.fail_changed_ratio:
            raise ValueError("warn_changed_ratio cannot exceed fail_changed_ratio")
        if self.warn_perceptual_ratio > self.fail_perceptual_ratio:
            raise ValueError("warn_perceptual_ratio cannot exceed fail_perceptual_ratio")

    def to_dict(self) -> dict[str, Any]:
        return {
            "pixel_delta_threshold": self.pixel_delta_threshold,
            "warn_changed_ratio": self.warn_changed_ratio,
            "fail_changed_ratio": self.fail_changed_ratio,
            "warn_perceptual_ratio": self.warn_perceptual_ratio,
            "fail_perceptual_ratio": self.fail_perceptual_ratio,
            "masks": [mask.to_dict() for mask in self.masks],
        }

    @property
    def sha256(self) -> str:
        return _sha_bytes(_canonical(self.to_dict()))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VisualPolicy:
        raw_masks = payload.get("masks", [])
        if not isinstance(raw_masks, list):
            raise ValueError("Visual policy masks must be a list")
        return cls(
            pixel_delta_threshold=int(payload.get("pixel_delta_threshold", 0)),
            warn_changed_ratio=float(payload.get("warn_changed_ratio", 0.001)),
            fail_changed_ratio=float(payload.get("fail_changed_ratio", 0.01)),
            warn_perceptual_ratio=float(payload.get("warn_perceptual_ratio", 0.05)),
            fail_perceptual_ratio=float(payload.get("fail_perceptual_ratio", 0.15)),
            masks=tuple(VisualMask.from_dict(dict(item)) for item in raw_masks),
        )


@dataclass(frozen=True, slots=True)
class VisualImage:
    path: str
    sha256: str
    bytes: int
    format: str
    mode: str
    width: int
    height: int

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("Visual image path cannot be empty")
        if not _SHA256.fullmatch(self.sha256):
            raise ValueError("Visual image sha256 must be lowercase hexadecimal SHA-256")
        if self.bytes <= 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("Visual image size and dimensions must be positive")
        if not self.format or not self.mode:
            raise ValueError("Visual image format and mode cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "format": self.format,
            "mode": self.mode,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VisualImage:
        return cls(
            path=str(payload["path"]),
            sha256=str(payload["sha256"]),
            bytes=int(payload["bytes"]),
            format=str(payload["format"]),
            mode=str(payload["mode"]),
            width=int(payload["width"]),
            height=int(payload["height"]),
        )


@dataclass(frozen=True, slots=True)
class VisualBaselineApproval:
    case_id: str
    approved_at: str
    approved_by: str
    reason: str
    image: VisualImage
    manifest_sha256: str

    def __post_init__(self) -> None:
        _case_id(self.case_id)
        _timestamp(self.approved_at)
        if not self.approved_by.strip() or not self.reason.strip():
            raise ValueError("Visual baseline approval requires approver and reason")
        if self.manifest_sha256 != self.compute_manifest_sha256():
            raise ValueError("Visual baseline manifest hash does not match evidence")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "case_id": self.case_id,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "reason": self.reason,
            "image": self.image.to_dict(),
        }

    def compute_manifest_sha256(self) -> str:
        return _sha_bytes(_canonical(self._payload()))

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "manifest_sha256": self.manifest_sha256}

    @classmethod
    def create(
        cls,
        *,
        case_id: str,
        approved_at: str,
        approved_by: str,
        reason: str,
        image: VisualImage,
    ) -> VisualBaselineApproval:
        safe_case = _case_id(case_id)
        normalized = _timestamp(approved_at)
        payload = {
            "schema_version": 1,
            "case_id": safe_case,
            "approved_at": normalized,
            "approved_by": approved_by,
            "reason": reason,
            "image": image.to_dict(),
        }
        return cls(
            case_id=safe_case,
            approved_at=normalized,
            approved_by=approved_by,
            reason=reason,
            image=image,
            manifest_sha256=_sha_bytes(_canonical(payload)),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VisualBaselineApproval:
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("Unsupported visual baseline schema version")
        return cls(
            case_id=str(payload["case_id"]),
            approved_at=str(payload["approved_at"]),
            approved_by=str(payload["approved_by"]),
            reason=str(payload["reason"]),
            image=VisualImage.from_dict(dict(payload["image"])),
            manifest_sha256=str(payload["manifest_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class VisualMetrics:
    comparable: bool
    exact_file_match: bool
    pixel_identical: bool
    changed_pixels: int
    compared_pixels: int
    masked_pixels: int
    changed_ratio: float
    mean_absolute_error: float
    max_channel_delta: int
    perceptual_distance_ratio: float

    def __post_init__(self) -> None:
        if min(self.changed_pixels, self.compared_pixels, self.masked_pixels) < 0:
            raise ValueError("Visual pixel counts cannot be negative")
        if self.changed_pixels > self.compared_pixels:
            raise ValueError("changed_pixels cannot exceed compared_pixels")
        for name, value in (
            ("changed_ratio", self.changed_ratio),
            ("mean_absolute_error", self.mean_absolute_error),
            ("perceptual_distance_ratio", self.perceptual_distance_ratio),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not 0 <= self.max_channel_delta <= 255:
            raise ValueError("max_channel_delta must be between 0 and 255")
        if not self.comparable:
            carried = (
                self.exact_file_match,
                self.pixel_identical,
                self.changed_pixels,
                self.compared_pixels,
                self.masked_pixels,
                self.changed_ratio,
                self.mean_absolute_error,
                self.max_channel_delta,
                self.perceptual_distance_ratio,
            )
            if any(carried):
                raise ValueError("Incomparable metrics cannot carry comparison values")
            return
        if self.compared_pixels <= 0:
            raise ValueError("Comparable metrics require at least one compared pixel")
        expected_ratio = round(self.changed_pixels / self.compared_pixels, 8)
        if abs(self.changed_ratio - expected_ratio) > 0.00000001:
            raise ValueError("changed_ratio does not match pixel evidence")
        expected_identical = self.changed_pixels == 0 and self.max_channel_delta == 0
        if self.pixel_identical != expected_identical:
            raise ValueError("pixel_identical does not match pixel evidence")

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparable": self.comparable,
            "exact_file_match": self.exact_file_match,
            "pixel_identical": self.pixel_identical,
            "changed_pixels": self.changed_pixels,
            "compared_pixels": self.compared_pixels,
            "masked_pixels": self.masked_pixels,
            "changed_ratio": self.changed_ratio,
            "mean_absolute_error": self.mean_absolute_error,
            "max_channel_delta": self.max_channel_delta,
            "perceptual_distance_ratio": self.perceptual_distance_ratio,
        }

    @classmethod
    def incomparable(cls) -> VisualMetrics:
        return cls(False, False, False, 0, 0, 0, 0.0, 0.0, 0, 0.0)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VisualMetrics:
        return cls(
            comparable=bool(payload["comparable"]),
            exact_file_match=bool(payload["exact_file_match"]),
            pixel_identical=bool(payload["pixel_identical"]),
            changed_pixels=int(payload["changed_pixels"]),
            compared_pixels=int(payload["compared_pixels"]),
            masked_pixels=int(payload["masked_pixels"]),
            changed_ratio=float(payload["changed_ratio"]),
            mean_absolute_error=float(payload["mean_absolute_error"]),
            max_channel_delta=int(payload["max_channel_delta"]),
            perceptual_distance_ratio=float(payload["perceptual_distance_ratio"]),
        )


@dataclass(frozen=True, slots=True)
class VisualReport:
    schema_version: int
    generated_at: str
    case_id: str
    status: VisualStatus
    baseline: VisualImage | None
    baseline_approval_sha256: str | None
    current: VisualImage | None
    policy: VisualPolicy
    policy_sha256: str
    metrics: VisualMetrics
    diff: VisualImage | None
    reasons: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("Unsupported visual report schema version")
        _timestamp(self.generated_at)
        _case_id(self.case_id)
        if self.policy_sha256 != self.policy.sha256:
            raise ValueError("Visual report policy hash does not match policy")
        if self.baseline_approval_sha256 is not None and not _SHA256.fullmatch(
            self.baseline_approval_sha256
        ):
            raise ValueError("baseline_approval_sha256 must be SHA-256")
        if len(self.reasons) != len(set(self.reasons)):
            raise ValueError("Visual report reasons must be unique")
        expected = self.derive_status(
            baseline=self.baseline,
            current=self.current,
            policy=self.policy,
            metrics=self.metrics,
            reasons=self.reasons,
        )
        if self.status is not expected:
            raise ValueError("Visual report status does not match evidence")
        if self.evidence_sha256 != self.compute_evidence_sha256():
            raise ValueError("Visual report evidence hash does not match evidence")

    @staticmethod
    def derive_status(
        *,
        baseline: VisualImage | None,
        current: VisualImage | None,
        policy: VisualPolicy,
        metrics: VisualMetrics,
        reasons: tuple[str, ...],
    ) -> VisualStatus:
        if baseline is None or current is None:
            return VisualStatus.UNKNOWN
        if not metrics.comparable:
            return VisualStatus.FAIL
        if any(reason.endswith("_mismatch") or reason.startswith("unsupported_") for reason in reasons):
            return VisualStatus.FAIL
        if metrics.exact_file_match:
            return VisualStatus.PASS
        if (
            metrics.changed_ratio >= policy.fail_changed_ratio
            or metrics.perceptual_distance_ratio >= policy.fail_perceptual_ratio
        ):
            return VisualStatus.FAIL
        if (
            metrics.changed_ratio >= policy.warn_changed_ratio
            or metrics.perceptual_distance_ratio >= policy.warn_perceptual_ratio
        ):
            return VisualStatus.WARN
        return VisualStatus.PASS

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "case_id": self.case_id,
            "status": self.status.value,
            "baseline": None if self.baseline is None else self.baseline.to_dict(),
            "baseline_approval_sha256": self.baseline_approval_sha256,
            "current": None if self.current is None else self.current.to_dict(),
            "policy": self.policy.to_dict(),
            "policy_sha256": self.policy_sha256,
            "metrics": self.metrics.to_dict(),
            "diff": None if self.diff is None else self.diff.to_dict(),
            "reasons": list(self.reasons),
        }

    def compute_evidence_sha256(self) -> str:
        return _sha_bytes(_canonical(self._payload()))

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "evidence_sha256": self.evidence_sha256}

    @classmethod
    def create(
        cls,
        *,
        generated_at: str,
        case_id: str,
        baseline: VisualImage | None,
        baseline_approval_sha256: str | None,
        current: VisualImage | None,
        policy: VisualPolicy,
        metrics: VisualMetrics,
        diff: VisualImage | None,
        reasons: tuple[str, ...],
    ) -> VisualReport:
        normalized = _timestamp(generated_at)
        safe_case = _case_id(case_id)
        status = cls.derive_status(
            baseline=baseline,
            current=current,
            policy=policy,
            metrics=metrics,
            reasons=reasons,
        )
        provisional = {
            "schema_version": 1,
            "generated_at": normalized,
            "case_id": safe_case,
            "status": status.value,
            "baseline": None if baseline is None else baseline.to_dict(),
            "baseline_approval_sha256": baseline_approval_sha256,
            "current": None if current is None else current.to_dict(),
            "policy": policy.to_dict(),
            "policy_sha256": policy.sha256,
            "metrics": metrics.to_dict(),
            "diff": None if diff is None else diff.to_dict(),
            "reasons": list(reasons),
        }
        return cls(
            schema_version=1,
            generated_at=normalized,
            case_id=safe_case,
            status=status,
            baseline=baseline,
            baseline_approval_sha256=baseline_approval_sha256,
            current=current,
            policy=policy,
            policy_sha256=policy.sha256,
            metrics=metrics,
            diff=diff,
            reasons=reasons,
            evidence_sha256=_sha_bytes(_canonical(provisional)),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VisualReport:
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("Unsupported visual report schema version")
        return cls(
            schema_version=1,
            generated_at=str(payload["generated_at"]),
            case_id=str(payload["case_id"]),
            status=VisualStatus(payload["status"]),
            baseline=(
                None
                if payload.get("baseline") is None
                else VisualImage.from_dict(dict(payload["baseline"]))
            ),
            baseline_approval_sha256=(
                None
                if payload.get("baseline_approval_sha256") is None
                else str(payload["baseline_approval_sha256"])
            ),
            current=(
                None
                if payload.get("current") is None
                else VisualImage.from_dict(dict(payload["current"]))
            ),
            policy=VisualPolicy.from_dict(dict(payload["policy"])),
            policy_sha256=str(payload["policy_sha256"]),
            metrics=VisualMetrics.from_dict(dict(payload["metrics"])),
            diff=(
                None
                if payload.get("diff") is None
                else VisualImage.from_dict(dict(payload["diff"]))
            ),
            reasons=tuple(str(item) for item in payload.get("reasons", [])),
            evidence_sha256=str(payload["evidence_sha256"]),
        )

    @classmethod
    def load(cls, path: Path) -> VisualReport:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Visual report must be a JSON object")
        return cls.from_dict(payload)


@dataclass(frozen=True, slots=True)
class VisualStore:
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
    def root(self) -> Path:
        return self._boundary.resolve(".kodepoia/visual_tests")

    @property
    def baselines_root(self) -> Path:
        return self._boundary.resolve(".kodepoia/visual_tests/baselines")

    @property
    def runs_root(self) -> Path:
        return self._boundary.resolve(".kodepoia/visual_tests/runs")

    @property
    def diffs_root(self) -> Path:
        return self._boundary.resolve(".kodepoia/visual_tests/diffs")

    def require_initialized_project(self) -> None:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia metadata not found: {self.metadata_root}")

    def ensure(self) -> None:
        self.require_initialized_project()
        self.root.mkdir(exist_ok=True)
        self.baselines_root.mkdir(exist_ok=True)
        self.runs_root.mkdir(exist_ok=True)
        self.diffs_root.mkdir(exist_ok=True)

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def inspect_image(self, path: str) -> VisualImage:
        target = self._boundary.resolve(path, must_exist=True)
        if not target.is_file():
            raise ValueError(f"Visual image is not a file: {path}")
        with Image.open(target) as image:
            image.load()
            image_format = str(image.format or "")
            mode = image.mode
            width, height = image.size
        return VisualImage(
            path=self._boundary.relative(target),
            sha256=_sha_file(target),
            bytes=target.stat().st_size,
            format=image_format,
            mode=mode,
            width=width,
            height=height,
        )

    def approve_baseline(
        self,
        *,
        case_id: str,
        source_path: str,
        approved_by: str,
        reason: str,
        approved_at: str | None = None,
    ) -> VisualBaselineApproval:
        self.ensure()
        safe_case = _case_id(case_id)
        source = self._boundary.resolve(source_path, must_exist=True)
        source_image = self.inspect_image(source_path)
        case_root = self.baselines_root / safe_case
        case_root.mkdir(parents=True, exist_ok=True)
        suffix = source.suffix.lower() or ".img"
        artifact = case_root / f"{source_image.sha256}{suffix}"
        manifest = case_root / f"{source_image.sha256}.json"
        if artifact.exists() or manifest.exists():
            if not artifact.is_file() or not manifest.is_file():
                raise RuntimeError("Visual baseline identity collides with a non-file")
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            existing = VisualBaselineApproval.from_dict(dict(payload))
            if _sha_file(artifact) != existing.image.sha256:
                raise ValueError("Stored visual baseline artifact hash does not match approval")
            return existing

        temporary = artifact.with_name(f".{artifact.name}.tmp")
        shutil.copyfile(source, temporary)
        if _sha_file(temporary) != source_image.sha256:
            temporary.unlink(missing_ok=True)
            raise RuntimeError("Visual baseline copy hash mismatch")
        temporary.replace(artifact)
        stored = self.inspect_image(self._boundary.relative(artifact))
        approval = VisualBaselineApproval.create(
            case_id=safe_case,
            approved_at=_timestamp(approved_at),
            approved_by=approved_by,
            reason=reason,
            image=stored,
        )
        self._write_json(manifest, approval.to_dict())
        return approval

    def load_baseline(self, *, case_id: str, sha256: str) -> VisualBaselineApproval:
        self.ensure()
        safe_case = _case_id(case_id)
        if not _SHA256.fullmatch(sha256):
            raise ValueError("Visual baseline SHA-256 must be lowercase hexadecimal")
        manifest = self._boundary.resolve(
            f".kodepoia/visual_tests/baselines/{safe_case}/{sha256}.json",
            must_exist=True,
        )
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Visual baseline manifest must be a JSON object")
        approval = VisualBaselineApproval.from_dict(payload)
        if approval.case_id != safe_case or approval.image.sha256 != sha256:
            raise ValueError("Visual baseline manifest identity mismatch")
        artifact = self._boundary.resolve(approval.image.path, must_exist=True)
        if _sha_file(artifact) != approval.image.sha256:
            raise ValueError("Visual baseline artifact was modified after approval")
        return approval

    def diff_path(self, *, case_id: str, generated_at: str) -> Path:
        self.ensure()
        parsed = datetime.fromisoformat(_timestamp(generated_at).replace("Z", "+00:00"))
        stamp = parsed.strftime("%Y%m%dT%H%M%S%fZ")
        return self._boundary.resolve(
            f".kodepoia/visual_tests/diffs/{_case_id(case_id)}-{stamp}.png"
        )

    def save_report(self, report: VisualReport) -> tuple[Path, Path]:
        self.ensure()
        case_root = self.runs_root / _case_id(report.case_id)
        case_root.mkdir(parents=True, exist_ok=True)
        parsed = datetime.fromisoformat(report.generated_at.replace("Z", "+00:00"))
        snapshot = case_root / f"visual-{parsed.strftime('%Y%m%dT%H%M%S%fZ')}.json"
        latest = case_root / "latest.json"
        self._write_json(snapshot, report.to_dict())
        self._write_json(latest, report.to_dict())
        return latest, snapshot

    def load_latest(self, case_id: str) -> VisualReport:
        self.require_initialized_project()
        path = self._boundary.resolve(
            f".kodepoia/visual_tests/runs/{_case_id(case_id)}/latest.json",
            must_exist=True,
        )
        return VisualReport.load(path)


class KodeVisualQA:
    """Deterministic, engine-neutral visual regression evaluator."""

    def __init__(self, project_root: Path) -> None:
        self.store = VisualStore(project_root)

    def compare(
        self,
        *,
        case_id: str,
        baseline: VisualBaselineApproval | None,
        current_path: str,
        policy: VisualPolicy | None = None,
        generated_at: str | None = None,
        write_diff: bool = True,
    ) -> VisualReport:
        safe_case = _case_id(case_id)
        visual_policy = policy or VisualPolicy()
        timestamp = _timestamp(generated_at)
        try:
            current = self.store.inspect_image(current_path)
        except FileNotFoundError:
            current = None

        if baseline is None:
            return self._save(
                safe_case,
                timestamp,
                None,
                None,
                current,
                visual_policy,
                VisualMetrics.incomparable(),
                None,
                ("missing_baseline",),
            )
        if baseline.case_id != safe_case:
            raise ValueError("Visual baseline case_id does not match comparison case_id")
        try:
            verified = self.store.load_baseline(
                case_id=safe_case, sha256=baseline.image.sha256
            )
        except FileNotFoundError:
            return self._save(
                safe_case,
                timestamp,
                None,
                baseline.manifest_sha256,
                current,
                visual_policy,
                VisualMetrics.incomparable(),
                None,
                ("missing_baseline_artifact",),
            )
        if verified.manifest_sha256 != baseline.manifest_sha256:
            raise ValueError("Visual baseline approval does not match stored manifest")
        if current is None:
            return self._save(
                safe_case,
                timestamp,
                verified.image,
                verified.manifest_sha256,
                None,
                visual_policy,
                VisualMetrics.incomparable(),
                None,
                ("missing_current",),
            )

        reasons: list[str] = []
        if verified.image.format != current.format:
            reasons.append("format_mismatch")
        if verified.image.mode != current.mode:
            reasons.append("mode_mismatch")
        if (verified.image.width, verified.image.height) != (current.width, current.height):
            reasons.append("resolution_mismatch")
        if current.mode not in _SUPPORTED_MODES:
            reasons.append(f"unsupported_mode_{current.mode}")
        if reasons:
            return self._save(
                safe_case,
                timestamp,
                verified.image,
                verified.manifest_sha256,
                current,
                visual_policy,
                VisualMetrics.incomparable(),
                None,
                tuple(reasons),
            )

        baseline_file = self.store._boundary.resolve(verified.image.path, must_exist=True)
        current_file = self.store._boundary.resolve(current.path, must_exist=True)
        diff_path = (
            self.store.diff_path(case_id=safe_case, generated_at=timestamp)
            if write_diff
            else None
        )
        metrics, diff = self._compare_images(
            baseline_file, current_file, visual_policy, diff_path=diff_path
        )
        reasons = self._metric_reasons(metrics, visual_policy)
        return self._save(
            safe_case,
            timestamp,
            verified.image,
            verified.manifest_sha256,
            current,
            visual_policy,
            metrics,
            diff,
            reasons,
        )

    @staticmethod
    def to_test_case(
        report: VisualReport,
        *,
        warn_is_failure: bool = False,
        duration_s: float = 0.0,
    ) -> TestCaseResult:
        if report.status is VisualStatus.PASS:
            status = TestCaseStatus.PASS
        elif report.status is VisualStatus.WARN:
            status = TestCaseStatus.FAIL if warn_is_failure else TestCaseStatus.PASS
        elif report.status is VisualStatus.FAIL:
            status = TestCaseStatus.FAIL
        else:
            status = TestCaseStatus.ERROR
        return TestCaseResult(
            id=f"visual:{report.case_id}",
            status=status,
            duration_s=duration_s,
            message="; ".join(report.reasons),
            source="KodeVisualQA",
            details={
                "visual_status": report.status.value,
                "evidence_sha256": report.evidence_sha256,
                "policy_sha256": report.policy_sha256,
                "warn_is_failure": warn_is_failure,
            },
        )

    def _save(
        self,
        case_id: str,
        generated_at: str,
        baseline: VisualImage | None,
        baseline_approval_sha256: str | None,
        current: VisualImage | None,
        policy: VisualPolicy,
        metrics: VisualMetrics,
        diff: VisualImage | None,
        reasons: tuple[str, ...],
    ) -> VisualReport:
        report = VisualReport.create(
            generated_at=generated_at,
            case_id=case_id,
            baseline=baseline,
            baseline_approval_sha256=baseline_approval_sha256,
            current=current,
            policy=policy,
            metrics=metrics,
            diff=diff,
            reasons=reasons,
        )
        self.store.save_report(report)
        return report

    @staticmethod
    def _metric_reasons(metrics: VisualMetrics, policy: VisualPolicy) -> tuple[str, ...]:
        if metrics.exact_file_match:
            return ("exact_file_match",)
        reasons: list[str] = []
        if metrics.pixel_identical:
            reasons.append("pixel_identical_encoding_difference")
        if metrics.changed_ratio >= policy.fail_changed_ratio:
            reasons.append("changed_ratio_fail")
        elif metrics.changed_ratio >= policy.warn_changed_ratio:
            reasons.append("changed_ratio_warn")
        if metrics.perceptual_distance_ratio >= policy.fail_perceptual_ratio:
            reasons.append("perceptual_distance_fail")
        elif metrics.perceptual_distance_ratio >= policy.warn_perceptual_ratio:
            reasons.append("perceptual_distance_warn")
        return tuple(reasons or ["within_tolerance"])

    def _compare_images(
        self,
        baseline_path: Path,
        current_path: Path,
        policy: VisualPolicy,
        *,
        diff_path: Path | None,
    ) -> tuple[VisualMetrics, VisualImage | None]:
        with Image.open(baseline_path) as baseline_image, Image.open(current_path) as current_image:
            baseline_image.load()
            current_image.load()
            width, height = baseline_image.size
            self._validate_masks(policy.masks, width, height)
            changed = 0
            compared = 0
            masked = 0
            channel_delta_sum = 0
            channel_samples = 0
            max_delta = 0
            baseline_pixels = list(baseline_image.getdata())
            current_pixels = list(current_image.getdata())
            for index, pair in enumerate(zip(baseline_pixels, current_pixels, strict=True)):
                x = index % width
                y = index // width
                if any(mask.contains(x, y) for mask in policy.masks):
                    masked += 1
                    continue
                left = self._channels(pair[0])
                right = self._channels(pair[1])
                deltas = tuple(
                    abs(a - b) for a, b in zip(left, right, strict=True)
                )
                local_max = max(deltas, default=0)
                if local_max > policy.pixel_delta_threshold:
                    changed += 1
                compared += 1
                channel_delta_sum += sum(deltas)
                channel_samples += len(deltas)
                max_delta = max(max_delta, local_max)
            if compared <= 0:
                raise ValueError("Visual masks cannot exclude every image pixel")

            perceptual = self._dhash_distance(
                self._masked_for_hash(baseline_image, policy.masks),
                self._masked_for_hash(current_image, policy.masks),
            )
            diff = self._write_diff(
                baseline_image, current_image, policy.masks, diff_path
            )
            metrics = VisualMetrics(
                comparable=True,
                exact_file_match=_sha_file(baseline_path) == _sha_file(current_path),
                pixel_identical=changed == 0 and max_delta == 0,
                changed_pixels=changed,
                compared_pixels=compared,
                masked_pixels=masked,
                changed_ratio=round(changed / compared, 8),
                mean_absolute_error=round(
                    channel_delta_sum / max(channel_samples, 1) / 255.0, 8
                ),
                max_channel_delta=max_delta,
                perceptual_distance_ratio=perceptual,
            )
            return metrics, diff

    def _write_diff(
        self,
        baseline: Image.Image,
        current: Image.Image,
        masks: tuple[VisualMask, ...],
        path: Path | None,
    ) -> VisualImage | None:
        if path is None:
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        image = ImageChops.difference(baseline.convert("RGB"), current.convert("RGB"))
        if masks:
            draw = ImageDraw.Draw(image)
            for mask in masks:
                draw.rectangle(
                    (mask.x, mask.y, mask.x + mask.width - 1, mask.y + mask.height - 1),
                    fill=(0, 0, 0),
                )
        image.save(path, format="PNG")
        return self.store.inspect_image(self.store._boundary.relative(path))

    @staticmethod
    def _channels(pixel: Any) -> tuple[int, ...]:
        if isinstance(pixel, int):
            return (pixel,)
        if isinstance(pixel, tuple):
            return tuple(int(value) for value in pixel)
        raise ValueError(f"Unsupported pixel representation: {type(pixel).__name__}")

    @staticmethod
    def _validate_masks(masks: tuple[VisualMask, ...], width: int, height: int) -> None:
        for mask in masks:
            if mask.x + mask.width > width or mask.y + mask.height > height:
                raise ValueError("Visual mask must be fully contained in the image")

    @staticmethod
    def _masked_for_hash(
        image: Image.Image, masks: tuple[VisualMask, ...]
    ) -> Image.Image:
        prepared = image.convert("RGB")
        if not masks:
            return prepared
        prepared = prepared.copy()
        draw = ImageDraw.Draw(prepared)
        for mask in masks:
            draw.rectangle(
                (mask.x, mask.y, mask.x + mask.width - 1, mask.y + mask.height - 1),
                fill=(0, 0, 0),
            )
        return prepared

    @staticmethod
    def _dhash(image: Image.Image) -> int:
        sample = image.convert("L").resize((9, 8), Image.Resampling.NEAREST)
        pixels = list(sample.getdata())
        value = 0
        for y in range(8):
            offset = y * 9
            for x in range(8):
                value <<= 1
                if pixels[offset + x] > pixels[offset + x + 1]:
                    value |= 1
        return value

    @classmethod
    def _dhash_distance(cls, first: Image.Image, second: Image.Image) -> float:
        distance = (cls._dhash(first) ^ cls._dhash(second)).bit_count()
        return round(distance / 64.0, 8)
