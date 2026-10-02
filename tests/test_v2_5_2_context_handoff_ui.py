from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


pytest.importorskip("PySide6")


def _project(root: Path, name: str) -> Path:
    (root / ".kodepoia").mkdir(parents=True)
    (root / ".kodepoia" / "project.yaml").write_text(
        f"schema_version: 1\nname: {name}\nproject_type: tool\nplatforms:\n  - windows\n",
        encoding="utf-8",
    )
    return root


def test_handoff_inspector_is_read_only_and_surfaces_data_only_state(tmp_path: Path) -> None:
    from PySide6.QtWidgets import QApplication, QLabel, QTableWidget

    from kodepoia.intelligence.project_knowledge import ProjectKnowledgeSourceKind
    from kodepoia.intelligence.project_workspace import ProjectWorkspaceContextSnapshot, ProjectWorkspaceSource
    from kodepoia.kodestudio.workspace_handoff import create_workspace_handoff_inspector
    from kodepoia.orchestrator.handoff import WorkspaceContextHandoff
    from kodepoia.orchestrator.workspaces import WorkspaceIdentity

    app = QApplication.instance() or QApplication([])
    source = WorkspaceIdentity.from_project_root(_project(tmp_path / "source", "Source"))
    destination = WorkspaceIdentity.from_project_root(_project(tmp_path / "destination", "Destination"))
    digest = hashlib.sha256(b"content").hexdigest()
    snapshot = ProjectWorkspaceContextSnapshot(
        project_scope=source.project_scope,
        retrieval_digest_sha256=hashlib.sha256(b"retrieval").hexdigest(),
        context_bundle_digest_sha256=hashlib.sha256(b"bundle").hexdigest(),
        selected_content_sha256s=(digest,),
        sources=(
            ProjectWorkspaceSource(
                knowledge_id=hashlib.sha256(b"knowledge").hexdigest(),
                source_kind=ProjectKnowledgeSourceKind.RESEARCH_PACK,
                content_sha256=digest,
                source_digest_sha256=hashlib.sha256(b"source").hexdigest(),
                locator="research-pack:///fixture",
                trust_class="external_guarded_untrusted",
                freshness="current",
                version="1",
                citation_ids=("citation-a",),
            ),
        ),
        rendered_context="<UNTRUSTED_DATA>fixture</UNTRUSTED_DATA>",
    )
    handoff = WorkspaceContextHandoff.from_snapshot(
        source=source,
        destination=destination,
        snapshot=snapshot,
        purpose="inspect",
    )

    widget = create_workspace_handoff_inspector(handoff)
    table = widget.findChild(QTableWidget, "workspaceHandoffSourcesTable")
    state = widget.findChild(QLabel, "workspaceHandoffState")

    assert table is not None and table.rowCount() == 1
    assert table.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
    assert state is not None and "authority=data_only" in state.text()
    widget.close()
    app.processEvents()
