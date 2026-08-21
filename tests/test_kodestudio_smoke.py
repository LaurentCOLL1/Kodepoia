from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
)

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.project_wizard import create_project_dialog
from kodepoia.product.spec import ProductDocumentType
from kodepoia.project.dna import ApprovalPolicy, DecisionState, Dimension, ProjectType


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


def test_project_wizard_normalizes_all_qt_enum_boundaries() -> None:
    qt_app()
    dialog = create_project_dialog()
    dialog.show()
    QApplication.processEvents()

    project_type = dialog.findChild(QComboBox, "projectType")
    dimension = dialog.findChild(QComboBox, "dimension")
    online = dialog.findChild(QComboBox, "online")
    multiplayer = dialog.findChild(QComboBox, "multiplayer")
    download_policy = dialog.findChild(QComboBox, "downloadPolicy")
    install_policy = dialog.findChild(QComboBox, "installPolicy")
    document_type = dialog.findChild(QComboBox, "productDocumentType")
    capability = dialog.findChild(QComboBox, "capability_voice")

    assert project_type is not None
    assert dimension is not None
    assert online is not None
    assert multiplayer is not None
    assert download_policy is not None
    assert install_policy is not None
    assert document_type is not None
    assert capability is not None

    # Qt stores primitive strings. Domain code reconstructs typed StrEnum values.
    assert project_type.currentData() == ProjectType.GAME.value
    assert dialog._enum_value(project_type, ProjectType) is ProjectType.GAME
    assert dialog._enum_value(dimension, Dimension) is Dimension.D3
    assert dialog._enum_value(online, DecisionState) is DecisionState.NO
    assert dialog._enum_value(multiplayer, DecisionState) is DecisionState.NO
    assert dialog._enum_value(download_policy, ApprovalPolicy) is ApprovalPolicy.ASK
    assert dialog._enum_value(install_policy, ApprovalPolicy) is ApprovalPolicy.ASK
    assert dialog._enum_value(document_type, ProductDocumentType) is ProductDocumentType.GDD
    assert dialog._enum_value(capability, DecisionState) is DecisionState.NO

    # Switching to a non-game project must use the same normalized boundary.
    project_type.setCurrentIndex(project_type.findData(ProjectType.DESKTOP_APP.value))
    QApplication.processEvents()
    assert dialog._enum_value(project_type, ProjectType) is ProjectType.DESKTOP_APP
    engine = dialog.findChild(QLineEdit, "engine")
    assert engine is not None and not engine.isEnabled()
    assert dialog._enum_value(document_type, ProductDocumentType) is ProductDocumentType.PRD

    # Switching back to game must restore game-specific controls and GDD default.
    project_type.setCurrentIndex(project_type.findData(ProjectType.GAME.value))
    QApplication.processEvents()
    assert engine.isEnabled()
    assert dialog._enum_value(document_type, ProductDocumentType) is ProductDocumentType.GDD
    dialog.close()
