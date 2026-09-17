from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QListWidget, QPushButton, QTableWidget, QWidget

from kodepoia.intelligence.research.service import (
    ResearchOperationStatus,
    ResearchService,
    ResearchServiceResult,
    ResearchViewItem,
)
from kodepoia.kodestudio.app import build_window


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _window(tmp_path: Path):
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    window = build_window(locale="en", project_root=root, research_service=ResearchService(root))
    window.show()
    QApplication.processEvents()
    nav = window.findChild(QListWidget, "mainNavigation")
    assert nav is not None
    nav.setCurrentRow(2)
    QApplication.processEvents()
    return window


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_candidate_row_shows_lifecycle_locator_and_has_no_selection_actions(tmp_path: Path) -> None:
    qt_app()
    window = _window(tmp_path)
    page = window.findChild(QWidget, "researchPage")
    table = window.findChild(QTableWidget, "researchResultsTable")
    include = window.findChild(QPushButton, "researchEvidenceIncludeButton")
    exclude = window.findChild(QPushButton, "researchEvidenceExcludeButton")
    assert page is not None and table is not None and include is not None and exclude is not None
    candidate = ResearchViewItem(
        source_kind="web",
        source_id=_sha("candidate-source"),
        locator="HTTPS://Example.COM/docs/#top",
        status=ResearchOperationStatus.READY,
        freshness="unfetched",
        trust="candidate-only",
        title="Candidate",
        reason="descriptor_only_not_fetched:brave-web:rank=1",
    )
    page._research_render(
        ResearchServiceResult(
            operation="discover",
            status=ResearchOperationStatus.READY,
            items=(candidate,),
            metadata={"candidate_only": True, "fetched": False, "persisted": False},
        )
    )
    QApplication.processEvents()
    assert table.rowCount() == 1
    assert table.item(0, 7).text() == "CANDIDATE_ONLY"
    assert table.item(0, 8).text() == "NOT_APPLICABLE"
    assert table.item(0, 9).text() == "https://example.com/docs"
    assert table.item(0, 12).text() == "brave-web"
    assert not include.isEnabled()
    assert not exclude.isEnabled()
    window.close()


def test_fetched_row_can_be_excluded_without_deleting_evidence(tmp_path: Path) -> None:
    qt_app()
    window = _window(tmp_path)
    page = window.findChild(QWidget, "researchPage")
    table = window.findChild(QTableWidget, "researchResultsTable")
    exclude = window.findChild(QPushButton, "researchEvidenceExcludeButton")
    assert page is not None and table is not None and exclude is not None
    artifact_id = _sha("artifact")
    fetched = ResearchViewItem(
        source_kind="web",
        source_id=_sha("fetched-source"),
        locator="https://example.com/docs",
        status=ResearchOperationStatus.READY,
        freshness="current",
        trust="guarded",
        title="Fetched",
        version="2.0.0",
        retrieved_at="2026-09-17T10:00:00Z",
        updated_at="2026-09-16T10:00:00Z",
        artifact_id=artifact_id,
    )
    result = ResearchServiceResult(
        operation="fetch",
        status=ResearchOperationStatus.READY,
        items=(fetched,),
    )
    page._research_render(result)
    QApplication.processEvents()
    assert table.item(0, 7).text() == "FETCHED"
    assert table.item(0, 8).text() == "INCLUDED"
    assert exclude.isEnabled()
    exclude.click()
    QApplication.processEvents()
    assert table.item(0, 8).text() == "EXCLUDED"
    selection_path = tmp_path / "project" / ".kodepoia" / "research" / "evidence-selection.json"
    assert selection_path.is_file()
    assert artifact_id in selection_path.read_text(encoding="utf-8")
    window.close()
