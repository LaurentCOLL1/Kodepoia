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

R11_INTEGRATION_SCHEMA_VERSION = 1
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_SUBDIVISIONS = tuple(f"R11.{index}" for index in range(1, 15))
_EXPECTED_PRIOR_PHASES = ("R7", "R8", "R9", "R10")
_REQUIRED_LOCAL = ("R11.5", "R11.9")
_CONTINUITY_SOURCE = "docs/continuity/KODEPOIA_CONTINUITY.md"

_ACCEPTED_HEADS = {
    "R11.1": "46ee14f3e94ed8c5c1cadbf139a890fab853929f",
    "R11.2": "103365dc7d5e3d725e0a9d23a839283079fe959c",
    "R11.3": "a835ab4491b5c49268ac85e389a2584ba379fcf3",
    "R11.4": "a662046c9fd38a198cc76c33b9012774f254407c",
    "R11.5": "a9862b3bf475b259fe154d1e2486116ad04602f3",
    "R11.6": "ea86762ecaa5ab16f6637701638c3461eea9d5ce",
    "R11.7": "1d2347178b804ae46e8696a8fd78e88e8cb2d84b",
    "R11.8": "26703862a91b5d6a86e83be4f0c2dfabd0541efc",
    "R11.9": "087eae19ea03dd544d75a08c1eb348fe187624c5",
    "R11.10": "5fb1b80a212880bd510977d54a570859c532c206",
    "R11.11": "38dc7dce1bf288b61eabfa3b174add11ade4ae49",
    "R11.12": "66ccd03bf486ac325ee2fba7133a6fc2a9c244b0",
    "R11.13": "79a891eaede7e5ecf7d8daf35846b20b1d3d02f9",
}


class R11IntegrationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"


class R11ManualState(StrEnum):
    NONE = "none"
    REQUIRED_SATISFIED = "required_satisfied"
    CONDITIONAL_NOT_TRIGGERED = "conditional_not_triggered"
    CONDITIONAL_SATISFIED = "conditional_satisfied"
    REQUIRED_UNSATISFIED = "required_unsatisfied"
    CONDITIONAL_TRIGGERED_UNSATISFIED = "conditional_triggered_unsatisfied"

    @property
    def satisfied(self) -> bool:
        return self in {
            R11ManualState.NONE,
            R11ManualState.REQUIRED_SATISFIED,
            R11ManualState.CONDITIONAL_NOT_TRIGGERED,
            R11ManualState.CONDITIONAL_SATISFIED,
        }


_MANUAL_STATES = {
    "R11.1": R11ManualState.NONE,
    "R11.2": R11ManualState.CONDITIONAL_NOT_TRIGGERED,
    "R11.3": R11ManualState.NONE,
    "R11.4": R11ManualState.NONE,
    "R11.5": R11ManualState.REQUIRED_SATISFIED,
    "R11.6": R11ManualState.CONDITIONAL_NOT_TRIGGERED,
    "R11.7": R11ManualState.CONDITIONAL_NOT_TRIGGERED,
    "R11.8": R11ManualState.NONE,
    "R11.9": R11ManualState.REQUIRED_SATISFIED,
    "R11.10": R11ManualState.NONE,
    "R11.11": R11ManualState.NONE,
    "R11.12": R11ManualState.CONDITIONAL_NOT_TRIGGERED,
    "R11.13": R11ManualState.NONE,
    "R11.14": R11ManualState.CONDITIONAL_NOT_TRIGGERED,
}


def _require_sha40(value: str, name: str) -> None:
    if not _SHA40_RE.fullmatch(value):
        raise ValueError(f"{name} must be lowercase 40-hex commit SHA")


def _require_sha256(value: str, name: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


def _identity(data: bytes) -> tuple[str, int]:
    if not isinstance(data, bytes):
        raise TypeError("Repository evidence loader must return bytes")
    return hashlib.sha256(data).hexdigest(), len(data)


def _json_object(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} must be valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} root must be an object")
    return value


def _recompute_evidence_digest(payload: Mapping[str, Any]) -> str:
    semantic = dict(payload)
    semantic.pop("evidence_digest", None)
    return hashlib.sha256(canonical_json_bytes(semantic)).hexdigest()


@dataclass(frozen=True, slots=True)
class FileBinding:
    source: str
    sha256: str
    bytes: int

    def __post_init__(self) -> None:
        if not self.source or self.source.startswith("/") or ".." in Path(self.source).parts:
            raise ValueError("evidence source must be a safe repository-relative path")
        _require_sha256(self.sha256, "file sha256")
        if self.bytes < 1:
            raise ValueError("evidence byte length must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "sha256": self.sha256, "bytes": self.bytes}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "FileBinding":
        return cls(str(value["source"]), str(value["sha256"]), int(value["bytes"]))


@dataclass(frozen=True, slots=True)
class SubdivisionBinding(FileBinding):
    subdivision: str
    accepted_head: str
    manual_state: R11ManualState

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.subdivision not in _EXPECTED_SUBDIVISIONS:
            raise ValueError(f"Unsupported R11 subdivision: {self.subdivision}")
        expected = f"docs/roadmap/R11_{self.subdivision.split('.')[1]}_ACCEPTANCE.md"
        if self.source != expected:
            raise ValueError(f"{self.subdivision} must bind {expected}")
        _require_sha40(self.accepted_head, "accepted_head")
        if self.subdivision != "R11.14" and self.accepted_head != _ACCEPTED_HEADS[self.subdivision]:
            raise ValueError(f"Historical accepted head drift for {self.subdivision}")
        if self.manual_state is not _MANUAL_STATES[self.subdivision]:
            raise ValueError(f"Manual state drift for {self.subdivision}")

    @property
    def manual_satisfied(self) -> bool:
        return self.manual_state.satisfied

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "subdivision": self.subdivision,
            "accepted_head": self.accepted_head,
            "manual_state": self.manual_state.value,
            "manual_satisfied": self.manual_satisfied,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SubdivisionBinding":
        item = cls(
            source=str(value["source"]),
            sha256=str(value["sha256"]),
            bytes=int(value["bytes"]),
            subdivision=str(value["subdivision"]),
            accepted_head=str(value["accepted_head"]),
            manual_state=R11ManualState(value["manual_state"]),
        )
        if bool(value.get("manual_satisfied")) is not item.manual_satisfied:
            raise ValueError("manual_satisfied does not match manual_state")
        return item


@dataclass(frozen=True, slots=True)
class LocalEvidenceBinding(FileBinding):
    subdivision: str
    source_sha: str
    evidence_digest: str

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.subdivision not in _REQUIRED_LOCAL:
            raise ValueError("Only R11.5 and R11.9 are required local bindings")
        expected = f"docs/roadmap/R11_{self.subdivision.split('.')[1]}_LOCAL_ACCEPTANCE.json"
        if self.source != expected:
            raise ValueError(f"{self.subdivision} must bind {expected}")
        _require_sha40(self.source_sha, "local source_sha")
        _require_sha256(self.evidence_digest, "local evidence digest")
        if self.source_sha != _ACCEPTED_HEADS[self.subdivision]:
            raise ValueError(f"{self.subdivision} local source SHA drift")

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "subdivision": self.subdivision,
            "source_sha": self.source_sha,
            "evidence_digest": self.evidence_digest,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "LocalEvidenceBinding":
        return cls(
            source=str(value["source"]),
            sha256=str(value["sha256"]),
            bytes=int(value["bytes"]),
            subdivision=str(value["subdivision"]),
            source_sha=str(value["source_sha"]),
            evidence_digest=str(value["evidence_digest"]),
        )


@dataclass(frozen=True, slots=True)
class PriorPhaseBinding(FileBinding):
    phase: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.phase not in _EXPECTED_PRIOR_PHASES:
            raise ValueError(f"Unsupported prior phase {self.phase}")
        if self.source != f"docs/roadmap/{self.phase}_INTEGRATED_ACCEPTANCE.json":
            raise ValueError("prior phase source is not canonical")
        _require_sha256(self.evidence_sha256, "prior evidence digest")

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "phase": self.phase, "evidence_sha256": self.evidence_sha256}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PriorPhaseBinding":
        return cls(
            source=str(value["source"]),
            sha256=str(value["sha256"]),
            bytes=int(value["bytes"]),
            phase=str(value["phase"]),
            evidence_sha256=str(value["evidence_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class R11IntegratedReport:
    generated_at: str
    source_sha: str
    continuity: FileBinding
    subdivisions: tuple[SubdivisionBinding, ...]
    local_evidence: tuple[LocalEvidenceBinding, ...]
    prior_phases: tuple[PriorPhaseBinding, ...]
    status: R11IntegrationStatus
    blockers: tuple[str, ...] = ()
    schema_version: int = R11_INTEGRATION_SCHEMA_VERSION
    evidence_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("Unsupported R11 integrated schema version")
        if not self.generated_at.strip():
            raise ValueError("generated_at is required")
        _require_sha40(self.source_sha, "source_sha")
        if self.continuity.source != _CONTINUITY_SOURCE:
            raise ValueError("R11 report must bind canonical continuity source")
        if tuple(item.subdivision for item in self.subdivisions) != _EXPECTED_SUBDIVISIONS:
            raise ValueError("R11 report must contain R11.1 through R11.14 in order")
        if tuple(item.subdivision for item in self.local_evidence) != _REQUIRED_LOCAL:
            raise ValueError("R11 report must bind R11.5 then R11.9 local evidence")
        if tuple(item.phase for item in self.prior_phases) != _EXPECTED_PRIOR_PHASES:
            raise ValueError("R11 report must bind R7, R8, R9 and R10 in order")
        if self.subdivisions[-1].accepted_head != self.source_sha:
            raise ValueError("R11.14 accepted head must equal report source_sha")
        if len(set(self.blockers)) != len(self.blockers) or any(not item.strip() for item in self.blockers):
            raise ValueError("blockers must be unique non-empty strings")
        derived = self.derived_blockers()
        if self.status is R11IntegrationStatus.PASS and (self.blockers or derived):
            raise ValueError("PASS report cannot contain blockers")
        if self.status is R11IntegrationStatus.FAIL and not (self.blockers or derived):
            raise ValueError("FAIL report requires a blocker")
        object.__setattr__(self, "evidence_sha256", hashlib.sha256(canonical_json_bytes(self.semantic_payload())).hexdigest())

    def derived_blockers(self) -> tuple[str, ...]:
        return tuple(
            f"{item.subdivision}:manual={item.manual_state.value}"
            for item in self.subdivisions
            if not item.manual_satisfied
        )

    def semantic_payload(self) -> dict[str, Any]:
        # generated_at is intentionally excluded from semantic identity.
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "continuity": self.continuity.to_dict(),
            "subdivisions": [item.to_dict() for item in self.subdivisions],
            "local_evidence": [item.to_dict() for item in self.local_evidence],
            "prior_phases": [item.to_dict() for item in self.prior_phases],
            "status": self.status.value,
            "blockers": list(self.blockers),
        }

    def to_dict(self) -> dict[str, Any]:
        return {"generated_at": self.generated_at, **self.semantic_payload(), "evidence_sha256": self.evidence_sha256}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "R11IntegratedReport":
        report = cls(
            generated_at=str(value["generated_at"]),
            source_sha=str(value["source_sha"]),
            continuity=FileBinding.from_dict(value["continuity"]),
            subdivisions=tuple(SubdivisionBinding.from_dict(item) for item in value.get("subdivisions", [])),
            local_evidence=tuple(LocalEvidenceBinding.from_dict(item) for item in value.get("local_evidence", [])),
            prior_phases=tuple(PriorPhaseBinding.from_dict(item) for item in value.get("prior_phases", [])),
            status=R11IntegrationStatus(value["status"]),
            blockers=tuple(str(item) for item in value.get("blockers", [])),
            schema_version=int(value.get("schema_version", 0)),
        )
        if str(value.get("evidence_sha256", "")) != report.evidence_sha256:
            raise ValueError("R11 integrated semantic digest mismatch")
        return report


def _binding(source: str, data: bytes) -> FileBinding:
    digest, size = _identity(data)
    return FileBinding(source, digest, size)


def _subdivision_binding(subdivision: str, data: bytes, *, source_sha: str) -> SubdivisionBinding:
    source = f"docs/roadmap/R11_{subdivision.split('.')[1]}_ACCEPTANCE.md"
    digest, size = _identity(data)
    head = source_sha if subdivision == "R11.14" else _ACCEPTED_HEADS[subdivision]
    return SubdivisionBinding(source, digest, size, subdivision, head, _MANUAL_STATES[subdivision])


def _local_binding(subdivision: str, data: bytes) -> LocalEvidenceBinding:
    source = f"docs/roadmap/R11_{subdivision.split('.')[1]}_LOCAL_ACCEPTANCE.json"
    digest, size = _identity(data)
    document = _json_object(data, subdivision)
    return LocalEvidenceBinding(
        source=source,
        sha256=digest,
        bytes=size,
        subdivision=subdivision,
        source_sha=str(document.get("source_sha", "")),
        evidence_digest=str(document.get("evidence_digest", "")),
    )


def _prior_binding(phase: str, data: bytes) -> PriorPhaseBinding:
    source = f"docs/roadmap/{phase}_INTEGRATED_ACCEPTANCE.json"
    digest, size = _identity(data)
    document = _json_object(data, phase)
    return PriorPhaseBinding(source, digest, size, phase, str(document.get("evidence_sha256", "")))


def build_repository_report(*, source_sha: str, generated_at: str, read_bytes: Callable[[str], bytes]) -> R11IntegratedReport:
    _require_sha40(source_sha, "source_sha")
    subdivisions = tuple(
        _subdivision_binding(
            subdivision,
            read_bytes(f"docs/roadmap/R11_{subdivision.split('.')[1]}_ACCEPTANCE.md"),
            source_sha=source_sha,
        )
        for subdivision in _EXPECTED_SUBDIVISIONS
    )
    local = tuple(
        _local_binding(subdivision, read_bytes(f"docs/roadmap/R11_{subdivision.split('.')[1]}_LOCAL_ACCEPTANCE.json"))
        for subdivision in _REQUIRED_LOCAL
    )
    prior = tuple(
        _prior_binding(phase, read_bytes(f"docs/roadmap/{phase}_INTEGRATED_ACCEPTANCE.json"))
        for phase in _EXPECTED_PRIOR_PHASES
    )
    report = R11IntegratedReport(
        generated_at=generated_at,
        source_sha=source_sha,
        continuity=_binding(_CONTINUITY_SOURCE, read_bytes(_CONTINUITY_SOURCE)),
        subdivisions=subdivisions,
        local_evidence=local,
        prior_phases=prior,
        status=R11IntegrationStatus.PASS,
        blockers=(),
    )
    validate_repository_evidence(report, read_bytes)
    return report


def _validate_local(binding: LocalEvidenceBinding, data: bytes) -> None:
    if _identity(data) != (binding.sha256, binding.bytes):
        raise ValueError(f"{binding.subdivision} local evidence identity mismatch")
    document = _json_object(data, binding.subdivision)
    if document.get("status") != "pass" or document.get("blockers") != []:
        raise ValueError(f"{binding.subdivision} local evidence is not PASS")
    if document.get("source_sha") != binding.source_sha:
        raise ValueError(f"{binding.subdivision} local source SHA mismatch")
    if document.get("evidence_digest") != binding.evidence_digest:
        raise ValueError(f"{binding.subdivision} evidence digest field mismatch")
    if _recompute_evidence_digest(document) != binding.evidence_digest:
        raise ValueError(f"{binding.subdivision} canonical evidence digest mismatch")

    if binding.subdivision == "R11.5":
        capability = document.get("capability")
        synthesis = document.get("synthesis")
        privacy = document.get("privacy")
        approval = document.get("approval")
        if not isinstance(capability, dict) or capability.get("status") != "pass":
            raise ValueError("R11.5 capability is not PASS")
        caps = capability.get("capabilities")
        if not isinstance(caps, dict) or caps.get("network_required") is not False:
            raise ValueError("R11.5 local evidence does not prove offline capability")
        if not isinstance(synthesis, dict) or synthesis.get("status") != "pass":
            raise ValueError("R11.5 synthesis is not PASS")
        process = synthesis.get("process")
        qa = synthesis.get("qa")
        if not isinstance(process, dict) or process.get("timed_out") or process.get("cancelled"):
            raise ValueError("R11.5 synthesis process did not complete cleanly")
        if process.get("text_passed_via_argv") is not False or process.get("ephemeral_input_deleted") is not True:
            raise ValueError("R11.5 privacy-safe text transport invariant failed")
        if not isinstance(qa, dict) or qa.get("state") != "PASS" or qa.get("blockers") != []:
            raise ValueError("R11.5 speech QA is not PASS")
        if not isinstance(privacy, dict) or any(privacy.get(key) is not False for key in ("audio_retained", "network_download_performed_by_collector", "private_recording_used", "voice_clone_used")):
            raise ValueError("R11.5 privacy invariants failed")
        if not isinstance(approval, dict) or approval.get("license_reviewed") is not True:
            raise ValueError("R11.5 license approval is not explicit")
    else:
        runtime = document.get("runtime")
        capture = document.get("capture")
        fixture = document.get("fixture")
        if not isinstance(runtime, dict) or runtime.get("godot_compatible_47") is not True:
            raise ValueError("R11.9 local evidence does not bind compatible Godot 4.7")
        if not str(runtime.get("godot_version", "")).startswith("4.7."):
            raise ValueError("R11.9 Godot version drift")
        if not isinstance(fixture, dict) or fixture.get("kind") != "repository_synthetic":
            raise ValueError("R11.9 local fixture is not repository synthetic")
        if not isinstance(capture, dict) or capture.get("status") != "pass":
            raise ValueError("R11.9 capture is not PASS")
        if capture.get("reported_frames") != capture.get("expected_frames"):
            raise ValueError("R11.9 frame count mismatch")
        if float(capture.get("av_sync_error_seconds", 1e9)) > float(capture.get("av_sync_limit_seconds", -1)):
            raise ValueError("R11.9 A/V sync exceeds accepted bound")


def validate_repository_evidence(report: R11IntegratedReport, read_bytes: Callable[[str], bytes]) -> None:
    continuity = read_bytes(report.continuity.source)
    observed = _identity(continuity)
    if observed != (report.continuity.sha256, report.continuity.bytes):
        # The only accepted post-report difference is the final continuity-only
        # normalization. It must explicitly bind this report's semantic digest.
        text = continuity.decode("utf-8", errors="strict")
        if "R11.14" not in text or "COMPLETE + NORMALIZED" not in text or report.evidence_sha256 not in text:
            raise ValueError("R11 continuity evidence identity mismatch")

    continuity_text = continuity.decode("utf-8", errors="strict")
    for item in report.subdivisions:
        data = read_bytes(item.source)
        if _identity(data) != (item.sha256, item.bytes):
            raise ValueError(f"R11 acceptance identity mismatch for {item.subdivision}")
        text = data.decode("utf-8", errors="strict")
        if item.subdivision != "R11.14" and item.accepted_head not in text and item.accepted_head not in continuity_text:
            raise ValueError(f"Accepted head not evidenced for {item.subdivision}")
        if not item.manual_satisfied:
            raise ValueError(f"Unsatisfied manual state for {item.subdivision}")

    for item in report.local_evidence:
        _validate_local(item, read_bytes(item.source))

    for item in report.prior_phases:
        data = read_bytes(item.source)
        if _identity(data) != (item.sha256, item.bytes):
            raise ValueError(f"{item.phase} integrated report identity mismatch")
        document = _json_object(data, item.phase)
        if document.get("status") != "pass" or document.get("blockers") != []:
            raise ValueError(f"{item.phase} integrated report is not PASS")
        if document.get("evidence_sha256") != item.evidence_sha256:
            raise ValueError(f"{item.phase} integrated semantic digest mismatch")

    if report.status is not R11IntegrationStatus.PASS or report.blockers or report.derived_blockers():
        raise ValueError("R11 integrated report is not PASS")


def write_integrated_acceptance_report(path: Path, report: R11IntegratedReport) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return destination


__all__ = [
    "FileBinding",
    "LocalEvidenceBinding",
    "PriorPhaseBinding",
    "R11IntegratedReport",
    "R11IntegrationStatus",
    "R11ManualState",
    "SubdivisionBinding",
    "build_repository_report",
    "validate_repository_evidence",
    "write_integrated_acceptance_report",
]
