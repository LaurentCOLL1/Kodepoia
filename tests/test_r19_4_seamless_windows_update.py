from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.update.delivery import (
    UpdateConsentRequired,
    UpdateDeliveryError,
    UpdateVerificationFailed,
    VerifiedUpdateArtifact,
)
from kodepoia.update.network import NetworkUpdateTransport
from kodepoia.update.seamless import (
    INNO_UPDATE_ARGUMENTS,
    SeamlessUpdateInstallCoordinator,
)
from kodepoia.update.startup import build_packaged_update_services

ROOT = Path(__file__).resolve().parents[1]


class FakeLauncher:
    def __init__(self, *, failure: Exception | None = None) -> None:
        self.failure = failure
        self.paths: list[Path] = []

    def launch(self, path: Path) -> None:
        self.paths.append(path)
        if self.failure is not None:
            raise self.failure


class UnusedDownloader:
    def stage(self, candidate, transport):
        del candidate, transport
        raise AssertionError("download must not be used in this test")


class UnusedTransport:
    def iter_target(self, path: str, *, chunk_size: int):
        del path, chunk_size
        raise AssertionError("transport must not be used in this test")


class EmptyPool:
    def __init__(self) -> None:
        self.requests: list[str] = []

    def request(self, method: str, url: str, **kwargs):
        del method, kwargs
        self.requests.append(url)
        raise AssertionError("packaged service construction must remain network-free")


def artifact(tmp_path: Path, *, version: str = "1.1.0-rc2") -> VerifiedUpdateArtifact:
    path = tmp_path / "KodepoiaSetup.exe"
    payload = b"verified-installer-fixture"
    path.write_bytes(payload)
    return VerifiedUpdateArtifact(
        path=path,
        public_version=version,
        source_sha="a" * 40,
        channel="beta",
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        authenticode_status="valid",
        identity_status=f"ProductVersion={version!r}",
    )


def coordinator(tmp_path: Path, launcher: FakeLauncher) -> SeamlessUpdateInstallCoordinator:
    return SeamlessUpdateInstallCoordinator(
        tmp_path / "state",
        downloader=UnusedDownloader(),
        transport=UnusedTransport(),
        launcher=launcher,
        current_public_version="1.1.0-rc1",
    )


def state_payload(tmp_path: Path) -> dict[str, object]:
    return json.loads((tmp_path / "state" / "install-handoff.json").read_text(encoding="utf-8"))


def test_inno_update_arguments_are_fixed_and_noninteractive() -> None:
    assert INNO_UPDATE_ARGUMENTS == (
        "/SP-",
        "/SILENT",
        "/NORESTART",
        "/CLOSEAPPLICATIONS",
        "/NORESTARTAPPLICATIONS",
        "/KODEPOIAUPDATE=1",
    )
    assert all("http" not in item.lower() for item in INNO_UPDATE_ARGUMENTS)


def test_explicit_confirmation_remains_mandatory(tmp_path: Path) -> None:
    launcher = FakeLauncher()
    service = coordinator(tmp_path, launcher)
    with pytest.raises(UpdateConsentRequired, match="explicit user confirmation"):
        service.launch_staged(artifact(tmp_path), confirmed=False)
    assert launcher.paths == []


def test_staged_payload_is_rechecked_immediately_before_handoff(tmp_path: Path) -> None:
    launcher = FakeLauncher()
    service = coordinator(tmp_path, launcher)
    staged = artifact(tmp_path)
    staged.path.write_bytes(b"tampered")
    with pytest.raises(UpdateVerificationFailed, match="changed before launch"):
        service.launch_staged(staged, confirmed=True)
    assert launcher.paths == []


def test_successful_handoff_is_reconciled_on_new_version_startup(tmp_path: Path) -> None:
    launcher = FakeLauncher()
    service = coordinator(tmp_path, launcher)
    staged = artifact(tmp_path)
    service.launch_staged(staged, confirmed=True)
    assert launcher.paths == [staged.path]
    assert state_payload(tmp_path)["status"] == "launching"

    assert service.reconcile_startup("1.1.0-rc2") == "succeeded"
    payload = state_payload(tmp_path)
    assert payload["status"] == "succeeded"
    assert "reconciled after relaunch" in str(payload["outcome_detail"])


def test_old_version_restart_becomes_recoverable_not_false_success(tmp_path: Path) -> None:
    launcher = FakeLauncher()
    service = coordinator(tmp_path, launcher)
    service.launch_staged(artifact(tmp_path), confirmed=True)

    assert service.reconcile_startup("1.1.0-rc1") == "recovery-needed"
    payload = state_payload(tmp_path)
    assert payload["status"] == "recovery-needed"
    assert payload["user_consent_observed"] is True


def test_launcher_failure_is_persisted_and_application_can_remain_running(tmp_path: Path) -> None:
    launcher = FakeLauncher(failure=UpdateDeliveryError("UAC cancelled"))
    service = coordinator(tmp_path, launcher)
    with pytest.raises(UpdateDeliveryError, match="UAC cancelled"):
        service.launch_staged(artifact(tmp_path), confirmed=True)
    payload = state_payload(tmp_path)
    assert payload["status"] == "failed"
    assert "UAC cancelled" in str(payload["outcome_detail"])


def test_packaged_windows_construction_remains_network_free(tmp_path: Path) -> None:
    pool = EmptyPool()
    services = build_packaged_update_services(
        state_dir=tmp_path,
        platform_name="win32",
        transport_factory=lambda policy: NetworkUpdateTransport(policy, pool=pool),
    )
    assert pool.requests == []
    assert isinstance(services.installer, SeamlessUpdateInstallCoordinator)


def test_inno_script_relaunches_only_for_governed_update_marker() -> None:
    text = (ROOT / "packaging" / "windows" / "Kodepoia.iss").read_text(encoding="utf-8")
    assert "RestartApplications=no" in text
    assert "{param:KODEPOIAUPDATE|0}" in text
    assert "Check: IsKodepoiaUpdate" in text
    assert "runasoriginaluser" in text
    assert "skipifsilent" in text
