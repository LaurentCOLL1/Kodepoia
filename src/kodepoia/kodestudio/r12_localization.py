from __future__ import annotations

from typing import Any, Mapping

from kodepoia.quality.localization import KodeLocalization, LocaleCatalog, LocalizedMessage, pseudo_catalog

SOURCE_LOCALE = "en"
PSEUDO_LOCALE = "qps-ploc"

R12_SOURCE_CATALOG = LocaleCatalog(
    locale=SOURCE_LOCALE,
    messages=(
        LocalizedMessage.text("r12.nav", "Desktop"),
        LocalizedMessage.text("r12.title", "Desktop application workspace"),
        LocalizedMessage.text(
            "r12.description",
            "Inspect Project Wizard desktop intent, passive capability/evidence state, and explicit governed scaffold/build/test/package actions. Refresh never launches an external process.",
        ),
        LocalizedMessage.text("r12.project", "Project"),
        LocalizedMessage.text("r12.framework", "Framework"),
        LocalizedMessage.text("r12.architecture", "Architecture"),
        LocalizedMessage.text("r12.package", "Package"),
        LocalizedMessage.text("r12.state", "Workspace state"),
        LocalizedMessage.text("r12.blockers", "Blockers"),
        LocalizedMessage.text("r12.refresh", "Refresh status"),
        LocalizedMessage.text("r12.validate", "Validate"),
        LocalizedMessage.text("r12.scaffold", "Scaffold"),
        LocalizedMessage.text("r12.build", "Build"),
        LocalizedMessage.text("r12.test", "Test"),
        LocalizedMessage.text("r12.package_action", "Package"),
        LocalizedMessage.text("r12.cancel", "Cancel protected desktop operations"),
        LocalizedMessage.text("r12.evidence", "Read-only desktop evidence"),
        LocalizedMessage.text("r12.idle", "Desktop workspace: IDLE"),
        LocalizedMessage.text("r12.cancelled", "Desktop workspace: CANCELLED — {count} protected process(es) stopped"),
        LocalizedMessage.text("r12.result", "Desktop {operation}: {state} — {summary}"),
    ),
)


class R12Translator:
    def __init__(self, locale: str = SOURCE_LOCALE) -> None:
        self.locale = locale
        if locale == SOURCE_LOCALE:
            self.catalog = R12_SOURCE_CATALOG
        elif locale == PSEUDO_LOCALE:
            self.catalog = pseudo_catalog(R12_SOURCE_CATALOG, locale=PSEUDO_LOCALE)
        else:
            self.catalog = LocaleCatalog(locale=locale, messages=(), fallback_locale=SOURCE_LOCALE)

    def text(self, message_id: str, **values: Any) -> str:
        return KodeLocalization(R12_SOURCE_CATALOG).translate(self.catalog, message_id, values=values)


def r12_nav_text(locale: str = SOURCE_LOCALE) -> str:
    return R12Translator(locale).text("r12.nav")


def registered_r12_messages() -> Mapping[str, str]:
    return {message.id: message.forms["other"] for message in R12_SOURCE_CATALOG.messages}


__all__ = [
    "PSEUDO_LOCALE",
    "R12_SOURCE_CATALOG",
    "R12Translator",
    "SOURCE_LOCALE",
    "r12_nav_text",
    "registered_r12_messages",
]
