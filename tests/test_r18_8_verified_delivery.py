from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from kodepoia.update.delivery import (
    AuthenticodeEvidence,
    InstallerIdentityEvidence,
    MemoryStreamingTargetTransport,
    UpdateConsentRequired,
    UpdateDownloadCancelled,
    UpdateInstallCoordinator,
    UpdateVerificationFailed,
    VerifiedUpdateDownloader,
)
from kodepoia.update.discovery import UpdateDiscoveryCandidate
from kodepoia.update.trust import UpdateTargetSpec

SOURCE_SHA = "a" * 40


class _Auth:
    def __init__(self, verified: bool = True) -> None:
        self.verified = verified

    def verify(self, path: Path) -> AuthenticodeEvidence:
        assert path.is_file()
        return AuthenticodeEvidence(
            verified=self.verified,
            status="valid" if self.verified else "invalid",
            detail="synthetic Authenticode acceptance",
        )


class _Identity:
    def __init__(self, verified: bool = True) -> None:
        self.verified = verified

    def verify(self, path: Path, *, expected_public_version: str) -> InstallerIdentityEvidence:
        assert path.is_file()
        return InstallerIdentityEvidence(
            verified=self.verified,
            public_version=expected_public_version if self.verified else "0.0.0",
            detail=(
                f"ProductVersion={expected_public_version!r}"
                if self.verified
                else "ProductVersion mismatch"
            ),
        )


class _Launcher:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def launch(self, path: Path) -> None:
        self.paths.append(path)


def _candidate(data: bytes = b"verified-installer") -> UpdateDiscoveryCandidate:
    target = UpdateTargetSpec(
        channel="beta",
        platform="windows-x86_64",
        public_version="1.1.0-rc2",
        source_sha=SOURCE_SHA,
    )
    return UpdateDiscoveryCandidate(
        target=target,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def _downloader(
    tmp_path: Path, *, auth: bool = True, identity: bool = True, max_bytes: int = 1024
) -> VerifiedUpdateDownloader:
    return VerifiedUpdateDownloader(
        tmp_path / "cache",
        authenticode=_Auth(auth),
        identity=_Identity(identity),
        max_installer_bytes=max_bytes,
        chunk_size=3,
    )


def test_r18_8_verified_download_atomically_finalizes_after_all_checks(tmp_path: Path) -> None:
    data = b"verified-installer"
    candidate = _candidate(data)
    transport = MemoryStreamingTargetTransport({candidate.target.path: data})
    artifact = _downloader(tmp_path).stage(candidate, transport)

    assert artifact.path.is_file()
    assert artifact.path.read_bytes() == data
    assert artifact.sha256 == candidate.sha256
    assert artifact.size_bytes == candidate.size_bytes
    assert artifact.authenticode_status == "valid"
    assert not (artifact.path.parent / f".{candidate.target.filename}.partial").exists()
    evidence = artifact.path.parent / "verified-update.json"
    assert evidence.is_file()
    assert "user_consent_required_before_launch" in evidence.read_text(encoding="utf-8")


def test_r18_8_wrong_hash_fails_before_executable_finalize(tmp_path: Path) -> None:
    candidate = replace(_candidate(), sha256="0" * 64)
    transport = MemoryStreamingTargetTransport({candidate.target.path: b"verified-installer"})
    with pytest.raises(UpdateVerificationFailed, match="SHA-256"):
        _downloader(tmp_path).stage(candidate, transport)
    final = tmp_path / "cache" / "beta" / "1.1.0-rc2" / SOURCE_SHA / "KodepoiaSetup.exe"
    assert not final.exists()
    assert not final.with_name(".KodepoiaSetup.exe.partial").exists()


def test_r18_8_truncated_download_fails_and_partial_is_removed(tmp_path: Path) -> None:
    candidate = _candidate(b"verified-installer")
    transport = MemoryStreamingTargetTransport({candidate.target.path: b"short"})
    with pytest.raises(UpdateVerificationFailed, match="length mismatch"):
        _downloader(tmp_path).stage(candidate, transport)
    partial = tmp_path / "cache" / "beta" / "1.1.0-rc2" / SOURCE_SHA / ".KodepoiaSetup.exe.partial"
    assert not partial.exists()


def test_r18_8_oversize_target_fails_closed(tmp_path: Path) -> None:
    data = b"x" * 20
    candidate = _candidate(data)
    with pytest.raises(UpdateVerificationFailed, match="configured bound"):
        _downloader(tmp_path, max_bytes=10).stage(
            candidate,
            MemoryStreamingTargetTransport({candidate.target.path: data}),
        )


def test_r18_8_cancelled_download_leaves_no_executable_partial(tmp_path: Path) -> None:
    data = b"verified-installer"
    candidate = _candidate(data)
    calls = {"count": 0}

    def cancel() -> bool:
        calls["count"] += 1
        return calls["count"] >= 2

    with pytest.raises(UpdateDownloadCancelled):
        _downloader(tmp_path).stage(
            candidate,
            MemoryStreamingTargetTransport({candidate.target.path: data}),
            cancel_check=cancel,
        )
    partial = tmp_path / "cache" / "beta" / "1.1.0-rc2" / SOURCE_SHA / ".KodepoiaSetup.exe.partial"
    assert not partial.exists()


def test_r18_8_bad_authenticode_never_finalizes(tmp_path: Path) -> None:
    data = b"verified-installer"
    candidate = _candidate(data)
    with pytest.raises(UpdateVerificationFailed, match="Authenticode"):
        _downloader(tmp_path, auth=False).stage(
            candidate,
            MemoryStreamingTargetTransport({candidate.target.path: data}),
        )


def test_r18_8_identity_mismatch_never_finalizes(tmp_path: Path) -> None:
    data = b"verified-installer"
    candidate = _candidate(data)
    with pytest.raises(UpdateVerificationFailed, match="identity"):
        _downloader(tmp_path, identity=False).stage(
            candidate,
            MemoryStreamingTargetTransport({candidate.target.path: data}),
        )


def test_r18_8_withdrawn_or_untrusted_candidate_cannot_download(tmp_path: Path) -> None:
    data = b"verified-installer"
    withdrawn = replace(_candidate(data), withdrawn=True)
    transport = MemoryStreamingTargetTransport({withdrawn.target.path: data})
    with pytest.raises(UpdateVerificationFailed, match="withdrawn"):
        _downloader(tmp_path).stage(withdrawn, transport)

    untrusted = replace(_candidate(data), source_verification_state="metadata-only-untrusted")
    with pytest.raises(UpdateVerificationFailed, match="TUF"):
        _downloader(tmp_path).stage(untrusted, transport)


def test_r18_8_explicit_consent_and_tamper_recheck_gate_launch(tmp_path: Path) -> None:
    data = b"verified-installer"
    candidate = _candidate(data)
    transport = MemoryStreamingTargetTransport({candidate.target.path: data})
    launcher = _Launcher()
    coordinator = UpdateInstallCoordinator(
        tmp_path / "state",
        downloader=_downloader(tmp_path),
        transport=transport,
        launcher=launcher,
        current_public_version="1.1.0-rc1",
        previous_installer=tmp_path / "previous" / "KodepoiaSetup.exe",
    )
    artifact = coordinator.stage(candidate)

    with pytest.raises(UpdateConsentRequired):
        coordinator.launch_staged(artifact, confirmed=False)
    assert launcher.paths == []

    coordinator.launch_staged(artifact, confirmed=True)
    assert launcher.paths == [artifact.path]
    coordinator.record_outcome(success=False, detail="synthetic installer failure")
    recovery = coordinator.recovery_instructions()
    assert recovery["available"] is True
    assert recovery["previous_public_version"] == "1.1.0-rc1"
    assert recovery["status"] == "failed"

    artifact.path.write_bytes(b"tampered")
    with pytest.raises(UpdateVerificationFailed, match="changed before launch"):
        coordinator.launch_staged(artifact, confirmed=True)
    assert launcher.paths == [artifact.path]


def test_r18_8_failed_stage_does_not_modify_project_data(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    project_file = project / "vision.json"
    project_file.write_text('{"keep": true}\n', encoding="utf-8")
    before = project_file.read_bytes()

    candidate = replace(_candidate(), sha256="0" * 64)
    with pytest.raises(UpdateVerificationFailed):
        _downloader(tmp_path).stage(
            candidate,
            MemoryStreamingTargetTransport({candidate.target.path: b"verified-installer"}),
        )
    assert project_file.read_bytes() == before
