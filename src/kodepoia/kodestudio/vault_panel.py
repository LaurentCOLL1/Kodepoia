from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from kodepoia.assets.contracts import AssetKind, AssetRole, ReuseScope
from kodepoia.assets.search import SearchFilters
from kodepoia.assets.service import AssetCancellationToken, AssetService, jsonable
from kodepoia.kodestudio.accessibility import mark_accessible


def create_vault_page(
    project_root: Path,
    *,
    translator,
    service: AssetService | None = None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
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

    class WorkerSignals(QObject):
        result = Signal(object)
        failed = Signal(str)
        finished = Signal()

    class Worker(QRunnable):
        def __init__(self, action: Callable[[], Any]) -> None:
            super().__init__()
            self.action = action
            self.signals = WorkerSignals()

        def run(self) -> None:
            try:
                value = self.action()
            except Exception as exc:
                self.signals.failed.emit(f"{type(exc).__name__}: {exc}")
            else:
                self.signals.result.emit(value)
            finally:
                self.signals.finished.emit()

    root = project_root.resolve(strict=False)
    asset_service = service or AssetService(root)
    page = QWidget()
    page.setObjectName("vaultPage")
    page._kodepoia_asset_service = asset_service
    page._kodepoia_workers = []
    page._kodepoia_cancel_token = None
    pool = QThreadPool.globalInstance()

    layout = QVBoxLayout(page)
    title = QLabel(f"<h2>{translator.text('vault.title')}</h2>")
    description = QLabel(translator.text("vault.description"))
    description.setWordWrap(True)
    layout.addWidget(title)
    layout.addWidget(description)

    health_row = QHBoxLayout()
    vault_badge = QLabel(translator.text("vault.status.idle"))
    vault_badge.setObjectName("vaultStatusBadge")
    vcs_badge = QLabel("VCS: UNKNOWN")
    vcs_badge.setObjectName("vaultVcsBadge")
    lfs_badge = QLabel("LFS: UNKNOWN")
    lfs_badge.setObjectName("vaultLfsBadge")
    health_row.addWidget(vault_badge)
    health_row.addWidget(vcs_badge)
    health_row.addWidget(lfs_badge)
    health_row.addStretch(1)
    layout.addLayout(health_row)

    controls = QHBoxLayout()
    query = QLineEdit()
    mark_accessible(
        query,
        object_name="vaultSearchInput",
        name=translator.text("vault.search.name"),
        description=translator.text("vault.search.description"),
        description_required=True,
    )
    query.setPlaceholderText(translator.text("vault.search.placeholder"))

    kind = QComboBox()
    kind.setObjectName("vaultKindFilter")
    kind.addItem(translator.text("vault.filter.all_kinds"), None)
    for item in AssetKind:
        kind.addItem(item.value, item.value)

    role = QComboBox()
    role.setObjectName("vaultRoleFilter")
    role.addItem(translator.text("vault.filter.all_roles"), None)
    for item in AssetRole:
        role.addItem(item.value, item.value)

    reuse = QComboBox()
    reuse.setObjectName("vaultReuseFilter")
    reuse.addItem(translator.text("vault.filter.all_reuse"), None)
    for item in ReuseScope:
        reuse.addItem(item.value, item.value)

    include_blocked = QCheckBox(translator.text("vault.filter.include_blocked"))
    include_blocked.setObjectName("vaultIncludeBlocked")

    search_button = QPushButton(translator.text("vault.search"))
    search_button.setObjectName("vaultSearchButton")
    refresh_button = QPushButton(translator.text("vault.refresh"))
    refresh_button.setObjectName("vaultRefreshButton")
    duplicate_button = QPushButton(translator.text("vault.duplicates"))
    duplicate_button.setObjectName("vaultDuplicatesButton")
    rebuild_button = QPushButton(translator.text("vault.rebuild"))
    rebuild_button.setObjectName("vaultRebuildButton")
    cancel_button = QPushButton(translator.text("vault.cancel"))
    cancel_button.setObjectName("vaultCancelButton")
    cancel_button.setEnabled(False)

    for widget in (query, kind, role, reuse, include_blocked, search_button, refresh_button, duplicate_button, rebuild_button, cancel_button):
        controls.addWidget(widget)
    layout.addLayout(controls)

    table = QTableWidget(0, 8)
    table.setObjectName("vaultAssetTable")
    table.setHorizontalHeaderLabels(
        [
            translator.text("vault.column.name"),
            translator.text("vault.column.kind"),
            translator.text("vault.column.role"),
            translator.text("vault.column.status"),
            translator.text("vault.column.license"),
            translator.text("vault.column.reuse"),
            translator.text("vault.column.revision"),
            translator.text("vault.column.score"),
        ]
    )
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    mark_accessible(
        table,
        object_name="vaultAssetTable",
        name=translator.text("vault.results.name"),
        description=translator.text("vault.results.description"),
        description_required=True,
    )
    layout.addWidget(table, 2)

    warning = QLabel("")
    warning.setObjectName("vaultLicenseWarning")
    warning.setWordWrap(True)
    layout.addWidget(warning)

    details = QPlainTextEdit()
    details.setReadOnly(True)
    mark_accessible(
        details,
        object_name="vaultAssetDetails",
        name=translator.text("vault.details.name"),
        description=translator.text("vault.details.description"),
        description_required=True,
    )
    layout.addWidget(details, 1)

    operation = QLabel(translator.text("vault.operation.idle"))
    operation.setObjectName("vaultOperationStatus")
    layout.addWidget(operation)

    def set_status(text: str) -> None:
        operation.setText(text)
        if status_bar is not None:
            status_bar.showMessage(text)

    def finish_worker(worker) -> None:
        cancel_button.setEnabled(False)
        if worker in page._kodepoia_workers:
            page._kodepoia_workers.remove(worker)
        page._kodepoia_cancel_token = None

    def start_worker(action: Callable[[AssetService, AssetCancellationToken], Any], on_result: Callable[[Any], None]) -> None:
        token = AssetCancellationToken()
        page._kodepoia_cancel_token = token
        cancel_button.setEnabled(True)
        set_status(translator.text("vault.operation.running"))

        def isolated() -> Any:
            token.require_active()
            worker_service = asset_service.fork()
            try:
                return action(worker_service, token)
            finally:
                worker_service.close()

        worker = Worker(isolated)
        page._kodepoia_workers.append(worker)

        def failed(reason: str) -> None:
            set_status(translator.text("vault.operation.error", reason=reason))

        def result(value: Any) -> None:
            on_result(value)
            set_status(translator.text("vault.operation.ready"))

        worker.signals.result.connect(result)
        worker.signals.failed.connect(failed)
        worker.signals.finished.connect(lambda: finish_worker(worker))
        pool.start(worker)

    def fill_rows(items: Any) -> None:
        rows = []
        for item in items:
            if hasattr(item, "summary") and hasattr(item, "score"):
                summary = item.summary
                score = f"{float(item.score):.4f}"
            else:
                summary = item
                score = ""
            rows.append((summary, score))
        table.setRowCount(len(rows))
        for row_index, (summary, score) in enumerate(rows):
            values = (
                summary.display_name,
                summary.kind,
                summary.role or "",
                summary.status or "",
                f"{summary.license_state} / {summary.license_token}",
                summary.reuse_scope or "",
                summary.revision_id or "",
                score,
            )
            for column, value in enumerate(values):
                table.setItem(row_index, column, QTableWidgetItem(str(value)))
        table.resizeColumnsToContents()

    def apply_status(payload: dict[str, Any]) -> None:
        vault = payload.get("vault", {})
        vcs = payload.get("vcs", {})
        lfs = payload.get("lfs", {})
        vault_badge.setText(
            f"Vault: {payload.get('state', 'unknown').upper()} — {vault.get('assets', 0)} assets / {vault.get('revisions', 0)} revisions"
        )
        vcs_badge.setText(f"VCS: {str(vcs.get('state', 'unknown')).upper()}")
        lfs_badge.setText(f"LFS: {str(lfs.get('state', 'unknown')).upper()}")

    def refresh() -> None:
        def action(worker_service: AssetService, token: AssetCancellationToken):
            token.require_active()
            return {"status": worker_service.status(), "assets": worker_service.list_assets()}

        def done(payload: dict[str, Any]) -> None:
            apply_status(payload["status"])
            fill_rows(payload["assets"])

        start_worker(action, done)

    def run_search() -> None:
        text = query.text().strip()
        if not text:
            refresh()
            return
        filters = SearchFilters(
            kind=AssetKind(str(kind.currentData())) if kind.currentData() else None,
            role=AssetRole(str(role.currentData())) if role.currentData() else None,
            reuse_scope=ReuseScope(str(reuse.currentData())) if reuse.currentData() else None,
            include_blocked=include_blocked.isChecked(),
        )
        start_worker(
            lambda worker_service, token: worker_service.search(text, filters=filters, token=token),
            fill_rows,
        )

    def run_duplicates() -> None:
        start_worker(
            lambda worker_service, token: worker_service.duplicate_candidates(token=token),
            lambda payload: details.setPlainText(json.dumps(jsonable(payload), ensure_ascii=False, indent=2, sort_keys=True)),
        )

    def run_rebuild() -> None:
        start_worker(
            lambda worker_service, token: worker_service.rebuild(token=token),
            lambda payload: details.setPlainText(json.dumps(jsonable(payload), ensure_ascii=False, indent=2, sort_keys=True)),
        )

    def cancel() -> None:
        token = page._kodepoia_cancel_token
        if token is not None:
            token.cancel()
            set_status(translator.text("vault.operation.cancelling"))

    def select_row() -> None:
        row = table.currentRow()
        if row < 0:
            return
        revision_item = table.item(row, 6)
        if revision_item is None or not revision_item.text():
            return
        revision_id = revision_item.text()
        try:
            detail = asset_service.show(revision_id)
        except Exception as exc:
            details.setPlainText(f"{type(exc).__name__}: {exc}")
            return
        payload = jsonable(detail)
        details.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        if detail.summary.license_state in {"unknown", "block"}:
            warning.setText(translator.text("vault.license.warning", state=detail.summary.license_state))
        else:
            warning.setText("")

        def repository_done(evidence: Any) -> None:
            current = json.loads(details.toPlainText())
            current["repository_evidence"] = jsonable(evidence)
            details.setPlainText(json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True))

        start_worker(
            lambda worker_service, token: worker_service.repository_evidence(revision_id),
            repository_done,
        )

    search_button.clicked.connect(run_search)
    query.returnPressed.connect(run_search)
    refresh_button.clicked.connect(refresh)
    duplicate_button.clicked.connect(run_duplicates)
    rebuild_button.clicked.connect(run_rebuild)
    cancel_button.clicked.connect(cancel)
    table.itemSelectionChanged.connect(select_row)

    return page
