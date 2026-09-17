from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kodepoia.core.secrets import KodeSecrets
from kodepoia.intelligence.research.contracts import ResearchSourceKind
from kodepoia.intelligence.research.discovery import ResearchDiscoveryService
from kodepoia.intelligence.research.extended_sources import ExtendedSourceCoordinator
from kodepoia.intelligence.research.service import (
    ResearchCancellation,
    ResearchOperationStatus,
    ResearchService,
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


def _ensure_runtime_secrets(research: Any) -> KodeSecrets:
    secrets = getattr(research, "secrets", None)
    if secrets is None:
        secrets = KodeSecrets()
        research.secrets = secrets
    return secrets


def _cancelled_result() -> ResearchServiceResult:
    return ResearchServiceResult(
        "fetch",
        ResearchOperationStatus.CANCELLED,
        reason="cancelled",
        metadata={"v2_1_5": True},
    )


class ExtendedResearchServiceAdapter:
    """Delegate historical Research operations and route only V2.1.5 fetch kinds."""

    def __init__(self, delegate: Any, coordinator: ExtendedSourceCoordinator) -> None:
        self._delegate = delegate
        self.coordinator = coordinator

    @property
    def allow_network(self) -> bool:
        return bool(self._delegate.allow_network)

    @allow_network.setter
    def allow_network(self, value: bool) -> None:
        enabled = bool(value)
        self._delegate.allow_network = enabled
        self.coordinator.allow_network = enabled

    @property
    def secrets(self):
        return self._delegate.secrets

    @secrets.setter
    def secrets(self, value) -> None:
        self._delegate.secrets = value
        self.coordinator.secrets = value

    @property
    def web_transport(self):
        return self._delegate.web_transport

    @property
    def web_policy(self):
        return self._delegate.web_policy

    def fetch(
        self,
        request: ExtendedResearchFetchRequest,
        *,
        cancellation: ResearchCancellation | None = None,
    ) -> ResearchServiceResult:
        token = cancellation or ResearchCancellation()
        if token.cancelled:
            return _cancelled_result()
        if request.kind in _BASE_KINDS:
            return self._delegate.fetch(request, cancellation=token)

        self.coordinator.allow_network = self.allow_network
        if request.kind is ResearchSourceKind.COMMUNITY:
            extended = self.coordinator.fetch_community_url(
                request.locator,
                retrieved_at=request.effective_retrieved_at,
            )
        elif request.kind is ResearchSourceKind.YOUTUBE:
            extended = self.coordinator.fetch_youtube(
                request.locator,
                retrieved_at=request.effective_retrieved_at,
                include_transcript=True,
            )
        else:  # pragma: no cover - guarded by request validation
            raise ValueError("Unsupported extended Research source kind")
        if token.cancelled:
            return _cancelled_result()
        return extended.to_service_result()

    def __getattr__(self, name: str):
        return getattr(self._delegate, name)


class ExtendedResearchDiscoveryService(ResearchDiscoveryService):
    """Preserve V2.1.2 discovery while typing recognized media/community candidates."""

    def discover(
        self,
        query: str,
        *,
        limit: int = 10,
        cancellation: ResearchCancellation | None = None,
    ) -> ResearchServiceResult:
        result = super().discover(query, limit=limit, cancellation=cancellation)
        return ExtendedSourceCoordinator.classify_discovery_result(result)


def _extend_page(page, coordinator: ExtendedSourceCoordinator) -> None:
    from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QTableWidget

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
    page._research_extended_sources = coordinator

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
    coordinator.allow_network = bool(network.isChecked())


def create_research_page(
    project_root: Path,
    *,
    translator,
    service=None,
    status_bar=None,
):
    root = Path(project_root).resolve(strict=False)
    base_service = service or ResearchService(root)
    secrets = _ensure_runtime_secrets(base_service)
    coordinator = ExtendedSourceCoordinator(
        root,
        allow_network=bool(base_service.allow_network),
        secrets=secrets,
        web_transport=base_service.web_transport,
        web_policy=base_service.web_policy,
    )
    adapted_service = ExtendedResearchServiceAdapter(base_service, coordinator)
    page = _ORIGINAL_CREATE_RESEARCH_PAGE(
        root,
        translator=translator,
        service=adapted_service,
        status_bar=status_bar,
    )
    _extend_page(page, coordinator)
    return page


def install_extended_research_ui() -> None:
    """Install V2.1.5 adapters before app.py imports create_research_page."""

    global _INSTALLED
    if _INSTALLED:
        return
    _panel.ResearchFetchRequest = ExtendedResearchFetchRequest
    _panel.ResearchDiscoveryService = ExtendedResearchDiscoveryService
    _panel.create_research_page = create_research_page
    _INSTALLED = True
