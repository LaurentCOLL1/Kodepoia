from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.release.windows_release_rehearsal import (
    CANDIDATE_INSTALLER_BYTES,
    CANDIDATE_INSTALLER_SHA256,
    CANDIDATE_PUBLIC_VERSION,
    CANDIDATE_SOURCE_SHA,
    CANDIDATE_V263_EVIDENCE_SHA256,
    RC8_INSTALLER_BYTES,
    RC8_INSTALLER_SHA256,
    RC8_PUBLIC_VERSION,
    TARGET_PATH,
    V263_ARTIFACT_ID,
    V263_ARTIFACT_NAME,
    V263_ARTIFACT_RUN_ID,
    V264_ACCEPTED_HEAD,
    V264_REQUEST_SHA256,
    build_contract_report,
    candidate_target,
    reconstruct_v264_request,
    synthetic_transition_status,
    validate_frozen_installer,
    validate_v263_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "a" * 40


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v265_frozen_public_baseline_and_candidate_are_exact() -> None:
    assert RC8_PUBLIC_VERSION == "1.1.0-rc8"
    assert RC8_INSTALLER_BYTES == 37_730_750
    assert RC8_INSTALLER_SHA256 == (
        "6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422"
    )

    assert CANDIDATE_PUBLIC_VERSION == "1.1.0"
    assert CANDIDATE_SOURCE_SHA == "46ed800888b4f19da9e984232dd1ad6cdb639cc1"
    assert CANDIDATE_INSTALLER_BYTES == 38_834_833
    assert CANDIDATE_INSTALLER_SHA256 == (
        "8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef"
    )
    assert CANDIDATE_V263_EVIDENCE_SHA256 == (
        "80192b517ebd6a607536f52892e5b23d05448138e63d7d222c30c7f4444dc3d8"
    )

    target = candidate_target()
    assert target.path == TARGET_PATH
    assert target.public_version == CANDIDATE_PUBLIC_VERSION
    assert target.source_sha == CANDIDATE_SOURCE_SHA
    assert target.channel == "stable"


def test_v265_reconstructs_exact_accepted_v264_request() -> None:
    request = reconstruct_v264_request(ROOT)
    assert V264_ACCEPTED_HEAD == "addbaf43b286f825ce42a11176c6647d15748845"
    assert request["request_sha256"] == V264_REQUEST_SHA256
    assert V264_REQUEST_SHA256 == (
        "a44914e80fb2fafb6b03f2a9847a78805b1ccb2a87fafedae9199f66c88bacea"
    )
    target = dict(request["requested_target"])
    assert target["path"] == TARGET_PATH
    assert target["length"] == CANDIDATE_INSTALLER_BYTES
    assert target["sha256"] == CANDIDATE_INSTALLER_SHA256
    assert dict(target["custom"])["authenticode_policy"] == "allow-unsigned"


def test_v265_synthetic_transition_is_forward_then_up_to_date(tmp_path: Path) -> None:
    fixture = b"v2.6.5 staged transport fixture\n"
    before, candidate = synthetic_transition_status(
        installer=fixture,
        installed_public_version=RC8_PUBLIC_VERSION,
        state_dir=tmp_path / "before",
    )
    after, current = synthetic_transition_status(
        installer=fixture,
        installed_public_version=CANDIDATE_PUBLIC_VERSION,
        state_dir=tmp_path / "after",
    )

    assert before == "update-available"
    assert candidate is not None
    assert candidate.target.path == TARGET_PATH
    assert after == "up-to-date"
    assert current is not None
    assert current.target.path == TARGET_PATH


def test_v265_contract_report_is_deterministic_and_has_no_live_effect() -> None:
    first = build_contract_report(SOURCE_SHA, repository_root=ROOT)
    second = build_contract_report(SOURCE_SHA, repository_root=ROOT)

    assert first == second
    assert first["status"] == "PASS"
    assert first["summary"] == {"passed": 8, "total": 8, "failed": []}
    assert first["fixture_only"] is True
    assert first["production_proof"] is False
    assert first["public_release_triggered"] is False
    assert first["production_tuf_mutation_triggered"] is False
    assert first["live_updater_activation_triggered"] is False
    assert len(str(first["evidence_sha256"])) == 64


def test_v265_frozen_installer_validation_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "KodepoiaSetup.exe"
    path.write_bytes(b"wrong")
    with pytest.raises(ValueError, match="length mismatch"):
        validate_frozen_installer(
            path,
            expected_size=CANDIDATE_INSTALLER_BYTES,
            expected_sha256=CANDIDATE_INSTALLER_SHA256,
            label="candidate",
        )


def test_v265_v263_evidence_binding_is_exact(tmp_path: Path) -> None:
    evidence = tmp_path / "V2_6_3_WINDOWS_CANDIDATE.json"
    evidence.write_text(
        json.dumps(
            {
                "status": "PASS",
                "candidate_source_sha": CANDIDATE_SOURCE_SHA,
                "evidence_sha256": CANDIDATE_V263_EVIDENCE_SHA256,
            }
        ),
        encoding="utf-8",
    )
    restored = validate_v263_evidence(evidence)
    assert restored["candidate_source_sha"] == CANDIDATE_SOURCE_SHA

    bad = dict(restored)
    bad["evidence_sha256"] = "0" * 64
    evidence.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="evidence digest drift"):
        validate_v263_evidence(evidence)


def test_v265_frozen_v263_artifact_authority_is_pinned() -> None:
    assert V263_ARTIFACT_RUN_ID == 37_151_521_725
    assert V263_ARTIFACT_ID == 11_284_279_492
    assert V263_ARTIFACT_NAME == (
        "v2-6-3-windows-candidate-46ed800888b4f19da9e984232dd1ad6cdb639cc1"
    )


def test_v265_workflow_is_exact_head_read_only_and_windows_real() -> None:
    workflow = _read(".github/workflows/v2-6-5-windows-release-rehearsal.yml")

    for marker in (
        "EVIDENCE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}",
        "Checkout exact V2.6.5 evidence source",
        "Download frozen V2.6.3 accepted candidate artifact",
        "Observe and download exact public rc8 baseline",
        "Run Windows V2.6.5 verified staging preflight",
        "Install public rc8 in custom directory and prove baseline",
        "Upgrade rc8 to the frozen candidate from staged verified bytes",
        "Run post-upgrade smoke, preservation checks and uninstall",
        "Clean install exact candidate and uninstall rehearsal",
        "Run final V2.6.5 go/no-go acceptance",
        "Upload V2.6.5 exact-head evidence",
    ):
        assert marker in workflow, marker

    assert "permissions:\n  contents: read" in workflow
    assert "run-id: 37151521725" in workflow
    assert V263_ARTIFACT_NAME in workflow
    assert "gh release download v1.1.0-rc8" in workflow
    assert "DisplayVersion" in workflow
    assert ".VersionInfo.ProductVersion" not in workflow
    assert "gh release create" not in workflow
    assert "git tag" not in workflow
    assert "tuf_release_ceremony" not in workflow
    assert "contents: write" not in workflow


def test_v265_contract_authorizes_v266_only_after_normalization() -> None:
    contract = _read("docs/release/V2_6_5_WINDOWS_RELEASE_REHEARSAL.md")
    assert "V2.6.6 remains unauthorized" in contract
    assert "post-merge normalization" in contract
    assert "no public GitHub Release" in contract
    assert "no live production TUF mutation" in contract
