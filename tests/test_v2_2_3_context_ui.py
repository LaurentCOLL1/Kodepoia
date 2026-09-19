from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QWidget,
)

from kodepoia.intelligence.project_knowledge import (
    ProjectKnowledgeSourceKind,
    ProjectKnowledgeState,
)
from kodepoia.intelligence.project_retrieval import (
    ProjectEmbeddingIdentity,
    ProjectRetrievalHit,
    ProjectRetrievalRequest,
    ProjectRetrievalResult,
    ProjectRetrievalSourceRef,
    ProjectRetrievalState,
)
from kodepoia.kodestudio.project_context_preview import (
    create_project_context_preview_widget,
)
from kodepoia.kodestudio.research_panel import create_research_page
from kodepoia.kodestudio.runtime_localization import KodeStudioTranslator


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _hit(seed: str, text: str, score: float) -> ProjectRetrievalHit:
    content_sha = _digest(f"content:{seed}")
    ref = ProjectRetrievalSourceRef(
        knowledge_id=_digest(f"knowledge:{seed}"),
        source_kind=ProjectKnowledgeSourceKind.RESEARCH_PACK,
        source_identity=_digest(f"identity:{seed}"),
        source_digest_sha256=_digest(f"source:{seed}"),
        content_sha256=content_sha,
        locator=f"research-pack:///{seed}",
        trust_class="external_guarded_untrusted",
        freshness="current",
        version="4.7",
        state=ProjectKnowledgeState.ACTIVE,
        provenance={"citation_ids": [f"citation-{seed}"]},
    )
    return ProjectRetrievalHit(
        content_sha256=content_sha,
        score=score,
        primary_knowledge_id=ref.knowledge_id,
        text=text,
        source_refs=(ref,),
    )


def _ready_result() -> ProjectRetrievalResult:
    hits = (
        _hit("one", "first context candidate", 0.95),
        _hit("two", "second context candidate", 0.60),
    )
    return ProjectRetrievalResult(
        state=ProjectRetrievalState.READY,
        request=ProjectRetrievalRequest(
            "project:fixture",
            "Explain this project",
            limit=2,
        ),
        catalog_digest_sha256=_digest("catalog"),
        provider_identity=ProjectEmbeddingIdentity(
            "fixture",
            "deterministic",
            "1",
        ),
        eligible_candidates=2,
        normalized_candidates=2,
        hits=hits,
        diagnostic="Semantic retrieval completed",
    )


def test_context_preview_exposes_source_trust_budget_reason_and_overrides() -> None:
    qt_app()
    widget = create_project_context_preview_widget(budget_tokens=1)
    widget.show()
    result = _ready_result()
    widget._project_context_load_result(result)
    QApplication.processEvents()

    table = widget.findChild(QTableWidget, "projectContextCandidatesTable")
    budget = widget.findChild(QSpinBox, "projectContextBudget")
    build = widget.findChild(QPushButton, "projectContextBuildButton")
    summary = widget.findChild(QLabel, "projectContextBudgetSummary")
    state = widget.findChild(QLabel, "projectContextPreviewState")
    preview = widget.findChild(QPlainTextEdit, "projectContextRenderedPreview")
    assert table is not None and budget is not None and build is not None
    assert summary is not None and state is not None and preview is not None

    assert table.rowCount() == 2
    assert table.item(0, 1).text().startswith("research_pack:")
    assert table.item(0, 2).text() == "0.950000"
    assert "external_guarded_untrusted" in table.item(0, 3).text()
    assert "current" in table.item(0, 4).text()
    assert int(table.item(0, 5).text()) > 0
    assert build.isEnabled()

    first_override = widget.findChild(QComboBox, "projectContextOverride_0")
    second_override = widget.findChild(QComboBox, "projectContextOverride_1")
    assert first_override is not None and second_override is not None
    first_override.setCurrentIndex(first_override.findData("exclude"))
    second_override.setCurrentIndex(second_override.findData("include"))
    budget.setValue(1)

    build.click()
    QApplication.processEvents()

    assert table.item(0, 6).text() == "omitted / user_excluded"
    assert table.item(1, 6).text() == "selected / user_included"
    assert "<UNTRUSTED_DATA>" in preview.toPlainText()
    assert "citation-two" in preview.toPlainText()
    assert "over-budget=" in summary.text()
    assert "data-only" in state.text()
    widget.close()


def test_context_preview_keeps_non_ready_retrieval_explicit() -> None:
    qt_app()
    widget = create_project_context_preview_widget()
    empty = ProjectRetrievalResult(
        state=ProjectRetrievalState.EMPTY,
        request=ProjectRetrievalRequest(
            "project:fixture",
            "Nothing matched",
        ),
        catalog_digest_sha256=_digest("catalog"),
        provider_identity=ProjectEmbeddingIdentity(
            "fixture",
            "deterministic",
            "1",
        ),
        eligible_candidates=1,
        normalized_candidates=1,
        hits=(),
        diagnostic="Embedding capability is ready; no candidate met min_score",
    )
    widget._project_context_load_result(empty)

    build = widget.findChild(QPushButton, "projectContextBuildButton")
    state = widget.findChild(QLabel, "projectContextPreviewState")
    table = widget.findChild(QTableWidget, "projectContextCandidatesTable")
    assert build is not None and state is not None and table is not None
    assert not build.isEnabled()
    assert table.rowCount() == 0
    assert "EMPTY" in state.text()
    assert "no candidate met min_score" in state.text()
    widget.close()


def test_research_page_contains_project_context_preview(tmp_path: Path) -> None:
    qt_app()
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)

    page = create_research_page(
        root,
        translator=KodeStudioTranslator("en"),
    )
    preview = page.findChild(QWidget, "projectContextPreview")
    table = page.findChild(QTableWidget, "projectContextCandidatesTable")
    state = page.findChild(QLabel, "projectContextPreviewState")

    assert preview is not None
    assert table is not None
    assert state is not None
    assert "No retrieval result loaded" in state.text()
    assert page._project_context_preview_widget is preview
    page.close()
