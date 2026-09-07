from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.kodestudio.blender_localization import registered_blender_messages
from kodepoia.kodestudio.fr_catalogs import (
    BLENDER_FR,
    KODESTUDIO_FR,
    R11_FR,
    R12_FR,
    R13_FR,
    R13_WIZARD_FR,
    placeholders,
)
from kodepoia.kodestudio.localization import registered_messages
from kodepoia.kodestudio.preferences import ApplicationPreferences
from kodepoia.kodestudio.r11_localization import registered_r11_messages
from kodepoia.kodestudio.r12_localization import registered_r12_messages
from kodepoia.kodestudio.r13_localization import registered_r13_messages
from kodepoia.kodestudio.r13_wizard_localization import registered_r13_wizard_messages
from kodepoia.kodestudio.runtime_localization import KodeStudioTranslator
from kodepoia.kodestudio.v11_localization import MESSAGES, V11Translator


def _assert_complete_catalog(source: dict[str, str], french: dict[str, str]) -> None:
    assert set(french) == set(source)
    for key, source_text in source.items():
        assert placeholders(french[key]) == placeholders(source_text), key
        assert french[key].strip(), key


def test_all_shipped_french_catalogs_are_complete_and_placeholder_safe() -> None:
    _assert_complete_catalog(dict(registered_messages()), KODESTUDIO_FR)
    _assert_complete_catalog(dict(registered_blender_messages()), BLENDER_FR)
    _assert_complete_catalog(dict(registered_r11_messages()), R11_FR)
    _assert_complete_catalog(dict(registered_r12_messages()), R12_FR)
    _assert_complete_catalog(dict(registered_r13_messages()), R13_FR)
    _assert_complete_catalog(dict(registered_r13_wizard_messages()), R13_WIZARD_FR)
    _assert_complete_catalog(MESSAGES["en"], MESSAGES["fr"])


def test_runtime_french_translator_never_silently_falls_back_to_english() -> None:
    tr = KodeStudioTranslator("fr-FR")
    assert tr.text("app.nav.projects") == "Projets"
    assert tr.text("research.refresh_status") == "Actualiser le statut"
    assert tr.text("vault.rebuild") == "Reconstruire les index"
    assert tr.text("comfy.run") == "Exécuter"
    with pytest.raises(KeyError, match="missing French KodeStudio translation"):
        tr.text("r19.missing.key")


def test_v11_french_translator_is_strict_and_has_apply_restart_copy() -> None:
    tr = V11Translator("fr")
    assert tr.text("nav.settings") == "Paramètres"
    assert "Redémarrer KodeStudio" in tr.text("settings.apply_prompt")
    assert "Aucun dépôt structuré" in tr.text("updates.repository_unconfigured")
    with pytest.raises(KeyError, match="missing fr v1.1 translation"):
        tr.text("missing.key")


def test_preferences_merge_and_round_trip_locale_without_clobbering(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "locale": "fr",
                "theme": "dark",
                "telemetry": False,
                "nested": {"keep": [1, 2, 3]},
            }
        ),
        encoding="utf-8",
    )
    prefs = ApplicationPreferences(path)
    prefs.set_locale("en")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload == {
        "locale": "en",
        "nested": {"keep": [1, 2, 3]},
        "telemetry": False,
        "theme": "dark",
    }
    prefs.set_locale("fr")
    assert prefs.locale() == "fr"
    assert prefs.load()["nested"] == {"keep": [1, 2, 3]}
    assert not list(path.parent.glob(f".{path.name}.*.tmp"))


def test_corrupt_preferences_fail_safe(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{ definitely not json", encoding="utf-8")
    prefs = ApplicationPreferences(path)
    assert prefs.load() == {}
    assert prefs.locale() is None
    prefs.set_locale("fr")
    assert prefs.load() == {"locale": "fr"}


def test_saved_locale_precedes_diagnostic_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from kodepoia.kodestudio import app_v11

    path = tmp_path / "settings.json"
    ApplicationPreferences(path).set_locale("en")
    monkeypatch.setattr(app_v11, "SETTINGS_PATH", path)
    monkeypatch.setenv("KODEPOIA_LOCALE", "fr")
    assert app_v11.selected_locale() == "en"
    assert app_v11.selected_locale("fr") == "fr"


def test_no_saved_locale_allows_diagnostic_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from kodepoia.kodestudio import app_v11

    path = tmp_path / "missing-settings.json"
    monkeypatch.setattr(app_v11, "SETTINGS_PATH", path)
    monkeypatch.setenv("KODEPOIA_LOCALE", "fr_FR")
    assert app_v11.selected_locale() == "fr"


def _collect_ui_texts(root) -> list[str]:
    from PySide6.QtWidgets import (
        QAbstractButton,
        QComboBox,
        QGroupBox,
        QLabel,
        QLineEdit,
        QListWidget,
        QPlainTextEdit,
        QTabWidget,
        QTableWidget,
        QWidget,
    )

    texts: list[str] = [root.windowTitle(), root.accessibleName(), root.accessibleDescription()]
    for widget in root.findChildren(QWidget):
        texts.extend((widget.accessibleName(), widget.accessibleDescription()))
        if isinstance(widget, QLabel):
            texts.append(widget.text())
        if isinstance(widget, QAbstractButton):
            texts.append(widget.text())
        if isinstance(widget, QGroupBox):
            texts.append(widget.title())
        if isinstance(widget, QLineEdit):
            texts.append(widget.placeholderText())
        if isinstance(widget, QPlainTextEdit):
            texts.append(widget.placeholderText())
        if isinstance(widget, QListWidget):
            texts.extend(widget.item(i).text() for i in range(widget.count()))
        if isinstance(widget, QComboBox):
            texts.extend(widget.itemText(i) for i in range(widget.count()))
        if isinstance(widget, QTabWidget):
            texts.extend(widget.tabText(i) for i in range(widget.count()))
        if isinstance(widget, QTableWidget):
            for column in range(widget.columnCount()):
                item = widget.horizontalHeaderItem(column)
                if item is not None:
                    texts.append(item.text())
    return [text for text in texts if text]


def test_french_v11_window_has_no_known_english_surface_regressions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QListWidget

    from kodepoia.kodestudio.app_v11 import build_window

    app = QApplication.instance() or QApplication([])
    window = build_window(locale="fr", project_root=tmp_path)
    try:
        joined = "\n".join(_collect_ui_texts(window))
        forbidden = (
            "Projects",
            "Research status",
            "Asset Vault",
            "Runtime and capabilities",
            "Voice",
            "Cinematics",
            "Desktop application workspace",
            "Mobile, DeviceLab & Release workspace",
            "Security",
            "Settings",
            "Installed version",
            "Update channel",
            "Check for updates",
            "Chat & Project Vision",
            "Main navigation",
            "Application status",
        )
        for phrase in forbidden:
            assert phrase not in joined, phrase

        nav = window.findChild(QListWidget, "mainNavigation")
        assert nav is not None
        nav_text = [nav.item(i).text() for i in range(nav.count())]
        assert "Projets" in nav_text
        assert "Recherche" in nav_text
        assert "Sécurité" in nav_text
        assert "Paramètres" in nav_text
        assert "Bureau" in nav_text
        assert "Mobile et publication" in nav_text
        assert "Expérience et réglage" in nav_text
    finally:
        window.close()
        app.processEvents()


def test_french_project_wizard_is_translated_after_full_r14_assembly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QTabWidget

    from kodepoia.kodestudio.wizard_runtime_localization import create_project_dialog

    app = QApplication.instance() or QApplication([])
    dialog = create_project_dialog(locale="fr")
    try:
        app.processEvents()
        joined = "\n".join(_collect_ui_texts(dialog))
        forbidden = (
            "New Kodepoia Project",
            "Project wizard sections",
            "Project wizard actions",
            "Target platforms are mandatory",
            "Target platforms",
            "Performance budgets",
            "Local AI / creation tools",
            "Download / install policy",
            "Feature decisions",
            "Project lineage",
            "Product requirements",
            "Desktop framework",
            "Desktop architecture",
            "Desktop package intent",
            "Backend services are optional product intent",
            "Enable backend service intent",
            "Authentication / identity",
            "Authoritative state / session",
            "Multiplayer matchmaking",
            "Cloud saves",
            "Entitlements",
            "Billing",
            "Remote config / flags",
            "Content delivery",
            "Backend dependency guidance",
        )
        for phrase in forbidden:
            assert phrase not in joined, phrase

        assert "Nouveau projet Kodepoia" in dialog.windowTitle()
        tabs = dialog.findChild(QTabWidget, "wizardTabs")
        assert tabs is not None
        tab_texts = [tabs.tabText(i) for i in range(tabs.count())]
        assert "Général" in tab_texts
        assert "Plateformes et budgets" in tab_texts
        assert "Fonctionnalités et outils" in tab_texts
        assert "Bureau" in tab_texts
        assert "Mobile" in tab_texts
        assert "Backend" in tab_texts

        assert dialog.backend_dependency_hint.text() == (
            "Backend désactivé : aucune intention d’exécution n’est générée."
        )
        dialog.backend_enabled.setChecked(True)
        app.processEvents()
        app.processEvents()
        assert dialog.backend_dependency_hint.text() == (
            "Sélectionne uniquement les services nécessaires au produit."
        )
    finally:
        dialog.close()
        dialog.deleteLater()
        app.processEvents()


def test_language_selector_persists_choice_and_requests_apply(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from kodepoia.kodestudio import app_v11

    app = QApplication.instance() or QApplication([])
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"locale": "fr", "theme": "dark"}), encoding="utf-8")
    monkeypatch.setattr(app_v11, "SETTINGS_PATH", path)
    applied: list[str] = []
    page = app_v11._settings_page("fr", apply_locale=applied.append)
    try:
        selector = page._kodepoia_language_selector
        selector.setCurrentIndex(selector.findData("en"))
        app.processEvents()
        assert applied == ["en"]
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["locale"] == "en"
        assert payload["theme"] == "dark"
    finally:
        page.deleteLater()
        app.processEvents()
