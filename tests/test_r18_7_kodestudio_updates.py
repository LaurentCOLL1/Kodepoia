from __future__ import annotations

import os

import pytest

from kodepoia.kodestudio.update_settings import (
    DEFAULT_PERIODIC_CHECK_HOURS,
    create_update_settings_group,
)
from kodepoia.update.discovery import UpdateDiscoveryCandidate, UpdateDiscoveryResult
from kodepoia.update.trust import UpdateTargetSpec

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtCore = pytest.importorskip("PySide6.QtCore")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QSettings = QtCore.QSettings
QApplication = QtWidgets.QApplication
QCheckBox = QtWidgets.QCheckBox
QComboBox = QtWidgets.QComboBox
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton
QSpinBox = QtWidgets.QSpinBox


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def _candidate() -> UpdateDiscoveryCandidate:
    return UpdateDiscoveryCandidate(
        target=UpdateTargetSpec(
            channel="beta",
            platform="windows-x86_64",
            public_version="1.1.0-rc2",
            source_sha="c" * 40,
        ),
        size_bytes=42 * 1024 * 1024,
        sha256="d" * 64,
        release_notes_summary="Synthetic R18.7 acceptance release.",
        signing_status="reported-by-tuf-metadata:staged-evidence-available",
        provenance_status="reported-by-tuf-metadata:attestation-available",
    )


class FakeDiscoveryService:
    def __init__(self, result: UpdateDiscoveryResult | None = None) -> None:
        self.channels: list[str] = []
        self.result = result or UpdateDiscoveryResult(
            status="update-available",
            candidate=_candidate(),
            detail="trusted metadata authorizes a newer update",
        )

    def check(self, channel: str) -> UpdateDiscoveryResult:
        self.channels.append(channel)
        return self.result


class FailingDiscoveryService:
    def check(self, channel: str) -> UpdateDiscoveryResult:
        raise RuntimeError(f"synthetic failure on {channel}")


def _settings(tmp_path, name: str = "updates.ini") -> QSettings:
    return QSettings(str(tmp_path / name), QSettings.Format.IniFormat)


def test_defaults_are_stable_periodic_and_do_not_check_on_startup(app, tmp_path) -> None:
    service = FakeDiscoveryService()
    settings = _settings(tmp_path)

    group = create_update_settings_group(service=service, settings=settings)

    channel = group.findChild(QComboBox, "updateChannelSelector")
    periodic = group.findChild(QCheckBox, "updatePeriodicEnabled")
    hours = group.findChild(QSpinBox, "updatePeriodicHours")
    timer = group._kodepoia_update_timer
    assert channel.currentData() == "stable"
    assert channel.count() == 3
    assert channel.findData("beta") >= 0
    assert channel.findData("nightly") >= 0
    assert periodic.isChecked() is True
    assert hours.value() == DEFAULT_PERIODIC_CHECK_HOURS
    assert timer.isActive() is True
    assert timer.interval() == DEFAULT_PERIODIC_CHECK_HOURS * 60 * 60 * 1000
    assert service.channels == []


def test_beta_selection_warns_and_persists(app, tmp_path) -> None:
    settings = _settings(tmp_path)
    group = create_update_settings_group(service=FakeDiscoveryService(), settings=settings)
    channel = group.findChild(QComboBox, "updateChannelSelector")
    warning = group.findChild(QLabel, "updatePrereleaseWarning")

    channel.setCurrentIndex(channel.findData("beta"))
    app.processEvents()

    assert warning.isHidden() is False
    assert "beta" in warning.text().lower()
    assert settings.value("updates/channel") == "beta"

    restored = create_update_settings_group(service=FakeDiscoveryService(), settings=_settings(tmp_path))
    restored_channel = restored.findChild(QComboBox, "updateChannelSelector")
    assert restored_channel.currentData() == "beta"


def test_nightly_selection_has_stronger_warning_and_persists(app, tmp_path) -> None:
    settings = _settings(tmp_path)
    group = create_update_settings_group(service=FakeDiscoveryService(), settings=settings)
    channel = group.findChild(QComboBox, "updateChannelSelector")
    warning = group.findChild(QLabel, "updatePrereleaseWarning")

    channel.setCurrentIndex(channel.findData("nightly"))
    app.processEvents()

    assert warning.isHidden() is False
    assert "nightly" in warning.text().lower()
    assert "experimental" in warning.text().lower()
    assert settings.value("updates/channel") == "nightly"


def test_manual_check_renders_trusted_candidate_without_install_action(app, tmp_path) -> None:
    service = FakeDiscoveryService()
    group = create_update_settings_group(service=service, settings=_settings(tmp_path))
    channel = group.findChild(QComboBox, "updateChannelSelector")
    channel.setCurrentIndex(channel.findData("beta"))
    button = group.findChild(QPushButton, "checkForUpdatesButton")

    button.click()
    app.processEvents()

    state = group.findChild(QLabel, "updateDiscoveryState")
    details = group.findChild(QLabel, "updateDiscoveryDetails")
    assert service.channels == ["beta"]
    assert "Update available" in state.text()
    assert "1.1.0-rc2" in details.text()
    assert "tuf-verified-metadata" in details.text()
    assert "not verified here" in details.text()
    assert "reported-by-tuf-metadata:staged-evidence-available" in details.text()
    assert "reported-by-tuf-metadata:attestation-available" in details.text()
    assert group.findChild(QPushButton, "installUpdateButton") is None


@pytest.mark.parametrize(
    ("status", "expected", "has_candidate"),
    (
        ("up-to-date", "Up to date", True),
        ("update-available", "Update available", True),
        ("offline", "Offline", False),
        ("metadata-expired", "Metadata expired", False),
        ("verification-failed", "Verification failed", False),
        ("channel-unavailable", "Channel unavailable", False),
        ("update-withdrawn", "Update withdrawn", True),
    ),
)
def test_every_major_discovery_state_has_explicit_qt_rendering(
    app,
    tmp_path,
    status: str,
    expected: str,
    has_candidate: bool,
) -> None:
    result = UpdateDiscoveryResult(
        status=status,
        candidate=_candidate() if has_candidate else None,
        detail=f"synthetic {status} detail",
    )
    service = FakeDiscoveryService(result)
    group = create_update_settings_group(
        service=service,
        settings=_settings(tmp_path, f"{status}.ini"),
    )
    button = group.findChild(QPushButton, "checkForUpdatesButton")

    button.click()
    app.processEvents()

    state = group.findChild(QLabel, "updateDiscoveryState")
    details = group.findChild(QLabel, "updateDiscoveryDetails")
    assert expected in state.text()
    assert f"synthetic {status} detail" in state.text()
    assert bool(details.text()) is has_candidate


def test_periodic_opt_out_stops_timer_and_persists(app, tmp_path) -> None:
    settings = _settings(tmp_path)
    group = create_update_settings_group(service=FakeDiscoveryService(), settings=settings)
    periodic = group.findChild(QCheckBox, "updatePeriodicEnabled")

    periodic.setChecked(False)
    app.processEvents()

    assert group._kodepoia_update_timer.isActive() is False
    assert str(settings.value("updates/periodic_enabled")).lower() in {"false", "0"}


def test_ui_boundary_turns_service_exception_into_verification_failure(app, tmp_path) -> None:
    group = create_update_settings_group(
        service=FailingDiscoveryService(),
        settings=_settings(tmp_path),
    )
    button = group.findChild(QPushButton, "checkForUpdatesButton")

    button.click()
    app.processEvents()

    state = group.findChild(QLabel, "updateDiscoveryState")
    assert "Verification failed" in state.text()
    assert "synthetic failure" in state.text()
