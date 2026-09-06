from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable, Iterable
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import Request, urlopen

from kodepoia.release.signing import signtool_verify_args
from kodepoia.update.discovery import UpdateDiscoveryCandidate

DEFAULT_CHUNK_SIZE = 1024 * 1024
DEFAULT_MAX_INSTALLER_BYTES = 1024 * 1024 * 1024
DELIVERY_SCHEMA_VERSION = 1


class UpdateDeliveryError(RuntimeError):
    """Base R18.8 verified-delivery failure."""


class UpdateDownloadCancelled(UpdateDeliveryError):
    """Raised when the user cancels an in-progress verified download."""


class UpdateVerificationFailed(UpdateDeliveryError):
    """Raised when downloaded bytes fail an authoritative verification step."""


class UpdateConsentRequired(UpdateDeliveryError):
    """Raised when installer execution is attempted without explicit consent."""


@dataclass(frozen=True, slots=True)
class AuthenticodeEvidence:
    verified: bool
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class InstallerIdentityEvidence:
    verified: bool
    public_version: str
    detail: str


@dataclass(frozen=True, slots=True)
class VerifiedUpdateArtifact:
    path: Path
    public_version: str
    source_sha: str
    channel: str
    size_bytes: int
    sha256: str
    authenticode_status: str
    identity_status: str

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["path"] = str(self.path)
        return result


class StreamingTargetTransport(Protocol):
    def iter_target(self, path: str, *, chunk_size: int) -> Iterable[bytes]: ...


class AuthenticodeVerifier(Protocol):
    def verify(self, path: Path) -> AuthenticodeEvidence: ...


class InstallerIdentityVerifier(Protocol):
    def verify(self, path: Path, *, expected_public_version: str) -> InstallerIdentityEvidence: ...


class InstallerLauncher(Protocol):
    def launch(self, path: Path) -> None: ...


@dataclass(slots=True)
class MemoryStreamingTargetTransport:
    targets: dict[str, bytes]

    def iter_target(self, path: str, *, chunk_size: int) -> Iterable[bytes]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        try:
            data = self.targets[path]
        except KeyError as exc:
            raise UpdateDeliveryError(f"target is unavailable: {path}") from exc
        for offset in range(0, len(data), chunk_size):
            yield data[offset : offset + chunk_size]


class HttpsStreamingTargetTransport:
    """Bounded HTTPS-only target transport with same-origin redirect enforcement."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 30.0,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        parsed = urlsplit(base_url.strip())
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("update target base URL must be absolute HTTPS")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("update target base URL cannot contain credentials, query or fragment")
        normalized_path = parsed.path if parsed.path.endswith("/") else f"{parsed.path}/"
        self.base_url = parsed._replace(path=normalized_path).geturl()
        self._origin = (parsed.scheme.lower(), parsed.hostname.lower(), parsed.port or 443)
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self.opener = opener

    @staticmethod
    def _safe_relative_path(path: str) -> str:
        pieces = path.replace("\\", "/").split("/")
        if not pieces or any(not piece or piece in {".", ".."} for piece in pieces):
            raise UpdateDeliveryError("target path is not a safe repository-relative path")
        return "/".join(quote(piece, safe="-._~") for piece in pieces)

    def iter_target(self, path: str, *, chunk_size: int) -> Iterable[bytes]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        url = urljoin(self.base_url, self._safe_relative_path(path))
        request = Request(url, headers={"User-Agent": "Kodepoia-Updater/1"})
        try:
            response = self.opener(request, timeout=self.timeout_seconds)
        except Exception as exc:
            raise UpdateDeliveryError(f"target transport failed: {exc}") from exc
        try:
            final = urlsplit(str(response.geturl()))
            final_origin = (final.scheme.lower(), (final.hostname or "").lower(), final.port or 443)
            if final_origin != self._origin:
                raise UpdateDeliveryError("cross-origin target redirect is forbidden")
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                if not isinstance(chunk, bytes):
                    raise UpdateDeliveryError("target transport returned non-byte data")
                yield chunk
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()


class SigntoolAuthenticodeVerifier:
    """Use the R18.4 structured SignTool verification command; zero exit is required."""

    def __init__(
        self,
        signtool: str,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        if not signtool.strip():
            raise ValueError("signtool path must be non-empty")
        self.signtool = signtool
        self.runner = runner

    def verify(self, path: Path) -> AuthenticodeEvidence:
        command = signtool_verify_args(self.signtool, path)
        result = self.runner(command, text=True, capture_output=True, check=False)
        detail = (result.stdout or result.stderr or "").strip()
        return AuthenticodeEvidence(
            verified=result.returncode == 0,
            status="valid" if result.returncode == 0 else "invalid",
            detail=detail or f"SignTool exit code {result.returncode}",
        )


class PowerShellInstallerIdentityVerifier:
    """Read Windows ProductVersion through fixed PowerShell code, never model-provided shell text."""

    _SCRIPT = (
        "$ErrorActionPreference='Stop';"
        "$v=(Get-Item -LiteralPath $args[0]).VersionInfo.ProductVersion;"
        "if([string]::IsNullOrWhiteSpace($v)){exit 7};"
        "[Console]::Out.Write($v.Trim())"
    )

    def __init__(
        self,
        powershell: str = "powershell.exe",
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
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
            str(path),
        ]
        result = self.runner(command, text=True, capture_output=True, check=False)
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


class VerifiedUpdateDownloader:
    """Download a TUF-authorized installer, verify it, then atomically finalize it."""

    def __init__(
        self,
        cache_dir: str | Path,
        *,
        authenticode: AuthenticodeVerifier,
        identity: InstallerIdentityVerifier,
        max_installer_bytes: int = DEFAULT_MAX_INSTALLER_BYTES,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.authenticode = authenticode
        self.identity = identity
        if max_installer_bytes <= 0:
            raise ValueError("max_installer_bytes must be positive")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.max_installer_bytes = max_installer_bytes
        self.chunk_size = chunk_size

    def _paths(self, candidate: UpdateDiscoveryCandidate) -> tuple[Path, Path, Path]:
        target = candidate.target
        directory = self.cache_dir / target.channel / target.public_version / target.source_sha
        final = directory / target.filename
        partial = directory / f".{target.filename}.partial"
        evidence = directory / "verified-update.json"
        return final, partial, evidence

    @staticmethod
    def _unlink(path: Path) -> None:
        with suppress(FileNotFoundError):
            path.unlink()

    def stage(
        self,
        candidate: UpdateDiscoveryCandidate,
        transport: StreamingTargetTransport,
        *,
        cancel_check: Callable[[], bool] | None = None,
    ) -> VerifiedUpdateArtifact:
        if candidate.source_verification_state != "tuf-verified-metadata":
            raise UpdateVerificationFailed("candidate is not backed by verified TUF metadata")
        if candidate.withdrawn:
            raise UpdateVerificationFailed("withdrawn update cannot be downloaded")
        if candidate.size_bytes <= 0 or candidate.size_bytes > self.max_installer_bytes:
            raise UpdateVerificationFailed("authorized installer size exceeds the configured bound")
        expected_sha = candidate.sha256.strip().lower()
        if len(expected_sha) != 64 or any(c not in "0123456789abcdef" for c in expected_sha):
            raise UpdateVerificationFailed("authorized installer SHA-256 is malformed")

        final, partial, evidence_path = self._paths(candidate)
        final.parent.mkdir(parents=True, exist_ok=True)
        self._unlink(partial)
        digest = hashlib.sha256()
        total = 0
        cancelled = cancel_check or (lambda: False)
        try:
            with partial.open("xb") as handle:
                for chunk in transport.iter_target(candidate.target.path, chunk_size=self.chunk_size):
                    if cancelled():
                        raise UpdateDownloadCancelled("update download cancelled")
                    if not isinstance(chunk, bytes):
                        raise UpdateDeliveryError("target stream yielded non-byte data")
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > candidate.size_bytes or total > self.max_installer_bytes:
                        raise UpdateVerificationFailed("download exceeded authorized installer size")
                    digest.update(chunk)
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())

            if total != candidate.size_bytes:
                raise UpdateVerificationFailed(
                    f"installer length mismatch: expected {candidate.size_bytes}, got {total}"
                )
            actual_sha = digest.hexdigest()
            if actual_sha != expected_sha:
                raise UpdateVerificationFailed("installer SHA-256 does not match TUF authorization")

            auth = self.authenticode.verify(partial)
            if not auth.verified:
                raise UpdateVerificationFailed(f"Authenticode verification failed: {auth.detail}")
            identity = self.identity.verify(
                partial, expected_public_version=candidate.target.public_version
            )
            if not identity.verified:
                raise UpdateVerificationFailed(f"installer identity verification failed: {identity.detail}")

            os.replace(partial, final)
            artifact = VerifiedUpdateArtifact(
                path=final,
                public_version=candidate.target.public_version,
                source_sha=candidate.target.source_sha,
                channel=candidate.target.channel,
                size_bytes=total,
                sha256=actual_sha,
                authenticode_status=auth.status,
                identity_status=identity.detail,
            )
            temp_evidence = evidence_path.with_suffix(".tmp")
            temp_evidence.write_text(
                json.dumps(
                    {
                        "schema_version": DELIVERY_SCHEMA_VERSION,
                        "artifact": artifact.to_dict(),
                        "tuf_target_path": candidate.target.path,
                        "user_consent_required_before_launch": True,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            os.replace(temp_evidence, evidence_path)
            return artifact
        except Exception:
            self._unlink(partial)
            raise


class WindowsInstallerLauncher:
    """Launch only a pre-verified path through ShellExecuteW/runs as with fixed parameters."""

    def launch(self, path: Path) -> None:
        if sys.platform != "win32":
            raise UpdateDeliveryError("Windows installer launch is only supported on Windows")
        import ctypes

        result = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None,
            "runas",
            str(path),
            None,
            str(path.parent),
            1,
        )
        if int(result) <= 32:
            raise UpdateDeliveryError(f"ShellExecuteW failed with code {int(result)}")


class UpdateInstallCoordinator:
    """Bind staging, explicit consent, tamper recheck and recoverable installer handoff."""

    def __init__(
        self,
        state_dir: str | Path,
        *,
        downloader: VerifiedUpdateDownloader,
        transport: StreamingTargetTransport,
        launcher: InstallerLauncher,
        current_public_version: str,
        previous_installer: str | Path | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.downloader = downloader
        self.transport = transport
        self.launcher = launcher
        self.current_public_version = current_public_version
        self.previous_installer = Path(previous_installer) if previous_installer else None
        self._state_path = self.state_dir / "install-handoff.json"

    def _write_state(self, payload: dict[str, object]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temp = self._state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, self._state_path)

    def stage(self, candidate: UpdateDiscoveryCandidate) -> VerifiedUpdateArtifact:
        artifact = self.downloader.stage(candidate, self.transport)
        self._write_state(
            {
                "schema_version": DELIVERY_SCHEMA_VERSION,
                "status": "verified-staged",
                "current_public_version": self.current_public_version,
                "candidate_public_version": artifact.public_version,
                "artifact": artifact.to_dict(),
                "previous_installer": str(self.previous_installer) if self.previous_installer else None,
                "user_consent_observed": False,
            }
        )
        return artifact

    def launch_staged(self, artifact: VerifiedUpdateArtifact, *, confirmed: bool) -> None:
        if not confirmed:
            raise UpdateConsentRequired("explicit user confirmation is required before installer launch")
        if not artifact.path.is_file():
            raise UpdateVerificationFailed("verified staged installer is missing")
        actual_size = artifact.path.stat().st_size
        actual_sha = hashlib.sha256(artifact.path.read_bytes()).hexdigest()
        if actual_size != artifact.size_bytes or actual_sha != artifact.sha256:
            raise UpdateVerificationFailed("verified staged installer changed before launch")
        self._write_state(
            {
                "schema_version": DELIVERY_SCHEMA_VERSION,
                "status": "launching",
                "current_public_version": self.current_public_version,
                "candidate_public_version": artifact.public_version,
                "artifact": artifact.to_dict(),
                "previous_installer": str(self.previous_installer) if self.previous_installer else None,
                "user_consent_observed": True,
            }
        )
        self.launcher.launch(artifact.path)

    def record_outcome(self, *, success: bool, detail: str = "") -> None:
        if not self._state_path.is_file():
            raise UpdateDeliveryError("no install handoff state exists")
        payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        payload["status"] = "succeeded" if success else "failed"
        payload["outcome_detail"] = detail
        self._write_state(payload)

    def recovery_instructions(self) -> dict[str, object]:
        if not self._state_path.is_file():
            return {"available": False, "reason": "no install handoff state"}
        payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        previous = payload.get("previous_installer")
        return {
            "available": bool(previous),
            "previous_public_version": payload.get("current_public_version"),
            "previous_installer": previous,
            "status": payload.get("status"),
        }


__all__ = [
    "AuthenticodeEvidence",
    "AuthenticodeVerifier",
    "HttpsStreamingTargetTransport",
    "InstallerIdentityEvidence",
    "InstallerIdentityVerifier",
    "InstallerLauncher",
    "MemoryStreamingTargetTransport",
    "PowerShellInstallerIdentityVerifier",
    "SigntoolAuthenticodeVerifier",
    "StreamingTargetTransport",
    "UpdateConsentRequired",
    "UpdateDeliveryError",
    "UpdateDownloadCancelled",
    "UpdateInstallCoordinator",
    "UpdateVerificationFailed",
    "VerifiedUpdateArtifact",
    "VerifiedUpdateDownloader",
    "WindowsInstallerLauncher",
]
