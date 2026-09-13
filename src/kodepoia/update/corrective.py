from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from tuf.api.metadata import Targets

from kodepoia.release.tuf_security import TufVerificationError
from kodepoia.update.delivery import (
    AuthenticodeEvidence,
    AuthenticodeVerifier,
    InstallerIdentityEvidence,
    StreamingTargetTransport,
    UpdateVerificationFailed,
    VerifiedUpdateArtifact,
    VerifiedUpdateDownloader,
)
from kodepoia.update.discovery import UpdateDiscoveryCandidate, UpdateDiscoveryService

AUTHENTICODE_POLICY_KEY = "authenticode_policy"
AUTHENTICODE_POLICY_REQUIRE_VALID = "require-valid"
AUTHENTICODE_POLICY_ALLOW_UNSIGNED = "allow-unsigned"
AUTHENTICODE_POLICIES = frozenset(
    {AUTHENTICODE_POLICY_REQUIRE_VALID, AUTHENTICODE_POLICY_ALLOW_UNSIGNED}
)
POWERSHELL_LITERAL_PATH_ENV = "KODEPOIA_UPDATER_LITERAL_PATH"


def parse_authenticode_policy(custom: dict[str, object]) -> str:
    """Return the exact trusted target policy, failing closed on malformed declarations."""

    if AUTHENTICODE_POLICY_KEY not in custom:
        return AUTHENTICODE_POLICY_REQUIRE_VALID
    value = custom[AUTHENTICODE_POLICY_KEY]
    if not isinstance(value, str) or value not in AUTHENTICODE_POLICIES:
        raise TufVerificationError(
            "authorized target has invalid authenticode_policy; expected exactly "
            f"{sorted(AUTHENTICODE_POLICIES)!r}"
        )
    return value


@dataclass(frozen=True, slots=True)
class PolicyUpdateDiscoveryCandidate(UpdateDiscoveryCandidate):
    authenticode_policy: str = AUTHENTICODE_POLICY_REQUIRE_VALID


class PolicyUpdateDiscoveryService(UpdateDiscoveryService):
    """Bind an exact Authenticode policy to the already TUF-verified target candidate."""

    def _candidate(self, targets: Targets, channel: str) -> UpdateDiscoveryCandidate | None:
        candidate = super()._candidate(targets, channel)
        if candidate is None:
            return None
        target_info = targets.targets.get(candidate.target.path)
        if target_info is None:
            raise TufVerificationError("selected update target disappeared from trusted Targets metadata")
        custom = target_info.custom if isinstance(target_info.custom, dict) else {}
        policy = parse_authenticode_policy(custom)
        return PolicyUpdateDiscoveryCandidate(
            target=candidate.target,
            size_bytes=candidate.size_bytes,
            sha256=candidate.sha256,
            source_verification_state=candidate.source_verification_state,
            release_notes_summary=candidate.release_notes_summary,
            signing_status=candidate.signing_status,
            provenance_status=candidate.provenance_status,
            withdrawn=candidate.withdrawn,
            authenticode_policy=policy,
        )


def _powershell_environment(path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env[POWERSHELL_LITERAL_PATH_ENV] = str(path)
    return env


class PowerShellAuthenticodeVerifier:
    """Query Authenticode with fixed code while transporting the path only as process data."""

    _SCRIPT = (
        "$ErrorActionPreference='Stop';"
        f"$p=$env:{POWERSHELL_LITERAL_PATH_ENV};"
        "if([string]::IsNullOrEmpty($p)){exit 8};"
        "$s=Get-AuthenticodeSignature -LiteralPath $p;"
        "[Console]::Out.Write(($s.Status.ToString())+'|'+($s.StatusMessage))"
    )

    def __init__(
        self,
        powershell: str = "powershell.exe",
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        if not powershell.strip():
            raise ValueError("PowerShell executable must be non-empty")
        self.powershell = powershell
        self.runner = runner

    def verify(self, path: Path) -> AuthenticodeEvidence:
        command = [
            self.powershell,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            self._SCRIPT,
        ]
        result = self.runner(
            command,
            text=True,
            capture_output=True,
            check=False,
            env=_powershell_environment(path),
        )
        output = (result.stdout or "").strip()
        status, _, detail = output.partition("|")
        normalized = status.strip().lower()
        verified = result.returncode == 0 and normalized == "valid"
        if not detail:
            detail = (result.stderr or output or f"PowerShell exit code {result.returncode}").strip()
        return AuthenticodeEvidence(
            verified=verified,
            status=normalized or "invalid",
            detail=detail,
        )


class PowerShellInstallerIdentityVerifier:
    """Read ProductVersion through fixed PowerShell and a literal data-only staged path."""

    _SCRIPT = (
        "$ErrorActionPreference='Stop';"
        f"$p=$env:{POWERSHELL_LITERAL_PATH_ENV};"
        "if([string]::IsNullOrEmpty($p)){exit 8};"
        "$v=(Get-Item -LiteralPath $p).VersionInfo.ProductVersion;"
        "if([string]::IsNullOrWhiteSpace($v)){exit 7};"
        "[Console]::Out.Write($v.Trim())"
    )

    def __init__(
        self,
        powershell: str = "powershell.exe",
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        if not powershell.strip():
            raise ValueError("PowerShell executable must be non-empty")
        self.powershell = powershell
        self.runner = runner

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower().replace("+", "-")

    def verify(self, path: Path, *, expected_public_version: str) -> InstallerIdentityEvidence:
        command = [
            self.powershell,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            self._SCRIPT,
        ]
        result = self.runner(
            command,
            text=True,
            capture_output=True,
            check=False,
            env=_powershell_environment(path),
        )
        actual = (result.stdout or "").strip()
        verified = result.returncode == 0 and self._normalize(actual) == self._normalize(
            expected_public_version
        )
        detail = (
            f"ProductVersion={actual!r}"
            if result.returncode == 0
            else (result.stderr or f"PowerShell exit code {result.returncode}").strip()
        )
        return InstallerIdentityEvidence(verified=verified, public_version=actual, detail=detail)


class _PolicyAuthenticodeVerifier:
    def __init__(self, delegate: AuthenticodeVerifier, policy: str) -> None:
        self.delegate = delegate
        self.policy = policy

    def verify(self, path: Path) -> AuthenticodeEvidence:
        evidence = self.delegate.verify(path)
        status = evidence.status.strip().lower()
        valid = evidence.verified and status == "valid"
        unsigned = not evidence.verified and status == "notsigned"
        accepted = valid or (
            self.policy == AUTHENTICODE_POLICY_ALLOW_UNSIGNED and unsigned
        )
        return replace(evidence, verified=accepted, status=status or "invalid")


class PolicyVerifiedUpdateDownloader(VerifiedUpdateDownloader):
    """Apply target-scoped Authenticode policy without weakening the base TUF payload gates."""

    def stage(
        self,
        candidate: UpdateDiscoveryCandidate,
        transport: StreamingTargetTransport,
        *,
        cancel_check: Callable[[], bool] | None = None,
    ) -> VerifiedUpdateArtifact:
        policy = getattr(candidate, "authenticode_policy", AUTHENTICODE_POLICY_REQUIRE_VALID)
        if policy not in AUTHENTICODE_POLICIES:
            raise UpdateVerificationFailed("trusted target Authenticode policy is invalid")
        scoped = VerifiedUpdateDownloader(
            self.cache_dir,
            authenticode=_PolicyAuthenticodeVerifier(self.authenticode, policy),
            identity=self.identity,
            max_installer_bytes=self.max_installer_bytes,
            chunk_size=self.chunk_size,
        )
        return scoped.stage(candidate, transport, cancel_check=cancel_check)


__all__ = [
    "AUTHENTICODE_POLICIES",
    "AUTHENTICODE_POLICY_ALLOW_UNSIGNED",
    "AUTHENTICODE_POLICY_KEY",
    "AUTHENTICODE_POLICY_REQUIRE_VALID",
    "POWERSHELL_LITERAL_PATH_ENV",
    "PolicyUpdateDiscoveryCandidate",
    "PolicyUpdateDiscoveryService",
    "PolicyVerifiedUpdateDownloader",
    "PowerShellAuthenticodeVerifier",
    "PowerShellInstallerIdentityVerifier",
    "parse_authenticode_policy",
]
