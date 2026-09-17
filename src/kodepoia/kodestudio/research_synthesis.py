from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from kodepoia.core.secrets import KodeSecrets
from kodepoia.intelligence.research.evidence import EvidenceSelection, EvidenceWorkspace
from kodepoia.intelligence.research.synthesis import (
    CitedSynthesisService,
    ResearchPackStore,
    ResearchSynthesis,
)
from kodepoia.kodestudio.accessibility import mark_accessible


def create_cited_synthesis_widget(
    project_root: Path,
    *,
    workspace_provider: Callable[[], EvidenceWorkspace],
    selection_provider: Callable[[], dict[str, EvidenceSelection]],
    question_provider: Callable[[], str],
    secrets: KodeSecrets | None = None,
):
    """Create the V2.1.4 structured synthesis/save surface for KodeStudio."""

    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    widget = QWidget()
    widget.setObjectName("researchCitedSynthesisWidget")
    layout = QVBoxLayout(widget)

    title = QLabel("Cited synthesis")
    title.setObjectName("researchCitedSynthesisLabel")
    layout.addWidget(title)

    actions = QHBoxLayout()
    synthesize_button = mark_accessible(
        QPushButton("Synthesize included evidence"),
        object_name="researchSynthesizeButton",
        name="Synthesize included evidence",
        description="Create a cited synthesis only from explicitly included fetched evidence.",
        description_required=True,
    )
    save_button = mark_accessible(
        QPushButton("Save Research Pack"),
        object_name="researchSavePackButton",
        name="Save Research Pack",
        description="Persist the current citation-bearing synthesis as governed project knowledge.",
        description_required=True,
    )
    save_button.setEnabled(False)
    actions.addWidget(synthesize_button)
    actions.addWidget(save_button)
    actions.addStretch(1)
    layout.addLayout(actions)

    state = QLabel("No synthesis yet. Explicitly include fetched evidence before synthesis.")
    state.setObjectName("researchSynthesisState")
    state.setWordWrap(True)
    layout.addWidget(state)

    claims = mark_accessible(
        QTableWidget(0, 5),
        object_name="researchSynthesisClaimsTable",
        name="Cited synthesis claims",
        description="Claim kind, text, immutable citation provenance, confidence and uncertainty.",
        description_required=True,
    )
    claims.setHorizontalHeaderLabels(["Kind", "Claim", "Citations", "Confidence", "Uncertainty"])
    claims.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    claims.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(claims)

    provenance = QLabel("")
    provenance.setObjectName("researchSynthesisProvenance")
    provenance.setWordWrap(True)
    layout.addWidget(provenance)

    synthesis_service = CitedSynthesisService(project_root, secrets=secrets)
    pack_store = ResearchPackStore(project_root)
    widget._research_synthesis = None
    widget._research_pack_path = None

    def render(synthesis: ResearchSynthesis) -> None:
        widget._research_synthesis = synthesis
        claims.setRowCount(len(synthesis.claims))
        citation_map = {item.citation_id: item for item in synthesis.citations}
        for row, claim in enumerate(synthesis.claims):
            citation_text = ", ".join(
                f"{citation_map[citation_id].artifact_id[:10]}@{citation_map[citation_id].revision_id[:10]}"
                for citation_id in claim.citation_ids
                if citation_id in citation_map
            ) or "—"
            values = (
                claim.kind.value,
                claim.claim,
                citation_text,
                "—" if claim.confidence is None else f"{claim.confidence:.2f}",
                claim.uncertainty or "—",
            )
            for column, value in enumerate(values):
                claims.setItem(row, column, QTableWidgetItem(value))
        conflict = f"conflicts={len(synthesis.conflicts)}"
        uncertainty = f"uncertainty={len(synthesis.uncertainty)}"
        state.setText(
            f"Synthesis ready: {len(synthesis.claims)} claims, {len(synthesis.citations)} citations; "
            f"{conflict}; {uncertainty}."
        )
        provenance.setText(
            "Citation provenance pinned to exact artifact/revision IDs. "
            f"synthesis_digest={synthesis.digest_sha256}"
        )
        save_button.setEnabled(True)

    def synthesize() -> None:
        try:
            result = synthesis_service.synthesize(
                question_provider(),
                workspace_provider(),
                explicit_selections=selection_provider(),
                generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            )
        except Exception as exc:
            widget._research_synthesis = None
            claims.setRowCount(0)
            provenance.setText("")
            state.setText(f"Synthesis unavailable: {exc}")
            save_button.setEnabled(False)
            return
        render(result)

    def save_pack() -> None:
        synthesis = widget._research_synthesis
        if synthesis is None:
            return
        pack = synthesis_service.pack(synthesis)
        path = pack_store.save(pack)
        widget._research_pack_path = path
        state.setText(
            f"Research Pack saved: {path.name} | digest={pack.digest_sha256} | "
            "citation provenance remains pinned."
        )

    synthesize_button.clicked.connect(synthesize)
    save_button.clicked.connect(save_pack)
    widget._research_run_synthesis = synthesize
    widget._research_save_pack = save_pack
    widget._research_render_synthesis = render
    return widget