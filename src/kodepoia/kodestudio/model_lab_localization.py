from __future__ import annotations

from kodepoia.quality.localization import pseudo_localize_text


_EN = {
    "nav": "Model Lab",
    "title": "Model Lab",
    "subtitle": (
        "Read-only V2.3.1 inventory of governed R15 datasets, benchmark/training evidence, "
        "specialized-model lineage and optional local runtime state. No training or promotion is available here."
    ),
    "refresh_inventory": "Refresh inventory",
    "refresh_runtime": "Refresh Ollama / Kaggle",
    "state_ready": "Model Lab inventory ready",
    "state_runtime": "Refreshing read-only runtime state…",
    "state_error": "Model Lab read failed",
    "stores": "Evidence stores",
    "evidence": "Governed evidence",
    "registry": "Specialized model registry",
    "models": "Local Ollama inventory",
    "capabilities": "Training dependency capability",
    "lineage": "Lineage",
    "diagnostics": "Diagnostics JSON",
    "read_only": "Read-only: dataset build, training, conversion, promotion and rollback are disabled in V2.3.1.",
    "not_checked": "not checked",
    "missing": "missing",
    "none": "none",
}

_FR = {
    "nav": "Laboratoire modèles",
    "title": "Laboratoire modèles",
    "subtitle": (
        "Inventaire V2.3.1 en lecture seule des jeux de données R15 gouvernés, preuves de benchmark/entraînement, "
        "lignage des modèles spécialisés et état local optionnel. Aucun entraînement ni promotion n'est disponible ici."
    ),
    "refresh_inventory": "Actualiser l’inventaire",
    "refresh_runtime": "Actualiser Ollama / Kaggle",
    "state_ready": "Inventaire du laboratoire modèles prêt",
    "state_runtime": "Actualisation de l’état runtime en lecture seule…",
    "state_error": "Lecture du laboratoire modèles échouée",
    "stores": "Stores de preuves",
    "evidence": "Preuves gouvernées",
    "registry": "Registre des modèles spécialisés",
    "models": "Inventaire Ollama local",
    "capabilities": "Capacités des dépendances d’entraînement",
    "lineage": "Lignage",
    "diagnostics": "JSON de diagnostic",
    "read_only": "Lecture seule : construction de dataset, entraînement, conversion, promotion et rollback sont désactivés en V2.3.1.",
    "not_checked": "non vérifié",
    "missing": "absent",
    "none": "aucun",
}


class ModelLabTranslator:
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
            raise KeyError(f"unknown Model Lab localization key: {key}") from exc
        return pseudo_localize_text(value) if self.locale == "qps-ploc" else value


def model_lab_nav_text(locale: str = "en") -> str:
    return ModelLabTranslator(locale).text("nav")


__all__ = ["ModelLabTranslator", "model_lab_nav_text"]
