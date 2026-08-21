from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QPlainTextEdit, QPushButton, QTableWidget

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.project_wizard import create_project_dialog


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_kodestudio_builds_and_exposes_emergency_stop() -> None:
    qt_app()
    switch = KillSwitch()
    window = build_window(switch)
    assert window.objectName() == "kodepoiaMainWindow"
    stop = window.findChild(QPushButton, "killSwitchButton")
    assert stop is not None
    stop.click()
    assert switch.triggered
    window.close()


def test_project_wizard_contains_r2_acceptance_fields() -> None:
    qt_app()
    dialog = create_project_dialog()
    dialog.show()
    QApplication.processEvents()

    assert dialog.findChild(QTableWidget, "performanceBudgets") is not None
    assert dialog.findChild(QComboBox, "downloadPolicy") is not None
    assert dialog.findChild(QComboBox, "installPolicy") is not None
    assert dialog.findChild(QPlainTextEdit, "productVision") is not None
    assert dialog.findChild(QTableWidget, "productRequirements") is not None
    assert dialog.findChild(QCheckBox, "tool_comfyui") is not None

    touch = dialog.findChild(QCheckBox, "input_touch")
    android = dialog.findChild(QCheckBox, "platform_android")
    assert touch is not None and android is not None
    assert not touch.isVisible()

    android.setChecked(True)
    QApplication.processEvents()
    assert touch.isVisible()

    android.setChecked(False)
    QApplication.processEvents()
    assert not touch.isVisible()
    dialog.close()
