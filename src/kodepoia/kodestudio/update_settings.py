from __future__ import annotations

from typing import Protocol

from kodepoia.kodestudio.v11_localization import V11Translator
from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.update.delivery import VerifiedUpdateArtifact
from kodepoia.update.discovery import UpdateDiscoveryCandidate, UpdateDiscoveryResult

MIN_PERIODIC_CHECK_HOURS = 6
MAX_PERIODIC_CHECK_HOURS = 168
DEFAULT_PERIODIC_CHECK_HOURS = 24
DEFAULT_UPDATE_CHANNEL = "stable"


class UpdateDiscoveryProvider(Protocol):
    def check(self, channel: str) -> UpdateDiscoveryResult: ...


class UpdateInstallProvider(Protocol):
    def stage(self, candidate: UpdateDiscoveryCandidate) -> VerifiedUpdateArtifact: ...

    def launch_staged(self, artifact: VerifiedUpdateArtifact, *, confirmed: bool) -> None: ...


def create_update_settings_group(
    *,
    locale: str = "en",
    service: UpdateDiscoveryProvider | None = None,
    install_service: UpdateInstallProvider | None = None,
    settings=None,
):
    from PySide6.QtCore import QSettings, QTimer
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFormLayout,
        QGroupBox,
        QLabel,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
    )

    translator = V11Translator(locale)
    tr = translator.text
    store = settings or QSettings("Kodepoia", "KodeStudio")
    group = QGroupBox(tr("updates.title"))
    group.setObjectName("updateSettingsGroup")
    layout = QVBoxLayout(group)
    form = QFormLayout()

    installed = QLabel(f"{CURRENT_RELEASE.public_version} ({CURRENT_RELEASE.channel})")
    installed.setObjectName("updateInstalledVersion")
    form.addRow(tr("updates.installed"), installed)

    channel = QComboBox()
    channel.setObjectName("updateChannelSelector")
    channel.addItem(tr("updates.stable"), "stable")
    channel.addItem(tr("updates.beta"), "beta")
    channel.addItem(tr("updates.nightly"), "nightly")
    saved_channel = str(store.value("updates/channel", DEFAULT_UPDATE_CHANNEL)).lower()
    channel_index = channel.findData(saved_channel)
    channel.setCurrentIndex(channel_index if channel_index >= 0 else 0)
    form.addRow(tr("updates.channel"), channel)

    prerelease_warning = QLabel("")
    prerelease_warning.setObjectName("updatePrereleaseWarning")
    prerelease_warning.setWordWrap(True)
    form.addRow(prerelease_warning)

    periodic = QCheckBox(tr("updates.periodic"))
    periodic.setObjectName("updatePeriodicEnabled")
    enabled_value = store.value("updates/periodic_enabled", True)
    if isinstance(enabled_value, str):
        periodic.setChecked(enabled_value.strip().lower() not in {"0", "false", "no", "off"})
    else:
        periodic.setChecked(bool(enabled_value))
    form.addRow(periodic)

    interval = QSpinBox()
    interval.setObjectName("updatePeriodicHours")
    interval.setRange(MIN_PERIODIC_CHECK_HOURS, MAX_PERIODIC_CHECK_HOURS)
    try:
        saved_hours = int(store.value("updates/periodic_hours", DEFAULT_PERIODIC_CHECK_HOURS))
    except (TypeError, ValueError):
        saved_hours = DEFAULT_PERIODIC_CHECK_HOURS
    interval.setValue(max(MIN_PERIODIC_CHECK_HOURS, min(MAX_PERIODIC_CHECK_HOURS, saved_hours)))
    interval.setEnabled(periodic.isChecked())
    form.addRow(tr("updates.interval"), interval)
    layout.addLayout(form)

    note = QLabel(tr("updates.never_startup"))
    note.setObjectName("updateStartupPolicy")
    note.setWordWrap(True)
    layout.addWidget(note)

    check_button = QPushButton(tr("updates.check"))
    check_button.setObjectName("checkForUpdatesButton")
    layout.addWidget(check_button)

    download_button = QPushButton(tr("updates.download_verify"))
    download_button.setObjectName("downloadVerifiedUpdateButton")
    download_button.setEnabled(False)
    layout.addWidget(download_button)

    install_button = QPushButton(tr("updates.install_verified"))
    install_button.setObjectName("installVerifiedUpdateButton")
    install_button.setEnabled(False)
    layout.addWidget(install_button)

    initial_state = tr("updates.channel-unavailable") if service is None else ""
    state = QLabel(initial_state)
    state.setObjectName("updateDiscoveryState")
    state.setWordWrap(True)
    layout.addWidget(state)

    details = QLabel("")
    details.setObjectName("updateDiscoveryDetails")
    details.setWordWrap(True)
    details.setTextInteractionFlags(details.textInteractionFlags())
    layout.addWidget(details)

    timer = QTimer(group)
    timer.setObjectName("updatePeriodicTimer")
    timer.setSingleShot(False)
    busy = {"value": False}
    current = {"candidate": None}
    staged = {"artifact": None}

    def persist() -> None:
        store.setValue("updates/channel", str(channel.currentData()))
        store.setValue("updates/periodic_enabled", periodic.isChecked())
        store.setValue("updates/periodic_hours", interval.value())
        store.sync()

    def configure_timer() -> None:
        interval.setEnabled(periodic.isChecked())
        timer.stop()
        if periodic.isChecked():
            timer.setInterval(interval.value() * 60 * 60 * 1000)
            timer.start()

    def clear_staged() -> None:
        staged["artifact"] = None
        install_button.setEnabled(False)

    def render(result: UpdateDiscoveryResult) -> None:
        state_key = f"updates.{result.status}"
        state.setText(f"{tr(state_key)}: {result.detail}")
        candidate = result.candidate
        current["candidate"] = candidate
        clear_staged()
        download_button.setEnabled(
            result.status == "update-available"
            and candidate is not None
            and install_service is not None
        )
        if candidate is None:
            details.setText("")
            return
        mib = candidate.size_bytes / (1024 * 1024)
        details.setText(
            "\n".join(
                (
                    f"{tr('updates.candidate')}: "
                    f"{candidate.target.public_version} ({candidate.target.channel})",
                    f"{tr('updates.verified')}: {candidate.source_verification_state}",
                    f"{tr('updates.size')}: {candidate.size_bytes} bytes ({mib:.2f} MiB)",
                    f"{tr('updates.notes')}: {candidate.release_notes_summary}",
                    f"{tr('updates.signing')}: {candidate.signing_status}",
                    f"{tr('updates.provenance')}: {candidate.provenance_status}",
                )
            )
        )

    def run_check() -> None:
        if busy["value"]:
            return
        if service is None:
            render(
                UpdateDiscoveryResult(
                    status="channel-unavailable",
                    candidate=None,
                    detail="no structured update repository is configured",
                )
            )
            return
        busy["value"] = True
        check_button.setEnabled(False)
        state.setText(tr("updates.checking"))
        try:
            result = service.check(str(channel.currentData()))
        except Exception as exc:  # UI boundary: never let update discovery crash KodeStudio.
            result = UpdateDiscoveryResult(
                status="verification-failed", candidate=None, detail=str(exc)
            )
        finally:
            busy["value"] = False
            check_button.setEnabled(True)
        render(result)

    def download_verified() -> None:
        candidate = current["candidate"]
        if candidate is None or install_service is None or busy["value"]:
            return
        busy["value"] = True
        download_button.setEnabled(False)
        clear_staged()
        try:
            artifact = install_service.stage(candidate)
        except Exception as exc:
            state.setText(f"{tr('updates.download_failed')}: {exc}")
        else:
            staged["artifact"] = artifact
            install_button.setEnabled(True)
            state.setText(tr("updates.download_ready"))
        finally:
            busy["value"] = False
            download_button.setEnabled(
                current["candidate"] is not None and install_service is not None
            )

    def install_verified() -> None:
        artifact = staged["artifact"]
        if artifact is None or install_service is None or busy["value"]:
            return
        answer = QMessageBox.question(
            group,
            tr("updates.install_confirm_title"),
            tr("updates.install_confirm", version=artifact.public_version),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        busy["value"] = True
        install_button.setEnabled(False)
        state.setText(tr("updates.install_launching"))
        try:
            install_service.launch_staged(artifact, confirmed=True)
        except Exception as exc:
            state.setText(f"{tr('updates.install_failed')}: {exc}")
            install_button.setEnabled(True)
        finally:
            busy["value"] = False

    def channel_changed() -> None:
        selected = str(channel.currentData())
        if selected == "beta":
            prerelease_warning.setText(tr("updates.beta_warning"))
            prerelease_warning.setVisible(True)
        elif selected == "nightly":
            prerelease_warning.setText(tr("updates.nightly_warning"))
            prerelease_warning.setVisible(True)
        else:
            prerelease_warning.clear()
            prerelease_warning.setVisible(False)
        clear_staged()
        persist()

    channel.currentIndexChanged.connect(lambda *_: channel_changed())
    periodic.toggled.connect(lambda *_: (persist(), configure_timer()))
    interval.valueChanged.connect(lambda *_: (persist(), configure_timer()))
    check_button.clicked.connect(run_check)
    download_button.clicked.connect(download_verified)
    install_button.clicked.connect(install_verified)
    timer.timeout.connect(run_check)
    channel_changed()
    configure_timer()

    group._kodepoia_update_settings = store
    group._kodepoia_update_service = service
    group._kodepoia_install_service = install_service
    group._kodepoia_update_timer = timer
    group._kodepoia_run_update_check = run_check
    group._kodepoia_download_verified = download_verified
    group._kodepoia_install_verified = install_verified
    return group
