from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from kodepoia.backend.integrated_acceptance import (
    R13_ACCEPTED_DIGEST,
    R13_INTEGRATED_PATH,
    R14_CI_PATH,
    R14_DESIGN_PATH,
    R14_INTEGRATED_REPORT_PATH,
    R14_SCENARIO_PATH,
    R14_SUBDIVISION_PATHS,
    REQUIRED_RUNS,
    IntegratedCIEvidence,
    IntegratedReport,
    WorkflowArtifactBinding,
    WorkflowRunBinding,
    build_ci_evidence,
    build_repository_report,
    canonical_sha256,
    validate_repository_evidence,
)


SOURCE = "a" * 40


def _ci(source: str = SOURCE) -> IntegratedCIEvidence:
    runs = tuple(
        WorkflowRunBinding(name, index + 1, index + 101)
        for index, name in enumerate(REQUIRED_RUNS)
    )
    artifacts = (
        WorkflowArtifactBinding(
            "integrated_scenario",
            "R14 Integrated Acceptance",
            91,
            "R14_17_INTEGRATED_SCENARIO",
            "b" * 64,
        ),
    )
    return build_ci_evidence(
        source_sha=source,
        generated_at="2026-08-29T17:00:00Z",
        runs=runs,
        artifacts=artifacts,
    )


def _scenario(source: str = SOURCE) -> bytes:
    return (
        json.dumps(
            {
                "schema_version": 1,
                "source_sha": source,
                "status": "pass",
                "blockers": [],
                "manual_state": "conditional_not_triggered",
                "provider_live_claim": False,
                "secrets_exposed": False,
                "pii_exposed": False,
                "production_publish_claim": False,
            },
            sort_keys=True,
        )
        + "\n"
    ).encode()


def _repository(source: str = SOURCE) -> dict[str, bytes]:
    files: dict[str, bytes] = {
        R13_INTEGRATED_PATH: (json.dumps({"evidence_sha256": R13_ACCEPTED_DIGEST}) + "\n").encode(),
        R14_CI_PATH: (json.dumps(_ci(source).to_dict(), sort_keys=True) + "\n").encode(),
        R14_SCENARIO_PATH: _scenario(source),
        R14_DESIGN_PATH: b"# R14.17 design\nanti-circular evidence\n",
    }
    files.update({path: f"# {path}\naccepted\n".encode() for path in R14_SUBDIVISION_PATHS})
    return files


def test_ci_evidence_requires_exact_ordered_fresh_run_set() -> None:
    evidence = _ci()
    assert tuple(run.name for run in evidence.runs) == REQUIRED_RUNS
    assert evidence.status == "pass"
    assert evidence.provider_live_claim is False
    assert evidence.evidence_sha256 == canonical_sha256(evidence.payload_without_digest())


def test_ci_evidence_rejects_tampered_digest() -> None:
    raw = _ci().to_dict()
    raw["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="digest mismatch"):
        IntegratedCIEvidence.from_dict(raw)


def test_ci_evidence_rejects_provider_live_overclaim() -> None:
    raw = _ci().to_dict()
    raw["provider_live_claim"] = True
    without_digest = {key: value for key, value in raw.items() if key != "evidence_sha256"}
    raw["evidence_sha256"] = canonical_sha256(without_digest)
    with pytest.raises(ValueError, match="provider-live"):
        IntegratedCIEvidence.from_dict(raw)


def test_repository_report_binds_prior_phase_and_r14_1_through_16_without_self_reference() -> None:
    files = _repository()
    report = build_repository_report(
        source_sha=SOURCE,
        generated_at=datetime.now(timezone.utc).isoformat(),
        read_bytes=files.__getitem__,
    )
    assert report.prior_phase.source == R13_INTEGRATED_PATH
    assert tuple(item.source for item in report.subdivision_acceptance) == R14_SUBDIVISION_PATHS
    bound_sources = {
        report.prior_phase.source,
        *(item.source for item in report.subdivision_acceptance),
        report.design.source,
        report.scenario.source,
        report.ci.source,
    }
    assert R14_INTEGRATED_REPORT_PATH not in bound_sources
    validate_repository_evidence(report, files.__getitem__)


def test_repository_report_rejects_mixed_source_sha() -> None:
    files = _repository()
    files[R14_SCENARIO_PATH] = _scenario("c" * 40)
    with pytest.raises(ValueError, match="mixes source SHAs"):
        build_repository_report(
            source_sha=SOURCE,
            generated_at="2026-08-29T17:00:00Z",
            read_bytes=files.__getitem__,
        )


def test_repository_report_rejects_prior_phase_semantic_drift() -> None:
    files = _repository()
    files[R13_INTEGRATED_PATH] = (json.dumps({"evidence_sha256": "d" * 64}) + "\n").encode()
    with pytest.raises(ValueError, match="R13 integrated semantic digest drift"):
        build_repository_report(
            source_sha=SOURCE,
            generated_at="2026-08-29T17:00:00Z",
            read_bytes=files.__getitem__,
        )


def test_offline_verifier_detects_bound_file_tamper() -> None:
    files = _repository()
    report = build_repository_report(
        source_sha=SOURCE,
        generated_at="2026-08-29T17:00:00Z",
        read_bytes=files.__getitem__,
    )
    files[R14_DESIGN_PATH] += b"tampered\n"
    with pytest.raises(ValueError, match="bound evidence drift"):
        validate_repository_evidence(report, files.__getitem__)


def test_report_rejects_synthetic_production_claim() -> None:
    files = _repository()
    report = build_repository_report(
        source_sha=SOURCE,
        generated_at="2026-08-29T17:00:00Z",
        read_bytes=files.__getitem__,
    )
    raw = report.to_dict()
    raw["production_publish_claim"] = True
    without_digest = {key: value for key, value in raw.items() if key != "evidence_sha256"}
    raw["evidence_sha256"] = canonical_sha256(without_digest)
    with pytest.raises(ValueError, match="unsupported live/sensitive claim"):
        IntegratedReport.from_dict(raw)
