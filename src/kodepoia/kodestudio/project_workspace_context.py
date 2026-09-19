from __future__ import annotations

from kodepoia.intelligence.project_workspace import (
    ProjectWorkspaceContextSession,
    ProjectWorkspaceSurface,
)
from kodepoia.kodestudio.accessibility import mark_accessible


def create_project_workspace_context_widget(
    session: ProjectWorkspaceContextSession,
    *,
    surface: ProjectWorkspaceSurface,
    workspace_id: str,
):
    """Read-only V2.2.5 visibility for the governed active project context."""

    from PySide6.QtWidgets import (
        QLabel,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    widget = QWidget()
    widget.setObjectName(f"projectWorkspaceContext_{workspace_id}")
    widget.setAccessibleName("Active Project Knowledge context")
    layout = QVBoxLayout(widget)

    title = QLabel("<h3>Active Project Knowledge context</h3>")
    title.setObjectName(f"projectWorkspaceContextTitle_{workspace_id}")
    layout.addWidget(title)

    state = QLabel("No governed project context is active for this workspace.")
    state.setObjectName(f"projectWorkspaceContextState_{workspace_id}")
    state.setAccessibleName("Active Project Knowledge context state")
    state.setWordWrap(True)
    layout.addWidget(state)

    table = mark_accessible(
        QTableWidget(0, 5),
        object_name=f"projectWorkspaceContextTable_{workspace_id}",
        name="Active Project Knowledge sources",
        description=(
            "Read-only sources entering this workspace through the governed "
            "project context contract."
        ),
        description_required=True,
    )
    table.setHorizontalHeaderLabels(
        ["Source", "Trust", "Freshness", "Version", "Citations"]
    )
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(table)

    refresh = mark_accessible(
        QPushButton("Refresh active context"),
        object_name=f"projectWorkspaceContextRefresh_{workspace_id}",
        name="Refresh active Project Knowledge context",
        description=(
            "Refresh this read-only view from the shared in-memory governed "
            "context session. It does not read unrestricted stores."
        ),
        description_required=True,
    )
    layout.addWidget(refresh)

    def refresh_context():
        context = session.context_for(surface, workspace_id=workspace_id)
        if context is None:
            table.setRowCount(0)
            state.setText("No governed project context is active for this workspace.")
            widget._project_workspace_context = None
            return None

        table.setRowCount(len(context.sources))
        for row, source in enumerate(context.sources):
            values = (
                f"{source.source_kind.value}: {source.locator}",
                source.trust_class,
                source.freshness,
                source.version or "none",
                ", ".join(source.citation_ids) or "none",
            )
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
        state.setText(
            f"{context.project_scope} | {surface.value}:{workspace_id} | "
            f"{len(context.sources)} source(s) | "
            f"snapshot={context.snapshot.digest_sha256[:12]}. "
            "Context is project-scoped data only; selection does not grant authority."
        )
        widget._project_workspace_context = context
        return context

    refresh.clicked.connect(refresh_context)
    widget._project_workspace_refresh = refresh_context
    widget._project_workspace_context = None
    refresh_context()
    return widget


__all__ = ["create_project_workspace_context_widget"]
