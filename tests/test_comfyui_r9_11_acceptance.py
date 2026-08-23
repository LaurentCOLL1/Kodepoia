from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.comfyui.acceptance import (
    R9IntegrationReport,
    R9IntegrationStatus,
    R9ManualState,
    build_subdivision_evidence,
    expected_r9_subdivisions,
    validate_repository_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "r9-integration-report-v1.schema.json"
R98_LOCAL_DIGEST = "a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967"
R98_LOCAL_BYTES = 5744


def _fixture_report() -> tuple[R9IntegrationReport, dict[str, bytes]]:
    blobs: dict[str, bytes] = {}
    evidence = []
    for index, subdivision in enumerate(expected_r9_subdivisions(), start=1):
        token = f"{index:x}"
        head = token * 40
        source = f"docs/roadmap/R9_{index}_ACCEPTANCE.md"
        suffix = ""
        kwargs = {}
        manual_state = R9ManualState.NONE
        manual_reason = "No manual intervention is required for this fixture subdivision."
        if subdivision == "R9.8":
            manual_state = R9ManualState.REQUIRED_SATISFIED
            manual_reason = "The frozen R9.8 local GPU evidence is reviewed and satisfied."
            kwargs = {
                "manual_evidence_sha256": R98_LOCAL_DIGEST,
                "manual_evidence_bytes": R98_LOCAL_BYTES,
            }
            suffix = f" local={R98_LOCAL_DIGEST} bytes={R98_LOCAL_BYTES}"
        elif subdivision in {"R9.2", "R9.5", "R9.9", "R9.11"}:
            manual_state = R9ManualState.CONDITIONAL_NOT_TRIGGERED
            manual_reason = "The frozen conditional was evaluated and not triggered."
        blob = f"# {subdivision}\naccepted head {head}{suffix}\n".encode("utf-8")
        blobs[source] = blob
        evidence.append(
            build_subdivision_evidence(
                subdivision,
                accepted_head=head,
                manual_state=manual_state,
                manual_reason=manual_reason,
                canonical_bytes=blob,
                **kwargs,
            )
        )
    report = R9IntegrationReport(
        generated_at="2026-08-23T20:00:00Z",
        source_sha="b" * 40,
        subdivisions=tuple(evidence),
        status=R9IntegrationStatus.PASS,
        blockers=(),
    )
    return report, blobs


def test_r9_report_roundtrip_schema_and_repository_validation() -> None:
    report, blobs = _fixture_report()
    payload = report.to_dict()
    Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(payload)
    loaded = R9IntegrationReport.from_dict(json.loads(json.dumps(payload)))
    assert loaded == report
    assert loaded.blockers == ()
    assert loaded.derived_blockers() == ()
    validate_repository_evidence(loaded, lambda path: blobs[path])


def test_r98_required_state_cannot_omit_reviewed_local_evidence() -> None:
    with pytest.raises(ValueError, match="R9.8 REQUIRED SATISFIED"):
        build_subdivision_evidence(
            "R9.8",
            accepted_head="8" * 40,
            manual_state=R9ManualState.REQUIRED_SATISFIED,
            manual_reason="required fixture",
            canonical_bytes=b"accepted 8888888888888888888888888888888888888888",
        )


def test_repository_validation_rejects_tampered_canonical_acceptance_blob() -> None:
    report, blobs = _fixture_report()
    poisoned = dict(blobs)
    poisoned["docs/roadmap/R9_4_ACCEPTANCE.md"] += b"tampered"
    with pytest.raises(ValueError, match="byte length mismatch|SHA-256 mismatch"):
        validate_repository_evidence(report, lambda path: poisoned[path])


def test_repository_validation_requires_r98_digest_to_be_in_acceptance_document() -> None:
    report, blobs = _fixture_report()
    poisoned = dict(blobs)
    source = "docs/roadmap/R9_8_ACCEPTANCE.md"
    poisoned[source] = poisoned[source].replace(R98_LOCAL_DIGEST.encode("ascii"), b"0" * 64)
    item = report.subdivisions[7]
    from dataclasses import replace

    adjusted = replace(
        item,
        evidence_sha256=__import__("hashlib").sha256(poisoned[source]).hexdigest(),
        evidence_bytes=len(poisoned[source]),
    )
    adjusted_report = replace(report, subdivisions=report.subdivisions[:7] + (adjusted,) + report.subdivisions[8:])
    with pytest.raises(ValueError, match="manual evidence digest"):
        validate_repository_evidence(adjusted_report, lambda path: poisoned[path])


def test_unsatisfied_manual_state_is_a_derived_blocker() -> None:
    report, _blobs = _fixture_report()
    from dataclasses import replace

    broken = replace(
        report.subdivisions[1],
        manual_state=R9ManualState.CONDITIONAL_TRIGGERED_UNSATISFIED,
    )
    with pytest.raises(ValueError, match="cannot contain blockers"):
        replace(report, subdivisions=(report.subdivisions[0], broken) + report.subdivisions[2:])


def test_r911_accepted_head_must_equal_report_source_sha() -> None:
    report, _blobs = _fixture_report()
    from dataclasses import replace

    mismatched = replace(report.subdivisions[-1], accepted_head="0" * 40)
    with pytest.raises(ValueError, match="R9.11 accepted head"):
        replace(report, subdivisions=report.subdivisions[:-1] + (mismatched,))


def test_report_digest_tampering_is_rejected() -> None:
    report, _blobs = _fixture_report()
    payload = report.to_dict()
    payload["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="digest"):
        R9IntegrationReport.from_dict(payload)
