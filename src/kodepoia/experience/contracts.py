from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

SCHEMA_NAME = "kodepoia.experience.record"
SCHEMA_VERSION = 1
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class ExperienceContractError(ValueError):
    """Base error for R15 experience-contract violations."""


class InvalidTransition(ExperienceContractError):
    """Raised when an experience state transition is not allowed."""


class EligibilityDenied(ExperienceContractError):
    """Raised when a record cannot cross the training-data trust boundary."""


class WorkspaceMismatch(ExperienceContractError):
    """Raised when content is referenced from another workspace."""


class ExperienceState(StrEnum):
    OBSERVED = "observed"
    ELIGIBLE = "eligible"
    SANITIZED = "sanitized"
    CURATED = "curated"
    DATASET_INCLUDED = "dataset_included"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    REVOKED = "revoked"
    EXPIRED = "expired"


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    UNKNOWN = "unknown"
    REVIEW = "review"


class SanitizationStatus(StrEnum):
    NOT_RUN = "not_run"
    PASSED = "passed"
    BLOCKED = "blocked"


class OutcomeLabel(StrEnum):
    UNKNOWN = "unknown"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CORRECTED = "corrected"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ExperienceId:
    value: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"exp_[0-9a-f]{64}", self.value):
            raise ExperienceContractError("ExperienceId must be exp_<64 lowercase hex chars>")

    @classmethod
    def derive(cls, *, workspace_id: str, source_id: str, origin_digest: str) -> ExperienceId:
        _require_safe_id("workspace_id", workspace_id)
        _require_safe_id("source_id", source_id)
        _require_digest("origin_digest", origin_digest)
        payload = f"{workspace_id}\0{source_id}\0{origin_digest}".encode()
        return cls("exp_" + hashlib.sha256(payload).hexdigest())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ContentRef:
    workspace_id: str
    storage_key: str
    sha256: str
    byte_length: int
    media_type: str = "text/plain"

    def __post_init__(self) -> None:
        _require_safe_id("workspace_id", self.workspace_id)
        _require_digest("sha256", self.sha256)
        if not self.storage_key or self.storage_key.startswith(("/", "\\")):
            raise ExperienceContractError("storage_key must be a non-empty governed relative key")
        parts = self.storage_key.replace("\\", "/").split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise ExperienceContractError("storage_key must not contain empty/dot/traversal segments")
        if ":" in parts[0]:
            raise ExperienceContractError("storage_key must not be drive-qualified")
        if self.byte_length < 0:
            raise ExperienceContractError("byte_length must be >= 0")
        if not self.media_type or any(ch in self.media_type for ch in "\r\n"):
            raise ExperienceContractError("media_type must be a single non-empty line")

    def assert_workspace(self, workspace_id: str) -> None:
        if self.workspace_id != workspace_id:
            raise WorkspaceMismatch(
                f"content workspace {self.workspace_id!r} does not match record workspace {workspace_id!r}"
            )

    def public_descriptor(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "sha256": self.sha256,
            "byte_length": self.byte_length,
            "media_type": self.media_type,
        }

    def canonical_descriptor(self) -> dict[str, Any]:
        return {**self.public_descriptor(), "storage_key": self.storage_key}


@dataclass(frozen=True, slots=True)
class TrainingAuthorization:
    """Independent source decisions required before training eligibility.

    Sanitization is deliberately separate: redacting content cannot turn a denied,
    unknown or review-only source/consent/provenance/licence/privacy decision into ALLOW.
    """

    source_scope: PolicyDecision = PolicyDecision.UNKNOWN
    consent: PolicyDecision = PolicyDecision.UNKNOWN
    provenance: PolicyDecision = PolicyDecision.UNKNOWN
    license: PolicyDecision = PolicyDecision.UNKNOWN
    privacy: PolicyDecision = PolicyDecision.UNKNOWN

    def blockers(self) -> tuple[str, ...]:
        fields = ("source_scope", "consent", "provenance", "license", "privacy")
        return tuple(name for name in fields if getattr(self, name) is not PolicyDecision.ALLOW)

    def is_allowed(self) -> bool:
        return not self.blockers()


@dataclass(frozen=True, slots=True)
class ProvenanceDescriptor:
    source_type: str
    source_id: str
    origin_digest: str
    project_scope: str
    license_expression: str | None = None

    def __post_init__(self) -> None:
        _require_safe_id("source_type", self.source_type)
        _require_safe_id("source_id", self.source_id)
        _require_safe_id("project_scope", self.project_scope)
        _require_digest("origin_digest", self.origin_digest)
        if self.license_expression is not None:
            value = self.license_expression.strip()
            if not value or "\n" in value or "\r" in value:
                raise ExperienceContractError("license_expression must be a non-empty single line")


@dataclass(frozen=True, slots=True)
class TransformationRef:
    transformation_id: str
    input_digest: str
    output_digest: str
    policy_digest: str

    def __post_init__(self) -> None:
        _require_safe_id("transformation_id", self.transformation_id)
        for name in ("input_digest", "output_digest", "policy_digest"):
            _require_digest(name, getattr(self, name))


@dataclass(frozen=True, slots=True)
class SanitizationEvidence:
    status: SanitizationStatus = SanitizationStatus.NOT_RUN
    sanitizer_digest: str | None = None
    categories: tuple[str, ...] = ()
    finding_count: int = 0

    def __post_init__(self) -> None:
        if self.sanitizer_digest is not None:
            _require_digest("sanitizer_digest", self.sanitizer_digest)
        if self.finding_count < 0:
            raise ExperienceContractError("finding_count must be >= 0")
        for category in self.categories:
            _require_safe_id("sanitization category", category)
        if self.status is SanitizationStatus.PASSED and self.sanitizer_digest is None:
            raise ExperienceContractError("PASSED sanitization requires sanitizer_digest")
        if self.status is SanitizationStatus.NOT_RUN and self.finding_count:
            raise ExperienceContractError("NOT_RUN sanitization cannot report findings")


@dataclass(frozen=True, slots=True)
class ExperienceRecord:
    experience_id: ExperienceId
    workspace_id: str
    project_id: str
    task_label: str
    domain_label: str
    state: ExperienceState
    outcome: OutcomeLabel
    content: ContentRef
    provenance: ProvenanceDescriptor
    authorization: TrainingAuthorization = field(default_factory=TrainingAuthorization)
    sanitization: SanitizationEvidence = field(default_factory=SanitizationEvidence)
    benchmark_protected: bool = False
    transformations: tuple[TransformationRef, ...] = ()
    schema: str = SCHEMA_NAME
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_safe_id("workspace_id", self.workspace_id)
        _require_safe_id("project_id", self.project_id)
        _require_safe_id("task_label", self.task_label)
        _require_safe_id("domain_label", self.domain_label)
        self.content.assert_workspace(self.workspace_id)
        if self.provenance.project_scope != self.project_id:
            raise ExperienceContractError("provenance project_scope must match project_id")
        if self.schema != SCHEMA_NAME or self.schema_version != SCHEMA_VERSION:
            raise ExperienceContractError("unsupported experience schema/version")
        self._validate_state_invariants()

    def _validate_state_invariants(self) -> None:
        if self.state in {
            ExperienceState.ELIGIBLE,
            ExperienceState.SANITIZED,
            ExperienceState.CURATED,
            ExperienceState.DATASET_INCLUDED,
        }:
            self.assert_training_source_allowed()
        if self.state in {
            ExperienceState.SANITIZED,
            ExperienceState.CURATED,
            ExperienceState.DATASET_INCLUDED,
        } and self.sanitization.status is not SanitizationStatus.PASSED:
            raise EligibilityDenied(f"{self.state.value} requires PASSED sanitization")
        if self.state is ExperienceState.DATASET_INCLUDED and self.benchmark_protected:
            raise EligibilityDenied("benchmark-protected content cannot enter a training dataset")

    def assert_training_source_allowed(self) -> None:
        blockers = self.authorization.blockers()
        if blockers:
            raise EligibilityDenied("training authorization is not fully allowed: " + ", ".join(blockers))
        if self.benchmark_protected:
            raise EligibilityDenied("benchmark-protected content is not training-eligible")

    def to_dict(self, *, redacted: bool = False) -> dict[str, Any]:
        content = self.content.public_descriptor() if redacted else self.content.canonical_descriptor()
        return {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "experience_id": self.experience_id.value,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "task_label": self.task_label,
            "domain_label": self.domain_label,
            "state": self.state.value,
            "outcome": self.outcome.value,
            "content": content,
            "provenance": {
                "source_type": self.provenance.source_type,
                "source_id": self.provenance.source_id,
                "origin_digest": self.provenance.origin_digest,
                "project_scope": self.provenance.project_scope,
                "license_expression": self.provenance.license_expression,
            },
            "authorization": {
                "source_scope": self.authorization.source_scope.value,
                "consent": self.authorization.consent.value,
                "provenance": self.authorization.provenance.value,
                "license": self.authorization.license.value,
                "privacy": self.authorization.privacy.value,
            },
            "sanitization": {
                "status": self.sanitization.status.value,
                "sanitizer_digest": self.sanitization.sanitizer_digest,
                "categories": list(self.sanitization.categories),
                "finding_count": self.sanitization.finding_count,
            },
            "benchmark_protected": self.benchmark_protected,
            "transformations": [
                {
                    "transformation_id": item.transformation_id,
                    "input_digest": item.input_digest,
                    "output_digest": item.output_digest,
                    "policy_digest": item.policy_digest,
                }
                for item in self.transformations
            ],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(redacted=False), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    def contract_digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def audit_summary(self) -> dict[str, Any]:
        """Return safe metadata only; never raw content or the governed storage key."""
        return {
            "experience_id": self.experience_id.value,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "state": self.state.value,
            "outcome": self.outcome.value,
            "content": self.content.public_descriptor(),
            "authorization_blockers": list(self.authorization.blockers()),
            "sanitization_status": self.sanitization.status.value,
            "sanitization_categories": list(self.sanitization.categories),
            "sanitization_finding_count": self.sanitization.finding_count,
            "benchmark_protected": self.benchmark_protected,
            "contract_digest": self.contract_digest(),
        }


_ALLOWED_TRANSITIONS: dict[ExperienceState, frozenset[ExperienceState]] = {
    ExperienceState.OBSERVED: frozenset(
        {ExperienceState.ELIGIBLE, ExperienceState.REJECTED, ExperienceState.QUARANTINED, ExperienceState.EXPIRED}
    ),
    ExperienceState.ELIGIBLE: frozenset(
        {
            ExperienceState.SANITIZED,
            ExperienceState.REJECTED,
            ExperienceState.QUARANTINED,
            ExperienceState.REVOKED,
            ExperienceState.EXPIRED,
        }
    ),
    ExperienceState.SANITIZED: frozenset(
        {
            ExperienceState.CURATED,
            ExperienceState.REJECTED,
            ExperienceState.QUARANTINED,
            ExperienceState.REVOKED,
            ExperienceState.EXPIRED,
        }
    ),
    ExperienceState.CURATED: frozenset(
        {
            ExperienceState.DATASET_INCLUDED,
            ExperienceState.REJECTED,
            ExperienceState.QUARANTINED,
            ExperienceState.REVOKED,
            ExperienceState.EXPIRED,
        }
    ),
    ExperienceState.DATASET_INCLUDED: frozenset({ExperienceState.REVOKED, ExperienceState.EXPIRED}),
    ExperienceState.REJECTED: frozenset(),
    ExperienceState.QUARANTINED: frozenset(),
    ExperienceState.REVOKED: frozenset(),
    ExperienceState.EXPIRED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class TransitionResult:
    record: ExperienceRecord
    audit_details: dict[str, Any]


def transition_experience(
    record: ExperienceRecord,
    target: ExperienceState,
    *,
    actor: str,
    reason: str,
) -> TransitionResult:
    actor = actor.strip()
    reason = reason.strip()
    if not actor:
        raise InvalidTransition("transition actor is required")
    if not reason:
        raise InvalidTransition("transition reason is required")
    if target not in _ALLOWED_TRANSITIONS[record.state]:
        raise InvalidTransition(f"transition {record.state.value}->{target.value} is not allowed")

    if target in {
        ExperienceState.ELIGIBLE,
        ExperienceState.SANITIZED,
        ExperienceState.CURATED,
        ExperienceState.DATASET_INCLUDED,
    }:
        record.assert_training_source_allowed()
    if target in {
        ExperienceState.SANITIZED,
        ExperienceState.CURATED,
        ExperienceState.DATASET_INCLUDED,
    } and record.sanitization.status is not SanitizationStatus.PASSED:
        raise EligibilityDenied(f"{target.value} requires PASSED sanitization")

    updated = replace(record, state=target)
    return TransitionResult(
        record=updated,
        audit_details={
            "experience_id": record.experience_id.value,
            "from_state": record.state.value,
            "to_state": target.value,
            "actor": actor,
            "reason": reason,
            "record_digest": updated.contract_digest(),
        },
    )


@runtime_checkable
class ExperienceRegistry(Protocol):
    def get(self, experience_id: ExperienceId) -> ExperienceRecord | None: ...

    def save(self, record: ExperienceRecord) -> None: ...


@runtime_checkable
class ExperienceContentStore(Protocol):
    def exists(self, ref: ContentRef) -> bool: ...

    def verify_digest(self, ref: ContentRef) -> bool: ...


def _require_digest(name: str, value: str) -> None:
    if not _HEX64.fullmatch(value):
        raise ExperienceContractError(f"{name} must be 64 lowercase hex chars")


def _require_safe_id(name: str, value: str) -> None:
    if not _SAFE_ID.fullmatch(value):
        raise ExperienceContractError(f"{name} must be a stable non-empty safe identifier")
