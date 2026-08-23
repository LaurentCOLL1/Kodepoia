from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.assets.acceptance import (
    R8IntegrationReport,
    R8IntegrationStatus,
    R8ManualState,
    build_subdivision_evidence,
    expected_r8_subdivisions,
    validate_repository_evidence,
)

NOW = "2026-08-23T06:00:00Z"


def _head(index: int) -> str:
    return f"{index + 32:040x}"


def _manual(index: int) -> tuple[R8ManualState, str]:
    if index in {5, 8, 11}:
        return R8ManualState.CONDITIONAL_NOT_TRIGGERED, "Frozen conditional gate was not triggered."
    if index == 9:
        return R8ManualState.REQUIRED_SATISFIED, "Authoritative Godot 4.7 local acceptance is recorded."
    return R8ManualState.NONE, "No manual intervention is defined for this subdivision."


def _fixture() -> tuple[R8IntegrationReport, dict[str, bytes]]:
    blobs: dict[str, bytes] = {}
    items = []
    for index, subdivision in enumerate(expected_r8_subdivisions(), 1):
        accepted_head = _head(index)
        source = f"docs/roadmap/R8_{index}_ACCEPTANCE.md"
        blob = (
            f"# {subdivision} acceptance\n\n"
            f"Status: COMPLETE\nAccepted head: `{accepted_head}`\n"
        ).encode("utf-8")
        blobs[source] = blob
        state, reason = _manual(index)
        items.append(
            build_subdivision_evidence(
                subdivision,
                accepted_head=accepted_head,
                manual_state=state,
                manual_reason=reason,
                canonical_bytes=blob,
            )
        )
    report = R8IntegrationReport(
        generated_at=NOW,
        source_sha=_head(11),
        subdivisions=tuple(items),
        status=R8IntegrationStatus.PASS,
    )
    return report, blobs


def test_integrated_report_roundtrip_schema_and_repository_validation() -> None:
    report, blobs = _fixture()
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "schemas" / "r8-integration-report-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(report.to_dict())
    loaded = R8IntegrationReport.from_dict(report.to_dict())
    assert loaded == report
    assert loaded.evidence_sha256 == report.evidence_sha256
    assert not loaded.derived_blockers()
    validate_repository_evidence(loaded, blobs.__getitem__)


def test_integrated_report_digest_tampering_fails_closed() -> None:
    report, _ = _fixture()
    payload = report.to_dict()
    payload["generated_at"] = "2026-08-23T06:05:00Z"
    with pytest.raises(ValueError, match="digest"):
        R8IntegrationReport.from_dict(payload)


def test_repository_validation_recalculates_hash_and_byte_length() -> None:
    report, blobs = _fixture()
    source = report.subdivisions[2].source
    tampered = dict(blobs)
    tampered[source] += b"tamper"
    with pytest.raises(ValueError, match="byte length mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)

    same_length = dict(blobs)
    changed = bytearray(same_length[source])
    changed[-2] = ord("X")
    same_length[source] = bytes(changed)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        validate_repository_evidence(report, same_length.__getitem__)


def test_repository_validation_rejects_missing_blob_and_declared_head_mismatch() -> None:
    report, blobs = _fixture()
    missing = dict(blobs)
    missing.pop(report.subdivisions[0].source)
    with pytest.raises(ValueError, match="Missing R8 acceptance evidence"):
        validate_repository_evidence(report, missing.__getitem__)

    source = report.subdivisions[1].source
    wrong_head = dict(blobs)
    text = wrong_head[source].decode("utf-8").replace(report.subdivisions[1].accepted_head, "f" * 40)
    wrong_head[source] = text.encode("utf-8")
    altered = replace(
        report.subdivisions[1],
        evidence_sha256=hashlib.sha256(wrong_head[source]).hexdigest(),
        evidence_bytes=len(wrong_head[source]),
    )
    rebuilt = R8IntegrationReport(
        generated_at=report.generated_at,
        source_sha=report.source_sha,
        subdivisions=(report.subdivisions[0], altered, *report.subdivisions[2:]),
        status=R8IntegrationStatus.PASS,
    )
    with pytest.raises(ValueError, match="does not contain declared accepted head"):
        validate_repository_evidence(rebuilt, wrong_head.__getitem__)


def test_unsatisfied_manual_state_and_missing_reason_fail_closed() -> None:
    report, _ = _fixture()
    bad = replace(
        report.subdivisions[8],
        manual_state=R8ManualState.REQUIRED_UNSATISFIED,
    )
    with pytest.raises(ValueError, match="cannot contain blockers"):
        R8IntegrationReport(
            generated_at=report.generated_at,
            source_sha=report.source_sha,
            subdivisions=(*report.subdivisions[:8], bad, *report.subdivisions[9:]),
            status=R8IntegrationStatus.PASS,
        )

    with pytest.raises(ValueError, match="explicit reason"):
        replace(report.subdivisions[4], manual_reason="  ")


def test_r8_11_head_must_equal_source_sha_and_exact_subdivision_order_is_required() -> None:
    report, _ = _fixture()
    with pytest.raises(ValueError, match="R8.11 accepted head"):
        R8IntegrationReport(
            generated_at=report.generated_at,
            source_sha="e" * 40,
            subdivisions=report.subdivisions,
            status=R8IntegrationStatus.PASS,
        )
    with pytest.raises(ValueError, match="R8.1 through R8.11 in order"):
        R8IntegrationReport(
            generated_at=report.generated_at,
            source_sha=report.source_sha,
            subdivisions=(report.subdivisions[1], report.subdivisions[0], *report.subdivisions[2:]),
            status=R8IntegrationStatus.PASS,
        )


def _git_blob_bytes(root: Path, repository_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"HEAD:{repository_path}"],
        cwd=root,
        check=True,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def test_checked_in_r8_integrated_acceptance_is_bound_to_exact_git_blobs() -> None:
    root = Path(__file__).resolve().parents[1]
    report_path = root / "docs" / "roadmap" / "R8_INTEGRATED_ACCEPTANCE.json"
    if not report_path.is_file():
        pytest.skip("final R8 integrated report is created after the R8.11 implementation head is frozen")

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    schema = json.loads((root / "schemas" / "r8-integration-report-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(payload)
    report = R8IntegrationReport.from_dict(payload)
    assert report.status is R8IntegrationStatus.PASS
    assert not report.blockers
    assert len(report.subdivisions) == 11
    validate_repository_evidence(report, lambda path: _git_blob_bytes(root, path))
