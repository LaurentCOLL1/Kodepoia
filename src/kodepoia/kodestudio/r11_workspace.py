from __future__ import annotations

import json

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.media.workspace import R11WorkspaceService


def create_r11_workspace_page(
    *,
    translator,
    service: R11WorkspaceService | None = None,
    status_bar=None,
    kill_switch: KillSwitch | None = None,
):
    from PySide6.QtWidgets import (
        QGroupBox,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    media_service = service or R11WorkspaceService()
    switch = kill_switch or GLOBAL_KILL_SWITCH
    page = QWidget()
    page.setObjectName("r11WorkspacePage")
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(f"<h2>{translator.text('r11.title')}</h2>"))
    layout.addWidget(QLabel(translator.text("r11.description")))

    tabs = QTabWidget()
    mark_accessible(
        tabs,
        object_name="r11WorkspaceTabs",
        name=translator.text("r11.tabs.name"),
        description=translator.text("r11.tabs.description"),
        description_required=True,
    )

    tab_specs = (
        ("audio", translator.text("r11.tab.audio"), ("audio", "cues")),
        ("voice", translator.text("r11.tab.voice"), ("voice", "synthesis", "alignment", "facial")),
        ("cinematics", translator.text("r11.tab.cinematics"), ("cinematics",)),
        ("franchise", translator.text("r11.tab.franchise"), ("continuity", "franchise", "canon")),
        ("persistence", translator.text("r11.tab.persistence"), ("savebridge",)),
    )

    tables: dict[str, QTableWidget] = {}
    details: dict[str, QPlainTextEdit] = {}

    def build_tab(tab_id: str, groups: tuple[str, ...]) -> QWidget:
        container = QWidget()
        tab_layout = QVBoxLayout(container)
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(
            [
                translator.text("r11.column.capability"),
                translator.text("r11.column.state"),
                translator.text("r11.column.runtime"),
                translator.text("r11.column.subdivision"),
                translator.text("r11.column.blockers"),
            ]
        )
        mark_accessible(
            table,
            object_name=f"r11_{tab_id}_table",
            name=translator.text("r11.table.name", tab=tab_id),
            description=translator.text("r11.table.description"),
            description_required=True,
        )
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.horizontalHeader().setStretchLastSection(True)
        tables[tab_id] = table
        tab_layout.addWidget(table)

        evidence_group = QGroupBox(translator.text("r11.evidence.title"))
        evidence_layout = QVBoxLayout(evidence_group)
        evidence = QPlainTextEdit()
        evidence.setReadOnly(True)
        mark_accessible(
            evidence,
            object_name=f"r11_{tab_id}_evidence",
            name=translator.text("r11.evidence.name", tab=tab_id),
            description=translator.text("r11.evidence.description"),
            description_required=True,
        )
        details[tab_id] = evidence
        evidence_layout.addWidget(evidence)
        tab_layout.addWidget(evidence_group)
        container.setProperty("r11Groups", groups)
        return container

    for tab_id, title, groups in tab_specs:
        tabs.addTab(build_tab(tab_id, groups), title)
    layout.addWidget(tabs)

    refresh = QPushButton(translator.text("r11.refresh"))
    mark_accessible(
        refresh,
        object_name="r11RefreshButton",
        name=translator.text("r11.refresh"),
        description=translator.text("r11.refresh.description"),
        description_required=True,
    )
    cancel = QPushButton(translator.text("r11.cancel"))
    mark_accessible(
        cancel,
        object_name="r11CancelButton",
        name=translator.text("r11.cancel"),
        description=translator.text("r11.cancel.description"),
        description_required=True,
    )
    layout.addWidget(refresh)
    layout.addWidget(cancel)

    state_label = QLabel(translator.text("r11.operation.idle"))
    state_label.setObjectName("r11OperationState")
    state_label.setAccessibleName(translator.text("r11.operation.idle"))
    layout.addWidget(state_label)

    def refresh_status() -> None:
        for tab_id, _title, groups in tab_specs:
            table = tables[tab_id]
            table.setRowCount(len(groups))
            evidence_rows: list[dict[str, object]] = []
            for row, group in enumerate(groups):
                item = media_service.capability(group)
                values = (
                    item.title,
                    item.state.value,
                    item.runtime_state.value,
                    item.subdivision,
                    "; ".join(item.blockers) if item.blockers else translator.text("r11.blockers.none"),
                )
                for column, value in enumerate(values):
                    table.setItem(row, column, QTableWidgetItem(value))
                evidence_rows.append(
                    {
                        "group": group,
                        "accepted_evidence": list(item.accepted_evidence),
                        "blockers": list(item.blockers),
                        "operations": list(item.operations),
                    }
                )
            details[tab_id].setPlainText(json.dumps(evidence_rows, ensure_ascii=False, indent=2, sort_keys=True))
            table.resizeColumnsToContents()
        text = translator.text("r11.operation.ready")
        state_label.setText(text)
        state_label.setAccessibleName(text)
        if status_bar is not None:
            status_bar.showMessage(text)

    def cancel_operations() -> None:
        stopped = switch.trigger()
        text = translator.text("r11.operation.cancelled", count=stopped)
        state_label.setText(text)
        state_label.setAccessibleName(text)
        if status_bar is not None:
            status_bar.showMessage(text)

    refresh.clicked.connect(refresh_status)
    cancel.clicked.connect(cancel_operations)
    refresh_status()
    page._r11_service = media_service
    page._r11_kill_switch = switch
    return page


__all__ = ["create_r11_workspace_page"]
