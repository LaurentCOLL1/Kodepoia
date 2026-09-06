from __future__ import annotations

import locale as system_locale
import os
from dataclasses import dataclass

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "app.title": "Kodepoia — KodeStudio",
        "nav.chat": "Chat",
        "nav.projects": "Projects",
        "nav.research": "Research",
        "nav.vault": "Vault",
        "nav.comfy": "ComfyUI",
        "nav.security": "Security",
        "nav.audit": "Audit",
        "nav.settings": "Settings",
        "projects.new": "New project…",
        "chat.title": "Chat & Project Vision",
        "chat.intro": (
            "Describe your idea in your own words. Kodepoia structures it, asks for missing "
            "details and helps keep the Vision consistent when it changes."
        ),
        "chat.model": "Local model",
        "chat.guided": "Guided mode (no model required)",
        "chat.refresh": "Refresh local models",
        "chat.input": "What do you want to create or change?",
        "chat.send": "Send",
        "chat.clear": "New conversation",
        "chat.save": "Save draft",
        "chat.apply": "Apply to project Vision",
        "chat.no_project": "No project folder selected; the draft remains in this session.",
        "chat.saved": "Vision draft saved locally: {path}",
        "chat.error": "Vision assistant error: {reason}",
        "wizard.help.title": "Guided creation",
        "wizard.help.genre": "Add a genre",
        "wizard.help.graphics": "Visual style",
        "wizard.help.scope": "Project scope",
        "wizard.help.audience": "Primary audience",
        "wizard.help.add": "Add",
        "wizard.help.vision": "Help me build the Vision…",
        "wizard.help.tip": (
            "These lists are suggestions, not restrictions. You can always type your own values."
        ),
        "wizard.vision.title": "Vision Assistant",
        "wizard.vision.apply": "Apply this Vision",
        "wizard.vision.close": "Close",
        "settings.language": "Language",
        "settings.restart": "The selected language is used the next time KodeStudio starts.",
        "updates.title": "Updates",
        "updates.installed": "Installed version",
        "updates.channel": "Update channel",
        "updates.stable": "Stable",
        "updates.beta": "Beta",
        "updates.nightly": "Nightly / development",
        "updates.beta_warning": "The beta channel can offer less stable prerelease builds.",
        "updates.nightly_warning": (
            "The nightly/development channel can offer very recent, experimental, less stable builds."
        ),
        "updates.periodic": "Check periodically for updates",
        "updates.interval": "Interval (hours)",
        "updates.check": "Check for updates",
        "updates.never_startup": (
            "Update checks never gate startup and no installer is launched automatically."
        ),
        "updates.checking": "Checking trusted update metadata…",
        "updates.up-to-date": "Up to date",
        "updates.update-available": "Update available",
        "updates.offline": "Offline",
        "updates.metadata-expired": "Metadata expired",
        "updates.verification-failed": "Verification failed",
        "updates.channel-unavailable": "Channel unavailable",
        "updates.update-withdrawn": "Update withdrawn",
        "updates.candidate": "Candidate",
        "updates.verified": "Source verification",
        "updates.size": "Declared size",
        "updates.notes": "Notes",
        "updates.signing": "Signing (TUF metadata report; not verified here)",
        "updates.provenance": "Provenance (TUF metadata report; not verified here)",
    },
    "fr": {
        "app.title": "Kodepoia — KodeStudio",
        "nav.chat": "Chat",
        "nav.projects": "Projets",
        "nav.research": "Recherche",
        "nav.vault": "Bibliothèque",
        "nav.comfy": "ComfyUI",
        "nav.security": "Sécurité",
        "nav.audit": "Audit",
        "nav.settings": "Paramètres",
        "projects.new": "Nouveau projet…",
        "chat.title": "Chat & Vision du projet",
        "chat.intro": (
            "Décris ton idée avec tes mots. Kodepoia la structure, demande les précisions "
            "manquantes et aide à garder la Vision cohérente lorsqu'elle évolue."
        ),
        "chat.model": "Modèle local",
        "chat.guided": "Mode guidé (aucun modèle requis)",
        "chat.refresh": "Actualiser les modèles locaux",
        "chat.input": "Que veux-tu créer, préciser ou modifier ?",
        "chat.send": "Envoyer",
        "chat.clear": "Nouvelle conversation",
        "chat.save": "Enregistrer le brouillon",
        "chat.apply": "Appliquer à la Vision du projet",
        "chat.no_project": (
            "Aucun dossier de projet sélectionné ; le brouillon reste disponible dans cette session."
        ),
        "chat.saved": "Brouillon de Vision enregistré localement : {path}",
        "chat.error": "Erreur de l'assistant Vision : {reason}",
        "wizard.help.title": "Création guidée",
        "wizard.help.genre": "Ajouter un genre",
        "wizard.help.graphics": "Style graphique",
        "wizard.help.scope": "Portée du projet",
        "wizard.help.audience": "Public principal",
        "wizard.help.add": "Ajouter",
        "wizard.help.vision": "M'aider à construire la Vision…",
        "wizard.help.tip": (
            "Ces listes sont des suggestions, pas des restrictions. Tu peux toujours saisir "
            "tes propres valeurs."
        ),
        "wizard.vision.title": "Assistant Vision",
        "wizard.vision.apply": "Appliquer cette Vision",
        "wizard.vision.close": "Fermer",
        "settings.language": "Langue",
        "settings.restart": "La langue sélectionnée sera utilisée au prochain démarrage de KodeStudio.",
        "updates.title": "Mises à jour",
        "updates.installed": "Version installée",
        "updates.channel": "Canal de mise à jour",
        "updates.stable": "Stable",
        "updates.beta": "Bêta",
        "updates.nightly": "Nightly / développement",
        "updates.beta_warning": (
            "Le canal bêta peut proposer des versions de prépublication moins stables."
        ),
        "updates.nightly_warning": (
            "Le canal nightly/développement peut proposer des versions très récentes, "
            "expérimentales et moins stables."
        ),
        "updates.periodic": "Vérifier périodiquement les mises à jour",
        "updates.interval": "Intervalle (heures)",
        "updates.check": "Rechercher des mises à jour",
        "updates.never_startup": (
            "La vérification n'est jamais une dépendance du démarrage et aucun installateur "
            "n'est lancé automatiquement."
        ),
        "updates.checking": "Vérification des métadonnées de mise à jour…",
        "updates.up-to-date": "À jour",
        "updates.update-available": "Mise à jour disponible",
        "updates.offline": "Hors ligne",
        "updates.metadata-expired": "Métadonnées expirées",
        "updates.verification-failed": "Échec de vérification",
        "updates.channel-unavailable": "Canal indisponible",
        "updates.update-withdrawn": "Mise à jour retirée",
        "updates.candidate": "Candidate",
        "updates.verified": "Vérification source",
        "updates.size": "Taille annoncée",
        "updates.notes": "Notes",
        "updates.signing": "Signature (rapport TUF, non vérifiée ici)",
        "updates.provenance": "Provenance (rapport TUF, non vérifiée ici)",
    },
}


def resolve_locale(requested: str | None = None, *, system_name: str | None = None) -> str:
    explicit = (requested or os.environ.get("KODEPOIA_LOCALE") or "").strip().lower()
    if explicit:
        return "fr" if explicit.startswith("fr") else "en"
    detected = system_name
    if not detected:
        detected = system_locale.getlocale()[0] or ""
    return "fr" if detected.lower().startswith("fr") else "en"


@dataclass(frozen=True, slots=True)
class V11Translator:
    locale: str = "en"

    def text(self, key: str, **values: object) -> str:
        chosen = "fr" if self.locale.lower().startswith("fr") else "en"
        template = MESSAGES.get(chosen, MESSAGES["en"]).get(key, MESSAGES["en"].get(key, key))
        return template.format(**values)


__all__ = ["MESSAGES", "V11Translator", "resolve_locale"]
