from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.intelligence.research.acceptance import (
    R7IntegrationReport,
    R7IntegrationStatus,
    R7ManualState,
    build_subdivision_evidence,
    expected_r7_subdivisions,
    validate_repository_evidence,
)

NOW = "2026-08-22T21:00:00Z"


def _head(index: int) -> str:
    return f"{index:040x}"


def _manual(index: int) -> R7ManualState:
    if index == 4 or index == 6 or index == 11:
        return R7ManualState.CONDITIONAL_NOT_TRIGGERED
    if index == 7:
        return R7ManualState.REQUIRED_SATISFIED
    return R7ManualState.NONE


def _fixture() -> tuple[R7IntegrationReport, dict[str, bytes]]:
    blobs: dict[str, bytes] = {}
    items = []
    for index, subdivision in enumerate(expected_r7_subdivisions(), 1):
        accepted_head = _head(index)
        source = f"docs/roadmap/R7_{index}_ACCEPTANCE.md"
        blob = (
            f"# {subdivision} acceptance\n\n"
            f"Status: COMPLETE\nAccepted head: `{accepted_head}`\n"
        ).encode("utf-8")
        blobs[source] = blob
        items.append(
            build_subdivision_evidence(
                subdivision,
                accepted_head=accepted_head,
                manual_state=_manual(index),
                canonical_bytes=blob,
            )
        )
    report = R7IntegrationReport(
        generated_at=NOW,
        source_sha=_head(11),
        subdivisions=tuple(items),
        status=R7IntegrationStatus.PASS,
    )
    return report, blobs


def test_integrated_report_roundtrip_schema_and_repository_validation() -> None:
    report, blobs = _fixture()
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "schemas" / "r7-integration-report-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(report.to_dict())
    loaded = R7IntegrationReport.from_dict(report.to_dict())
    assert loaded == report
    assert loaded.evidence_sha256 == report.evidence_sha256
    assert not loaded.derived_blockers()
    validate_repository_evidence(loaded, blobs.__getitem__)


def test_integrated_report_digest_tampering_fails_closed() -> None:
    report, _ = _fixture()
    payload = report.to_dict()
    payload["generated_at"] = "2026-08-22T22:00:00Z"
    with pytest.raises(ValueError, match="digest"):
        R7IntegrationReport.from_dict(payload)


def test_repository_validation_recalculates_hash_and_byte_length() -> None:
    report, blobs = _fixture()
    source = report.subdivisions[2].source
    tampered = dict(blobs)
    tampered[source] = tampered[source] + b"tamper"
    with pytest.raises(ValueError, match="byte length mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)

    same_length = dict(blobs)
    original = bytearray(same_length[source])
    original[-2] = ord("X")
    same_length[source] = bytes(original)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        validate_repository_evidence(report, same_length.__getitem__)


def test_repository_validation_rejects_missing_blob_and_head_mismatch() -> None:
    report, blobs = _fixture()
    missing = dict(blobs)
    missing.pop(report.subdivisions[0].source)
    with pytest.raises(ValueError, match="Missing R7 acceptance evidence"):
        validate_repository_evidence(report, missing.__getitem__)

    source = report.subdivisions[1].source
    wrong_head = dict(blobs)
    text = wrong_head[source].decode().replace(report.subdivisions[1].accepted_head, "f" * 40)
    wrong_head[source] = text.encode()
    altered = replace(
        report.subdivisions[1],
        evidence_sha256=__import__("hashlib").sha256(wrong_head[source]).hexdigest(),
        evidence_bytes=len(wrong_head[source]),
    )
    rebuilt = R7IntegrationReport(
        generated_at=report.generated_at,
        source_sha=report.source_sha,
        subdivisions=(report.subdivisions[0], altered, *report.subdivisions[2:]),
        status=R7IntegrationStatus.PASS,
    )
    with pytest.raises(ValueError, match="does not contain declared accepted head"):
        validate_repository_evidence(rebuilt, wrong_head.__getitem__)


def test_unsatisfied_manual_state_cannot_be_pass_report() -> None:
    report, _ = _fixture()
    bad = replace(
        report.subdivisions[6],
        manual_state=R7ManualState.REQUIRED_UNSATISFIED,
    )
    with pytest.raises(ValueError, match="cannot contain blockers"):
        R7IntegrationReport(
            generated_at=report.generated_at,
            source_sha=report.source_sha,
            subdivisions=(*report.subdivisions[:6], bad, *report.subdivisions[7:]),
            status=R7IntegrationStatus.PASS,
        )


def test_r7_11_head_must_equal_source_sha() -> None:
    report, _ = _fixture()
    with pytest.raises(ValueError, match="R7.11 accepted head"):
        R7IntegrationReport(
            generated_at=report.generated_at,
            source_sha="e" * 40,
            subdivisions=report.subdivisions,
            status=R7IntegrationStatus.PASS,
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


def test_checked_in_r7_integrated_acceptance_is_bound_to_acceptance_documents() -> None:
    root = Path(__file__).resolve().parents[1]
    report_path = root / "docs" / "roadmap" / "R7_INTEGRATED_ACCEPTANCE.json"
    if not report_path.is_file():
        pytest.skip("final R7 integrated report is created during post-merge normalization")

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (root / "schemas" / "r7-integration-report-v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(payload)
    report = R7IntegrationReport.from_dict(payload)
    assert report.status is R7IntegrationStatus.PASS
    assert not report.blockers
    assert len(report.subdivisions) == 11
    validate_repository_evidence(report, lambda path: _git_blob_bytes(root, path))
