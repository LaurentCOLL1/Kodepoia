from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.kodecode.workspace import WorkspaceBoundary


_STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class AccessibilitySeverity(StrEnum):
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class AccessibilityStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


class AccessibilityReportStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


def _stable_id(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized or _STABLE_ID.fullmatch(normalized) is None:
        raise ValueError(f"{label} must be a stable non-empty identifier")
    return normalized


def _canonical_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class AccessibilityResult:
    rule_id: str
    target_id: str
    status: AccessibilityStatus
    severity: AccessibilitySeverity = AccessibilitySeverity.MAJOR
    summary: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    applicability_reason: str = ""
    blocking: bool = False

    def __post_init__(self) -> None:
        _stable_id(self.rule_id, label="Accessibility rule ID")
        _stable_id(self.target_id, label="Accessibility target ID")
        if self.status is AccessibilityStatus.NOT_APPLICABLE:
            if not self.applicability_reason.strip():
                raise ValueError("Not-applicable accessibility results require a reason")
            if self.blocking:
                raise ValueError("Not-applicable accessibility results cannot be blocking")
        elif self.applicability_reason.strip():
            raise ValueError("Applicability reason is only valid for not-applicable results")
        if self.blocking and self.status is not AccessibilityStatus.FAIL:
            raise ValueError("Only failing accessibility results can be blocking")

    @property
    def key(self) -> tuple[str, str]:
        return self.rule_id, self.target_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "target_id": self.target_id,
            "status": self.status.value,
            "severity": self.severity.value,
            "summary": self.summary,
            "evidence": self.evidence,
            "applicability_reason": self.applicability_reason,
            "blocking": self.blocking,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AccessibilityResult:
        return cls(
            rule_id=str(payload["rule_id"]),
            target_id=str(payload["target_id"]),
            status=AccessibilityStatus(payload["status"]),
            severity=AccessibilitySeverity(payload.get("severity", "major")),
            summary=str(payload.get("summary", "")),
            evidence=dict(payload.get("evidence", {})),
            applicability_reason=str(payload.get("applicability_reason", "")),
            blocking=bool(payload.get("blocking", False)),
        )


@dataclass(frozen=True, slots=True)
class AccessibilityReport:
    schema_version: int
    generated_at: str
    surface: str
    status: AccessibilityReportStatus
    results: tuple[AccessibilityResult, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("Unsupported accessibility report schema version")
        parsed = datetime.fromisoformat(self.generated_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Accessibility report timestamp must include a timezone")
        if not self.surface.strip():
            raise ValueError("Accessibility report surface is required")
        keys = [result.key for result in self.results]
        if len(keys) != len(set(keys)):
            raise ValueError("Accessibility rule/target pairs must be unique")
        if self.status is not self._derive_status():
            raise ValueError("Accessibility report status does not match result evidence")

    def _derive_status(self) -> AccessibilityReportStatus:
        applicable = [
            result
            for result in self.results
            if result.status is not AccessibilityStatus.NOT_APPLICABLE
        ]
        if not applicable:
            return AccessibilityReportStatus.UNKNOWN
        if any(result.status is AccessibilityStatus.FAIL for result in applicable):
            return AccessibilityReportStatus.FAIL
        if any(
            result.status in {AccessibilityStatus.WARN, AccessibilityStatus.UNKNOWN}
            for result in applicable
        ):
            return AccessibilityReportStatus.WARN
        return AccessibilityReportStatus.PASS

    @property
    def counts(self) -> dict[str, int]:
        return {
            "total": len(self.results),
            "applicable": sum(
                result.status is not AccessibilityStatus.NOT_APPLICABLE
                for result in self.results
            ),
            "passed": sum(result.status is AccessibilityStatus.PASS for result in self.results),
            "warnings": sum(result.status is AccessibilityStatus.WARN for result in self.results),
            "failed": sum(result.status is AccessibilityStatus.FAIL for result in self.results),
            "unknown": sum(result.status is AccessibilityStatus.UNKNOWN for result in self.results),
            "not_applicable": sum(
                result.status is AccessibilityStatus.NOT_APPLICABLE for result in self.results
            ),
            "blocking_failures": sum(
                result.status is AccessibilityStatus.FAIL and result.blocking
                for result in self.results
            ),
        }

    @property
    def blockers(self) -> tuple[AccessibilityResult, ...]:
        return tuple(
            result
            for result in self.results
            if result.status is AccessibilityStatus.FAIL and result.blocking
        )

    def _evidence_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "surface": self.surface,
            "status": self.status.value,
            "results": [result.to_dict() for result in self.results],
        }

    @property
    def evidence_sha256(self) -> str:
        return _canonical_sha256(self._evidence_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self._evidence_payload()
        payload["counts"] = self.counts
        payload["blockers"] = [
            {"rule_id": result.rule_id, "target_id": result.target_id}
            for result in self.blockers
        ]
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AccessibilityReport:
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("Unsupported accessibility report schema version")
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise ValueError("Accessibility report results must be a list")
        report = cls(
            schema_version=1,
            generated_at=str(payload["generated_at"]),
            surface=str(payload["surface"]),
            status=AccessibilityReportStatus(payload["status"]),
            results=tuple(AccessibilityResult.from_dict(item) for item in raw_results),
        )
        if payload.get("counts") != report.counts:
            raise ValueError("Serialized accessibility counts do not match result evidence")
        expected_blockers = [
            {"rule_id": result.rule_id, "target_id": result.target_id}
            for result in report.blockers
        ]
        if payload.get("blockers") != expected_blockers:
            raise ValueError("Serialized accessibility blockers do not match result evidence")
        if str(payload.get("evidence_sha256", "")) != report.evidence_sha256:
            raise ValueError("Accessibility evidence SHA-256 does not match report evidence")
        return report

    @classmethod
    def load(cls, path: Path) -> AccessibilityReport:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Accessibility report must be a JSON object")
        return cls.from_dict(payload)

    def to_test_case_results(self):
        from kodepoia.quality.tests import TestCaseResult, TestCaseStatus

        test_results: list[TestCaseResult] = []
        for result in self.results:
            if result.status is AccessibilityStatus.NOT_APPLICABLE:
                continue
            if result.status is AccessibilityStatus.PASS:
                status = TestCaseStatus.PASS
            elif result.status is AccessibilityStatus.WARN:
                status = TestCaseStatus.SKIP
            elif result.status is AccessibilityStatus.FAIL:
                status = TestCaseStatus.FAIL
            else:
                status = TestCaseStatus.ERROR
            test_results.append(
                TestCaseResult(
                    id=f"accessibility:{result.rule_id}:{result.target_id}",
                    status=status,
                    message=result.summary,
                    source="kodeaccessibility",
                    details={
                        "severity": result.severity.value,
                        "blocking": result.blocking,
                        "accessibility_evidence_sha256": self.evidence_sha256,
                    },
                )
            )
        return tuple(test_results)


class KodeAccessibility:
    @staticmethod
    def evaluate(
        results: Iterable[AccessibilityResult],
        *,
        surface: str,
        generated_at: str | None = None,
    ) -> AccessibilityReport:
        normalized = tuple(results)
        applicable = [
            result
            for result in normalized
            if result.status is not AccessibilityStatus.NOT_APPLICABLE
        ]
        if not applicable:
            status = AccessibilityReportStatus.UNKNOWN
        elif any(result.status is AccessibilityStatus.FAIL for result in applicable):
            status = AccessibilityReportStatus.FAIL
        elif any(
            result.status in {AccessibilityStatus.WARN, AccessibilityStatus.UNKNOWN}
            for result in applicable
        ):
            status = AccessibilityReportStatus.WARN
        else:
            status = AccessibilityReportStatus.PASS
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return AccessibilityReport(
            schema_version=1,
            generated_at=timestamp,
            surface=surface,
            status=status,
            results=normalized,
        )

    @staticmethod
    def contrast_ratio(foreground: tuple[int, int, int], background: tuple[int, int, int]) -> float:
        def luminance(rgb: tuple[int, int, int]) -> float:
            if len(rgb) != 3 or any(component < 0 or component > 255 for component in rgb):
                raise ValueError("RGB colors must contain three components from 0 to 255")
            channels = []
            for component in rgb:
                value = component / 255.0
                channels.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
            return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

        lighter = max(luminance(foreground), luminance(background))
        darker = min(luminance(foreground), luminance(background))
        return round((lighter + 0.05) / (darker + 0.05), 4)

    @classmethod
    def check_contrast(
        cls,
        *,
        target_id: str,
        foreground: tuple[int, int, int],
        background: tuple[int, int, int],
        minimum_ratio: float = 4.5,
        blocking: bool = True,
    ) -> AccessibilityResult:
        if minimum_ratio <= 1.0:
            raise ValueError("Minimum contrast ratio must be greater than 1")
        ratio = cls.contrast_ratio(foreground, background)
        passed = ratio >= minimum_ratio
        return AccessibilityResult(
            rule_id="contrast.minimum",
            target_id=target_id,
            status=AccessibilityStatus.PASS if passed else AccessibilityStatus.FAIL,
            severity=AccessibilitySeverity.MAJOR,
            summary=(
                f"Contrast ratio {ratio:.4g} meets minimum {minimum_ratio:.4g}"
                if passed
                else f"Contrast ratio {ratio:.4g} is below minimum {minimum_ratio:.4g}"
            ),
            evidence={
                "foreground_rgb": list(foreground),
                "background_rgb": list(background),
                "ratio": ratio,
                "minimum_ratio": minimum_ratio,
                "measurement": "explicit_srgb_values",
            },
            blocking=blocking and not passed,
        )

    @staticmethod
    def check_target_size(
        *,
        target_id: str,
        width: int,
        height: int,
        minimum_width: int = 24,
        minimum_height: int = 24,
        blocking: bool = False,
    ) -> AccessibilityResult:
        if min(width, height, minimum_width, minimum_height) <= 0:
            raise ValueError("Target dimensions and minimums must be positive")
        passed = width >= minimum_width and height >= minimum_height
        status = AccessibilityStatus.PASS if passed else (
            AccessibilityStatus.FAIL if blocking else AccessibilityStatus.WARN
        )
        return AccessibilityResult(
            rule_id="target.minimum_size",
            target_id=target_id,
            status=status,
            severity=AccessibilitySeverity.MAJOR,
            summary=(
                f"Target {width}x{height} meets minimum {minimum_width}x{minimum_height}"
                if passed
                else f"Target {width}x{height} is below direct-rectangle minimum {minimum_width}x{minimum_height}"
            ),
            evidence={
                "width": width,
                "height": height,
                "minimum_width": minimum_width,
                "minimum_height": minimum_height,
                "measurement": "direct_rectangle_only",
            },
            blocking=blocking and not passed,
        )


@dataclass(frozen=True, slots=True)
class AccessibilityStore:
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
    def accessibility_root(self) -> Path:
        return self._boundary.resolve(".kodepoia/diagnostics/accessibility")

    def _require_initialized_project(self) -> None:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")

    @staticmethod
    def _safe_surface(surface: str) -> str:
        value = re.sub(r"[^A-Za-z0-9._-]+", "-", surface.strip()).strip("-.")
        if not value:
            raise ValueError("Accessibility surface cannot normalize to an empty name")
        return value[:80]

    @staticmethod
    def _snapshot_name(surface: str, generated_at: str) -> str:
        parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00")).astimezone(UTC)
        stamp = parsed.strftime("%Y%m%dT%H%M%S%fZ")
        return f"accessibility-{surface}-{stamp}.json"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def save(
        self,
        report: AccessibilityReport,
        *,
        snapshot: bool = True,
    ) -> tuple[Path, Path | None]:
        self._require_initialized_project()
        root = self.accessibility_root
        root.mkdir(parents=True, exist_ok=True)
        safe_surface = self._safe_surface(report.surface)
        payload = report.to_dict()
        latest = root / f"{safe_surface}-latest.json"
        self._write_json(latest, payload)
        snapshot_path: Path | None = None
        if snapshot:
            snapshot_path = root / self._snapshot_name(safe_surface, report.generated_at)
            self._write_json(snapshot_path, payload)
        return latest, snapshot_path

    def load_latest(self, surface: str) -> AccessibilityReport:
        self._require_initialized_project()
        safe_surface = self._safe_surface(surface)
        return AccessibilityReport.load(self.accessibility_root / f"{safe_surface}-latest.json")
