from __future__ import annotations

import contextlib
import os
import sys
from collections.abc import Callable
from pathlib import Path

from kodepoia.kodestudio.preferences import DEFAULT_SETTINGS_PATH, ApplicationPreferences
from kodepoia.kodestudio.v11_localization import V11Translator, resolve_locale
from kodepoia.kodestudio.vision_assistant import VisionDraft
from kodepoia.release_identity import CURRENT_RELEASE

SETTINGS_PATH = DEFAULT_SETTINGS_PATH


def _preferences() -> ApplicationPreferences:
    # Keep SETTINGS_PATH as the compatibility/test seam while centralizing all
    # persistence behavior in the merge-safe preference store.
    return ApplicationPreferences(SETTINGS_PATH)


def _load_saved_locale() -> str | None:
    return _preferences().locale()


def _save_locale(locale: str) -> None:
    _preferences().set_locale(resolve_locale(locale))


def selected_locale(requested: str | None = None) -> str:
    """Resolve the product locale without letting packaging env defeat user choice.

    Precedence is explicit runtime/test request, persisted user preference,
    developer/diagnostic environment override, then OS locale detection.
    """

    if requested and requested.strip():
        return resolve_locale(requested)
    saved = _load_saved_locale()
    if saved:
        return resolve_locale(saved)
    diagnostic_override = os.environ.get("KODEPOIA_LOCALE")
    if diagnostic_override and diagnostic_override.strip():
        return resolve_locale(diagnostic_override)
    return resolve_locale(None)


def _restart_application() -> bool:
    """Start a replacement process using the same executable/arguments."""

    from PySide6.QtCore import QProcess

    executable = sys.executable
    arguments = list(sys.argv[1:] if getattr(sys, "frozen", False) else sys.argv)
    result = QProcess.startDetached(executable, arguments)
    if isinstance(result, tuple):
        return bool(result[0])
    return bool(result)


def _offer_locale_restart(parent, locale: str) -> bool:
    """Offer an explicit, user-consented restart to apply a saved locale."""

    from PySide6.QtWidgets import QApplication, QMessageBox

    tr = V11Translator(locale)
    answer = QMessageBox.question(
        parent,
        tr.text("settings.apply_title"),
        tr.text("settings.apply_prompt"),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if answer != QMessageBox.StandardButton.Yes:
        return False
    if not _restart_application():
        QMessageBox.warning(
            parent,
            tr.text("settings.apply_title"),
            tr.text("settings.restart_failed"),
        )
        return False
    app = QApplication.instance()
    if app is not None:
        app.quit()
    return True


def _replace_stack_page(stack, index: int, widget) -> None:
    old = stack.widget(index)
    stack.removeWidget(old)
    stack.insertWidget(index, widget)
    old.deleteLater()


def _projects_page(
    locale: str,
    *,
    project_root: Path,
    preferences: ApplicationPreferences,
    create_project: Callable[[], None],
    activate_project: Callable[[Path], None],
):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    from kodepoia.kodestudio.project_sessions import (
        forget_recent_project,
        is_kodepoia_project,
        recent_project_roots,
        validate_project_root,
    )

    french = locale.lower().startswith("fr")

    def ui(fr: str, en: str) -> str:
        return fr if french else en

    page = QWidget()
    page.setObjectName("v11ProjectsPage")
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(f"<h2>{ui('Projets', 'Projects')}</h2>"))

    current = QLabel(
        ui(f"Projet actif : {project_root}", f"Active project: {project_root}")
        if is_kodepoia_project(project_root)
        else ui("Aucun projet Kodepoia actif", "No active Kodepoia project")
    )
    current.setObjectName("activeProjectPathLabel")
    current.setWordWrap(True)
    layout.addWidget(current)

    actions = QHBoxLayout()
    create = QPushButton(ui("Nouveau projet…", "New project…"))
    create.setObjectName("newProjectButton")
    open_existing = QPushButton(ui("Ouvrir un projet existant…", "Open existing project…"))
    open_existing.setObjectName("openExistingProjectButton")
    actions.addWidget(create)
    actions.addWidget(open_existing)
    actions.addStretch(1)
    layout.addLayout(actions)

    layout.addWidget(QLabel(f"<b>{ui('Projets récents', 'Recent projects')}</b>"))
    recent = QListWidget()
    recent.setObjectName("recentProjectsList")
    layout.addWidget(recent, 1)

    recent_actions = QHBoxLayout()
    open_selected = QPushButton(ui("Ouvrir", "Open"))
    open_selected.setObjectName("openRecentProjectButton")
    remove_selected = QPushButton(ui("Retirer de la liste", "Remove from list"))
    remove_selected.setObjectName("removeRecentProjectButton")
    recent_actions.addWidget(open_selected)
    recent_actions.addWidget(remove_selected)
    recent_actions.addStretch(1)
    layout.addLayout(recent_actions)

    def selected_path() -> Path | None:
        item = recent.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return Path(str(value)) if value else None

    def populate() -> None:
        recent.clear()
        for root in recent_project_roots(preferences, include_missing=True):
            available = is_kodepoia_project(root)
            label = str(root)
            if not available:
                label += ui(" — indisponible", " — unavailable")
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(root))
            if not available:
                item.setToolTip(
                    ui(
                        "Le dossier ou .kodepoia/project.yaml n'est plus disponible.",
                        "The folder or .kodepoia/project.yaml is no longer available.",
                    )
                )
            recent.addItem(item)

    def browse_existing() -> None:
        directory = QFileDialog.getExistingDirectory(
            page,
            ui("Choisir le dossier du projet Kodepoia", "Choose the Kodepoia project folder"),
            str(project_root if project_root.exists() else Path.home()),
        )
        if not directory:
            return
        try:
            root = validate_project_root(directory)
        except ValueError as exc:
            QMessageBox.warning(page, "Kodepoia", str(exc))
            return
        activate_project(root)

    def open_recent() -> None:
        root = selected_path()
        if root is None:
            return
        try:
            root = validate_project_root(root)
        except ValueError as exc:
            QMessageBox.warning(page, "Kodepoia", str(exc))
            populate()
            return
        activate_project(root)

    def remove_recent() -> None:
        root = selected_path()
        if root is None:
            return
        forget_recent_project(preferences, root)
        populate()

    create.clicked.connect(create_project)
    open_existing.clicked.connect(browse_existing)
    open_selected.clicked.connect(open_recent)
    remove_selected.clicked.connect(remove_recent)
    recent.itemDoubleClicked.connect(lambda *_: open_recent())
    populate()

    page._kodepoia_recent_projects = recent
    page._kodepoia_refresh_recent_projects = populate
    return page


def _settings_page(
    locale: str,
    *,
    preferences: ApplicationPreferences,
    update_service=None,
    install_service=None,
    update_settings=None,
    apply_locale: Callable[[str], object] | None = None,
):
    from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QVBoxLayout, QWidget

    from kodepoia.kodestudio.model_manager import create_model_manager_group
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
    note.setObjectName("applicationLanguageApplyNote")
    note.setWordWrap(True)
    form.addRow(note)
    layout.addLayout(form)

    model_group = create_model_manager_group(preferences, locale=locale)
    layout.addWidget(model_group)

    update_group = create_update_settings_group(
        locale=locale,
        service=update_service,
        install_service=install_service,
        settings=update_settings,
    )
    layout.addWidget(update_group)
    layout.addStretch(1)

    def language_changed() -> None:
        chosen = resolve_locale(str(language.currentData()))
        _save_locale(chosen)
        if chosen != resolve_locale(locale) and apply_locale is not None:
            apply_locale(chosen)

    language.currentIndexChanged.connect(lambda *_: language_changed())
    page._kodepoia_language_selector = language
    page._kodepoia_language_changed = language_changed
    page._kodepoia_model_group = model_group
    page._kodepoia_update_group = update_group
    return page


def _install_help_menu(window, locale: str) -> None:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QAction, QDesktopServices

    french = locale.lower().startswith("fr")
    menu = window.menuBar().addMenu("Aide" if french else "Help")
    guide = QAction("Guide d’utilisation de Kodepoia" if french else "Kodepoia User Guide", window)
    guide.setObjectName("kodepoiaUserGuideAction")

    def open_guide() -> None:
        candidates = [
            Path(__file__).resolve().parents[3] / "docs" / "user" / "KODEPOIA_USER_GUIDE.md",
            Path(sys.executable).resolve().parent / "docs" / "user" / "KODEPOIA_USER_GUIDE.md",
        ]
        for candidate in candidates:
            if candidate.is_file():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(candidate)))
                return
        QDesktopServices.openUrl(
            QUrl(
                "https://github.com/LaurentCOLL1/Kodepoia/blob/main/"
                "docs/user/KODEPOIA_USER_GUIDE.md"
            )
        )

    guide.triggered.connect(open_guide)
    menu.addAction(guide)
    window._kodepoia_user_guide_action = guide


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
    install_service=None,
    update_settings=None,
):
    from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QMessageBox, QPushButton, QStackedWidget

    from kodepoia.brain.ollama import OllamaClient
    from kodepoia.kodestudio.app import build_window as build_v10_window
    from kodepoia.kodestudio.model_manager import (
        preferred_model,
        saved_ollama_base_url,
    )
    from kodepoia.kodestudio.project_sessions import (
        active_project_root,
        is_kodepoia_project,
        remember_project,
    )
    from kodepoia.kodestudio.vision_assistant import VisionAssistant
    from kodepoia.kodestudio.vision_chat import create_vision_chat_page
    from kodepoia.kodestudio.wizard_runtime_localization import create_project_dialog

    chosen_locale = selected_locale(locale)
    tr = V11Translator(chosen_locale)
    preferences = _preferences()
    saved_root = active_project_root(preferences)
    root = (project_root or saved_root or Path.cwd()).resolve(strict=False)

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

    def restart_for_project(selected: Path) -> None:
        try:
            selected = remember_project(preferences, selected)
        except ValueError as exc:
            QMessageBox.warning(window, "Kodepoia", str(exc))
            return
        if selected == root and is_kodepoia_project(root):
            return
        if not _restart_application():
            QMessageBox.warning(
                window,
                "Kodepoia",
                (
                    "Le projet a été mémorisé mais le redémarrage automatique a échoué. "
                    "Relancez KodeStudio."
                    if chosen_locale.startswith("fr")
                    else "The project was saved but automatic restart failed. Restart KodeStudio."
                ),
            )
            return
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def open_project_with_draft(draft: VisionDraft | None = None) -> None:
        dialog = create_project_dialog(window, locale=chosen_locale)
        if draft is not None and _draft_has_content(draft):
            dialog._kodepoia_apply_vision_draft(draft)
        if not dialog.exec():
            return
        project_root_getter = getattr(dialog, "project_root", None)
        if callable(project_root_getter):
            created_root = Path(project_root_getter()).resolve(strict=False)
            if is_kodepoia_project(created_root):
                restart_for_project(created_root)

    assistant = VisionAssistant(
        OllamaClient(base_url=saved_ollama_base_url(preferences), timeout=8.0)
    )
    chat_page = create_vision_chat_page(
        root,
        locale=chosen_locale,
        assistant=assistant,
        preferred_model=preferred_model(preferences, "core"),
        apply_callback=open_project_with_draft,
    )
    _replace_stack_page(pages, 0, chat_page)

    def create_from_projects_page() -> None:
        state = getattr(chat_page, "_kodepoia_vision_state", {})
        draft = state.get("draft") if isinstance(state, dict) else None
        open_project_with_draft(draft if isinstance(draft, VisionDraft) else None)

    _replace_stack_page(
        pages,
        1,
        _projects_page(
            chosen_locale,
            project_root=root,
            preferences=preferences,
            create_project=create_from_projects_page,
            activate_project=restart_for_project,
        ),
    )

    # R19.3 injects a packaged trusted service. Construction is deliberately
    # network-free, so update discovery can never become a startup dependency.
    settings_index = nav.count() - 1
    if settings_index >= 0:
        _replace_stack_page(
            pages,
            settings_index,
            _settings_page(
                chosen_locale,
                preferences=preferences,
                update_service=update_service,
                install_service=install_service,
                update_settings=update_settings,
                apply_locale=lambda new_locale: _offer_locale_restart(window, new_locale),
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

    _install_help_menu(window, chosen_locale)
    window._kodepoia_chat_page = chat_page
    window._kodepoia_project_root = root
    window._kodepoia_open_project_with_draft = open_project_with_draft
    window._kodepoia_update_service = update_service
    window._kodepoia_install_service = install_service
    return window


def _build_packaged_window():
    from kodepoia.kodestudio.project_sessions import active_project_root
    from kodepoia.update.startup import build_packaged_update_services_resilient

    services = build_packaged_update_services_resilient()
    window = build_window(
        project_root=active_project_root(_preferences()),
        update_service=services.discovery,
        install_service=services.installer,
    )
    window._kodepoia_packaged_update_services = services
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
    window = _build_packaged_window()
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
