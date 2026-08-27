from __future__ import annotations

import json
from pathlib import Path

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.kodestudio.accessibility import mark_accessible
from kodepoia.kodestudio.r13_localization import R13Translator
from kodepoia.mobile.workspace import (
    MobileWorkspaceOperation,
    MobileWorkspaceResult,
    MobileWorkspaceService,
)


def create_r13_workspace_page(
    project_root: Path,
    *,
    translator: R13Translator,
    service: MobileWorkspaceService | None = None,
    status_bar=None,
    kill_switch: KillSwitch | None = None,
):
    from PySide6.QtWidgets import (
        QFormLayout,
        QGridLayout,
        QLabel,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    switch = kill_switch or GLOBAL_KILL_SWITCH
    workspace = service or MobileWorkspaceService(project_root, kill_switch=switch)
    page = QWidget()
    page.setObjectName("r13MobileWorkspace")
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(f"<h2>{translator.text('r13.title')}</h2>"))
    description = QLabel(translator.text("r13.description"))
    description.setWordWrap(True)
    layout.addWidget(description)

    form = QFormLayout()
    project_value = QLabel("—")
    platforms_value = QLabel("—")
    source_value = QLabel("—")
    channel_value = QLabel("—")
    signing_value = QLabel("—")
    state_value = QLabel(translator.text("r13.idle"))
    blockers_value = QLabel("—")
    blockers_value.setWordWrap(True)
    for object_name, widget, accessible_name in (
        ("r13Project", project_value, translator.text("r13.project")),
        ("r13Platforms", platforms_value, translator.text("r13.platforms")),
        ("r13Source", source_value, translator.text("r13.source")),
        ("r13Channel", channel_value, translator.text("r13.channel")),
        ("r13Signing", signing_value, translator.text("r13.signing")),
        ("r13State", state_value, translator.text("r13.state")),
        ("r13Blockers", blockers_value, translator.text("r13.blockers")),
    ):
        mark_accessible(widget, object_name=object_name, name=accessible_name)
    form.addRow(translator.text("r13.project"), project_value)
    form.addRow(translator.text("r13.platforms"), platforms_value)
    form.addRow(translator.text("r13.source"), source_value)
    form.addRow(translator.text("r13.channel"), channel_value)
    form.addRow(translator.text("r13.signing"), signing_value)
    form.addRow(translator.text("r13.state"), state_value)
    form.addRow(translator.text("r13.blockers"), blockers_value)
    layout.addLayout(form)

    evidence = QPlainTextEdit()
    evidence.setReadOnly(True)
    mark_accessible(
        evidence,
        object_name="r13Evidence",
        name=translator.text("r13.evidence"),
        description=(
            "Read-only R13 capability and evidence snapshot. Reported status values are data; "
            "this control cannot edit evidence or manufacture PASS."
        ),
        description_required=True,
    )
    layout.addWidget(evidence)

    def render(result: MobileWorkspaceResult) -> None:
        project_value.setText(result.project_name or "—")
        platforms_value.setText(", ".join(result.platforms) if result.platforms else "—")
        source_value.setText(result.source_kind or "—")
        channel_value.setText(result.release_channel or "—")
        signing_value.setText(result.signing_intent or "—")
        state_text = translator.text(
            "r13.result",
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

    def run(operation: MobileWorkspaceOperation) -> None:
        render(workspace.execute(operation))

    buttons = QGridLayout()
    button_specs = (
        ("r13Refresh", "r13.refresh", MobileWorkspaceOperation.STATUS),
        ("r13Scaffold", "r13.scaffold", MobileWorkspaceOperation.SCAFFOLD),
        ("r13Build", "r13.build", MobileWorkspaceOperation.BUILD),
        ("r13Test", "r13.test", MobileWorkspaceOperation.TEST),
        ("r13Package", "r13.package", MobileWorkspaceOperation.PACKAGE),
        ("r13Device", "r13.device", MobileWorkspaceOperation.DEVICE),
        ("r13Compliance", "r13.compliance", MobileWorkspaceOperation.COMPLIANCE),
        ("r13Release", "r13.release", MobileWorkspaceOperation.RELEASE),
    )
    for index, (object_name, message_id, operation) in enumerate(button_specs):
        button = QPushButton(translator.text(message_id))
        mark_accessible(
            button,
            object_name=object_name,
            name=translator.text(message_id),
            description=(
                "Passive refresh reads owned Project DNA and bounded evidence only; it never launches or probes an external tool."
                if operation is MobileWorkspaceOperation.STATUS
                else f"Explicit governed R13 {operation.value} intent; no raw tool or credential input is exposed."
            ),
            description_required=True,
        )
        button.clicked.connect(lambda _checked=False, op=operation: run(op))
        buttons.addWidget(button, index // 4, index % 4)

    cancel = QPushButton(translator.text("r13.cancel"))
    mark_accessible(
        cancel,
        object_name="r13Cancel",
        name=translator.text("r13.cancel"),
        description="Trigger the global KillSwitch for protected R13 execution.",
        description_required=True,
    )

    def cancel_protected() -> None:
        count = workspace.cancel()
        text = translator.text("r13.cancelled", count=count)
        state_value.setText(text)
        state_value.setAccessibleName(text)
        if status_bar is not None:
            status_bar.showMessage(text)

    cancel.clicked.connect(cancel_protected)
    buttons.addWidget(cancel, 2, 0, 1, 4)
    layout.addLayout(buttons)
    layout.addStretch(1)

    # Initial population is deliberately passive: status() launches no external process.
    render(workspace.status())
    page._kodepoia_r13_service = workspace
    page._kodepoia_r13_evidence = evidence
    return page


__all__ = ["create_r13_workspace_page"]
