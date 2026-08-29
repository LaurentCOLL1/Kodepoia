from __future__ import annotations

from pathlib import Path

from kodepoia.backend.contracts import BackendEnvironmentKind
from kodepoia.backend.liveops_ux import (
    BackendLiveOpsUXService,
    LiveOpsMode,
    LiveOpsOperation,
    LiveOpsUXPolicyError,
    LiveOpsUXRequest,
    stable_liveops_json,
)
from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.r14_localization import R14Translator


def create_backend_liveops_page(
    project_root: Path,
    *,
    locale: str = "en",
    service: BackendLiveOpsUXService | None = None,
    status_bar=None,
):
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

    tr = R14Translator(locale)
    liveops = service or BackendLiveOpsUXService.for_project(project_root)
    catalog = liveops.catalog()
    operation_catalog = catalog["operations"]

    page = QWidget()
    mark_accessible(
        page,
        object_name="backendLiveOpsPage",
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
    environment = QComboBox()
    mark_accessible(
        environment,
        object_name="r14Environment",
        name=tr.text("environment"),
        description="Explicit backend environment boundary.",
        description_required=True,
    )
    for item in BackendEnvironmentKind:
        environment.addItem(item.value, item.value)
    form.addRow(tr.text("environment"), environment)

    operation = QComboBox()
    mark_accessible(
        operation,
        object_name="r14Operation",
        name=tr.text("operation"),
        description="Typed R14 domain operation; no raw command entry.",
        description_required=True,
    )
    for item in LiveOpsOperation:
        operation.addItem(item.value.replace("_", " ").title(), item.value)
    form.addRow(tr.text("operation"), operation)

    action = QComboBox()
    mark_accessible(
        action,
        object_name="r14Action",
        name=tr.text("action"),
        description="Allowed structured action for the selected operation.",
        description_required=True,
    )
    form.addRow(tr.text("action"), action)

    mode = QComboBox()
    mark_accessible(
        mode,
        object_name="r14Mode",
        name=tr.text("mode"),
        description="Inspect, preview, apply or rollback policy mode.",
        description_required=True,
    )
    form.addRow(tr.text("mode"), mode)

    resource = QLineEdit()
    resource.setPlaceholderText(tr.text("resource_hint"))
    mark_accessible(
        resource,
        object_name="r14ResourceId",
        name=tr.text("resource"),
        description=tr.text("resource_hint"),
        description_required=True,
    )
    form.addRow(tr.text("resource"), resource)

    confirm = QCheckBox(tr.text("confirm"))
    mark_accessible(
        confirm,
        object_name="r14ConfirmMutation",
        name=tr.text("confirm"),
        description="User confirmation only; domain authorization remains mandatory.",
        description_required=True,
    )
    form.addRow("", confirm)
    layout.addLayout(form)

    buttons = QHBoxLayout()
    show_catalog = QPushButton(tr.text("catalog"))
    mark_accessible(
        show_catalog,
        object_name="r14CatalogButton",
        name=tr.text("catalog"),
        description="Show the stable R14.16 capability and safety catalog.",
        description_required=True,
    )
    execute = QPushButton(tr.text("execute"))
    mark_accessible(
        execute,
        object_name="r14ExecuteButton",
        name=tr.text("execute"),
        description="Execute only the selected typed operation through the governed domain port.",
        description_required=True,
    )
    buttons.addWidget(show_catalog)
    buttons.addWidget(execute)
    layout.addLayout(buttons)

    result = QPlainTextEdit()
    result.setReadOnly(True)
    result.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    mark_accessible(
        result,
        object_name="r14StructuredResult",
        name=tr.text("result"),
        description="Redacted stable JSON result for the selected Backend or LiveOps operation.",
        description_required=True,
    )
    layout.addWidget(QLabel(tr.text("result")))
    layout.addWidget(result, 1)

    def set_status(message: str) -> None:
        if status_bar is not None:
            status_bar.showMessage(message)

    def sync_policy() -> None:
        selected = str(operation.currentData())
        policy = operation_catalog[selected]
        action.clear()
        for item in policy["actions"]:
            action.addItem(str(item), str(item))
        mode.clear()
        modes = [str(item) for item in policy["modes"]]
        for item in modes:
            mode.addItem(item, item)
        preferred = "preview" if "preview" in modes else modes[0]
        mode.setCurrentIndex(mode.findData(preferred))
        resource.setEnabled(bool(policy["resource_required"]))
        if not resource.isEnabled():
            resource.clear()
        confirm.setChecked(False)
        confirm.setEnabled(any(item in {"apply", "rollback"} for item in modes))

    def sync_action_mode() -> None:
        operation_value = str(operation.currentData())
        action_value = str(action.currentData())
        preferred: str | None = None
        if operation_value == LiveOpsOperation.LOCAL_STACK.value:
            preferred = "inspect" if action_value == "status" else "apply"
        elif operation_value == LiveOpsOperation.MIGRATION.value:
            preferred = "preview" if action_value == "plan" else "apply"
        elif operation_value in {
            LiveOpsOperation.REMOTE_CONFIG.value,
            LiveOpsOperation.CONTENT.value,
            LiveOpsOperation.CAMPAIGN.value,
        }:
            preferred = {
                "preview": "preview",
                "rollout": "apply",
                "rollback": "rollback",
            }.get(action_value)
        if preferred is not None:
            index = mode.findData(preferred)
            if index >= 0:
                mode.setCurrentIndex(index)
        confirm.setChecked(False)

    def run_operation() -> None:
        try:
            request = LiveOpsUXRequest(
                operation=LiveOpsOperation(str(operation.currentData())),
                environment=BackendEnvironmentKind(str(environment.currentData())),
                mode=LiveOpsMode(str(mode.currentData())),
                action=str(action.currentData()),
                resource_id=resource.text().strip() or None,
                confirmed=confirm.isChecked(),
            )
            payload = liveops.execute(request)
        except LiveOpsUXPolicyError as exc:
            payload = {
                "schema": "kodepoia.r14.liveops-ux.v1",
                "status": "blocked",
                "reason": "policy_error",
                "detail": str(exc),
                "redacted": True,
            }
        result.setPlainText(stable_liveops_json(payload))
        if payload.get("status") == "blocked":
            set_status(tr.text("status_blocked"))
        else:
            set_status(tr.text("status_complete"))

    def show_catalog_payload() -> None:
        result.setPlainText(stable_liveops_json(catalog))
        set_status(tr.text("status_complete"))

    operation.currentIndexChanged.connect(sync_policy)
    action.currentIndexChanged.connect(sync_action_mode)
    execute.clicked.connect(run_operation)
    show_catalog.clicked.connect(show_catalog_payload)
    sync_policy()
    set_status(tr.text("status_ready"))
    return page
