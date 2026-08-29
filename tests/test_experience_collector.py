from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.assets.boundary import VaultBoundary
from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.exceptions import PermissionDenied
from kodepoia.experience import (
    CaptureConflict,
    CaptureDisposition,
    CapturePolicy,
    CaptureStorageError,
    CorrectionProvenance,
    ExperienceCollector,
    ExperienceId,
    OutcomeLabel,
    ValidatedOutcome,
)

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
ROOT = Path(__file__).resolve().parents[1]


def outcome(
    *,
    event_id: str = "event-1",
    project_id: str = "project-1",
    source_type: str = "validated_workflow",
    validated: bool = True,
    label: OutcomeLabel = OutcomeLabel.ACCEPTED,
    correction: CorrectionProvenance | None = None,
) -> ValidatedOutcome:
    return ValidatedOutcome(
        event_id=event_id,
        workspace_id="ws-1",
        project_id=project_id,
        source_type=source_type,
        source_id="source-1",
        task_label="debugging",
        domain_label="python",
        action_ref="action-1",
        result_ref="result-1",
        validation_ref="validation-1",
        validator_id="validator-1",
        validated=validated,
        outcome=label,
        origin_digest=DIGEST_A,
        license_expression="MIT",
        correction=correction,
    )


def policy(**changes: object) -> CapturePolicy:
    values: dict[str, object] = {
        "enabled": True,
        "opted_in_projects": ("project-1",),
        "allowed_source_types": ("validated_workflow",),
    }
    values.update(changes)
    return CapturePolicy(**values)  # type: ignore[arg-type]


def collector(
    tmp_path: Path,
    *,
    capture_policy: CapturePolicy | None = None,
    grant_write: bool = True,
) -> tuple[ExperienceCollector, Path, Path]:
    vault = tmp_path / "vault"
    audit_path = vault / "audit" / "experience.jsonl"
    audit = AuditLog(audit_path)
    permissions = PermissionSet()
    if grant_write:
        permissions.grant(
            PermissionGrant(
                Capability.FILE_WRITE,
                roots=(vault,),
            )
        )
    instance = ExperienceCollector(
        VaultBoundary(vault),
        policy=capture_policy or policy(),
        guardian=KodeGuardian(permissions),
        audit_log=audit,
    )
    return instance, vault, audit_path


def records(vault: Path) -> list[Path]:
    return sorted(vault.glob("experience/raw/scopes/*/records/*.json"))


def objects(vault: Path) -> list[Path]:
    return sorted(vault.glob("experience/raw/scopes/*/objects/sha256/*/*"))


def test_capture_is_disabled_by_default_without_raw_or_audit_write(tmp_path: Path) -> None:
    instance, vault, audit_path = collector(
        tmp_path,
        capture_policy=CapturePolicy(),
    )
    result = instance.capture(outcome(), "validated result", actor="brain")
    assert result.disposition is CaptureDisposition.DISABLED
    assert records(vault) == []
    assert objects(vault) == []
    assert not audit_path.exists()


def test_project_and_source_require_repository_policy_opt_in(tmp_path: Path) -> None:
    instance, vault, _ = collector(tmp_path)
    blocked_project = instance.capture(
        outcome(project_id="project-2"),
        "result",
        actor="brain",
    )
    blocked_source = instance.capture(
        outcome(source_type="unreviewed_chat"),
        "result",
        actor="brain",
    )
    assert blocked_project.disposition is CaptureDisposition.POLICY_BLOCKED
    assert blocked_source.disposition is CaptureDisposition.POLICY_BLOCKED
    assert records(vault) == []


def test_unvalidated_or_unknown_outcomes_are_not_captured(tmp_path: Path) -> None:
    instance, vault, _ = collector(tmp_path)
    unvalidated = instance.capture(outcome(validated=False), "result", actor="brain")
    unknown = instance.capture(
        outcome(event_id="event-2", label=OutcomeLabel.UNKNOWN),
        "result",
        actor="brain",
    )
    assert unvalidated.disposition is CaptureDisposition.VALIDATION_BLOCKED
    assert unknown.disposition is CaptureDisposition.OUTCOME_BLOCKED
    assert records(vault) == []


def test_accepted_capture_is_observed_and_training_disabled(tmp_path: Path) -> None:
    instance, vault, _ = collector(tmp_path)
    result = instance.capture(outcome(), "accepted patch", actor="brain")
    assert result.disposition is CaptureDisposition.STORED
    assert result.summary is not None
    assert result.summary.state == "observed"
    manifest = json.loads(records(vault)[0].read_text(encoding="utf-8"))
    assert set(manifest["record"]["authorization"].values()) == {"unknown"}
    assert manifest["record"]["sanitization"]["status"] == "not_run"
    assert objects(vault)[0].read_bytes() == b"accepted patch"


def test_identical_event_replay_is_idempotent_without_audit_inflation(tmp_path: Path) -> None:
    instance, vault, audit_path = collector(tmp_path)
    first = instance.capture(outcome(), "same", actor="brain")
    replay = instance.capture(outcome(), "same", actor="brain")
    assert first.disposition is CaptureDisposition.STORED
    assert replay.disposition is CaptureDisposition.IDEMPOTENT
    assert first.summary == replay.summary
    assert len(records(vault)) == 1
    assert len(audit_path.read_text(encoding="utf-8").splitlines()) == 1


def test_replayed_event_with_changed_payload_fails_closed(tmp_path: Path) -> None:
    instance, _, _ = collector(tmp_path)
    instance.capture(outcome(), "first", actor="brain")
    with pytest.raises(CaptureConflict):
        instance.capture(outcome(), "changed", actor="brain")


def test_negative_outcomes_need_explicit_diagnostic_policy_and_stay_quarantined(
    tmp_path: Path,
) -> None:
    default, vault, _ = collector(tmp_path)
    blocked = default.capture(
        outcome(label=OutcomeLabel.FAILED),
        "failed result",
        actor="brain",
    )
    assert blocked.disposition is CaptureDisposition.OUTCOME_BLOCKED
    assert records(vault) == []

    enabled, vault2, _ = collector(
        tmp_path / "negative",
        capture_policy=policy(capture_negative_outcomes=True),
    )
    stored = enabled.capture(
        outcome(label=OutcomeLabel.REJECTED),
        "rejected result",
        actor="brain",
    )
    assert stored.disposition is CaptureDisposition.STORED
    assert stored.summary is not None
    assert stored.summary.state == "quarantined"
    manifest = json.loads(records(vault2)[0].read_text(encoding="utf-8"))
    assert set(manifest["record"]["authorization"].values()) == {"unknown"}


def test_correction_provenance_is_explicit_and_scope_confined(tmp_path: Path) -> None:
    original = ExperienceId.derive(
        workspace_id="ws-1",
        source_id="event-original",
        origin_digest=DIGEST_B,
    )
    correction = CorrectionProvenance(
        original_experience_id=original,
        original_workspace_id="ws-1",
        original_project_id="project-1",
        original_content_digest=DIGEST_B,
        evaluator_id="reviewer-1",
    )
    instance, _, _ = collector(tmp_path)
    stored = instance.capture(
        outcome(label=OutcomeLabel.CORRECTED, correction=correction),
        "corrected answer",
        actor="brain",
    )
    assert stored.summary is not None
    assert stored.summary.correction_of == str(original)
    assert stored.summary.state == "observed"

    with pytest.raises(ValueError, match="same workspace/project"):
        outcome(
            event_id="event-cross-scope",
            label=OutcomeLabel.CORRECTED,
            correction=CorrectionProvenance(
                original_experience_id=original,
                original_workspace_id="ws-1",
                original_project_id="project-other",
                original_content_digest=DIGEST_B,
                evaluator_id="reviewer-1",
            ),
        )


def test_payload_record_count_and_project_byte_quotas_fail_closed(tmp_path: Path) -> None:
    payload_limit, vault, _ = collector(
        tmp_path / "payload",
        capture_policy=policy(max_payload_bytes=3),
    )
    oversized = payload_limit.capture(outcome(), "1234", actor="brain")
    assert oversized.disposition is CaptureDisposition.QUOTA_BLOCKED
    assert records(vault) == []

    count_limit, _, _ = collector(
        tmp_path / "count",
        capture_policy=policy(max_records_per_project=1),
    )
    assert count_limit.capture(outcome(), "one", actor="brain").disposition is CaptureDisposition.STORED
    blocked_count = count_limit.capture(
        outcome(event_id="event-2"),
        "two",
        actor="brain",
    )
    assert blocked_count.disposition is CaptureDisposition.QUOTA_BLOCKED

    byte_limit, _, _ = collector(
        tmp_path / "bytes",
        capture_policy=policy(max_bytes_per_project=5),
    )
    assert byte_limit.capture(outcome(), "123", actor="brain").disposition is CaptureDisposition.STORED
    blocked_bytes = byte_limit.capture(
        outcome(event_id="event-2"),
        "456",
        actor="brain",
    )
    assert blocked_bytes.disposition is CaptureDisposition.QUOTA_BLOCKED


def test_same_payload_is_physically_isolated_between_projects(tmp_path: Path) -> None:
    instance, vault, _ = collector(
        tmp_path,
        capture_policy=policy(opted_in_projects=("project-1", "project-2")),
    )
    one = instance.capture(outcome(project_id="project-1"), "same bytes", actor="brain")
    two = instance.capture(
        outcome(event_id="event-2", project_id="project-2"),
        "same bytes",
        actor="brain",
    )
    assert one.disposition is CaptureDisposition.STORED
    assert two.disposition is CaptureDisposition.STORED
    stored_objects = objects(vault)
    assert len(stored_objects) == 2
    assert stored_objects[0].parent.parent.parent.parent != stored_objects[1].parent.parent.parent.parent
    assert instance.status(workspace_id="ws-1", project_id="project-1")["records"] == 1
    assert instance.status(workspace_id="ws-1", project_id="project-2")["records"] == 1


def test_audit_and_status_never_echo_raw_secret_or_storage_key(tmp_path: Path) -> None:
    instance, _, audit_path = collector(tmp_path)
    secret = "ghp_SYNTHETIC_SECRET_VALUE_123456789"
    stored = instance.capture(outcome(), f"token={secret}", actor="brain")
    assert stored.disposition is CaptureDisposition.STORED
    audit = audit_path.read_text(encoding="utf-8")
    status = repr(instance.status(workspace_id="ws-1", project_id="project-1"))
    for rendered in (audit, status, repr(stored.summary)):
        assert secret not in rendered
        assert "storage_key" not in rendered
        assert "experience/raw/" not in rendered


def test_guardian_permission_is_required_for_raw_write(tmp_path: Path) -> None:
    instance, vault, _ = collector(tmp_path, grant_write=False)
    with pytest.raises(PermissionDenied):
        instance.capture(outcome(), "accepted", actor="brain")
    assert records(vault) == []
    assert objects(vault) == []


def test_tampered_raw_object_is_rejected_on_inspection(tmp_path: Path) -> None:
    instance, vault, _ = collector(tmp_path)
    instance.capture(outcome(), "accepted", actor="brain")
    objects(vault)[0].write_bytes(b"tampered")
    with pytest.raises(CaptureStorageError, match="SHA-256"):
        instance.inspect(workspace_id="ws-1", project_id="project-1", event_id="event-1")


def test_tampered_manifest_digest_is_rejected(tmp_path: Path) -> None:
    instance, vault, _ = collector(tmp_path)
    instance.capture(outcome(), "accepted", actor="brain")
    manifest_path = records(vault)[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["record"]["content"]["byte_length"] += 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CaptureStorageError, match="record digest mismatch"):
        instance.inspect(workspace_id="ws-1", project_id="project-1", event_id="event-1")


def test_capture_schema_and_nested_experience_schema_validate(tmp_path: Path) -> None:
    instance, vault, _ = collector(tmp_path)
    instance.capture(outcome(), "accepted", actor="brain")
    manifest = json.loads(records(vault)[0].read_text(encoding="utf-8"))
    capture_schema = json.loads(
        (ROOT / "schemas/experience-capture-v1.schema.json").read_text(encoding="utf-8")
    )
    record_schema = json.loads(
        (ROOT / "schemas/experience-record-v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(capture_schema)
    Draft202012Validator.check_schema(record_schema)
    Draft202012Validator(capture_schema).validate(manifest)
    Draft202012Validator(record_schema).validate(manifest["record"])
