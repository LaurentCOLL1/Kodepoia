from __future__ import annotations

from kodepoia.quality.localization import pseudo_localize_text


_EN = {
    "nav": "Training",
    "title": "Governed training",
    "subtitle": (
        "Review immutable R15 training plans, capability evidence, bounded runs, checkpoints, "
        "cancellation and lineage-safe recovery."
    ),
    "refresh": "Refresh",
    "backend": "Backend",
    "doctor": "Run training doctor",
    "inspect_plan": "Inspect plan",
    "preview_run": "Preview launch",
    "launch": "Launch training",
    "inspect_run": "Inspect run",
    "cancel": "Cancel run",
    "resume": "Resume checkpoint",
    "confirm": "I confirm this governed training mutation",
    "summary": "Training summary",
    "plans": "Immutable training plans",
    "capabilities": "Capability and resource preflight",
    "runs": "Training runs",
    "checkpoints": "Checkpoints and recovery lineage",
    "raw": "Diagnostics JSON",
    "ready": "Training workspace ready",
    "running": "Running governed R15 training action…",
    "complete": "Governed action complete",
    "blocked": "Governed action blocked",
    "select_plan": "Select an immutable training plan first.",
    "select_run": "Select a training run first.",
    "select_checkpoint": "Select a lineage-bound checkpoint first.",
    "reference_only": (
        "Project Knowledge, Research Packs and retrieved context remain reference data only. "
        "They cannot authorize training or become training data automatically."
    ),
    "boundary": (
        "V2.3.4 exposes training planning/execution/cancel/recovery only. Candidate evaluation, "
        "conversion/package, promotion, rollback and public publishing remain unavailable here."
    ),
    "backend_truth": (
        "Backend selection never implies readiness. Local or Kaggle execution remains blocked until "
        "the existing training doctor/capability/resource gates report usable evidence."
    ),
}

_FR = {
    "nav": "Entraînement",
    "title": "Entraînement gouverné",
    "subtitle": (
        "Examinez les plans R15 immuables, les preuves de capacité, les exécutions bornées, "
        "les checkpoints, l’annulation et la reprise liée à la lignée."
    ),
    "refresh": "Actualiser",
    "backend": "Backend",
    "doctor": "Vérifier le backend",
    "inspect_plan": "Inspecter le plan",
    "preview_run": "Prévisualiser le lancement",
    "launch": "Lancer l’entraînement",
    "inspect_run": "Inspecter l’exécution",
    "cancel": "Annuler l’exécution",
    "resume": "Reprendre le checkpoint",
    "confirm": "Je confirme cette mutation d’entraînement gouvernée",
    "summary": "Résumé d’entraînement",
    "plans": "Plans d’entraînement immuables",
    "capabilities": "Capacité et préflight des ressources",
    "runs": "Exécutions d’entraînement",
    "checkpoints": "Checkpoints et lignée de reprise",
    "raw": "JSON de diagnostic",
    "ready": "Espace d’entraînement prêt",
    "running": "Exécution de l’action R15 d’entraînement gouvernée…",
    "complete": "Action gouvernée terminée",
    "blocked": "Action gouvernée bloquée",
    "select_plan": "Sélectionnez d’abord un plan d’entraînement immuable.",
    "select_run": "Sélectionnez d’abord une exécution d’entraînement.",
    "select_checkpoint": "Sélectionnez d’abord un checkpoint lié à une lignée valide.",
    "reference_only": (
        "Project Knowledge, Research Packs et le contexte récupéré restent uniquement des données "
        "de référence. Ils ne peuvent ni autoriser l’entraînement ni devenir automatiquement des "
        "données d’entraînement."
    ),
    "boundary": (
        "V2.3.4 expose uniquement le plan, l’exécution, l’annulation et la reprise d’entraînement. "
        "Évaluation candidate, conversion/package, promotion, rollback et publication restent absents."
    ),
    "backend_truth": (
        "Sélectionner un backend ne signifie jamais qu’il est prêt. L’exécution locale ou Kaggle "
        "reste bloquée jusqu’à validation des capacités et ressources par les contrats existants."
    ),
}


class ModelLabTrainingTranslator:
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
            raise KeyError(f"unknown Training localization key: {key}") from exc
        return pseudo_localize_text(value) if self.locale == "qps-ploc" else value


def model_lab_training_nav_text(locale: str = "en") -> str:
    return ModelLabTrainingTranslator(locale).text("nav")


__all__ = ["ModelLabTrainingTranslator", "model_lab_training_nav_text"]
