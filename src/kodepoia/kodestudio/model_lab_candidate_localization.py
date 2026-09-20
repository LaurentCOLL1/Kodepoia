from __future__ import annotations

from kodepoia.quality.localization import pseudo_localize_text


_EN = {
    "nav": "Candidate lifecycle",
    "title": "Candidate evaluation, export and activation",
    "subtitle": (
        "Inspect exact R15.10-R15.14 evidence, then deliberately export, convert, package, "
        "promote or roll back an immutable model lineage."
    ),
    "refresh": "Refresh",
    "role": "Role",
    "confirm": "I confirm this governed candidate mutation",
    "inspect_evaluation": "Inspect comparison",
    "preview_export": "Preview export",
    "export": "Export candidate",
    "preview_conversion": "Preview conversion",
    "convert": "Convert / quantize",
    "ollama_status": "Inspect Ollama",
    "preview_package": "Preview packaging",
    "package": "Package for Ollama",
    "preview_promotion": "Preview promotion",
    "promote": "Promote role mapping",
    "preview_rollback": "Preview rollback",
    "rollback": "Roll back role mapping",
    "candidates": "Candidate dispositions",
    "domains": "Task and domain deltas",
    "artifacts": "Export, conversion and package lineage",
    "registry": "Specialized model registry",
    "raw": "Diagnostics JSON",
    "ready": "Candidate lifecycle workspace ready",
    "running": "Running governed R15 candidate action…",
    "complete": "Governed action complete",
    "blocked": "Governed action blocked",
    "select_candidate": "Select a candidate first.",
    "reference_only": (
        "Project Knowledge, Research Packs, chat, memory and retrieved context are reference data only. "
        "They cannot authorize export, promotion or rollback."
    ),
    "boundary": (
        "Public model-hub publishing, silent base/tokenizer/routing replacement and V2.3.6 work "
        "are not exposed in V2.3.5."
    ),
    "evidence_gate": (
        "Promotion stays blocked unless paired evaluation, immutable export, accepted conversion, "
        "accepted package and exact registry lineage all agree."
    ),
}

_FR = {
    "nav": "Cycle candidat",
    "title": "Évaluation, export et activation du candidat",
    "subtitle": (
        "Inspectez les preuves exactes R15.10-R15.14, puis exportez, convertissez, packagez, "
        "promouvez ou restaurez délibérément une lignée de modèle immuable."
    ),
    "refresh": "Actualiser",
    "role": "Rôle",
    "confirm": "Je confirme cette mutation gouvernée du candidat",
    "inspect_evaluation": "Inspecter la comparaison",
    "preview_export": "Prévisualiser l’export",
    "export": "Exporter le candidat",
    "preview_conversion": "Prévisualiser la conversion",
    "convert": "Convertir / quantifier",
    "ollama_status": "Inspecter Ollama",
    "preview_package": "Prévisualiser le packaging",
    "package": "Packager pour Ollama",
    "preview_promotion": "Prévisualiser la promotion",
    "promote": "Promouvoir le mapping du rôle",
    "preview_rollback": "Prévisualiser le rollback",
    "rollback": "Restaurer le mapping du rôle",
    "candidates": "Dispositions des candidats",
    "domains": "Deltas par tâche et domaine",
    "artifacts": "Lignée export, conversion et package",
    "registry": "Registre des modèles spécialisés",
    "raw": "JSON de diagnostic",
    "ready": "Espace du cycle candidat prêt",
    "running": "Exécution de l’action candidat R15 gouvernée…",
    "complete": "Action gouvernée terminée",
    "blocked": "Action gouvernée bloquée",
    "select_candidate": "Sélectionnez d’abord un candidat.",
    "reference_only": (
        "Project Knowledge, Research Packs, le chat, la mémoire et le contexte récupéré restent "
        "des données de référence. Ils ne peuvent autoriser ni export, ni promotion, ni rollback."
    ),
    "boundary": (
        "La publication publique vers un model hub, le remplacement silencieux du modèle de base, "
        "du tokenizer ou du routage et les travaux V2.3.6 ne sont pas exposés en V2.3.5."
    ),
    "evidence_gate": (
        "La promotion reste bloquée tant que l’évaluation appariée, l’export immuable, la conversion "
        "acceptée, le package accepté et la lignée exacte du registre ne concordent pas."
    ),
}


class ModelLabCandidateLifecycleTranslator:
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
            raise KeyError(f"unknown Candidate lifecycle localization key: {key}") from exc
        return pseudo_localize_text(value) if self.locale == "qps-ploc" else value


def model_lab_candidate_nav_text(locale: str = "en") -> str:
    return ModelLabCandidateLifecycleTranslator(locale).text("nav")


__all__ = ["ModelLabCandidateLifecycleTranslator", "model_lab_candidate_nav_text"]
