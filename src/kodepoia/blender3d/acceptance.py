from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from .serialization import canonical_json_bytes

R10_INTEGRATION_SCHEMA_VERSION = 1
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_SUBDIVISIONS = tuple(f"R10.{index}" for index in range(1, 13))
_EXPECTED_PRIOR_PHASES = ("R7", "R8", "R9")
_REQUIRED_LOCAL = ("R10.2", "R10.10")
_RUNTIME_POLICY = {
    "blender": {
        "major": 5,
        "minor": 2,
        "autoexec_disabled": True,
        "offline_mode": True,
    },
    "godot": {"major": 4, "minor": 7},
}


class R10IntegrationStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"


class R10ManualState(StrEnum):
    NONE = "none"
    REQUIRED_SATISFIED = "required_satisfied"
    CONDITIONAL_NOT_TRIGGERED = "conditional_not_triggered"
    CONDITIONAL_SATISFIED = "conditional_satisfied"
    REQUIRED_UNSATISFIED = "required_unsatisfied"
    CONDITIONAL_TRIGGERED_UNSATISFIED = "conditional_triggered_unsatisfied"

    @property
    def satisfied(self) -> bool:
        return self in {
            R10ManualState.NONE,
            R10ManualState.REQUIRED_SATISFIED,
            R10ManualState.CONDITIONAL_NOT_TRIGGERED,
            R10ManualState.CONDITIONAL_SATISFIED,
        }


def _require_sha256(value: str, field_name: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be lowercase SHA-256 hex")


def _require_sha40(value: str, field_name: str) -> None:
    if not _SHA40_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase 40-hex commit SHA")


def _file_identity(data: bytes) -> tuple[str, int]:
    if not isinstance(data, bytes):
        raise TypeError("Repository evidence loader must return bytes")
    return hashlib.sha256(data).hexdigest(), len(data)


@dataclass(frozen=True, slots=True)
class R10LocalEvidenceBinding:
    subdivision: str
    source: str
    sha256: str
    bytes: int
    source_sha: str
    blender_version_prefix: str = "5.2."
    godot_major: int | None = None
    godot_minor: int | None = None

    def __post_init__(self) -> None:
        if self.subdivision not in _REQUIRED_LOCAL:
            raise ValueError("Only R10.2 and R10.10 are required local evidence bindings")
        expected = f"docs/roadmap/R10_{self.subdivision.split('.')[1]}_LOCAL_ACCEPTANCE.json"
        if self.source != expected:
            raise ValueError(
                f"{self.subdivision} must use canonical local evidence {expected}"
            )
        _require_sha256(self.sha256, "local evidence sha256")
        if self.bytes < 1:
            raise ValueError("local evidence byte length must be positive")
        _require_sha40(self.source_sha, "local evidence source_sha")
        if not self.blender_version_prefix.startswith("5.2."):
            raise ValueError("R10 integrated acceptance is frozen to Blender 5.2.x")
        if (self.godot_major is None) != (self.godot_minor is None):
            raise ValueError("Godot major/minor must be provided together")
        if self.subdivision == "R10.10" and (
            self.godot_major,
            self.godot_minor,
        ) != (4, 7):
            raise ValueError("R10.10 required local evidence must bind Godot 4.7")

    def to_dict(self) -> dict[str, Any]:
        return {
            "subdivision": self.subdivision,
            "source": self.source,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "source_sha": self.source_sha,
            "blender_version_prefix": self.blender_version_prefix,
            "godot_major": self.godot_major,
            "godot_minor": self.godot_minor,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "R10LocalEvidenceBinding":
        return cls(
            subdivision=str(payload["subdivision"]),
            source=str(payload["source"]),
            sha256=str(payload["sha256"]),
            bytes=int(payload["bytes"]),
            source_sha=str(payload["source_sha"]),
            blender_version_prefix=str(payload.get("blender_version_prefix", "")),
            godot_major=(
                None if payload.get("godot_major") is None else int(payload["godot_major"])
            ),
            godot_minor=(
                None if payload.get("godot_minor") is None else int(payload["godot_minor"])
            ),
        )


@dataclass(frozen=True, slots=True)
class R10SubdivisionEvidence:
    subdivision: str
    source: str
    sha256: str
    bytes: int
    accepted_head: str
    manual_state: R10ManualState
    manual_reason: str

    def __post_init__(self) -> None:
        if self.subdivision not in _EXPECTED_SUBDIVISIONS:
            raise ValueError(f"Unsupported R10 subdivision: {self.subdivision}")
        expected = f"docs/roadmap/R10_{self.subdivision.split('.')[1]}_ACCEPTANCE.md"
        if self.source != expected:
            raise ValueError(f"{self.subdivision} must use canonical source {expected}")
        _require_sha256(self.sha256, "subdivision evidence sha256")
        if self.bytes < 1:
            raise ValueError("subdivision evidence byte length must be positive")
        _require_sha40(self.accepted_head, "accepted_head")
        if not self.manual_reason.strip():
            raise ValueError("manual_reason must be explicit")

    @property
    def manual_satisfied(self) -> bool:
        return self.manual_state.satisfied

    def to_dict(self) -> dict[str, Any]:
        return {
            "subdivision": self.subdivision,
            "source": self.source,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "accepted_head": self.accepted_head,
            "manual_state": self.manual_state.value,
            "manual_reason": self.manual_reason,
            "manual_satisfied": self.manual_satisfied,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "R10SubdivisionEvidence":
        item = cls(
            subdivision=str(payload["subdivision"]),
            source=str(payload["source"]),
            sha256=str(payload["sha256"]),
            bytes=int(payload["bytes"]),
            accepted_head=str(payload["accepted_head"]),
            manual_state=R10ManualState(payload["manual_state"]),
            manual_reason=str(payload["manual_reason"]),
        )
        if bool(payload.get("manual_satisfied", False)) != item.manual_satisfied:
            raise ValueError("manual_satisfied does not match manual_state")
        return item


@dataclass(frozen=True, slots=True)
class PriorPhaseEvidence:
    phase: str
    source: str
    sha256: str
    bytes: int
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.phase not in _EXPECTED_PRIOR_PHASES:
            raise ValueError(f"Unsupported prior phase: {self.phase}")
        expected = f"docs/roadmap/{self.phase}_INTEGRATED_ACCEPTANCE.json"
        if self.source != expected:
            raise ValueError(f"{self.phase} must use canonical integrated report {expected}")
        _require_sha256(self.sha256, "prior phase file sha256")
        _require_sha256(self.evidence_sha256, "prior phase evidence_sha256")
        if self.bytes < 1:
            raise ValueError("prior phase evidence byte length must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "source": self.source,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "evidence_sha256": self.evidence_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PriorPhaseEvidence":
        return cls(
            phase=str(payload["phase"]),
            source=str(payload["source"]),
            sha256=str(payload["sha256"]),
            bytes=int(payload["bytes"]),
            evidence_sha256=str(payload["evidence_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class R10IntegrationReport:
    generated_at: str
    source_sha: str
    subdivisions: tuple[R10SubdivisionEvidence, ...]
    local_evidence: tuple[R10LocalEvidenceBinding, ...]
    prior_phases: tuple[PriorPhaseEvidence, ...]
    status: R10IntegrationStatus
    blockers: tuple[str, ...] = ()
    runtime_policy: Mapping[str, Any] = field(default_factory=lambda: dict(_RUNTIME_POLICY))
    schema_version: int = R10_INTEGRATION_SCHEMA_VERSION
    evidence_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != R10_INTEGRATION_SCHEMA_VERSION:
            raise ValueError("Unsupported R10 integration schema version")
        if not self.generated_at.strip():
            raise ValueError("generated_at must not be empty")
        _require_sha40(self.source_sha, "source_sha")
        if tuple(item.subdivision for item in self.subdivisions) != _EXPECTED_SUBDIVISIONS:
            raise ValueError(
                "R10 integration subdivisions must contain R10.1 through R10.12 in order"
            )
        if tuple(item.subdivision for item in self.local_evidence) != _REQUIRED_LOCAL:
            raise ValueError("R10 required local evidence must contain R10.2 then R10.10")
        if tuple(item.phase for item in self.prior_phases) != _EXPECTED_PRIOR_PHASES:
            raise ValueError("Prior integrated evidence must contain R7, R8 and R9 in order")
        if dict(self.runtime_policy) != _RUNTIME_POLICY:
            raise ValueError(
                "R10 runtime policy must remain frozen to Blender 5.2.x and Godot 4.7"
            )
        if len(set(self.blockers)) != len(self.blockers) or any(
            not item.strip() for item in self.blockers
        ):
            raise ValueError("blockers must be unique non-empty strings")
        derived = self.derived_blockers()
        if self.status is R10IntegrationStatus.PASS and (self.blockers or derived):
            raise ValueError("Passing R10 integration evidence cannot contain blockers")
        if self.status is R10IntegrationStatus.FAIL and not (self.blockers or derived):
            raise ValueError("Failing R10 integration evidence requires a blocker")
        if self.subdivisions[-1].accepted_head != self.source_sha:
            raise ValueError("R10.12 accepted head must equal integration source_sha")
        object.__setattr__(
            self,
            "evidence_sha256",
            hashlib.sha256(canonical_json_bytes(self.identity_payload())).hexdigest(),
        )

    def derived_blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for item in self.subdivisions:
            if not item.manual_satisfied:
                blockers.append(f"{item.subdivision}:manual={item.manual_state.value}")
        local_by_id = {item.subdivision: item for item in self.local_evidence}
        for required in _REQUIRED_LOCAL:
            if required not in local_by_id:
                blockers.append(f"{required}:missing_required_local_evidence")
        return tuple(blockers)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_sha": self.source_sha,
            "runtime_policy": dict(self.runtime_policy),
            "subdivisions": [item.to_dict() for item in self.subdivisions],
            "local_evidence": [item.to_dict() for item in self.local_evidence],
            "prior_phases": [item.to_dict() for item in self.prior_phases],
            "status": self.status.value,
            "blockers": list(self.blockers),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.identity_payload(), "evidence_sha256": self.evidence_sha256}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "R10IntegrationReport":
        report = cls(
            generated_at=str(payload["generated_at"]),
            source_sha=str(payload["source_sha"]),
            subdivisions=tuple(
                R10SubdivisionEvidence.from_dict(item)
                for item in payload.get("subdivisions", [])
            ),
            local_evidence=tuple(
                R10LocalEvidenceBinding.from_dict(item)
                for item in payload.get("local_evidence", [])
            ),
            prior_phases=tuple(
                PriorPhaseEvidence.from_dict(item)
                for item in payload.get("prior_phases", [])
            ),
            status=R10IntegrationStatus(payload["status"]),
            blockers=tuple(str(item) for item in payload.get("blockers", [])),
            runtime_policy=payload.get("runtime_policy", {}),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("evidence_sha256", "")) != report.evidence_sha256:
            raise ValueError("R10 integration evidence digest does not match canonical content")
        return report


def build_subdivision_evidence(
    subdivision: str,
    *,
    accepted_head: str,
    manual_state: R10ManualState,
    manual_reason: str,
    canonical_bytes: bytes,
) -> R10SubdivisionEvidence:
    digest, size = _file_identity(canonical_bytes)
    return R10SubdivisionEvidence(
        subdivision=subdivision,
        source=f"docs/roadmap/R10_{subdivision.split('.')[1]}_ACCEPTANCE.md",
        sha256=digest,
        bytes=size,
        accepted_head=accepted_head,
        manual_state=manual_state,
        manual_reason=manual_reason,
    )


def build_local_evidence(
    subdivision: str,
    *,
    canonical_bytes: bytes,
    godot_major: int | None = None,
    godot_minor: int | None = None,
) -> R10LocalEvidenceBinding:
    digest, size = _file_identity(canonical_bytes)
    try:
        payload = json.loads(canonical_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{subdivision} local evidence must be UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("local evidence root must be an object")
    return R10LocalEvidenceBinding(
        subdivision=subdivision,
        source=f"docs/roadmap/R10_{subdivision.split('.')[1]}_LOCAL_ACCEPTANCE.json",
        sha256=digest,
        bytes=size,
        source_sha=str(payload.get("source_sha", "")),
        blender_version_prefix="5.2.",
        godot_major=godot_major,
        godot_minor=godot_minor,
    )


def build_prior_phase_evidence(
    phase: str,
    *,
    canonical_bytes: bytes,
) -> PriorPhaseEvidence:
    digest, size = _file_identity(canonical_bytes)
    try:
        payload = json.loads(canonical_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{phase} integrated evidence must be UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("prior integrated report root must be an object")
    return PriorPhaseEvidence(
        phase=phase,
        source=f"docs/roadmap/{phase}_INTEGRATED_ACCEPTANCE.json",
        sha256=digest,
        bytes=size,
        evidence_sha256=str(payload.get("evidence_sha256", "")),
    )


def _validate_local_payload(binding: R10LocalEvidenceBinding, payload: bytes) -> None:
    observed_sha, observed_bytes = _file_identity(payload)
    if (observed_sha, observed_bytes) != (binding.sha256, binding.bytes):
        raise ValueError(f"{binding.subdivision} local evidence identity mismatch")
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{binding.subdivision} local evidence is invalid JSON") from exc
    if not isinstance(document, dict):
        raise ValueError("local evidence root must be an object")
    if document.get("status") != "pass" or document.get("blockers") != []:
        raise ValueError(f"{binding.subdivision} local evidence is not PASS")
    if document.get("source_sha") != binding.source_sha:
        raise ValueError(f"{binding.subdivision} local evidence source SHA mismatch")

    if binding.subdivision == "R10.2":
        runtime = document.get("runtime")
        policy = document.get("command_policy")
        if not isinstance(runtime, dict) or not str(runtime.get("version", "")).startswith(
            binding.blender_version_prefix
        ):
            raise ValueError("R10.2 local evidence does not bind Blender 5.2.x")
        if not isinstance(policy, dict):
            raise ValueError("R10.2 command policy is missing")
        required = {
            "background": True,
            "factory_startup": True,
            "autoexec_disabled": True,
            "offline_mode": True,
        }
        if any(policy.get(key) is not value for key, value in required.items()):
            raise ValueError("R10.2 local evidence command policy is not fail-closed")
    else:
        blender = document.get("blender")
        godot = document.get("godot")
        if not isinstance(blender, dict) or not str(blender.get("version", "")).startswith(
            binding.blender_version_prefix
        ):
            raise ValueError("R10.10 local evidence does not bind Blender 5.2.x")
        if blender.get("background") is not True or blender.get("online_access") is not False:
            raise ValueError("R10.10 Blender runtime policy is not fail-closed")
        version = godot.get("version") if isinstance(godot, dict) else None
        if not isinstance(version, dict) or (version.get("major"), version.get("minor")) != (
            binding.godot_major,
            binding.godot_minor,
        ):
            raise ValueError("R10.10 local evidence does not bind Godot 4.7")
        smoke = godot.get("semantic_smoke") if isinstance(godot, dict) else None
        if not isinstance(smoke, dict) or smoke.get("pass_marker") is not True:
            raise ValueError("R10.10 Godot semantic smoke is not PASS")


def validate_repository_evidence(
    report: R10IntegrationReport,
    read_bytes: Callable[[str], bytes],
) -> None:
    for item in report.subdivisions:
        try:
            payload = read_bytes(item.source)
        except Exception as exc:
            raise ValueError(f"Missing R10 acceptance evidence: {item.source}") from exc
        observed_sha, observed_bytes = _file_identity(payload)
        if (observed_sha, observed_bytes) != (item.sha256, item.bytes):
            raise ValueError(f"R10 acceptance identity mismatch for {item.subdivision}")
        text = payload.decode("utf-8", errors="strict")
        if item.accepted_head not in text:
            raise ValueError(
                "R10 acceptance document does not contain declared accepted head: "
                f"{item.subdivision}"
            )
        if not item.manual_satisfied:
            raise ValueError(f"R10 manual gate is not satisfied: {item.subdivision}")

    for binding in report.local_evidence:
        try:
            payload = read_bytes(binding.source)
        except Exception as exc:
            raise ValueError(f"Missing required R10 local evidence: {binding.source}") from exc
        _validate_local_payload(binding, payload)

    for item in report.prior_phases:
        try:
            payload = read_bytes(item.source)
        except Exception as exc:
            raise ValueError(f"Missing prior integrated evidence: {item.source}") from exc
        observed_sha, observed_bytes = _file_identity(payload)
        if (observed_sha, observed_bytes) != (item.sha256, item.bytes):
            raise ValueError(f"{item.phase} integrated evidence identity mismatch")
        try:
            document = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"{item.phase} integrated evidence is invalid JSON") from exc
        if not isinstance(document, dict):
            raise ValueError("prior integrated report root must be an object")
        if document.get("status") != "pass" or document.get("blockers") != []:
            raise ValueError(f"{item.phase} integrated report is not PASS")
        if document.get("evidence_sha256") != item.evidence_sha256:
            raise ValueError(f"{item.phase} integrated evidence digest mismatch")

    if report.status is not R10IntegrationStatus.PASS:
        raise ValueError("R10 integrated report is not PASS")
    if report.blockers or report.derived_blockers():
        raise ValueError("R10 integrated report contains blockers")
    if report.subdivisions[-1].accepted_head != report.source_sha:
        raise ValueError("R10.12 accepted head does not match integration source SHA")


def write_integrated_acceptance_report(path: Path, report: R10IntegrationReport) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        report.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    destination.write_bytes(payload)
    return destination


def expected_r10_subdivisions() -> tuple[str, ...]:
    return _EXPECTED_SUBDIVISIONS
