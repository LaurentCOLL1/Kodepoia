from __future__ import annotations

import json
import os
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


def test_french_v11_window_has_no_known_english_surface_regressions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import (
        QApplication,
        QAbstractButton,
        QComboBox,
        QGroupBox,
        QLabel,
        QListWidget,
        QTableWidget,
    )

    from kodepoia.kodestudio.app_v11 import build_window

    app = QApplication.instance() or QApplication([])
    window = build_window(locale="fr", project_root=tmp_path)
    try:
        texts: list[str] = [window.windowTitle(), window.accessibleDescription()]
        for widget in window.findChildren(QLabel):
            texts.extend((widget.text(), widget.accessibleName(), widget.accessibleDescription()))
        for widget in window.findChildren(QAbstractButton):
            texts.extend((widget.text(), widget.accessibleName(), widget.accessibleDescription()))
        for widget in window.findChildren(QGroupBox):
            texts.extend((widget.title(), widget.accessibleName(), widget.accessibleDescription()))
        for widget in window.findChildren(QListWidget):
            texts.extend(widget.item(i).text() for i in range(widget.count()))
        for widget in window.findChildren(QComboBox):
            texts.extend(widget.itemText(i) for i in range(widget.count()))
            texts.extend((widget.accessibleName(), widget.accessibleDescription()))
        for widget in window.findChildren(QTableWidget):
            for column in range(widget.columnCount()):
                item = widget.horizontalHeaderItem(column)
                if item is not None:
                    texts.append(item.text())
            texts.extend((widget.accessibleName(), widget.accessibleDescription()))
        joined = "\n".join(text for text in texts if text)
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
