from __future__ import annotations

from typing import Any, Mapping

from kodepoia.quality.localization import KodeLocalization, LocaleCatalog, LocalizedMessage, pseudo_catalog

SOURCE_LOCALE = "en"
PSEUDO_LOCALE = "qps-ploc"

R13_WIZARD_SOURCE_CATALOG = LocaleCatalog(
    locale=SOURCE_LOCALE,
    messages=(
        LocalizedMessage.text("r13.wizard.tab", "Mobile"),
        LocalizedMessage.text("r13.wizard.source", "Source"),
        LocalizedMessage.text("r13.wizard.form_factors", "Form factors"),
        LocalizedMessage.text("r13.wizard.android_id", "Android application ID"),
        LocalizedMessage.text("r13.wizard.android_min", "Android minimum API"),
        LocalizedMessage.text("r13.wizard.android_target", "Android target API"),
        LocalizedMessage.text("r13.wizard.apple_id", "Apple bundle ID"),
        LocalizedMessage.text("r13.wizard.apple_min", "Apple minimum OS"),
        LocalizedMessage.text("r13.wizard.apple_target", "Apple target OS intent"),
        LocalizedMessage.text("r13.wizard.network", "Network intent"),
        LocalizedMessage.text("r13.wizard.release", "Release channel"),
        LocalizedMessage.text("r13.wizard.signing", "Signing intent"),
        LocalizedMessage.text("r13.wizard.permissions", "Permissions (; separated)"),
        LocalizedMessage.text("r13.wizard.capabilities", "Capabilities (; separated)"),
        LocalizedMessage.text("r13.wizard.package_mb", "Maximum package MB"),
        LocalizedMessage.text("r13.wizard.build_seconds", "Maximum build seconds"),
        LocalizedMessage.text("r13.wizard.matrix_runs", "Maximum device matrix runs"),
        LocalizedMessage.text(
            "r13.wizard.intent_only",
            "Intent only — this wizard never installs an SDK, builds, signs, accesses a device, or contacts a store.",
        ),
    ),
)


class R13WizardTranslator:
    def __init__(self, locale: str = SOURCE_LOCALE) -> None:
        self.locale = locale
        if locale == SOURCE_LOCALE:
            self.catalog = R13_WIZARD_SOURCE_CATALOG
        elif locale == PSEUDO_LOCALE:
            self.catalog = pseudo_catalog(R13_WIZARD_SOURCE_CATALOG, locale=PSEUDO_LOCALE)
        else:
            self.catalog = LocaleCatalog(locale=locale, messages=(), fallback_locale=SOURCE_LOCALE)

    def text(self, message_id: str, **values: Any) -> str:
        return KodeLocalization(R13_WIZARD_SOURCE_CATALOG).translate(
            self.catalog, message_id, values=values
        )


def registered_r13_wizard_messages() -> Mapping[str, str]:
    return {
        message.id: message.forms["other"]
        for message in R13_WIZARD_SOURCE_CATALOG.messages
    }


__all__ = [
    "PSEUDO_LOCALE",
    "R13_WIZARD_SOURCE_CATALOG",
    "R13WizardTranslator",
    "SOURCE_LOCALE",
    "registered_r13_wizard_messages",
]
