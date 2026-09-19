from __future__ import annotations

from collections.abc import Callable

from kodepoia.intelligence.project_knowledge_lifecycle import (
    ProjectKnowledgeLifecycleReport,
    ProjectKnowledgeLifecycleStatus,
    ProjectKnowledgeSelection,
)
from kodepoia.kodestudio.accessibility import mark_accessible


def create_project_knowledge_lifecycle_widget(
    *,
    on_selection: Callable[[str, ProjectKnowledgeSelection], ProjectKnowledgeLifecycleReport | None]
    | None = None,
    on_refresh: Callable[[], ProjectKnowledgeLifecycleReport | None] | None = None,
    on_delete_derived: Callable[[tuple[str, ...]], ProjectKnowledgeLifecycleReport | None]
    | None = None,
):
    """Create the V2.2.4 project-knowledge lifecycle surface.

    The widget performs no hidden source scan, network request, memory write, or
    source deletion. Callers supply explicit lifecycle operations and load the
    resulting report through the exposed callback.
    """

    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    widget = QWidget()
    widget.setObjectName("projectKnowledgeLifecycle")
    widget.setAccessibleName("Project Knowledge lifecycle")
    layout = QVBoxLayout(widget)

    title = QLabel("<h3>Project Knowledge lifecycle</h3>")
    title.setObjectName("projectKnowledgeLifecycleTitle")
    layout.addWidget(title)

    state = QLabel(
        "No lifecycle report loaded. Refresh/rebuild is explicit and derived-only."
    )
    state.setObjectName("projectKnowledgeLifecycleState")
    state.setAccessibleName("Project Knowledge lifecycle state")
    state.setWordWrap(True)
    layout.addWidget(state)

    boundary = QLabel(
        "Delete derived knowledge removes only the derived catalog/lifecycle entry. "
        "It never deletes Research Packs, project files, memory source records, or "
        "historical citation evidence."
    )
    boundary.setObjectName("projectKnowledgeSourceDeleteBoundary")
    boundary.setAccessibleName("Source deletion boundary")
    boundary.setWordWrap(True)
    layout.addWidget(boundary)

    table = mark_accessible(
        QTableWidget(0, 6),
        object_name="projectKnowledgeLifecycleTable",
        name="Project Knowledge lifecycle entries",
        description=(
            "Project knowledge source, persisted selection, lifecycle state, "
            "invalidation reason, version dependencies, and fingerprint."
        ),
        description_required=True,
    )
    table.setHorizontalHeaderLabels(
        [
            "Source",
            "Selection",
            "Lifecycle",
            "Reason",
            "Version dependencies",
            "Fingerprint",
        ]
    )
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(table)

    actions = QHBoxLayout()
    auto_button = mark_accessible(
        QPushButton("Auto"),
        object_name="projectKnowledgeAutoButton",
        name="Use automatic project knowledge selection",
        description="Persist Auto for the selected derived knowledge entry.",
        description_required=True,
    )
    include_button = mark_accessible(
        QPushButton("Include"),
        object_name="projectKnowledgeIncludeButton",
        name="Include project knowledge",
        description="Persist Include for the selected derived knowledge entry.",
        description_required=True,
    )
    exclude_button = mark_accessible(
        QPushButton("Exclude"),
        object_name="projectKnowledgeExcludeButton",
        name="Exclude project knowledge",
        description="Persist Exclude for the selected derived knowledge entry.",
        description_required=True,
    )
    refresh_button = mark_accessible(
        QPushButton("Refresh / rebuild derived"),
        object_name="projectKnowledgeRefreshButton",
        name="Refresh or rebuild derived project knowledge",
        description=(
            "Run the caller-supplied explicit refresh/rebuild operation. Source "
            "evidence remains immutable."
        ),
        description_required=True,
    )
    delete_button = mark_accessible(
        QPushButton("Delete derived"),
        object_name="projectKnowledgeDeleteDerivedButton",
        name="Delete derived project knowledge",
        description=(
            "Delete only the selected derived Project Knowledge entry. Source "
            "files, Research Packs, memory records, and citation evidence are preserved."
        ),
        description_required=True,
    )
    for button in (auto_button, include_button, exclude_button, refresh_button, delete_button):
        button.setEnabled(False)
        actions.addWidget(button)
    actions.addStretch(1)
    layout.addLayout(actions)

    widget._project_knowledge_lifecycle_report = None
    widget._project_knowledge_lifecycle_ids = []

    def _selected_id() -> str | None:
        row = table.currentRow()
        if row < 0 or row >= len(widget._project_knowledge_lifecycle_ids):
            return None
        return widget._project_knowledge_lifecycle_ids[row]

    def load_report(report: ProjectKnowledgeLifecycleReport) -> None:
        widget._project_knowledge_lifecycle_report = report
        widget._project_knowledge_lifecycle_ids = [
            item.knowledge_id for item in report.items
        ]
        table.setRowCount(len(report.items))
        for row, item in enumerate(report.items):
            source = f"{item.source_kind.value}: {item.locator}"
            fingerprint = (
                item.current_source_fingerprint_sha256
                or item.baseline_source_fingerprint_sha256
                or "none"
            )
            values = (
                source,
                item.selection.value,
                item.status.value.upper(),
                item.reason.value,
                ", ".join(item.version_keys) or "none",
                fingerprint,
            )
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
        if report.items:
            table.selectRow(0)
        state.setText(
            f"Lifecycle: {len(report.items)} item(s) | "
            f"stale={report.stale_count} | "
            f"invalidated={report.invalidated_count} | "
            f"missing={report.missing_count}. "
            "Stale/invalidated knowledge is not eligible for fresh context."
        )
        has_selection_handler = on_selection is not None and bool(report.items)
        auto_button.setEnabled(has_selection_handler)
        include_button.setEnabled(has_selection_handler)
        exclude_button.setEnabled(has_selection_handler)
        refresh_button.setEnabled(on_refresh is not None)
        delete_button.setEnabled(on_delete_derived is not None and bool(report.items))

    def apply_selection(selection: ProjectKnowledgeSelection) -> None:
        knowledge_id = _selected_id()
        if knowledge_id is None or on_selection is None:
            return
        report = on_selection(knowledge_id, selection)
        if report is not None:
            load_report(report)

    def refresh() -> None:
        if on_refresh is None:
            return
        report = on_refresh()
        if report is not None:
            load_report(report)

    def delete_derived() -> None:
        knowledge_id = _selected_id()
        if knowledge_id is None or on_delete_derived is None:
            return
        report = on_delete_derived((knowledge_id,))
        if report is not None:
            load_report(report)
        else:
            state.setText(
                "Derived entry deleted. Source evidence was preserved; load a new "
                "lifecycle report to continue."
            )

    auto_button.clicked.connect(
        lambda: apply_selection(ProjectKnowledgeSelection.AUTO)
    )
    include_button.clicked.connect(
        lambda: apply_selection(ProjectKnowledgeSelection.INCLUDE)
    )
    exclude_button.clicked.connect(
        lambda: apply_selection(ProjectKnowledgeSelection.EXCLUDE)
    )
    refresh_button.clicked.connect(refresh)
    delete_button.clicked.connect(delete_derived)

    widget._project_knowledge_load_lifecycle = load_report
    widget._project_knowledge_selected_id = _selected_id
    return widget
