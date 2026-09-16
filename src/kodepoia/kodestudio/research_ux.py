from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
            "Discover new candidate sources through qualified providers. V2.1.1 exposes capability state only; real discovery begins in V2.1.2.",
        ),
        LocalizedMessage.text(
            "research_ux.discovery.not_implemented",
            "Search sources: NOT IMPLEMENTED — no qualified discovery provider is available yet. Use Search saved research or Open/fetch source with a known locator.",
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
            "research_ux.empty.discovery_unavailable",
            "Source discovery is not implemented yet. V2.1.2 is the first subdivision allowed to add qualified discovery providers.",
        ),
        LocalizedMessage.text(
            "research_ux.empty.network_restricted",
            "Known Web-source fetch is network-restricted. Enable network only for the explicit fetch when appropriate.",
        ),
        LocalizedMessage.text(
            "research_ux.empty.auth_required",
            "Authenticated/private GitHub access requires a configured least-privilege read-only credential.",
        ),
        LocalizedMessage.text(
            "research_ux.provider.summary",
            "Provider status — discovery: {discovery} • explicit Web fetch: {web} • private GitHub: {github} • vision: {vision}",
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
        LocalizedMessage.text(
            "research_ux.error.empty_query",
            "Enter a question before searching saved research.",
        ),
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


def _research_rows(
    *,
    allow_network: bool = False,
    github_authenticated: bool = False,
) -> dict[str, dict[str, Any]]:
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
    rows = _research_rows(allow_network=allow_network, github_authenticated=github_authenticated)
    state = rows["research.web-discovery"]["runtime_state"]
    if state == "not-implemented":
        return translator.text("research_ux.discovery.not_implemented")
    return f"{translator.text('research_ux.discovery.button')}: {state.upper()}"


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
    if rows["research.web-discovery"]["runtime_state"] != "ready":
        parts.append(translator.text("research_ux.empty.discovery_unavailable"))
    if rows["research.explicit-web-fetch"]["runtime_state"] == "network-restricted":
        parts.append(translator.text("research_ux.empty.network_restricted"))
    if rows["research.github-authenticated-resource"]["runtime_state"] == "auth-required":
        parts.append(translator.text("research_ux.empty.auth_required"))
    return "\n".join(parts)


def saved_search_status_text(
    translator: ResearchUxTranslator,
    *,
    status: str,
    count: int,
) -> str:
    message = (
        translator.text("research_ux.empty.no_saved_matches")
        if count == 0
        else translator.text("research_ux.saved.matches")
    )
    return translator.text(
        "research_ux.saved.result",
        status=status.upper(),
        count=count,
        message=message,
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
    if "query must not be empty" in lowered:
        return translator.text("research_ux.error.empty_query")
    if "locator must not be empty" in lowered:
        return translator.text("research_ux.error.empty_locator")
    return translator.text("research_ux.error.generic", reason=message)
