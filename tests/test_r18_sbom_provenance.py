from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.release.provenance import (
    ATTESTATION_SEMANTICS,
    SPDX_PREDICATE_TYPE,
    ReleaseEvidenceError,
    build_spdx_sbom,
    verify_release_evidence_files,
    write_release_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"
REPOSITORY = "LaurentCOLL1/Kodepoia"


def _write(output: Path):
    return write_release_evidence(
        repo_root=ROOT,
        output_dir=output,
        source_sha=SOURCE_SHA,
        repository=REPOSITORY,
        workflow_ref="test-workflow",
        run_id="test",
        run_attempt="1",
        optional_groups=(),
        created_at="2026-09-05T00:00:00Z",
    )


def test_release_evidence_is_deterministic_and_spdx_23(tmp_path: Path) -> None:
    first = _write(tmp_path / "first")
    second = _write(tmp_path / "second")
    assert first.sbom_sha256 == second.sbom_sha256
    assert first.provenance_sha256 == second.provenance_sha256
    sbom = json.loads(first.sbom_path.read_text(encoding="utf-8"))
    assert sbom["spdxVersion"] == "SPDX-2.3"
    assert sbom["dataLicense"] == "CC0-1.0"
    assert sbom["documentNamespace"].endswith(SOURCE_SHA)
    assert sbom["documentDescribes"]
    assert sbom["packages"]
    assert "does not claim a complete native-file inventory" in sbom["documentComment"]


def test_release_evidence_binds_repository_source_and_provenance(tmp_path: Path) -> None:
    result = _write(tmp_path / "evidence")
    verified = verify_release_evidence_files(
        result.sbom_path,
        result.provenance_path,
        expected_source_sha=SOURCE_SHA,
        expected_repository=REPOSITORY,
    )
    assert verified["sbom_sha256"] == result.sbom_sha256
    assert verified["provenance_sha256"] == result.provenance_sha256
    assert verified["sbom"]["predicate_type"] == SPDX_PREDICATE_TYPE
    assert verified["sbom"]["inventory_complete"] is False
    assert verified["provenance"]["attestation_semantics"] == ATTESTATION_SEMANTICS


def test_tampered_sbom_breaks_provenance_digest_binding(tmp_path: Path) -> None:
    result = _write(tmp_path / "evidence")
    result.sbom_path.write_bytes(result.sbom_path.read_bytes() + b" ")
    with pytest.raises(ReleaseEvidenceError, match="SBOM digest mismatch"):
        verify_release_evidence_files(
            result.sbom_path,
            result.provenance_path,
            expected_source_sha=SOURCE_SHA,
            expected_repository=REPOSITORY,
        )


def test_cross_source_replay_is_rejected(tmp_path: Path) -> None:
    result = _write(tmp_path / "evidence")
    with pytest.raises(ReleaseEvidenceError):
        verify_release_evidence_files(
            result.sbom_path,
            result.provenance_path,
            expected_source_sha="f" * 40,
            expected_repository=REPOSITORY,
        )


def test_cross_repository_replay_is_rejected(tmp_path: Path) -> None:
    result = _write(tmp_path / "evidence")
    with pytest.raises(ReleaseEvidenceError):
        verify_release_evidence_files(
            result.sbom_path,
            result.provenance_path,
            expected_source_sha=SOURCE_SHA,
            expected_repository="example/other",
        )


def test_unknown_optional_runtime_group_is_rejected() -> None:
    with pytest.raises(ReleaseEvidenceError, match="unknown optional dependency group"):
        build_spdx_sbom(
            repo_root=ROOT,
            source_sha=SOURCE_SHA,
            repository=REPOSITORY,
            optional_groups=("does-not-exist",),
            created_at="2026-09-05T00:00:00Z",
        )


def test_provenance_never_claims_signing_or_publication(tmp_path: Path) -> None:
    result = _write(tmp_path / "evidence")
    provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
    assert provenance["production_signed"] is False
    assert provenance["github_release_published"] is False
    assert provenance["winget_published"] is False
    assert provenance["inventory"]["complete"] is False
    assert provenance["external_attestation"]["expected"] is True
    assert provenance["external_attestation"]["semantics"] == (
        "provenance_only_not_security_verdict"
    )
