from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QListWidget, QPlainTextEdit, QPushButton, QWidget

from kodepoia.intelligence.research.service import ResearchOperationStatus, ResearchService, ResearchServiceResult
from kodepoia.kodestudio.app import build_window


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _research_window(tmp_path: Path, *, locale: str = "en"):
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    service = ResearchService(root)
    window = build_window(locale=locale, project_root=root, research_service=service)
    window.show()
    QApplication.processEvents()
    nav = window.findChild(QListWidget, "mainNavigation")
    assert nav is not None
    nav.setCurrentRow(2)
    QApplication.processEvents()
    return window


def test_v211_three_research_operations_remain_distinct(tmp_path: Path) -> None:
    qt_app()
    window = _research_window(tmp_path)
    saved = window.findChild(QPushButton, "researchSearchButton")
    discovery = window.findChild(QPushButton, "researchDiscoveryButton")
    fetch = window.findChild(QPushButton, "researchFetchButton")
    discovery_state = window.findChild(QLabel, "researchDiscoveryState")
    provider = window.findChild(QLabel, "researchProviderSummary")
    empty = window.findChild(QLabel, "researchEmptyState")
    assert saved is not None and saved.text() == "Search saved research"
    assert discovery is not None and discovery.text() == "Search sources"
    assert not discovery.isEnabled()
    assert fetch is not None and fetch.text() == "Open/fetch source"
    assert discovery_state is not None and "NETWORK-RESTRICTED" in discovery_state.text()
    assert provider is not None
    provider_text = provider.text()
    assert "Web discovery: NETWORK-RESTRICTED" in provider_text
    assert "GitHub discovery: NETWORK-RESTRICTED" in provider_text
    assert "explicit Web fetch: NETWORK-RESTRICTED" in provider_text
    assert "private GitHub: AUTH-REQUIRED" in provider_text
    assert empty is not None
    empty_text = empty.text()
    assert "No saved research exists in this project" in empty_text
    assert "Source discovery exists in live source" in empty_text
    assert "network-restricted" in empty_text
    assert "read-only credential" in empty_text
    window.close()


def test_v211_zero_saved_results_are_not_presented_as_discovery(tmp_path: Path) -> None:
    qt_app()
    window = _research_window(tmp_path)
    page = window.findChild(QWidget, "researchPage")
    status = window.findChild(QLabel, "researchCapabilityStatus")
    empty = window.findChild(QLabel, "researchEmptyState")
    assert page is not None and status is not None and empty is not None
    page._research_render(ResearchServiceResult(operation="query", status=ResearchOperationStatus.READY, items=(), reason="query_completed"))
    QApplication.processEvents()
    assert "Saved research search: READY" in status.text()
    assert "0 result" in status.text()
    assert "stored in this project" in status.text()
    assert "No matching saved research" in empty.text()
    assert "not source discovery" in empty.text()
    window.close()


def test_v211_network_permission_updates_discovery_and_fetch_truth_independently(tmp_path: Path) -> None:
    qt_app()
    window = _research_window(tmp_path)
    allow_network = window.findChild(QCheckBox, "researchAllowNetwork")
    provider = window.findChild(QLabel, "researchProviderSummary")
    discovery = window.findChild(QPushButton, "researchDiscoveryButton")
    diagnostics = window.findChild(QPlainTextEdit, "researchCapabilityDiagnostics")
    assert allow_network is not None and provider is not None and discovery is not None and diagnostics is not None
    allow_network.setChecked(True)
    QApplication.processEvents()
    assert discovery.isEnabled()
    assert "explicit Web fetch: READY" in provider.text()
    assert "Web discovery: AUTH-REQUIRED" in provider.text()
    assert "GitHub discovery: READY" in provider.text()
    text = diagnostics.toPlainText()
    assert "research.explicit-web-fetch: READY" in text
    assert "research.web-discovery: AUTH-REQUIRED" in text
    assert "research.github-discovery: READY" in text
    window.close()


def test_v211_blocked_fetch_is_actionable_and_json_is_secondary(tmp_path: Path) -> None:
    qt_app()
    window = _research_window(tmp_path)
    page = window.findChild(QWidget, "researchPage")
    status = window.findChild(QLabel, "researchCapabilityStatus")
    empty = window.findChild(QLabel, "researchEmptyState")
    technical = window.findChild(QLabel, "researchTechnicalDetailsLabel")
    details = window.findChild(QPlainTextEdit, "researchDetails")
    assert page is not None and status is not None and empty is not None
    assert technical is not None and details is not None
    page._research_render(ResearchServiceResult(operation="fetch", status=ResearchOperationStatus.BLOCKED, items=(), reason="NETWORK permission not granted"))
    QApplication.processEvents()
    assert "Open/fetch source: BLOCKED" in status.text()
    assert "Check the explicit locator and the required network permission" in empty.text()
    assert technical.text() == "Technical details (JSON)"
    assert details.maximumHeight() <= 160
    assert '"operation": "fetch"' in details.toPlainText()
    window.close()


def test_v211_new_controls_survive_pseudo_localization(tmp_path: Path) -> None:
    qt_app()
    window = _research_window(tmp_path, locale="qps-ploc")
    saved = window.findChild(QPushButton, "researchSearchButton")
    discovery = window.findChild(QPushButton, "researchDiscoveryButton")
    fetch = window.findChild(QPushButton, "researchFetchButton")
    technical = window.findChild(QLabel, "researchTechnicalDetailsLabel")
    assert saved is not None and saved.text().startswith("⟦") and saved.text().endswith("⟧")
    assert discovery is not None and discovery.text().startswith("⟦") and discovery.text().endswith("⟧")
    assert fetch is not None and fetch.text().startswith("⟦") and fetch.text().endswith("⟧")
    assert technical is not None and technical.text().startswith("⟦") and technical.text().endswith("⟧")
    window.close()
