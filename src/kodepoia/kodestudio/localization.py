from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from kodepoia.quality.localization import KodeLocalization, LocaleCatalog, LocalizedMessage, pseudo_catalog


SOURCE_LOCALE = "en"
PSEUDO_LOCALE = "qps-ploc"


KODESTUDIO_SOURCE_CATALOG = LocaleCatalog(
    locale=SOURCE_LOCALE,
    messages=(
        LocalizedMessage.text("app.window.title", "Kodepoia — KodeStudio"),
        LocalizedMessage.text("app.nav.chat", "Chat"),
        LocalizedMessage.text("app.nav.projects", "Projects"),
        LocalizedMessage.text("app.nav.security", "Security"),
        LocalizedMessage.text("app.nav.audit", "Audit"),
        LocalizedMessage.text("app.nav.settings", "Settings"),
        LocalizedMessage.text("app.page.foundation", "KodeStudio foundation."),
        LocalizedMessage.text("app.projects.title", "Projects"),
        LocalizedMessage.text("app.projects.new", "New project…"),
        LocalizedMessage.text("app.security.title", "Protected Core"),
        LocalizedMessage.text("app.security.ready", "Emergency stop: READY"),
        LocalizedMessage.text(
            "app.security.active",
            "Emergency stop: ACTIVE — {count} process(es) stopped",
        ),
        LocalizedMessage.text("app.security.stop", "STOP ALL PROTECTED PROCESSES"),
        LocalizedMessage.text("app.security.reset", "Reset emergency stop"),
        LocalizedMessage.text(
            "app.status.ready",
            "Guardian ● Sandbox ● Secrets ● Project DNA",
        ),
        LocalizedMessage.text(
            "app.status.blocked",
            "KILL SWITCH ACTIVE — protected execution is blocked",
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class KodeStudioTranslator:
    locale: str = SOURCE_LOCALE
    catalog: LocaleCatalog | None = None

    def __post_init__(self) -> None:
        catalog = self.catalog
        if catalog is None:
            catalog = (
                KODESTUDIO_SOURCE_CATALOG
                if self.locale == SOURCE_LOCALE
                else pseudo_catalog(KODESTUDIO_SOURCE_CATALOG, locale=PSEUDO_LOCALE)
                if self.locale == PSEUDO_LOCALE
                else LocaleCatalog(
                    locale=self.locale,
                    messages=(),
                    fallback_locale=SOURCE_LOCALE,
                )
            )
        object.__setattr__(self, "catalog", catalog)

    def text(self, message_id: str, **values: Any) -> str:
        return KodeLocalization(KODESTUDIO_SOURCE_CATALOG).translate(
            self.catalog or KODESTUDIO_SOURCE_CATALOG,
            message_id,
            values=values,
        )


def registered_messages() -> Mapping[str, str]:
    return {
        message.id: message.forms["other"]
        for message in KODESTUDIO_SOURCE_CATALOG.messages
    }
