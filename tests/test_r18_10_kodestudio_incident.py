from __future__ import annotations

import hashlib

import pytest

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
    qt_core = pytest.importorskip(
        "PySide6.QtCore",
        reason="KodeStudio UI coverage requires the optional ui dependency",
    )
    qt_widgets = pytest.importorskip(
        "PySide6.QtWidgets",
        reason="KodeStudio UI coverage requires the optional ui dependency",
    )
    from kodepoia.kodestudio.update_settings import create_update_settings_group

    q_settings = qt_core.QSettings
    q_application = qt_widgets.QApplication
    q_label = qt_widgets.QLabel
    q_push_button = qt_widgets.QPushButton

    app = q_application.instance() or q_application([])
    settings = q_settings(str(tmp_path / "settings.ini"), q_settings.Format.IniFormat)
    settings.setValue("updates/channel", "beta")
    group = create_update_settings_group(
        locale="en",
        service=_SupersededService(),
        settings=settings,
    )
    group._kodepoia_run_update_check()

    state = group.findChild(q_label, "updateDiscoveryState")
    download = group.findChild(q_push_button, "downloadVerifiedUpdateButton")
    assert state is not None
    assert download is not None
    assert state.text().startswith("Update superseded:")
    assert not download.isEnabled()
    group.deleteLater()
    app.processEvents()
