from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QWidget,
)

from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.model_lab_training import ModelLabTrainingService
from kodepoia.tuning.r15_ux import R15UXService, R15WorkflowRequest
from tests.test_v2_3_4_training import _project


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _wait(page: QWidget) -> None:
    deadline = time.monotonic() + 4.0
    while page._model_lab_training_workers and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.01)
    QApplication.processEvents()
    assert page._model_lab_training_workers == []


def _service(tmp_path: Path, calls: list[R15WorkflowRequest]) -> ModelLabTrainingService:
    root, _plan, _run = _project(tmp_path)

    def handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {
            "status": "ok",
            "identifier": request.identifier,
            "parent_identifier": request.parent_identifier,
            "backend": request.backend,
        }

    return ModelLabTrainingService(
        root,
        r15_service=R15UXService(
            root,
            handlers={
                "training.doctor": handler,
                "training.plan": handler,
                "training.run": handler,
                "training.status": handler,
                "training.cancel": handler,
                "training.resume": handler,
            },
        ),
    )


def test_training_workspace_is_wired_structured_accessible_localized_and_bounded(
    tmp_path: Path,
) -> None:
    _app()
    calls: list[R15WorkflowRequest] = []
    service = _service(tmp_path, calls)
    window = build_window(
        locale="fr",
        project_root=service.root,
        model_lab_training_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabTrainingPage")
    nav = window.findChild(QListWidget, "mainNavigation")
    assert page is not None and nav is not None
    labels = [nav.item(index).text() for index in range(nav.count())]
    assert "Entraînement" in labels

    plans = window.findChild(QTableWidget, "modelLabTrainingPlansTable")
    capabilities = window.findChild(QTableWidget, "modelLabTrainingCapabilitiesTable")
    runs = window.findChild(QTableWidget, "modelLabTrainingRunsTable")
    checkpoints = window.findChild(QTableWidget, "modelLabTrainingCheckpointsTable")
    assert plans is not None and plans.rowCount() == 1
    assert capabilities is not None and capabilities.rowCount() == 1
    assert runs is not None and runs.rowCount() == 1
    assert checkpoints is not None and checkpoints.rowCount() == 1
    assert plans.item(0, 1).text() == "yes"

    for object_name in (
        "modelLabTrainingPage",
        "modelLabTrainingReferenceNotice",
        "modelLabTrainingBoundaryNotice",
        "modelLabTrainingBackendTruth",
        "modelLabTrainingRefresh",
        "modelLabTrainingBackend",
        "modelLabTrainingDoctor",
        "modelLabTrainingInspectPlan",
        "modelLabTrainingPreviewRun",
        "modelLabTrainingLaunch",
        "modelLabTrainingInspectRun",
        "modelLabTrainingCancel",
        "modelLabTrainingResume",
        "modelLabTrainingConfirm",
        "modelLabTrainingState",
        "modelLabTrainingScroll",
        "modelLabTrainingSummary",
        "modelLabTrainingPlansTable",
        "modelLabTrainingCapabilitiesTable",
        "modelLabTrainingRunsTable",
        "modelLabTrainingCheckpointsTable",
        "modelLabTrainingDiagnostics",
    ):
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.accessibleName(), object_name
        assert widget.accessibleDescription(), object_name

    forbidden = {
        "modelLabTrainingConvert",
        "modelLabTrainingPromote",
        "modelLabTrainingRollback",
        "modelLabTrainingPublish",
        "modelLabTrainingRawCommand",
        "modelLabTrainingPackageInstall",
    }
    present = {
        child.objectName()
        for child in window.findChildren(QWidget)
        if child.objectName()
    }
    assert forbidden.isdisjoint(present)
    assert calls == []
    window.close()


def test_training_preview_apply_cancel_and_resume_use_typed_handlers(tmp_path: Path) -> None:
    _app()
    calls: list[R15WorkflowRequest] = []
    service = _service(tmp_path, calls)
    window = build_window(
        project_root=service.root,
        model_lab_training_service=service,
    )
    window.show()
    QApplication.processEvents()

    page = window.findChild(QWidget, "modelLabTrainingPage")
    backend = window.findChild(QComboBox, "modelLabTrainingBackend")
    preview = window.findChild(QPushButton, "modelLabTrainingPreviewRun")
    launch = window.findChild(QPushButton, "modelLabTrainingLaunch")
    cancel = window.findChild(QPushButton, "modelLabTrainingCancel")
    resume = window.findChild(QPushButton, "modelLabTrainingResume")
    confirm = window.findChild(QCheckBox, "modelLabTrainingConfirm")
    diagnostics = window.findChild(QPlainTextEdit, "modelLabTrainingDiagnostics")
    assert all(
        item is not None
        for item in (page, backend, preview, launch, cancel, resume, confirm, diagnostics)
    )

    preview.click()
    _wait(page)
    assert calls == []
    assert '"status": "dry_run"' in diagnostics.toPlainText()

    launch.click()
    _wait(page)
    assert calls == []
    assert "confirmation" in diagnostics.toPlainText().lower()

    confirm.setChecked(True)
    launch.click()
    _wait(page)
    assert calls[-1].key == "training.run"
    assert calls[-1].backend == "local"

    cancel.click()
    _wait(page)
    assert calls[-1].key == "training.cancel"

    backend.setCurrentIndex(backend.findData("kaggle"))
    resume.click()
    _wait(page)
    assert calls[-1].key == "training.resume"
    assert calls[-1].backend == "kaggle"
    assert calls[-1].parent_identifier is not None

    window.close()
