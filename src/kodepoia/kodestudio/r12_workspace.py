from __future__ import annotations

import json
from pathlib import Path

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.desktop.workspace import (
    DesktopWorkspaceOperation,
    DesktopWorkspaceResult,
    DesktopWorkspaceService,
)
from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.r12_localization import R12Translator


def create_r12_workspace_page(
    project_root: Path,
    *,
    translator: R12Translator,
    service: DesktopWorkspaceService | None = None,
    status_bar=None,
    kill_switch: KillSwitch | None = None,
):
    from PySide6.QtWidgets import (
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    switch = kill_switch or GLOBAL_KILL_SWITCH
    workspace = service or DesktopWorkspaceService(project_root, kill_switch=switch)
    page = QWidget()
    page.setObjectName("r12DesktopWorkspace")
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(f"<h2>{translator.text('r12.title')}</h2>"))
    description = QLabel(translator.text("r12.description"))
    description.setWordWrap(True)
    layout.addWidget(description)

    form = QFormLayout()
    project_value = QLabel("—")
    framework_value = QLabel("—")
    architecture_value = QLabel("—")
    package_value = QLabel("—")
    state_value = QLabel(translator.text("r12.idle"))
    blockers_value = QLabel("—")
    blockers_value.setWordWrap(True)
    for object_name, widget, accessible_name in (
        ("r12Project", project_value, translator.text("r12.project")),
        ("r12Framework", framework_value, translator.text("r12.framework")),
        ("r12Architecture", architecture_value, translator.text("r12.architecture")),
        ("r12Package", package_value, translator.text("r12.package")),
        ("r12State", state_value, translator.text("r12.state")),
        ("r12Blockers", blockers_value, translator.text("r12.blockers")),
    ):
        mark_accessible(widget, object_name=object_name, name=accessible_name)
    form.addRow(translator.text("r12.project"), project_value)
    form.addRow(translator.text("r12.framework"), framework_value)
    form.addRow(translator.text("r12.architecture"), architecture_value)
    form.addRow(translator.text("r12.package"), package_value)
    form.addRow(translator.text("r12.state"), state_value)
    form.addRow(translator.text("r12.blockers"), blockers_value)
    layout.addLayout(form)

    evidence = QPlainTextEdit()
    evidence.setReadOnly(True)
    mark_accessible(
        evidence,
        object_name="r12Evidence",
        name=translator.text("r12.evidence"),
        description=(
            "Read-only evidence snapshot. Reported status fields are displayed as data "
            "and cannot be edited into workspace PASS."
        ),
        description_required=True,
    )
    layout.addWidget(evidence)

    def render(result: DesktopWorkspaceResult) -> None:
        project_value.setText(result.project_name or "—")
        framework_value.setText(result.framework or "—")
        architecture_value.setText(result.architecture or "—")
        package_value.setText(result.package_kind or "—")
        state_text = translator.text(
            "r12.result",
            operation=result.operation.value,
            state=result.state.value.upper(),
            summary=result.summary,
        )
        state_value.setText(state_text)
        state_value.setAccessibleName(state_text)
        blockers_value.setText(", ".join(result.blockers) if result.blockers else "—")
        evidence.setPlainText(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        if status_bar is not None:
            status_bar.showMessage(state_text)

    def run(operation: DesktopWorkspaceOperation) -> None:
        render(workspace.execute(operation))

    buttons = QHBoxLayout()
    button_specs = (
        ("r12Refresh", "r12.refresh", DesktopWorkspaceOperation.STATUS),
        ("r12Validate", "r12.validate", DesktopWorkspaceOperation.VALIDATE),
        ("r12Scaffold", "r12.scaffold", DesktopWorkspaceOperation.SCAFFOLD),
        ("r12Build", "r12.build", DesktopWorkspaceOperation.BUILD),
        ("r12Test", "r12.test", DesktopWorkspaceOperation.TEST),
        ("r12PackageAction", "r12.package_action", DesktopWorkspaceOperation.PACKAGE),
    )
    for object_name, message_id, operation in button_specs:
        button = QPushButton(translator.text(message_id))
        mark_accessible(
            button,
            object_name=object_name,
            name=translator.text(message_id),
            description=(
                "Refresh reads local Project DNA and evidence only; it never probes or launches external tools."
                if operation is DesktopWorkspaceOperation.STATUS
                else f"Explicit governed desktop {operation.value} intent."
            ),
            description_required=True,
        )
        button.clicked.connect(lambda _checked=False, op=operation: run(op))
        buttons.addWidget(button)

    cancel = QPushButton(translator.text("r12.cancel"))
    mark_accessible(
        cancel,
        object_name="r12Cancel",
        name=translator.text("r12.cancel"),
        description="Trigger the global KillSwitch for protected desktop execution.",
        description_required=True,
    )

    def cancel_protected() -> None:
        count = workspace.cancel()
        text = translator.text("r12.cancelled", count=count)
        state_value.setText(text)
        state_value.setAccessibleName(text)
        if status_bar is not None:
            status_bar.showMessage(text)

    cancel.clicked.connect(cancel_protected)
    buttons.addWidget(cancel)
    layout.addLayout(buttons)
    layout.addStretch(1)

    # Initial population is deliberately passive: status() performs no external probe.
    render(workspace.status())
    page._kodepoia_r12_service = workspace
    page._kodepoia_r12_evidence = evidence
    return page


__all__ = ["create_r12_workspace_page"]
