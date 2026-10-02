from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from kodepoia.orchestrator.workspaces import WorkspaceRegistry


def create_workspace_inventory_widget(
    roots: Iterable[Path | str],
    *,
    locale: str = "en",
):
    """Create the V2.5.1 read-only selected-workspace inventory."""

    from PySide6.QtWidgets import (
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    french = locale.lower().startswith("fr")

    def ui(fr: str, en: str) -> str:
        return fr if french else en

    widget = QWidget()
    widget.setObjectName("workspaceInventory")
    widget.setAccessibleName(ui("Inventaire des espaces de travail", "Workspace inventory"))
    layout = QVBoxLayout(widget)

    title = QLabel(f"<b>{ui('Espaces de travail sélectionnés', 'Selected workspaces')}</b>")
    title.setObjectName("workspaceInventoryTitle")
    layout.addWidget(title)

    state = QLabel()
    state.setObjectName("workspaceInventoryState")
    state.setWordWrap(True)
    layout.addWidget(state)

    table = QTableWidget(0, 4)
    table.setObjectName("workspaceInventoryTable")
    table.setAccessibleName(ui("Espaces de travail Kodepoia", "Kodepoia workspaces"))
    table.setHorizontalHeaderLabels(
        [
            ui("Projet", "Project"),
            ui("ID espace", "Workspace ID"),
            ui("Portée", "Scope"),
            ui("Racine canonique", "Canonical root"),
        ]
    )
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(table)

    registry = WorkspaceRegistry()
    rejected: list[str] = []
    for root in roots:
        try:
            registry.register(root)
        except (ValueError, OSError) as exc:
            rejected.append(str(exc))

    workspaces = registry.workspaces()
    table.setRowCount(len(workspaces))
    for row, workspace in enumerate(workspaces):
        values = (
            workspace.project_name,
            workspace.workspace_id[:16],
            workspace.project_scope,
            workspace.canonical_root,
        )
        for column, value in enumerate(values):
            table.setItem(row, column, QTableWidgetItem(value))

    if workspaces:
        state.setText(
            ui(
                f"{len(workspaces)} espace(s) valide(s). Inventaire en lecture seule ; "
                "aucune orchestration ou mutation inter-projets n'est autorisée ici.",
                f"{len(workspaces)} valid workspace(s). Read-only inventory; "
                "no cross-project orchestration or mutation is authorized here.",
            )
        )
    else:
        state.setText(
            ui(
                "Aucun autre projet Kodepoia valide sélectionné.",
                "No valid Kodepoia workspace selected.",
            )
        )
    if rejected:
        state.setText(
            state.text()
            + ui(
                f" {len(rejected)} entrée(s) ignorée(s) car invalide(s) ou dupliquée(s).",
                f" {len(rejected)} invalid or duplicate entrie(s) ignored.",
            )
        )

    widget._kodepoia_workspace_registry = registry
    widget._kodepoia_workspace_rejected = tuple(rejected)
    return widget


__all__ = ["create_workspace_inventory_widget"]
