from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

R8_INTEGRATION_SCHEMA_VERSION = 1
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_SUBDIVISIONS = tuple(f"R8.{index}" for index in range(1, 12))


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _digest_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


class R8IntegrationStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"


class R8ManualState(StrEnum):
    NONE = "none"
    REQUIRED_SATISFIED = "required_satisfied"
    CONDITIONAL_NOT_TRIGGERED = "conditional_not_triggered"
    CONDITIONAL_SATISFIED = "conditional_satisfied"
    REQUIRED_UNSATISFIED = "required_unsatisfied"
    CONDITIONAL_TRIGGERED_UNSATISFIED = "conditional_triggered_unsatisfied"

    @property
    def satisfied(self) -> bool:
        return self in {
            R8ManualState.NONE,
            R8ManualState.REQUIRED_SATISFIED,
            R8ManualState.CONDITIONAL_NOT_TRIGGERED,
            R8ManualState.CONDITIONAL_SATISFIED,
        }


@dataclass(frozen=True, slots=True)
class R8SubdivisionEvidence:
    subdivision: str
    status: R8IntegrationStatus
    source: str
    evidence_sha256: str
    evidence_bytes: int
    accepted_head: str
    manual_state: R8ManualState
    manual_reason: str
    manual_satisfied: bool = field(init=False)

    def __post_init__(self) -> None:
        if self.subdivision not in _EXPECTED_SUBDIVISIONS:
            raise ValueError(f"Unsupported R8 subdivision: {self.subdivision}")
        expected_source = f"docs/roadmap/R8_{self.subdivision.split('.')[1]}_ACCEPTANCE.md"
        if self.source != expected_source:
            raise ValueError(
                f"R8 subdivision {self.subdivision} must use canonical source {expected_source}"
            )
        if not _SHA256_RE.fullmatch(self.evidence_sha256):
            raise ValueError("R8 evidence SHA-256 must be lowercase hexadecimal")
        if self.evidence_bytes < 1:
            raise ValueError("R8 evidence byte length must be positive")
        if self.accepted_head and not _SHA40_RE.fullmatch(self.accepted_head):
            raise ValueError("R8 accepted head must be a lowercase 40-hex commit SHA")
        if self.status is R8IntegrationStatus.PASS and not self.accepted_head:
            raise ValueError("Passing R8 subdivision evidence requires an accepted head")
        if not self.manual_reason.strip():
            raise ValueError("R8 manual state requires an explicit reason")
        object.__setattr__(self, "manual_satisfied", self.manual_state.satisfied)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subdivision": self.subdivision,
            "status": self.status.value,
            "source": self.source,
            "evidence_sha256": self.evidence_sha256,
            "evidence_bytes": self.evidence_bytes,
            "accepted_head": self.accepted_head,
            "manual_state": self.manual_state.value,
            "manual_reason": self.manual_reason,
            "manual_satisfied": self.manual_satisfied,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "R8SubdivisionEvidence":
        item = cls(
            subdivision=str(payload["subdivision"]),
            status=R8IntegrationStatus(payload["status"]),
            source=str(payload["source"]),
            evidence_sha256=str(payload["evidence_sha256"]),
            evidence_bytes=int(payload["evidence_bytes"]),
            accepted_head=str(payload.get("accepted_head", "")),
            manual_state=R8ManualState(payload["manual_state"]),
            manual_reason=str(payload.get("manual_reason", "")),
        )
        if bool(payload.get("manual_satisfied", False)) != item.manual_satisfied:
            raise ValueError("R8 manual_satisfied does not match manual_state")
        return item


@dataclass(frozen=True, slots=True)
class R8IntegrationReport:
    generated_at: str
    source_sha: str
    subdivisions: tuple[R8SubdivisionEvidence, ...]
    status: R8IntegrationStatus
    blockers: tuple[str, ...] = ()
    schema_version: int = R8_INTEGRATION_SCHEMA_VERSION
    evidence_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != R8_INTEGRATION_SCHEMA_VERSION:
            raise ValueError("Unsupported R8 integration schema version")
        if not self.generated_at.strip():
            raise ValueError("R8 integration generated_at must not be empty")
        if not _SHA40_RE.fullmatch(self.source_sha):
            raise ValueError("R8 integration source_sha must be lowercase 40-hex")
        ids = tuple(item.subdivision for item in self.subdivisions)
        if ids != _EXPECTED_SUBDIVISIONS:
            raise ValueError("R8 integration subdivisions must contain R8.1 through R8.11 in order")
        if len(set(self.blockers)) != len(self.blockers):
            raise ValueError("R8 integration blockers must be unique")
        if any(not item.strip() for item in self.blockers):
            raise ValueError("R8 integration blockers must not be empty")
        derived = self.derived_blockers()
        if self.status is R8IntegrationStatus.PASS:
            if self.blockers or derived:
                raise ValueError("Passing R8 integration evidence cannot contain blockers")
        if self.status is R8IntegrationStatus.FAIL and not (self.blockers or derived):
            raise ValueError("Failing R8 integration evidence requires a blocker")
        r8_11 = self.subdivisions[-1]
        if r8_11.accepted_head and r8_11.accepted_head != self.source_sha:
            raise ValueError("R8.11 accepted head must equal integration source_sha")
        object.__setattr__(self, "evidence_sha256", _digest_payload(self.identity_payload()))

    def derived_blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for item in self.subdivisions:
            if item.status is not R8IntegrationStatus.PASS:
                blockers.append(f"{item.subdivision}:status={item.status.value}")
            if not item.accepted_head:
                blockers.append(f"{item.subdivision}:missing_accepted_head")
            if not item.manual_satisfied:
                blockers.append(f"{item.subdivision}:manual={item.manual_state.value}")
        return tuple(blockers)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_sha": self.source_sha,
            "subdivisions": [item.to_dict() for item in self.subdivisions],
            "status": self.status.value,
            "blockers": list(self.blockers),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.identity_payload(), "evidence_sha256": self.evidence_sha256}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "R8IntegrationReport":
        report = cls(
            generated_at=str(payload["generated_at"]),
            source_sha=str(payload["source_sha"]),
            subdivisions=tuple(
                R8SubdivisionEvidence.from_dict(item)
                for item in payload.get("subdivisions", [])
            ),
            status=R8IntegrationStatus(payload["status"]),
            blockers=tuple(str(item) for item in payload.get("blockers", [])),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("evidence_sha256", "")) != report.evidence_sha256:
            raise ValueError("R8 integration evidence digest does not match canonical content")
        return report


def build_subdivision_evidence(
    subdivision: str,
    *,
    accepted_head: str,
    manual_state: R8ManualState,
    manual_reason: str,
    canonical_bytes: bytes,
) -> R8SubdivisionEvidence:
    return R8SubdivisionEvidence(
        subdivision=subdivision,
        status=R8IntegrationStatus.PASS,
        source=f"docs/roadmap/R8_{subdivision.split('.')[1]}_ACCEPTANCE.md",
        evidence_sha256=hashlib.sha256(canonical_bytes).hexdigest(),
        evidence_bytes=len(canonical_bytes),
        accepted_head=accepted_head,
        manual_state=manual_state,
        manual_reason=manual_reason,
    )


def validate_repository_evidence(
    report: R8IntegrationReport,
    read_bytes: Callable[[str], bytes],
) -> None:
    """Recalculate canonical acceptance blobs and fail closed on any mismatch."""

    for item in report.subdivisions:
        try:
            payload = read_bytes(item.source)
        except Exception as exc:
            raise ValueError(f"Missing R8 acceptance evidence: {item.source}") from exc
        if not isinstance(payload, bytes):
            raise TypeError("R8 acceptance blob loader must return bytes")
        observed_length = len(payload)
        observed_sha = hashlib.sha256(payload).hexdigest()
        if observed_length != item.evidence_bytes:
            raise ValueError(
                f"R8 acceptance byte length mismatch for {item.subdivision}: "
                f"expected {item.evidence_bytes}, observed {observed_length}"
            )
        if observed_sha != item.evidence_sha256:
            raise ValueError(f"R8 acceptance SHA-256 mismatch for {item.subdivision}")
        text = payload.decode("utf-8", errors="strict")
        if item.accepted_head not in text:
            raise ValueError(
                f"R8 acceptance document does not contain declared accepted head: {item.subdivision}"
            )
        if item.status is not R8IntegrationStatus.PASS:
            raise ValueError(f"R8 subdivision is not PASS: {item.subdivision}")
        if not item.manual_satisfied:
            raise ValueError(f"R8 manual gate is not satisfied: {item.subdivision}")
        if not item.manual_reason.strip():
            raise ValueError(f"R8 manual reason is missing: {item.subdivision}")

    if report.subdivisions[-1].accepted_head != report.source_sha:
        raise ValueError("R8.11 accepted head does not match integration source SHA")
    if report.status is not R8IntegrationStatus.PASS:
        raise ValueError("R8 integrated report is not PASS")
    if report.blockers or report.derived_blockers():
        raise ValueError("R8 integrated report contains blockers")


def expected_r8_subdivisions() -> tuple[str, ...]:
    return _EXPECTED_SUBDIVISIONS
