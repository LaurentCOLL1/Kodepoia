from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget, QWidget

from kodepoia.intelligence.project_knowledge import (
    ProjectKnowledgeSourceKind,
    ProjectKnowledgeState,
)
from kodepoia.intelligence.project_knowledge_lifecycle import (
    ProjectKnowledgeLifecycleAssessment,
    ProjectKnowledgeLifecycleReason,
    ProjectKnowledgeLifecycleReport,
    ProjectKnowledgeLifecycleStatus,
    ProjectKnowledgeSelection,
)
from kodepoia.kodestudio.project_knowledge_lifecycle import (
    create_project_knowledge_lifecycle_widget,
)
from kodepoia.kodestudio.research_panel import create_research_page
from kodepoia.kodestudio.runtime_localization import KodeStudioTranslator


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _assessment(
    seed: str,
    *,
    status: ProjectKnowledgeLifecycleStatus,
    reason: ProjectKnowledgeLifecycleReason,
    selection: ProjectKnowledgeSelection = ProjectKnowledgeSelection.AUTO,
) -> ProjectKnowledgeLifecycleAssessment:
    return ProjectKnowledgeLifecycleAssessment(
        knowledge_id=_digest(f"knowledge:{seed}"),
        source_kind=ProjectKnowledgeSourceKind.PROJECT_FILE,
        locator=f"project:///{seed}.md",
        selection=selection,
        status=status,
        reason=reason,
        effective_state=(
            ProjectKnowledgeState.ACTIVE
            if status is ProjectKnowledgeLifecycleStatus.FRESH
            else ProjectKnowledgeState.INVALIDATED
        ),
        version_keys=("engine.godot",),
        baseline_source_fingerprint_sha256=_digest(f"baseline:{seed}"),
        current_source_fingerprint_sha256=_digest(f"current:{seed}"),
        baseline_version_fingerprint_sha256=_digest("version:4.7"),
        current_version_fingerprint_sha256=_digest("version:4.8"),
    )


def _report(*items: ProjectKnowledgeLifecycleAssessment) -> ProjectKnowledgeLifecycleReport:
    return ProjectKnowledgeLifecycleReport(
        project_scope="project:fixture",
        catalog_digest_sha256=_digest("catalog"),
        lifecycle_digest_sha256=_digest("lifecycle"),
        items=tuple(items),
    )


def test_lifecycle_widget_exposes_stale_state_and_source_delete_boundary() -> None:
    qt_app()
    widget = create_project_knowledge_lifecycle_widget()
    widget._project_knowledge_load_lifecycle(
        _report(
            _assessment(
                "stale",
                status=ProjectKnowledgeLifecycleStatus.STALE,
                reason=ProjectKnowledgeLifecycleReason.SOURCE_CHANGED,
            )
        )
    )

    table = widget.findChild(QTableWidget, "projectKnowledgeLifecycleTable")
    state = widget.findChild(QLabel, "projectKnowledgeLifecycleState")
    boundary = widget.findChild(QLabel, "projectKnowledgeSourceDeleteBoundary")
    delete_button = widget.findChild(
        QPushButton,
        "projectKnowledgeDeleteDerivedButton",
    )
    assert table is not None and state is not None and boundary is not None
    assert delete_button is not None
    assert table.rowCount() == 1
    assert table.item(0, 2).text() == "STALE"
    assert table.item(0, 3).text() == "source_changed"
    assert "stale=1" in state.text()
    assert "never deletes Research Packs" in boundary.text()
    assert not delete_button.isEnabled()
    widget.close()


def test_lifecycle_controls_call_explicit_handlers() -> None:
    qt_app()
    events: list[tuple[str, str]] = []
    current = _report(
        _assessment(
            "fresh",
            status=ProjectKnowledgeLifecycleStatus.FRESH,
            reason=ProjectKnowledgeLifecycleReason.CURRENT,
        )
    )

    def on_selection(knowledge_id: str, selection: ProjectKnowledgeSelection):
        events.append((knowledge_id, selection.value))
        return current

    def on_refresh():
        events.append(("refresh", "rebuild"))
        return current

    def on_delete(ids: tuple[str, ...]):
        events.append((ids[0], "delete-derived"))
        return None

    widget = create_project_knowledge_lifecycle_widget(
        on_selection=on_selection,
        on_refresh=on_refresh,
        on_delete_derived=on_delete,
    )
    widget._project_knowledge_load_lifecycle(current)

    include = widget.findChild(QPushButton, "projectKnowledgeIncludeButton")
    exclude = widget.findChild(QPushButton, "projectKnowledgeExcludeButton")
    auto = widget.findChild(QPushButton, "projectKnowledgeAutoButton")
    refresh = widget.findChild(QPushButton, "projectKnowledgeRefreshButton")
    delete_button = widget.findChild(
        QPushButton,
        "projectKnowledgeDeleteDerivedButton",
    )
    assert all(
        button is not None and button.isEnabled()
        for button in (include, exclude, auto, refresh, delete_button)
    )

    include.click()
    exclude.click()
    auto.click()
    refresh.click()
    delete_button.click()
    QApplication.processEvents()

    knowledge_id = current.items[0].knowledge_id
    assert (knowledge_id, "include") in events
    assert (knowledge_id, "exclude") in events
    assert (knowledge_id, "auto") in events
    assert ("refresh", "rebuild") in events
    assert (knowledge_id, "delete-derived") in events
    widget.close()


def test_research_page_contains_v2_2_4_lifecycle_surface(tmp_path: Path) -> None:
    qt_app()
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)

    page = create_research_page(
        root,
        translator=KodeStudioTranslator("en"),
    )
    lifecycle = page.findChild(QWidget, "projectKnowledgeLifecycle")
    table = page.findChild(QTableWidget, "projectKnowledgeLifecycleTable")
    boundary = page.findChild(QLabel, "projectKnowledgeSourceDeleteBoundary")
    assert lifecycle is not None
    assert table is not None
    assert boundary is not None
    assert "derived catalog/lifecycle entry" in boundary.text()
    assert page._project_knowledge_lifecycle_widget is lifecycle
    page.close()
