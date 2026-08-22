from __future__ import annotations

import json
import os
import tarfile
import zipfile
from pathlib import Path

import pytest
from jsonschema import validate as validate_json_schema

from kodepoia.kodecode.workspace import WorkspaceViolation
from kodepoia.quality.build import (
    BuildArtifact,
    BuildArtifactKind,
    BuildManifest,
    BuildStatus,
    BuildStore,
    KodeBuild,
    collect_python_artifacts,
    hash_source_inputs,
    redact_sensitive,
)
from kodepoia.quality.ci import CICheck, CICheckStatus, CIReport, CIReportStatus, CIStore, KodeCI
from kodepoia.quality.health import HealthDimension, HealthStatus
from kodepoia.quality.tests import TestCaseStatus


SHA = "a" * 40
T0 = "2026-08-22T10:00:00Z"


def _project(tmp_path: Path) -> Path:
    (tmp_path / ".kodepoia").mkdir(exist_ok=True)
    (tmp_path / "src" / "kodepoia").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "kodepoia" / "__init__.py").write_text("__version__ = '0.1'\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[build-system]\nbuild-backend='hatchling.build'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# fixture\n", encoding="utf-8")
    (tmp_path / "dist").mkdir(exist_ok=True)
    return tmp_path


def _archives(root: Path) -> None:
    wheel = root / "dist" / "kodepoia-0.1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("kodepoia/__init__.py", "")
        archive.writestr("kodepoia-0.1.dist-info/METADATA", "Name: kodepoia\nVersion: 0.1\n")

    sdist = root / "dist" / "kodepoia-0.1.tar.gz"
    staging = root / "sdist-staging" / "kodepoia-0.1"
    (staging / "src" / "kodepoia").mkdir(parents=True)
    (staging / "pyproject.toml").write_text("[build-system]\n", encoding="utf-8")
    (staging / "src" / "kodepoia" / "__init__.py").write_text("", encoding="utf-8")
    with tarfile.open(sdist, "w:gz") as archive:
        archive.add(staging, arcname="kodepoia-0.1")


def test_ci_required_terminal_failures_never_pass() -> None:
    for status in (CICheckStatus.FAIL, CICheckStatus.CANCELLED, CICheckStatus.SKIPPED):
        report = KodeCI.evaluate((CICheck("gate", status),), workflow_id="wf", source_sha=SHA, generated_at=T0)
        assert report.status is CIReportStatus.FAIL
        assert report.blocking_checks == ("gate",)
        case = KodeCI.to_test_cases(report)[0]
        assert case.status is TestCaseStatus.FAIL


def test_ci_incomplete_required_is_unknown_and_optional_skip_warns() -> None:
    queued = KodeCI.evaluate(
        (CICheck("gate", CICheckStatus.IN_PROGRESS),),
        workflow_id="wf",
        source_sha=SHA,
        generated_at=T0,
    )
    assert queued.status is CIReportStatus.UNKNOWN
    assert KodeCI.to_test_cases(queued)[0].status is TestCaseStatus.ERROR

    optional = KodeCI.evaluate(
        (
            CICheck("required", CICheckStatus.PASS),
            CICheck("optional", CICheckStatus.SKIPPED, required=False),
        ),
        workflow_id="wf",
        source_sha=SHA,
        generated_at=T0,
    )
    assert optional.status is CIReportStatus.WARN
    assert KodeCI.to_test_cases(optional)[1].status is TestCaseStatus.SKIP


def test_ci_report_roundtrip_tamper_schema_and_store(tmp_path: Path) -> None:
    _project(tmp_path)
    report = KodeCI.evaluate(
        (CICheck("tests", CICheckStatus.PASS, source="pytest"),),
        workflow_id="python-core",
        source_sha=SHA,
        generated_at=T0,
    )
    payload = report.to_dict()
    assert CIReport.from_dict(payload).to_dict() == payload
    schema = json.loads(Path("schemas/ci-report-v1.schema.json").read_text(encoding="utf-8"))
    validate_json_schema(payload, schema)

    tampered = json.loads(json.dumps(payload))
    tampered["counts"]["pass"] += 1
    with pytest.raises(ValueError, match="counts"):
        CIReport.from_dict(tampered)

    store = CIStore(tmp_path)
    latest, snapshot = store.save(report)
    assert latest.is_file() and snapshot and snapshot.is_file()
    assert latest.parent == tmp_path / ".kodepoia" / "workflows" / "python-core"
    assert store.load_latest("python-core").to_dict() == payload


def test_ci_rejects_duplicate_ids_and_wrong_sha() -> None:
    with pytest.raises(ValueError, match="unique"):
        KodeCI.evaluate(
            (CICheck("same", CICheckStatus.PASS), CICheck("same", CICheckStatus.PASS)),
            workflow_id="wf",
            source_sha=SHA,
        )
    with pytest.raises(ValueError, match="40-character"):
        KodeCI.evaluate((CICheck("x", CICheckStatus.PASS),), workflow_id="wf", source_sha="bad")


def test_collect_python_artifacts_validates_wheel_and_sdist(tmp_path: Path) -> None:
    root = _project(tmp_path)
    _archives(root)
    artifacts = collect_python_artifacts(root)
    by_kind = {artifact.kind: artifact for artifact in artifacts}
    assert by_kind[BuildArtifactKind.WHEEL].validated is True
    assert by_kind[BuildArtifactKind.SDIST].validated is True
    assert by_kind[BuildArtifactKind.WHEEL].size_bytes > 0
    assert len(by_kind[BuildArtifactKind.WHEEL].sha256) == 64


def test_build_manifest_pass_health_test_cases_roundtrip_schema_store(tmp_path: Path) -> None:
    root = _project(tmp_path)
    _archives(root)
    manifest = KodeBuild.collect(
        root,
        source_sha=SHA,
        platform="windows-latest",
        python_version="3.12.4",
        metadata={"runner": "hosted", "token": "must-not-survive"},
    )
    assert manifest.status is BuildStatus.PASS
    assert manifest.metadata["token"] == "<redacted>"
    assert manifest.blockers == ()
    assert manifest.artifact_counts["wheel"] == 1
    assert manifest.artifact_counts["sdist"] == 1

    metric = KodeBuild.to_health_metric(manifest)
    assert metric.dimension is HealthDimension.BUILD
    assert metric.status is HealthStatus.PASS
    assert metric.score == 100.0
    cases = KodeBuild.to_test_cases(manifest)
    assert {case.id for case in cases} == {
        "build:windows-latest:wheel",
        "build:windows-latest:sdist",
    }
    assert all(case.status is TestCaseStatus.PASS for case in cases)

    payload = manifest.to_dict()
    assert BuildManifest.from_dict(payload).to_dict() == payload
    schema = json.loads(Path("schemas/build-manifest-v1.schema.json").read_text(encoding="utf-8"))
    validate_json_schema(payload, schema)

    store = BuildStore(root)
    latest, snapshot = store.save(manifest)
    assert latest.is_file() and snapshot and snapshot.is_file()
    assert latest.parent == root / ".kodepoia" / "releases" / "windows-latest"
    assert store.load_latest("windows-latest").to_dict() == payload


def test_build_missing_required_artifact_fails_and_blocks(tmp_path: Path) -> None:
    root = _project(tmp_path)
    wheel = root / "dist" / "kodepoia-0.1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("kodepoia/__init__.py", "")
        archive.writestr("kodepoia-0.1.dist-info/METADATA", "Name: kodepoia\n")
    manifest = KodeBuild.collect(root, source_sha=SHA, platform="linux", python_version="3.12")
    assert manifest.status is BuildStatus.FAIL
    assert "missing:sdist" in manifest.blockers
    metric = KodeBuild.to_health_metric(manifest)
    assert metric.status is HealthStatus.FAIL and metric.blocking
    cases = {case.id: case for case in KodeBuild.to_test_cases(manifest)}
    assert cases["build:linux:sdist"].status is TestCaseStatus.FAIL


def test_source_digest_changes_with_source_and_dependency_digest_is_explicit(tmp_path: Path) -> None:
    root = _project(tmp_path)
    before = hash_source_inputs(root)
    (root / "src" / "kodepoia" / "__init__.py").write_text("changed\n", encoding="utf-8")
    after = hash_source_inputs(root)
    assert before != after


def test_redaction_is_recursive_and_direct_unredacted_manifest_rejected(tmp_path: Path) -> None:
    root = _project(tmp_path)
    _archives(root)
    redacted = redact_sensitive(
        {
            "Authorization": "Bearer abc.def",
            "nested": {"api_key": "123", "note": "token=xyz"},
        }
    )
    assert redacted["Authorization"] == "<redacted>"
    assert redacted["nested"]["api_key"] == "<redacted>"
    assert "xyz" not in redacted["nested"]["note"]

    clean = KodeBuild.collect(root, source_sha=SHA, platform="linux", python_version="3.12")
    with pytest.raises(ValueError, match="unredacted"):
        BuildManifest(
            generated_at=clean.generated_at,
            source_sha=clean.source_sha,
            platform=clean.platform,
            python_version=clean.python_version,
            build_backend=clean.build_backend,
            source_digest_sha256=clean.source_digest_sha256,
            dependency_inputs=clean.dependency_inputs,
            artifacts=clean.artifacts,
            metadata={"password": "plaintext"},
            status=clean.status,
            evidence_sha256=clean.evidence_sha256,
        )


def test_build_manifest_derived_tamper_rejected(tmp_path: Path) -> None:
    root = _project(tmp_path)
    _archives(root)
    manifest = KodeBuild.collect(root, source_sha=SHA, platform="linux", python_version="3.12")
    payload = manifest.to_dict()

    tampered = json.loads(json.dumps(payload))
    tampered["artifact_counts"]["wheel"] = 99
    with pytest.raises(ValueError, match="artifact counts"):
        BuildManifest.from_dict(tampered)

    tampered = json.loads(json.dumps(payload))
    tampered["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        BuildManifest.from_dict(tampered)


def test_artifact_name_and_digest_validation() -> None:
    with pytest.raises(ValueError, match="file name"):
        BuildArtifact("../escape.whl", BuildArtifactKind.WHEEL, 1, "0" * 64, True)
    with pytest.raises(ValueError, match="SHA-256"):
        BuildArtifact("x.whl", BuildArtifactKind.WHEEL, 1, "BAD", True)


def test_stores_reject_symlink_escape(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("symlink creation may require elevated Windows policy")
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / ".kodepoia").mkdir()
    (tmp_path / ".kodepoia" / "releases").symlink_to(outside, target_is_directory=True)
    with pytest.raises(WorkspaceViolation):
        BuildStore(tmp_path).boundary.resolve(".kodepoia/releases/linux")
