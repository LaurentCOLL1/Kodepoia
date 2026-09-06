from __future__ import annotations

import hashlib

import pytest

from kodepoia.release.incident import (
    CompromisedCertificateTrustPolicy,
    IncidentDrillError,
    ReleaseIncidentDirective,
    run_synthetic_incident_drills,
)
from kodepoia.update.discovery import UpdateDiscoveryCandidate, UpdateDiscoveryResult
from kodepoia.update.trust import UpdateTargetSpec

SOURCE_SHA = "1" * 40


def _candidate() -> UpdateDiscoveryCandidate:
    data = b"candidate"
    return UpdateDiscoveryCandidate(
        target=UpdateTargetSpec(
            channel="beta",
            platform="windows-x86_64",
            public_version="1.1.0-rc1",
            source_sha=SOURCE_SHA,
        ),
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def test_r18_10_synthetic_drill_report_is_deterministic_and_passes(tmp_path) -> None:
    first = run_synthetic_incident_drills(
        source_sha=SOURCE_SHA,
        work_dir=tmp_path / "first",
    ).to_dict()
    second = run_synthetic_incident_drills(
        source_sha=SOURCE_SHA,
        work_dir=tmp_path / "second",
    ).to_dict()

    assert first == second
    assert first["status"] == "PASS"
    assert first["critical_bypass_count"] == 0
    assert first["provider_effect_count"] == 0
    assert first["project_data_mutation"] is False
    assert first["manual_intervention"] == "NONE"
    assert len(first["report_sha256"]) == 64

    scenarios = {item["scenario_id"]: item for item in first["scenarios"]}
    assert set(scenarios) == {
        "CERT-COMPROMISED-01",
        "TUF-ROOT-ROTATION-01",
        "TUF-ROOT-ROLLBACK-01",
        "TUF-TIMESTAMP-ROLLBACK-01",
        "TUF-SNAPSHOT-ROLLBACK-01",
        "TUF-TARGETS-ROLLBACK-01",
        "TUF-TIMESTAMP-FREEZE-01",
        "RELEASE-WITHDRAWN-01",
        "RELEASE-SUPERSEDED-01",
        "ASSET-TAMPER-01",
        "RECOVERY-LAST-KNOWN-GOOD-01",
    }
    assert all(item["passed"] for item in scenarios.values())
    assert scenarios["TUF-ROOT-ROTATION-01"]["actual_verdict"] == "ALLOW"
    assert scenarios["RECOVERY-LAST-KNOWN-GOOD-01"]["actual_verdict"] == "RECOVER"
    assert all(
        effect["status"] == "NOT_EXECUTED" for effect in first["provider_effects"]
    )


def test_r18_10_compromised_certificate_policy_is_fail_closed() -> None:
    policy = CompromisedCertificateTrustPolicy.from_thumbprints(["A" * 40])
    with pytest.raises(IncidentDrillError, match="blocked by incident trust policy"):
        policy.assert_trusted(
            {
                "subjects": [
                    {
                        "filename": "KodepoiaSetup.exe",
                        "signer_thumbprint": "A" * 40,
                    }
                ]
            }
        )


def test_r18_10_supersession_requires_tuf_verified_candidate() -> None:
    directive = ReleaseIncidentDirective(
        source_sha=SOURCE_SHA,
        public_version="1.1.0-rc1",
        superseded_by="1.1.0-rc2",
    )
    result = UpdateDiscoveryResult(
        status="update-available",
        candidate=_candidate(),
        detail="trusted metadata authorizes a newer update",
    )
    superseded = directive.apply(result)
    assert superseded.status == "update-superseded"
    assert superseded.candidate is result.candidate
    assert "1.1.0-rc2" in superseded.detail

    candidate = result.candidate
    assert candidate is not None
    unverified = UpdateDiscoveryCandidate(
        target=candidate.target,
        size_bytes=candidate.size_bytes,
        sha256=candidate.sha256,
        source_verification_state="unverified",
    )
    with pytest.raises(IncidentDrillError, match="TUF-verified"):
        directive.apply(
            UpdateDiscoveryResult(
                status="update-available",
                candidate=unverified,
                detail="untrusted fixture",
            )
        )


def test_r18_10_directive_rejects_mismatched_source() -> None:
    directive = ReleaseIncidentDirective(
        source_sha="2" * 40,
        public_version="1.1.0-rc1",
        withdrawn=True,
    )
    with pytest.raises(IncidentDrillError, match="source SHA"):
        directive.apply(
            UpdateDiscoveryResult(
                status="update-available",
                candidate=_candidate(),
                detail="candidate",
            )
        )
