from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton

from kodepoia.kodestudio.accessibility import (
    MAIN_REQUIRED_CONTROL_IDS,
    WIZARD_REQUIRED_CONTROL_IDS,
    audit_qt_surface,
)
from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.project_wizard import create_project_dialog
from kodepoia.quality.accessibility import AccessibilityReportStatus, AccessibilityStatus


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _assert_clean(report) -> None:
    failures = [
        f"{item.rule_id}:{item.target_id}:{item.summary}"
        for item in report.results
        if item.status in {AccessibilityStatus.FAIL, AccessibilityStatus.UNKNOWN}
    ]
    assert report.status is AccessibilityReportStatus.PASS, failures
    assert report.counts["failed"] == 0, failures
    assert report.counts["unknown"] == 0, failures
    assert report.counts["blocking_failures"] == 0, failures
    assert report.counts["passed"] > 0


def test_kodestudio_main_surface_exposes_accessible_controls() -> None:
    qt_app()
    window = build_window()
    window.show()
    QApplication.processEvents()

    report = audit_qt_surface(
        window,
        surface="kodestudio-main",
        expected_ids=MAIN_REQUIRED_CONTROL_IDS,
        generated_at="2026-08-22T10:10:00Z",
    )
    _assert_clean(report)
    assert all(
        window.findChild(type(window.findChild(QPushButton, "newProjectButton")), object_name)
        is not None
        if object_name.endswith("Button")
        else True
        for object_name in ("newProjectButton", "killSwitchButton", "killSwitchResetButton")
    )
    window.close()


def test_project_wizard_exposes_required_and_dynamic_accessible_controls() -> None:
    qt_app()
    dialog = create_project_dialog()
    dialog.show()
    QApplication.processEvents()

    report = audit_qt_surface(
        dialog,
        surface="kodestudio-project-wizard",
        expected_ids=WIZARD_REQUIRED_CONTROL_IDS,
        generated_at="2026-08-22T10:11:00Z",
    )
    _assert_clean(report)

    dialog._add_requirement()
    QApplication.processEvents()
    priority = dialog.findChild(QComboBox, "requirement_1_priority")
    assert priority is not None
    assert priority.accessibleName() == "Requirement 1 priority"

    report_with_dynamic = audit_qt_surface(
        dialog,
        surface="kodestudio-project-wizard-with-requirement",
        expected_ids=WIZARD_REQUIRED_CONTROL_IDS,
        generated_at="2026-08-22T10:12:00Z",
    )
    _assert_clean(report_with_dynamic)
    assert any(
        item.target_id == "requirement_1_priority"
        and item.rule_id == "qt.control.present"
        and item.status is AccessibilityStatus.PASS
        for item in report_with_dynamic.results
    )
    dialog.close()


def test_project_wizard_keyboard_tab_progresses_through_general_fields() -> None:
    qt_app()
    dialog = create_project_dialog()
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    QApplication.processEvents()

    name = dialog.findChild(QLineEdit, "projectName")
    directory = dialog.findChild(QLineEdit, "projectDirectory")
    browse = dialog.findChild(QPushButton, "browseProjectDirectoryButton")
    assert name is not None and directory is not None and browse is not None

    name.setFocus(Qt.FocusReason.TabFocusReason)
    QApplication.processEvents()
    assert QApplication.focusWidget() is name

    QTest.keyClick(name, Qt.Key.Key_Tab)
    QApplication.processEvents()
    assert QApplication.focusWidget() is directory

    QTest.keyClick(directory, Qt.Key.Key_Tab)
    QApplication.processEvents()
    assert QApplication.focusWidget() is browse
    dialog.close()


def test_hidden_adaptive_controls_are_not_falsely_reported_as_focus_passes() -> None:
    qt_app()
    dialog = create_project_dialog()
    dialog.show()
    QApplication.processEvents()
    report = audit_qt_surface(
        dialog,
        surface="kodestudio-project-wizard-adaptive",
        expected_ids=WIZARD_REQUIRED_CONTROL_IDS,
        generated_at="2026-08-22T10:13:00Z",
    )

    for target_id in ("input_touch", "input_gyro", "input_accelerometer", "input_motion_controllers"):
        result = next(
            item
            for item in report.results
            if item.rule_id == "qt.keyboard.tab_focus" and item.target_id == target_id
        )
        assert result.status is AccessibilityStatus.NOT_APPLICABLE
        assert result.applicability_reason
    dialog.close()
