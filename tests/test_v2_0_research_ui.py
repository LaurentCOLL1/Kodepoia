from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QListWidget, QPlainTextEdit, QWidget

from kodepoia.intelligence.research.service import (
    ResearchOperationStatus,
    ResearchService,
    ResearchServiceResult,
)
from kodepoia.kodestudio.app import build_window


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _research_window(tmp_path: Path):
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    service = ResearchService(root)
    window = build_window(locale="en", project_root=root, research_service=service)
    window.show()
    QApplication.processEvents()
    nav = window.findChild(QListWidget, "mainNavigation")
    assert nav is not None
    nav.setCurrentRow(2)
    QApplication.processEvents()
    return window


def test_research_ui_exposes_scope_and_actionable_capability_states(tmp_path: Path) -> None:
    qt_app()
    window = _research_window(tmp_path)
    scope = window.findChild(QLabel, "researchQueryScope")
    diagnostics = window.findChild(QPlainTextEdit, "researchCapabilityDiagnostics")
    assert scope is not None and diagnostics is not None
    assert "stored in this project" in scope.text().lower()
    text = diagnostics.toPlainText()
    assert "research.web-discovery: NETWORK-RESTRICTED" in text
    assert "research.github-discovery: NETWORK-RESTRICTED" in text
    assert "research.github-authenticated-resource: AUTH-REQUIRED" in text
    assert "research.vision-provider: UNAVAILABLE" in text
    assert "research.explicit-web-fetch: NETWORK-RESTRICTED" in text
    assert "Action:" in text
    window.close()


def test_zero_result_query_is_labeled_as_persisted_local_search(tmp_path: Path) -> None:
    qt_app()
    window = _research_window(tmp_path)
    page = window.findChild(QWidget, "researchPage")
    status = window.findChild(QLabel, "researchCapabilityStatus")
    assert page is not None and status is not None
    page._research_render(
        ResearchServiceResult(
            operation="query",
            status=ResearchOperationStatus.READY,
            items=(),
            reason="query_completed",
        )
    )
    QApplication.processEvents()
    assert "0 result" in status.text().lower()
    assert "stored in this project" in status.text().lower()
    window.close()


def test_network_toggle_updates_provider_truth_without_hiding_failures(tmp_path: Path) -> None:
    qt_app()
    window = _research_window(tmp_path)
    diagnostics = window.findChild(QPlainTextEdit, "researchCapabilityDiagnostics")
    allow_network = window.findChild(QCheckBox, "researchAllowNetwork")
    assert diagnostics is not None and allow_network is not None
    assert "research.explicit-web-fetch: NETWORK-RESTRICTED" in diagnostics.toPlainText()
    allow_network.setChecked(True)
    QApplication.processEvents()
    updated = diagnostics.toPlainText()
    assert "research.explicit-web-fetch: READY" in updated
    assert "research.github-discovery: READY" in updated
    assert "research.web-discovery: AUTH-REQUIRED" in updated
    window.close()
