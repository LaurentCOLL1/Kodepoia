from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from kodepoia.blender3d.service import BlenderUXResult, BlenderUXState
from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.blender_localization import (
    blender_nav_text,
    registered_blender_messages,
)


class FakeBlenderService:
    def fork(self):
        return self

    def status(self, *, cancellation=None):
        return BlenderUXResult(
            "status",
            BlenderUXState.READY,
            {
                "runtime_evidence": {
                    "blender_version": "5.2.0 LTS",
                    "godot_version": "4.7.2.stable",
                }
            },
        )

    def capabilities(self, *, cancellation=None):
        return BlenderUXResult(
            "capabilities",
            BlenderUXState.READY,
            {
                "capabilities": {
                    "geometry": "accepted",
                    "rig_skin": "accepted",
                    "gltf_glb": "accepted",
                }
            },
        )

    def inspect(self, kind, record_id, *, cancellation=None):
        return BlenderUXResult(
            "inspect",
            BlenderUXState.READY,
            {"kind": kind, "record_id": record_id, "report": {"status": "pass"}},
        )

    def validate_geometry(self, record_id, *, cancellation=None):
        return BlenderUXResult(
            "geometry",
            BlenderUXState.READY,
            {"recipe_id": record_id, "digest": "a" * 64},
        )

    def qa(self, record_id, *, cancellation=None):
        return self.inspect("qa", record_id, cancellation=cancellation)

    def rig(self, record_id, *, cancellation=None):
        return self.inspect("rig", record_id, cancellation=cancellation)

    def animation(self, record_id, *, cancellation=None):
        return self.inspect("animation", record_id, cancellation=cancellation)

    def lod(self, record_id, *, cancellation=None):
        return self.inspect("lod", record_id, cancellation=cancellation)

    def export(self, record_id, *, cancellation=None):
        return self.inspect("export", record_id, cancellation=cancellation)

    def evidence(self, evidence_id, *, cancellation=None):
        return BlenderUXResult(
            "evidence",
            BlenderUXState.READY,
            {"evidence_id": evidence_id, "status": "pass"},
        )


class SlowBlenderService(FakeBlenderService):
    def status(self, *, cancellation=None):
        for _ in range(200):
            if cancellation is not None and cancellation.cancelled:
                return BlenderUXResult(
                    "status",
                    BlenderUXState.CANCELLED,
                    {},
                    "cancelled",
                )
            time.sleep(0.005)
        return super().status(cancellation=cancellation)


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _drain(page: QWidget, *, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while getattr(page, "_kodepoia_blender_busy", False) and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.005)
    QApplication.processEvents()
    assert not getattr(page, "_kodepoia_blender_busy", False)


def test_kodestudio_exposes_service_backed_blender_page(tmp_path: Path) -> None:
    qt_app()
    window = build_window(
        project_root=tmp_path,
        blender_service=FakeBlenderService(),
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "blenderPage")
    assert page is not None
    assert page.findChild(QLabel, "blenderRuntimeStatus") is not None
    assert page.findChild(QLabel, "blenderCapabilityStatus") is not None
    assert page.findChild(QLabel, "blenderOperationStatus") is not None
    assert page.findChild(QComboBox, "blenderReportKind") is not None
    record = page.findChild(QLineEdit, "blenderRecordId")
    assert record is not None
    assert record.accessibleName()
    assert record.accessibleDescription()
    assert page.findChild(QComboBox, "blenderEvidenceId") is not None
    assert page.findChild(QPushButton, "blenderRefreshButton") is not None
    assert page.findChild(QPushButton, "blenderCapabilitiesButton") is not None
    assert page.findChild(QPushButton, "blenderLoadReportButton") is not None
    assert page.findChild(QPushButton, "blenderValidateGeometryButton") is not None
    assert page.findChild(QPushButton, "blenderEvidenceButton") is not None
    assert page.findChild(QPushButton, "blenderCancelButton") is not None
    details = page.findChild(QPlainTextEdit, "blenderDetailsView")
    assert details is not None
    assert details.accessibleName()
    assert details.accessibleDescription()
    assert getattr(page, "_kodepoia_blender_service", None) is not None

    window.close()


def test_blender_page_worker_is_non_blocking_and_cancellation_state_is_rendered(
    tmp_path: Path,
) -> None:
    qt_app()
    window = build_window(
        project_root=tmp_path,
        blender_service=SlowBlenderService(),
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "blenderPage")
    assert page is not None
    refresh = page.findChild(QPushButton, "blenderRefreshButton")
    cancel = page.findChild(QPushButton, "blenderCancelButton")
    state = page.findChild(QLabel, "blenderOperationStatus")
    assert refresh is not None and cancel is not None and state is not None

    refresh.click()
    QApplication.processEvents()
    assert getattr(page, "_kodepoia_blender_busy", False)
    assert cancel.isEnabled()
    cancel.click()
    QApplication.processEvents()
    assert "CANCELL" in state.text().upper()

    _drain(page)
    assert "CANCEL" in state.text().upper()
    window.close()


def test_blender_pseudo_locale_and_message_registration_are_explicit(tmp_path: Path) -> None:
    qt_app()
    messages = registered_blender_messages()
    assert "blender.nav" in messages
    assert "blender.details.description" in messages
    assert blender_nav_text("qps-ploc") != blender_nav_text("en")

    window = build_window(
        project_root=tmp_path,
        locale="qps-ploc",
        blender_service=FakeBlenderService(),
    )
    nav = window.findChild(QListWidget, "mainNavigation")
    assert nav is not None
    assert any(nav.item(index).text() == blender_nav_text("qps-ploc") for index in range(nav.count()))
    window.close()
