from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.mobile.devicelab import (
    DeviceLabCapabilityState,
    DeviceLabDeviceSpec,
    DeviceLabMatrixDefinition,
    DeviceLabOrientation,
    DeviceLabPlatform,
    DeviceLabProviderCapability,
    DeviceLabProviderKind,
    DeviceLabResultState,
    DeviceLabTargetClass,
    normalize_verified_provider_result,
    select_provider,
)
from kodepoia.mobile.integrated_acceptance import (
    EvidenceBinding,
    R12_ACCEPTED_DIGEST,
    R13IntegratedCIEvidence,
    R13IntegratedReport,
    REQUIRED_ARTIFACT_KINDS,
    REQUIRED_RUNS,
    WorkflowArtifactBinding,
    WorkflowRunBinding,
    build_ci_evidence,
    build_repository_report,
    validate_repository_evidence,
)
from kodepoia.mobile.contracts import MobilePackageKind, MobilePlatform
from kodepoia.mobile.release import (
    PromotionDecision,
    PromotionRequest,
    ReleaseArtifactBinding,
    ReleaseAuthorityState,
    ReleaseCandidate,
    ReleaseChannel,
    ReleaseVersion,
    SemanticVersion,
    promote_release,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "f" * 40


def _runs() -> tuple[WorkflowRunBinding, ...]:
    return tuple(
        WorkflowRunBinding(name, 1000 + index, 200 + index, "success")
        for index, name in enumerate(REQUIRED_RUNS, start=1)
    )


def _artifacts() -> tuple[WorkflowArtifactBinding, ...]:
    values = (
        ("android_build", "R13 Android Build Acceptance", 2001, "android-build", "a" * 64),
        ("android_device", "R13 Android Device Acceptance", 2002, "android-device", "b" * 64),
        ("apple_xctest", "R13 Apple XCTest Acceptance", 2003, "apple-xctest", "c" * 64),
    )
    return tuple(WorkflowArtifactBinding(*value) for value in values)


def _ci() -> R13IntegratedCIEvidence:
    return build_ci_evidence(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-27T22:00:00Z",
        runs=_runs(),
        artifacts=_artifacts(),
    )


def _fake_repository() -> dict[str, bytes]:
    ci = _ci()
    repository: dict[str, bytes] = {
        "docs/continuity/KODEPOIA_CONTINUITY.md": b"# continuity\nR13.1-R13.17 integrated fixture\n",
        "docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json": json.dumps(
            {"status": "pass", "blockers": [], "evidence_sha256": R12_ACCEPTED_DIGEST},
            sort_keys=True,
        ).encode(),
        "docs/roadmap/R13_17_CI_ACCEPTANCE.json": (json.dumps(ci.to_dict(), sort_keys=True) + "\n").encode(),
    }
    for index in range(1, 18):
        repository[f"docs/roadmap/R13_{index}_ACCEPTANCE.md"] = (
            f"# R13.{index} acceptance\nfixture evidence\n"
        ).encode()
    return repository


def test_r13_17_ci_evidence_is_exact_head_semantic_and_schema_strict() -> None:
    evidence = _ci()
    assert tuple(item.name for item in evidence.runs) == REQUIRED_RUNS
    assert tuple(item.kind for item in evidence.artifacts) == REQUIRED_ARTIFACT_KINDS
    schema = json.loads((ROOT / "schemas/r13/r13-integrated-ci-acceptance.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(evidence.to_dict())

    changed = dict(evidence.to_dict())
    changed["generated_at"] = "2099-01-01T00:00:00Z"
    assert R13IntegratedCIEvidence.from_dict(changed).evidence_sha256 == evidence.evidence_sha256


def test_r13_17_integrated_report_binds_r12_all_subdivisions_and_ci() -> None:
    repository = _fake_repository()
    report = build_repository_report(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-27T22:30:00Z",
        read_bytes=repository.__getitem__,
    )
    validate_repository_evidence(report, repository.__getitem__)
    assert len(report.subdivisions) == 17
    assert report.ci.source_sha == SOURCE_SHA
    assert report.prior_phase.evidence_sha256 == R12_ACCEPTED_DIGEST
    assert report.status == "pass"
    assert report.blockers == ()

    schema = json.loads((ROOT / "schemas/r13/r13-integrated-acceptance.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(report.to_dict())


def test_r13_17_subdivision_continuity_ci_and_prior_substitution_fail_closed() -> None:
    repository = _fake_repository()
    report = build_repository_report(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-27T22:30:00Z",
        read_bytes=repository.__getitem__,
    )

    tampered = dict(repository)
    tampered["docs/roadmap/R13_8_ACCEPTANCE.md"] += b"tamper"
    with pytest.raises(ValueError, match="subdivision acceptance identity mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)

    tampered = dict(repository)
    tampered["docs/continuity/KODEPOIA_CONTINUITY.md"] += b"tamper"
    with pytest.raises(ValueError, match="continuity evidence identity mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)

    tampered = dict(repository)
    ci = json.loads(tampered["docs/roadmap/R13_17_CI_ACCEPTANCE.json"])
    ci["runs"][0]["conclusion"] = "failure"
    tampered["docs/roadmap/R13_17_CI_ACCEPTANCE.json"] = json.dumps(ci).encode()
    with pytest.raises(ValueError):
        validate_repository_evidence(report, tampered.__getitem__)

    tampered = dict(repository)
    prior = json.loads(tampered["docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json"])
    prior["evidence_sha256"] = "0" * 64
    tampered["docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json"] = json.dumps(prior).encode()
    with pytest.raises(ValueError, match="R12 integrated semantic digest drift"):
        validate_repository_evidence(report, tampered.__getitem__)


def test_r13_17_ci_claim_escalation_and_run_replay_are_rejected() -> None:
    payload = _ci().to_dict()
    forged = json.loads(json.dumps(payload))
    forged["claims"]["android_physical_device_claim"] = True
    with pytest.raises(ValueError, match="physical-device"):
        R13IntegratedCIEvidence.from_dict(forged)

    forged = json.loads(json.dumps(payload))
    forged["claims"]["live_store_query_attempted"] = True
    with pytest.raises(ValueError, match="live store"):
        R13IntegratedCIEvidence.from_dict(forged)

    forged = json.loads(json.dumps(payload))
    forged["runs"][1]["run_id"] = forged["runs"][0]["run_id"]
    semantic = {key: value for key, value in forged.items() if key not in {"generated_at", "evidence_sha256"}}
    from kodepoia.mobile.integrated_acceptance import canonical_sha256
    forged["evidence_sha256"] = canonical_sha256(semantic)
    with pytest.raises(ValueError, match="unique"):
        R13IntegratedCIEvidence.from_dict(forged)


def test_r13_17_report_digest_rejects_forgery_and_timestamp_is_not_semantic() -> None:
    repository = _fake_repository()
    report = build_repository_report(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-27T22:30:00Z",
        read_bytes=repository.__getitem__,
    )
    changed = dict(report.to_dict())
    changed["generated_at"] = "2099-01-01T00:00:00Z"
    assert R13IntegratedReport.from_dict(changed).evidence_sha256 == report.evidence_sha256

    forged = dict(report.to_dict())
    forged["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="semantic digest mismatch"):
        R13IntegratedReport.from_dict(forged)

    with pytest.raises(ValueError, match="escapes repository boundary"):
        EvidenceBinding("../escape", "a" * 64, 1)


def test_r13_17_virtual_devicelab_evidence_cannot_be_upgraded_to_physical() -> None:
    definition = DeviceLabMatrixDefinition(
        matrix_id="r13.integrated.android",
        platform=DeviceLabPlatform.ANDROID,
        artifact_sha256="a" * 64,
        test_execution_id="r13.integrated.tests",
        devices=(
            DeviceLabDeviceSpec(
                "Pixel 9",
                "16.0",
                "en-US",
                DeviceLabOrientation.PORTRAIT,
                DeviceLabTargetClass.VIRTUAL,
            ),
        ),
    )
    provider = DeviceLabProviderCapability(
        provider=DeviceLabProviderKind.LOCAL_ANDROID,
        platform=DeviceLabPlatform.ANDROID,
        target_classes=(DeviceLabTargetClass.VIRTUAL,),
        state=DeviceLabCapabilityState.AVAILABLE,
    )
    route = select_provider(definition, (provider,))
    with pytest.raises(ValueError, match="virtual evidence"):
        normalize_verified_provider_result(
            source_sha=SOURCE_SHA,
            matrix=definition,
            route=route,
            provider_result_sha256="b" * 64,
            result=DeviceLabResultState.PASSED,
            target_class=DeviceLabTargetClass.VIRTUAL,
            physical_device_proven=True,
        )


def test_r13_17_release_promotion_rejects_cross_evidence_substitution() -> None:
    artifact = ReleaseArtifactBinding(
        artifact_id="r13-integrated-aab",
        platform=MobilePlatform.ANDROID,
        package_kind=MobilePackageKind.AAB,
        artifact_sha256="a" * 64,
        provenance_sha256="b" * 64,
    )
    candidate = ReleaseCandidate(
        candidate_id="r13-integrated-candidate",
        train_id="mobile-stable",
        channel=ReleaseChannel.PRODUCTION,
        version=ReleaseVersion(product_version=SemanticVersion.parse("1.0.0"), android_version_code=1),
        artifacts=(artifact,),
        evidence_sha256=("c" * 64, "d" * 64),
        changelog_sha256="e" * 64,
        sbom_sha256="f" * 64,
        compliance_sha256="1" * 64,
    )
    state = ReleaseAuthorityState(train_id="mobile-stable", channel=ReleaseChannel.PRODUCTION)
    request = PromotionRequest(
        promotion_id="r13-integrated-promote",
        candidate=candidate,
        expected_revision=state.revision,
        expected_candidate_sha256=candidate.digest(),
        expected_artifact_set_sha256=candidate.artifact_set_sha256(),
        expected_evidence_set_sha256="9" * 64,
        expected_authoritative_candidate_sha256=state.authoritative_candidate_sha256,
    )
    outcome = promote_release(state, request)
    assert outcome.decision is PromotionDecision.EVIDENCE_SUBSTITUTION
    assert outcome.state is state


def test_r13_17_canonical_report_is_not_part_of_its_own_source_binding() -> None:
    repository = _fake_repository()
    report = build_repository_report(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-27T22:30:00Z",
        read_bytes=repository.__getitem__,
    )
    sources = {report.continuity.source, report.ci.source, report.prior_phase.source}
    sources.update(item.source for item in report.subdivisions)
    assert "docs/roadmap/R13_INTEGRATED_ACCEPTANCE.json" not in sources
