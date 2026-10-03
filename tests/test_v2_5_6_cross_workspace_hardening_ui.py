from __future__ import annotations

import json
from pathlib import Path

import pytest


pytest.importorskip("PySide6")


def test_v256_corrupt_history_remains_visible_and_disables_operations(tmp_path: Path) -> None:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from kodepoia.kodestudio.orchestration_workspace import create_orchestration_workspace
    from kodepoia.orchestrator.history import OrchestrationHistoryStore

    app = QApplication.instance() or QApplication([])
    store = OrchestrationHistoryStore(tmp_path)
    store.append(event="plan_loaded", plan_digest_sha256="a" * 64)
    payload = json.loads(store.path.read_text(encoding="utf-8").strip())
    payload["event"] = "tampered"
    store.path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    widget = create_orchestration_workspace(tmp_path, history_store=store)
    state = widget.findChild(QLabel, "orchestrationWorkspaceState")
    execute = widget.findChild(QPushButton, "orchestrationExecuteButton")
    approve = widget.findChild(QPushButton, "orchestrationApproveButton")

    assert state is not None and "Invalid history" in state.text()
    assert execute is not None and execute.isEnabled() is False
    assert approve is not None and approve.isEnabled() is False
    widget.close()
    app.processEvents()


def test_v256_missing_coordinator_is_explicit_and_non_authorizing(tmp_path: Path) -> None:
    from PySide6.QtWidgets import QApplication, QLabel

    from kodepoia.kodestudio.orchestration_workspace import create_orchestration_workspace
    from kodepoia.orchestrator.plan import (
        OrchestrationEffect,
        OrchestrationPlan,
        OrchestrationRoute,
        OrchestrationTask,
    )
    from kodepoia.orchestrator.workspaces import WorkspaceIdentity

    project = tmp_path / "alpha"
    (project / ".kodepoia").mkdir(parents=True)
    (project / ".kodepoia" / "project.yaml").write_text(
        "schema_version: 1\nname: Alpha\nproject_type: tool\nplatforms:\n  - windows\n",
        encoding="utf-8",
    )
    workspace = WorkspaceIdentity.from_project_root(project)
    task = OrchestrationTask.for_workspace(
        task_id="inspect",
        workspace=workspace,
        goal="Inspect",
        route=OrchestrationRoute.PROJECT_CONTEXT,
        effect=OrchestrationEffect.READ_ONLY,
    )
    plan = OrchestrationPlan(plan_id="degraded", tasks=(task,))

    app = QApplication.instance() or QApplication([])
    widget = create_orchestration_workspace(tmp_path, plan=plan)
    state = widget.findChild(QLabel, "orchestrationWorkspaceState")

    assert state is not None
    assert "execution is unavailable" in state.text()
    widget.close()
    app.processEvents()
