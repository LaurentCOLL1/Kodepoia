from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QTableWidget, QWidget

from kodepoia.kodestudio.app import build_window


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_v236_empty_project_model_lab_surfaces_are_deterministic_accessible_and_non_authorizing(
    tmp_path,
) -> None:
    qt_app()
    window = build_window(project_root=tmp_path / "project", locale="qps-ploc")

    for object_name in (
        "modelLabPage",
        "modelLabCurationPage",
        "modelLabBenchDecisionPage",
        "modelLabTrainingPage",
        "modelLabCandidatePage",
    ):
        page = window.findChild(QWidget, object_name)
        assert page is not None, object_name
        assert page.accessibleName(), object_name
        assert page.accessibleDescription(), object_name

    for object_name in (
        "modelLabCurationExperiencesTable",
        "modelLabCurationDatasetsTable",
        "modelLabBenchDecisionReportsTable",
        "modelLabBenchDecisionDecisionsTable",
        "modelLabTrainingPlansTable",
        "modelLabTrainingRunsTable",
        "modelLabCandidateCandidatesTable",
        "modelLabCandidateArtifactsTable",
    ):
        table = window.findChild(QTableWidget, object_name)
        assert table is not None, object_name
        assert table.rowCount() == 0, object_name
        assert table.accessibleName(), object_name
        assert table.accessibleDescription(), object_name

    names = {
        child.objectName()
        for child in window.findChildren(QWidget)
        if child.objectName()
    }
    assert "modelLabPublicPublish" not in names
    assert "modelLabArbitraryShell" not in names
    assert "modelLabInstallDependency" not in names
    assert "modelLabAutoTrainKnowledge" not in names
    window.close()
