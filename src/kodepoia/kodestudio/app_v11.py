from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from kodepoia.kodestudio.v11_localization import V11Translator, resolve_locale


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


def _settings_page(locale: str):
    from PySide6.QtWidgets import QComboBox, QLabel, QFormLayout, QVBoxLayout, QWidget

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
    layout.addStretch(1)
    language.currentIndexChanged.connect(lambda *_: _save_locale(str(language.currentData())))
    page._kodepoia_language_selector = language
    return page


def build_window(*, locale: str | None = None, project_root: Path | None = None):
    from PySide6.QtWidgets import (
        QLabel,
        QListWidget,
        QPushButton,
        QStackedWidget,
    )

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
    window.setWindowTitle(tr.text("app.title"))
    window._kodepoia_locale = chosen_locale

    nav = window.findChild(QListWidget, "mainNavigation")
    pages = window.findChild(QStackedWidget, "mainPages")
    if nav is None or pages is None:
        raise RuntimeError("Accepted KodeStudio shell navigation contract is missing")

    chat_page = create_vision_chat_page(root, locale=chosen_locale)
    _replace_stack_page(pages, 0, chat_page)

    new_project = window.findChild(QPushButton, "newProjectButton")
    if new_project is not None:
        try:
            new_project.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        new_project.setText(tr.text("projects.new"))
        new_project.clicked.connect(
            lambda: create_project_dialog(window, locale=chosen_locale).exec()
        )

    # Replace the former placeholder Settings page with a real language setting.
    settings_index = nav.count() - 1
    if settings_index >= 0:
        _replace_stack_page(pages, settings_index, _settings_page(chosen_locale))

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
    return window


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "KodeStudio requires its bundled UI runtime or the optional UI extra when developing from source.",
            file=sys.stderr,
        )
        return 2

    app = QApplication.instance() or QApplication(sys.argv)
    window = build_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
