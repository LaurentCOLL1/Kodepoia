from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.model_lab_bench import ModelLabBenchDecisionService
from kodepoia.kodestudio.model_lab_bench_localization import (
    ModelLabBenchDecisionTranslator,
)


def create_model_lab_bench_decision_page(
    project_root: Path,
    *,
    locale: str = "en",
    service: ModelLabBenchDecisionService | None = None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
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

    bench = service or ModelLabBenchDecisionService.for_project(project_root)
    tr = ModelLabBenchDecisionTranslator(locale)

    page = QWidget()
    mark_accessible(
        page,
        object_name="modelLabBenchDecisionPage",
        name=tr.text("title"),
        description=tr.text("subtitle"),
        description_required=True,
    )
    outer = QVBoxLayout(page)
    outer.addWidget(QLabel(f"<h2>{tr.text('title')}</h2>"))

    subtitle = QLabel(tr.text("subtitle"))
    subtitle.setWordWrap(True)
    outer.addWidget(subtitle)

    reference_notice = QLabel(tr.text("reference_only"))
    reference_notice.setWordWrap(True)
    mark_accessible(
        reference_notice,
        object_name="modelLabBenchDecisionReferenceNotice",
        name=tr.text("reference_only"),
        description=tr.text("reference_only"),
        description_required=True,
    )
    outer.addWidget(reference_notice)

    training_notice = QLabel(tr.text("no_training"))
    training_notice.setWordWrap(True)
    mark_accessible(
        training_notice,
        object_name="modelLabBenchDecisionNoTrainingNotice",
        name=tr.text("no_training"),
        description=tr.text("no_training"),
        description_required=True,
    )
    outer.addWidget(training_notice)

    toolbar = QHBoxLayout()
    refresh = QPushButton(tr.text("refresh"))
    inspect_status = QPushButton(tr.text("inspect_status"))
    preview_run = QPushButton(tr.text("preview_run"))
    run_bench = QPushButton(tr.text("run_bench"))
    for widget, name, text_value in (
        (refresh, "modelLabBenchDecisionRefresh", tr.text("refresh")),
        (inspect_status, "modelLabBenchDecisionInspectStatus", tr.text("inspect_status")),
        (preview_run, "modelLabBenchDecisionPreviewRun", tr.text("preview_run")),
        (run_bench, "modelLabBenchDecisionRun", tr.text("run_bench")),
    ):
        mark_accessible(
            widget,
            object_name=name,
            name=text_value,
            description=text_value,
            description_required=True,
        )
        toolbar.addWidget(widget)
    toolbar.addStretch(1)
    outer.addLayout(toolbar)

    confirm = QCheckBox(tr.text("confirm"))
    mark_accessible(
        confirm,
        object_name="modelLabBenchDecisionConfirm",
        name=tr.text("confirm"),
        description=tr.text("confirm"),
        description_required=True,
    )
    outer.addWidget(confirm)

    state = QLabel(tr.text("ready"))
    state.setWordWrap(True)
    mark_accessible(
        state,
        object_name="modelLabBenchDecisionState",
        name=tr.text("ready"),
        description=tr.text("ready"),
        description_required=True,
    )
    outer.addWidget(state)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    mark_accessible(
        scroll,
        object_name="modelLabBenchDecisionScroll",
        name=tr.text("title"),
        description=tr.text("subtitle"),
        description_required=True,
    )
    body = QWidget()
    body_layout = QVBoxLayout(body)

    summary_group = QGroupBox(tr.text("summary"))
    summary_layout = QVBoxLayout(summary_group)
    summary_label = QLabel()
    summary_label.setWordWrap(True)
    mark_accessible(
        summary_label,
        object_name="modelLabBenchDecisionSummary",
        name=tr.text("summary"),
        description=tr.text("summary"),
        description_required=True,
    )
    summary_layout.addWidget(summary_label)
    body_layout.addWidget(summary_group)

    def create_table(name: str, headers: list[str], accessible_name: str) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setMinimumHeight(155)
        mark_accessible(
            table,
            object_name=name,
            name=accessible_name,
            description=accessible_name,
            description_required=True,
        )
        return table

    reports_group = QGroupBox(tr.text("reports"))
    reports_layout = QVBoxLayout(reports_group)
    reports = create_table(
        "modelLabBenchDecisionReportsTable",
        ["Report", "Integrity", "Suite", "Config", "Models", "Tasks", "Domains"],
        tr.text("reports"),
    )
    reports_layout.addWidget(reports)
    body_layout.addWidget(reports_group)

    tasks_group = QGroupBox(tr.text("tasks"))
    tasks_layout = QVBoxLayout(tasks_group)
    tasks = create_table(
        "modelLabBenchDecisionTasksTable",
        ["Model", "Task", "Domain", "Critical", "Passed", "Total", "Score", "Categories"],
        tr.text("tasks"),
    )
    tasks_layout.addWidget(tasks)
    body_layout.addWidget(tasks_group)

    decisions_group = QGroupBox(tr.text("decisions"))
    decisions_layout = QVBoxLayout(decisions_group)
    decisions = create_table(
        "modelLabBenchDecisionDecisionsTable",
        ["Decision", "Disposition", "Integrity", "Base model", "Benchmark", "Dataset", "Blockers"],
        tr.text("decisions"),
    )
    decisions_layout.addWidget(decisions)
    inspect_decision = QPushButton(tr.text("inspect_decision"))
    mark_accessible(
        inspect_decision,
        object_name="modelLabBenchDecisionInspectDecision",
        name=tr.text("inspect_decision"),
        description=tr.text("inspect_decision"),
        description_required=True,
    )
    decisions_layout.addWidget(inspect_decision)
    body_layout.addWidget(decisions_group)

    diagnosis_group = QGroupBox(tr.text("diagnostics"))
    diagnosis_layout = QVBoxLayout(diagnosis_group)
    diagnosis = create_table(
        "modelLabBenchDecisionDiagnosisTable",
        ["Component", "Status", "Affected domains", "Evidence digest"],
        tr.text("diagnostics"),
    )
    diagnosis_layout.addWidget(diagnosis)
    body_layout.addWidget(diagnosis_group)

    targets_group = QGroupBox(tr.text("targets"))
    targets_layout = QVBoxLayout(targets_group)
    targets = create_table(
        "modelLabBenchDecisionTargetsTable",
        ["Domain", "Baseline", "Minimum", "Critical"],
        tr.text("targets"),
    )
    targets_layout.addWidget(targets)
    body_layout.addWidget(targets_group)

    raw_group = QGroupBox(tr.text("raw"))
    raw_layout = QVBoxLayout(raw_group)
    raw = QPlainTextEdit()
    raw.setReadOnly(True)
    raw.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    raw.setMinimumHeight(150)
    mark_accessible(
        raw,
        object_name="modelLabBenchDecisionDiagnosticsJson",
        name=tr.text("raw"),
        description=tr.text("raw"),
        description_required=True,
    )
    raw_layout.addWidget(raw)
    body_layout.addWidget(raw_group)

    body_layout.addStretch(1)
    scroll.setWidget(body)
    outer.addWidget(scroll, 1)

    snapshot: dict[str, object] = {}
    last_action: dict[str, object] | None = None

    def set_rows(table: QTableWidget, rows: list[list[str]]) -> None:
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        table.resizeColumnsToContents()

    def render_json() -> None:
        raw.setPlainText(
            json.dumps(
                {"snapshot": snapshot, "last_action": last_action},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )

    def selected_report() -> dict[str, object] | None:
        row = reports.currentRow()
        report_rows = snapshot.get("reports")
        if row < 0 or not isinstance(report_rows, list) or row >= len(report_rows):
            return None
        value = report_rows[row]
        return value if isinstance(value, dict) else None

    def selected_decision_payload() -> dict[str, object] | None:
        row = decisions.currentRow()
        decision_rows = snapshot.get("decisions")
        if row < 0 or not isinstance(decision_rows, list) or row >= len(decision_rows):
            return None
        value = decision_rows[row]
        return value if isinstance(value, dict) else None

    def render_report_detail() -> None:
        report = selected_report()
        rows: list[list[str]] = []
        if report is not None:
            for item in report.get("task_results", []):
                if not isinstance(item, dict):
                    continue
                rows.append(
                    [
                        str(item.get("model_ref", "")),
                        str(item.get("task_id", "")),
                        str(item.get("domain", "")),
                        "yes" if bool(item.get("critical")) else "no",
                        str(item.get("passed", 0)),
                        str(item.get("total", 0)),
                        str(item.get("score", 0.0)),
                        ", ".join(str(value) for value in item.get("categories", [])),
                    ]
                )
        set_rows(tasks, rows)

    def render_decision_detail() -> None:
        decision = selected_decision_payload()
        diag_rows: list[list[str]] = []
        target_rows: list[list[str]] = []
        if decision is not None:
            for item in decision.get("diagnostics", []):
                if not isinstance(item, dict):
                    continue
                diag_rows.append(
                    [
                        str(item.get("component", "")),
                        str(item.get("status", "")),
                        ", ".join(str(value) for value in item.get("affected_domains", [])),
                        str(item.get("evidence_digest") or ""),
                    ]
                )
            for item in decision.get("targets", []):
                if not isinstance(item, dict):
                    continue
                target_rows.append(
                    [
                        str(item.get("domain", "")),
                        str(item.get("baseline_score", "")),
                        str(item.get("minimum_score", "")),
                        "yes" if bool(item.get("critical")) else "no",
                    ]
                )
        set_rows(diagnosis, diag_rows)
        set_rows(targets, target_rows)

    def render_snapshot(payload: dict[str, object]) -> None:
        nonlocal snapshot
        snapshot = payload
        summary = payload.get("summary")
        summary_map = summary if isinstance(summary, dict) else {}
        summary_label.setText(
            " | ".join(
                (
                    f"Reports: {summary_map.get('report_count', 0)}",
                    f"Ready reports: {summary_map.get('ready_reports', 0)}",
                    f"Decisions: {summary_map.get('decision_count', 0)}",
                    f"Ready decisions: {summary_map.get('ready_decisions', 0)}",
                    f"Benchmark-bound: {summary_map.get('benchmark_bound_decisions', 0)}",
                    "Dispositions: " + json.dumps(summary_map.get("dispositions", {}), sort_keys=True),
                )
            )
        )

        report_rows: list[list[str]] = []
        for item in payload.get("reports", []):
            if not isinstance(item, dict):
                continue
            models = [
                str(model.get("model_ref", ""))
                for model in item.get("models", [])
                if isinstance(model, dict)
            ]
            domains = sorted(
                {
                    str(task.get("domain", ""))
                    for task in item.get("task_results", [])
                    if isinstance(task, dict)
                }
            )
            report_rows.append(
                [
                    str(item.get("report_digest", "")),
                    str(item.get("integrity", "")),
                    f"{item.get('suite_id', '')}@{item.get('suite_version', '')}",
                    str(item.get("config_digest", "")),
                    ", ".join(models),
                    str(len(item.get("task_results", []))),
                    ", ".join(domains),
                ]
            )
        set_rows(reports, report_rows)

        decision_rows: list[list[str]] = []
        for item in payload.get("decisions", []):
            if not isinstance(item, dict):
                continue
            base_model = item.get("base_model")
            base_map = base_model if isinstance(base_model, dict) else {}
            dataset = item.get("dataset")
            dataset_map = dataset if isinstance(dataset, dict) else {}
            decision_rows.append(
                [
                    str(item.get("decision_digest", "")),
                    str(item.get("disposition", "")).upper(),
                    str(item.get("integrity", "")),
                    f"{base_map.get('model_ref', '')}:{base_map.get('model_digest', '')}",
                    "bound" if bool(item.get("benchmark_bound")) else "unbound",
                    str(dataset_map.get("dataset_id") or "none"),
                    ", ".join(str(value) for value in item.get("blockers", [])),
                ]
            )
        set_rows(decisions, decision_rows)

        if report_rows:
            reports.selectRow(0)
        else:
            set_rows(tasks, [])
        if decision_rows:
            decisions.selectRow(0)
        else:
            set_rows(diagnosis, [])
            set_rows(targets, [])
        render_report_detail()
        render_decision_detail()
        render_json()

    def set_state(message: str) -> None:
        state.setText(message)
        state.setAccessibleName(message)
        state.setAccessibleDescription(message)
        if status_bar is not None:
            status_bar.showMessage(message)

    def refresh_now() -> None:
        try:
            render_snapshot(bench.snapshot())
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
                result = self.operation()
            except Exception as exc:
                self.signals.failed.emit(str(exc))
            else:
                self.signals.done.emit(result)

    pool = QThreadPool.globalInstance()
    workers: list[Task] = []
    action_buttons = (inspect_status, preview_run, run_bench, inspect_decision)

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
                "schema": ModelLabBenchDecisionService.schema,
                "status": "blocked",
                "detail": detail,
            }
            render_json()
            set_state(f"{tr.text('blocked')}: {detail}")

        task.signals.done.connect(finish)
        task.signals.failed.connect(fail)
        pool.start(task)

    def inspect_selected_decision() -> None:
        item = selected_decision_payload()
        if item is None:
            set_state(tr.text("select_decision"))
            return
        decision_id = str(item.get("decision_digest", "")).strip()
        if not decision_id:
            set_state(tr.text("select_decision"))
            return
        run_action(lambda: bench.inspect_gap_decision(decision_id))

    refresh.clicked.connect(refresh_now)
    inspect_status.clicked.connect(lambda: run_action(bench.inspect_benchmark_status))
    preview_run.clicked.connect(lambda: run_action(bench.preview_benchmark_run))
    run_bench.clicked.connect(
        lambda: run_action(
            lambda: bench.run_benchmark(confirmed=confirm.isChecked()),
            refresh_after=True,
        )
    )
    inspect_decision.clicked.connect(inspect_selected_decision)
    reports.itemSelectionChanged.connect(render_report_detail)
    decisions.itemSelectionChanged.connect(render_decision_detail)

    refresh_now()
    page._model_lab_bench_decision_service = bench
    page._model_lab_bench_decision_workers = workers
    page._model_lab_bench_decision_refresh = refresh_now
    page._model_lab_bench_decision_render_snapshot = render_snapshot
    return page


__all__ = ["create_model_lab_bench_decision_page"]
