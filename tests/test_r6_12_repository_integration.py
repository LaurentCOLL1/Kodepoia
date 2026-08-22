from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.quality.patch_gate import IntegrationEvidenceStatus, R6IntegrationReport


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
        expected_name = f"R6_{item.subdivision.split('.')[1]}_ACCEPTANCE.md"
        expected_repository_path = f"docs/roadmap/{expected_name}"
        assert item.source == expected_repository_path

        source = (root / item.source).resolve(strict=True)
        assert source.parent == roadmap_root
        assert source.name == expected_name

        # Hash the canonical Git blob, not working-tree bytes. Windows checkout may
        # materialize CRLF while the repository blob remains the same LF content.
        canonical_bytes = _git_blob_bytes(root, expected_repository_path)
        assert hashlib.sha256(canonical_bytes).hexdigest() == item.evidence_sha256
        assert item.status is IntegrationEvidenceStatus.PASS
        assert item.manual_satisfied
        assert item.accepted_head

    r6_12 = next(item for item in report.subdivisions if item.subdivision == "R6.12")
    assert r6_12.accepted_head == report.source_sha
