from __future__ import annotations

from kodepoia.quality.localization import pseudo_localize_text


_EN = {
    "nav": "Data Curation",
    "title": "Governed data curation",
    "subtitle": (
        "Structured R15 experience governance and immutable dataset curation. "
        "Raw experience payloads and dataset rows are never displayed."
    ),
    "refresh": "Refresh",
    "experiences": "Governed experiences",
    "evidence": "Dedup / contamination evidence",
    "datasets": "Immutable datasets",
    "summary": "Curation summary",
    "preview_curation": "Preview curation",
    "apply_curation": "Apply curation",
    "preview_dataset": "Preview dataset build",
    "build_dataset": "Build immutable dataset",
    "inspect_dataset": "Inspect dataset",
    "confirm": "I confirm this governed mutation",
    "diagnostics": "Diagnostics JSON",
    "ready": "Curation workspace ready",
    "running": "Running governed R15 action…",
    "blocked": "Governed action blocked",
    "complete": "Governed action complete",
    "select_experience": "Select one experience row first.",
    "select_dataset": "Select one dataset row first.",
    "no_raw": (
        "No raw training payload is shown here. Project Knowledge, Research Packs, "
        "chat, memory and retrieved context are not training examples."
    ),
}

_FR = {
    "nav": "Curation des données",
    "title": "Curation gouvernée des données",
    "subtitle": (
        "Gouvernance structurée des expériences R15 et curation de datasets immuables. "
        "Les contenus bruts des expériences et les lignes de dataset ne sont jamais affichés."
    ),
    "refresh": "Actualiser",
    "experiences": "Expériences gouvernées",
    "evidence": "Preuves déduplication / contamination",
    "datasets": "Datasets immuables",
    "summary": "Résumé de curation",
    "preview_curation": "Prévisualiser la curation",
    "apply_curation": "Appliquer la curation",
    "preview_dataset": "Prévisualiser le build du dataset",
    "build_dataset": "Construire le dataset immuable",
    "inspect_dataset": "Inspecter le dataset",
    "confirm": "Je confirme cette mutation gouvernée",
    "diagnostics": "JSON de diagnostic",
    "ready": "Espace de curation prêt",
    "running": "Exécution de l’action R15 gouvernée…",
    "blocked": "Action gouvernée bloquée",
    "complete": "Action gouvernée terminée",
    "select_experience": "Sélectionnez d’abord une ligne d’expérience.",
    "select_dataset": "Sélectionnez d’abord une ligne de dataset.",
    "no_raw": (
        "Aucun contenu brut d’entraînement n’est affiché ici. Project Knowledge, "
        "Research Packs, chat, mémoire et contexte récupéré ne sont pas des exemples d’entraînement."
    ),
}


class ModelLabCurationTranslator:
    def __init__(self, locale: str = "en") -> None:
        normalized = locale.lower()
        self.locale = (
            "qps-ploc"
            if normalized == "qps-ploc"
            else "fr"
            if normalized.startswith("fr")
            else "en"
        )
        self._table = _FR if self.locale == "fr" else _EN

    def text(self, key: str) -> str:
        try:
            value = self._table[key]
        except KeyError as exc:
            raise KeyError(f"unknown Model Lab curation localization key: {key}") from exc
        return pseudo_localize_text(value) if self.locale == "qps-ploc" else value


def model_lab_curation_nav_text(locale: str = "en") -> str:
    return ModelLabCurationTranslator(locale).text("nav")


__all__ = ["ModelLabCurationTranslator", "model_lab_curation_nav_text"]
