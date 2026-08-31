from __future__ import annotations

import json

import pytest

from kodepoia.tuning.integrated_acceptance import CHECK_NAMES, canonical_sha256
from kodepoia.tuning.integrated_evidence import (
    R14_ACCEPTED_DIGEST,
    R14_INTEGRATED_PATH,
    R15_CI_PATH,
    R15_DESIGN_PATH,
    R15_SCENARIO_PATH,
    R15_SUBDIVISION_PATHS,
    IntegratedCIEvidence,
    WorkflowArtifactBinding,
    WorkflowRunBinding,
    build_ci_evidence,
    build_repository_report,
    validate_repository_evidence,
)

SOURCE_SHA = "a" * 40


def _runs() -> tuple[WorkflowRunBinding, ...]:
    return (
        WorkflowRunBinding("R0 Repository Guard", 101, 1),
        WorkflowRunBinding("Python Core", 102, 2),
        WorkflowRunBinding("KodeStudio UI Smoke", 103, 3),
        WorkflowRunBinding("R15 Integrated Acceptance", 104, 4),
    )


def _artifact(source_sha: str = SOURCE_SHA) -> WorkflowArtifactBinding:
    return WorkflowArtifactBinding(
        "integrated_scenario",
        "R15 Integrated Acceptance",
        201,
        f"R15_17_INTEGRATED_SCENARIO-{source_sha}",
        "f" * 64,
    )


def _scenario(source_sha: str = SOURCE_SHA) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "kodepoia.r15.integrated-acceptance",
        "schema_version": 1,
        "source_sha": source_sha,
        "checks": {name: True for name in CHECK_NAMES},
        "check_count": len(CHECK_NAMES),
        "identities": {
            "dataset": "1" * 64,
            "benchmark_suite": "2" * 64,
            "benchmark_protection": "3" * 64,
            "base_model": "4" * 64,
            "training_plan": "5" * 64,
            "adapter": "6" * 64,
            "evaluation_binding": "7" * 64,
            "quantization_policy": "8" * 64,
        },
        "manual_state": "conditional_not_triggered",
        "optional_capability_state": "unavailable",
        "secrets_exposed": False,
        "status": "pass",
        "blockers": [],
    }
    payload["semantic_digest"] = canonical_sha256(payload)
    return payload


def _ci(source_sha: str = SOURCE_SHA) -> IntegratedCIEvidence:
    return build_ci_evidence(
        source_sha=source_sha,
        generated_at="2026-08-31T00:00:00Z",
        runs=_runs(),
        artifacts=(_artifact(source_sha),),
    )


def _repository_bytes(
    *,
    scenario_sha: str = SOURCE_SHA,
    ci_sha: str = SOURCE_SHA,
) -> dict[str, bytes]:
    values = {
        R14_INTEGRATED_PATH: json.dumps(
            {"evidence_sha256": R14_ACCEPTED_DIGEST},
            sort_keys=True,
        ).encode("utf-8"),
        R15_DESIGN_PATH: b"# R15.17 design fixture\n",
        R15_SCENARIO_PATH: json.dumps(
            _scenario(scenario_sha),
            sort_keys=True,
        ).encode("utf-8"),
        R15_CI_PATH: json.dumps(_ci(ci_sha).to_dict(), sort_keys=True).encode("utf-8"),
    }
    for path in R15_SUBDIVISION_PATHS:
        values[path] = f"# accepted {path}\n".encode()
    return values


def test_ci_authority_binds_exact_runs_artifact_and_semantic_digest() -> None:
    evidence = _ci()
    assert evidence.source_sha == SOURCE_SHA
    assert tuple(item.name for item in evidence.runs) == (
        "R0 Repository Guard",
        "Python Core",
        "KodeStudio UI Smoke",
        "R15 Integrated Acceptance",
    )
    assert evidence.artifacts[0].name.endswith(SOURCE_SHA)
    assert evidence.evidence_sha256 == canonical_sha256(evidence.payload_without_digest())
    assert IntegratedCIEvidence.from_dict(evidence.to_dict()) == evidence


def test_ci_authority_rejects_artifact_from_another_source() -> None:
    with pytest.raises(ValueError, match="artifact name/source SHA mismatch"):
        build_ci_evidence(
            source_sha=SOURCE_SHA,
            generated_at="2026-08-31T00:00:00Z",
            runs=_runs(),
            artifacts=(_artifact("b" * 40),),
        )


def test_repository_report_rehashes_every_bound_file() -> None:
    values = _repository_bytes()
    report = build_repository_report(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-31T00:00:01Z",
        read_bytes=values.__getitem__,
    )
    validate_repository_evidence(report, values.__getitem__)
    assert report.status == "pass"
    assert report.blockers == ()
    assert len(report.subdivision_acceptance) == 16
    assert report.evidence_sha256 == canonical_sha256(report.payload_without_digest())

    values[R15_DESIGN_PATH] += b"tampered"
    with pytest.raises(ValueError, match="bound evidence drift"):
        validate_repository_evidence(report, values.__getitem__)


def test_repository_report_rejects_mixed_scenario_and_ci_source_sha() -> None:
    values = _repository_bytes(ci_sha="b" * 40)
    with pytest.raises(ValueError, match="mixes source SHAs"):
        build_repository_report(
            source_sha=SOURCE_SHA,
            generated_at="2026-08-31T00:00:01Z",
            read_bytes=values.__getitem__,
        )


def test_repository_report_rejects_prior_phase_semantic_drift() -> None:
    values = _repository_bytes()
    values[R14_INTEGRATED_PATH] = json.dumps(
        {"evidence_sha256": "0" * 64},
        sort_keys=True,
    ).encode("utf-8")
    with pytest.raises(ValueError, match="R14 integrated semantic digest drift"):
        build_repository_report(
            source_sha=SOURCE_SHA,
            generated_at="2026-08-31T00:00:01Z",
            read_bytes=values.__getitem__,
        )
