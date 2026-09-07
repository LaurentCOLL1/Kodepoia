from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.update.bootstrap import load_production_packaged_root
from kodepoia.update.delivery import (
    AuthenticodeEvidence,
    PowerShellInstallerIdentityVerifier,
    UpdateInstallCoordinator,
    VerifiedUpdateDownloader,
    WindowsInstallerLauncher,
)
from kodepoia.update.discovery import UpdateDiscoveryResult, UpdateDiscoveryService
from kodepoia.update.network import NetworkTransportPolicy, NetworkUpdateTransport


class PowerShellAuthenticodeVerifier:
    """Verify Authenticode through packaged Windows PowerShell without SignTool SDK."""

    _SCRIPT = (
        "$ErrorActionPreference='Stop';"
        "$s=Get-AuthenticodeSignature -LiteralPath $args[0];"
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
        result = self.runner(
            [
                self.powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                self._SCRIPT,
                str(path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        output = (result.stdout or "").strip()
        status, _, detail = output.partition("|")
        verified = result.returncode == 0 and status.strip().lower() == "valid"
        if not detail:
            detail = (result.stderr or output or f"PowerShell exit code {result.returncode}").strip()
        return AuthenticodeEvidence(
            verified=verified,
            status=status.strip().lower() or "invalid",
            detail=detail,
        )


class UnavailableUpdateDiscoveryService:
    """Fail-closed local startup state that preserves normal KodeStudio launch."""

    def __init__(self, detail: str) -> None:
        self.detail = detail

    def check(self, channel: str) -> UpdateDiscoveryResult:
        return UpdateDiscoveryResult(
            status="verification-failed",
            candidate=None,
            detail=self.detail,
        )


@dataclass(frozen=True, slots=True)
class PackagedUpdateServices:
    discovery: object
    installer: UpdateInstallCoordinator | None
    transport: NetworkUpdateTransport | None
    startup_error: str | None = None


def default_update_state_dir() -> Path:
    return Path.home() / ".kodepoia" / "updates"


def build_packaged_update_services(
    *,
    state_dir: str | Path | None = None,
    platform_name: str | None = None,
    transport_factory: Callable[[NetworkTransportPolicy], NetworkUpdateTransport] = NetworkUpdateTransport,
) -> PackagedUpdateServices:
    """Build trusted update services without performing any network request."""

    root = load_production_packaged_root()
    base_state = Path(state_dir) if state_dir is not None else default_update_state_dir()
    policy = NetworkTransportPolicy()
    transport = transport_factory(policy)
    discovery = UpdateDiscoveryService(
        base_state / "discovery",
        root_pin=root.pin,
        transport=transport,
        platform="windows-x86_64",
        installed_release=CURRENT_RELEASE,
    )

    runtime_platform = platform_name or sys.platform
    installer: UpdateInstallCoordinator | None = None
    if runtime_platform == "win32":
        downloader = VerifiedUpdateDownloader(
            base_state / "downloads",
            authenticode=PowerShellAuthenticodeVerifier(),
            identity=PowerShellInstallerIdentityVerifier(),
        )
        installer = UpdateInstallCoordinator(
            base_state / "install",
            downloader=downloader,
            transport=transport,
            launcher=WindowsInstallerLauncher(),
            current_public_version=CURRENT_RELEASE.public_version,
        )

    return PackagedUpdateServices(
        discovery=discovery,
        installer=installer,
        transport=transport,
    )


def build_packaged_update_services_resilient(
    *,
    state_dir: str | Path | None = None,
    platform_name: str | None = None,
    transport_factory: Callable[[NetworkTransportPolicy], NetworkUpdateTransport] = NetworkUpdateTransport,
) -> PackagedUpdateServices:
    """Keep application startup available if local trust configuration is damaged."""

    try:
        return build_packaged_update_services(
            state_dir=state_dir,
            platform_name=platform_name,
            transport_factory=transport_factory,
        )
    except Exception as exc:
        detail = f"trusted update service startup failed: {exc}"
        return PackagedUpdateServices(
            discovery=UnavailableUpdateDiscoveryService(detail),
            installer=None,
            transport=None,
            startup_error=detail,
        )
