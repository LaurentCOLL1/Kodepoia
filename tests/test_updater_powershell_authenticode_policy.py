from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from tuf.api.metadata import Metadata, Targets

from kodepoia.release.tuf_security import TufVerificationError
from kodepoia.update.corrective import (
    AUTHENTICODE_POLICY_ALLOW_UNSIGNED,
    AUTHENTICODE_POLICY_REQUIRE_VALID,
    POWERSHELL_LITERAL_PATH_ENV,
    PolicyUpdateDiscoveryCandidate,
    PolicyUpdateDiscoveryService,
    PolicyVerifiedUpdateDownloader,
    PowerShellAuthenticodeVerifier,
    PowerShellInstallerIdentityVerifier,
    parse_authenticode_policy,
)
from kodepoia.update.delivery import (
    AuthenticodeEvidence,
    InstallerIdentityEvidence,
    MemoryStreamingTargetTransport,
    UpdateVerificationFailed,
)
from kodepoia.update.trust import PackagedRootPin, UpdateTargetSpec

SOURCE_SHA = "a" * 40
PLATFORM = "windows-x86_64"
PUBLIC_VERSION = "1.1.0-rc7"
DATA = b"policy-bound-installer-fixture"


class _UnusedTransport:
    def fetch_metadata(self, name: str) -> bytes:
        raise AssertionError(f"unexpected metadata fetch: {name}")


class _Auth:
    def __init__(self, status: str, *, verified: bool | None = None) -> None:
        self.status = status
        self.verified = status.lower() == "valid" if verified is None else verified
        self.calls: list[Path] = []

    def verify(self, path: Path) -> AuthenticodeEvidence:
        self.calls.append(path)
        return AuthenticodeEvidence(
            verified=self.verified,
            status=self.status,
            detail=f"synthetic Authenticode status {self.status}",
        )


class _Identity:
    def verify(self, path: Path, *, expected_public_version: str) -> InstallerIdentityEvidence:
        assert path.is_file()
        return InstallerIdentityEvidence(
            verified=True,
            public_version=expected_public_version,
            detail=f"ProductVersion={expected_public_version!r}",
        )


def _target() -> UpdateTargetSpec:
    return UpdateTargetSpec(
        channel="beta",
        platform=PLATFORM,
        public_version=PUBLIC_VERSION,
        source_sha=SOURCE_SHA,
    )


def _candidate(
    *,
    policy: str = AUTHENTICODE_POLICY_REQUIRE_VALID,
    sha256: str | None = None,
) -> PolicyUpdateDiscoveryCandidate:
    return PolicyUpdateDiscoveryCandidate(
        target=_target(),
        size_bytes=len(DATA),
        sha256=sha256 or hashlib.sha256(DATA).hexdigest(),
        authenticode_policy=policy,
    )


def _downloader(tmp_path: Path, auth: _Auth) -> PolicyVerifiedUpdateDownloader:
    return PolicyVerifiedUpdateDownloader(
        tmp_path / "Cache With Spaces",
        authenticode=auth,
        identity=_Identity(),
        chunk_size=4,
        max_installer_bytes=1024,
    )


def _targets_with_custom(custom: dict[str, object]) -> Targets:
    target = _target()
    payload = {
        "signatures": [],
        "signed": {
            "_type": "targets",
            "expires": "2030-01-01T00:00:00Z",
            "spec_version": "1.0.31",
            "targets": {
                target.path: {
                    "custom": custom,
                    "hashes": {"sha256": hashlib.sha256(DATA).hexdigest()},
                    "length": len(DATA),
                }
            },
            "version": 1,
        },
    }
    metadata = Metadata.from_dict(payload)
    assert isinstance(metadata.signed, Targets)
    return metadata.signed


def _discovery_service(tmp_path: Path) -> PolicyUpdateDiscoveryService:
    return PolicyUpdateDiscoveryService(
        tmp_path,
        root_pin=PackagedRootPin(version=1, sha256="0" * 64),
        transport=_UnusedTransport(),
        platform=PLATFORM,
        reference_time=datetime(2026, 9, 13, tzinfo=UTC),
    )


def test_absent_tuf_policy_defaults_to_require_valid_even_if_signing_status_says_unsigned(
    tmp_path: Path,
) -> None:
    targets = _targets_with_custom(
        {"signing_status": "unsigned; production trust is not claimed", "withdrawn": False}
    )
    candidate = _discovery_service(tmp_path)._candidate(targets, "beta")
    assert isinstance(candidate, PolicyUpdateDiscoveryCandidate)
    assert candidate.authenticode_policy == AUTHENTICODE_POLICY_REQUIRE_VALID


def test_explicit_tuf_allow_unsigned_policy_is_bound_to_selected_target(tmp_path: Path) -> None:
    targets = _targets_with_custom({"authenticode_policy": "allow-unsigned", "withdrawn": False})
    candidate = _discovery_service(tmp_path)._candidate(targets, "beta")
    assert isinstance(candidate, PolicyUpdateDiscoveryCandidate)
    assert candidate.authenticode_policy == AUTHENTICODE_POLICY_ALLOW_UNSIGNED


@pytest.mark.parametrize(
    "value",
    ["ALLOW-UNSIGNED", " allow-unsigned", "allow_unsigned", "bogus", True, 1, [], {}],
)
def test_malformed_or_unknown_tuf_policy_fails_closed(value: object) -> None:
    with pytest.raises(TufVerificationError, match="authenticode_policy"):
        parse_authenticode_policy({"authenticode_policy": value})


def test_powershell_authenticode_partial_path_is_process_data_not_command_text() -> None:
    path = Path(r"C:\Kodepoia Cache [qa]&safe\beta\1.1.0-rc7\.KodepoiaSetup.exe.partial")
    observed: dict[str, object] = {}

    def runner(command, **kwargs):
        observed["command"] = command
        observed["env"] = kwargs["env"]
        return subprocess.CompletedProcess(command, 0, stdout="NotSigned|Not digitally signed", stderr="")

    evidence = PowerShellAuthenticodeVerifier(runner=runner).verify(path)
    command = observed["command"]
    assert isinstance(command, list)
    assert str(path) not in command
    assert "-LiteralPath $p" in command[-1]
    env = observed["env"]
    assert isinstance(env, dict)
    assert env[POWERSHELL_LITERAL_PATH_ENV] == str(path)
    assert evidence.status == "notsigned"
    assert evidence.verified is False


def test_powershell_identity_partial_path_is_process_data_not_command_text() -> None:
    path = Path(r"C:\Kodepoia Cache [qa]&safe\beta\1.1.0-rc7\.KodepoiaSetup.exe.partial")
    observed: dict[str, object] = {}

    def runner(command, **kwargs):
        observed["command"] = command
        observed["env"] = kwargs["env"]
        return subprocess.CompletedProcess(command, 0, stdout=PUBLIC_VERSION, stderr="")

    evidence = PowerShellInstallerIdentityVerifier(runner=runner).verify(
        path, expected_public_version=PUBLIC_VERSION
    )
    command = observed["command"]
    assert isinstance(command, list)
    assert str(path) not in command
    assert "Get-Item -LiteralPath $p" in command[-1]
    env = observed["env"]
    assert isinstance(env, dict)
    assert env[POWERSHELL_LITERAL_PATH_ENV] == str(path)
    assert evidence.verified is True


def test_signed_required_plus_valid_passes(tmp_path: Path) -> None:
    auth = _Auth("Valid")
    candidate = _candidate(policy=AUTHENTICODE_POLICY_REQUIRE_VALID)
    artifact = _downloader(tmp_path, auth).stage(
        candidate, MemoryStreamingTargetTransport({candidate.target.path: DATA})
    )
    assert artifact.authenticode_status == "valid"


def test_signed_required_plus_notsigned_fails(tmp_path: Path) -> None:
    auth = _Auth("NotSigned")
    candidate = _candidate(policy=AUTHENTICODE_POLICY_REQUIRE_VALID)
    with pytest.raises(UpdateVerificationFailed, match="Authenticode"):
        _downloader(tmp_path, auth).stage(
            candidate, MemoryStreamingTargetTransport({candidate.target.path: DATA})
        )


def test_allow_unsigned_plus_notsigned_passes_after_tuf_length_and_hash(tmp_path: Path) -> None:
    auth = _Auth("NotSigned")
    candidate = _candidate(policy=AUTHENTICODE_POLICY_ALLOW_UNSIGNED)
    artifact = _downloader(tmp_path, auth).stage(
        candidate, MemoryStreamingTargetTransport({candidate.target.path: DATA})
    )
    assert artifact.authenticode_status == "notsigned"
    assert artifact.sha256 == candidate.sha256
    assert artifact.size_bytes == candidate.size_bytes


@pytest.mark.parametrize(
    "status",
    ["HashMismatch", "NotTrusted", "UnknownError", "NotSupportedFileFormat", "Incompatible"],
)
def test_allow_unsigned_never_accepts_bad_or_untrusted_signature_status(
    tmp_path: Path, status: str
) -> None:
    auth = _Auth(status)
    candidate = _candidate(policy=AUTHENTICODE_POLICY_ALLOW_UNSIGNED)
    with pytest.raises(UpdateVerificationFailed, match="Authenticode"):
        _downloader(tmp_path, auth).stage(
            candidate, MemoryStreamingTargetTransport({candidate.target.path: DATA})
        )


def test_allow_unsigned_does_not_bypass_tuf_sha_and_authenticode_is_not_called(
    tmp_path: Path,
) -> None:
    auth = _Auth("NotSigned")
    candidate = _candidate(
        policy=AUTHENTICODE_POLICY_ALLOW_UNSIGNED,
        sha256="0" * 64,
    )
    with pytest.raises(UpdateVerificationFailed, match="SHA-256"):
        _downloader(tmp_path, auth).stage(
            candidate, MemoryStreamingTargetTransport({candidate.target.path: DATA})
        )
    assert auth.calls == []


def test_unknown_candidate_policy_fails_before_download(tmp_path: Path) -> None:
    auth = _Auth("Valid")
    candidate = _candidate(policy="unknown")
    with pytest.raises(UpdateVerificationFailed, match="policy"):
        _downloader(tmp_path, auth).stage(
            candidate, MemoryStreamingTargetTransport({candidate.target.path: DATA})
        )
    assert auth.calls == []


@pytest.mark.skipif(sys.platform != "win32", reason="native PowerShell acceptance is Windows-only")
def test_native_windows_authenticode_handles_hidden_partial_path_with_spaces(tmp_path: Path) -> None:
    powershell = shutil.which("powershell.exe")
    assert powershell is not None
    directory = tmp_path / "Kodepoia Cache With Spaces"
    directory.mkdir()
    staged = directory / ".KodepoiaSetup.exe.partial"
    shutil.copy2(sys.executable, staged)

    evidence = PowerShellAuthenticodeVerifier(powershell=powershell).verify(staged)
    assert evidence.status in {"valid", "notsigned"}, evidence.detail


@pytest.mark.skipif(sys.platform != "win32", reason="native PowerShell acceptance is Windows-only")
def test_native_windows_identity_handles_hidden_partial_path_with_spaces(tmp_path: Path) -> None:
    powershell = shutil.which("powershell.exe")
    assert powershell is not None
    directory = tmp_path / "Kodepoia Cache With Spaces"
    directory.mkdir()
    staged = directory / ".KodepoiaSetup.exe.partial"
    shutil.copy2(sys.executable, staged)

    evidence = PowerShellInstallerIdentityVerifier(powershell=powershell).verify(
        staged, expected_public_version="definitely-not-the-python-file-version"
    )
    assert evidence.public_version.strip(), evidence.detail
