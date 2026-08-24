from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from kodepoia.blender3d.service import BlenderCancellation, BlenderService, BlenderUXResult
from kodepoia.kodestudio.accessibility import mark_accessible


def create_blender_page(
    project_root: Path,
    *,
    locale: str = "en",
    service=None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QComboBox,
        QFormLayout,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    class WorkerSignals(QObject):
        result = Signal(object)
        failed = Signal(str)
        finished = Signal()

    class Worker(QRunnable):
        def __init__(self, operation: Callable[[], Any]) -> None:
            super().__init__()
            self.operation = operation
            self.signals = WorkerSignals()

        def run(self) -> None:
            try:
                result = self.operation()
            except Exception as exc:  # worker boundary: convert failures to UI state
                self.signals.failed.emit(f"{type(exc).__name__}: {exc}")
            else:
                self.signals.result.emit(result)
            finally:
                self.signals.finished.emit()

    from kodepoia.kodestudio.blender_localization import BlenderTranslator

    tr = BlenderTranslator(locale)
    root = Path(project_root).resolve(strict=False)
    facade = service or BlenderService(root)
    page = QWidget()
    page.setObjectName("blenderPage")
    page._kodepoia_blender_service = facade
    page._kodepoia_blender_workers = []
    page._kodepoia_blender_busy = False
    page._kodepoia_blender_cancellation = None
    pool = QThreadPool.globalInstance()

    layout = QVBoxLayout(page)
    title = QLabel(f"<h2>{tr.text('blender.title')}</h2>")
    description = QLabel(tr.text("blender.description"))
    description.setWordWrap(True)
    layout.addWidget(title)
    layout.addWidget(description)

    status_group = QGroupBox(tr.text("blender.status.group"))
    status_grid = QGridLayout(status_group)
    runtime = QLabel(tr.text("blender.status.runtime.unknown"))
    runtime.setObjectName("blenderRuntimeStatus")
    capability = QLabel(tr.text("blender.status.capabilities.unknown"))
    capability.setObjectName("blenderCapabilityStatus")
    operation_state = QLabel(tr.text("blender.operation.idle"))
    operation_state.setObjectName("blenderOperationStatus")
    status_grid.addWidget(runtime, 0, 0)
    status_grid.addWidget(capability, 0, 1)
    status_grid.addWidget(operation_state, 1, 0, 1, 2)
    layout.addWidget(status_group)

    query_group = QGroupBox(tr.text("blender.query.group"))
    form = QFormLayout(query_group)
    kind = QComboBox()
    kind.setObjectName("blenderReportKind")
    for value, label_key in (
        ("inspect", "blender.kind.inspect"),
        ("qa", "blender.kind.qa"),
        ("rig", "blender.kind.rig"),
        ("animation", "blender.kind.animation"),
        ("lod", "blender.kind.lod"),
        ("export", "blender.kind.export"),
    ):
        kind.addItem(tr.text(label_key), value)
    record_id = QLineEdit()
    record_id.setObjectName("blenderRecordId")
    record_id.setPlaceholderText(tr.text("blender.record.placeholder"))
    evidence_id = QComboBox()
    evidence_id.setObjectName("blenderEvidenceId")
    for value in ("r10.2", "r10.6", "r10.7", "r10.10"):
        evidence_id.addItem(value, value)
    form.addRow(tr.text("blender.kind"), kind)
    form.addRow(tr.text("blender.record"), record_id)
    form.addRow(tr.text("blender.evidence"), evidence_id)
    layout.addWidget(query_group)

    actions = QHBoxLayout()
    refresh = QPushButton(tr.text("blender.refresh"))
    refresh.setObjectName("blenderRefreshButton")
    capabilities = QPushButton(tr.text("blender.capabilities"))
    capabilities.setObjectName("blenderCapabilitiesButton")
    load_report = QPushButton(tr.text("blender.load_report"))
    load_report.setObjectName("blenderLoadReportButton")
    validate_geometry = QPushButton(tr.text("blender.validate_geometry"))
    validate_geometry.setObjectName("blenderValidateGeometryButton")
    show_evidence = QPushButton(tr.text("blender.show_evidence"))
    show_evidence.setObjectName("blenderEvidenceButton")
    cancel = QPushButton(tr.text("blender.cancel"))
    cancel.setObjectName("blenderCancelButton")
    for button in (
        refresh,
        capabilities,
        load_report,
        validate_geometry,
        show_evidence,
        cancel,
    ):
        actions.addWidget(button)
    layout.addLayout(actions)

    details = QPlainTextEdit()
    details.setReadOnly(True)
    mark_accessible(
        details,
        object_name="blenderDetailsView",
        name=tr.text("blender.details.name"),
        description=tr.text("blender.details.description"),
        description_required=True,
    )
    layout.addWidget(details, 1)

    for widget, name, description_text in (
        (kind, tr.text("blender.kind"), tr.text("blender.kind.description")),
        (record_id, tr.text("blender.record"), tr.text("blender.record.description")),
        (evidence_id, tr.text("blender.evidence"), tr.text("blender.evidence.description")),
    ):
        mark_accessible(
            widget,
            object_name=widget.objectName(),
            name=name,
            description=description_text,
            description_required=True,
        )

    for widget, name in (
        (refresh, tr.text("blender.refresh")),
        (capabilities, tr.text("blender.capabilities")),
        (load_report, tr.text("blender.load_report")),
        (validate_geometry, tr.text("blender.validate_geometry")),
        (show_evidence, tr.text("blender.show_evidence")),
        (cancel, tr.text("blender.cancel")),
    ):
        mark_accessible(widget, object_name=widget.objectName(), name=name)

    def set_busy(value: bool) -> None:
        page._kodepoia_blender_busy = value
        for button in (refresh, capabilities, load_report, validate_geometry, show_evidence):
            button.setEnabled(not value)
        cancel.setEnabled(value)

    def pretty(value: Any) -> str:
        if isinstance(value, BlenderUXResult):
            value = value.canonical()
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)

    def show_result(value: Any) -> None:
        payload = value.canonical() if isinstance(value, BlenderUXResult) else value
        details.setPlainText(pretty(payload))
        if not isinstance(payload, dict):
            return
        state = str(payload.get("state", "unknown"))
        operation = str(payload.get("operation", "operation"))
        operation_state.setText(tr.text("blender.operation.state", operation=operation, state=state))
        body = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        runtime_evidence = body.get("runtime_evidence") if isinstance(body, dict) else None
        if isinstance(runtime_evidence, dict):
            blender_version = runtime_evidence.get("blender_version") or "unknown"
            godot_version = runtime_evidence.get("godot_version")
            runtime.setText(
                tr.text(
                    "blender.status.runtime",
                    blender=blender_version,
                    godot=godot_version or "n/a",
                )
            )
        caps = body.get("capabilities") if isinstance(body, dict) else None
        if isinstance(caps, dict):
            accepted = sum(1 for item in caps.values() if item == "accepted")
            capability.setText(
                tr.text("blender.status.capabilities", accepted=accepted, total=len(caps))
            )

    def finish_worker(worker: Worker) -> None:
        try:
            page._kodepoia_blender_workers.remove(worker)
        except ValueError:
            pass
        page._kodepoia_blender_cancellation = None
        set_busy(False)

    def run_async(operation: Callable[[BlenderService, BlenderCancellation], BlenderUXResult]) -> None:
        if page._kodepoia_blender_busy:
            return
        cancellation = BlenderCancellation()
        page._kodepoia_blender_cancellation = cancellation
        set_busy(True)
        operation_state.setText(tr.text("blender.operation.running"))
        worker_service = facade.fork() if hasattr(facade, "fork") else facade
        worker = Worker(lambda: operation(worker_service, cancellation))
        page._kodepoia_blender_workers.append(worker)
        worker.signals.result.connect(show_result)
        worker.signals.failed.connect(
            lambda reason: (
                details.setPlainText(reason),
                operation_state.setText(tr.text("blender.operation.error", reason=reason)),
            )
        )
        worker.signals.finished.connect(lambda: finish_worker(worker))
        pool.start(worker)

    def selected_id() -> str:
        return record_id.text().strip()

    def load_selected(worker_service: BlenderService, cancellation: BlenderCancellation) -> BlenderUXResult:
        selected_kind = str(kind.currentData())
        value = selected_id()
        if selected_kind == "inspect":
            return worker_service.inspect("inspect", value, cancellation=cancellation)
        method = getattr(worker_service, selected_kind)
        return method(value, cancellation=cancellation)

    def validate_selected(
        worker_service: BlenderService,
        cancellation: BlenderCancellation,
    ) -> BlenderUXResult:
        return worker_service.validate_geometry(selected_id(), cancellation=cancellation)

    def evidence_selected(
        worker_service: BlenderService,
        cancellation: BlenderCancellation,
    ) -> BlenderUXResult:
        return worker_service.evidence(str(evidence_id.currentData()), cancellation=cancellation)

    def cancel_active() -> None:
        token = page._kodepoia_blender_cancellation
        if token is None:
            return
        token.cancel()
        operation_state.setText(tr.text("blender.operation.cancelling"))
        if status_bar is not None:
            status_bar.showMessage(tr.text("blender.operation.cancelling"))

    refresh.clicked.connect(lambda: run_async(lambda svc, token: svc.status(cancellation=token)))
    capabilities.clicked.connect(
        lambda: run_async(lambda svc, token: svc.capabilities(cancellation=token))
    )
    load_report.clicked.connect(lambda: run_async(load_selected))
    validate_geometry.clicked.connect(lambda: run_async(validate_selected))
    show_evidence.clicked.connect(lambda: run_async(evidence_selected))
    cancel.clicked.connect(cancel_active)

    set_busy(False)
    return page


__all__ = ["create_blender_page"]
