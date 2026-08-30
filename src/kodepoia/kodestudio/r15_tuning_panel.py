from __future__ import annotations

from pathlib import Path

from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.r15_localization import R15Translator
from kodepoia.tuning.r15_ux import (
    R15UXPolicyError,
    R15UXService,
    R15WorkflowMode,
    R15WorkflowRequest,
    stable_r15_json,
)


def create_r15_tuning_page(
    project_root: Path,
    *,
    locale: str = "en",
    service: R15UXService | None = None,
    status_bar=None,
):
    from PySide6.QtCore import QObject, QThread, Signal, Slot
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    tr = R15Translator(locale)
    ux = service or R15UXService.for_project(project_root)
    page = QWidget()
    mark_accessible(
        page,
        object_name="r15TuningPage",
        name=tr.text("title"),
        description=tr.text("subtitle"),
        description_required=True,
    )
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(f"<h2>{tr.text('title')}</h2>"))
    subtitle = QLabel(tr.text("subtitle"))
    subtitle.setWordWrap(True)
    layout.addWidget(subtitle)

    form = QFormLayout()
    domain = QComboBox()
    mark_accessible(
        domain,
        object_name="r15Domain",
        name=tr.text("domain"),
        description="Select one frozen R15 workflow domain.",
        description_required=True,
    )
    domains = sorted({spec.domain for spec in ux.actions()})
    for value in domains:
        domain.addItem(value.replace("_", " ").title(), value)
    form.addRow(tr.text("domain"), domain)

    action = QComboBox()
    mark_accessible(
        action,
        object_name="r15Action",
        name=tr.text("action"),
        description="Select one typed R15 action; arbitrary commands are not accepted.",
        description_required=True,
    )
    form.addRow(tr.text("action"), action)

    identifier = QLineEdit()
    identifier.setPlaceholderText(tr.text("identifier_hint"))
    mark_accessible(
        identifier,
        object_name="r15StableIdentifier",
        name=tr.text("identifier"),
        description=tr.text("identifier_hint"),
        description_required=True,
    )
    form.addRow(tr.text("identifier"), identifier)

    confirm = QCheckBox(tr.text("confirm"))
    mark_accessible(
        confirm,
        object_name="r15ConfirmMutation",
        name=tr.text("confirm"),
        description="Explicit user confirmation only; configured backend authorization remains mandatory.",
        description_required=True,
    )
    form.addRow("", confirm)
    layout.addLayout(form)

    buttons = QHBoxLayout()
    catalog_button = QPushButton(tr.text("catalog"))
    status_button = QPushButton(tr.text("status"))
    evidence_button = QPushButton(tr.text("evidence"))
    dry_run_button = QPushButton(tr.text("dry_run"))
    execute_button = QPushButton(tr.text("execute"))
    for widget, object_name, description in (
        (catalog_button, "r15CatalogButton", "Show the stable R15 workflow catalog."),
        (status_button, "r15StatusButton", "Inspect redacted persisted R15 evidence status."),
        (evidence_button, "r15EvidenceButton", "Export redacted R15 UX evidence inside the project root."),
        (dry_run_button, "r15DryRunButton", "Preview the selected request without mutation."),
        (execute_button, "r15ExecuteButton", "Execute the selected governed action with policy checks."),
    ):
        mark_accessible(
            widget,
            object_name=object_name,
            name=widget.text(),
            description=description,
            description_required=True,
        )
        buttons.addWidget(widget)
    layout.addLayout(buttons)

    result = QPlainTextEdit()
    result.setReadOnly(True)
    result.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    mark_accessible(
        result,
        object_name="r15StructuredResult",
        name=tr.text("result"),
        description="Read-only redacted JSON. Raw secrets and quarantined payload content are not displayed.",
        description_required=True,
    )
    layout.addWidget(QLabel(tr.text("result")))
    layout.addWidget(result, 1)

    def set_status(message: str) -> None:
        if status_bar is not None:
            status_bar.showMessage(message)

    def render(payload: object) -> None:
        if isinstance(payload, dict):
            result.setPlainText(stable_r15_json(payload))
        else:
            result.setPlainText(str(payload))

    def sync_actions() -> None:
        selected_domain = str(domain.currentData())
        action.clear()
        for spec in ux.actions():
            if spec.domain == selected_domain:
                action.addItem(spec.action.replace("_", " ").title(), spec.action)
        sync_policy()

    def selected_spec():
        return ux.action(str(domain.currentData()), str(action.currentData()))

    def sync_policy() -> None:
        if action.currentData() is None:
            return
        spec = selected_spec()
        identifier.setEnabled(spec.identifier_required or spec.mutation)
        if not identifier.isEnabled():
            identifier.clear()
        confirm.setEnabled(spec.mutation)
        if not spec.mutation:
            confirm.setChecked(False)

    class Worker(QObject):
        finished = Signal(object)
        failed = Signal(str)

        def __init__(self, request: R15WorkflowRequest) -> None:
            super().__init__()
            self.request = request

        @Slot()
        def run(self) -> None:
            try:
                self.finished.emit(ux.execute(self.request))
            except Exception as exc:  # UI boundary converts failures into redacted status text.
                self.failed.emit(str(exc))

    def finish_thread() -> None:
        page._r15_worker = None
        page._r15_thread = None
        dry_run_button.setEnabled(True)
        execute_button.setEnabled(True)

    def on_success(payload: object) -> None:
        render(payload)
        set_status(tr.text("status_complete"))

    def on_failure(detail: str) -> None:
        render(
            {
                "schema": R15UXService.schema,
                "status": "blocked",
                "reason": "policy_error",
                "detail": detail,
                "redacted": True,
            }
        )
        set_status(tr.text("status_blocked"))

    def run_async(mode: R15WorkflowMode) -> None:
        current = getattr(page, "_r15_thread", None)
        if current is not None and current.isRunning():
            return
        spec = selected_spec()
        request = R15WorkflowRequest(
            domain=spec.domain,
            action=spec.action,
            mode=mode,
            identifier=identifier.text().strip() or None,
            confirmed=confirm.isChecked(),
        )
        thread = QThread(page)
        worker = Worker(request)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(on_success)
        worker.failed.connect(on_failure)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(finish_thread)
        page._r15_thread = thread
        page._r15_worker = worker
        dry_run_button.setEnabled(False)
        execute_button.setEnabled(False)
        set_status(tr.text("status_running"))
        thread.start()

    def run_dry() -> None:
        run_async(R15WorkflowMode.DRY_RUN)

    def run_execute() -> None:
        spec = selected_spec()
        mode = spec.terminal_mode if spec.mutation else R15WorkflowMode.INSPECT
        run_async(mode)

    def show_catalog() -> None:
        render(ux.catalog())
        set_status(tr.text("status_complete"))

    def show_status() -> None:
        render(ux.status())
        set_status(tr.text("status_complete"))

    def export_evidence() -> None:
        try:
            payload = ux.export_evidence(Path(".kodepoia/tuning/r15-ux-evidence.json"))
        except R15UXPolicyError as exc:
            on_failure(str(exc))
            return
        render(payload)
        set_status(tr.text("status_complete"))

    domain.currentIndexChanged.connect(sync_actions)
    action.currentIndexChanged.connect(sync_policy)
    catalog_button.clicked.connect(show_catalog)
    status_button.clicked.connect(show_status)
    evidence_button.clicked.connect(export_evidence)
    dry_run_button.clicked.connect(run_dry)
    execute_button.clicked.connect(run_execute)
    sync_actions()
    set_status(tr.text("status_ready"))
    return page
