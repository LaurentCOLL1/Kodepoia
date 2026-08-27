from __future__ import annotations

from typing import Any, Mapping

from kodepoia.quality.localization import KodeLocalization, LocaleCatalog, LocalizedMessage, pseudo_catalog

SOURCE_LOCALE = "en"
PSEUDO_LOCALE = "qps-ploc"

R13_SOURCE_CATALOG = LocaleCatalog(
    locale=SOURCE_LOCALE,
    messages=(
        LocalizedMessage.text("r13.nav", "Mobile & Release"),
        LocalizedMessage.text("r13.title", "Mobile, DeviceLab & Release workspace"),
        LocalizedMessage.text(
            "r13.description",
            "Inspect Project Wizard mobile intent, capability blockers and read-only evidence. Refresh is passive; execution uses explicit governed intents only.",
        ),
        LocalizedMessage.text("r13.project", "Project"),
        LocalizedMessage.text("r13.platforms", "Platforms"),
        LocalizedMessage.text("r13.source", "Source"),
        LocalizedMessage.text("r13.channel", "Release channel"),
        LocalizedMessage.text("r13.signing", "Signing intent"),
        LocalizedMessage.text("r13.state", "Workspace state"),
        LocalizedMessage.text("r13.blockers", "Blockers"),
        LocalizedMessage.text("r13.refresh", "Refresh status"),
        LocalizedMessage.text("r13.scaffold", "Scaffold"),
        LocalizedMessage.text("r13.build", "Build"),
        LocalizedMessage.text("r13.test", "Test"),
        LocalizedMessage.text("r13.package", "Package"),
        LocalizedMessage.text("r13.device", "DeviceLab"),
        LocalizedMessage.text("r13.compliance", "Compliance"),
        LocalizedMessage.text("r13.release", "Release"),
        LocalizedMessage.text("r13.cancel", "Cancel protected mobile operations"),
        LocalizedMessage.text("r13.evidence", "Read-only R13 evidence and capability matrix"),
        LocalizedMessage.text("r13.idle", "R13 workspace: IDLE"),
        LocalizedMessage.text(
            "r13.cancelled",
            "R13 workspace: CANCELLED — {count} protected process(es) stopped",
        ),
        LocalizedMessage.text("r13.result", "R13 {operation}: {state} — {summary}"),
    ),
)


class R13Translator:
    def __init__(self, locale: str = SOURCE_LOCALE) -> None:
        self.locale = locale
        if locale == SOURCE_LOCALE:
            self.catalog = R13_SOURCE_CATALOG
        elif locale == PSEUDO_LOCALE:
            self.catalog = pseudo_catalog(R13_SOURCE_CATALOG, locale=PSEUDO_LOCALE)
        else:
            self.catalog = LocaleCatalog(locale=locale, messages=(), fallback_locale=SOURCE_LOCALE)

    def text(self, message_id: str, **values: Any) -> str:
        return KodeLocalization(R13_SOURCE_CATALOG).translate(self.catalog, message_id, values=values)


def r13_nav_text(locale: str = SOURCE_LOCALE) -> str:
    return R13Translator(locale).text("r13.nav")


def registered_r13_messages() -> Mapping[str, str]:
    return {message.id: message.forms["other"] for message in R13_SOURCE_CATALOG.messages}


__all__ = [
    "PSEUDO_LOCALE",
    "R13_SOURCE_CATALOG",
    "R13Translator",
    "SOURCE_LOCALE",
    "r13_nav_text",
    "registered_r13_messages",
]
