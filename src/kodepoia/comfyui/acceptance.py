from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

R9_INTEGRATION_SCHEMA_VERSION = 1
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_SUBDIVISIONS = tuple(f"R9.{index}" for index in range(1, 12))


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


class R9IntegrationStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"


class R9ManualState(StrEnum):
    NONE = "none"
    REQUIRED_SATISFIED = "required_satisfied"
    CONDITIONAL_NOT_TRIGGERED = "conditional_not_triggered"
    CONDITIONAL_SATISFIED = "conditional_satisfied"
    REQUIRED_UNSATISFIED = "required_unsatisfied"
    CONDITIONAL_TRIGGERED_UNSATISFIED = "conditional_triggered_unsatisfied"

    @property
    def satisfied(self) -> bool:
        return self in {
            R9ManualState.NONE,
            R9ManualState.REQUIRED_SATISFIED,
            R9ManualState.CONDITIONAL_NOT_TRIGGERED,
            R9ManualState.CONDITIONAL_SATISFIED,
        }


@dataclass(frozen=True, slots=True)
class R9SubdivisionEvidence:
    subdivision: str
    status: R9IntegrationStatus
    source: str
    evidence_sha256: str
    evidence_bytes: int
    accepted_head: str
    manual_state: R9ManualState
    manual_reason: str
    manual_evidence_sha256: str | None = None
    manual_evidence_bytes: int | None = None
    manual_satisfied: bool = field(init=False)

    def __post_init__(self) -> None:
        if self.subdivision not in _EXPECTED_SUBDIVISIONS:
            raise ValueError(f"Unsupported R9 subdivision: {self.subdivision}")
        expected_source = f"docs/roadmap/R9_{self.subdivision.split('.')[1]}_ACCEPTANCE.md"
        if self.source != expected_source:
            raise ValueError(
                f"R9 subdivision {self.subdivision} must use canonical source {expected_source}"
            )
        if not _SHA256_RE.fullmatch(self.evidence_sha256):
            raise ValueError("R9 evidence SHA-256 must be lowercase hexadecimal")
        if self.evidence_bytes < 1:
            raise ValueError("R9 evidence byte length must be positive")
        if self.accepted_head and not _SHA40_RE.fullmatch(self.accepted_head):
            raise ValueError("R9 accepted head must be a lowercase 40-hex commit SHA")
        if self.status is R9IntegrationStatus.PASS and not self.accepted_head:
            raise ValueError("Passing R9 subdivision evidence requires an accepted head")
        if not self.manual_reason.strip():
            raise ValueError("R9 manual state requires an explicit reason")
        has_manual_digest = self.manual_evidence_sha256 is not None
        has_manual_bytes = self.manual_evidence_bytes is not None
        if has_manual_digest != has_manual_bytes:
            raise ValueError("R9 manual evidence digest and byte length must be provided together")
        if self.manual_evidence_sha256 is not None and not _SHA256_RE.fullmatch(
            self.manual_evidence_sha256
        ):
            raise ValueError("R9 manual evidence SHA-256 must be lowercase hexadecimal")
        if self.manual_evidence_bytes is not None and self.manual_evidence_bytes < 1:
            raise ValueError("R9 manual evidence byte length must be positive")
        if (
            self.subdivision == "R9.8"
            and self.manual_state is R9ManualState.REQUIRED_SATISFIED
            and not has_manual_digest
        ):
            raise ValueError("R9.8 REQUIRED SATISFIED evidence must reference reviewed local evidence")
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
            "manual_evidence_sha256": self.manual_evidence_sha256,
            "manual_evidence_bytes": self.manual_evidence_bytes,
            "manual_satisfied": self.manual_satisfied,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "R9SubdivisionEvidence":
        digest = payload.get("manual_evidence_sha256")
        byte_length = payload.get("manual_evidence_bytes")
        item = cls(
            subdivision=str(payload["subdivision"]),
            status=R9IntegrationStatus(payload["status"]),
            source=str(payload["source"]),
            evidence_sha256=str(payload["evidence_sha256"]),
            evidence_bytes=int(payload["evidence_bytes"]),
            accepted_head=str(payload.get("accepted_head", "")),
            manual_state=R9ManualState(payload["manual_state"]),
            manual_reason=str(payload.get("manual_reason", "")),
            manual_evidence_sha256=None if digest is None else str(digest),
            manual_evidence_bytes=None if byte_length is None else int(byte_length),
        )
        if bool(payload.get("manual_satisfied", False)) != item.manual_satisfied:
            raise ValueError("R9 manual_satisfied does not match manual_state")
        return item


@dataclass(frozen=True, slots=True)
class R9IntegrationReport:
    generated_at: str
    source_sha: str
    subdivisions: tuple[R9SubdivisionEvidence, ...]
    status: R9IntegrationStatus
    blockers: tuple[str, ...] = ()
    schema_version: int = R9_INTEGRATION_SCHEMA_VERSION
    evidence_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != R9_INTEGRATION_SCHEMA_VERSION:
            raise ValueError("Unsupported R9 integration schema version")
        if not self.generated_at.strip():
            raise ValueError("R9 integration generated_at must not be empty")
        if not _SHA40_RE.fullmatch(self.source_sha):
            raise ValueError("R9 integration source_sha must be lowercase 40-hex")
        ids = tuple(item.subdivision for item in self.subdivisions)
        if ids != _EXPECTED_SUBDIVISIONS:
            raise ValueError("R9 integration subdivisions must contain R9.1 through R9.11 in order")
        if len(set(self.blockers)) != len(self.blockers):
            raise ValueError("R9 integration blockers must be unique")
        if any(not item.strip() for item in self.blockers):
            raise ValueError("R9 integration blockers must not be empty")
        derived = self.derived_blockers()
        if self.status is R9IntegrationStatus.PASS:
            if self.blockers or derived:
                raise ValueError("Passing R9 integration evidence cannot contain blockers")
        if self.status is R9IntegrationStatus.FAIL and not (self.blockers or derived):
            raise ValueError("Failing R9 integration evidence requires a blocker")
        r9_11 = self.subdivisions[-1]
        if r9_11.accepted_head and r9_11.accepted_head != self.source_sha:
            raise ValueError("R9.11 accepted head must equal integration source_sha")
        object.__setattr__(self, "evidence_sha256", _digest_payload(self.identity_payload()))

    def derived_blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for item in self.subdivisions:
            if item.status is not R9IntegrationStatus.PASS:
                blockers.append(f"{item.subdivision}:status={item.status.value}")
            if not item.accepted_head:
                blockers.append(f"{item.subdivision}:missing_accepted_head")
            if not item.manual_satisfied:
                blockers.append(f"{item.subdivision}:manual={item.manual_state.value}")
            if (
                item.subdivision == "R9.8"
                and item.manual_state is R9ManualState.REQUIRED_SATISFIED
                and item.manual_evidence_sha256 is None
            ):
                blockers.append("R9.8:missing_required_local_evidence")
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
    def from_dict(cls, payload: Mapping[str, Any]) -> "R9IntegrationReport":
        report = cls(
            generated_at=str(payload["generated_at"]),
            source_sha=str(payload["source_sha"]),
            subdivisions=tuple(
                R9SubdivisionEvidence.from_dict(item)
                for item in payload.get("subdivisions", [])
            ),
            status=R9IntegrationStatus(payload["status"]),
            blockers=tuple(str(item) for item in payload.get("blockers", [])),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("evidence_sha256", "")) != report.evidence_sha256:
            raise ValueError("R9 integration evidence digest does not match canonical content")
        return report


def build_subdivision_evidence(
    subdivision: str,
    *,
    accepted_head: str,
    manual_state: R9ManualState,
    manual_reason: str,
    canonical_bytes: bytes,
    manual_evidence_sha256: str | None = None,
    manual_evidence_bytes: int | None = None,
) -> R9SubdivisionEvidence:
    return R9SubdivisionEvidence(
        subdivision=subdivision,
        status=R9IntegrationStatus.PASS,
        source=f"docs/roadmap/R9_{subdivision.split('.')[1]}_ACCEPTANCE.md",
        evidence_sha256=hashlib.sha256(canonical_bytes).hexdigest(),
        evidence_bytes=len(canonical_bytes),
        accepted_head=accepted_head,
        manual_state=manual_state,
        manual_reason=manual_reason,
        manual_evidence_sha256=manual_evidence_sha256,
        manual_evidence_bytes=manual_evidence_bytes,
    )


def validate_repository_evidence(
    report: R9IntegrationReport,
    read_bytes: Callable[[str], bytes],
) -> None:
    """Recalculate canonical R9 acceptance blobs and fail closed on mismatch."""

    for item in report.subdivisions:
        try:
            payload = read_bytes(item.source)
        except Exception as exc:
            raise ValueError(f"Missing R9 acceptance evidence: {item.source}") from exc
        if not isinstance(payload, bytes):
            raise TypeError("R9 acceptance blob loader must return bytes")
        observed_length = len(payload)
        observed_sha = hashlib.sha256(payload).hexdigest()
        if observed_length != item.evidence_bytes:
            raise ValueError(
                f"R9 acceptance byte length mismatch for {item.subdivision}: "
                f"expected {item.evidence_bytes}, observed {observed_length}"
            )
        if observed_sha != item.evidence_sha256:
            raise ValueError(f"R9 acceptance SHA-256 mismatch for {item.subdivision}")
        text = payload.decode("utf-8", errors="strict")
        if item.accepted_head not in text:
            raise ValueError(
                f"R9 acceptance document does not contain declared accepted head: {item.subdivision}"
            )
        if item.status is not R9IntegrationStatus.PASS:
            raise ValueError(f"R9 subdivision is not PASS: {item.subdivision}")
        if not item.manual_satisfied:
            raise ValueError(f"R9 manual gate is not satisfied: {item.subdivision}")
        if not item.manual_reason.strip():
            raise ValueError(f"R9 manual reason is missing: {item.subdivision}")
        if item.manual_evidence_sha256 is not None:
            if item.manual_evidence_sha256 not in text:
                raise ValueError(
                    f"R9 acceptance document does not reference manual evidence digest: {item.subdivision}"
                )
            if str(item.manual_evidence_bytes) not in text:
                raise ValueError(
                    f"R9 acceptance document does not reference manual evidence byte length: {item.subdivision}"
                )

    if report.subdivisions[-1].accepted_head != report.source_sha:
        raise ValueError("R9.11 accepted head does not match integration source SHA")
    if report.status is not R9IntegrationStatus.PASS:
        raise ValueError("R9 integrated report is not PASS")
    if report.blockers or report.derived_blockers():
        raise ValueError("R9 integrated report contains blockers")


def expected_r9_subdivisions() -> tuple[str, ...]:
    return _EXPECTED_SUBDIVISIONS
