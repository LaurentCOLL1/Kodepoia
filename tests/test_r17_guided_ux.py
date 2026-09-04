from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.brain.base import BrainResponse
from kodepoia.kodestudio.guided_catalog import GENRE_OPTIONS, GRAPHICS_OPTIONS
from kodepoia.kodestudio.v11_localization import V11Translator, resolve_locale
from kodepoia.kodestudio.vision_assistant import (
    VisionAssistant,
    VisionAssistantResult,
    VisionDraft,
    load_vision_draft,
    save_vision_draft,
)


class FakeOllama:
    def list_models(self) -> list[str]:
        return ["local-test:latest"]

    def chat(self, model, messages, **kwargs):
        assert model == "local-test:latest"
        assert kwargs["response_schema"]["type"] == "object"
        payload = {
            "summary": "Un RPG de simulation locale.",
            "goals": ["Créer une boucle de jeu claire"],
            "success_metrics": ["60 FPS"],
            "constraints": ["Windows", "local-first"],
            "mvp": ["Créer un personnage", "Jouer une journée"],
            "out_of_scope": ["Multijoueur pour le MVP"],
            "requirements": [
                {
                    "id": "REQ-001",
                    "priority": "P0",
                    "title": "Boucle principale",
                    "description": "Le joueur peut terminer une journée.",
                    "acceptance_criteria": ["Une journée peut être commencée et terminée"],
                }
            ],
            "clarifying_questions": ["Quel est le public principal ?"],
        }
        return BrainResponse(content=json.dumps(payload), model=model)


def test_french_locale_resolution_and_catalog(monkeypatch) -> None:
    # System-locale detection must be testable independently from the workflow's
    # explicit KODEPOIA_LOCALE=fr setting. An explicit user/environment choice
    # intentionally takes precedence over OS detection.
    monkeypatch.delenv("KODEPOIA_LOCALE", raising=False)
    assert resolve_locale(system_name="fr_FR") == "fr"
    assert resolve_locale(system_name="en_US") == "en"
    assert resolve_locale("fr-FR", system_name="en_US") == "fr"
    monkeypatch.setenv("KODEPOIA_LOCALE", "fr")
    assert resolve_locale(system_name="en_US") == "fr"
    assert V11Translator("fr").text("nav.projects") == "Projets"
    assert V11Translator("fr").text("chat.send") == "Envoyer"


def test_guided_catalog_contains_requested_beginner_options() -> None:
    french_genres = {item.label("fr") for item in GENRE_OPTIONS}
    assert "RPG / jeu de rôle" in french_genres
    assert "Simulation" in french_genres
    assert "Sexe / adulte" in french_genres
    assert "Stratégie" in french_genres
    assert "Action" in french_genres
    assert any(item.value == "photorealistic" for item in GRAPHICS_OPTIONS)
    assert any(item.value == "pixel_art" for item in GRAPHICS_OPTIONS)


def test_guided_fallback_asks_for_missing_precision() -> None:
    assistant = VisionAssistant(client=FakeOllama())
    result = assistant.refine("Je veux créer un RPG contemporain.", locale="fr")
    assert result.mode == "guided"
    assert result.draft.summary == "Je veux créer un RPG contemporain."
    assert result.clarifying_questions
    assert len(result.clarifying_questions) == 1
    assert "précision" in result.assistant_message


def test_guided_fallback_progressively_builds_vision() -> None:
    assistant = VisionAssistant(client=FakeOllama())
    result = assistant.refine("Un jeu de gestion spatiale", locale="fr")
    result = assistant.refine("Construire une station; survivre 100 jours", current=result.draft, locale="fr")
    assert result.draft.goals == ["Construire une station", "survivre 100 jours"]
    result = assistant.refine("60 FPS; aucune sauvegarde corrompue", current=result.draft, locale="fr")
    assert result.draft.success_metrics == ["60 FPS", "aucune sauvegarde corrompue"]
    result = assistant.refine("Windows; hors ligne; public adulte", current=result.draft, locale="fr")
    result = assistant.refine("Construire une pièce; produire de l'oxygène", current=result.draft, locale="fr")
    result = assistant.refine("Pas de multijoueur", current=result.draft, locale="fr")
    result = assistant.refine("Construire une station habitable", current=result.draft, locale="fr")
    assert result.draft.requirements[0].title == "Construire une station habitable"
    result = assistant.refine("La station garde de l'oxygène pendant 10 minutes", current=result.draft, locale="fr")
    assert result.draft.requirements[0].acceptance_criteria == [
        "La station garde de l'oxygène pendant 10 minutes"
    ]
    assert result.clarifying_questions == []
    changed = assistant.refine("Objectifs: Construire une colonie autonome", current=result.draft, locale="fr")
    assert changed.draft.goals == ["Construire une colonie autonome"]


def test_local_ollama_structures_vision() -> None:
    assistant = VisionAssistant(client=FakeOllama())
    result = assistant.refine(
        "Structure cette idée",
        current=VisionDraft(summary="Idée initiale"),
        model="local-test:latest",
        locale="fr",
    )
    assert result.mode == "ollama"
    assert result.model == "local-test:latest"
    assert result.draft.summary == "Un RPG de simulation locale."
    assert result.draft.success_metrics == ["60 FPS"]
    assert result.draft.requirements[0].id == "REQ-001"
    assert result.draft.requirements[0].acceptance_criteria
    assert result.clarifying_questions == ["Quel est le public principal ?"]


def test_vision_draft_persists_locally(tmp_path: Path) -> None:
    result = VisionAssistantResult(
        draft=VisionDraft(summary="Vision locale", goals=["Objectif A"]),
        clarifying_questions=["Question ?"],
    )
    path = save_vision_draft(tmp_path / ".kodepoia" / "vision" / "draft.json", result)
    assert path.exists()
    loaded = load_vision_draft(path)
    assert loaded.summary == "Vision locale"
    assert loaded.goals == ["Objectif A"]


def test_windows_installer_contract_is_real_setup() -> None:
    root = Path(__file__).resolve().parents[1]
    iss = (root / "packaging" / "windows" / "Kodepoia.iss").read_text(encoding="utf-8")
    build = (root / "scripts" / "build_windows_installer.ps1").read_text(encoding="utf-8")
    assert "OutputBaseFilename=KodepoiaSetup" in iss
    assert "PrivilegesRequired=lowest" in iss
    assert "[Icons]" in iss
    assert "{autodesktop}\\Kodepoia" in iss
    assert "{uninstallexe}" in iss
    assert "KodepoiaStudio.exe" in iss
    assert '"--standalone"' in build
    assert "KodepoiaSetup.exe" in build
    assert "production_signed = $false" in build


def test_guided_project_wizard_preserves_line_edit_contract(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton

    from kodepoia.kodestudio.guided_project_wizard import create_project_dialog

    app = QApplication.instance() or QApplication([])
    dialog = create_project_dialog(locale="fr")
    assert isinstance(dialog.genres, QLineEdit)
    assert isinstance(dialog.graphics_style, QLineEdit)
    genre = dialog.guided_genre_selector
    genre.setCurrentIndex(genre.findText("RPG / jeu de rôle"))
    add = dialog.findChild(QPushButton, "guidedGenreAddButton")
    assert add is not None
    add.click()
    assert "RPG / jeu de rôle" in dialog.genres.text()
    graphics = dialog.guided_graphics_selector
    graphics.setCurrentIndex(graphics.findText("Réaliste"))
    assert dialog.graphics_style.text() == "Réaliste"
    assert dialog.findChild(QPushButton, "openVisionAssistantButton") is not None
    dialog.close()
    app.processEvents()


def test_v11_shell_has_real_chat_and_french_navigation(monkeypatch, tmp_path: Path) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QListWidget, QPushButton, QWidget

    from kodepoia.kodestudio.app_v11 import build_window

    app = QApplication.instance() or QApplication([])
    window = build_window(locale="fr", project_root=tmp_path)
    nav = window.findChild(QListWidget, "mainNavigation")
    assert nav is not None
    assert nav.item(0).text() == "Chat"
    assert nav.item(1).text() == "Projets"
    assert window.findChild(QWidget, "visionChatPage") is not None
    assert window.findChild(QPushButton, "visionChatSendButton") is not None
    assert window.findChild(QPushButton, "newProjectButton").text() == "Nouveau projet…"
    window.close()
    app.processEvents()
