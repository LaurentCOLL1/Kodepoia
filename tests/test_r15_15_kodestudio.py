from __future__ import annotations

import json
import os
import time

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

from kodepoia.kodestudio.app import build_window
from kodepoia.tuning.r15_ux import R15UXService, R15WorkflowRequest


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_r15_page_is_wired_accessible_and_localized(tmp_path) -> None:
    qt_app()
    window = build_window(locale="fr", project_root=tmp_path, r15_service=R15UXService(tmp_path))
    page = window.findChild(QWidget, "r15TuningPage")
    assert page is not None
    for object_name in (
        "r15Domain",
        "r15Action",
        "r15StableIdentifier",
        "r15ConfirmMutation",
        "r15CatalogButton",
        "r15StatusButton",
        "r15EvidenceButton",
        "r15DryRunButton",
        "r15ExecuteButton",
        "r15StructuredResult",
    ):
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.accessibleName(), object_name
        assert widget.accessibleDescription(), object_name

    nav = window.findChild(QListWidget, "mainNavigation")
    labels = [nav.item(index).text() for index in range(nav.count())]
    assert "Expérience et Tune" in labels
    window.close()


def test_r15_ui_dry_run_is_non_mutating_and_runs_off_ui_thread(tmp_path) -> None:
    qt_app()
    calls: list[R15WorkflowRequest] = []

    def handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {"status": "ok", "token": "never-visible"}

    service = R15UXService(tmp_path, handlers={"training.run": handler})
    window = build_window(project_root=tmp_path, r15_service=service)
    domain = window.findChild(QComboBox, "r15Domain")
    action = window.findChild(QComboBox, "r15Action")
    identifier = window.findChild(QLineEdit, "r15StableIdentifier")
    dry_run = window.findChild(QPushButton, "r15DryRunButton")
    result = window.findChild(QPlainTextEdit, "r15StructuredResult")

    domain.setCurrentIndex(domain.findData("training"))
    QApplication.processEvents()
    action.setCurrentIndex(action.findData("run"))
    QApplication.processEvents()
    identifier.setText("train.plan.1")
    dry_run.click()
    page = window.findChild(QWidget, "r15TuningPage")
    assert page._r15_thread is not None
    deadline = time.monotonic() + 3.0
    while page._r15_thread is not None and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.01)
    assert page._r15_thread is None
    QApplication.processEvents()

    payload = json.loads(result.toPlainText())
    assert payload["status"] == "dry_run"
    assert payload["would_mutate"] is True
    assert calls == []
    window.close()


def test_r15_ui_confirmed_apply_uses_typed_handler_and_redacts_result(tmp_path) -> None:
    qt_app()

    def handler(request: R15WorkflowRequest) -> dict[str, object]:
        return {
            "status": "ok",
            "candidate_id": request.identifier,
            "secret": "never-visible",
        }

    service = R15UXService(tmp_path, handlers={"registry.promote": handler})
    window = build_window(project_root=tmp_path, r15_service=service)
    domain = window.findChild(QComboBox, "r15Domain")
    action = window.findChild(QComboBox, "r15Action")
    identifier = window.findChild(QLineEdit, "r15StableIdentifier")
    confirm = window.findChild(QCheckBox, "r15ConfirmMutation")
    execute = window.findChild(QPushButton, "r15ExecuteButton")
    result = window.findChild(QPlainTextEdit, "r15StructuredResult")

    domain.setCurrentIndex(domain.findData("registry"))
    QApplication.processEvents()
    action.setCurrentIndex(action.findData("promote"))
    QApplication.processEvents()
    identifier.setText("candidate.1")
    confirm.setChecked(True)
    execute.click()
    page = window.findChild(QWidget, "r15TuningPage")
    assert page._r15_thread is not None
    deadline = time.monotonic() + 3.0
    while page._r15_thread is not None and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.01)
    assert page._r15_thread is None
    QApplication.processEvents()

    payload = json.loads(result.toPlainText())
    assert payload["status"] == "ok"
    assert payload["candidate_id"] == "candidate.1"
    assert payload["secret"] == "<redacted>"
    assert "never-visible" not in result.toPlainText()
    window.close()


def test_r15_ui_exposes_no_raw_shell_or_secret_editor(tmp_path) -> None:
    qt_app()
    window = build_window(project_root=tmp_path)
    forbidden = {
        "r15RawCommand",
        "r15Shell",
        "r15Secret",
        "r15Token",
        "r15Password",
        "r15QuarantinedContent",
    }
    present = {
        child.objectName()
        for child in window.findChildren(QLineEdit)
        if child.objectName()
    }
    assert forbidden.isdisjoint(present)
    window.close()
