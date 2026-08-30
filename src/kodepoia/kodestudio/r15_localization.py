from __future__ import annotations

from kodepoia.quality.localization import pseudo_localize_text


_EN = {
    "nav": "Experience & Tune",
    "title": "Experience, Bench & Tune",
    "subtitle": (
        "Structured R15 status, dry-run, evidence and permission-gated workflows. "
        "Raw shell commands, secrets and quarantined content are never exposed."
    ),
    "domain": "Domain",
    "action": "Action",
    "identifier": "Stable ID",
    "identifier_hint": (
        "Immutable candidate, run, dataset or evidence ID when the selected action requires one."
    ),
    "confirm": "I confirm this requested mutation",
    "dry_run": "Dry-run",
    "execute": "Execute governed action",
    "status": "Refresh status",
    "catalog": "Show capability catalog",
    "evidence": "Export redacted evidence",
    "result": "Structured redacted result",
    "status_ready": "R15 Experience & Tune controls ready",
    "status_running": "R15 governed operation running",
    "status_complete": "R15 governed operation completed",
    "status_blocked": "R15 operation blocked by policy",
}

_FR = {
    "nav": "Expérience et Tune",
    "title": "Expérience, Bench et Tune",
    "subtitle": (
        "Statut, simulation, preuves et workflows R15 structurés avec permissions explicites. "
        "Les commandes shell brutes, secrets et contenus en quarantaine ne sont jamais exposés."
    ),
    "domain": "Domaine",
    "action": "Action",
    "identifier": "ID stable",
    "identifier_hint": (
        "ID immuable de candidat, exécution, dataset ou preuve lorsque l’action sélectionnée l’exige."
    ),
    "confirm": "Je confirme cette mutation demandée",
    "dry_run": "Simuler",
    "execute": "Exécuter l’action gouvernée",
    "status": "Actualiser le statut",
    "catalog": "Afficher le catalogue des capacités",
    "evidence": "Exporter les preuves expurgées",
    "result": "Résultat structuré expurgé",
    "status_ready": "Contrôles R15 Expérience et Tune prêts",
    "status_running": "Opération R15 gouvernée en cours",
    "status_complete": "Opération R15 gouvernée terminée",
    "status_blocked": "Opération R15 bloquée par la politique",
}


class R15Translator:
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
            raise KeyError(f"unknown R15 KodeStudio localization key: {key}") from exc
        return pseudo_localize_text(value) if self.locale == "qps-ploc" else value


def r15_nav_text(locale: str = "en") -> str:
    return R15Translator(locale).text("nav")
