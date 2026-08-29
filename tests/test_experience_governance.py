from __future__ import annotations

import hashlib
import json

import pytest

from kodepoia.experience.contracts import (
    ContentRef,
    ExperienceId,
    ExperienceRecord,
    ExperienceState,
    OutcomeLabel,
    PolicyDecision,
    ProvenanceDescriptor,
)
from kodepoia.experience.governance import (
    GovernancePolicy,
    RedactionRule,
    RevocationIndex,
    assess_license,
    sanitize_experience,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _record(*, license_expression: str | None = "MIT", benchmark: bool = False) -> ExperienceRecord:
    origin = _digest("origin")
    return ExperienceRecord(
        experience_id=ExperienceId.derive(
            workspace_id="ws-demo", source_id="src-demo", origin_digest=origin
        ),
        workspace_id="ws-demo",
        project_id="project-demo",
        task_label="coding",
        domain_label="python",
        state=ExperienceState.OBSERVED,
        outcome=OutcomeLabel.ACCEPTED,
        content=ContentRef(
            workspace_id="ws-demo",
            storage_key="experience/raw/project-demo/raw.txt",
            sha256=_digest("raw"),
            byte_length=3,
        ),
        provenance=ProvenanceDescriptor(
            source_type="fixture",
            source_id="src-demo",
            origin_digest=origin,
            project_scope="project-demo",
            license_expression=license_expression,
        ),
        benchmark_protected=benchmark,
    )


def _policy(**kwargs: object) -> GovernancePolicy:
    defaults = {
        "allowed_source_types": frozenset({"fixture"}),
        "trusted_provenance_source_types": frozenset({"fixture"}),
        "allowed_licenses": frozenset({"MIT", "Apache-2.0", "GPL-2.0-only"}),
        "allowed_exceptions": frozenset({"Classpath-exception-2.0"}),
    }
    defaults.update(kwargs)
    return GovernancePolicy(**defaults)


def test_allowed_record_is_redacted_and_reaches_sanitized() -> None:
    secret = "super-secret-token-123"
    raw = f"email alice@example.com\napi_key={secret}\npath C:\\Users\\Alice\\project\\x.py"
    result = sanitize_experience(
        _record(), raw, policy=_policy(), consent=PolicyDecision.ALLOW, actor="tester"
    )
    assert result.record.state is ExperienceState.SANITIZED
    assert result.record.authorization.blockers() == ()
    assert result.record.content.sha256 == _digest(result.sanitized_text)
    assert result.record.content.storage_key.startswith("experience/sanitized/project-demo/")
    assert result.record.transformations[-1].input_digest == _digest(raw)
    assert secret not in result.sanitized_text
    assert "alice@example.com" not in result.sanitized_text
    assert "C:\\Users\\Alice" not in result.sanitized_text
    assert {"credential", "email", "windows_path"} <= set(result.report.categories)


def test_report_never_contains_detected_values_or_storage_path() -> None:
    secret = "TOKENVALUE123456"
    raw = f"access_token={secret}\n/home/alice/secret/project.txt"
    result = sanitize_experience(
        _record(), raw, policy=_policy(), consent=PolicyDecision.ALLOW
    )
    encoded = json.dumps(result.report.to_dict(), sort_keys=True)
    assert secret not in encoded
    assert "/home/alice" not in encoded
    assert "experience/sanitized" not in encoded
    assert result.report.finding_count == 2


def test_sanitization_is_deterministic_and_policy_digest_bound() -> None:
    raw = "password=abcdefghijk email bob@example.net"
    first = sanitize_experience(_record(), raw, policy=_policy(), consent=PolicyDecision.ALLOW)
    second = sanitize_experience(_record(), raw, policy=_policy(), consent=PolicyDecision.ALLOW)
    assert first.sanitized_text == second.sanitized_text
    assert first.report.to_dict() == second.report.to_dict()
    other = sanitize_experience(
        _record(),
        raw,
        policy=_policy(extra_redaction_rules=(RedactionRule("word", r"email"),)),
        consent=PolicyDecision.ALLOW,
    )
    assert other.report.policy_digest != first.report.policy_digest
    assert other.report.output_digest != first.report.output_digest


def test_unknown_consent_cannot_be_laundered_by_successful_redaction() -> None:
    result = sanitize_experience(_record(), "password=abcdefghijk", policy=_policy())
    assert result.record.state is ExperienceState.QUARANTINED
    assert result.record.authorization.consent is PolicyDecision.UNKNOWN
    assert "consent" in result.report.blockers


def test_unknown_license_is_review_and_quarantined() -> None:
    result = sanitize_experience(
        _record(license_expression="Unknown-9.9"),
        "clean",
        policy=_policy(),
        consent=PolicyDecision.ALLOW,
    )
    assert result.record.state is ExperienceState.QUARANTINED
    assert result.record.authorization.license is PolicyDecision.REVIEW
    assert result.report.license_summary["reason"] == "license_unknown"


def test_missing_license_is_unknown_and_quarantined() -> None:
    result = sanitize_experience(
        _record(license_expression=None), "clean", policy=_policy(), consent=PolicyDecision.ALLOW
    )
    assert result.record.authorization.license is PolicyDecision.UNKNOWN
    assert result.record.state is ExperienceState.QUARANTINED


def test_denied_license_and_source_fail_closed() -> None:
    policy = _policy(
        allowed_source_types=frozenset(),
        denied_source_types=frozenset({"fixture"}),
        allowed_licenses=frozenset({"Apache-2.0"}),
        denied_licenses=frozenset({"MIT"}),
    )
    result = sanitize_experience(_record(), "clean", policy=policy, consent=PolicyDecision.ALLOW)
    assert result.record.authorization.source_scope is PolicyDecision.DENY
    assert result.record.authorization.license is PolicyDecision.DENY
    assert result.record.state is ExperienceState.QUARANTINED


def test_compound_spdx_style_expression_is_assessed() -> None:
    result = assess_license("MIT OR Apache-2.0", _policy())
    assert result.decision is PolicyDecision.ALLOW
    assert result.identifiers == ("MIT", "Apache-2.0")
    assert result.operators == ("OR",)
    lower = assess_license("MIT or Apache-2.0", _policy())
    assert lower.decision is PolicyDecision.ALLOW
    assert lower.operators == ("OR",)
    with_exception = assess_license(
        "GPL-2.0-only WITH Classpath-exception-2.0", _policy()
    )
    assert with_exception.decision is PolicyDecision.ALLOW
    assert with_exception.operators == ("WITH",)


def test_invalid_and_license_ref_expressions_require_review() -> None:
    assert assess_license("MIT OR", _policy()).decision is PolicyDecision.REVIEW
    assert assess_license("LicenseRef-Custom", _policy()).decision is PolicyDecision.REVIEW


def test_explicit_license_ref_policy_still_requires_allowlisting() -> None:
    policy = _policy(
        allow_license_refs=True,
        allowed_licenses=frozenset({"MIT", "LicenseRef-Custom"}),
    )
    assert assess_license("LicenseRef-Custom", policy).decision is PolicyDecision.ALLOW


def test_benchmark_protection_remains_a_hard_blocker() -> None:
    result = sanitize_experience(
        _record(benchmark=True), "clean", policy=_policy(), consent=PolicyDecision.ALLOW
    )
    assert result.record.state is ExperienceState.QUARANTINED
    assert result.report.disposition == "quarantined"


def test_configured_private_category_can_deny_even_after_redaction() -> None:
    policy = _policy(
        extra_redaction_rules=(RedactionRule("phone", r"\+33[0-9]{9}"),),
        deny_categories=frozenset({"phone"}),
    )
    result = sanitize_experience(
        _record(), "+33123456789", policy=policy, consent=PolicyDecision.ALLOW
    )
    assert "+33123456789" not in result.sanitized_text
    assert result.record.authorization.privacy is PolicyDecision.DENY
    assert result.record.state is ExperienceState.QUARANTINED


def test_policy_rejects_allow_deny_overlap() -> None:
    with pytest.raises(ValueError):
        GovernancePolicy(
            allowed_source_types=frozenset({"fixture"}),
            denied_source_types=frozenset({"fixture"}),
        )


def test_revocation_cascades_to_derived_artifact_ids() -> None:
    sanitized = sanitize_experience(
        _record(), "clean", policy=_policy(), consent=PolicyDecision.ALLOW
    ).record
    index = RevocationIndex()
    index.register("dataset:v1", [sanitized.experience_id.value])
    index.register("candidate:v1", ["dataset:v1"])
    records, report = index.revoke_source(
        "src-demo", [sanitized], actor="guardian", reason="consent revoked"
    )
    assert records[0].state is ExperienceState.REVOKED
    assert report.revoked_experience_ids == (sanitized.experience_id.value,)
    assert report.invalidated_artifact_ids == ("candidate:v1", "dataset:v1")
    assert report.to_dict()["rebuild_required"] is True
    assert "consent revoked" not in json.dumps(report.to_dict())


def test_observed_revocation_quarantines_instead_of_promoting() -> None:
    index = RevocationIndex()
    records, report = index.revoke_source(
        "src-demo", [_record()], actor="guardian", reason="source removed"
    )
    assert records[0].state is ExperienceState.QUARANTINED
    assert report.quarantined_experience_ids == (records[0].experience_id.value,)


def test_revocation_does_not_touch_other_sources() -> None:
    record = _record()
    index = RevocationIndex()
    records, report = index.revoke_source(
        "other-source", [record], actor="guardian", reason="other"
    )
    assert records == (record,)
    assert report.revoked_experience_ids == ()
    assert report.invalidated_artifact_ids == ()
