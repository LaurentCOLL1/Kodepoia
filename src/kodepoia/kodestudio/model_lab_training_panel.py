from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.model_lab_training import ModelLabTrainingService
from kodepoia.kodestudio.model_lab_training_localization import ModelLabTrainingTranslator


def create_model_lab_training_page(
    project_root: Path,
    *,
    locale: str = "en",
    service: ModelLabTrainingService | None = None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
        QComboBox,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QScrollArea,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    training = service or ModelLabTrainingService.for_project(project_root)
    tr = ModelLabTrainingTranslator(locale)

    page = QWidget()
    mark_accessible(
        page,
        object_name="modelLabTrainingPage",
        name=tr.text("title"),
        description=tr.text("subtitle"),
        description_required=True,
    )
    outer = QVBoxLayout(page)
    outer.addWidget(QLabel(f"<h2>{tr.text('title')}</h2>"))
    subtitle = QLabel(tr.text("subtitle"))
    subtitle.setWordWrap(True)
    outer.addWidget(subtitle)

    for object_name, text_value in (
        ("modelLabTrainingReferenceNotice", tr.text("reference_only")),
        ("modelLabTrainingBoundaryNotice", tr.text("boundary")),
        ("modelLabTrainingBackendTruth", tr.text("backend_truth")),
    ):
        label = QLabel(text_value)
        label.setWordWrap(True)
        mark_accessible(
            label,
            object_name=object_name,
            name=text_value,
            description=text_value,
            description_required=True,
        )
        outer.addWidget(label)

    toolbar = QHBoxLayout()
    refresh = QPushButton(tr.text("refresh"))
    backend = QComboBox()
    backend.addItem("Local", "local")
    backend.addItem("Kaggle T4", "kaggle")
    doctor = QPushButton(tr.text("doctor"))
    inspect_plan = QPushButton(tr.text("inspect_plan"))
    preview = QPushButton(tr.text("preview_run"))
    launch = QPushButton(tr.text("launch"))
    inspect_run = QPushButton(tr.text("inspect_run"))
    cancel = QPushButton(tr.text("cancel"))
    resume = QPushButton(tr.text("resume"))
    for widget, object_name, text_value in (
        (refresh, "modelLabTrainingRefresh", tr.text("refresh")),
        (backend, "modelLabTrainingBackend", tr.text("backend")),
        (doctor, "modelLabTrainingDoctor", tr.text("doctor")),
        (inspect_plan, "modelLabTrainingInspectPlan", tr.text("inspect_plan")),
        (preview, "modelLabTrainingPreviewRun", tr.text("preview_run")),
        (launch, "modelLabTrainingLaunch", tr.text("launch")),
        (inspect_run, "modelLabTrainingInspectRun", tr.text("inspect_run")),
        (cancel, "modelLabTrainingCancel", tr.text("cancel")),
        (resume, "modelLabTrainingResume", tr.text("resume")),
    ):
        mark_accessible(
            widget,
            object_name=object_name,
            name=text_value,
            description=text_value,
            description_required=True,
        )
        toolbar.addWidget(widget)
    outer.addLayout(toolbar)

    confirm = QCheckBox(tr.text("confirm"))
    mark_accessible(
        confirm,
        object_name="modelLabTrainingConfirm",
        name=tr.text("confirm"),
        description=tr.text("confirm"),
        description_required=True,
    )
    outer.addWidget(confirm)

    state = QLabel(tr.text("ready"))
    state.setWordWrap(True)
    mark_accessible(
        state,
        object_name="modelLabTrainingState",
        name=tr.text("ready"),
        description=tr.text("ready"),
        description_required=True,
    )
    outer.addWidget(state)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    mark_accessible(
        scroll,
        object_name="modelLabTrainingScroll",
        name=tr.text("title"),
        description=tr.text("subtitle"),
        description_required=True,
    )
    body = QWidget()
    body_layout = QVBoxLayout(body)

    summary_group = QGroupBox(tr.text("summary"))
    summary_layout = QVBoxLayout(summary_group)
    summary = QLabel()
    summary.setWordWrap(True)
    mark_accessible(
        summary,
        object_name="modelLabTrainingSummary",
        name=tr.text("summary"),
        description=tr.text("summary"),
        description_required=True,
    )
    summary_layout.addWidget(summary)
    body_layout.addWidget(summary_group)

    def make_table(name: str, headers: list[str], accessible_name: str) -> QTableWidget:
        widget = QTableWidget(0, len(headers))
        widget.setHorizontalHeaderLabels(headers)
        widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        widget.setMinimumHeight(145)
        mark_accessible(
            widget,
            object_name=name,
            name=accessible_name,
            description=accessible_name,
            description_required=True,
        )
        return widget

    plans_group = QGroupBox(tr.text("plans"))
    plans_layout = QVBoxLayout(plans_group)
    plans = make_table(
        "modelLabTrainingPlansTable",
        ["Plan", "Authorized", "Mode", "Model", "Tokenizer", "Dataset", "Decision", "Capability", "Steps", "LoRA", "Blockers"],
        tr.text("plans"),
    )
    plans_layout.addWidget(plans)
    body_layout.addWidget(plans_group)

    capability_group = QGroupBox(tr.text("capabilities"))
    capability_layout = QVBoxLayout(capability_group)
    capabilities = make_table(
        "modelLabTrainingCapabilitiesTable",
        ["Report", "Integrity", "Disposition", "Backend", "DType", "4-bit", "Blockers"],
        tr.text("capabilities"),
    )
    capability_layout.addWidget(capabilities)
    body_layout.addWidget(capability_group)

    runs_group = QGroupBox(tr.text("runs"))
    runs_layout = QVBoxLayout(runs_group)
    runs = make_table(
        "modelLabTrainingRunsTable",
        ["Run", "State", "Plan", "Steps", "Train loss", "Eval loss", "Resumed", "Blockers"],
        tr.text("runs"),
    )
    runs_layout.addWidget(runs)
    body_layout.addWidget(runs_group)

    checkpoints_group = QGroupBox(tr.text("checkpoints"))
    checkpoints_layout = QVBoxLayout(checkpoints_group)
    checkpoints = make_table(
        "modelLabTrainingCheckpointsTable",
        ["Checkpoint", "Step", "Plan", "Lineage", "Train loss", "Eval loss", "Artifact digest"],
        tr.text("checkpoints"),
    )
    checkpoints_layout.addWidget(checkpoints)
    body_layout.addWidget(checkpoints_group)

    raw_group = QGroupBox(tr.text("raw"))
    raw_layout = QVBoxLayout(raw_group)
    diagnostics = QPlainTextEdit()
    diagnostics.setReadOnly(True)
    diagnostics.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    diagnostics.setMinimumHeight(160)
    mark_accessible(
        diagnostics,
        object_name="modelLabTrainingDiagnostics",
        name=tr.text("raw"),
        description=tr.text("raw"),
        description_required=True,
    )
    raw_layout.addWidget(diagnostics)
    body_layout.addWidget(raw_group)
    body_layout.addStretch(1)
    scroll.setWidget(body)
    outer.addWidget(scroll, 1)

    snapshot: dict[str, object] = {}
    last_action: dict[str, object] | None = None
    checkpoint_rows: list[dict[str, object]] = []

    def set_rows(widget: QTableWidget, rows: list[list[str]]) -> None:
        widget.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                widget.setItem(row_index, column_index, QTableWidgetItem(value))
        widget.resizeColumnsToContents()

    def set_state(message: str) -> None:
        state.setText(message)
        state.setAccessibleName(message)
        state.setAccessibleDescription(message)
        if status_bar is not None:
            status_bar.showMessage(message)

    def render_json() -> None:
        diagnostics.setPlainText(
            json.dumps(
                {"snapshot": snapshot, "last_action": last_action},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )

    def selected(items: object, widget: QTableWidget) -> dict[str, object] | None:
        row = widget.currentRow()
        if row < 0 or not isinstance(items, list) or row >= len(items):
            return None
        item = items[row]
        return item if isinstance(item, dict) else None

    def selected_plan() -> dict[str, object] | None:
        return selected(snapshot.get("plans"), plans)

    def selected_run() -> dict[str, object] | None:
        return selected(snapshot.get("runs"), runs)

    def selected_checkpoint() -> dict[str, object] | None:
        row = checkpoints.currentRow()
        if row < 0 or row >= len(checkpoint_rows):
            return None
        return checkpoint_rows[row]

    def render_checkpoints() -> None:
        nonlocal checkpoint_rows
        run = selected_run()
        checkpoint_rows = []
        rows: list[list[str]] = []
        if run is not None:
            for item in run.get("checkpoints", []):
                if not isinstance(item, dict):
                    continue
                checkpoint_rows.append(item)
                rows.append(
                    [
                        str(item.get("checkpoint_id", "")),
                        str(item.get("step", "")),
                        str(item.get("plan_digest", "")),
                        "bound" if bool(item.get("lineage_bound")) else "blocked",
                        str(item.get("train_loss", "")),
                        str(item.get("eval_loss", "")),
                        str(item.get("artifact_digest", "")),
                    ]
                )
        set_rows(checkpoints, rows)
        if rows:
            checkpoints.selectRow(0)

    def render(payload: dict[str, object]) -> None:
        nonlocal snapshot
        snapshot = payload
        summary_map = payload.get("summary")
        summary_data = summary_map if isinstance(summary_map, dict) else {}
        summary.setText(
            " | ".join(
                (
                    f"Plans: {summary_data.get('plan_count', 0)}",
                    f"Authorized: {summary_data.get('authorized_plans', 0)}",
                    f"Capabilities: {summary_data.get('capability_count', 0)}",
                    f"Runs: {summary_data.get('run_count', 0)}",
                    f"Active: {summary_data.get('active_runs', 0)}",
                )
            )
        )

        plan_rows: list[list[str]] = []
        for item in payload.get("plans", []):
            if not isinstance(item, dict):
                continue
            model = item.get("model") if isinstance(item.get("model"), dict) else {}
            dataset = item.get("dataset") if isinstance(item.get("dataset"), dict) else {}
            sft = item.get("sft") if isinstance(item.get("sft"), dict) else {}
            lora = item.get("lora") if isinstance(item.get("lora"), dict) else {}
            plan_rows.append(
                [
                    str(item.get("plan_digest", "")),
                    "yes" if bool(item.get("authorized")) else "no",
                    str(item.get("mode", "")),
                    f"{model.get('model_ref', '')}@{model.get('model_revision', '')}",
                    f"{model.get('tokenizer_ref', '')}@{model.get('tokenizer_revision', '')}",
                    f"{dataset.get('dataset_id', '')}:{dataset.get('dataset_digest', '')}",
                    str(item.get("decision_digest") or ""),
                    str(item.get("capability_report_digest") or ""),
                    str(sft.get("max_steps", "")),
                    f"r={lora.get('rank', '')}, a={lora.get('alpha', '')}",
                    ", ".join(str(value) for value in item.get("blockers", [])),
                ]
            )
        set_rows(plans, plan_rows)

        capability_rows: list[list[str]] = []
        for item in payload.get("capabilities", []):
            if not isinstance(item, dict):
                continue
            capability_rows.append(
                [
                    str(item.get("report_digest", "")),
                    str(item.get("integrity", "")),
                    str(item.get("disposition", "")),
                    str(item.get("backend", "")),
                    str(item.get("dtype_supported", "")),
                    str(item.get("four_bit_supported", "")),
                    ", ".join(str(value) for value in item.get("blockers", [])),
                ]
            )
        set_rows(capabilities, capability_rows)

        run_rows: list[list[str]] = []
        for item in payload.get("runs", []):
            if not isinstance(item, dict):
                continue
            run_rows.append(
                [
                    str(item.get("run_id", "")),
                    str(item.get("state", "")),
                    str(item.get("plan_digest", "")),
                    str(item.get("completed_steps", "")),
                    str(item.get("train_loss", "")),
                    str(item.get("eval_loss", "")),
                    str(item.get("resumed_from") or ""),
                    ", ".join(str(value) for value in item.get("blockers", [])),
                ]
            )
        set_rows(runs, run_rows)
        if plan_rows:
            plans.selectRow(0)
        if run_rows:
            runs.selectRow(0)
        render_checkpoints()
        render_json()

    def refresh_now() -> None:
        try:
            render(training.snapshot())
        except Exception as exc:
            set_state(f"{tr.text('blocked')}: {exc}")
            return
        set_state(tr.text("ready"))

    class WorkerSignals(QObject):
        done = Signal(object)
        failed = Signal(str)

    class Task(QRunnable):
        def __init__(self, operation: Callable[[], object]) -> None:
            super().__init__()
            self.operation = operation
            self.signals = WorkerSignals()

        def run(self) -> None:
            try:
                self.signals.done.emit(self.operation())
            except Exception as exc:
                self.signals.failed.emit(str(exc))

    pool = QThreadPool.globalInstance()
    workers: list[Task] = []
    action_buttons = (doctor, inspect_plan, preview, launch, inspect_run, cancel, resume)

    def run_action(operation: Callable[[], object], *, refresh_after: bool = False) -> None:
        nonlocal last_action
        for button in action_buttons:
            button.setEnabled(False)
        set_state(tr.text("running"))
        task = Task(operation)
        workers.append(task)

        def finish(result: object) -> None:
            nonlocal last_action
            if task in workers:
                workers.remove(task)
            for button in action_buttons:
                button.setEnabled(True)
            last_action = result if isinstance(result, dict) else {"result": str(result)}
            if refresh_after:
                refresh_now()
            else:
                render_json()
                set_state(tr.text("complete"))

        def fail(detail: str) -> None:
            nonlocal last_action
            if task in workers:
                workers.remove(task)
            for button in action_buttons:
                button.setEnabled(True)
            last_action = {
                "schema": ModelLabTrainingService.schema,
                "status": "blocked",
                "detail": detail,
            }
            render_json()
            set_state(f"{tr.text('blocked')}: {detail}")

        task.signals.done.connect(finish)
        task.signals.failed.connect(fail)
        pool.start(task)

    def backend_value() -> str:
        return str(backend.currentData())

    def plan_id() -> str | None:
        item = selected_plan()
        return None if item is None else str(item.get("plan_digest", "")).strip() or None

    def run_id() -> str | None:
        item = selected_run()
        return None if item is None else str(item.get("run_id", "")).strip() or None

    def do_inspect_plan() -> None:
        value = plan_id()
        if value is None:
            set_state(tr.text("select_plan"))
            return
        run_action(lambda: training.inspect_plan(value))

    def do_preview() -> None:
        value = plan_id()
        if value is None:
            set_state(tr.text("select_plan"))
            return
        run_action(lambda: training.preview_run(value, backend_value()))

    def do_launch() -> None:
        value = plan_id()
        if value is None:
            set_state(tr.text("select_plan"))
            return
        run_action(
            lambda: training.run_training(
                value,
                backend_value(),
                confirmed=confirm.isChecked(),
            ),
            refresh_after=True,
        )

    def do_inspect_run() -> None:
        value = run_id()
        if value is None:
            set_state(tr.text("select_run"))
            return
        run_action(lambda: training.inspect_run(value, backend_value()))

    def do_cancel() -> None:
        value = run_id()
        if value is None:
            set_state(tr.text("select_run"))
            return
        run_action(
            lambda: training.cancel_run(
                value,
                backend_value(),
                confirmed=confirm.isChecked(),
            ),
            refresh_after=True,
        )

    def do_resume() -> None:
        item = selected_checkpoint()
        if item is None or not bool(item.get("lineage_bound")):
            set_state(tr.text("select_checkpoint"))
            return
        checkpoint_id = str(item.get("checkpoint_id", "")).strip()
        if not checkpoint_id:
            set_state(tr.text("select_checkpoint"))
            return
        run_action(
            lambda: training.resume_checkpoint(
                checkpoint_id,
                backend_value(),
                confirmed=confirm.isChecked(),
            ),
            refresh_after=True,
        )

    refresh.clicked.connect(refresh_now)
    doctor.clicked.connect(lambda: run_action(lambda: training.inspect_doctor(backend_value())))
    inspect_plan.clicked.connect(do_inspect_plan)
    preview.clicked.connect(do_preview)
    launch.clicked.connect(do_launch)
    inspect_run.clicked.connect(do_inspect_run)
    cancel.clicked.connect(do_cancel)
    resume.clicked.connect(do_resume)
    runs.itemSelectionChanged.connect(render_checkpoints)

    refresh_now()
    page._model_lab_training_service = training
    page._model_lab_training_workers = workers
    page._model_lab_training_refresh = refresh_now
    return page


__all__ = ["create_model_lab_training_page"]
