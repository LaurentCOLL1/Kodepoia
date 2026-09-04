from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from kodepoia.kodestudio.v11_localization import V11Translator
from kodepoia.kodestudio.vision_assistant import (
    VisionAssistant,
    VisionAssistantResult,
    VisionDraft,
    save_vision_draft,
)


def _draft_text(draft: VisionDraft, *, locale: str) -> str:
    french = locale.lower().startswith("fr")
    labels = (
        ("Résumé", "Summary", draft.summary),
        ("Objectifs", "Goals", draft.goals),
        ("Indicateurs de réussite", "Success metrics", draft.success_metrics),
        ("Contraintes", "Constraints", draft.constraints),
        ("MVP", "MVP", draft.mvp),
        ("Hors périmètre", "Out of scope", draft.out_of_scope),
    )
    chunks: list[str] = []
    for label_fr, label_en, value in labels:
        label = label_fr if french else label_en
        if isinstance(value, str):
            if value:
                chunks.append(f"**{label}**\n{value}")
        elif value:
            chunks.append(f"**{label}**\n" + "\n".join(f"- {item}" for item in value))
    if draft.requirements:
        title = "Exigences et critères d'acceptation" if french else "Requirements and acceptance criteria"
        lines = [f"**{title}**"]
        for requirement in draft.requirements:
            lines.append(f"- {requirement.id} [{requirement.priority}] {requirement.title}")
            if requirement.description:
                lines.append(f"  {requirement.description}")
            for criterion in requirement.acceptance_criteria:
                lines.append(f"  - ✓ {criterion}")
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks)


def create_vision_chat_page(
    project_root: Path | None = None,
    *,
    locale: str = "fr",
    assistant: VisionAssistant | None = None,
    initial_draft: VisionDraft | None = None,
    apply_callback: Callable[[VisionDraft], None] | None = None,
):
    from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
    from PySide6.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    tr = V11Translator(locale)
    service = assistant or VisionAssistant()

    class WorkerSignals(QObject):
        done = Signal(object)
        error = Signal(str)

    class RefineTask(QRunnable):
        def __init__(self, text: str, model: str | None, draft: VisionDraft) -> None:
            super().__init__()
            self.text = text
            self.model = model
            self.draft = draft
            self.signals = WorkerSignals()

        def run(self) -> None:
            try:
                result = service.refine(
                    self.text,
                    current=self.draft,
                    model=self.model,
                    locale=locale,
                )
            except Exception as exc:  # UI boundary: surface a redacted human error.
                self.signals.error.emit(str(exc))
            else:
                self.signals.done.emit(result)

    page = QWidget()
    page.setObjectName("visionChatPage")
    page.setAccessibleName(tr.text("chat.title"))
    layout = QVBoxLayout(page)

    title = QLabel(f"<h2>{tr.text('chat.title')}</h2>")
    intro = QLabel(tr.text("chat.intro"))
    intro.setWordWrap(True)
    layout.addWidget(title)
    layout.addWidget(intro)

    model_row = QHBoxLayout()
    model_row.addWidget(QLabel(tr.text("chat.model")))
    model_combo = QComboBox()
    model_combo.setObjectName("visionModelSelector")
    model_combo.setAccessibleName(tr.text("chat.model"))
    model_row.addWidget(model_combo, 1)
    refresh = QPushButton(tr.text("chat.refresh"))
    refresh.setObjectName("refreshVisionModelsButton")
    model_row.addWidget(refresh)
    layout.addLayout(model_row)

    transcript = QPlainTextEdit()
    transcript.setObjectName("visionChatTranscript")
    transcript.setReadOnly(True)
    transcript.setAccessibleName(tr.text("chat.title"))
    transcript.setPlaceholderText(tr.text("chat.intro"))
    layout.addWidget(transcript, 3)

    message = QPlainTextEdit()
    message.setObjectName("visionChatInput")
    message.setAccessibleName(tr.text("chat.input"))
    message.setPlaceholderText(tr.text("chat.input"))
    message.setMaximumHeight(130)
    layout.addWidget(message, 1)

    actions = QHBoxLayout()
    send = QPushButton(tr.text("chat.send"))
    send.setObjectName("visionChatSendButton")
    clear = QPushButton(tr.text("chat.clear"))
    clear.setObjectName("visionChatClearButton")
    save = QPushButton(tr.text("chat.save"))
    save.setObjectName("visionChatSaveButton")
    apply_button = QPushButton(tr.text("chat.apply"))
    apply_button.setObjectName("visionChatApplyButton")
    apply_button.setVisible(apply_callback is not None)
    actions.addWidget(send)
    actions.addWidget(clear)
    actions.addWidget(save)
    actions.addWidget(apply_button)
    actions.addStretch(1)
    layout.addLayout(actions)

    state: dict[str, object] = {
        "draft": initial_draft or VisionDraft(),
        "last_result": None,
        "workers": [],
    }
    pool = QThreadPool.globalInstance()

    def refresh_models() -> None:
        current = model_combo.currentData()
        model_combo.clear()
        model_combo.addItem(tr.text("chat.guided"), None)
        for model_name in service.available_models():
            model_combo.addItem(model_name, model_name)
        if current:
            index = model_combo.findData(current)
            if index >= 0:
                model_combo.setCurrentIndex(index)

    def append(role: str, text: str) -> None:
        transcript.appendPlainText(f"{role}\n{text}\n")

    def handle_result(value: object) -> None:
        send.setEnabled(True)
        if not isinstance(value, VisionAssistantResult):
            return
        state["last_result"] = value
        state["draft"] = value.draft
        assistant_label = "Kodepoia"
        blocks = [value.assistant_message, _draft_text(value.draft, locale=locale)]
        if value.clarifying_questions:
            question_title = "Précisions demandées" if locale.startswith("fr") else "Clarifications"
            blocks.append(
                question_title + "\n" + "\n".join(f"• {q}" for q in value.clarifying_questions)
            )
        append(assistant_label, "\n\n".join(block for block in blocks if block))

    def handle_error(reason: str) -> None:
        send.setEnabled(True)
        append("Kodepoia", tr.text("chat.error", reason=reason))

    def submit() -> None:
        text = message.toPlainText().strip()
        if not text:
            return
        append("Vous" if locale.startswith("fr") else "You", text)
        message.clear()
        send.setEnabled(False)
        model = model_combo.currentData()
        worker = RefineTask(text, str(model) if model else None, state["draft"])
        worker.signals.done.connect(handle_result)
        worker.signals.error.connect(handle_error)
        state["workers"].append(worker)
        pool.start(worker)

    def clear_session() -> None:
        state["draft"] = VisionDraft()
        state["last_result"] = None
        transcript.clear()

    def save_session() -> None:
        root = project_root
        if root is None or not (root / ".kodepoia").exists():
            QMessageBox.information(page, "Kodepoia", tr.text("chat.no_project"))
            return
        result = state.get("last_result")
        if not isinstance(result, VisionAssistantResult):
            result = VisionAssistantResult(draft=state["draft"])
        path = save_vision_draft(root / ".kodepoia" / "vision" / "draft.json", result)
        QMessageBox.information(page, "Kodepoia", tr.text("chat.saved", path=str(path)))

    def apply_session() -> None:
        if apply_callback is not None:
            apply_callback(state["draft"])

    refresh.clicked.connect(refresh_models)
    send.clicked.connect(submit)
    clear.clicked.connect(clear_session)
    save.clicked.connect(save_session)
    apply_button.clicked.connect(apply_session)

    page._kodepoia_vision_state = state
    page._kodepoia_refresh_models = refresh_models
    page._kodepoia_submit = submit
    page._kodepoia_apply = apply_session
    refresh_models()
    return page


def create_vision_assistant_dialog(
    parent=None,
    *,
    locale: str = "fr",
    initial_draft: VisionDraft | None = None,
    apply_callback: Callable[[VisionDraft], None] | None = None,
):
    from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout

    tr = V11Translator(locale)
    dialog = QDialog(parent)
    dialog.setObjectName("visionAssistantDialog")
    dialog.setWindowTitle(tr.text("wizard.vision.title"))
    dialog.resize(900, 700)
    layout = QVBoxLayout(dialog)

    def apply_and_accept(draft: VisionDraft) -> None:
        if apply_callback is not None:
            apply_callback(draft)
        dialog.accept()

    page = create_vision_chat_page(
        None,
        locale=locale,
        initial_draft=initial_draft,
        apply_callback=apply_and_accept,
    )
    layout.addWidget(page)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(dialog.reject)
    buttons.clicked.connect(lambda *_: dialog.reject())
    layout.addWidget(buttons)
    dialog._kodepoia_vision_page = page
    return dialog


__all__ = ["create_vision_assistant_dialog", "create_vision_chat_page"]
