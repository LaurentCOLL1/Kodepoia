from __future__ import annotations

from typing import Any, Mapping

from kodepoia.quality.localization import KodeLocalization, LocaleCatalog, LocalizedMessage, pseudo_catalog

SOURCE_LOCALE = "en"
PSEUDO_LOCALE = "qps-ploc"

R11_SOURCE_CATALOG = LocaleCatalog(
    locale=SOURCE_LOCALE,
    messages=(
        LocalizedMessage.text("r11.nav", "Media / Franchise"),
        LocalizedMessage.text("r11.title", "Audio / Voice / Cinematics / Franchise"),
        LocalizedMessage.text(
            "r11.description",
            "Inspect governed R11 capabilities, accepted evidence and explicit blockers. Raw process commands, model paths, filter graphs, scripts and migration code are not exposed.",
        ),
        LocalizedMessage.text("r11.tabs.name", "R11 media and franchise workspace tabs"),
        LocalizedMessage.text(
            "r11.tabs.description",
            "Switch between Audio, Voice, Cinematics, Franchise and Persistence governed views.",
        ),
        LocalizedMessage.text("r11.tab.audio", "Audio"),
        LocalizedMessage.text("r11.tab.voice", "Voice"),
        LocalizedMessage.text("r11.tab.cinematics", "Cinematics"),
        LocalizedMessage.text("r11.tab.franchise", "Franchise / Canon"),
        LocalizedMessage.text("r11.tab.persistence", "Persistence"),
        LocalizedMessage.text("r11.column.capability", "Capability"),
        LocalizedMessage.text("r11.column.state", "State"),
        LocalizedMessage.text("r11.column.runtime", "Runtime"),
        LocalizedMessage.text("r11.column.subdivision", "Subdivision"),
        LocalizedMessage.text("r11.column.blockers", "Blockers"),
        LocalizedMessage.text("r11.table.name", "{tab} governed capability table"),
        LocalizedMessage.text(
            "r11.table.description",
            "Read-only accepted capability, runtime state, subdivision and blocker summary.",
        ),
        LocalizedMessage.text("r11.evidence.title", "Evidence / operations"),
        LocalizedMessage.text("r11.evidence.name", "{tab} evidence and operations"),
        LocalizedMessage.text(
            "r11.evidence.description",
            "Read-only structured accepted evidence, blockers and high-level operation identifiers.",
        ),
        LocalizedMessage.text("r11.blockers.none", "None"),
        LocalizedMessage.text("r11.refresh", "Refresh R11 status"),
        LocalizedMessage.text(
            "r11.refresh.description",
            "Refresh accepted R11 capability and evidence state without launching external runtimes.",
        ),
        LocalizedMessage.text("r11.cancel", "Cancel protected media operations"),
        LocalizedMessage.text(
            "r11.cancel.description",
            "Trigger the global emergency stop for protected external media processes.",
        ),
        LocalizedMessage.text("r11.operation.idle", "R11 workspace: IDLE"),
        LocalizedMessage.text("r11.operation.ready", "R11 workspace: READY"),
        LocalizedMessage.text(
            "r11.operation.cancelled",
            "R11 workspace: CANCELLED — {count} protected process(es) stopped",
        ),
    ),
)


class R11Translator:
    def __init__(self, locale: str = SOURCE_LOCALE) -> None:
        self.locale = locale
        if locale == SOURCE_LOCALE:
            self.catalog = R11_SOURCE_CATALOG
        elif locale == PSEUDO_LOCALE:
            self.catalog = pseudo_catalog(R11_SOURCE_CATALOG, locale=PSEUDO_LOCALE)
        else:
            self.catalog = LocaleCatalog(locale=locale, messages=(), fallback_locale=SOURCE_LOCALE)

    def text(self, message_id: str, **values: Any) -> str:
        return KodeLocalization(R11_SOURCE_CATALOG).translate(self.catalog, message_id, values=values)


def r11_nav_text(locale: str = SOURCE_LOCALE) -> str:
    return R11Translator(locale).text("r11.nav")


def registered_r11_messages() -> Mapping[str, str]:
    return {message.id: message.forms["other"] for message in R11_SOURCE_CATALOG.messages}


__all__ = [
    "PSEUDO_LOCALE",
    "R11_SOURCE_CATALOG",
    "R11Translator",
    "SOURCE_LOCALE",
    "r11_nav_text",
    "registered_r11_messages",
]
