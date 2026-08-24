from __future__ import annotations

from typing import Any, Mapping

from kodepoia.quality.localization import KodeLocalization, LocaleCatalog, LocalizedMessage, pseudo_catalog

SOURCE_LOCALE = "en"
PSEUDO_LOCALE = "qps-ploc"

BLENDER_SOURCE_CATALOG = LocaleCatalog(
    locale=SOURCE_LOCALE,
    messages=(
        LocalizedMessage.text("blender.nav", "Blender / 3D"),
        LocalizedMessage.text("blender.title", "Blender / 3D"),
        LocalizedMessage.text(
            "blender.description",
            "Inspect accepted Blender/3D capabilities, managed recipes, QA summaries and evidence "
            "through BlenderService. Raw Python, process and path surfaces are not exposed.",
        ),
        LocalizedMessage.text("blender.status.group", "Runtime and capabilities"),
        LocalizedMessage.text("blender.status.runtime.unknown", "Runtime evidence: UNKNOWN"),
        LocalizedMessage.text(
            "blender.status.runtime",
            "Runtime: Blender {blender} — Godot {godot}",
        ),
        LocalizedMessage.text(
            "blender.status.capabilities.unknown",
            "Accepted capabilities: UNKNOWN",
        ),
        LocalizedMessage.text(
            "blender.status.capabilities",
            "Accepted capabilities: {accepted} / {total}",
        ),
        LocalizedMessage.text("blender.query.group", "Managed R10 record"),
        LocalizedMessage.text("blender.kind", "Record kind"),
        LocalizedMessage.text(
            "blender.kind.description",
            "Choose one bounded R10 report kind. No Python operator or process command is accepted.",
        ),
        LocalizedMessage.text("blender.kind.inspect", "Inspection"),
        LocalizedMessage.text("blender.kind.qa", "Mesh / material QA"),
        LocalizedMessage.text("blender.kind.rig", "Rig / skin report"),
        LocalizedMessage.text("blender.kind.animation", "Animation / retarget report"),
        LocalizedMessage.text("blender.kind.lod", "LOD report"),
        LocalizedMessage.text("blender.kind.export", "GLB / glTF export report"),
        LocalizedMessage.text("blender.record", "Managed record ID"),
        LocalizedMessage.text(
            "blender.record.description",
            "Stable Kodepoia ID resolved only inside the managed Blender metadata roots.",
        ),
        LocalizedMessage.text("blender.record.placeholder", "managed-record-id"),
        LocalizedMessage.text("blender.evidence", "Accepted evidence"),
        LocalizedMessage.text(
            "blender.evidence.description",
            "Choose one allowlisted accepted R10 local evidence record.",
        ),
        LocalizedMessage.text("blender.refresh", "Refresh status"),
        LocalizedMessage.text("blender.capabilities", "Capabilities"),
        LocalizedMessage.text("blender.load_report", "Load report"),
        LocalizedMessage.text("blender.validate_geometry", "Validate geometry recipe"),
        LocalizedMessage.text("blender.show_evidence", "Show evidence"),
        LocalizedMessage.text("blender.cancel", "Cancel"),
        LocalizedMessage.text("blender.operation.idle", "Blender / 3D operation: IDLE"),
        LocalizedMessage.text("blender.operation.running", "Blender / 3D operation: RUNNING"),
        LocalizedMessage.text(
            "blender.operation.cancelling",
            "Blender / 3D operation: CANCELLING",
        ),
        LocalizedMessage.text(
            "blender.operation.state",
            "Blender / 3D {operation}: {state}",
        ),
        LocalizedMessage.text(
            "blender.operation.error",
            "Blender / 3D error: {reason}",
        ),
        LocalizedMessage.text("blender.details.name", "Blender / 3D structured result"),
        LocalizedMessage.text(
            "blender.details.description",
            "Read-only structured BlenderService state, capability, QA or accepted evidence details.",
        ),
    ),
)


class BlenderTranslator:
    def __init__(self, locale: str = SOURCE_LOCALE) -> None:
        self.locale = locale
        if locale == SOURCE_LOCALE:
            self.catalog = BLENDER_SOURCE_CATALOG
        elif locale == PSEUDO_LOCALE:
            self.catalog = pseudo_catalog(BLENDER_SOURCE_CATALOG, locale=PSEUDO_LOCALE)
        else:
            self.catalog = LocaleCatalog(
                locale=locale,
                messages=(),
                fallback_locale=SOURCE_LOCALE,
            )

    def text(self, message_id: str, **values: Any) -> str:
        return KodeLocalization(BLENDER_SOURCE_CATALOG).translate(
            self.catalog,
            message_id,
            values=values,
        )


def blender_nav_text(locale: str = SOURCE_LOCALE) -> str:
    return BlenderTranslator(locale).text("blender.nav")


def registered_blender_messages() -> Mapping[str, str]:
    return {
        message.id: message.forms["other"]
        for message in BLENDER_SOURCE_CATALOG.messages
    }


__all__ = [
    "BLENDER_SOURCE_CATALOG",
    "BlenderTranslator",
    "PSEUDO_LOCALE",
    "SOURCE_LOCALE",
    "blender_nav_text",
    "registered_blender_messages",
]
