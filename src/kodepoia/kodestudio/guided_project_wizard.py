from __future__ import annotations

from typing import Iterable

from kodepoia.kodestudio.guided_catalog import (
    AUDIENCE_OPTIONS,
    GENRE_OPTIONS,
    GRAPHICS_OPTIONS,
    SCOPE_OPTIONS,
    GuidedOption,
)
from kodepoia.kodestudio.v11_localization import V11Translator, resolve_locale
from kodepoia.kodestudio.vision_assistant import VisionDraft, VisionRequirement


def _append_semicolon(widget, value: str) -> None:
    current = [item.strip() for item in widget.text().split(";") if item.strip()]
    if value and value not in current:
        current.append(value)
    widget.setText("; ".join(current))


def _add_options(combo, options: Iterable[GuidedOption], locale: str, *, prompt: str) -> None:
    combo.addItem(prompt, None)
    for option in options:
        combo.addItem(option.label(locale), option.value)
        index = combo.count() - 1
        combo.setItemData(index, option.help(locale), 3)  # Qt.ToolTipRole == 3


def _current_draft(dialog) -> VisionDraft:
    requirements: list[VisionRequirement] = []
    for row in range(dialog.requirements.rowCount()):
        def item_text(column: int) -> str:
            item = dialog.requirements.item(row, column)
            return item.text().strip() if item else ""

        req_id = item_text(0) or f"REQ-{row + 1:03d}"
        priority_widget = dialog.requirements.cellWidget(row, 1)
        priority = priority_widget.currentText() if priority_widget else "P1"
        requirements.append(
            VisionRequirement(
                id=req_id,
                priority=priority,
                title=item_text(2),
                description=item_text(3),
                acceptance_criteria=[
                    value.strip()
                    for value in item_text(4).split(";")
                    if value.strip()
                ],
            )
        )
    split = lambda widget: [value.strip() for value in widget.text().split(";") if value.strip()]
    return VisionDraft(
        summary=dialog.summary.text().strip(),
        goals=split(dialog.goals),
        success_metrics=split(dialog.metrics),
        constraints=split(dialog.constraints),
        mvp=split(dialog.mvp),
        out_of_scope=split(dialog.out_of_scope),
        requirements=requirements,
    )


def _vision_narrative(draft: VisionDraft, locale: str) -> str:
    french = locale.startswith("fr")
    sections: list[str] = []
    if draft.summary:
        sections.append(draft.summary)
    for fr, en, values in (
        ("Objectifs", "Goals", draft.goals),
        ("Mesures de réussite", "Success metrics", draft.success_metrics),
        ("Contraintes", "Constraints", draft.constraints),
        ("MVP", "MVP", draft.mvp),
        ("Hors périmètre", "Out of scope", draft.out_of_scope),
    ):
        if values:
            sections.append(f"{fr if french else en}: " + "; ".join(values))
    return "\n\n".join(sections)


def _apply_draft(dialog, draft: VisionDraft, locale: str) -> None:
    from PySide6.QtWidgets import QTableWidgetItem

    if draft.summary:
        dialog.summary.setText(draft.summary)
    dialog.goals.setText("; ".join(draft.goals))
    dialog.metrics.setText("; ".join(draft.success_metrics))
    dialog.constraints.setText("; ".join(draft.constraints))
    dialog.mvp.setText("; ".join(draft.mvp))
    dialog.out_of_scope.setText("; ".join(draft.out_of_scope))
    narrative = _vision_narrative(draft, locale)
    if narrative:
        dialog.vision.setPlainText(narrative)

    dialog.requirements.setRowCount(0)
    for requirement in draft.requirements:
        dialog._add_requirement()
        row = dialog.requirements.rowCount() - 1
        dialog.requirements.setItem(row, 0, QTableWidgetItem(requirement.id))
        priority = dialog.requirements.cellWidget(row, 1)
        if priority is not None:
            priority.setCurrentText(requirement.priority)
        dialog.requirements.setItem(row, 2, QTableWidgetItem(requirement.title))
        dialog.requirements.setItem(row, 3, QTableWidgetItem(requirement.description))
        dialog.requirements.setItem(
            row,
            4,
            QTableWidgetItem("; ".join(requirement.acceptance_criteria)),
        )


def _translate_base_wizard(dialog, locale: str) -> None:
    if not locale.startswith("fr"):
        return
    from PySide6.QtWidgets import QDialogButtonBox, QLabel, QPushButton

    dialog.setWindowTitle("Nouveau projet Kodepoia")
    tab_names = {
        0: "Général",
        1: "Plateformes & budgets",
        2: "Fonctionnalités & outils",
        3: "Produit & Vision",
    }
    for index, title in tab_names.items():
        if index < dialog.tabs.count():
            dialog.tabs.setTabText(index, title)

    replacements = {
        "Name": "Nom",
        "Directory": "Dossier",
        "Type": "Type",
        "Engine": "Moteur",
        "Engine version": "Version du moteur",
        "Dimension": "Dimension",
        "Genres (; separated)": "Genres (séparés par ;)",
        "Graphics style": "Style graphique",
        "Online": "En ligne",
        "Multiplayer": "Multijoueur",
        "Document": "Document",
        "Vision (required)": "Vision (obligatoire)",
        "Summary": "Résumé",
        "Goals (; separated)": "Objectifs (séparés par ;)",
        "Success metrics (; separated)": "Mesures de réussite (séparées par ;)",
        "Constraints (; separated)": "Contraintes (séparées par ;)",
        "MVP (; separated)": "MVP (séparé par ;)",
        "Out of scope (; separated)": "Hors périmètre (séparé par ;)",
        "Requirements and acceptance criteria": "Exigences et critères d'acceptation",
    }
    for label in dialog.findChildren(QLabel):
        if label.text() in replacements:
            label.setText(replacements[label.text()])
    for button in dialog.findChildren(QPushButton):
        mapping = {
            "Browse…": "Parcourir…",
            "Add requirement": "Ajouter une exigence",
            "Remove selected": "Supprimer la sélection",
        }
        if button.text() in mapping:
            button.setText(mapping[button.text()])
    box = dialog.findChild(QDialogButtonBox, "wizardButtons")
    if box is not None:
        ok = box.button(QDialogButtonBox.StandardButton.Ok)
        cancel = box.button(QDialogButtonBox.StandardButton.Cancel)
        if ok is not None:
            ok.setText("Créer le projet")
        if cancel is not None:
            cancel.setText("Annuler")


def create_project_dialog(parent=None, *, locale: str | None = None):
    """Return the accepted R14 wizard enhanced without changing its public widget contract."""
    from PySide6.QtWidgets import (
        QComboBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    from kodepoia.kodestudio.r14_project_wizard import create_project_dialog as create_r14_dialog
    from kodepoia.kodestudio.vision_chat import create_vision_assistant_dialog

    chosen_locale = resolve_locale(locale)
    tr = V11Translator(chosen_locale)
    dialog = create_r14_dialog(parent, locale=chosen_locale)
    _translate_base_wizard(dialog, chosen_locale)

    general_tab = dialog.tabs.widget(0)
    general_layout = general_tab.layout()
    helper = QGroupBox(tr.text("wizard.help.title"))
    helper.setObjectName("guidedCreationGroup")
    helper_form = QFormLayout(helper)

    genre_row = QWidget()
    genre_layout = QHBoxLayout(genre_row)
    genre_layout.setContentsMargins(0, 0, 0, 0)
    genre_combo = QComboBox()
    genre_combo.setObjectName("guidedGenreSelector")
    _add_options(
        genre_combo,
        GENRE_OPTIONS,
        chosen_locale,
        prompt="Choisir un genre…" if chosen_locale == "fr" else "Choose a genre…",
    )
    add_genre = QPushButton(tr.text("wizard.help.add"))
    add_genre.setObjectName("guidedGenreAddButton")
    genre_layout.addWidget(genre_combo, 1)
    genre_layout.addWidget(add_genre)
    helper_form.addRow(tr.text("wizard.help.genre"), genre_row)

    graphics_combo = QComboBox()
    graphics_combo.setObjectName("guidedGraphicsSelector")
    _add_options(
        graphics_combo,
        GRAPHICS_OPTIONS,
        chosen_locale,
        prompt="Choisir un style…" if chosen_locale == "fr" else "Choose a style…",
    )
    helper_form.addRow(tr.text("wizard.help.graphics"), graphics_combo)

    scope_combo = QComboBox()
    scope_combo.setObjectName("guidedScopeSelector")
    _add_options(
        scope_combo,
        SCOPE_OPTIONS,
        chosen_locale,
        prompt="Choisir une portée…" if chosen_locale == "fr" else "Choose a scope…",
    )
    helper_form.addRow(tr.text("wizard.help.scope"), scope_combo)

    audience_combo = QComboBox()
    audience_combo.setObjectName("guidedAudienceSelector")
    _add_options(
        audience_combo,
        AUDIENCE_OPTIONS,
        chosen_locale,
        prompt="Choisir un public…" if chosen_locale == "fr" else "Choose an audience…",
    )
    helper_form.addRow(tr.text("wizard.help.audience"), audience_combo)

    tip = QLabel(tr.text("wizard.help.tip"))
    tip.setWordWrap(True)
    helper_form.addRow(tip)
    if isinstance(general_layout, QFormLayout):
        general_layout.addRow(helper)
    else:
        general_layout.addWidget(helper)

    def selected_label(combo: QComboBox) -> str:
        return combo.currentText() if combo.currentData() is not None else ""

    add_genre.clicked.connect(lambda: _append_semicolon(dialog.genres, selected_label(genre_combo)))

    def apply_graphics(index: int) -> None:
        if index > 0:
            dialog.graphics_style.setText(graphics_combo.currentText())

    def apply_scope(index: int) -> None:
        if index > 0:
            prefix = "Portée" if chosen_locale == "fr" else "Scope"
            _append_semicolon(dialog.constraints, f"{prefix}: {scope_combo.currentText()}")

    def apply_audience(index: int) -> None:
        if index > 0:
            prefix = "Public" if chosen_locale == "fr" else "Audience"
            _append_semicolon(dialog.constraints, f"{prefix}: {audience_combo.currentText()}")

    graphics_combo.currentIndexChanged.connect(apply_graphics)
    scope_combo.currentIndexChanged.connect(apply_scope)
    audience_combo.currentIndexChanged.connect(apply_audience)

    product_tab = dialog.tabs.widget(3)
    product_layout = product_tab.layout()
    assistant_row = QWidget()
    assistant_layout = QVBoxLayout(assistant_row)
    assistant_layout.setContentsMargins(0, 0, 0, 0)
    assistant_hint = QLabel(
        "Kodepoia peut structurer ton idée et te poser les questions manquantes avant la création."
        if chosen_locale == "fr"
        else "Kodepoia can structure your idea and ask for missing details before creation."
    )
    assistant_hint.setWordWrap(True)
    assistant_button = QPushButton(tr.text("wizard.help.vision"))
    assistant_button.setObjectName("openVisionAssistantButton")
    assistant_layout.addWidget(assistant_hint)
    assistant_layout.addWidget(assistant_button)
    product_layout.insertWidget(0, assistant_row)

    def open_assistant() -> None:
        window = create_vision_assistant_dialog(
            dialog,
            locale=chosen_locale,
            initial_draft=_current_draft(dialog),
            apply_callback=lambda draft: _apply_draft(dialog, draft, chosen_locale),
        )
        window.exec()

    assistant_button.clicked.connect(open_assistant)

    dialog.guided_genre_selector = genre_combo
    dialog.guided_graphics_selector = graphics_combo
    dialog.guided_scope_selector = scope_combo
    dialog.guided_audience_selector = audience_combo
    dialog.open_vision_assistant_button = assistant_button
    dialog._kodepoia_apply_vision_draft = lambda draft: _apply_draft(dialog, draft, chosen_locale)
    return dialog


__all__ = ["create_project_dialog"]
