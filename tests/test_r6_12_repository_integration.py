from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.quality.patch_gate import IntegrationEvidenceStatus, R6IntegrationReport


def test_checked_in_r6_integrated_acceptance_is_bound_to_acceptance_documents() -> None:
    root = Path(__file__).resolve().parents[1]
    report_path = root / "docs" / "roadmap" / "R6_INTEGRATED_ACCEPTANCE.json"
    if not report_path.is_file():
        pytest.skip("final R6 integrated report is created during post-merge normalization")

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (root / "schemas" / "r6-integration-report-v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(payload)
    report = R6IntegrationReport.from_dict(payload)
    assert report.status is IntegrationEvidenceStatus.PASS
    assert not report.blockers
    assert len(report.subdivisions) == 12

    expected_ids = {f"R6.{index}" for index in range(1, 13)}
    assert {item.subdivision for item in report.subdivisions} == expected_ids

    roadmap_root = (root / "docs" / "roadmap").resolve(strict=True)
    for item in report.subdivisions:
        source = (root / item.source).resolve(strict=True)
        assert source.parent == roadmap_root
        assert source.name == f"R6_{item.subdivision.split('.')[1]}_ACCEPTANCE.md"
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item.evidence_sha256
        assert item.status is IntegrationEvidenceStatus.PASS
        assert item.manual_satisfied
        assert item.accepted_head

    r6_12 = next(item for item in report.subdivisions if item.subdivision == "R6.12")
    assert r6_12.accepted_head == report.source_sha
