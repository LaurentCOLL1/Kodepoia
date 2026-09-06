from __future__ import annotations

from typing import Protocol

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.update.discovery import UpdateDiscoveryResult

MIN_PERIODIC_CHECK_HOURS = 6
MAX_PERIODIC_CHECK_HOURS = 168
DEFAULT_PERIODIC_CHECK_HOURS = 24
DEFAULT_UPDATE_CHANNEL = "stable"


class UpdateDiscoveryProvider(Protocol):
    def check(self, channel: str) -> UpdateDiscoveryResult: ...


def _texts(locale: str) -> dict[str, str]:
    if locale == "fr":
        return {
            "title": "Mises à jour",
            "installed": "Version installée",
            "channel": "Canal de mise à jour",
            "stable": "Stable",
            "beta": "Bêta",
            "beta_warning": "Le canal bêta peut proposer des versions de prépublication moins stables.",
            "periodic": "Vérifier périodiquement les mises à jour",
            "interval": "Intervalle (heures)",
            "check": "Rechercher des mises à jour",
            "never_startup": "La vérification n'est jamais une dépendance du démarrage et aucun installateur n'est lancé automatiquement.",
            "checking": "Vérification des métadonnées de mise à jour…",
            "up-to-date": "À jour",
            "update-available": "Mise à jour disponible",
            "offline": "Hors ligne",
            "metadata-expired": "Métadonnées expirées",
            "verification-failed": "Échec de vérification",
            "channel-unavailable": "Canal indisponible",
            "update-withdrawn": "Mise à jour retirée",
            "candidate": "Candidate",
            "verified": "Vérification source",
            "size": "Taille annoncée",
            "notes": "Notes",
            "signing": "Signature",
            "provenance": "Provenance",
        }
    return {
        "title": "Updates",
        "installed": "Installed version",
        "channel": "Update channel",
        "stable": "Stable",
        "beta": "Beta",
        "beta_warning": "The beta channel can offer less stable prerelease builds.",
        "periodic": "Check periodically for updates",
        "interval": "Interval (hours)",
        "check": "Check for updates",
        "never_startup": "Update checks never gate startup and no installer is launched automatically.",
        "checking": "Checking trusted update metadata…",
        "up-to-date": "Up to date",
        "update-available": "Update available",
        "offline": "Offline",
        "metadata-expired": "Metadata expired",
        "verification-failed": "Verification failed",
        "channel-unavailable": "Channel unavailable",
        "update-withdrawn": "Update withdrawn",
        "candidate": "Candidate",
        "verified": "Source verification",
        "size": "Declared size",
        "notes": "Notes",
        "signing": "Signing",
        "provenance": "Provenance",
    }


def create_update_settings_group(
    *,
    locale: str = "en",
    service: UpdateDiscoveryProvider | None = None,
    settings=None,
):
    from PySide6.QtCore import QSettings, QTimer
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFormLayout,
        QGroupBox,
        QLabel,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
    )

    tr = _texts(locale)
    store = settings or QSettings("Kodepoia", "KodeStudio")
    group = QGroupBox(tr["title"])
    group.setObjectName("updateSettingsGroup")
    layout = QVBoxLayout(group)
    form = QFormLayout()

    installed = QLabel(f"{CURRENT_RELEASE.public_version} ({CURRENT_RELEASE.channel})")
    installed.setObjectName("updateInstalledVersion")
    form.addRow(tr["installed"], installed)

    channel = QComboBox()
    channel.setObjectName("updateChannelSelector")
    channel.addItem(tr["stable"], "stable")
    channel.addItem(tr["beta"], "beta")
    saved_channel = str(store.value("updates/channel", DEFAULT_UPDATE_CHANNEL)).lower()
    channel_index = channel.findData(saved_channel)
    channel.setCurrentIndex(channel_index if channel_index >= 0 else 0)
    form.addRow(tr["channel"], channel)

    beta_warning = QLabel(tr["beta_warning"])
    beta_warning.setObjectName("updatePrereleaseWarning")
    beta_warning.setWordWrap(True)
    beta_warning.setVisible(channel.currentData() == "beta")
    form.addRow(beta_warning)

    periodic = QCheckBox(tr["periodic"])
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
    form.addRow(tr["interval"], interval)
    layout.addLayout(form)

    note = QLabel(tr["never_startup"])
    note.setObjectName("updateStartupPolicy")
    note.setWordWrap(True)
    layout.addWidget(note)

    check_button = QPushButton(tr["check"])
    check_button.setObjectName("checkForUpdatesButton")
    layout.addWidget(check_button)

    state = QLabel(tr["channel-unavailable"] if service is None else "")
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

    def render(result: UpdateDiscoveryResult) -> None:
        state_text = tr.get(result.status, result.status)
        state.setText(f"{state_text}: {result.detail}")
        candidate = result.candidate
        if candidate is None:
            details.setText("")
            return
        mib = candidate.size_bytes / (1024 * 1024)
        details.setText(
            "\n".join(
                (
                    f"{tr['candidate']}: {candidate.target.public_version} ({candidate.target.channel})",
                    f"{tr['verified']}: {candidate.source_verification_state}",
                    f"{tr['size']}: {candidate.size_bytes} bytes ({mib:.2f} MiB)",
                    f"{tr['notes']}: {candidate.release_notes_summary}",
                    f"{tr['signing']}: {candidate.signing_status}",
                    f"{tr['provenance']}: {candidate.provenance_status}",
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
        state.setText(tr["checking"])
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

    def channel_changed() -> None:
        beta_warning.setVisible(channel.currentData() == "beta")
        persist()

    channel.currentIndexChanged.connect(lambda *_: channel_changed())
    periodic.toggled.connect(lambda *_: (persist(), configure_timer()))
    interval.valueChanged.connect(lambda *_: (persist(), configure_timer()))
    check_button.clicked.connect(run_check)
    timer.timeout.connect(run_check)
    configure_timer()

    group._kodepoia_update_settings = store
    group._kodepoia_update_service = service
    group._kodepoia_update_timer = timer
    group._kodepoia_run_update_check = run_check
    return group
