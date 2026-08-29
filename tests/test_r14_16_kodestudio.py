from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from kodepoia.backend.liveops_ux import BackendLiveOpsUXService, LiveOpsUXRequest
from kodepoia.kodestudio.app import build_window


class FixtureDomain:
    def authorize(self, request: LiveOpsUXRequest) -> bool:
        return True

    def authorize_production(self, request: LiveOpsUXRequest) -> bool:
        return False

    def invoke(self, request: LiveOpsUXRequest) -> dict[str, object]:
        return {
            "status": "ok",
            "resource": request.resource_id,
            "access_token": "never-visible",
        }


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_backend_liveops_page_is_wired_into_main_window_and_accessible(tmp_path) -> None:
    qt_app()
    window = build_window(
        locale="en",
        project_root=tmp_path,
        r14_service=BackendLiveOpsUXService(FixtureDomain()),
    )
    page = window.findChild(QWidget, "backendLiveOpsPage")
    assert page is not None
    required = (
        "r14Environment",
        "r14Operation",
        "r14Action",
        "r14Mode",
        "r14ResourceId",
        "r14ConfirmMutation",
        "r14CatalogButton",
        "r14ExecuteButton",
        "r14StructuredResult",
    )
    for object_name in required:
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.accessibleName(), object_name
        assert widget.accessibleDescription(), object_name
    window.close()


def test_backend_liveops_preview_uses_same_domain_facade_and_redacts_result(tmp_path) -> None:
    qt_app()
    window = build_window(
        project_root=tmp_path,
        r14_service=BackendLiveOpsUXService(FixtureDomain()),
    )
    operation = window.findChild(QComboBox, "r14Operation")
    action = window.findChild(QComboBox, "r14Action")
    mode = window.findChild(QComboBox, "r14Mode")
    resource = window.findChild(QLineEdit, "r14ResourceId")
    execute = window.findChild(QPushButton, "r14ExecuteButton")
    result = window.findChild(QPlainTextEdit, "r14StructuredResult")
    assert all(item is not None for item in (operation, action, mode, resource, execute, result))

    operation.setCurrentIndex(operation.findData("remote_config"))
    QApplication.processEvents()
    assert action.currentData() == "preview"
    assert mode.currentData() == "preview"
    assert resource.isEnabled()
    resource.setText("flag.release")
    execute.click()
    QApplication.processEvents()

    payload = json.loads(result.toPlainText())
    assert payload["status"] == "ok"
    assert payload["operation"] == "remote_config"
    assert payload["mode"] == "preview"
    assert payload["result"]["access_token"] == "<redacted>"
    assert "never-visible" not in result.toPlainText()
    window.close()


def test_mutating_ui_action_resets_confirmation_and_keeps_domain_authority_separate(tmp_path) -> None:
    qt_app()
    window = build_window(project_root=tmp_path)
    operation = window.findChild(QComboBox, "r14Operation")
    action = window.findChild(QComboBox, "r14Action")
    mode = window.findChild(QComboBox, "r14Mode")
    resource = window.findChild(QLineEdit, "r14ResourceId")
    confirm = window.findChild(QCheckBox, "r14ConfirmMutation")
    execute = window.findChild(QPushButton, "r14ExecuteButton")
    result = window.findChild(QPlainTextEdit, "r14StructuredResult")

    operation.setCurrentIndex(operation.findData("content"))
    QApplication.processEvents()
    action.setCurrentIndex(action.findData("rollout"))
    QApplication.processEvents()
    assert mode.currentData() == "apply"
    assert not confirm.isChecked()
    resource.setText("content.release")
    confirm.setChecked(True)
    execute.click()
    QApplication.processEvents()
    payload = json.loads(result.toPlainText())
    assert payload["status"] == "blocked"
    assert payload["reason"] == "domain_permission_denied"
    window.close()


def test_french_navigation_is_localized_and_no_raw_secret_or_endpoint_editor_exists(tmp_path) -> None:
    qt_app()
    window = build_window(locale="fr", project_root=tmp_path)
    nav = window.findChild(QListWidget, "mainNavigation")
    assert nav is not None
    labels = [nav.item(index).text() for index in range(nav.count())]
    assert "Backend et LiveOps" in labels
    forbidden_names = {
        "r14RawCommand",
        "r14Endpoint",
        "r14Secret",
        "r14Token",
        "r14Password",
    }
    present_names = {
        child.objectName()
        for child in window.findChildren(QLineEdit)
        if child.objectName()
    }
    assert forbidden_names.isdisjoint(present_names)
    window.close()
