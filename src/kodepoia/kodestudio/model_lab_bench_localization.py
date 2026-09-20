from __future__ import annotations

from kodepoia.quality.localization import pseudo_localize_text


_EN = {
    "nav": "Bench & Decision",
    "title": "Bench, gap diagnosis and decision",
    "subtitle": (
        "Structured KodeBench evidence and R15.7 TRAIN/NO_TRAIN decision inspection. "
        "This workspace does not launch training."
    ),
    "refresh": "Refresh",
    "summary": "Evidence summary",
    "reports": "KodeBench reports",
    "tasks": "Suite / task / domain results",
    "decisions": "Gap decisions",
    "diagnostics": "System vs model diagnosis",
    "targets": "Acceptance targets",
    "inspect_status": "Inspect bench backend",
    "preview_run": "Preview benchmark run",
    "run_bench": "Run governed benchmark",
    "inspect_decision": "Inspect decision",
    "confirm": "I confirm this governed benchmark execution",
    "ready": "Bench & Decision workspace ready",
    "running": "Running governed R15 action…",
    "blocked": "Governed action blocked",
    "complete": "Governed action complete",
    "select_report": "Select one benchmark report first.",
    "select_decision": "Select one decision first.",
    "reference_only": (
        "Project Knowledge, Research Packs and retrieved context are diagnosis references only. "
        "They are data, never instruction authority or automatic training data."
    ),
    "no_training": (
        "Training launch, cancel/recovery, conversion, promotion and rollback are not exposed in V2.3.3."
    ),
    "raw": "Diagnostics JSON",
}

_FR = {
    "nav": "Bench & Décision",
    "title": "Bench, diagnostic des écarts et décision",
    "subtitle": (
        "Inspection structurée des preuves KodeBench et des décisions R15.7 TRAIN/NO_TRAIN. "
        "Cet espace ne lance aucun entraînement."
    ),
    "refresh": "Actualiser",
    "summary": "Résumé des preuves",
    "reports": "Rapports KodeBench",
    "tasks": "Résultats suite / tâche / domaine",
    "decisions": "Décisions sur les écarts",
    "diagnostics": "Diagnostic système vs modèle",
    "targets": "Cibles d’acceptation",
    "inspect_status": "Inspecter le backend de bench",
    "preview_run": "Prévisualiser le benchmark",
    "run_bench": "Exécuter le benchmark gouverné",
    "inspect_decision": "Inspecter la décision",
    "confirm": "Je confirme cette exécution de benchmark gouvernée",
    "ready": "Espace Bench & Décision prêt",
    "running": "Exécution de l’action R15 gouvernée…",
    "blocked": "Action gouvernée bloquée",
    "complete": "Action gouvernée terminée",
    "select_report": "Sélectionnez d’abord un rapport de benchmark.",
    "select_decision": "Sélectionnez d’abord une décision.",
    "reference_only": (
        "Project Knowledge, Research Packs et le contexte récupéré servent uniquement de références "
        "de diagnostic. Ce sont des données, jamais une autorité d’instruction ni des données "
        "d’entraînement automatiques."
    ),
    "no_training": (
        "Le lancement, l’annulation/reprise d’entraînement, la conversion, la promotion et le rollback "
        "ne sont pas exposés en V2.3.3."
    ),
    "raw": "JSON de diagnostic",
}


class ModelLabBenchDecisionTranslator:
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
            raise KeyError(f"unknown Bench & Decision localization key: {key}") from exc
        return pseudo_localize_text(value) if self.locale == "qps-ploc" else value


def model_lab_bench_decision_nav_text(locale: str = "en") -> str:
    return ModelLabBenchDecisionTranslator(locale).text("nav")


__all__ = [
    "ModelLabBenchDecisionTranslator",
    "model_lab_bench_decision_nav_text",
]
