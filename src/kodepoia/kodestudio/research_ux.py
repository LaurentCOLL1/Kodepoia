from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from kodepoia.capability_truth import build_capability_matrix
from kodepoia.quality.localization import KodeLocalization, LocaleCatalog, LocalizedMessage, pseudo_catalog

SOURCE_LOCALE = "en"
PSEUDO_LOCALE = "qps-ploc"

RESEARCH_UX_SOURCE_CATALOG = LocaleCatalog(
    locale=SOURCE_LOCALE,
    messages=(
        LocalizedMessage.text("research_ux.saved.button", "Search saved research"),
        LocalizedMessage.text("research_ux.saved.name", "Saved research search"),
        LocalizedMessage.text(
            "research_ux.saved.description",
            "Search validated research reports already stored in this project. This does not search the Internet.",
        ),
        LocalizedMessage.text("research_ux.saved.placeholder", "Search saved research in this project…"),
        LocalizedMessage.text("research_ux.discovery.button", "Search sources"),
        LocalizedMessage.text("research_ux.discovery.name", "Source discovery"),
        LocalizedMessage.text(
            "research_ux.discovery.description",
            "Discover new Web and GitHub candidate sources. Candidates are not fetched, persisted, trusted, or evidence until you explicitly open/fetch a locator.",
        ),
        LocalizedMessage.text(
            "research_ux.discovery.network_restricted",
            "Search sources: NETWORK-RESTRICTED — enable network to query the qualified discovery providers.",
        ),
        LocalizedMessage.text(
            "research_ux.discovery.available",
            "Search sources is available. GitHub public discovery can run without credentials; Brave Web discovery also requires brave/search_api_key.",
        ),
        LocalizedMessage.text(
            "research_ux.discovery.result",
            "Source discovery: {status} — {count} candidate(s). Nothing here has been fetched, persisted, trusted, or promoted to evidence. {provider_summary}",
        ),
        LocalizedMessage.text(
            "research_ux.discovery.provider",
            "{provider}: {status}{reason}",
        ),
        LocalizedMessage.text("research_ux.fetch.button", "Open/fetch source"),
        LocalizedMessage.text("research_ux.fetch.name", "Known-source acquisition"),
        LocalizedMessage.text(
            "research_ux.fetch.description",
            "Open or fetch one known local path or explicit HTTP(S) locator through the existing guarded acquisition path.",
        ),
        LocalizedMessage.text(
            "research_ux.empty.no_reports",
            "No saved research exists in this project yet. Search saved research only checks previously stored reports.",
        ),
        LocalizedMessage.text(
            "research_ux.empty.saved_available",
            "This project contains {count} saved research report(s). Search saved research queries only those persisted reports.",
        ),
        LocalizedMessage.text(
            "research_ux.empty.no_saved_matches",
            "No matching saved research stored in this project was found. This was a local saved-report search, not source discovery.",
        ),
        LocalizedMessage.text(
            "research_ux.empty.discovery_restricted",
            "Source discovery exists in live source but is network-restricted until you explicitly enable network.",
        ),
        LocalizedMessage.text(
            "research_ux.empty.network_restricted",
            "Known Web-source fetch is network-restricted. Enable network only for the explicit operation when appropriate.",
        ),
        LocalizedMessage.text(
            "research_ux.empty.auth_required",
            "Authenticated/private GitHub access requires a configured least-privilege read-only credential.",
        ),
        LocalizedMessage.text(
            "research_ux.provider.summary",
            "Provider status — Web discovery: {discovery} • GitHub discovery: {github_discovery} • explicit Web fetch: {web} • private GitHub: {github} • vision: {vision}",
        ),
        LocalizedMessage.text(
            "research_ux.saved.result",
            "Saved research search: {status} — {count} result(s). {message}",
        ),
        LocalizedMessage.text(
            "research_ux.saved.matches",
            "Results come only from validated research reports stored in this project; they are not newly discovered Internet sources.",
        ),
        LocalizedMessage.text(
            "research_ux.fetch.result",
            "Open/fetch source: {status} — {count} item(s). {reason}",
        ),
        LocalizedMessage.text(
            "research_ux.fetch.blocked_action",
            "The guarded source fetch did not succeed. Check the explicit locator and the required network permission; this state is not an empty successful search.",
        ),
        LocalizedMessage.text(
            "research_ux.fetch.unavailable_action",
            "The source provider or transport is unavailable. Check provider/network diagnostics and retry the same explicit locator when the dependency is available.",
        ),
        LocalizedMessage.text("research_ux.error.empty_query", "Enter a question before searching."),
        LocalizedMessage.text(
            "research_ux.error.empty_locator",
            "Enter a local path or explicit HTTP(S) URL before opening/fetching a source.",
        ),
        LocalizedMessage.text("research_ux.error.generic", "Research operation failed: {reason}"),
        LocalizedMessage.text("research_ux.diagnostics.title", "Provider and capability diagnostics"),
        LocalizedMessage.text("research_ux.technical.title", "Technical details (JSON)"),
    ),
)


@dataclass(frozen=True, slots=True)
class ResearchUxTranslator:
    locale: str = SOURCE_LOCALE
    catalog: LocaleCatalog | None = None

    def __post_init__(self) -> None:
        catalog = self.catalog
        if catalog is None:
            catalog = (
                RESEARCH_UX_SOURCE_CATALOG
                if self.locale == SOURCE_LOCALE
                else pseudo_catalog(RESEARCH_UX_SOURCE_CATALOG, locale=PSEUDO_LOCALE)
                if self.locale == PSEUDO_LOCALE
                else LocaleCatalog(locale=self.locale, messages=(), fallback_locale=SOURCE_LOCALE)
            )
        object.__setattr__(self, "catalog", catalog)

    def text(self, message_id: str, **values: Any) -> str:
        return KodeLocalization(RESEARCH_UX_SOURCE_CATALOG).translate(
            self.catalog or RESEARCH_UX_SOURCE_CATALOG,
            message_id,
            values=values,
        )


def _research_rows(*, allow_network: bool = False, github_authenticated: bool = False) -> dict[str, dict[str, Any]]:
    return {
        row["capability_id"]: row
        for row in build_capability_matrix(
            allow_network=allow_network,
            github_authenticated=github_authenticated,
        )
        if row["capability_id"].startswith("research.")
    }


def provider_summary_text(
    translator: ResearchUxTranslator,
    *,
    allow_network: bool = False,
    github_authenticated: bool = False,
) -> str:
    rows = _research_rows(allow_network=allow_network, github_authenticated=github_authenticated)
    return translator.text(
        "research_ux.provider.summary",
        discovery=rows["research.web-discovery"]["runtime_state"].upper(),
        github_discovery=rows["research.github-discovery"]["runtime_state"].upper(),
        web=rows["research.explicit-web-fetch"]["runtime_state"].upper(),
        github=rows["research.github-authenticated-resource"]["runtime_state"].upper(),
        vision=rows["research.vision-provider"]["runtime_state"].upper(),
    )


def discovery_state_text(
    translator: ResearchUxTranslator,
    *,
    allow_network: bool = False,
    github_authenticated: bool = False,
) -> str:
    if allow_network:
        return translator.text("research_ux.discovery.available")
    return translator.text("research_ux.discovery.network_restricted")


def default_empty_state_text(
    translator: ResearchUxTranslator,
    *,
    report_count: int,
    allow_network: bool = False,
    github_authenticated: bool = False,
) -> str:
    rows = _research_rows(allow_network=allow_network, github_authenticated=github_authenticated)
    parts = [
        translator.text("research_ux.empty.no_reports")
        if report_count <= 0
        else translator.text("research_ux.empty.saved_available", count=report_count)
    ]
    if not allow_network:
        parts.append(translator.text("research_ux.empty.discovery_restricted"))
    if rows["research.explicit-web-fetch"]["runtime_state"] == "network-restricted":
        parts.append(translator.text("research_ux.empty.network_restricted"))
    if rows["research.github-authenticated-resource"]["runtime_state"] == "auth-required":
        parts.append(translator.text("research_ux.empty.auth_required"))
    return "\n".join(parts)


def saved_search_status_text(translator: ResearchUxTranslator, *, status: str, count: int) -> str:
    message = (
        translator.text("research_ux.empty.no_saved_matches")
        if count == 0
        else translator.text("research_ux.saved.matches")
    )
    return translator.text("research_ux.saved.result", status=status.upper(), count=count, message=message)


def discovery_status_text(
    translator: ResearchUxTranslator,
    *,
    status: str,
    count: int,
    providers: object,
) -> str:
    summaries: list[str] = []
    if isinstance(providers, list):
        for raw in providers:
            if not isinstance(raw, Mapping):
                continue
            provider = str(raw.get("provider_id", "provider"))
            provider_status = str(raw.get("status", "unknown")).upper()
            reason_value = str(raw.get("reason", "")).strip()
            reason = f" ({reason_value})" if reason_value else ""
            summaries.append(
                translator.text(
                    "research_ux.discovery.provider",
                    provider=provider,
                    status=provider_status,
                    reason=reason,
                )
            )
    provider_summary = " • ".join(summaries) if summaries else "provider state unavailable"
    return translator.text(
        "research_ux.discovery.result",
        status=status.upper(),
        count=count,
        provider_summary=provider_summary,
    )


def fetch_status_text(
    translator: ResearchUxTranslator,
    *,
    status: str,
    count: int,
    reason: str,
) -> str:
    normalized = status.casefold()
    action = ""
    if normalized == "blocked":
        action = translator.text("research_ux.fetch.blocked_action")
    elif normalized == "unavailable":
        action = translator.text("research_ux.fetch.unavailable_action")
    visible_reason = reason.strip() or "—"
    if action:
        visible_reason = f"{visible_reason} {action}"
    return translator.text(
        "research_ux.fetch.result",
        status=status.upper(),
        count=count,
        reason=visible_reason,
    )


def error_text(translator: ResearchUxTranslator, message: str) -> str:
    lowered = message.casefold()
    if "query must not be empty" in lowered or "discovery query must not be empty" in lowered:
        return translator.text("research_ux.error.empty_query")
    if "locator must not be empty" in lowered:
        return translator.text("research_ux.error.empty_locator")
    return translator.text("research_ux.error.generic", reason=message)
