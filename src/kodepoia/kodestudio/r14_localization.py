from __future__ import annotations

from kodepoia.quality.localization import pseudo_localize_text


_EN = {
    "nav": "Backend & LiveOps",
    "title": "Backend & LiveOps",
    "subtitle": "Structured inspection, preview and authorized operations. Raw commands, endpoints and secrets are never accepted.",
    "environment": "Environment",
    "operation": "Operation",
    "action": "Action",
    "mode": "Mode",
    "resource": "Resource ID",
    "confirm": "I confirm this requested mutation",
    "execute": "Run governed operation",
    "catalog": "Show capability catalog",
    "result": "Structured result",
    "status_ready": "Backend & LiveOps controls ready",
    "status_blocked": "Operation blocked by R14.16 policy",
    "status_complete": "Backend & LiveOps operation completed",
    "resource_hint": "Stable resource identifier only; raw URLs/endpoints are forbidden.",
}

_FR = {
    "nav": "Backend et LiveOps",
    "title": "Backend et LiveOps",
    "subtitle": "Inspection, prévisualisation et opérations autorisées structurées. Les commandes brutes, endpoints et secrets ne sont jamais acceptés.",
    "environment": "Environnement",
    "operation": "Opération",
    "action": "Action",
    "mode": "Mode",
    "resource": "ID de ressource",
    "confirm": "Je confirme cette mutation demandée",
    "execute": "Exécuter l’opération gouvernée",
    "catalog": "Afficher le catalogue des capacités",
    "result": "Résultat structuré",
    "status_ready": "Contrôles Backend et LiveOps prêts",
    "status_blocked": "Opération bloquée par la politique R14.16",
    "status_complete": "Opération Backend et LiveOps terminée",
    "resource_hint": "Identifiant stable uniquement ; les URL/endpoints bruts sont interdits.",
}


class R14Translator:
    def __init__(self, locale: str = "en") -> None:
        normalized = locale.lower()
        self.locale = "qps-ploc" if normalized == "qps-ploc" else "fr" if normalized.startswith("fr") else "en"
        self._table = _FR if self.locale == "fr" else _EN

    def text(self, key: str) -> str:
        try:
            value = self._table[key]
        except KeyError as exc:
            raise KeyError(f"unknown R14 KodeStudio localization key: {key}") from exc
        return pseudo_localize_text(value) if self.locale == "qps-ploc" else value


def r14_nav_text(locale: str = "en") -> str:
    return R14Translator(locale).text("nav")
