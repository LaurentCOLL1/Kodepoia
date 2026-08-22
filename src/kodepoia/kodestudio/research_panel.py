from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from kodepoia.intelligence.research.contracts import ResearchSourceKind
from kodepoia.intelligence.research.service import (
    ResearchCancellation,
    ResearchFetchRequest,
    ResearchService,
    ResearchServiceResult,
)
from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.localization import KodeStudioTranslator


def create_research_page(
    project_root: Path,
    *,
    translator: KodeStudioTranslator,
    service: ResearchService | None = None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    tr = translator
    research = service or ResearchService(project_root)
    page = QWidget()
    page.setObjectName("researchPage")
    page.setAccessibleName(tr.text("research.title"))
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(f"<h2>{tr.text('research.title')}</h2>"))

    description = QLabel(tr.text("research.description"))
    description.setWordWrap(True)
    description.setObjectName("researchDescription")
    layout.addWidget(description)

    query_row = QHBoxLayout()
    query = mark_accessible(
        QLineEdit(),
        object_name="researchQuery",
        name=tr.text("research.query.name"),
        description=tr.text("research.query.description"),
        description_required=True,
    )
    query.setPlaceholderText(tr.text("research.query.placeholder"))
    source_filter = mark_accessible(
        QComboBox(),
        object_name="researchSourceFilter",
        name=tr.text("research.source_filter.name"),
        description=tr.text("research.source_filter.description"),
        description_required=True,
    )
    source_filter.addItem(tr.text("research.source.all"), "")
    for kind in ResearchSourceKind:
        source_filter.addItem(kind.value, kind.value)
    search_button = mark_accessible(
        QPushButton(tr.text("research.search")),
        object_name="researchSearchButton",
        name=tr.text("research.search"),
        description=tr.text("research.search.description"),
        description_required=True,
    )
    query_row.addWidget(query, 1)
    query_row.addWidget(source_filter)
    query_row.addWidget(search_button)
    layout.addLayout(query_row)

    fetch_form = QFormLayout()
    fetch_kind = mark_accessible(
        QComboBox(),
        object_name="researchFetchKind",
        name=tr.text("research.fetch_kind.name"),
        description=tr.text("research.fetch_kind.description"),
        description_required=True,
    )
    for kind in (
        ResearchSourceKind.LOCAL,
        ResearchSourceKind.OFFICIAL_DOCS,
        ResearchSourceKind.WEB,
    ):
        fetch_kind.addItem(kind.value, kind.value)
    locator = mark_accessible(
        QLineEdit(),
        object_name="researchLocator",
        name=tr.text("research.locator.name"),
        description=tr.text("research.locator.description"),
        description_required=True,
    )
    locator.setPlaceholderText(tr.text("research.locator.placeholder"))
    allow_network = mark_accessible(
        QCheckBox(tr.text("research.allow_network")),
        object_name="researchAllowNetwork",
        name=tr.text("research.allow_network"),
        description=tr.text("research.allow_network.description"),
        description_required=True,
    )
    fetch_button = mark_accessible(
        QPushButton(tr.text("research.fetch")),
        object_name="researchFetchButton",
        name=tr.text("research.fetch"),
        description=tr.text("research.fetch.description"),
        description_required=True,
    )
    fetch_form.addRow(tr.text("research.fetch_kind.label"), fetch_kind)
    fetch_form.addRow(tr.text("research.locator.label"), locator)
    fetch_form.addRow("", allow_network)
    fetch_form.addRow("", fetch_button)
    layout.addLayout(fetch_form)

    action_row = QHBoxLayout()
    cancel_button = mark_accessible(
        QPushButton(tr.text("research.cancel")),
        object_name="researchCancelButton",
        name=tr.text("research.cancel"),
        description=tr.text("research.cancel.description"),
        description_required=True,
    )
    cancel_button.setEnabled(False)
    refresh_button = mark_accessible(
        QPushButton(tr.text("research.refresh_status")),
        object_name="researchRefreshStatusButton",
        name=tr.text("research.refresh_status"),
        description=tr.text("research.refresh_status.description"),
        description_required=True,
    )
    copy_button = mark_accessible(
        QPushButton(tr.text("research.copy")),
        object_name="researchCopyButton",
        name=tr.text("research.copy"),
        description=tr.text("research.copy.description"),
        description_required=True,
    )
    export_button = mark_accessible(
        QPushButton(tr.text("research.export")),
        object_name="researchExportButton",
        name=tr.text("research.export"),
        description=tr.text("research.export.description"),
        description_required=True,
    )
    copy_button.setEnabled(False)
    export_button.setEnabled(False)
    action_row.addWidget(cancel_button)
    action_row.addWidget(refresh_button)
    action_row.addStretch(1)
    action_row.addWidget(copy_button)
    action_row.addWidget(export_button)
    layout.addLayout(action_row)

    capability = QLabel(tr.text("research.status.idle"))
    capability.setObjectName("researchCapabilityStatus")
    capability.setAccessibleName(tr.text("research.status.name"))
    capability.setWordWrap(True)
    layout.addWidget(capability)

    warning = QLabel("")
    warning.setObjectName("researchSuspiciousWarning")
    warning.setAccessibleName(tr.text("research.warning.name"))
    warning.setWordWrap(True)
    warning.setVisible(False)
    layout.addWidget(warning)

    results = mark_accessible(
        QTableWidget(0, 7),
        object_name="researchResultsTable",
        name=tr.text("research.results.name"),
        description=tr.text("research.results.description"),
        description_required=True,
    )
    results.setHorizontalHeaderLabels(
        [
            tr.text("research.column.source"),
            tr.text("research.column.status"),
            tr.text("research.column.freshness"),
            tr.text("research.column.version"),
            tr.text("research.column.trust"),
            tr.text("research.column.suspicious"),
            tr.text("research.column.title"),
        ]
    )
    results.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    results.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(results, 2)

    details = mark_accessible(
        QPlainTextEdit(),
        object_name="researchDetails",
        name=tr.text("research.details.name"),
        description=tr.text("research.details.description"),
        description_required=True,
    )
    details.setReadOnly(True)
    layout.addWidget(details, 1)

    page._research_service = research
    page._research_result = None
    page._research_cancellation = None
    page._research_tasks = []
    pool = QThreadPool.globalInstance()

    class TaskSignals(QObject):
        result = Signal(object)
        error = Signal(str)
        finished = Signal()

    class Task(QRunnable):
        def __init__(self, operation: Callable[[], ResearchServiceResult]) -> None:
            super().__init__()
            self.operation = operation
            self.signals = TaskSignals()

        def run(self) -> None:
            try:
                self.signals.result.emit(self.operation())
            except Exception as exc:  # display boundary; domain errors remain plain text
                self.signals.error.emit(str(exc))
            finally:
                self.signals.finished.emit()

    def set_busy(value: bool) -> None:
        search_button.setEnabled(not value)
        fetch_button.setEnabled(not value)
        refresh_button.setEnabled(not value)
        cancel_button.setEnabled(value)

    def render(result: ResearchServiceResult) -> None:
        page._research_result = result
        results.setRowCount(len(result.items))
        for row, item in enumerate(result.items):
            values = (
                item.source_kind,
                item.status.value.upper(),
                item.freshness.upper(),
                item.version or "—",
                item.trust,
                "YES" if item.suspicious else "NO",
                item.title or item.locator or item.text[:80],
            )
            for column, value in enumerate(values):
                results.setItem(row, column, QTableWidgetItem(value))
        payload = research.serialized(result)
        details.setPlainText(payload)
        suspicious = any(item.suspicious for item in result.items)
        warning.setVisible(suspicious)
        warning.setText(tr.text("research.warning.suspicious") if suspicious else "")
        capability.setText(
            tr.text(
                "research.status.result",
                operation=result.operation,
                status=result.status.value.upper(),
                count=len(result.items),
                reason=result.reason or "—",
            )
        )
        copy_button.setEnabled(True)
        export_button.setEnabled(True)
        if result.items:
            results.selectRow(0)
        if status_bar is not None:
            status_bar.showMessage(capability.text())

    def show_error(message: str) -> None:
        page._research_result = None
        results.setRowCount(0)
        details.setPlainText(message)
        warning.setVisible(False)
        capability.setText(tr.text("research.status.error", reason=message))
        copy_button.setEnabled(False)
        export_button.setEnabled(False)

    def finish_task() -> None:
        set_busy(False)
        page._research_cancellation = None
        page._research_tasks = [task for task in page._research_tasks if not task.isAutoDelete()]

    def run_async(operation: Callable[[ResearchCancellation], ResearchServiceResult]) -> None:
        token = ResearchCancellation()
        page._research_cancellation = token
        set_busy(True)
        capability.setText(tr.text("research.status.running"))
        task = Task(lambda: operation(token))
        task.signals.result.connect(render)
        task.signals.error.connect(show_error)
        task.signals.finished.connect(finish_task)
        page._research_tasks.append(task)
        pool.start(task)

    def run_search() -> None:
        source_value = str(source_filter.currentData() or "")
        selected = () if not source_value else (ResearchSourceKind(source_value),)
        run_async(
            lambda token: research.query(
                query.text(),
                source_kinds=selected,
                cancellation=token,
            )
        )

    def run_fetch() -> None:
        kind = ResearchSourceKind(str(fetch_kind.currentData()))
        research.allow_network = bool(allow_network.isChecked())
        request = ResearchFetchRequest(kind=kind, locator=locator.text())
        run_async(lambda token: research.fetch(request, cancellation=token))

    def cancel() -> None:
        token = page._research_cancellation
        if token is not None:
            token.cancel()
            capability.setText(tr.text("research.status.cancelling"))
            cancel_button.setEnabled(False)

    def refresh_status() -> None:
        run_async(lambda _token: research.status())

    def copy_result() -> None:
        current = page._research_result
        if current is None:
            return
        QApplication.clipboard().setText(research.serialized(current))
        capability.setText(tr.text("research.status.copied"))

    def export_result() -> None:
        current = page._research_result
        if current is None:
            return
        destination = research.export(current)
        capability.setText(tr.text("research.status.exported", path=str(destination)))

    def show_selected() -> None:
        current = page._research_result
        row = results.currentRow()
        if current is None or not 0 <= row < len(current.items):
            return
        item = current.items[row]
        details.setPlainText(json.dumps(item.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))

    search_button.clicked.connect(run_search)
    query.returnPressed.connect(run_search)
    fetch_button.clicked.connect(run_fetch)
    cancel_button.clicked.connect(cancel)
    refresh_button.clicked.connect(refresh_status)
    copy_button.clicked.connect(copy_result)
    export_button.clicked.connect(export_result)
    results.itemSelectionChanged.connect(show_selected)

    page._research_run_search = run_search
    page._research_run_fetch = run_fetch
    page._research_cancel_active = cancel
    page._research_render = render
    page._research_set_busy = set_busy
    return page
