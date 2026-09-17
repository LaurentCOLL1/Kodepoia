from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QListWidget, QTableWidget, QWidget

from kodepoia.intelligence.research.contracts import ResearchSourceKind
from kodepoia.intelligence.research.service import (
    ResearchOperationStatus,
    ResearchService,
    ResearchServiceResult,
    ResearchViewItem,
)
from kodepoia.kodestudio.app import build_window

VIDEO_ID = "dQw4w9WgXcQ"


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
    page = window.findChild(QWidget, "researchPage")
    assert page is not None
    return window, page


def test_v215_kodestudio_exposes_extended_fetch_kinds_and_provider_state(tmp_path: Path) -> None:
    qt_app()
    window, page = _research_window(tmp_path)
    fetch_kind = window.findChild(QComboBox, "researchFetchKind")
    state = window.findChild(QLabel, "researchExtendedSourceState")
    assert fetch_kind is not None and state is not None
    values = {str(fetch_kind.itemData(index)) for index in range(fetch_kind.count())}
    assert ResearchSourceKind.COMMUNITY.value in values
    assert ResearchSourceKind.YOUTUBE.value in values
    assert "Community HTML" in state.text()
    assert "YouTube metadata" in state.text()
    assert page._research_extended_sources is not None
    window.close()


def test_v215_selecting_typed_candidate_prefills_explicit_fetch(tmp_path: Path) -> None:
    qt_app()
    window, page = _research_window(tmp_path)
    locator = window.findChild(QLineEdit, "researchLocator")
    fetch_kind = window.findChild(QComboBox, "researchFetchKind")
    results = window.findChild(QTableWidget, "researchResultsTable")
    state = window.findChild(QLabel, "researchExtendedSourceState")
    assert locator is not None and fetch_kind is not None and results is not None and state is not None

    candidate = ResearchViewItem(
        source_kind=ResearchSourceKind.YOUTUBE.value,
        source_id="a" * 64,
        locator=f"https://www.youtube.com/watch?v={VIDEO_ID}",
        status=ResearchOperationStatus.READY,
        freshness="unfetched",
        trust="candidate-only",
        title="Video candidate",
        reason="descriptor_only_not_fetched:youtube-search:rank=1",
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

    assert results.currentRow() == 0
    assert str(fetch_kind.currentData()) == ResearchSourceKind.YOUTUBE.value
    assert locator.text() == candidate.locator
    assert "descriptor-only" in state.text()
    assert "Open/fetch source" in state.text()
    window.close()


def test_v215_youtube_without_network_is_explicitly_blocked(tmp_path: Path) -> None:
    qt_app()
    window, page = _research_window(tmp_path)
    fetch_kind = window.findChild(QComboBox, "researchFetchKind")
    locator = window.findChild(QLineEdit, "researchLocator")
    assert fetch_kind is not None and locator is not None

    index = fetch_kind.findData(ResearchSourceKind.YOUTUBE.value)
    assert index >= 0
    fetch_kind.setCurrentIndex(index)
    locator.setText(f"https://www.youtube.com/watch?v={VIDEO_ID}")

    request_type = page._research_run_fetch.__globals__.get("ResearchFetchRequest")
    assert request_type is not None
    request = request_type(kind=ResearchSourceKind.YOUTUBE, locator=locator.text())
    result = page._research_service.fetch(request)
    assert result.status is ResearchOperationStatus.BLOCKED
    assert result.reason == "network_permission_not_granted"
    assert result.items == ()
    assert result.metadata["v2_1_5"] is True
    window.close()
