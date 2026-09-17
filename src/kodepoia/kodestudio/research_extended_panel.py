from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kodepoia.core.secrets import KodeSecrets
from kodepoia.intelligence.research.contracts import ResearchSourceKind
from kodepoia.intelligence.research.extended_sources import ExtendedSourceCoordinator
from kodepoia.intelligence.research.service import (
    ResearchCancellation,
    ResearchOperationStatus,
    ResearchServiceResult,
)
from kodepoia.kodestudio import research_panel as _panel

_BASE_KINDS = {
    ResearchSourceKind.LOCAL,
    ResearchSourceKind.OFFICIAL_DOCS,
    ResearchSourceKind.WEB,
}
_EXTENDED_KINDS = {
    ResearchSourceKind.COMMUNITY,
    ResearchSourceKind.YOUTUBE,
}
_ORIGINAL_CREATE_RESEARCH_PAGE = _panel.create_research_page
_INSTALLED = False


@dataclass(frozen=True, slots=True)
class ExtendedResearchFetchRequest:
    """UI-compatible fetch request that adds V2.1.5 source kinds without widening R7.10."""

    kind: ResearchSourceKind
    locator: str
    retrieved_at: str = ""
    canonical_locator: str = ""
    title: str = ""
    publisher: str = ""
    product: str = ""
    version: str = ""
    target_version: str = ""

    def __post_init__(self) -> None:
        if not self.locator.strip():
            raise ValueError("Research fetch locator must not be empty")
        if self.kind not in _BASE_KINDS | _EXTENDED_KINDS:
            raise ValueError("Interactive Research fetch source kind is not supported")

    @property
    def effective_retrieved_at(self) -> str:
        if self.retrieved_at:
            return self.retrieved_at
        from datetime import UTC, datetime

        return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _ensure_runtime_secrets(research) -> KodeSecrets:
    if research.secrets is None:
        research.secrets = KodeSecrets()
    return research.secrets


def _cancelled_result() -> ResearchServiceResult:
    return ResearchServiceResult(
        "fetch",
        ResearchOperationStatus.CANCELLED,
        reason="cancelled",
        metadata={"v2_1_5": True},
    )


def _extend_page(page, project_root: Path) -> None:
    from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QTableWidget

    research = page._research_service
    discovery = page._research_discovery_service
    secrets = _ensure_runtime_secrets(research)
    discovery.secrets = secrets
    coordinator = ExtendedSourceCoordinator(
        project_root,
        allow_network=research.allow_network,
        secrets=secrets,
        web_transport=research.web_transport,
        web_policy=research.web_policy,
    )
    page._research_extended_sources = coordinator

    fetch_kind = page.findChild(QComboBox, "researchFetchKind")
    locator = page.findChild(QLineEdit, "researchLocator")
    network = page.findChild(QCheckBox, "researchAllowNetwork")
    results = page.findChild(QTableWidget, "researchResultsTable")
    if fetch_kind is None or locator is None or network is None or results is None:
        raise RuntimeError("Research panel V2.1.5 extension requires the accepted Research UI contract")

    for kind in (ResearchSourceKind.COMMUNITY, ResearchSourceKind.YOUTUBE):
        if fetch_kind.findData(kind.value) < 0:
            fetch_kind.addItem(kind.value, kind.value)

    state = QLabel(
        "V2.1.5 sources: Community HTML is fetched through the guarded Web transport; "
        "YouTube metadata uses KodeSecrets youtube/data_api_key and captions use "
        "youtube/oauth_access_token. Unavailable transcripts remain explicit."
    )
    state.setObjectName("researchExtendedSourceState")
    state.setAccessibleName("Extended research provider state")
    state.setWordWrap(True)
    layout = page.layout()
    if layout is not None:
        layout.insertWidget(4, state)
    page._research_extended_source_state = state

    original_discover = discovery.discover

    def discover_with_extended_candidates(*args: Any, **kwargs: Any) -> ResearchServiceResult:
        coordinator.allow_network = bool(network.isChecked())
        result = original_discover(*args, **kwargs)
        return ExtendedSourceCoordinator.classify_discovery_result(result)

    discovery.discover = discover_with_extended_candidates

    original_fetch = research.fetch

    def fetch_with_extended_sources(
        request: ExtendedResearchFetchRequest,
        *,
        cancellation: ResearchCancellation | None = None,
    ) -> ResearchServiceResult:
        token = cancellation or ResearchCancellation()
        if token.cancelled:
            return _cancelled_result()
        if request.kind in _BASE_KINDS:
            return original_fetch(request, cancellation=token)

        coordinator.allow_network = bool(network.isChecked())
        if request.kind is ResearchSourceKind.COMMUNITY:
            extended = coordinator.fetch_community_url(
                request.locator,
                retrieved_at=request.effective_retrieved_at,
            )
        elif request.kind is ResearchSourceKind.YOUTUBE:
            extended = coordinator.fetch_youtube(
                request.locator,
                retrieved_at=request.effective_retrieved_at,
                include_transcript=True,
            )
        else:  # pragma: no cover - guarded by request validation
            raise ValueError("Unsupported extended Research source kind")
        if token.cancelled:
            return _cancelled_result()
        return extended.to_service_result()

    research.fetch = fetch_with_extended_sources

    def sync_selected_candidate_to_fetch() -> None:
        current = page._research_result
        row = results.currentRow()
        if current is None or current.operation != "discover" or not 0 <= row < len(current.items):
            return
        item = current.items[row]
        if item.source_kind not in {kind.value for kind in _EXTENDED_KINDS}:
            return
        index = fetch_kind.findData(item.source_kind)
        if index >= 0:
            fetch_kind.setCurrentIndex(index)
            locator.setText(item.locator)
            state.setText(
                f"Selected {item.source_kind} candidate is descriptor-only. "
                "Use Open/fetch source for guarded acquisition before evidence selection."
            )

    results.itemSelectionChanged.connect(sync_selected_candidate_to_fetch)

    def network_changed(checked: bool) -> None:
        coordinator.allow_network = bool(checked)

    network.toggled.connect(network_changed)


def create_research_page(
    project_root: Path,
    *,
    translator,
    service=None,
    status_bar=None,
):
    page = _ORIGINAL_CREATE_RESEARCH_PAGE(
        project_root,
        translator=translator,
        service=service,
        status_bar=status_bar,
    )
    _extend_page(page, Path(project_root).resolve(strict=False))
    return page


def install_extended_research_ui() -> None:
    """Install the V2.1.5 adapter before app.py imports create_research_page."""

    global _INSTALLED
    if _INSTALLED:
        return
    _panel.ResearchFetchRequest = ExtendedResearchFetchRequest
    _panel.create_research_page = create_research_page
    _INSTALLED = True
