from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.assets.boundary import VaultBoundary
from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.experience.contracts import (
    ContentRef,
    ExperienceId,
    ExperienceRecord,
    ExperienceState,
    OutcomeLabel,
    ProvenanceDescriptor,
    SanitizationEvidence,
    TrainingAuthorization,
)

CAPTURE_SCHEMA_NAME = "kodepoia.experience.capture"
CAPTURE_SCHEMA_VERSION = 1
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CaptureDisposition(StrEnum):
    STORED = "stored"
    IDEMPOTENT = "idempotent"
    DISABLED = "disabled"
    POLICY_BLOCKED = "policy_blocked"
    OUTCOME_BLOCKED = "outcome_blocked"
    VALIDATION_BLOCKED = "validation_blocked"
    QUOTA_BLOCKED = "quota_blocked"


class CaptureError(RuntimeError):
    """Base error for governed experience capture."""


class CaptureConflict(CaptureError):
    """Raised when a replay-safe event ID is reused for different content or metadata."""


class CaptureStorageError(CaptureError):
    """Raised when governed raw storage cannot be verified safely."""


@dataclass(frozen=True, slots=True)
class CapturePolicy:
    enabled: bool = False
    opted_in_projects: tuple[str, ...] = ()
    allowed_source_types: tuple[str, ...] = ()
    allowed_media_types: tuple[str, ...] = ("text/plain", "application/json")
    max_payload_bytes: int = 256 * 1024
    max_records_per_project: int = 1_000
    max_bytes_per_project: int = 64 * 1024 * 1024
    capture_negative_outcomes: bool = False

    def __post_init__(self) -> None:
        for project_id in self.opted_in_projects:
            _require_safe_id("opted-in project", project_id)
        for source_type in self.allowed_source_types:
            _require_safe_id("allowed source type", source_type)
        if not self.allowed_media_types:
            raise ValueError("allowed_media_types must not be empty")
        for media_type in self.allowed_media_types:
            if not media_type or any(ch in media_type for ch in "\r\n"):
                raise ValueError("allowed media types must be non-empty single-line values")
        if self.max_payload_bytes <= 0:
            raise ValueError("max_payload_bytes must be > 0")
        if self.max_records_per_project <= 0:
            raise ValueError("max_records_per_project must be > 0")
        if self.max_bytes_per_project <= 0:
            raise ValueError("max_bytes_per_project must be > 0")

    def canonical(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "opted_in_projects": sorted(set(self.opted_in_projects)),
            "allowed_source_types": sorted(set(self.allowed_source_types)),
            "allowed_media_types": sorted(set(self.allowed_media_types)),
            "max_payload_bytes": self.max_payload_bytes,
            "max_records_per_project": self.max_records_per_project,
            "max_bytes_per_project": self.max_bytes_per_project,
            "capture_negative_outcomes": self.capture_negative_outcomes,
        }

    def digest(self) -> str:
        payload = json.dumps(
            self.canonical(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CorrectionProvenance:
    original_experience_id: ExperienceId
    original_workspace_id: str
    original_project_id: str
    original_content_digest: str
    evaluator_id: str

    def __post_init__(self) -> None:
        _require_safe_id("original_workspace_id", self.original_workspace_id)
        _require_safe_id("original_project_id", self.original_project_id)
        _require_digest("original_content_digest", self.original_content_digest)
        _require_safe_id("evaluator_id", self.evaluator_id)

    def canonical(self) -> dict[str, str]:
        return {
            "original_experience_id": str(self.original_experience_id),
            "original_workspace_id": self.original_workspace_id,
            "original_project_id": self.original_project_id,
            "original_content_digest": self.original_content_digest,
            "evaluator_id": self.evaluator_id,
        }


@dataclass(frozen=True, slots=True)
class ValidatedOutcome:
    event_id: str
    workspace_id: str
    project_id: str
    source_type: str
    source_id: str
    task_label: str
    domain_label: str
    action_ref: str
    result_ref: str
    validation_ref: str
    validator_id: str
    validated: bool
    outcome: OutcomeLabel
    origin_digest: str
    license_expression: str | None = None
    correction: CorrectionProvenance | None = None

    def __post_init__(self) -> None:
        for name in (
            "event_id",
            "workspace_id",
            "project_id",
            "source_type",
            "source_id",
            "task_label",
            "domain_label",
            "action_ref",
            "result_ref",
            "validation_ref",
            "validator_id",
        ):
            _require_safe_id(name, getattr(self, name))
        _require_digest("origin_digest", self.origin_digest)
        if self.outcome is OutcomeLabel.CORRECTED and self.correction is None:
            raise ValueError("corrected outcomes require correction provenance")
        if self.outcome is not OutcomeLabel.CORRECTED and self.correction is not None:
            raise ValueError("correction provenance is only valid for corrected outcomes")
        if self.correction is not None and (
            self.correction.original_workspace_id != self.workspace_id
            or self.correction.original_project_id != self.project_id
        ):
            raise ValueError("correction provenance must stay within the same workspace/project scope")


@dataclass(frozen=True, slots=True)
class CaptureSummary:
    experience_id: str
    event_id: str
    workspace_id: str
    project_id: str
    outcome: str
    state: str
    content_sha256: str
    byte_length: int
    media_type: str
    validator_id: str
    validation_ref: str
    correction_of: str | None
    policy_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "event_id": self.event_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "outcome": self.outcome,
            "state": self.state,
            "content_sha256": self.content_sha256,
            "byte_length": self.byte_length,
            "media_type": self.media_type,
            "validator_id": self.validator_id,
            "validation_ref": self.validation_ref,
            "correction_of": self.correction_of,
            "policy_digest": self.policy_digest,
        }


@dataclass(frozen=True, slots=True)
class CaptureResult:
    disposition: CaptureDisposition
    reason: str
    summary: CaptureSummary | None = None


class ExperienceCollector:
    """Governed, opt-in capture of validated terminal outcomes into raw Vault storage."""

    def __init__(
        self,
        boundary: VaultBoundary,
        *,
        policy: CapturePolicy,
        guardian: KodeGuardian,
        audit_log: AuditLog,
    ) -> None:
        self.boundary = boundary
        self.policy = policy
        self.guardian = guardian
        self.audit_log = audit_log
        self.raw_root = boundary.resolve("experience/raw")

    def capture(
        self,
        outcome: ValidatedOutcome,
        payload: bytes | str,
        *,
        actor: str,
        media_type: str = "text/plain",
    ) -> CaptureResult:
        actor = actor.strip()
        if not actor:
            raise ValueError("capture actor is required")
        if not self.policy.enabled:
            return CaptureResult(CaptureDisposition.DISABLED, "capture policy disabled")
        if outcome.project_id not in self.policy.opted_in_projects:
            return CaptureResult(CaptureDisposition.POLICY_BLOCKED, "project is not opted in")
        if outcome.source_type not in self.policy.allowed_source_types:
            return CaptureResult(CaptureDisposition.POLICY_BLOCKED, "source type is not allowed")
        if media_type not in self.policy.allowed_media_types:
            return CaptureResult(CaptureDisposition.POLICY_BLOCKED, "media type is not allowed")
        if not outcome.validated:
            return CaptureResult(
                CaptureDisposition.VALIDATION_BLOCKED,
                "terminal outcome has not been explicitly validated",
            )
        if outcome.outcome is OutcomeLabel.UNKNOWN:
            return CaptureResult(CaptureDisposition.OUTCOME_BLOCKED, "unknown outcome is not capturable")
        if (
            outcome.outcome in {OutcomeLabel.REJECTED, OutcomeLabel.FAILED}
            and not self.policy.capture_negative_outcomes
        ):
            return CaptureResult(
                CaptureDisposition.OUTCOME_BLOCKED,
                "negative outcomes require explicit diagnostic capture policy",
            )

        raw = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
        if len(raw) > self.policy.max_payload_bytes:
            return CaptureResult(
                CaptureDisposition.QUOTA_BLOCKED,
                "payload exceeds per-record byte limit",
            )
        payload_digest = hashlib.sha256(raw).hexdigest()
        event_key = self._event_key(outcome)
        scope_key = self._scope_key(outcome.workspace_id, outcome.project_id)
        record_key = f"experience/raw/scopes/{scope_key}/records/{event_key}.json"
        record_path = self.boundary.resolve(record_key)
        request_digest = self._request_digest(outcome, payload_digest, media_type)

        existing = self._load_manifest(record_path)
        if existing is not None:
            if existing["request_digest"] != request_digest:
                raise CaptureConflict("event ID replay does not match the original capture request")
            self._verify_manifest_content(existing)
            return CaptureResult(
                CaptureDisposition.IDEMPOTENT,
                "identical replay returned existing capture",
                self._summary_from_manifest(existing),
            )

        count, total_bytes = self._project_usage(outcome.workspace_id, outcome.project_id)
        if count >= self.policy.max_records_per_project:
            return self._quota_blocked(outcome, actor, "project record-count quota exceeded")
        if total_bytes + len(raw) > self.policy.max_bytes_per_project:
            return self._quota_blocked(outcome, actor, "project byte quota exceeded")

        experience_id = ExperienceId.derive(
            workspace_id=outcome.workspace_id,
            source_id=outcome.event_id,
            origin_digest=payload_digest,
        )
        object_key = (
            f"experience/raw/scopes/{scope_key}/objects/sha256/"
            f"{payload_digest[:2]}/{payload_digest}"
        )
        object_path = self.boundary.resolve(object_key)
        self._store_object(object_path, raw, payload_digest, actor)

        state = (
            ExperienceState.QUARANTINED
            if outcome.outcome in {OutcomeLabel.REJECTED, OutcomeLabel.FAILED}
            else ExperienceState.OBSERVED
        )
        record = ExperienceRecord(
            experience_id=experience_id,
            workspace_id=outcome.workspace_id,
            project_id=outcome.project_id,
            task_label=outcome.task_label,
            domain_label=outcome.domain_label,
            state=state,
            outcome=outcome.outcome,
            content=ContentRef(
                workspace_id=outcome.workspace_id,
                storage_key=object_key,
                sha256=payload_digest,
                byte_length=len(raw),
                media_type=media_type,
            ),
            provenance=ProvenanceDescriptor(
                source_type=outcome.source_type,
                source_id=outcome.source_id,
                origin_digest=outcome.origin_digest,
                project_scope=outcome.project_id,
                license_expression=outcome.license_expression,
            ),
            authorization=TrainingAuthorization(),
            sanitization=SanitizationEvidence(),
        )
        manifest = self._manifest(
            outcome=outcome,
            record=record,
            event_key=event_key,
            request_digest=request_digest,
        )
        self._authorize_write(record_path, actor)
        self._atomic_json(record_path, manifest, actor=actor, scope_key=scope_key)

        summary = self._summary_from_manifest(manifest)
        try:
            self._authorize_write(self.audit_log.path, actor)
            self.audit_log.append(
                "experience",
                "capture",
                actor,
                "stored",
                {
                    "disposition": CaptureDisposition.STORED.value,
                    **summary.to_dict(),
                },
            )
        except Exception:
            record_path.unlink(missing_ok=True)
            raise
        return CaptureResult(CaptureDisposition.STORED, "validated experience captured", summary)

    def inspect(self, *, workspace_id: str, project_id: str, event_id: str) -> CaptureSummary | None:
        for name, value in (
            ("workspace_id", workspace_id),
            ("project_id", project_id),
            ("event_id", event_id),
        ):
            _require_safe_id(name, value)
        event_key = self._event_key_parts(workspace_id, project_id, event_id)
        scope_key = self._scope_key(workspace_id, project_id)
        manifest = self._load_manifest(
            self.boundary.resolve(
                f"experience/raw/scopes/{scope_key}/records/{event_key}.json"
            )
        )
        if manifest is None:
            return None
        self._verify_manifest_content(manifest)
        return self._summary_from_manifest(manifest)

    def status(self, *, workspace_id: str, project_id: str) -> dict[str, Any]:
        _require_safe_id("workspace_id", workspace_id)
        _require_safe_id("project_id", project_id)
        count, total_bytes = self._project_usage(workspace_id, project_id)
        return {
            "enabled": self.policy.enabled,
            "project_opted_in": project_id in self.policy.opted_in_projects,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "records": count,
            "bytes": total_bytes,
            "max_records": self.policy.max_records_per_project,
            "max_bytes": self.policy.max_bytes_per_project,
            "policy_digest": self.policy.digest(),
        }

    def _quota_blocked(
        self,
        outcome: ValidatedOutcome,
        actor: str,
        reason: str,
    ) -> CaptureResult:
        self._authorize_write(self.audit_log.path, actor)
        self.audit_log.append(
            "experience",
            "capture",
            actor,
            "blocked",
            {
                "disposition": CaptureDisposition.QUOTA_BLOCKED.value,
                "workspace_id": outcome.workspace_id,
                "project_id": outcome.project_id,
                "event_id": outcome.event_id,
                "outcome": outcome.outcome.value,
                "reason": reason,
                "policy_digest": self.policy.digest(),
            },
        )
        return CaptureResult(CaptureDisposition.QUOTA_BLOCKED, reason)

    def _store_object(
        self,
        path: Path,
        raw: bytes,
        digest: str,
        actor: str,
    ) -> None:
        if path.exists():
            self._verify_object(path, digest, len(raw))
            return
        self._authorize_write(path, actor)
        scope_key = self._scope_key_from_object_path(path)
        stage = self.boundary.resolve(
            f"experience/raw/scopes/{scope_key}/.staging/{uuid.uuid4().hex}.part"
        )
        self._authorize_write(stage, actor)
        stage.parent.mkdir(parents=True, exist_ok=True)
        stage.write_bytes(raw)
        try:
            self._verify_object(stage, digest, len(raw))
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                self._verify_object(path, digest, len(raw))
            else:
                os.replace(stage, path)
                self._verify_object(path, digest, len(raw))
        finally:
            stage.unlink(missing_ok=True)

    @staticmethod
    def _verify_object(path: Path, digest: str, expected_length: int) -> None:
        data = path.read_bytes()
        if len(data) != expected_length or hashlib.sha256(data).hexdigest() != digest:
            raise CaptureStorageError("raw Vault object failed length/SHA-256 verification")

    def _atomic_json(
        self,
        path: Path,
        document: dict[str, Any],
        *,
        actor: str,
        scope_key: str,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        stage = self.boundary.resolve(
            f"experience/raw/scopes/{scope_key}/.staging/{uuid.uuid4().hex}.json"
        )
        self._authorize_write(stage, actor)
        stage.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        stage.write_text(payload + "\n", encoding="utf-8", newline="\n")
        os.replace(stage, path)

    def _project_usage(self, workspace_id: str, project_id: str) -> tuple[int, int]:
        count = 0
        total_bytes = 0
        scope_key = self._scope_key(workspace_id, project_id)
        records_root = self.boundary.resolve(
            f"experience/raw/scopes/{scope_key}/records"
        )
        for path in sorted(records_root.glob("*.json")):
            manifest = self._load_manifest(path)
            if manifest is None:
                continue
            record = manifest["record"]
            if record["workspace_id"] == workspace_id and record["project_id"] == project_id:
                count += 1
                total_bytes += int(record["content"]["byte_length"])
        return count, total_bytes

    def _load_manifest(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CaptureStorageError(f"capture manifest cannot be read safely: {path.name}") from exc
        self._validate_manifest_shape(document)
        return document

    def _validate_manifest_shape(self, document: Any) -> None:
        if not isinstance(document, dict):
            raise CaptureStorageError("capture manifest must be an object")
        required = {
            "schema",
            "schema_version",
            "event_key",
            "event_id",
            "request_digest",
            "record_digest",
            "policy_digest",
            "validator_id",
            "validation_ref",
            "action_ref",
            "result_ref",
            "correction",
            "record",
        }
        if set(document) != required:
            raise CaptureStorageError("capture manifest fields do not match schema v1")
        if (
            document["schema"] != CAPTURE_SCHEMA_NAME
            or document["schema_version"] != CAPTURE_SCHEMA_VERSION
        ):
            raise CaptureStorageError("unsupported capture manifest schema/version")
        for name in ("event_key", "request_digest", "record_digest", "policy_digest"):
            _require_digest(name, str(document[name]))
        for name in ("event_id", "validator_id", "validation_ref", "action_ref", "result_ref"):
            _require_safe_id(name, str(document[name]))
        if not isinstance(document["record"], dict):
            raise CaptureStorageError("capture manifest record must be an object")
        record = document["record"]
        for name in ("experience_id", "workspace_id", "project_id", "state", "outcome", "content"):
            if name not in record:
                raise CaptureStorageError(f"capture record is missing required field: {name}")
        _require_safe_id("workspace_id", str(record["workspace_id"]))
        _require_safe_id("project_id", str(record["project_id"]))
        if not re.fullmatch(r"exp_[0-9a-f]{64}", str(record["experience_id"])):
            raise CaptureStorageError("capture experience ID is invalid")
        if not isinstance(record["content"], dict):
            raise CaptureStorageError("capture record content must be an object")
        content = record["content"]
        for name in ("storage_key", "sha256", "byte_length", "media_type"):
            if name not in content:
                raise CaptureStorageError(f"capture content is missing required field: {name}")
        _require_digest("content sha256", str(content["sha256"]))
        if not isinstance(content["byte_length"], int) or content["byte_length"] < 0:
            raise CaptureStorageError("capture content byte_length is invalid")
        expected_event_key = self._event_key_parts(
            str(record["workspace_id"]),
            str(record["project_id"]),
            str(document["event_id"]),
        )
        if document["event_key"] != expected_event_key:
            raise CaptureStorageError("capture event key does not match its scoped identifiers")
        if self._document_digest(record) != document["record_digest"]:
            raise CaptureStorageError("capture record digest mismatch")

    def _verify_manifest_content(self, manifest: dict[str, Any]) -> None:
        record = manifest["record"]
        content = record["content"]
        storage_key = str(content["storage_key"])
        scope_key = self._scope_key(
            str(record["workspace_id"]),
            str(record["project_id"]),
        )
        expected_prefix = f"experience/raw/scopes/{scope_key}/objects/sha256/"
        if not storage_key.startswith(expected_prefix):
            raise CaptureStorageError("capture content reference crosses workspace/project scope")
        path = self.boundary.resolve(storage_key, must_exist=True)
        self._verify_object(
            path,
            str(content["sha256"]),
            int(content["byte_length"]),
        )

    @staticmethod
    def _document_digest(document: dict[str, Any]) -> str:
        canonical = json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _scope_key(workspace_id: str, project_id: str) -> str:
        payload = f"{workspace_id}\0{project_id}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:32]

    def _scope_key_from_object_path(self, path: Path) -> str:
        relative = self.boundary.relative(path).replace("\\", "/")
        parts = relative.split("/")
        if len(parts) < 5 or parts[:3] != ["experience", "raw", "scopes"]:
            raise CaptureStorageError("raw object path is outside the scoped experience layout")
        scope_key = parts[3]
        if not re.fullmatch(r"[0-9a-f]{32}", scope_key):
            raise CaptureStorageError("raw object scope key is invalid")
        return scope_key

    def _manifest(
        self,
        *,
        outcome: ValidatedOutcome,
        record: ExperienceRecord,
        event_key: str,
        request_digest: str,
    ) -> dict[str, Any]:
        return {
            "schema": CAPTURE_SCHEMA_NAME,
            "schema_version": CAPTURE_SCHEMA_VERSION,
            "event_key": event_key,
            "event_id": outcome.event_id,
            "request_digest": request_digest,
            "record_digest": record.contract_digest(),
            "policy_digest": self.policy.digest(),
            "validator_id": outcome.validator_id,
            "validation_ref": outcome.validation_ref,
            "action_ref": outcome.action_ref,
            "result_ref": outcome.result_ref,
            "correction": outcome.correction.canonical() if outcome.correction else None,
            "record": record.to_dict(),
        }

    @staticmethod
    def _summary_from_manifest(manifest: dict[str, Any]) -> CaptureSummary:
        record = manifest["record"]
        correction = manifest["correction"]
        return CaptureSummary(
            experience_id=str(record["experience_id"]),
            event_id=str(manifest["event_id"]),
            workspace_id=str(record["workspace_id"]),
            project_id=str(record["project_id"]),
            outcome=str(record["outcome"]),
            state=str(record["state"]),
            content_sha256=str(record["content"]["sha256"]),
            byte_length=int(record["content"]["byte_length"]),
            media_type=str(record["content"]["media_type"]),
            validator_id=str(manifest["validator_id"]),
            validation_ref=str(manifest["validation_ref"]),
            correction_of=(
                str(correction["original_experience_id"]) if correction is not None else None
            ),
            policy_digest=str(manifest["policy_digest"]),
        )

    @staticmethod
    def _event_key(outcome: ValidatedOutcome) -> str:
        return ExperienceCollector._event_key_parts(
            outcome.workspace_id,
            outcome.project_id,
            outcome.event_id,
        )

    @staticmethod
    def _event_key_parts(workspace_id: str, project_id: str, event_id: str) -> str:
        payload = f"{workspace_id}\0{project_id}\0{event_id}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _request_digest(
        outcome: ValidatedOutcome,
        payload_digest: str,
        media_type: str,
    ) -> str:
        document = {
            "event_id": outcome.event_id,
            "workspace_id": outcome.workspace_id,
            "project_id": outcome.project_id,
            "source_type": outcome.source_type,
            "source_id": outcome.source_id,
            "task_label": outcome.task_label,
            "domain_label": outcome.domain_label,
            "action_ref": outcome.action_ref,
            "result_ref": outcome.result_ref,
            "validation_ref": outcome.validation_ref,
            "validator_id": outcome.validator_id,
            "validated": outcome.validated,
            "outcome": outcome.outcome.value,
            "origin_digest": outcome.origin_digest,
            "license_expression": outcome.license_expression,
            "correction": outcome.correction.canonical() if outcome.correction else None,
            "payload_digest": payload_digest,
            "media_type": media_type,
        }
        canonical = json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _authorize_write(self, path: Path, actor: str) -> None:
        decision = self.guardian.authorize(
            ActionRequest(
                action=ActionType.WRITE,
                actor=actor,
                target=str(path),
            )
        )
        if decision.kind is not DecisionKind.ALLOW:
            raise CaptureError(f"Guardian denied capture write: {decision.reason}")


def _require_safe_id(name: str, value: str) -> None:
    if not _SAFE_ID.fullmatch(value):
        raise ValueError(f"{name} must be a stable safe identifier")


def _require_digest(name: str, value: str) -> None:
    if not _HEX64.fullmatch(value):
        raise ValueError(f"{name} must be 64 lowercase hex chars")
