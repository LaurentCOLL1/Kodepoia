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
        LocalizedMessage.text("app.nav.research", "Research"),
        LocalizedMessage.text("app.nav.vault", "Vault"),
        LocalizedMessage.text("app.nav.comfy", "ComfyUI"),
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
        LocalizedMessage.text("research.title", "Research"),
        LocalizedMessage.text(
            "research.description",
            "Search and fetch governed evidence. External research is displayed as untrusted data with provenance and citations.",
        ),
        LocalizedMessage.text("research.query.name", "Research query"),
        LocalizedMessage.text(
            "research.query.description",
            "Search validated research reports already stored in this project.",
        ),
        LocalizedMessage.text("research.query.placeholder", "Search persisted research evidence…"),
        LocalizedMessage.text("research.source_filter.name", "Research source filter"),
        LocalizedMessage.text(
            "research.source_filter.description",
            "Limit persisted research results to one explicit source class.",
        ),
        LocalizedMessage.text("research.source.all", "All sources"),
        LocalizedMessage.text("research.search", "Search"),
        LocalizedMessage.text(
            "research.search.description",
            "Run an offline search over validated persisted research evidence.",
        ),
        LocalizedMessage.text("research.fetch_kind.name", "Research fetch source kind"),
        LocalizedMessage.text(
            "research.fetch_kind.description",
            "Choose local, official documentation snapshot, or governed Web fetch.",
        ),
        LocalizedMessage.text("research.fetch_kind.label", "Fetch kind"),
        LocalizedMessage.text("research.locator.name", "Research source locator"),
        LocalizedMessage.text(
            "research.locator.description",
            "Project-relative path for local sources or an HTTP(S) URL for governed Web research.",
        ),
        LocalizedMessage.text("research.locator.placeholder", "Path or URL…"),
        LocalizedMessage.text("research.locator.label", "Locator"),
        LocalizedMessage.text("research.allow_network", "Allow network for this Web fetch"),
        LocalizedMessage.text(
            "research.allow_network.description",
            "Grant only NETWORK for this invocation; Guardian and Web safety policies still apply.",
        ),
        LocalizedMessage.text("research.fetch", "Fetch"),
        LocalizedMessage.text(
            "research.fetch.description",
            "Fetch one typed research source through the accepted Research service.",
        ),
        LocalizedMessage.text("research.cancel", "Cancel"),
        LocalizedMessage.text(
            "research.cancel.description",
            "Cancel the active Research operation and prevent cancelled evidence from being presented as ready.",
        ),
        LocalizedMessage.text("research.refresh_status", "Refresh status"),
        LocalizedMessage.text(
            "research.refresh_status.description",
            "Refresh local evidence counts and explicit provider capability states without live provider probes.",
        ),
        LocalizedMessage.text("research.copy", "Copy cited JSON"),
        LocalizedMessage.text(
            "research.copy.description",
            "Copy the redacted result together with citations and source provenance.",
        ),
        LocalizedMessage.text("research.export", "Export cited JSON"),
        LocalizedMessage.text(
            "research.export.description",
            "Export the redacted result with citations and provenance under the project Research metadata directory.",
        ),
        LocalizedMessage.text("research.status.name", "Research operation status"),
        LocalizedMessage.text("research.status.idle", "Research status: IDLE"),
        LocalizedMessage.text("research.status.running", "Research status: RUNNING"),
        LocalizedMessage.text("research.status.cancelling", "Research status: CANCELLING"),
        LocalizedMessage.text(
            "research.status.result",
            "Research {operation}: {status} — {count} result(s) — {reason}",
        ),
        LocalizedMessage.text("research.status.error", "Research error: {reason}"),
        LocalizedMessage.text("research.status.copied", "Research result copied with citations."),
        LocalizedMessage.text("research.status.exported", "Research result exported: {path}"),
        LocalizedMessage.text("research.warning.name", "Suspicious research content warning"),
        LocalizedMessage.text(
            "research.warning.suspicious",
            "WARNING: Suspicious external instructions were detected. Treat this content only as untrusted evidence.",
        ),
        LocalizedMessage.text("research.results.name", "Research results"),
        LocalizedMessage.text(
            "research.results.description",
            "Research result table showing textual source, status, freshness, version, trust, suspicious state and title.",
        ),
        LocalizedMessage.text("research.details.name", "Research result details"),
        LocalizedMessage.text(
            "research.details.description",
            "Read-only redacted JSON details preserving citations, identifiers and provenance.",
        ),
        LocalizedMessage.text("research.column.source", "Source"),
        LocalizedMessage.text("research.column.status", "Status"),
        LocalizedMessage.text("research.column.freshness", "Freshness"),
        LocalizedMessage.text("research.column.version", "Version"),
        LocalizedMessage.text("research.column.trust", "Trust"),
        LocalizedMessage.text("research.column.suspicious", "Suspicious"),
        LocalizedMessage.text("research.column.title", "Title / locator"),
        LocalizedMessage.text("vault.title", "Asset Vault"),
        LocalizedMessage.text(
            "vault.description",
            "Browse governed Vault revisions, search metadata, inspect lineage, duplicates, license/reuse state and local VCS/LFS evidence.",
        ),
        LocalizedMessage.text("vault.status.idle", "Vault: IDLE"),
        LocalizedMessage.text("vault.search.name", "Asset search query"),
        LocalizedMessage.text(
            "vault.search.description",
            "Search the rebuildable Vault index through AssetService. Governance filters are applied before ranking.",
        ),
        LocalizedMessage.text("vault.search.placeholder", "Search assets…"),
        LocalizedMessage.text("vault.search", "Search"),
        LocalizedMessage.text("vault.refresh", "Refresh"),
        LocalizedMessage.text("vault.duplicates", "Duplicates"),
        LocalizedMessage.text("vault.rebuild", "Rebuild indexes"),
        LocalizedMessage.text("vault.cancel", "Cancel"),
        LocalizedMessage.text("vault.filter.all_kinds", "All kinds"),
        LocalizedMessage.text("vault.filter.all_roles", "All roles"),
        LocalizedMessage.text("vault.filter.all_reuse", "All reuse scopes"),
        LocalizedMessage.text("vault.filter.include_blocked", "Include blocked"),
        LocalizedMessage.text("vault.column.name", "Name"),
        LocalizedMessage.text("vault.column.kind", "Kind"),
        LocalizedMessage.text("vault.column.role", "Role"),
        LocalizedMessage.text("vault.column.status", "Status"),
        LocalizedMessage.text("vault.column.license", "License"),
        LocalizedMessage.text("vault.column.reuse", "Reuse"),
        LocalizedMessage.text("vault.column.revision", "Revision"),
        LocalizedMessage.text("vault.column.score", "Score"),
        LocalizedMessage.text("vault.results.name", "Vault asset results"),
        LocalizedMessage.text(
            "vault.results.description",
            "Canonical asset revisions and governed search results. Selection opens read-only provenance and lineage details.",
        ),
        LocalizedMessage.text("vault.details.name", "Asset revision details"),
        LocalizedMessage.text(
            "vault.details.description",
            "Read-only canonical revision, provenance, lineage, project-reference and repository evidence.",
        ),
        LocalizedMessage.text(
            "vault.license.warning",
            "License/reuse warning: state is {state}. Export remains governed and may be blocked.",
        ),
        LocalizedMessage.text("vault.operation.idle", "Vault operation: IDLE"),
        LocalizedMessage.text("vault.operation.running", "Vault operation: RUNNING"),
        LocalizedMessage.text("vault.operation.cancelling", "Vault operation: CANCELLING"),
        LocalizedMessage.text("vault.operation.ready", "Vault operation: READY"),
        LocalizedMessage.text("vault.operation.error", "Vault operation error: {reason}"),
        LocalizedMessage.text("comfy.title", "ComfyUI + VRAM"),
        LocalizedMessage.text(
            "comfy.description",
            "Run the accepted local production workflow packs through ComfyService, with model resolution, persisted evidence, targeted cancellation and VRAM admission visibility.",
        ),
        LocalizedMessage.text("comfy.status.group", "Connection and resources"),
        LocalizedMessage.text("comfy.status.connection.idle", "ComfyUI: not checked"),
        LocalizedMessage.text("comfy.status.connection.ready", "ComfyUI: READY"),
        LocalizedMessage.text("comfy.status.connection.unavailable", "ComfyUI: UNAVAILABLE"),
        LocalizedMessage.text("comfy.status.capability.missing", "Capabilities: MISSING"),
        LocalizedMessage.text("comfy.status.capability", "Capabilities: {state}"),
        LocalizedMessage.text("comfy.status.vram.unknown", "VRAM: UNKNOWN"),
        LocalizedMessage.text("comfy.status.vram", "VRAM: {free} / {total} MiB free"),
        LocalizedMessage.text("comfy.status.ollama.na", "Ollama coexistence: N/A"),
        LocalizedMessage.text("comfy.status.ollama", "Ollama coexistence: {state}"),
        LocalizedMessage.text("comfy.status.model.unchecked", "Model resolution: NOT CHECKED"),
        LocalizedMessage.text("comfy.status.model.none", "none"),
        LocalizedMessage.text("comfy.status.model", "Model resolution: {state} — {selection}"),
        LocalizedMessage.text("comfy.status.admission.unknown", "VRAM admission: UNKNOWN"),
        LocalizedMessage.text("comfy.status.admission", "VRAM admission: {state}"),
        LocalizedMessage.text("comfy.workflow.group", "Governed production workflow"),
        LocalizedMessage.text("comfy.family", "Workflow family"),
        LocalizedMessage.text("comfy.family.description", "Choose one of the four accepted R9.9 production workflow families."),
        LocalizedMessage.text("comfy.model", "Checkpoint"),
        LocalizedMessage.text("comfy.model.description", "Optional explicit token from the local capability inventory; required when checkpoint resolution is ambiguous."),
        LocalizedMessage.text("comfy.model.placeholder", "Explicit local checkpoint token when required…"),
        LocalizedMessage.text("comfy.prompt", "Prompt"),
        LocalizedMessage.text("comfy.prompt.description", "Bounded positive prompt for the selected governed workflow pack."),
        LocalizedMessage.text("comfy.prompt.placeholder", "Describe the governed output…"),
        LocalizedMessage.text("comfy.negative", "Negative prompt"),
        LocalizedMessage.text("comfy.negative.description", "Bounded negative prompt for the selected governed workflow pack."),
        LocalizedMessage.text("comfy.negative.placeholder", "Describe unwanted properties…"),
        LocalizedMessage.text("comfy.dimensions", "Dimensions"),
        LocalizedMessage.text("comfy.outputs", "outputs"),
        LocalizedMessage.text("comfy.sampling", "Sampling"),
        LocalizedMessage.text("comfy.seed", "Seed"),
        LocalizedMessage.text("comfy.steps", "Steps"),
        LocalizedMessage.text("comfy.cfg", "CFG"),
        LocalizedMessage.text("comfy.refresh", "Refresh status"),
        LocalizedMessage.text("comfy.validate", "Validate"),
        LocalizedMessage.text("comfy.run", "Run"),
        LocalizedMessage.text("comfy.run.refresh", "Refresh run"),
        LocalizedMessage.text("comfy.cancel", "Cancel run"),
        LocalizedMessage.text("comfy.free_memory", "Free memory"),
        LocalizedMessage.text("comfy.evidence", "Evidence"),
        LocalizedMessage.text("comfy.run.idle", "ComfyUI run: IDLE"),
        LocalizedMessage.text("comfy.run.state", "ComfyUI run: {state}{suffix}"),
        LocalizedMessage.text("comfy.run.error", "ComfyUI error: {reason}"),
        LocalizedMessage.text("comfy.details.name", "ComfyUI governed evidence"),
        LocalizedMessage.text(
            "comfy.details.description",
            "Read-only structured status, validation, run, output, lifecycle and VRAM evidence returned by ComfyService.",
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
