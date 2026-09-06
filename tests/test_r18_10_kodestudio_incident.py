from __future__ import annotations

import hashlib

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from kodepoia.kodestudio.update_settings import create_update_settings_group
from kodepoia.release.incident import ReleaseIncidentDirective
from kodepoia.update.discovery import UpdateDiscoveryCandidate, UpdateDiscoveryResult
from kodepoia.update.trust import UpdateTargetSpec

SOURCE_SHA = "1" * 40


class _SupersededService:
    def check(self, channel: str) -> UpdateDiscoveryResult:
        data = b"candidate"
        candidate = UpdateDiscoveryCandidate(
            target=UpdateTargetSpec(
                channel=channel,
                platform="windows-x86_64",
                public_version="1.1.0-rc1",
                source_sha=SOURCE_SHA,
            ),
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )
        base = UpdateDiscoveryResult(
            status="update-available",
            candidate=candidate,
            detail="trusted metadata authorizes a newer update",
        )
        return ReleaseIncidentDirective(
            source_sha=SOURCE_SHA,
            public_version="1.1.0-rc1",
            superseded_by="1.1.0-rc2",
        ).apply(base)


def test_r18_10_kodestudio_renders_superseded_state_fail_closed(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue("updates/channel", "beta")
    group = create_update_settings_group(
        locale="en",
        service=_SupersededService(),
        settings=settings,
    )
    group._kodepoia_run_update_check()

    state = group.findChild(QLabel, "updateDiscoveryState")
    download = group.findChild(QPushButton, "downloadVerifiedUpdateButton")
    assert state is not None
    assert download is not None
    assert state.text().startswith("Update superseded:")
    assert not download.isEnabled()
    group.deleteLater()
    app.processEvents()
