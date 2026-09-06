from __future__ import annotations

import contextlib
import json
import os
import sys
from pathlib import Path

from kodepoia.kodestudio.v11_localization import V11Translator, resolve_locale
from kodepoia.kodestudio.vision_assistant import VisionDraft
from kodepoia.release_identity import CURRENT_RELEASE

SETTINGS_PATH = Path.home() / ".kodepoia" / "settings.json"


def _load_saved_locale() -> str | None:
    try:
        payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = payload.get("locale") if isinstance(payload, dict) else None
    return str(value) if value else None


def _save_locale(locale: str) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps({"locale": locale}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def selected_locale(requested: str | None = None) -> str:
    return resolve_locale(requested or os.environ.get("KODEPOIA_LOCALE") or _load_saved_locale())


def _replace_stack_page(stack, index: int, widget) -> None:
    old = stack.widget(index)
    stack.removeWidget(old)
    stack.insertWidget(index, widget)
    old.deleteLater()


def _settings_page(locale: str, *, update_service=None, update_settings=None):
    from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QVBoxLayout, QWidget

    from kodepoia.kodestudio.update_settings import create_update_settings_group

    tr = V11Translator(locale)
    page = QWidget()
    page.setObjectName("v11SettingsPage")
    layout = QVBoxLayout(page)
    title = QLabel(f"<h2>{tr.text('nav.settings')}</h2>")
    layout.addWidget(title)
    form = QFormLayout()
    language = QComboBox()
    language.setObjectName("applicationLanguageSelector")
    language.addItem("Français", "fr")
    language.addItem("English", "en")
    index = language.findData(locale)
    if index >= 0:
        language.setCurrentIndex(index)
    form.addRow(tr.text("settings.language"), language)
    note = QLabel(tr.text("settings.restart"))
    note.setWordWrap(True)
    form.addRow(note)
    layout.addLayout(form)
    update_group = create_update_settings_group(
        locale=locale,
        service=update_service,
        settings=update_settings,
    )
    layout.addWidget(update_group)
    layout.addStretch(1)
    language.currentIndexChanged.connect(lambda *_: _save_locale(str(language.currentData())))
    page._kodepoia_language_selector = language
    page._kodepoia_update_group = update_group
    return page


def _draft_has_content(draft: VisionDraft) -> bool:
    return bool(
        draft.summary
        or draft.goals
        or draft.success_metrics
        or draft.constraints
        or draft.mvp
        or draft.out_of_scope
        or draft.requirements
    )


def build_window(
    *,
    locale: str | None = None,
    project_root: Path | None = None,
    update_service=None,
    update_settings=None,
):
    from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QStackedWidget

    from kodepoia.kodestudio.app import build_window as build_v10_window
    from kodepoia.kodestudio.guided_project_wizard import create_project_dialog
    from kodepoia.kodestudio.vision_chat import create_vision_chat_page

    chosen_locale = selected_locale(locale)
    tr = V11Translator(chosen_locale)
    root = (project_root or Path.cwd()).resolve(strict=False)

    # Build on the accepted v1.0 shell so R1–R16 specialist panels keep their
    # tested contracts. Locale is propagated to panels that already support it.
    window = build_v10_window(locale=chosen_locale, project_root=root)
    window.setObjectName("kodepoiaV11MainWindow")
    window.setWindowTitle(f"{tr.text('app.title')} — {CURRENT_RELEASE.display_version}")
    window.setProperty("kodepoiaReleaseVersion", CURRENT_RELEASE.display_version)
    window.setProperty("kodepoiaReleaseChannel", CURRENT_RELEASE.channel)
    window._kodepoia_locale = chosen_locale

    nav = window.findChild(QListWidget, "mainNavigation")
    pages = window.findChild(QStackedWidget, "mainPages")
    if nav is None or pages is None:
        raise RuntimeError("Accepted KodeStudio shell navigation contract is missing")

    def open_project_with_draft(draft: VisionDraft | None = None) -> None:
        dialog = create_project_dialog(window, locale=chosen_locale)
        if draft is not None and _draft_has_content(draft):
            dialog._kodepoia_apply_vision_draft(draft)
        dialog.exec()

    chat_page = create_vision_chat_page(
        root,
        locale=chosen_locale,
        apply_callback=open_project_with_draft,
    )
    _replace_stack_page(pages, 0, chat_page)

    new_project = window.findChild(QPushButton, "newProjectButton")
    if new_project is not None:
        with contextlib.suppress(RuntimeError, TypeError):
            new_project.clicked.disconnect()
        new_project.setText(tr.text("projects.new"))

        def open_project() -> None:
            state = getattr(chat_page, "_kodepoia_vision_state", {})
            draft = state.get("draft") if isinstance(state, dict) else None
            open_project_with_draft(draft if isinstance(draft, VisionDraft) else None)

        new_project.clicked.connect(open_project)

    # R18.7 extends the accepted Settings page without making network access a
    # startup dependency. The update service is injected only when a structured
    # trusted repository adapter is configured.
    settings_index = nav.count() - 1
    if settings_index >= 0:
        _replace_stack_page(
            pages,
            settings_index,
            _settings_page(
                chosen_locale,
                update_service=update_service,
                update_settings=update_settings,
            ),
        )

    direct_nav = {
        0: tr.text("nav.chat"),
        1: tr.text("nav.projects"),
        2: tr.text("nav.research"),
        3: tr.text("nav.vault"),
        4: tr.text("nav.comfy"),
        nav.count() - 3: tr.text("nav.security"),
        nav.count() - 2: tr.text("nav.audit"),
        nav.count() - 1: tr.text("nav.settings"),
    }
    for index, text in direct_nav.items():
        if 0 <= index < nav.count():
            nav.item(index).setText(text)

    if chosen_locale == "fr":
        security_state = window.findChild(QLabel, "killSwitchState")
        if security_state is not None and "READY" in security_state.text():
            security_state.setText("Arrêt d'urgence : PRÊT")
        stop = window.findChild(QPushButton, "killSwitchButton")
        if stop is not None:
            stop.setText("ARRÊTER TOUS LES PROCESSUS PROTÉGÉS")
        reset = window.findChild(QPushButton, "killSwitchResetButton")
        if reset is not None:
            reset.setText("Réinitialiser l'arrêt d'urgence")

        projects_page = pages.widget(1)
        if projects_page is not None:
            for label in projects_page.findChildren(QLabel):
                if "Projects" in label.text():
                    label.setText(label.text().replace("Projects", "Projets"))

    window._kodepoia_chat_page = chat_page
    window._kodepoia_project_root = root
    window._kodepoia_open_project_with_draft = open_project_with_draft
    window._kodepoia_update_service = update_service
    return window


def main() -> int:
    smoke_test = "--smoke-test" in sys.argv
    if smoke_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "KodeStudio requires its bundled UI runtime or the optional UI extra "
            "when developing from source.",
            file=sys.stderr,
        )
        return 2

    app = QApplication.instance() or QApplication(sys.argv)
    window = build_window()
    if smoke_test:
        window.show()
        app.processEvents()
        window.close()
        app.processEvents()
        return 0
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
