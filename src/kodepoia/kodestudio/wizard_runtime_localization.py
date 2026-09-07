from __future__ import annotations

import contextlib
from typing import Callable


_TEXT_FR: dict[str, str] = {
    "New Kodepoia Project": "Nouveau projet Kodepoia",
    "New Kodepoia project": "Nouveau projet Kodepoia",
    "Project wizard sections": "Sections de l’assistant de projet",
    "Project wizard actions": "Actions de l’assistant de projet",
    "Create project": "Créer le projet",
    "Cancel project creation": "Annuler la création du projet",
    "Name": "Nom",
    "Directory": "Dossier",
    "Type": "Type",
    "Engine": "Moteur",
    "Engine version": "Version du moteur",
    "Dimension": "Dimension",
    "Genres (; separated)": "Genres (séparés par ;)",
    "Graphics style": "Style graphique",
    "Inputs": "Entrées",
    "Input methods": "Méthodes d’entrée",
    "Online": "En ligne",
    "Multiplayer": "Multijoueur",
    "General": "Général",
    "Target platforms are mandatory. Budgets are stored per selected target.": "Les plateformes cibles sont obligatoires. Les budgets sont enregistrés pour chaque cible sélectionnée.",
    "Target platforms": "Plateformes cibles",
    "Performance budgets": "Budgets de performance",
    "Platform": "Plateforme",
    "Target FPS": "FPS cibles",
    "Min FPS": "FPS minimum",
    "VRAM MB": "VRAM (Mo)",
    "RAM MB": "RAM (Mo)",
    "Build MB": "Taille de build (Mo)",
    "Platforms & budgets": "Plateformes et budgets",
    "Local AI / creation tools": "IA locale / outils de création",
    "Local AI and creation tools": "IA locale et outils de création",
    "Download / install policy": "Politique de téléchargement / installation",
    "Download and install policy": "Politique de téléchargement et d’installation",
    "Downloads": "Téléchargements",
    "Installs": "Installations",
    "Feature decisions": "Décisions de fonctionnalités",
    "Lineage": "Filiation",
    "Project lineage": "Filiation du projet",
    "Parent project": "Projet parent",
    "Franchise": "Franchise",
    "Template": "Modèle",
    "Features & tools": "Fonctionnalités et outils",
    "Document": "Document",
    "Vision (required)": "Vision (obligatoire)",
    "Summary": "Résumé",
    "Goals (; separated)": "Objectifs (séparés par ;)",
    "Success metrics (; separated)": "Mesures de réussite (séparées par ;)",
    "Constraints (; separated)": "Contraintes (séparées par ;)",
    "MVP (; separated)": "MVP (séparé par ;)",
    "Out of scope (; separated)": "Hors périmètre (séparé par ;)",
    "Requirements and acceptance criteria": "Exigences et critères d’acceptation",
    "Product requirements": "Exigences produit",
    "Priority": "Priorité",
    "Title": "Titre",
    "Description": "Description",
    "Acceptance criteria (; separated)": "Critères d’acceptation (séparés par ;)",
    "Add requirement": "Ajouter une exigence",
    "Remove selected": "Supprimer la sélection",
    "Remove selected requirements": "Supprimer les exigences sélectionnées",
    "Product": "Produit",
    "Product & Vision": "Produit et Vision",
    "Browse…": "Parcourir…",
    "Desktop": "Bureau",
    "Desktop framework": "Framework de bureau",
    "Desktop architecture": "Architecture de bureau",
    "Desktop package intent": "Intention de paquet de bureau",
    "Desktop persistence decision": "Décision de persistance bureau",
    "Desktop IPC decision": "Décision IPC bureau",
    "Desktop update decision": "Décision de mise à jour bureau",
    "Framework": "Framework",
    "Architecture": "Architecture",
    "Package": "Paquet",
    "Persistence": "Persistance",
    "Local IPC": "IPC local",
    "Updates": "Mises à jour",
    "Mobile phone form factor": "Format téléphone mobile",
    "Mobile tablet form factor": "Format tablette mobile",
    "Android package intent": "Intention de paquet Android",
    "Apple package intent": "Intention de paquet Apple",
    "Android package": "Paquet Android",
    "Apple package": "Paquet Apple",
    "Backend": "Backend",
    "Backend intent only notice": "Information sur l’intention Backend uniquement",
    "Enable backend service intent": "Activer l’intention de services Backend",
    "Backend dependency guidance": "Guide des dépendances Backend",
    "Authentication / identity": "Authentification / identité",
    "Authoritative state / session": "État / session faisant autorité",
    "Multiplayer matchmaking": "Mise en relation multijoueur",
    "Cloud saves": "Sauvegardes cloud",
    "Progression": "Progression",
    "Catalog": "Catalogue",
    "Entitlements": "Droits d’accès",
    "Billing": "Facturation",
    "Remote config / flags": "Configuration distante / indicateurs",
    "Content delivery": "Distribution de contenu",
    "Events": "Événements",
    "Backend services are optional product intent. This wizard does not provision providers, store credentials or execute network operations.": "Les services Backend constituent une intention produit facultative. Cet assistant ne provisionne aucun fournisseur, ne stocke aucun identifiant secret et n’exécute aucune opération réseau.",
    "Backend disabled: no runtime intent is generated.": "Backend désactivé : aucune intention d’exécution n’est générée.",
    "Matchmaking requires authoritative state/session.": "La mise en relation nécessite un état / une session faisant autorité.",
    "Billing requires catalog and entitlement intents.": "La facturation nécessite des intentions de catalogue et de droits d’accès.",
    "Select only services required by the product.": "Sélectionne uniquement les services nécessaires au produit.",
    "phone": "téléphone",
    "tablet": "tablette",
}

_ACCESSIBLE_FR: dict[str, str] = {
    "Create Project DNA and product requirements for a new Kodepoia project.": "Créer l’ADN du projet et les exigences produit d’un nouveau projet Kodepoia.",
    "Switch between general, platform, feature and product sections.": "Basculer entre les sections générales, plateformes, fonctionnalités et produit.",
    "Validate the project definition and create the project.": "Valider la définition du projet et créer le projet.",
    "Filesystem directory where the new project will be initialized.": "Dossier du système de fichiers dans lequel le nouveau projet sera initialisé.",
    "Enter semicolon-separated genres.": "Saisir les genres séparés par des points-virgules.",
    "Per-platform target FPS, minimum FPS, VRAM, RAM and build size budgets.": "Budgets par plateforme pour les FPS cibles, FPS minimum, VRAM, RAM et taille de build.",
    "Select the governed desktop application framework intent.": "Sélectionner l’intention gouvernée de framework d’application de bureau.",
    "Select unpackaged, MSIX, MSI or archive intent without building it yet.": "Sélectionner une intention non empaquetée, MSIX, MSI ou archive sans encore la construire.",
    "Governed source intent; no generator or build is executed here.": "Intention de source gouvernée ; aucun générateur ni build n’est exécuté ici.",
    "Stable Android application identity. Leave empty to derive a deterministic new-project default.": "Identité stable de l’application Android. Laisser vide pour dériver une valeur par défaut déterministe pour le nouveau projet.",
    "Stable Apple bundle identity. Leave empty to derive a deterministic new-project default.": "Identité stable du bundle Apple. Laisser vide pour dériver une valeur par défaut déterministe pour le nouveau projet.",
    "Semicolon-separated permission intent names, not raw manifest or entitlement text.": "Noms d’intentions d’autorisations séparés par des points-virgules, et non texte brut de manifeste ou de droits.",
    "Semicolon-separated governed capability intent names.": "Noms d’intentions de capacités gouvernées séparés par des points-virgules.",
    "Opt in to provider-neutral backend requirements for this project.": "Activer des exigences Backend indépendantes du fournisseur pour ce projet.",
    "Editable requirement table with ID, priority, title, description and acceptance criteria.": "Tableau modifiable d’exigences avec ID, priorité, titre, description et critères d’acceptation.",
    "Remove the currently selected requirement rows.": "Supprimer les lignes d’exigences actuellement sélectionnées.",
    "Required explanation of what is being built and why.": "Explication obligatoire de ce qui est construit et de sa finalité.",
    "Enter semicolon-separated product goals.": "Saisir les objectifs produit séparés par des points-virgules.",
    "Enter semicolon-separated measurable success criteria.": "Saisir les critères mesurables de réussite séparés par des points-virgules.",
    "Enter semicolon-separated constraints.": "Saisir les contraintes séparées par des points-virgules.",
    "Enter semicolon-separated MVP capabilities.": "Saisir les capacités du MVP séparées par des points-virgules.",
    "Enter semicolon-separated out-of-scope items.": "Saisir les éléments hors périmètre séparés par des points-virgules.",
}

_PLACEHOLDER_FR: dict[str, str] = {
    "RPG; simulation; strategy": "RPG ; simulation ; stratégie",
    "realistic, pixel art, isometric…": "réaliste, pixel art, isométrique…",
    "What product/game are we building and why?": "Quel produit ou jeu construisons-nous, et pourquoi ?",
    "goal one; goal two": "objectif un ; objectif deux",
    "60 FPS; zero P0 crashes": "60 FPS ; zéro plantage P0",
    "local-first; Windows-only…": "local en priorité ; Windows uniquement…",
    "MVP capability one; MVP capability two": "capacité MVP une ; capacité MVP deux",
    "camera; location": "caméra ; localisation",
    "camera; notifications": "caméra ; notifications",
}

_COMBO_FR: dict[str, str] = {
    "game": "Jeu",
    "desktop_app": "Application de bureau",
    "mobile_app": "Application mobile",
    "tool": "Outil",
    "plugin": "Extension",
    "library": "Bibliothèque",
    "ai_project": "Projet IA",
    "other": "Autre",
    "yes": "Oui",
    "no": "Non",
    "undecided": "Indécis",
    "deny": "Refuser",
    "ask": "Demander",
    "allow_trusted": "Autoriser les sources de confiance",
    "offline": "Hors ligne",
    "optional": "Facultatif",
    "required": "Requis",
    "development": "Développement",
    "internal": "Interne",
    "beta": "Bêta",
    "production": "Production",
    "unsigned": "Non signé",
    "debug": "Débogage",
    "test": "Test",
    "distribution": "Distribution",
    "native": "Natif",
    "godot_export": "Export Godot",
}

_MESSAGE_FR: dict[str, str] = {
    "Select at least one target platform.": "Sélectionne au moins une plateforme cible.",
    "Name and directory are required.": "Le nom et le dossier sont obligatoires.",
    "Product vision is required.": "La Vision du produit est obligatoire.",
    "Enable backend intent before selecting backend services": "Active l’intention Backend avant de sélectionner des services Backend.",
    "Desktop Wizard failed to create desktop Project DNA": "L’assistant Bureau n’a pas pu créer l’ADN de projet Bureau.",
    "Mobile Wizard failed to create mobile Project DNA": "L’assistant Mobile n’a pas pu créer l’ADN de projet Mobile.",
}


def _translate_exact(value: str) -> str:
    return _TEXT_FR.get(value, _ACCESSIBLE_FR.get(value, value))


def _apply_french_texts(dialog) -> None:
    from PySide6.QtWidgets import (
        QAbstractButton,
        QComboBox,
        QGroupBox,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QTabWidget,
        QTableWidget,
    )

    if dialog.windowTitle() in _TEXT_FR:
        dialog.setWindowTitle(_TEXT_FR[dialog.windowTitle()])
    if dialog.accessibleName():
        dialog.setAccessibleName(_translate_exact(dialog.accessibleName()))
    if dialog.accessibleDescription():
        dialog.setAccessibleDescription(_translate_exact(dialog.accessibleDescription()))

    for widget in dialog.findChildren(QLabel):
        if widget.text() in _TEXT_FR:
            widget.setText(_TEXT_FR[widget.text()])
    for widget in dialog.findChildren(QAbstractButton):
        if widget.text() in _TEXT_FR:
            widget.setText(_TEXT_FR[widget.text()])
    for widget in dialog.findChildren(QGroupBox):
        if widget.title() in _TEXT_FR:
            widget.setTitle(_TEXT_FR[widget.title()])
    for widget in dialog.findChildren(QLineEdit):
        if widget.placeholderText() in _PLACEHOLDER_FR:
            widget.setPlaceholderText(_PLACEHOLDER_FR[widget.placeholderText()])
    for widget in dialog.findChildren(QPlainTextEdit):
        if widget.placeholderText() in _PLACEHOLDER_FR:
            widget.setPlaceholderText(_PLACEHOLDER_FR[widget.placeholderText()])
    for widget in dialog.findChildren(QTabWidget):
        for index in range(widget.count()):
            title = widget.tabText(index)
            if title in _TEXT_FR:
                widget.setTabText(index, _TEXT_FR[title])
    for widget in dialog.findChildren(QComboBox):
        for index in range(widget.count()):
            text = widget.itemText(index)
            if text in _COMBO_FR:
                widget.setItemText(index, _COMBO_FR[text])
    for widget in dialog.findChildren(QTableWidget):
        for column in range(widget.columnCount()):
            item = widget.horizontalHeaderItem(column)
            if item is not None and item.text() in _TEXT_FR:
                item.setText(_TEXT_FR[item.text()])

    for widget in dialog.findChildren((QLabel, QAbstractButton, QGroupBox, QLineEdit, QPlainTextEdit, QComboBox, QTableWidget, QTabWidget)):
        name = widget.accessibleName()
        description = widget.accessibleDescription()
        if name:
            widget.setAccessibleName(_translate_exact(name))
        if description:
            widget.setAccessibleDescription(_translate_exact(description))

    hint = getattr(dialog, "backend_dependency_hint", None)
    if hint is not None and hint.text() in _TEXT_FR:
        hint.setText(_TEXT_FR[hint.text()])

    budget_table = getattr(dialog, "budget_table", None)
    if budget_table is not None:
        for row in range(budget_table.rowCount()):
            for column in range(1, budget_table.columnCount()):
                spin = budget_table.cellWidget(row, column)
                if spin is not None and hasattr(spin, "specialValueText") and spin.specialValueText() == "unlimited":
                    spin.setSpecialValueText("illimité")


def _install_dynamic_refresh(dialog) -> None:
    from PySide6.QtCore import QTimer

    def refresh(*_args: object) -> None:
        QTimer.singleShot(0, lambda: _apply_french_texts(dialog))

    project_type = getattr(dialog, "project_type", None)
    if project_type is not None:
        project_type.currentIndexChanged.connect(refresh)
    for check in getattr(dialog, "platform_checks", {}).values():
        check.stateChanged.connect(refresh)
    backend_enabled = getattr(dialog, "backend_enabled", None)
    if backend_enabled is not None:
        backend_enabled.stateChanged.connect(refresh)
    for check in getattr(dialog, "backend_service_checks", {}).values():
        check.stateChanged.connect(refresh)
    desktop_framework = getattr(dialog, "desktop_framework", None)
    if desktop_framework is not None:
        desktop_framework.currentIndexChanged.connect(refresh)


def _install_french_browse(dialog) -> None:
    from PySide6.QtWidgets import QFileDialog, QPushButton

    browse = dialog.findChild(QPushButton, "browseProjectDirectoryButton")
    if browse is None:
        return
    with contextlib.suppress(RuntimeError, TypeError):
        browse.clicked.disconnect()

    def choose_directory() -> None:
        selected = QFileDialog.getExistingDirectory(dialog, "Dossier du projet")
        if selected:
            dialog.directory.setText(selected)

    browse.clicked.connect(choose_directory)


def _install_message_filter(dialog) -> None:
    from PySide6.QtCore import QEvent, QObject
    from PySide6.QtWidgets import QApplication, QMessageBox

    class FrenchMessageFilter(QObject):
        def eventFilter(self, watched, event):  # noqa: N802 - Qt API
            if event.type() == QEvent.Type.Show and isinstance(watched, QMessageBox):
                parent = watched.parentWidget()
                belongs = False
                while parent is not None:
                    if parent is dialog:
                        belongs = True
                        break
                    parent = parent.parentWidget()
                if belongs:
                    text = watched.text()
                    if text in _MESSAGE_FR:
                        watched.setText(_MESSAGE_FR[text])
                    informative = watched.informativeText()
                    if informative in _MESSAGE_FR:
                        watched.setInformativeText(_MESSAGE_FR[informative])
            return False

    app = QApplication.instance()
    if app is None:
        return
    filter_object = FrenchMessageFilter(dialog)
    app.installEventFilter(filter_object)
    dialog._kodepoia_french_message_filter = filter_object

    def remove_filter(*_args: object) -> None:
        with contextlib.suppress(RuntimeError):
            app.removeEventFilter(filter_object)

    dialog.destroyed.connect(remove_filter)


def create_project_dialog(parent=None, *, locale: str | None = None):
    """Create the assembled Project Wizard and enforce the selected runtime locale.

    The historical R2–R14 wizard layers contain some source-English widget text.
    R19.1 post-processes the fully assembled dialog so the installed French UI is
    complete while preserving enum item data and all domain contracts.
    """

    from kodepoia.kodestudio.guided_project_wizard import create_project_dialog as create_guided_dialog
    from kodepoia.kodestudio.v11_localization import resolve_locale

    chosen = resolve_locale(locale or getattr(parent, "_kodepoia_locale", None))
    dialog = create_guided_dialog(parent, locale=chosen)
    if chosen != "fr":
        return dialog

    _apply_french_texts(dialog)
    _install_dynamic_refresh(dialog)
    _install_french_browse(dialog)
    _install_message_filter(dialog)
    dialog._kodepoia_runtime_locale = "fr"
    dialog._kodepoia_retranslate_french = lambda: _apply_french_texts(dialog)
    return dialog


__all__ = ["create_project_dialog"]
