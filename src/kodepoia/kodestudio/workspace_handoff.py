from __future__ import annotations

from kodepoia.orchestrator.handoff import WorkspaceContextHandoff


def create_workspace_handoff_inspector(
    handoff: WorkspaceContextHandoff | None,
    *,
    locale: str = "en",
):
    """Create the V2.5.2 read-only cross-workspace handoff inspector."""

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
    widget.setObjectName("workspaceHandoffInspector")
    layout = QVBoxLayout(widget)

    title = QLabel(f"<b>{ui('Transfert de contexte inter-projets', 'Cross-workspace context handoff')}</b>")
    title.setObjectName("workspaceHandoffTitle")
    layout.addWidget(title)

    state = QLabel()
    state.setObjectName("workspaceHandoffState")
    state.setWordWrap(True)
    layout.addWidget(state)

    table = QTableWidget(0, 6)
    table.setObjectName("workspaceHandoffSourcesTable")
    table.setHorizontalHeaderLabels(
        [
            ui("Source", "Source"),
            ui("Confiance", "Trust"),
            ui("Fraîcheur", "Freshness"),
            ui("Version", "Version"),
            ui("Citations", "Citations"),
            ui("Contenu", "Content"),
        ]
    )
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(table)

    if handoff is None:
        state.setText(ui("Aucun transfert chargé.", "No handoff loaded."))
    else:
        table.setRowCount(len(handoff.sources))
        for row, source in enumerate(handoff.sources):
            values = (
                f"{source.source_kind}: {source.locator}",
                source.trust_class,
                source.freshness,
                source.version or "none",
                ", ".join(source.citation_ids) or "none",
                source.content_sha256[:16],
            )
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
        integrity = ui("valide", "valid") if handoff.verify_integrity() else ui("INVALIDE", "INVALID")
        state.setText(
            ui(
                f"{handoff.source_workspace_id[:12]} → {handoff.destination_workspace_id[:12]} | "
                f"autorité={handoff.authority} | intégrité={integrity} | "
                f"inclus={len(handoff.included_content_sha256s)} exclus={len(handoff.excluded_content_sha256s)}",
                f"{handoff.source_workspace_id[:12]} → {handoff.destination_workspace_id[:12]} | "
                f"authority={handoff.authority} | integrity={integrity} | "
                f"included={len(handoff.included_content_sha256s)} excluded={len(handoff.excluded_content_sha256s)}",
            )
        )

    widget._kodepoia_handoff = handoff
    return widget


__all__ = ["create_workspace_handoff_inspector"]
