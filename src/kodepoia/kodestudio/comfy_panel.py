from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from kodepoia.kodestudio.accessibility import mark_accessible


def create_comfy_page(
    project_root: Path,
    *,
    translator,
    service=None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    if service is None:
        from kodepoia.comfyui.service import ComfyService

        service = ComfyService(project_root)

    class WorkerSignals(QObject):
        result = Signal(object)
        error = Signal(str)
        finished = Signal()

    class Worker(QRunnable):
        def __init__(self, action: Callable[[], Any]) -> None:
            super().__init__()
            self.action = action
            self.signals = WorkerSignals()

        def run(self) -> None:
            try:
                self.signals.result.emit(self.action())
            except Exception as exc:  # UI boundary: display typed service failure, never infer success.
                self.signals.error.emit(str(exc))
            finally:
                self.signals.finished.emit()

    tr = translator
    page = QWidget()
    page.setObjectName("comfyPage")
    page.setAccessibleName(tr.text("comfy.title"))
    page._kodepoia_comfy_service = service
    page._kodepoia_workers = []
    page._kodepoia_current_run_id = None
    pool = QThreadPool.globalInstance()

    root_layout = QVBoxLayout(page)
    title = QLabel(f"<h2>{tr.text('comfy.title')}</h2>")
    description = QLabel(tr.text("comfy.description"))
    description.setWordWrap(True)
    root_layout.addWidget(title)
    root_layout.addWidget(description)

    service_group = QGroupBox(tr.text("comfy.service.group"))
    service_layout = QGridLayout(service_group)
    service_status = QLabel(tr.text("comfy.status.idle"))
    service_status.setObjectName("comfyServiceStatus")
    capability_status = QLabel(tr.text("comfy.capability.unknown"))
    capability_status.setObjectName("comfyCapabilityStatus")
    vram_status = QLabel(tr.text("comfy.vram.unknown"))
    vram_status.setObjectName("comfyVramStatus")
    warning = QLabel("")
    warning.setObjectName("comfyWarning")
    warning.setWordWrap(True)
    refresh = QPushButton(tr.text("comfy.refresh"))
    mark_accessible(
        refresh,
        object_name="comfyRefreshButton",
        name=tr.text("comfy.refresh"),
        description=tr.text("comfy.refresh.description"),
        description_required=True,
    )
    service_layout.addWidget(service_status, 0, 0, 1, 2)
    service_layout.addWidget(capability_status, 1, 0)
    service_layout.addWidget(vram_status, 1, 1)
    service_layout.addWidget(warning, 2, 0, 1, 2)
    service_layout.addWidget(refresh, 3, 0, 1, 2)
    root_layout.addWidget(service_group)

    workflow_group = QGroupBox(tr.text("comfy.workflow.group"))
    workflow_layout = QFormLayout(workflow_group)
    family = QComboBox()
    family.setObjectName("comfyWorkflowFamily")
    model = QComboBox()
    model.setEditable(True)
    model.setObjectName("comfyModelCheckpoint")
    prompt = QPlainTextEdit()
    prompt.setObjectName("comfyPrompt")
    prompt.setPlaceholderText(tr.text("comfy.prompt.placeholder"))
    prompt.setMaximumHeight(90)
    negative = QPlainTextEdit()
    negative.setObjectName("comfyNegativePrompt")
    negative.setPlaceholderText(tr.text("comfy.negative.placeholder"))
    negative.setMaximumHeight(65)
    width = QSpinBox()
    width.setObjectName("comfyWidth")
    width.setRange(64, 1536)
    width.setValue(512)
    width.setSingleStep(64)
    height = QSpinBox()
    height.setObjectName("comfyHeight")
    height.setRange(64, 1536)
    height.setValue(512)
    height.setSingleStep(64)
    outputs = QSpinBox()
    outputs.setObjectName("comfyOutputCount")
    outputs.setRange(1, 4)
    outputs.setValue(1)
    seed = QLineEdit("42")
    seed.setObjectName("comfySeed")
    steps = QSpinBox()
    steps.setObjectName("comfySteps")
    steps.setRange(1, 80)
    steps.setValue(20)
    cfg = QDoubleSpinBox()
    cfg.setObjectName("comfyCfg")
    cfg.setRange(1.0, 20.0)
    cfg.setValue(7.0)
    cfg.setSingleStep(0.1)
    cleanup = QCheckBox(tr.text("comfy.cleanup.allow"))
    cleanup.setObjectName("comfyAllowMemoryCleanup")
    cleanup.setToolTip(tr.text("comfy.cleanup.description"))

    for item in service.workflow_families():
        family.addItem(str(item["family"]), str(item["family"]))

    workflow_layout.addRow(tr.text("comfy.family.label"), family)
    workflow_layout.addRow(tr.text("comfy.model.label"), model)
    workflow_layout.addRow(tr.text("comfy.prompt.label"), prompt)
    workflow_layout.addRow(tr.text("comfy.negative.label"), negative)
    dimensions = QWidget()
    dimensions_layout = QHBoxLayout(dimensions)
    dimensions_layout.setContentsMargins(0, 0, 0, 0)
    dimensions_layout.addWidget(width)
    dimensions_layout.addWidget(QLabel("×"))
    dimensions_layout.addWidget(height)
    workflow_layout.addRow(tr.text("comfy.dimensions.label"), dimensions)
    workflow_layout.addRow(tr.text("comfy.outputs.label"), outputs)
    workflow_layout.addRow(tr.text("comfy.seed.label"), seed)
    workflow_layout.addRow(tr.text("comfy.steps.label"), steps)
    workflow_layout.addRow(tr.text("comfy.cfg.label"), cfg)
    workflow_layout.addRow("", cleanup)

    workflow_buttons = QWidget()
    workflow_buttons_layout = QHBoxLayout(workflow_buttons)
    workflow_buttons_layout.setContentsMargins(0, 0, 0, 0)
    validate = QPushButton(tr.text("comfy.validate"))
    validate.setObjectName("comfyValidateButton")
    run = QPushButton(tr.text("comfy.run"))
    run.setObjectName("comfyRunButton")
    workflow_buttons_layout.addWidget(validate)
    workflow_buttons_layout.addWidget(run)
    workflow_layout.addRow(workflow_buttons)
    root_layout.addWidget(workflow_group)

    run_group = QGroupBox(tr.text("comfy.run.group"))
    run_layout = QGridLayout(run_group)
    run_id = QLineEdit()
    run_id.setObjectName("comfyRunId")
    run_id.setReadOnly(True)
    progress = QProgressBar()
    progress.setObjectName("comfyProgress")
    progress.setRange(0, 100)
    progress.setValue(0)
    operation = QLabel(tr.text("comfy.operation.idle"))
    operation.setObjectName("comfyOperationStatus")
    refresh_run = QPushButton(tr.text("comfy.run.refresh"))
    refresh_run.setObjectName("comfyRunRefreshButton")
    cancel = QPushButton(tr.text("comfy.cancel"))
    cancel.setObjectName("comfyCancelButton")
    capture = QPushButton(tr.text("comfy.capture"))
    capture.setObjectName("comfyCaptureButton")
    free_confirm = QCheckBox(tr.text("comfy.free.confirm"))
    free_confirm.setObjectName("comfyFreeConfirm")
    free_button = QPushButton(tr.text("comfy.free"))
    free_button.setObjectName("comfyFreeMemoryButton")
    free_button.setEnabled(False)
    free_confirm.toggled.connect(free_button.setEnabled)

    run_layout.addWidget(QLabel(tr.text("comfy.run_id.label")), 0, 0)
    run_layout.addWidget(run_id, 0, 1, 1, 3)
    run_layout.addWidget(progress, 1, 0, 1, 4)
    run_layout.addWidget(operation, 2, 0, 1, 4)
    run_layout.addWidget(refresh_run, 3, 0)
    run_layout.addWidget(cancel, 3, 1)
    run_layout.addWidget(capture, 3, 2)
    run_layout.addWidget(free_button, 3, 3)
    run_layout.addWidget(free_confirm, 4, 0, 1, 4)
    root_layout.addWidget(run_group)

    output_table = QTableWidget(0, 4)
    output_table.setObjectName("comfyOutputTable")
    output_table.setHorizontalHeaderLabels(
        [
            tr.text("comfy.output.node"),
            tr.text("comfy.output.index"),
            tr.text("comfy.output.file"),
            tr.text("comfy.output.type"),
        ]
    )
    output_table.setAccessibleName(tr.text("comfy.outputs.name"))
    details = QPlainTextEdit()
    details.setObjectName("comfyEvidenceView")
    details.setReadOnly(True)
    details.setAccessibleName(tr.text("comfy.evidence.name"))
    details.setMaximumHeight(150)
    root_layout.addWidget(output_table)
    root_layout.addWidget(details)

    def canonical(value: Any) -> Any:
        if hasattr(value, "canonical"):
            return value.canonical()
        if hasattr(value, "payload"):
            return value.payload()
        return value

    def set_operation(text: str) -> None:
        operation.setText(text)
        if status_bar is not None:
            status_bar.showMessage(text)

    def submit(method_name: str, args: tuple[Any, ...], kwargs: dict[str, Any], success: Callable[[Any], None]) -> None:
        set_operation(tr.text("comfy.operation.running"))

        def action() -> Any:
            worker_service = service.fork() if hasattr(service, "fork") else service
            try:
                return getattr(worker_service, method_name)(*args, **kwargs)
            finally:
                if worker_service is not service and hasattr(worker_service, "close"):
                    worker_service.close()

        worker = Worker(action)
        page._kodepoia_workers.append(worker)

        def on_error(reason: str) -> None:
            warning.setText(tr.text("comfy.error", reason=reason))
            set_operation(tr.text("comfy.operation.error", reason=reason))

        def on_finished() -> None:
            try:
                page._kodepoia_workers.remove(worker)
            except ValueError:
                pass

        worker.signals.result.connect(success)
        worker.signals.error.connect(on_error)
        worker.signals.finished.connect(on_finished)
        pool.start(worker)

    def populate_outputs(manifest: Any) -> None:
        data = canonical(manifest)
        refs = data.get("output_references", []) if isinstance(data, dict) else []
        output_table.setRowCount(len(refs))
        for row, reference in enumerate(refs):
            if not isinstance(reference, dict):
                continue
            values = (
                reference.get("node_id", ""),
                reference.get("output_index", ""),
                reference.get("server_filename", ""),
                reference.get("storage_type", ""),
            )
            for column, value in enumerate(values):
                output_table.setItem(row, column, QTableWidgetItem(str(value)))

    def apply_status(value: Any) -> None:
        data = canonical(value)
        if not isinstance(data, dict):
            return
        ready = bool(data.get("ready"))
        service_status.setText(tr.text("comfy.status.ready") if ready else tr.text("comfy.status.unavailable"))
        capability_status.setText(
            tr.text("comfy.capability.state", state=str(data.get("capability_state", "unknown")))
        )
        total = data.get("vram_total_bytes")
        free = data.get("vram_free_bytes")
        if isinstance(total, int) and isinstance(free, int):
            vram_status.setText(tr.text("comfy.vram.state", free=free // (1024 * 1024), total=total // (1024 * 1024)))
        else:
            vram_status.setText(tr.text("comfy.vram.unknown"))
        reason = str(data.get("reason", ""))
        warning.setText("" if ready else reason)
        set_operation(tr.text("comfy.operation.ready"))
        details.setPlainText(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))

    def refresh_action() -> None:
        def success(value: Any) -> None:
            apply_status(value)
            # Populate discovered checkpoint tokens through a second bounded worker call.
            submit("inventory_snapshot", (), {}, inventory_success)

        submit("status", (), {}, success)

    def inventory_success(value: Any) -> None:
        data = canonical(value)
        models = data.get("models", []) if isinstance(data, dict) else []
        current = model.currentText()
        model.clear()
        for group in models:
            if isinstance(group, dict) and group.get("model_type") == "checkpoints":
                for token in group.get("tokens", []):
                    model.addItem(str(token))
        if current and model.findText(current) < 0:
            model.setEditText(current)
        set_operation(tr.text("comfy.operation.ready"))

    def request_parameters() -> dict[str, Any] | None:
        try:
            seed_value = int(seed.text())
        except ValueError:
            warning.setText(tr.text("comfy.seed.invalid"))
            return None
        positive = prompt.toPlainText()
        negative_text = negative.toPlainText()
        if not positive.strip() or not negative_text.strip() or not model.currentText().strip():
            warning.setText(tr.text("comfy.required.warning"))
            return None
        return {
            "prompt": positive,
            "negative_prompt": negative_text,
            "width": width.value(),
            "height": height.value(),
            "output_count": outputs.value(),
            "seed": seed_value,
            "steps": steps.value(),
            "cfg": cfg.value(),
        }

    def validate_action() -> None:
        if not model.currentText().strip():
            warning.setText(tr.text("comfy.required.warning"))
            return

        def success(value: Any) -> None:
            data = canonical(value)
            details.setPlainText(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
            state = str(data.get("state", "unknown")) if isinstance(data, dict) else "unknown"
            warning.setText("" if state == "compatible" else tr.text("comfy.compat.warning", state=state))
            set_operation(tr.text("comfy.operation.ready"))

        submit(
            "validate_workflow",
            (str(family.currentData() or family.currentText()),),
            {"model_selections": {"checkpoint": model.currentText().strip()}},
            success,
        )

    def run_action() -> None:
        parameters = request_parameters()
        if parameters is None:
            return

        def success(value: Any) -> None:
            data = canonical(value)
            manifest = data.get("manifest", {}) if isinstance(data, dict) else {}
            current = str(manifest.get("run_id", ""))
            page._kodepoia_current_run_id = current or None
            run_id.setText(current)
            state = str(manifest.get("state", "unknown"))
            fraction = manifest.get("progress_fraction")
            progress.setValue(int(max(0.0, min(1.0, float(fraction or 0.0))) * 100))
            populate_outputs(manifest)
            details.setPlainText(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
            warning.setText("" if state == "succeeded" else tr.text("comfy.run.warning", state=state))
            set_operation(tr.text("comfy.run.state", state=state))

        submit(
            "run_workflow",
            (str(family.currentData() or family.currentText()),),
            {
                "parameters": parameters,
                "model_selections": {"checkpoint": model.currentText().strip()},
                "allow_memory_cleanup": cleanup.isChecked(),
            },
            success,
        )

    def refresh_run_action() -> None:
        current = page._kodepoia_current_run_id
        if not current:
            warning.setText(tr.text("comfy.run.none"))
            return

        def success(value: Any) -> None:
            data = canonical(value)
            state = str(data.get("state", "unknown")) if isinstance(data, dict) else "unknown"
            fraction = data.get("progress_fraction") if isinstance(data, dict) else None
            progress.setValue(int(max(0.0, min(1.0, float(fraction or 0.0))) * 100))
            populate_outputs(data)
            details.setPlainText(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
            set_operation(tr.text("comfy.run.state", state=state))

        submit("run_status", (current,), {}, success)

    def cancel_action() -> None:
        current = page._kodepoia_current_run_id
        if not current:
            warning.setText(tr.text("comfy.run.none"))
            return

        def success(value: Any) -> None:
            data = canonical(value)
            state = str(data.get("state", "unknown")) if isinstance(data, dict) else "unknown"
            details.setPlainText(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
            set_operation(tr.text("comfy.run.state", state=state))

        submit("cancel_run", (current,), {}, success)

    def capture_action() -> None:
        current = page._kodepoia_current_run_id
        if not current:
            warning.setText(tr.text("comfy.run.none"))
            return

        def success(value: Any) -> None:
            data = canonical(value)
            details.setPlainText(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
            set_operation(tr.text("comfy.capture.ready"))

        submit("capture_run_outputs", (current,), {}, success)

    def free_action() -> None:
        if not free_confirm.isChecked():
            warning.setText(tr.text("comfy.free.required"))
            return

        def success(value: Any) -> None:
            data = canonical(value)
            details.setPlainText(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
            free_confirm.setChecked(False)
            set_operation(tr.text("comfy.free.ready"))

        submit("free_memory", (), {"confirmed": True}, success)

    refresh.clicked.connect(refresh_action)
    validate.clicked.connect(validate_action)
    run.clicked.connect(run_action)
    refresh_run.clicked.connect(refresh_run_action)
    cancel.clicked.connect(cancel_action)
    capture.clicked.connect(capture_action)
    free_button.clicked.connect(free_action)

    return page
