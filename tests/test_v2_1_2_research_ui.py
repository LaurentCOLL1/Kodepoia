from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QListWidget, QPlainTextEdit, QPushButton, QTableWidget, QWidget

from kodepoia.intelligence.research.service import ResearchOperationStatus, ResearchService, ResearchServiceResult, ResearchViewItem
from kodepoia.kodestudio.app import build_window


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _window(tmp_path: Path, *, locale: str = "en"):
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    window = build_window(locale=locale, project_root=root, research_service=ResearchService(root))
    window.show()
    QApplication.processEvents()
    nav = window.findChild(QListWidget, "mainNavigation")
    assert nav is not None
    nav.setCurrentRow(2)
    QApplication.processEvents()
    return window


def _candidate() -> ResearchViewItem:
    locator = "https://github.com/godotengine/godot"
    source_id = hashlib.sha256(f"github-public\0{locator}".encode("utf-8")).hexdigest()
    return ResearchViewItem(
        source_kind="github",
        source_id=source_id,
        locator=locator,
        status=ResearchOperationStatus.READY,
        freshness="unfetched",
        trust="candidate-only",
        title="godotengine/godot",
        text="Godot Engine",
        reason="descriptor_only_not_fetched:github-public:rank=1",
    )


def test_search_sources_requires_explicit_network_permission(tmp_path: Path) -> None:
    qt_app()
    window = _window(tmp_path)
    button = window.findChild(QPushButton, "researchDiscoveryButton")
    allow_network = window.findChild(QCheckBox, "researchAllowNetwork")
    state = window.findChild(QLabel, "researchDiscoveryState")
    assert button is not None and allow_network is not None and state is not None
    assert not button.isEnabled()
    assert "NETWORK-RESTRICTED" in state.text()
    allow_network.setChecked(True)
    QApplication.processEvents()
    assert button.isEnabled()
    assert "GitHub public discovery" in state.text()
    window.close()


def test_discovery_candidates_are_visibly_unfetched_and_not_evidence(tmp_path: Path) -> None:
    qt_app()
    window = _window(tmp_path)
    page = window.findChild(QWidget, "researchPage")
    status = window.findChild(QLabel, "researchCapabilityStatus")
    table = window.findChild(QTableWidget, "researchResultsTable")
    details = window.findChild(QPlainTextEdit, "researchDetails")
    assert page is not None and status is not None and table is not None and details is not None
    result = ResearchServiceResult(
        operation="discover",
        status=ResearchOperationStatus.READY,
        items=(_candidate(),),
        reason="discovery_partial",
        metadata={
            "candidate_only": True,
            "fetched": False,
            "persisted": False,
            "providers": [
                {"provider_id": "brave-web", "status": "auth-required", "reason": "brave_search_api_key_missing"},
                {"provider_id": "github-public", "status": "ready", "reason": ""},
            ],
        },
    )
    page._research_render(result)
    QApplication.processEvents()
    assert table.rowCount() == 1
    assert table.item(0, 2).text() == "UNFETCHED"
    assert table.item(0, 4).text() == "candidate-only"
    assert "Nothing here has been fetched" in status.text()
    payload = details.toPlainText()
    assert '"artifact_id": ""' in payload
    assert '"fetched": false' in payload
    assert '"persisted": false' in payload
    window.close()


def test_discovery_provider_failure_is_not_rendered_as_empty_success(tmp_path: Path) -> None:
    qt_app()
    window = _window(tmp_path)
    page = window.findChild(QWidget, "researchPage")
    status = window.findChild(QLabel, "researchCapabilityStatus")
    assert page is not None and status is not None
    result = ResearchServiceResult(
        operation="discover",
        status=ResearchOperationStatus.BLOCKED,
        items=(),
        reason="discovery_providers_unavailable",
        metadata={
            "candidate_only": True,
            "fetched": False,
            "persisted": False,
            "providers": [
                {"provider_id": "brave-web", "status": "auth-required", "reason": "brave_search_api_key_missing"},
                {"provider_id": "github-public", "status": "rate-limited", "reason": "github_search_rate_limited"},
            ],
        },
    )
    page._research_render(result)
    QApplication.processEvents()
    text = status.text()
    assert "Source discovery: BLOCKED" in text
    assert "AUTH-REQUIRED" in text
    assert "RATE-LIMITED" in text
    window.close()


def test_discovery_controls_survive_pseudo_localization(tmp_path: Path) -> None:
    qt_app()
    window = _window(tmp_path, locale="qps-ploc")
    button = window.findChild(QPushButton, "researchDiscoveryButton")
    assert button is not None and button.text().startswith("⟦") and button.text().endswith("⟧")
    window.close()
