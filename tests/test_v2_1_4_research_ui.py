from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget

from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchFreshness,
    ResearchSource,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.evidence import EvidenceSelection, EvidenceWorkspace
from kodepoia.intelligence.research.service import ResearchOperationStatus, ResearchViewItem
from kodepoia.intelligence.research.store import ResearchStore
from kodepoia.kodestudio.research_synthesis import create_cited_synthesis_widget


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _artifact() -> ResearchArtifact:
    return ResearchArtifact.from_content(
        source=ResearchSource(
            kind=ResearchSourceKind.WEB,
            locator="https://example.com/docs",
            status=ResearchStatus.READY,
            title="Evidence",
            version="2.0.0",
        ),
        content="The selected evidence supports this source fact.",
        retrieved_at="2026-09-17T10:00:00Z",
        freshness=ResearchFreshness.CURRENT,
    )


def _view(artifact: ResearchArtifact) -> ResearchViewItem:
    return ResearchViewItem(
        source_kind=artifact.source.kind.value,
        source_id=artifact.source.source_id,
        locator=artifact.source.locator,
        status=ResearchOperationStatus.READY,
        freshness=artifact.freshness.value,
        trust=artifact.trust.value,
        title=artifact.source.title,
        version=artifact.source.version,
        retrieved_at=artifact.retrieved_at,
        artifact_id=artifact.artifact_id,
    )


def test_structured_synthesis_and_pack_state_are_visible(tmp_path: Path) -> None:
    qt_app()
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    store = ResearchStore(root)
    artifact = _artifact()
    store.save_artifact(artifact)
    workspace = EvidenceWorkspace.project(
        (_view(artifact),),
        revisions=store.list_evidence_revisions(),
        selections={artifact.artifact_id: EvidenceSelection.INCLUDED},
    )
    widget = create_cited_synthesis_widget(
        root,
        workspace_provider=lambda: workspace,
        selection_provider=lambda: {artifact.artifact_id: EvidenceSelection.INCLUDED},
        question_provider=lambda: "What does the selected evidence support?",
    )
    widget.show()
    QApplication.processEvents()
    synthesize = widget.findChild(QPushButton, "researchSynthesizeButton")
    save = widget.findChild(QPushButton, "researchSavePackButton")
    table = widget.findChild(QTableWidget, "researchSynthesisClaimsTable")
    state = widget.findChild(QLabel, "researchSynthesisState")
    provenance = widget.findChild(QLabel, "researchSynthesisProvenance")
    assert synthesize is not None and save is not None and table is not None
    assert state is not None and provenance is not None
    assert not save.isEnabled()

    synthesize.click()
    QApplication.processEvents()
    assert table.rowCount() == 2
    assert table.item(0, 0).text() == "source_fact"
    assert table.item(1, 0).text() == "inference"
    assert "@" in table.item(0, 2).text()
    assert "citation" in provenance.text().lower()
    assert save.isEnabled()

    save.click()
    QApplication.processEvents()
    assert "Research Pack saved" in state.text()
    pack_path = widget._research_pack_path
    assert pack_path is not None and pack_path.is_file()
    assert pack_path.parent == root / ".kodepoia" / "research" / "packs"
    widget.close()


def test_synthesis_surface_rejects_non_explicit_selection(tmp_path: Path) -> None:
    qt_app()
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    store = ResearchStore(root)
    artifact = _artifact()
    store.save_artifact(artifact)
    workspace = EvidenceWorkspace.project((_view(artifact),), revisions=store.list_evidence_revisions())
    widget = create_cited_synthesis_widget(
        root,
        workspace_provider=lambda: workspace,
        selection_provider=dict,
        question_provider=lambda: "No implicit evidence.",
    )
    widget._research_run_synthesis()
    state = widget.findChild(QLabel, "researchSynthesisState")
    table = widget.findChild(QTableWidget, "researchSynthesisClaimsTable")
    assert state is not None and table is not None
    assert "explicitly included" in state.text()
    assert table.rowCount() == 0
    widget.close()
