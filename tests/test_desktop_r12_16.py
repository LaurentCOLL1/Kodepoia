from __future__ import annotations

import asyncio
import hashlib
import json
import struct
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.desktop.async_runtime import (
    AsyncOperationDescriptor,
    AsyncOperationKind,
    AsyncOperationRuntime,
    AsyncPolicy,
    OperationState,
)
from kodepoia.desktop.boundary import DesktopBoundaryError, validate_environment_overrides
from kodepoia.desktop.contracts import (
    DesktopArchitecture,
    DesktopFramework,
    DesktopOS,
    DesktopPackageKind,
)
from kodepoia.desktop.integrated_acceptance import (
    EvidenceBinding,
    R11_ACCEPTED_DIGEST,
    R12IntegratedReport,
    R12_WINDOWS_CI_PATH,
    WizardWindowsEvidence,
    build_repository_report,
    canonical_sha256,
    validate_repository_evidence,
)
from kodepoia.desktop.ipc import (
    IpcAuthenticationError,
    IpcEnvelope,
    IpcMessageKind,
    IpcPeerIdentity,
    IpcPolicy,
    IpcReplayError,
    ReplayWindow,
    decode_frame,
    encode_frame,
)
from kodepoia.desktop.packaging import (
    DesktopVersion,
    PackageIntegrityError,
    SigningState,
    build_artifact_manifest,
    verify_artifact_tree,
)
from kodepoia.desktop.persistence import QueryIntent, QueryOperation
from kodepoia.desktop.scaffold import DesktopScaffoldEngine, DesktopTemplateManifest, ScaffoldLineage, TemplateFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "f" * 40


def _windows_payload(source_sha: str = SOURCE_SHA) -> dict[str, object]:
    model = "d" * 64
    semantic = {
        "schema_version": 1,
        "source_sha": source_sha,
        "project_type": "desktop_app",
        "platform": "windows",
        "framework": "wpf",
        "architecture": "x64",
        "package_kind": "archive",
        "project_dna_sha256": "a" * 64,
        "product_sha256": "b" * 64,
        "workspace_manifest_sha256": "c" * 64,
        "model_sha256": model,
        "package_manifest_sha256": "e" * 64,
        "artifact_count": 3,
        "build_returncode": 0,
        "test_returncode": 0,
        "test_sentinel": f"KODEPOIA_WPF_TEST_PASS:{model}",
        "status": "pass",
        "blockers": [],
    }
    return {
        **semantic,
        "generated_at": "2026-08-25T12:00:00Z",
        "evidence_sha256": canonical_sha256(semantic),
    }


def _fake_repository() -> dict[str, bytes]:
    repository: dict[str, bytes] = {
        "docs/continuity/KODEPOIA_CONTINUITY.md": b"# continuity\nR12.1-R12.16 acceptance fixture\n",
        R12_WINDOWS_CI_PATH: (json.dumps(_windows_payload(), sort_keys=True) + "\n").encode(),
        "docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json": json.dumps(
            {"status": "pass", "blockers": [], "evidence_sha256": R11_ACCEPTED_DIGEST},
            sort_keys=True,
        ).encode(),
    }
    for index in range(1, 17):
        repository[f"docs/roadmap/R12_{index}_ACCEPTANCE.md"] = (
            f"# R12.{index} acceptance\nfixture evidence\n"
        ).encode()
    return repository


def test_r12_16_windows_ci_evidence_is_semantic_and_schema_strict() -> None:
    payload = _windows_payload()
    evidence = WizardWindowsEvidence.from_dict(payload)
    schema = json.loads(
        (ROOT / "schemas/r12/r12-windows-ci-acceptance.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(evidence.to_dict())

    changed = dict(payload)
    changed["generated_at"] = "2099-01-01T00:00:00Z"
    assert WizardWindowsEvidence.from_dict(changed).evidence_sha256 == evidence.evidence_sha256

    forged = dict(payload)
    forged["test_sentinel"] = "KODEPOIA_WPF_TEST_PASS:" + "0" * 64
    with pytest.raises(ValueError, match="sentinel"):
        WizardWindowsEvidence.from_dict(forged)


def test_r12_16_integrated_report_binds_all_subdivisions_windows_ci_and_r11() -> None:
    repository = _fake_repository()
    report = build_repository_report(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-25T12:30:00Z",
        read_bytes=repository.__getitem__,
    )
    validate_repository_evidence(report, repository.__getitem__)
    assert len(report.subdivisions) == 16
    assert report.windows_ci.source_sha == SOURCE_SHA
    assert report.prior_phase.evidence_sha256 == R11_ACCEPTED_DIGEST
    assert report.status == "pass"
    assert report.blockers == ()

    schema = json.loads(
        (ROOT / "schemas/r12/r12-integrated-acceptance.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(report.to_dict())


def test_r12_16_integrated_report_detects_acceptance_continuity_and_ci_substitution() -> None:
    repository = _fake_repository()
    report = build_repository_report(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-25T12:30:00Z",
        read_bytes=repository.__getitem__,
    )

    tampered = dict(repository)
    tampered["docs/roadmap/R12_8_ACCEPTANCE.md"] += b"tamper"
    with pytest.raises(ValueError, match="subdivision acceptance identity mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)

    tampered = dict(repository)
    tampered["docs/continuity/KODEPOIA_CONTINUITY.md"] += b"tamper"
    with pytest.raises(ValueError, match="continuity evidence identity mismatch"):
        validate_repository_evidence(report, tampered.__getitem__)

    tampered = dict(repository)
    ci = json.loads(tampered[R12_WINDOWS_CI_PATH])
    ci["status"] = "fail"
    ci["blockers"] = ["synthetic"]
    tampered[R12_WINDOWS_CI_PATH] = json.dumps(ci, sort_keys=True).encode()
    with pytest.raises(ValueError):
        validate_repository_evidence(report, tampered.__getitem__)


def test_r12_16_prior_r11_semantic_substitution_cannot_be_rebound() -> None:
    repository = _fake_repository()
    prior = json.loads(repository["docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json"])
    prior["evidence_sha256"] = "0" * 64
    repository["docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json"] = json.dumps(prior).encode()
    with pytest.raises(ValueError, match="R11 integrated semantic digest drift"):
        build_repository_report(
            source_sha=SOURCE_SHA,
            generated_at="2026-08-25T12:30:00Z",
            read_bytes=repository.__getitem__,
        )


def test_r12_16_report_digest_rejects_forgery_and_timestamp_is_not_semantic() -> None:
    repository = _fake_repository()
    report = build_repository_report(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-25T12:30:00Z",
        read_bytes=repository.__getitem__,
    )
    payload = report.to_dict()
    changed = dict(payload)
    changed["generated_at"] = "2099-01-01T00:00:00Z"
    assert R12IntegratedReport.from_dict(changed).evidence_sha256 == report.evidence_sha256

    forged = dict(payload)
    forged["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="semantic digest mismatch"):
        R12IntegratedReport.from_dict(forged)

    with pytest.raises(ValueError, match="escapes repository boundary"):
        EvidenceBinding("../escape", "a" * 64, 1)


def test_r12_16_path_identifier_environment_and_raw_sql_attacks_fail_closed() -> None:
    malicious = DesktopTemplateManifest(
        1,
        "bad",
        "1.0",
        (TemplateFile("../owned.txt", "x"),),
    )
    with pytest.raises(ValueError, match="unsafe scaffold path"):
        DesktopScaffoldEngine().render(
            malicious,
            {},
            ScaffoldLineage("a" * 64, "b" * 64),
        )
    with pytest.raises(DesktopBoundaryError, match="not allowlisted"):
        validate_environment_overrides({"DOTNET_ROOT": "C:/owned"})
    with pytest.raises(ValueError, match="invalid query table"):
        QueryIntent(QueryOperation.SELECT, 'items"; DROP TABLE items; --').compile()


def _ipc_message(message_id: str = "msg-1") -> IpcEnvelope:
    return IpcEnvelope(
        1,
        message_id,
        IpcMessageKind.REQUEST,
        "project.status",
        IpcPeerIdentity("peer", "session", "worker"),
        {"value": 1},
    )


def test_r12_16_ipc_tamper_replay_and_oversize_fail_closed() -> None:
    key = b"k" * 32
    policy = IpcPolicy(max_frame_bytes=512)
    frame = encode_frame(_ipc_message(), key, policy)
    replay = ReplayWindow(2)
    assert decode_frame(frame, key, policy, replay_window=replay).message_id == "msg-1"
    with pytest.raises(IpcReplayError):
        decode_frame(frame, key, policy, replay_window=replay)

    outer = json.loads(frame[4:].decode("utf-8"))
    outer["body"]["payload"]["value"] = 2
    tampered = json.dumps(outer, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(IpcAuthenticationError):
        decode_frame(struct.pack(">I", len(tampered)) + tampered, key, policy)

    with pytest.raises(Exception):
        encode_frame(_ipc_message("big").__class__(
            1,
            "big",
            IpcMessageKind.REQUEST,
            "project.status",
            IpcPeerIdentity("peer", "session", "worker"),
            {"blob": "x" * 2000},
        ), key, policy)


def test_r12_16_cancellation_race_cleans_owned_operation() -> None:
    async def scenario() -> None:
        kill_switch = KillSwitch()
        runtime = AsyncOperationRuntime(AsyncPolicy(operation_timeout_seconds=1.0), kill_switch=kill_switch)
        runtime.open_owner("integrated")
        entered = asyncio.Event()
        continue_work = asyncio.Event()

        async def work(context):
            entered.set()
            await continue_work.wait()
            await context.checkpoint()
            return "unreachable"

        handle = runtime.start(
            AsyncOperationDescriptor("integrated-build", "integrated", AsyncOperationKind.BUILD),
            work,
        )
        await entered.wait()
        kill_switch.trigger()
        continue_work.set()
        with pytest.raises(asyncio.CancelledError):
            await handle.wait()
        assert handle.state is OperationState.CANCELLED
        await runtime.close_owner("integrated")
        assert runtime.active_count == 0

    asyncio.run(scenario())


def test_r12_16_package_manifest_detects_post_build_tampering(tmp_path: Path) -> None:
    root = tmp_path / "artifact"
    (root / "bin").mkdir(parents=True)
    target = root / "bin/app.exe"
    target.write_bytes(b"accepted")
    manifest = build_artifact_manifest(
        root,
        package_id="kodepoia.r12.integrated.fixture",
        version=DesktopVersion(1, 0, 0),
        framework=DesktopFramework.WPF,
        platform=DesktopOS.WINDOWS,
        architecture=DesktopArchitecture.X64,
        package_kind=DesktopPackageKind.ARCHIVE,
        signing_state=SigningState.UNSIGNED,
        executable_paths=("bin/app.exe",),
    )
    verify_artifact_tree(root, manifest)
    target.write_bytes(b"tampered")
    with pytest.raises(PackageIntegrityError, match="digest mismatch|size mismatch"):
        verify_artifact_tree(root, manifest)


def test_r12_16_canonical_report_is_not_part_of_its_own_source_binding() -> None:
    repository = _fake_repository()
    report = build_repository_report(
        source_sha=SOURCE_SHA,
        generated_at="2026-08-25T12:30:00Z",
        read_bytes=repository.__getitem__,
    )
    sources = {report.continuity.source, report.windows_ci.source, report.prior_phase.source}
    sources.update(item.source for item in report.subdivisions)
    assert "docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json" not in sources
