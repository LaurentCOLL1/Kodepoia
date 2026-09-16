from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from kodepoia.capability_truth import build_capability_matrix
from kodepoia.intelligence.research.contracts import ResearchSourceKind
from kodepoia.intelligence.research.service import (
    ResearchCancellation,
    ResearchFetchRequest,
    ResearchService,
    ResearchServiceResult,
)
from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.localization import KodeStudioTranslator
from kodepoia.kodestudio.research_ux import (
    ResearchUxTranslator,
    default_empty_state_text,
    discovery_state_text,
    error_text,
    fetch_status_text,
    provider_summary_text,
    saved_search_status_text,
)


def research_capability_rows(
    *,
    allow_network: bool = False,
    github_authenticated: bool = False,
) -> tuple[dict[str, Any], ...]:
    """Return the canonical V2 research capability rows consumed by KodeStudio."""

    return tuple(
        row
        for row in build_capability_matrix(
            allow_network=allow_network,
            github_authenticated=github_authenticated,
        )
        if row["capability_id"].startswith("research.")
    )


def research_capability_diagnostics_text(
    *,
    allow_network: bool = False,
    github_authenticated: bool = False,
) -> str:
    """Render actionable diagnostics without turning provider failure into zero results."""

    lines = ["Capability truth (V2):"]
    for row in research_capability_rows(
        allow_network=allow_network,
        github_authenticated=github_authenticated,
    ):
        classes = ", ".join(row["classifications"])
        lines.append(
            f"{row['capability_id']}: {row['runtime_state'].upper()} | "
            f"network={row['network_state']} | auth={row['authentication_state']} | "
            f"classes={classes} — {row['details']} Action: {row['action']}"
        )
    return "\n".join(lines)


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
    ux = ResearchUxTranslator(locale=translator.locale)
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

    query_scope = QLabel(ux.text("research_ux.saved.description"))
    query_scope.setObjectName("researchQueryScope")
    query_scope.setAccessibleName(ux.text("research_ux.saved.name"))
    query_scope.setWordWrap(True)
    layout.addWidget(query_scope)

    query_row = QHBoxLayout()
    query = mark_accessible(
        QLineEdit(),
        object_name="researchQuery",
        name=tr.text("research.query.name"),
        description=ux.text("research_ux.saved.description"),
        description_required=True,
    )
    query.setPlaceholderText(ux.text("research_ux.saved.placeholder"))
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
        QPushButton(ux.text("research_ux.saved.button")),
        object_name="researchSearchButton",
        name=ux.text("research_ux.saved.name"),
        description=ux.text("research_ux.saved.description"),
        description_required=True,
    )
    query_row.addWidget(query, 1)
    query_row.addWidget(source_filter)
    query_row.addWidget(search_button)
    layout.addLayout(query_row)

    discovery_row = QHBoxLayout()
    discovery_button = mark_accessible(
        QPushButton(ux.text("research_ux.discovery.button")),
        object_name="researchDiscoveryButton",
        name=ux.text("research_ux.discovery.name"),
        description=ux.text("research_ux.discovery.description"),
        description_required=True,
    )
    # V2.1.1 deliberately exposes discovery as unavailable instead of wiring a fake no-op.
    # V2.1.2 is the first subdivision allowed to enable this control with real providers.
    discovery_button.setEnabled(False)
    discovery_state = QLabel("")
    discovery_state.setObjectName("researchDiscoveryState")
    discovery_state.setAccessibleName(ux.text("research_ux.discovery.name"))
    discovery_state.setWordWrap(True)
    discovery_row.addWidget(discovery_button)
    discovery_row.addWidget(discovery_state, 1)
    layout.addLayout(discovery_row)

    provider_summary = QLabel("")
    provider_summary.setObjectName("researchProviderSummary")
    provider_summary.setAccessibleName(ux.text("research_ux.diagnostics.title"))
    provider_summary.setWordWrap(True)
    layout.addWidget(provider_summary)

    empty_state = QLabel("")
    empty_state.setObjectName("researchEmptyState")
    empty_state.setAccessibleName(tr.text("research.results.name"))
    empty_state.setWordWrap(True)
    layout.addWidget(empty_state)

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
    allow_network.setChecked(bool(research.allow_network))
    fetch_button = mark_accessible(
        QPushButton(ux.text("research_ux.fetch.button")),
        object_name="researchFetchButton",
        name=ux.text("research_ux.fetch.name"),
        description=ux.text("research_ux.fetch.description"),
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

    diagnostics_title = QLabel(ux.text("research_ux.diagnostics.title"))
    diagnostics_title.setObjectName("researchDiagnosticsLabel")
    layout.addWidget(diagnostics_title)

    diagnostics = mark_accessible(
        QPlainTextEdit(),
        object_name="researchCapabilityDiagnostics",
        name=tr.text("research.status.name"),
        description=tr.text("research.refresh_status.description"),
        description_required=True,
    )
    diagnostics.setReadOnly(True)
    diagnostics.setMaximumHeight(150)
    layout.addWidget(diagnostics)

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

    technical_label = QLabel(ux.text("research_ux.technical.title"))
    technical_label.setObjectName("researchTechnicalDetailsLabel")
    layout.addWidget(technical_label)

    details = mark_accessible(
        QPlainTextEdit(),
        object_name="researchDetails",
        name=tr.text("research.details.name"),
        description=tr.text("research.details.description"),
        description_required=True,
    )
    details.setReadOnly(True)
    details.setMaximumHeight(160)
    layout.addWidget(details)

    page._research_service = research
    page._research_result = None
    page._research_cancellation = None
    page._research_tasks = []
    page._research_report_count = 0
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

    def current_status_metadata() -> dict[str, Any]:
        try:
            return dict(research.status().metadata)
        except Exception:
            return {}

    def refresh_report_count() -> int:
        metadata = current_status_metadata()
        value = metadata.get("reports", 0)
        try:
            page._research_report_count = max(0, int(value))
        except (TypeError, ValueError):
            page._research_report_count = 0
        return page._research_report_count

    def refresh_human_state(*, reset_empty: bool = False) -> None:
        network = bool(allow_network.isChecked())
        discovery_state.setText(
            discovery_state_text(
                ux,
                allow_network=network,
                github_authenticated=False,
            )
        )
        provider_summary.setText(
            provider_summary_text(
                ux,
                allow_network=network,
                github_authenticated=False,
            )
        )
        if reset_empty or page._research_result is None:
            empty_state.setText(
                default_empty_state_text(
                    ux,
                    report_count=refresh_report_count(),
                    allow_network=network,
                    github_authenticated=False,
                )
            )
            empty_state.setVisible(True)

    def refresh_capability_diagnostics() -> None:
        diagnostics.setPlainText(
            research_capability_diagnostics_text(
                allow_network=bool(allow_network.isChecked()),
                github_authenticated=False,
            )
        )
        refresh_human_state()

    def set_busy(value: bool) -> None:
        search_button.setEnabled(not value)
        fetch_button.setEnabled(not value)
        refresh_button.setEnabled(not value)
        discovery_button.setEnabled(False)
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

        if result.operation == "query":
            status_text = saved_search_status_text(
                ux,
                status=result.status.value,
                count=len(result.items),
            )
            if not result.items:
                empty_state.setText(ux.text("research_ux.empty.no_saved_matches"))
                empty_state.setVisible(True)
            else:
                empty_state.setVisible(False)
        elif result.operation == "fetch":
            status_text = fetch_status_text(
                ux,
                status=result.status.value,
                count=len(result.items),
                reason=result.reason,
            )
            if not result.items:
                empty_state.setText(status_text)
                empty_state.setVisible(True)
            else:
                empty_state.setVisible(False)
        else:
            status_text = tr.text(
                "research.status.result",
                operation=result.operation,
                status=result.status.value.upper(),
                count=len(result.items),
                reason=result.reason or "—",
            )

        capability.setText(status_text)
        diagnostics.setPlainText(
            research_capability_diagnostics_text(
                allow_network=bool(allow_network.isChecked()),
                github_authenticated=False,
            )
        )
        refresh_human_state(reset_empty=False)
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
        human = error_text(ux, message)
        capability.setText(human)
        empty_state.setText(human)
        empty_state.setVisible(True)
        diagnostics.setPlainText(
            research_capability_diagnostics_text(
                allow_network=bool(allow_network.isChecked()),
                github_authenticated=False,
            )
        )
        refresh_human_state(reset_empty=False)
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
        refresh_capability_diagnostics()
        request = ResearchFetchRequest(kind=kind, locator=locator.text())
        run_async(lambda token: research.fetch(request, cancellation=token))

    def cancel() -> None:
        token = page._research_cancellation
        if token is not None:
            token.cancel()
            capability.setText(tr.text("research.status.cancelling"))
            cancel_button.setEnabled(False)

    def refresh_status() -> None:
        refresh_report_count()
        refresh_capability_diagnostics()
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
    allow_network.toggled.connect(lambda _checked: refresh_capability_diagnostics())

    refresh_report_count()
    refresh_capability_diagnostics()
    page._research_run_search = run_search
    page._research_run_fetch = run_fetch
    page._research_cancel_active = cancel
    page._research_render = render
    page._research_set_busy = set_busy
    page._research_refresh_capability_diagnostics = refresh_capability_diagnostics
    page._research_refresh_human_state = refresh_human_state
    return page
