from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.media.serialization import canonical_sha256

from .contracts import FacialPerformanceProfile, FacialTargetCatalog, validate_profile_against_catalog
from .curves import FacialCurveSet


class FacialQAStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class FacialQAProfile:
    max_total_keys: int = 4096
    max_clipped_keys: int = 0
    require_non_empty_curves: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.max_total_keys, bool) or not isinstance(self.max_total_keys, int) or not 1 <= self.max_total_keys <= 100000:
            raise ValueError("max_total_keys must be 1..100000")
        if isinstance(self.max_clipped_keys, bool) or not isinstance(self.max_clipped_keys, int) or self.max_clipped_keys < 0:
            raise ValueError("max_clipped_keys must be non-negative")


@dataclass(frozen=True, slots=True)
class FacialQAReport:
    status: FacialQAStatus
    curve_set_digest: str
    total_curves: int
    total_keys: int
    clipped_keys: int
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "curve_set_digest": self.curve_set_digest,
            "total_curves": self.total_curves,
            "total_keys": self.total_keys,
            "clipped_keys": self.clipped_keys,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.facial_qa", "version": 1, "payload": self.canonical()})


def evaluate_facial_qa(
    curves: FacialCurveSet,
    profile: FacialPerformanceProfile,
    catalog: FacialTargetCatalog,
    *,
    qa_profile: FacialQAProfile = FacialQAProfile(),
) -> FacialQAReport:
    blockers: list[str] = []
    warnings: list[str] = []
    try:
        validate_profile_against_catalog(profile, catalog)
    except (ValueError, KeyError):
        blockers.append("profile_catalog_invalid")
    if curves.profile_digest != profile.digest():
        blockers.append("profile_digest_mismatch")
    if curves.target_catalog_digest != catalog.digest():
        blockers.append("catalog_digest_mismatch")
    total_keys = sum(len(curve.keys) for curve in curves.curves)
    if qa_profile.require_non_empty_curves and not curves.curves:
        blockers.append("empty_curves")
    if total_keys > qa_profile.max_total_keys:
        blockers.append("key_budget_exceeded")
    if curves.clipped_key_count > qa_profile.max_clipped_keys:
        blockers.append("clipped_key_budget_exceeded")
    for curve in curves.curves:
        try:
            target = catalog.target(curve.target_id)
        except KeyError:
            blockers.append("missing_target")
            continue
        for key in curve.keys:
            if key.value < target.minimum - 1e-9 or key.value > target.maximum + 1e-9:
                blockers.append("curve_value_out_of_range")
                break
    if curves.clipped_key_count and not blockers:
        warnings.append("curve_values_clamped")
    status = FacialQAStatus.FAIL if blockers else (FacialQAStatus.WARN if warnings else FacialQAStatus.PASS)
    return FacialQAReport(
        status=status,
        curve_set_digest=curves.digest(),
        total_curves=len(curves.curves),
        total_keys=total_keys,
        clipped_keys=curves.clipped_key_count,
        blockers=tuple(sorted(set(blockers))),
        warnings=tuple(sorted(set(warnings))),
    )
