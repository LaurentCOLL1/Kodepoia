from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path

from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.model_lab_candidate import ModelLabCandidateLifecycleService
from kodepoia.kodestudio.model_lab_candidate_localization import (
    ModelLabCandidateLifecycleTranslator,
)


def create_model_lab_candidate_page(
    project_root: Path,
    *,
    locale: str = "en",
    service: ModelLabCandidateLifecycleService | None = None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
        QComboBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    root = Path(project_root).resolve(strict=False)
    ux = service or ModelLabCandidateLifecycleService.for_project(root)
    tr = ModelLabCandidateLifecycleTranslator(locale)

    page = QWidget()
    mark_accessible(
        page,
        object_name="modelLabCandidatePage",
        name=tr.text("title"),
        description=tr.text("subtitle"),
        description_required=True,
    )
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(f"<h2>{tr.text('title')}</h2>"))
    layout.addWidget(QLabel(tr.text("subtitle")))
    layout.addWidget(QLabel(tr.text("evidence_gate")))
    layout.addWidget(QLabel(tr.text("reference_only")))
    layout.addWidget(QLabel(tr.text("boundary")))

    controls = QHBoxLayout()
    refresh = QPushButton(tr.text("refresh"))
    inspect_evaluation = QPushButton(tr.text("inspect_evaluation"))
    preview_export = QPushButton(tr.text("preview_export"))
    export = QPushButton(tr.text("export"))
    preview_conversion = QPushButton(tr.text("preview_conversion"))
    convert = QPushButton(tr.text("convert"))
    ollama_status = QPushButton(tr.text("ollama_status"))
    preview_package = QPushButton(tr.text("preview_package"))
    package = QPushButton(tr.text("package"))
    preview_promotion = QPushButton(tr.text("preview_promotion"))
    promote = QPushButton(tr.text("promote"))
    preview_rollback = QPushButton(tr.text("preview_rollback"))
    rollback = QPushButton(tr.text("rollback"))
    buttons = (
        (refresh, "modelLabCandidateRefresh"),
        (inspect_evaluation, "modelLabCandidateInspectEvaluation"),
        (preview_export, "modelLabCandidatePreviewExport"),
        (export, "modelLabCandidateExport"),
        (preview_conversion, "modelLabCandidatePreviewConversion"),
        (convert, "modelLabCandidateConvert"),
        (ollama_status, "modelLabCandidateOllamaStatus"),
        (preview_package, "modelLabCandidatePreviewPackage"),
        (package, "modelLabCandidatePackage"),
        (preview_promotion, "modelLabCandidatePreviewPromotion"),
        (promote, "modelLabCandidatePromote"),
        (preview_rollback, "modelLabCandidatePreviewRollback"),
        (rollback, "modelLabCandidateRollback"),
    )
    for button, object_name in buttons:
        mark_accessible(
            button,
            object_name=object_name,
            name=button.text(),
            description=button.text(),
            description_required=True,
        )
        controls.addWidget(button)
    layout.addLayout(controls)

    form = QFormLayout()
    role = QComboBox()
    for value in ("fast", "core", "coder", "embed", "vision"):
        role.addItem(value.title(), value)
    mark_accessible(
        role,
        object_name="modelLabCandidateRole",
        name=tr.text("role"),
        description=tr.text("role"),
        description_required=True,
    )
    form.addRow(tr.text("role"), role)

    confirm = QCheckBox(tr.text("confirm"))
    mark_accessible(
        confirm,
        object_name="modelLabCandidateConfirm",
        name=tr.text("confirm"),
        description=tr.text("confirm"),
        description_required=True,
    )
    form.addRow("", confirm)
    layout.addLayout(form)

    state = QLabel(tr.text("ready"))
    mark_accessible(
        state,
        object_name="modelLabCandidateState",
        name=tr.text("ready"),
        description=tr.text("ready"),
        description_required=True,
    )
    layout.addWidget(state)

    def make_table(name: str, headers: list[str], title: str) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        mark_accessible(
            table,
            object_name=name,
            name=title,
            description=title,
            description_required=True,
        )
        layout.addWidget(QLabel(f"<b>{title}</b>"))
        layout.addWidget(table)
        return table

    candidates = make_table(
        "modelLabCandidateCandidatesTable",
        ["Candidate", "Disposition", "Eval", "Export", "GGUF", "Package", "Critical"],
        tr.text("candidates"),
    )
    domains = make_table(
        "modelLabCandidateDomainsTable",
        ["Candidate", "Domain", "Base", "Candidate", "Delta"],
        tr.text("domains"),
    )
    artifacts = make_table(
        "modelLabCandidateArtifactsTable",
        ["Stage", "Candidate", "Identity", "State", "Detail"],
        tr.text("artifacts"),
    )
    registry = make_table(
        "modelLabCandidateRegistryTable",
        ["Version", "Candidate", "State", "Roles", "Preferred", "Record digest"],
        tr.text("registry"),
    )

    raw = QPlainTextEdit()
    raw.setReadOnly(True)
    mark_accessible(
        raw,
        object_name="modelLabCandidateDiagnostics",
        name=tr.text("raw"),
        description=tr.text("raw"),
        description_required=True,
    )
    layout.addWidget(QLabel(f"<b>{tr.text('raw')}</b>"))
    layout.addWidget(raw)

    page._candidate_payload = {}
    page._candidate_tasks = set()
    pool = QThreadPool.globalInstance()

    def text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "yes" if value else "no"
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        return str(value)

    def set_rows(table: QTableWidget, rows: list[list[str]]) -> None:
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        table.resizeColumnsToContents()

    def selected_candidate() -> str | None:
        row = candidates.currentRow()
        if row < 0:
            return None
        item = candidates.item(row, 0)
        return item.text() if item is not None else None

    def render(payload: Mapping[str, object]) -> None:
        page._candidate_payload = dict(payload)
        candidate_rows: list[list[str]] = []
        for item in payload.get("candidates", []):
            if not isinstance(item, Mapping):
                continue
            candidate_rows.append(
                [
                    text(item.get("candidate_id")),
                    ", ".join(str(value) for value in item.get("evaluation_dispositions", [])),
                    text(item.get("evaluation_count")),
                    text(item.get("export_count")),
                    text(item.get("conversion_count")),
                    text(item.get("package_count")),
                    text(item.get("critical_regression")),
                ]
            )
        set_rows(candidates, candidate_rows)

        domain_rows: list[list[str]] = []
        for evaluation in payload.get("evaluations", []):
            if not isinstance(evaluation, Mapping):
                continue
            candidate_id = text(evaluation.get("candidate_id"))
            for domain_name, domain_value in dict(evaluation.get("domain_deltas", {})).items():
                if not isinstance(domain_value, Mapping):
                    continue
                domain_rows.append(
                    [
                        candidate_id,
                        str(domain_name),
                        text(domain_value.get("base_score")),
                        text(domain_value.get("candidate_score")),
                        text(domain_value.get("delta")),
                    ]
                )
        set_rows(domains, domain_rows)

        artifact_rows: list[list[str]] = []
        for item in payload.get("exports", []):
            if isinstance(item, Mapping):
                artifact_rows.append(
                    [
                        "export",
                        text(item.get("candidate_id")),
                        text(item.get("manifest_digest")),
                        text(item.get("integrity")),
                        text(item.get("merge_disposition")),
                    ]
                )
        for item in payload.get("conversions", []):
            if isinstance(item, Mapping):
                artifact_rows.append(
                    [
                        "gguf",
                        text(item.get("candidate_id")),
                        text(item.get("report_digest")),
                        text(item.get("integrity")),
                        f"accepted_variants={text(item.get('accepted_variants'))}",
                    ]
                )
        for item in payload.get("packages", []):
            if isinstance(item, Mapping):
                artifact_rows.append(
                    [
                        "ollama",
                        text(item.get("candidate_id")),
                        text(item.get("report_digest")),
                        text(item.get("integrity")),
                        f"{text(item.get('quality'))} / {text(item.get('candidate_tag'))}",
                    ]
                )
        set_rows(artifacts, artifact_rows)

        registry_payload = payload.get("registry", {})
        registry_rows: list[list[str]] = []
        if isinstance(registry_payload, Mapping):
            for item in registry_payload.get("records", []):
                if not isinstance(item, Mapping):
                    continue
                registry_rows.append(
                    [
                        text(item.get("version_id")),
                        text(item.get("candidate_id")),
                        text(item.get("state")),
                        ", ".join(str(value) for value in item.get("roles", [])),
                        text(item.get("preferred_variant")),
                        text(item.get("record_digest")),
                    ]
                )
        set_rows(registry, registry_rows)
        raw.setPlainText(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True))

    def set_state(message: str) -> None:
        state.setText(message)
        state.setAccessibleName(message)
        if status_bar is not None:
            status_bar.showMessage(message)

    def refresh_now() -> None:
        try:
            payload = ux.snapshot()
        except Exception as exc:
            set_state(f"{tr.text('blocked')}: {type(exc).__name__}: {exc}")
            return
        render(payload)
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
                self.signals.failed.emit(f"{type(exc).__name__}: {exc}")

    def run_action(operation: Callable[[], object], *, refresh_after: bool = False) -> None:
        set_state(tr.text("running"))
        task = Task(operation)
        page._candidate_tasks.add(task)

        def finish(result: object) -> None:
            raw.setPlainText(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            if refresh_after:
                refresh_now()
            else:
                set_state(tr.text("complete"))
            page._candidate_tasks.discard(task)

        def fail(detail: str) -> None:
            raw.setPlainText(detail)
            set_state(f"{tr.text('blocked')}: {detail}")
            page._candidate_tasks.discard(task)

        task.signals.done.connect(finish)
        task.signals.failed.connect(fail)
        pool.start(task)

    def require_candidate() -> str | None:
        value = selected_candidate()
        if value is None:
            set_state(tr.text("select_candidate"))
        return value

    def candidate_action(operation: Callable[[str], object], *, refresh_after: bool = False) -> None:
        candidate = require_candidate()
        if candidate:
            run_action(lambda: operation(candidate), refresh_after=refresh_after)

    refresh.clicked.connect(refresh_now)
    inspect_evaluation.clicked.connect(lambda: candidate_action(ux.inspect_evaluation))
    preview_export.clicked.connect(lambda: candidate_action(ux.preview_export))
    export.clicked.connect(
        lambda: candidate_action(
            lambda candidate: ux.export_candidate(candidate, confirmed=confirm.isChecked()),
            refresh_after=True,
        )
    )
    preview_conversion.clicked.connect(lambda: candidate_action(ux.preview_conversion))
    convert.clicked.connect(
        lambda: candidate_action(
            lambda candidate: ux.run_conversion(candidate, confirmed=confirm.isChecked()),
            refresh_after=True,
        )
    )
    ollama_status.clicked.connect(lambda: run_action(ux.inspect_ollama))
    preview_package.clicked.connect(lambda: candidate_action(ux.preview_package))
    package.clicked.connect(
        lambda: candidate_action(
            lambda candidate: ux.package_candidate(candidate, confirmed=confirm.isChecked()),
            refresh_after=True,
        )
    )
    preview_promotion.clicked.connect(
        lambda: candidate_action(
            lambda candidate: ux.preview_promotion(candidate, str(role.currentData()))
        )
    )
    promote.clicked.connect(
        lambda: candidate_action(
            lambda candidate: ux.promote(
                candidate,
                str(role.currentData()),
                confirmed=confirm.isChecked(),
            ),
            refresh_after=True,
        )
    )
    preview_rollback.clicked.connect(
        lambda: run_action(lambda: ux.preview_rollback(str(role.currentData())))
    )
    rollback.clicked.connect(
        lambda: run_action(
            lambda: ux.rollback(str(role.currentData()), confirmed=confirm.isChecked()),
            refresh_after=True,
        )
    )

    refresh_now()
    return page


__all__ = ["create_model_lab_candidate_page"]
