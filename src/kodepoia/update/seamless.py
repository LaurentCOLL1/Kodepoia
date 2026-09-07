from __future__ import annotations

import json
import sys
from pathlib import Path

from kodepoia.update.delivery import (
    UpdateDeliveryError,
    UpdateInstallCoordinator,
    VerifiedUpdateArtifact,
)

INNO_UPDATE_ARGUMENTS = (
    "/SP-",
    "/SILENT",
    "/NORESTART",
    "/CLOSEAPPLICATIONS",
    "/NORESTARTAPPLICATIONS",
    "/KODEPOIAUPDATE=1",
)


class WindowsInnoUpdateLauncher:
    """Launch a verified Inno Setup payload with one fixed self-update contract."""

    def __init__(self, *, platform_name: str | None = None) -> None:
        self.platform_name = platform_name

    def launch(self, path: Path) -> None:
        runtime_platform = self.platform_name or sys.platform
        if runtime_platform != "win32":
            raise UpdateDeliveryError("Windows installer launch is only supported on Windows")
        import ctypes

        parameters = " ".join(INNO_UPDATE_ARGUMENTS)
        result = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None,
            "runas",
            str(path),
            parameters,
            str(path.parent),
            1,
        )
        if int(result) <= 32:
            raise UpdateDeliveryError(f"ShellExecuteW failed with code {int(result)}")


class SeamlessUpdateInstallCoordinator(UpdateInstallCoordinator):
    """R19.4 handoff: fail-recording plus local next-start outcome reconciliation."""

    @staticmethod
    def _normalize_version(value: object) -> str:
        return str(value or "").strip().lower().replace("+", "-")

    def launch_staged(self, artifact: VerifiedUpdateArtifact, *, confirmed: bool) -> None:
        try:
            super().launch_staged(artifact, confirmed=confirmed)
        except Exception as exc:
            if self._state_path.is_file():
                self.record_outcome(success=False, detail=f"installer launch failed: {exc}")
            raise

    def reconcile_startup(self, installed_public_version: str) -> str | None:
        """Resolve an earlier handoff without network access or installer side effects."""

        if not self._state_path.is_file():
            return None
        try:
            payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return "state-unreadable"
        status = str(payload.get("status") or "")
        if status != "launching":
            return status or None
        candidate = self._normalize_version(payload.get("candidate_public_version"))
        installed = self._normalize_version(installed_public_version)
        if candidate and candidate == installed:
            self.record_outcome(
                success=True,
                detail=f"reconciled after relaunch on installed version {installed_public_version}",
            )
            return "succeeded"
        payload["status"] = "recovery-needed"
        payload["outcome_detail"] = (
            "installer handoff has not produced the authorized version on this startup: "
            f"expected {payload.get('candidate_public_version')!r}, got {installed_public_version!r}"
        )
        self._write_state(payload)
        return "recovery-needed"


__all__ = [
    "INNO_UPDATE_ARGUMENTS",
    "SeamlessUpdateInstallCoordinator",
    "WindowsInnoUpdateLauncher",
]
