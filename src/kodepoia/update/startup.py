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
    VerifiedUpdateDownloader,
)
from kodepoia.update.discovery import UpdateDiscoveryResult, UpdateDiscoveryService
from kodepoia.update.network import NetworkTransportPolicy, NetworkUpdateTransport
from kodepoia.update.seamless import SeamlessUpdateInstallCoordinator, WindowsInnoUpdateLauncher


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
    installer: SeamlessUpdateInstallCoordinator | None
    transport: NetworkUpdateTransport | None
    startup_error: str | None = None


def default_update_state_dir() -> Path:
    return Path.home() / ".kodepoia" / "updates"


def _seed_packaged_discovery_root(base_state: Path, root_bytes: bytes) -> None:
    """Seed the embedded Root before the first network refresh.

    The discovery verifier already supports a sequential Root transition once a
    trusted Root exists in its state directory. Fresh installs must therefore
    start from the exact embedded Root rather than attempting to pin the newest
    network Root directly after a server-side Root rotation.
    """

    discovery_state = base_state / "discovery" / "tuf-discovery"
    state_path = discovery_state / "state.json"
    if state_path.is_file():
        return

    discovery_state.mkdir(parents=True, exist_ok=True)
    root_path = discovery_state / "root.json"
    temp_path = discovery_state / ".root.json.bootstrap.tmp"
    temp_path.write_bytes(root_bytes)
    temp_path.replace(root_path)


def build_packaged_update_services(
    *,
    state_dir: str | Path | None = None,
    platform_name: str | None = None,
    transport_factory: Callable[[NetworkTransportPolicy], NetworkUpdateTransport] = NetworkUpdateTransport,
) -> PackagedUpdateServices:
    """Build trusted update services without performing any network request."""

    root = load_production_packaged_root()
    base_state = Path(state_dir) if state_dir is not None else default_update_state_dir()
    _seed_packaged_discovery_root(base_state, root.root_bytes)
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
    installer: SeamlessUpdateInstallCoordinator | None = None
    if runtime_platform == "win32":
        downloader = VerifiedUpdateDownloader(
            base_state / "downloads",
            authenticode=PowerShellAuthenticodeVerifier(),
            identity=PowerShellInstallerIdentityVerifier(),
        )
        installer = SeamlessUpdateInstallCoordinator(
            base_state / "install",
            downloader=downloader,
            transport=transport,
            launcher=WindowsInnoUpdateLauncher(platform_name=runtime_platform),
            current_public_version=CURRENT_RELEASE.public_version,
        )
        installer.reconcile_startup(CURRENT_RELEASE.public_version)

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
