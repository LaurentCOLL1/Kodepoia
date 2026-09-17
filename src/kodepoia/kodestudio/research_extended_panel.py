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
_HARDENED_STATE_HELP = (
    "V2.1.6 hardened states: BLOCKED means policy denial; UNAVAILABLE means provider/transport "
    "failure; CANCELLED never promotes new evidence; STALE means cached evidence requires "
    "revalidation; CONFLICT preserves every immutable retrieved version in lineage."
)


def hardened_evidence_state_text(row: Any) -> str:
    """Render stale/version-conflict evidence state without requiring raw JSON inspection."""

    states: list[str] = []
    if str(getattr(row, "freshness", "")).strip().lower() == "stale":
        states.append("STALE — cached evidence requires revalidation")
    if bool(getattr(row, "has_version_conflict", False)):
        versions = tuple(str(value) for value in getattr(row, "conflicting_versions", ()))
        detail = ", ".join(versions) or "multiple versions"
        states.append(f"CONFLICT — immutable lineage versions: {detail}")
    return " | ".join(states)


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
        metadata={"v2_1_5": True, "v2_1_6_hardened": True},
    )


class ExtendedResearchServiceAdapter:
    """Delegate historical Research operations and route only extended fetch kinds."""

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
                cancellation=token,
            )
        elif request.kind is ResearchSourceKind.YOUTUBE:
            extended = self.coordinator.fetch_youtube(
                request.locator,
                retrieved_at=request.effective_retrieved_at,
                include_transcript=True,
                cancellation=token,
            )
        else:  # pragma: no cover - guarded by request validation
            raise ValueError("Unsupported extended Research source kind")
        if token.cancelled and extended.status is not ResearchOperationStatus.CANCELLED:
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
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QLabel,
        QLineEdit,
        QTableWidget,
        QTableWidgetItem,
    )

    fetch_kind = page.findChild(QComboBox, "researchFetchKind")
    locator = page.findChild(QLineEdit, "researchLocator")
    network = page.findChild(QCheckBox, "researchAllowNetwork")
    results = page.findChild(QTableWidget, "researchResultsTable")
    evidence_results = page.findChild(QTableWidget, "researchEvidenceWorkspaceTable")
    if (
        fetch_kind is None
        or locator is None
        or network is None
        or results is None
        or evidence_results is None
    ):
        raise RuntimeError("Research panel V2.1.6 extension requires the accepted Research UI contract")

    for kind in (ResearchSourceKind.COMMUNITY, ResearchSourceKind.YOUTUBE):
        if fetch_kind.findData(kind.value) < 0:
            fetch_kind.addItem(kind.value, kind.value)

    state = QLabel(_HARDENED_STATE_HELP)
    state.setObjectName("researchExtendedSourceState")
    state.setAccessibleName("Extended research provider and degraded state")
    state.setWordWrap(True)
    layout = page.layout()
    if layout is not None:
        layout.insertWidget(4, state)
    page._research_extended_source_state = state
    page._research_extended_sources = coordinator

    lineage_header = evidence_results.horizontalHeaderItem(6)
    if lineage_header is not None:
        lineage_header.setText("Lineage / hardening state")

    def refresh_hardened_evidence_state() -> None:
        workspace = getattr(page, "_research_workspace", None)
        rows = tuple(getattr(workspace, "rows", ()))
        selected_state = ""
        selected_row = evidence_results.currentRow()
        for row_index, item in enumerate(rows):
            if row_index >= evidence_results.rowCount():
                break
            lineage_count = len(item.lineage_revision_ids) or len(item.lineage_artifact_ids)
            degraded = hardened_evidence_state_text(item)
            rendered = str(lineage_count)
            if degraded:
                rendered = f"{rendered} | {degraded}"
            evidence_results.setItem(row_index, 6, QTableWidgetItem(rendered))
            if row_index == selected_row:
                selected_state = degraded
        state.setText(selected_state or _HARDENED_STATE_HELP)

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
    evidence_results.itemSelectionChanged.connect(refresh_hardened_evidence_state)

    def network_changed(checked: bool) -> None:
        coordinator.allow_network = bool(checked)

    network.toggled.connect(network_changed)
    coordinator.allow_network = bool(network.isChecked())
    refresh_hardened_evidence_state()


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
    """Install extended Research adapters before app.py imports create_research_page."""

    global _INSTALLED
    if _INSTALLED:
        return
    _panel.ResearchFetchRequest = ExtendedResearchFetchRequest
    _panel.ResearchDiscoveryService = ExtendedResearchDiscoveryService
    _panel.create_research_page = create_research_page
    _INSTALLED = True
