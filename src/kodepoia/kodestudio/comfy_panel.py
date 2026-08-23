from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from kodepoia.comfyui.packs import ProductionWorkflowFamily
from kodepoia.comfyui.service import ComfyService
from kodepoia.kodestudio.accessibility import mark_accessible


def create_comfy_page(
    project_root: Path,
    *,
    translator,
    service=None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal
    from PySide6.QtWidgets import (
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QPushButton,
        QSpinBox,
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

    tr = translator
    root = Path(project_root).resolve(strict=False)
    facade = service or ComfyService(root)
    page = QWidget()
    page.setObjectName("comfyPage")
    page._kodepoia_comfy_service = facade
    page._kodepoia_workers = []
    page._kodepoia_comfy_busy = False
    page._kodepoia_comfy_run_id = None
    pool = QThreadPool.globalInstance()

    layout = QVBoxLayout(page)
    title = QLabel(f"<h2>{tr.text('comfy.title')}</h2>")
    description = QLabel(tr.text("comfy.description"))
    description.setWordWrap(True)
    layout.addWidget(title)
    layout.addWidget(description)

    status_group = QGroupBox(tr.text("comfy.status.group"))
    status_grid = QGridLayout(status_group)
    connection = QLabel(tr.text("comfy.status.connection.idle"))
    connection.setObjectName("comfyConnectionStatus")
    capability = QLabel(tr.text("comfy.status.capability.missing"))
    capability.setObjectName("comfyCapabilityStatus")
    vram = QLabel(tr.text("comfy.status.vram.unknown"))
    vram.setObjectName("comfyVramStatus")
    ollama = QLabel(tr.text("comfy.status.ollama.na"))
    ollama.setObjectName("comfyOllamaStatus")
    model_status = QLabel(tr.text("comfy.status.model.unchecked"))
    model_status.setObjectName("comfyModelStatus")
    admission_status = QLabel(tr.text("comfy.status.admission.unknown"))
    admission_status.setObjectName("comfyAdmissionStatus")
    status_grid.addWidget(connection, 0, 0)
    status_grid.addWidget(capability, 0, 1)
    status_grid.addWidget(vram, 1, 0)
    status_grid.addWidget(ollama, 1, 1)
    status_grid.addWidget(model_status, 2, 0)
    status_grid.addWidget(admission_status, 2, 1)
    layout.addWidget(status_group)

    workflow_group = QGroupBox(tr.text("comfy.workflow.group"))
    form = QFormLayout(workflow_group)
    family = QComboBox()
    family.setObjectName("comfyWorkflowFamily")
    for item in ProductionWorkflowFamily:
        family.addItem(item.value, item.value)
    model = QLineEdit()
    model.setObjectName("comfyModelSelection")
    model.setPlaceholderText(tr.text("comfy.model.placeholder"))
    prompt = QPlainTextEdit()
    prompt.setObjectName("comfyPrompt")
    prompt.setPlaceholderText(tr.text("comfy.prompt.placeholder"))
    prompt.setMaximumHeight(90)
    negative = QPlainTextEdit()
    negative.setObjectName("comfyNegativePrompt")
    negative.setPlaceholderText(tr.text("comfy.negative.placeholder"))
    negative.setMaximumHeight(70)
    width = QSpinBox()
    width.setObjectName("comfyWidth")
    width.setRange(64, 1536)
    width.setValue(1024)
    height = QSpinBox()
    height.setObjectName("comfyHeight")
    height.setRange(64, 1536)
    height.setValue(1024)
    outputs = QSpinBox()
    outputs.setObjectName("comfyOutputCount")
    outputs.setRange(1, 4)
    outputs.setValue(1)
    seed = QSpinBox()
    seed.setObjectName("comfySeed")
    seed.setRange(0, 2_147_483_647)
    steps = QSpinBox()
    steps.setObjectName("comfySteps")
    steps.setRange(1, 80)
    steps.setValue(24)
    cfg = QDoubleSpinBox()
    cfg.setObjectName("comfyCfg")
    cfg.setRange(1.0, 20.0)
    cfg.setSingleStep(0.5)
    cfg.setValue(7.0)
    form.addRow(tr.text("comfy.family"), family)
    form.addRow(tr.text("comfy.model"), model)
    form.addRow(tr.text("comfy.prompt"), prompt)
    form.addRow(tr.text("comfy.negative"), negative)
    dimensions = QWidget()
    dimensions_layout = QHBoxLayout(dimensions)
    dimensions_layout.setContentsMargins(0, 0, 0, 0)
    dimensions_layout.addWidget(width)
    dimensions_layout.addWidget(QLabel("×"))
    dimensions_layout.addWidget(height)
    dimensions_layout.addWidget(QLabel(tr.text("comfy.outputs")))
    dimensions_layout.addWidget(outputs)
    form.addRow(tr.text("comfy.dimensions"), dimensions)
    sampling = QWidget()
    sampling_layout = QHBoxLayout(sampling)
    sampling_layout.setContentsMargins(0, 0, 0, 0)
    sampling_layout.addWidget(QLabel(tr.text("comfy.seed")))
    sampling_layout.addWidget(seed)
    sampling_layout.addWidget(QLabel(tr.text("comfy.steps")))
    sampling_layout.addWidget(steps)
    sampling_layout.addWidget(QLabel(tr.text("comfy.cfg")))
    sampling_layout.addWidget(cfg)
    form.addRow(tr.text("comfy.sampling"), sampling)
    layout.addWidget(workflow_group)

    actions = QHBoxLayout()
    refresh = QPushButton(tr.text("comfy.refresh"))
    refresh.setObjectName("comfyRefreshButton")
    validate = QPushButton(tr.text("comfy.validate"))
    validate.setObjectName("comfyValidateButton")
    run = QPushButton(tr.text("comfy.run"))
    run.setObjectName("comfyRunButton")
    run_refresh = QPushButton(tr.text("comfy.run.refresh"))
    run_refresh.setObjectName("comfyRunRefreshButton")
    cancel = QPushButton(tr.text("comfy.cancel"))
    cancel.setObjectName("comfyCancelButton")
    free_memory = QPushButton(tr.text("comfy.free_memory"))
    free_memory.setObjectName("comfyFreeMemoryButton")
    evidence = QPushButton(tr.text("comfy.evidence"))
    evidence.setObjectName("comfyEvidenceButton")
    for button in (refresh, validate, run, run_refresh, cancel, free_memory, evidence):
        actions.addWidget(button)
    layout.addLayout(actions)

    run_state = QLabel(tr.text("comfy.run.idle"))
    run_state.setObjectName("comfyRunStatus")
    layout.addWidget(run_state)
    details = QPlainTextEdit()
    details.setObjectName("comfyEvidenceView")
    details.setReadOnly(True)
    details.setAccessibleName(tr.text("comfy.details.name"))
    details.setAccessibleDescription(tr.text("comfy.details.description"))
    layout.addWidget(details, 1)

    for widget, name, description_text in (
        (family, tr.text("comfy.family"), tr.text("comfy.family.description")),
        (model, tr.text("comfy.model"), tr.text("comfy.model.description")),
        (prompt, tr.text("comfy.prompt"), tr.text("comfy.prompt.description")),
        (negative, tr.text("comfy.negative"), tr.text("comfy.negative.description")),
    ):
        mark_accessible(
            widget,
            object_name=widget.objectName(),
            name=name,
            description=description_text,
            description_required=True,
        )

    def set_busy(value: bool) -> None:
        page._kodepoia_comfy_busy = value
        for button in (refresh, validate, run, run_refresh, cancel, free_memory, evidence):
            button.setEnabled(not value)

    def pretty(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)

    def show_result(value: Any) -> None:
        details.setPlainText(pretty(value))
        if not isinstance(value, dict):
            return
        run_payload = value.get("run") if isinstance(value.get("run"), dict) else value
        run_id = run_payload.get("run_id") if isinstance(run_payload, dict) else None
        if isinstance(run_id, str):
            page._kodepoia_comfy_run_id = run_id
        state = run_payload.get("state") if isinstance(run_payload, dict) else value.get("state")
        progress = run_payload.get("progress_fraction") if isinstance(run_payload, dict) else None
        if state is not None:
            suffix = "" if progress is None else f" — {float(progress) * 100:.0f}%"
            run_state.setText(tr.text("comfy.run.state", state=state, suffix=suffix))
        if "protocol_ready" in value:
            connection.setText(
                tr.text("comfy.status.connection.ready")
                if value.get("protocol_ready")
                else tr.text("comfy.status.connection.unavailable")
            )
            capability.setText(
                tr.text("comfy.status.capability", state=value.get("capability_state", "unknown"))
            )
        compatibility = value.get("compatibility")
        if isinstance(compatibility, dict):
            selected = compatibility.get("selected_models", [])
            selected_text = ", ".join(
                str(item[1])
                for item in selected
                if isinstance(item, (list, tuple)) and len(item) == 2
            )
            model_status.setText(
                tr.text(
                    "comfy.status.model",
                    state=compatibility.get("state", "unknown"),
                    selection=selected_text or tr.text("comfy.status.model.none"),
                )
            )
        telemetry = value.get("telemetry")
        if isinstance(telemetry, dict):
            devices = telemetry.get("devices", [])
            if isinstance(devices, list) and devices:
                primary = devices[0]
                free = int(primary.get("vram_free_bytes", 0)) // (1024 * 1024)
                total = int(primary.get("vram_total_bytes", 0)) // (1024 * 1024)
                vram.setText(tr.text("comfy.status.vram", free=free, total=total))
        admission = value.get("admission")
        if isinstance(admission, dict):
            admission_status.setText(
                tr.text(
                    "comfy.status.admission",
                    state=admission.get("decision", "unknown"),
                )
            )
        coexistence = value.get("ollama_coexistence")
        if isinstance(coexistence, dict):
            ollama.setText(tr.text("comfy.status.ollama", state=coexistence.get("state", "unknown")))
        if status_bar is not None:
            status_bar.showMessage(run_state.text())

    def failure(reason: str) -> None:
        run_state.setText(tr.text("comfy.run.error", reason=reason))
        details.setPlainText(pretty({"state": "error", "reason": reason}))
        if status_bar is not None:
            status_bar.showMessage(run_state.text())

    def start(operation: Callable[[Any], Any], on_result: Callable[[Any], None] = show_result) -> None:
        if page._kodepoia_comfy_busy:
            return
        set_busy(True)

        def invoke() -> Any:
            worker_service = facade.fork() if hasattr(facade, "fork") else facade
            return operation(worker_service)

        worker = Worker(invoke)
        page._kodepoia_workers.append(worker)
        worker.signals.result.connect(on_result)
        worker.signals.failed.connect(failure)

        def finish() -> None:
            set_busy(False)
            try:
                page._kodepoia_workers.remove(worker)
            except ValueError:
                pass

        worker.signals.finished.connect(finish)
        pool.start(worker)

    def selected_family() -> str:
        return str(family.currentData())

    def selected_model() -> str | None:
        value = model.text().strip()
        return value or None

    def refresh_dashboard() -> None:
        def operation(worker_service):
            status_value = worker_service.status()
            vram_value = worker_service.vram(family=selected_family())
            return {"status": status_value, "vram": vram_value}

        def apply(value: Any) -> None:
            details.setPlainText(pretty(value))
            if isinstance(value, dict):
                status_value = value.get("status")
                vram_value = value.get("vram")
                if isinstance(status_value, dict):
                    show_result(status_value)
                if isinstance(vram_value, dict):
                    show_result(vram_value)

        start(operation, apply)

    def validate_workflow() -> None:
        start(
            lambda worker_service: worker_service.validate(
                selected_family(),
                model_selection=selected_model(),
                refresh_inventory=True,
            )
        )

    def submit_run() -> None:
        start(
            lambda worker_service: worker_service.run(
                selected_family(),
                prompt=prompt.toPlainText(),
                negative_prompt=negative.toPlainText(),
                width=width.value(),
                height=height.value(),
                output_count=outputs.value(),
                seed=seed.value(),
                steps=steps.value(),
                cfg=cfg.value(),
                model_selection=selected_model(),
            )
        )

    def refresh_run() -> None:
        run_id = page._kodepoia_comfy_run_id
        if not run_id:
            return
        start(lambda worker_service: worker_service.run_status(run_id, reconcile=True))

    def cancel_run() -> None:
        run_id = page._kodepoia_comfy_run_id
        if not run_id:
            return
        start(lambda worker_service: worker_service.cancel(run_id))

    def request_free_memory() -> None:
        start(lambda worker_service: worker_service.free_memory())

    def show_evidence() -> None:
        run_id = page._kodepoia_comfy_run_id
        if not run_id:
            return
        start(lambda worker_service: worker_service.evidence(run_id))

    refresh.clicked.connect(refresh_dashboard)
    validate.clicked.connect(validate_workflow)
    run.clicked.connect(submit_run)
    run_refresh.clicked.connect(refresh_run)
    cancel.clicked.connect(cancel_run)
    free_memory.clicked.connect(request_free_memory)
    evidence.clicked.connect(show_evidence)

    timer = QTimer(page)
    timer.setInterval(1000)
    timer.timeout.connect(refresh_run)
    timer.start()
    page._kodepoia_comfy_timer = timer
    return page
