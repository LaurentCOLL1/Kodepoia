from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from kodepoia.kodestudio.update_settings import create_update_settings_group
from kodepoia.update.delivery import VerifiedUpdateArtifact
from kodepoia.update.discovery import UpdateDiscoveryCandidate, UpdateDiscoveryResult
from kodepoia.update.trust import UpdateTargetSpec

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtCore = pytest.importorskip("PySide6.QtCore")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QSettings = QtCore.QSettings
QApplication = QtWidgets.QApplication
QLabel = QtWidgets.QLabel
QMessageBox = QtWidgets.QMessageBox
QPushButton = QtWidgets.QPushButton


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def _candidate() -> UpdateDiscoveryCandidate:
    data = b"synthetic-r18-8-installer"
    return UpdateDiscoveryCandidate(
        target=UpdateTargetSpec(
            channel="beta",
            platform="windows-x86_64",
            public_version="1.1.0-rc2",
            source_sha="e" * 40,
        ),
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )


class _Discovery:
    def __init__(self) -> None:
        self.candidate = _candidate()
        self.calls: list[str] = []

    def check(self, channel: str) -> UpdateDiscoveryResult:
        self.calls.append(channel)
        return UpdateDiscoveryResult(
            status="update-available",
            candidate=self.candidate,
            detail="trusted metadata authorizes a newer update",
        )


class _Install:
    def __init__(self, tmp_path: Path, *, fail_stage: bool = False) -> None:
        self.tmp_path = tmp_path
        self.fail_stage = fail_stage
        self.stage_calls: list[UpdateDiscoveryCandidate] = []
        self.launch_calls: list[tuple[VerifiedUpdateArtifact, bool]] = []

    def stage(self, candidate: UpdateDiscoveryCandidate) -> VerifiedUpdateArtifact:
        self.stage_calls.append(candidate)
        if self.fail_stage:
            raise RuntimeError("synthetic verification failure")
        path = self.tmp_path / "KodepoiaSetup.exe"
        path.write_bytes(b"synthetic-r18-8-installer")
        return VerifiedUpdateArtifact(
            path=path,
            public_version=candidate.target.public_version,
            source_sha=candidate.target.source_sha,
            channel=candidate.target.channel,
            size_bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            authenticode_status="valid",
            identity_status="ProductVersion='1.1.0-rc2'",
        )

    def launch_staged(self, artifact: VerifiedUpdateArtifact, *, confirmed: bool) -> None:
        self.launch_calls.append((artifact, confirmed))


def _settings(tmp_path: Path, name: str) -> QSettings:
    return QSettings(str(tmp_path / name), QSettings.Format.IniFormat)


def test_discovery_never_stages_or_launches_automatically(app, tmp_path) -> None:
    discovery = _Discovery()
    install = _Install(tmp_path)
    group = create_update_settings_group(
        service=discovery,
        install_service=install,
        settings=_settings(tmp_path, "manual.ini"),
    )
    check = group.findChild(QPushButton, "checkForUpdatesButton")
    download = group.findChild(QPushButton, "downloadVerifiedUpdateButton")
    launch = group.findChild(QPushButton, "installVerifiedUpdateButton")

    assert download.isEnabled() is False
    assert launch.isEnabled() is False
    check.click()
    app.processEvents()

    assert discovery.calls == ["stable"]
    assert install.stage_calls == []
    assert install.launch_calls == []
    assert download.isEnabled() is True
    assert launch.isEnabled() is False


def test_stage_enables_install_but_no_launch_until_yes(app, tmp_path, monkeypatch) -> None:
    discovery = _Discovery()
    install = _Install(tmp_path)
    group = create_update_settings_group(
        service=discovery,
        install_service=install,
        settings=_settings(tmp_path, "consent.ini"),
    )
    check = group.findChild(QPushButton, "checkForUpdatesButton")
    download = group.findChild(QPushButton, "downloadVerifiedUpdateButton")
    launch = group.findChild(QPushButton, "installVerifiedUpdateButton")
    state = group.findChild(QLabel, "updateDiscoveryState")

    check.click()
    download.click()
    app.processEvents()
    assert len(install.stage_calls) == 1
    assert install.launch_calls == []
    assert launch.isEnabled() is True
    assert "verified" in state.text().lower()

    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(lambda *args, **kwargs: QMessageBox.StandardButton.No),
    )
    launch.click()
    app.processEvents()
    assert install.launch_calls == []

    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(lambda *args, **kwargs: QMessageBox.StandardButton.Yes),
    )
    launch.click()
    app.processEvents()
    assert len(install.launch_calls) == 1
    artifact, confirmed = install.launch_calls[0]
    assert artifact.public_version == "1.1.0-rc2"
    assert confirmed is True


def test_failed_verified_stage_is_nonfatal_and_cannot_enable_install(app, tmp_path) -> None:
    discovery = _Discovery()
    install = _Install(tmp_path, fail_stage=True)
    group = create_update_settings_group(
        service=discovery,
        install_service=install,
        settings=_settings(tmp_path, "failure.ini"),
    )
    group.findChild(QPushButton, "checkForUpdatesButton").click()
    group.findChild(QPushButton, "downloadVerifiedUpdateButton").click()
    app.processEvents()

    state = group.findChild(QLabel, "updateDiscoveryState")
    launch = group.findChild(QPushButton, "installVerifiedUpdateButton")
    assert "failed" in state.text().lower()
    assert "synthetic verification failure" in state.text()
    assert launch.isEnabled() is False
    assert install.launch_calls == []
