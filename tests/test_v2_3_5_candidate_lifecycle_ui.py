from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QListWidget, QPushButton, QTableWidget, QWidget

from kodepoia.kodestudio.app import build_window
from kodepoia.kodestudio.model_lab_candidate import ModelLabCandidateLifecycleService
from kodepoia.tuning.r15_ux import R15UXService


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_candidate_lifecycle_page_is_wired_accessible_and_localized(tmp_path) -> None:
    qt_app()
    window = build_window(locale="fr", project_root=tmp_path)
    page = window.findChild(QWidget, "modelLabCandidatePage")
    assert page is not None
    required = (
        "modelLabCandidateRefresh",
        "modelLabCandidateInspectEvaluation",
        "modelLabCandidatePreviewExport",
        "modelLabCandidateExport",
        "modelLabCandidatePreviewConversion",
        "modelLabCandidateConvert",
        "modelLabCandidateOllamaStatus",
        "modelLabCandidatePreviewPackage",
        "modelLabCandidatePackage",
        "modelLabCandidatePreviewPromotion",
        "modelLabCandidatePromote",
        "modelLabCandidatePreviewRollback",
        "modelLabCandidateRollback",
        "modelLabCandidateRole",
        "modelLabCandidateConfirm",
        "modelLabCandidateCandidatesTable",
        "modelLabCandidateDomainsTable",
        "modelLabCandidateArtifactsTable",
        "modelLabCandidateRegistryTable",
        "modelLabCandidateDiagnostics",
    )
    for object_name in required:
        widget = window.findChild(QWidget, object_name)
        assert widget is not None, object_name
        assert widget.accessibleName(), object_name
        assert widget.accessibleDescription(), object_name

    nav = window.findChild(QListWidget, "mainNavigation")
    labels = [nav.item(index).text() for index in range(nav.count())]
    assert "Cycle candidat" in labels

    role = window.findChild(QComboBox, "modelLabCandidateRole")
    assert [role.itemData(index) for index in range(role.count())] == [
        "fast",
        "core",
        "coder",
        "embed",
        "vision",
    ]
    confirm = window.findChild(QCheckBox, "modelLabCandidateConfirm")
    assert confirm.isChecked() is False
    window.close()


def test_candidate_lifecycle_empty_project_is_honest_and_non_mutating(tmp_path) -> None:
    qt_app()
    calls = []
    service = ModelLabCandidateLifecycleService(
        tmp_path,
        r15_service=R15UXService(
            tmp_path,
            handlers={"registry.promote": lambda request: calls.append(request) or {"status": "ok"}},
        ),
    )
    window = build_window(project_root=tmp_path, model_lab_candidate_service=service)
    candidates = window.findChild(QTableWidget, "modelLabCandidateCandidatesTable")
    promote = window.findChild(QPushButton, "modelLabCandidatePromote")
    assert candidates.rowCount() == 0
    promote.click()
    QApplication.processEvents()
    assert calls == []
    window.close()
