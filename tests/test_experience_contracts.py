from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.experience import (
    ContentRef,
    EligibilityDenied,
    ExperienceContractError,
    ExperienceId,
    ExperienceRecord,
    ExperienceState,
    InvalidTransition,
    OutcomeLabel,
    PolicyDecision,
    ProvenanceDescriptor,
    SanitizationEvidence,
    SanitizationStatus,
    TrainingAuthorization,
    WorkspaceMismatch,
    transition_experience,
)

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
ROOT = Path(__file__).resolve().parents[1]


def allowed_auth() -> TrainingAuthorization:
    return TrainingAuthorization(
        source_scope=PolicyDecision.ALLOW,
        consent=PolicyDecision.ALLOW,
        provenance=PolicyDecision.ALLOW,
        license=PolicyDecision.ALLOW,
        privacy=PolicyDecision.ALLOW,
    )


def record(
    *,
    state: ExperienceState = ExperienceState.OBSERVED,
    authorization: TrainingAuthorization | None = None,
    sanitization: SanitizationEvidence | None = None,
    benchmark_protected: bool = False,
) -> ExperienceRecord:
    return ExperienceRecord(
        experience_id=ExperienceId.derive(
            workspace_id="ws-1", source_id="src-1", origin_digest=DIGEST_A
        ),
        workspace_id="ws-1",
        project_id="project-1",
        task_label="debugging",
        domain_label="python",
        state=state,
        outcome=OutcomeLabel.ACCEPTED,
        content=ContentRef(
            workspace_id="ws-1",
            storage_key="experience/raw/item-1",
            sha256=DIGEST_B,
            byte_length=123,
            media_type="text/plain",
        ),
        provenance=ProvenanceDescriptor(
            source_type="repository_fixture",
            source_id="src-1",
            origin_digest=DIGEST_A,
            project_scope="project-1",
            license_expression="MIT",
        ),
        authorization=authorization or TrainingAuthorization(),
        sanitization=sanitization or SanitizationEvidence(),
        benchmark_protected=benchmark_protected,
    )


def test_experience_id_is_deterministic_and_immutable() -> None:
    first = ExperienceId.derive(workspace_id="ws-1", source_id="src-1", origin_digest=DIGEST_A)
    second = ExperienceId.derive(workspace_id="ws-1", source_id="src-1", origin_digest=DIGEST_A)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.value = "exp_" + DIGEST_B  # type: ignore[misc]


def test_unknown_authorization_fails_closed() -> None:
    item = record()
    assert set(item.authorization.blockers()) == {
        "source_scope",
        "consent",
        "provenance",
        "license",
        "privacy",
    }
    with pytest.raises(EligibilityDenied):
        transition_experience(item, ExperienceState.ELIGIBLE, actor="curator", reason="candidate")


def test_redaction_cannot_launder_denied_source() -> None:
    denied = TrainingAuthorization(
        source_scope=PolicyDecision.DENY,
        consent=PolicyDecision.ALLOW,
        provenance=PolicyDecision.ALLOW,
        license=PolicyDecision.ALLOW,
        privacy=PolicyDecision.ALLOW,
    )
    sanitized = SanitizationEvidence(
        status=SanitizationStatus.PASSED,
        sanitizer_digest=DIGEST_C,
        categories=("secret",),
        finding_count=1,
    )
    item = record(authorization=denied, sanitization=sanitized)
    with pytest.raises(EligibilityDenied, match="source_scope"):
        transition_experience(item, ExperienceState.ELIGIBLE, actor="curator", reason="redacted")


def test_benchmark_protected_content_never_becomes_training_eligible() -> None:
    item = record(authorization=allowed_auth(), benchmark_protected=True)
    with pytest.raises(EligibilityDenied, match="benchmark-protected"):
        transition_experience(item, ExperienceState.ELIGIBLE, actor="curator", reason="protected")


def test_valid_state_machine_to_dataset_included() -> None:
    sanitized = SanitizationEvidence(status=SanitizationStatus.PASSED, sanitizer_digest=DIGEST_C)
    item = record(authorization=allowed_auth(), sanitization=sanitized)
    for target in (
        ExperienceState.ELIGIBLE,
        ExperienceState.SANITIZED,
        ExperienceState.CURATED,
        ExperienceState.DATASET_INCLUDED,
    ):
        result = transition_experience(
            item, target, actor="curator", reason=f"promote to {target.value}"
        )
        assert result.audit_details["from_state"] == item.state.value
        assert result.audit_details["to_state"] == target.value
        assert result.audit_details["record_digest"] == result.record.contract_digest()
        item = result.record
    assert item.state is ExperienceState.DATASET_INCLUDED


def test_sanitized_requires_sanitization_evidence() -> None:
    item = record(authorization=allowed_auth())
    item = transition_experience(
        item, ExperienceState.ELIGIBLE, actor="curator", reason="eligible"
    ).record
    with pytest.raises(EligibilityDenied, match="PASSED"):
        transition_experience(item, ExperienceState.SANITIZED, actor="curator", reason="not yet")


def test_terminal_and_skipping_transitions_rejected() -> None:
    item = record()
    with pytest.raises(InvalidTransition):
        transition_experience(item, ExperienceState.CURATED, actor="curator", reason="skip")
    rejected = transition_experience(
        item, ExperienceState.REJECTED, actor="curator", reason="policy"
    ).record
    with pytest.raises(InvalidTransition):
        transition_experience(
            rejected, ExperienceState.ELIGIBLE, actor="curator", reason="resurrect"
        )


def test_transition_requires_actor_and_reason() -> None:
    item = record()
    with pytest.raises(InvalidTransition):
        transition_experience(item, ExperienceState.REJECTED, actor="", reason="policy")
    with pytest.raises(InvalidTransition):
        transition_experience(item, ExperienceState.REJECTED, actor="curator", reason=" ")


def test_cross_workspace_content_ref_is_rejected() -> None:
    with pytest.raises(WorkspaceMismatch):
        ExperienceRecord(
            experience_id=ExperienceId.derive(
                workspace_id="ws-1", source_id="src-1", origin_digest=DIGEST_A
            ),
            workspace_id="ws-1",
            project_id="project-1",
            task_label="debugging",
            domain_label="python",
            state=ExperienceState.OBSERVED,
            outcome=OutcomeLabel.UNKNOWN,
            content=ContentRef(
                workspace_id="ws-2",
                storage_key="experience/raw/item",
                sha256=DIGEST_B,
                byte_length=1,
            ),
            provenance=ProvenanceDescriptor(
                source_type="fixture",
                source_id="src-1",
                origin_digest=DIGEST_A,
                project_scope="project-1",
            ),
        )


@pytest.mark.parametrize(
    "storage_key",
    ["/absolute", r"C:\secret\file", "../escape", "a/../b", "a//b", "./a"],
)
def test_content_ref_rejects_unsafe_storage_key(storage_key: str) -> None:
    with pytest.raises(ExperienceContractError):
        ContentRef(
            workspace_id="ws-1",
            storage_key=storage_key,
            sha256=DIGEST_A,
            byte_length=1,
        )


def test_audit_summary_never_exposes_storage_key_or_raw_content() -> None:
    summary = record().audit_summary()
    dumped = repr(summary)
    assert "experience/raw/item-1" not in dumped
    assert "storage_key" not in dumped
    assert "raw_content" not in dumped


def test_canonical_serialization_and_digest_are_stable() -> None:
    first = record().canonical_json()
    second = record().canonical_json()
    assert first == second
    assert record().contract_digest() == record().contract_digest()
    assert " " not in first


def test_json_schema_2020_12_validates_contract() -> None:
    schema = json.loads((ROOT / "schemas/experience-record-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(record().to_dict())
