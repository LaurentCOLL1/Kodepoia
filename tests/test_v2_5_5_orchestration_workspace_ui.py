from __future__ import annotations

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


def test_orchestration_workspace_exposes_integrated_readable_surfaces(tmp_path: Path) -> None:
    from PySide6.QtWidgets import QApplication, QTabWidget, QTableWidget

    from kodepoia.kodestudio.orchestration_workspace import create_orchestration_workspace
    from kodepoia.orchestrator.execution import DestinationServiceRegistry, GovernedExecutionCoordinator
    from kodepoia.orchestrator.plan import (
        OrchestrationEffect,
        OrchestrationPlan,
        OrchestrationRoute,
        OrchestrationTask,
    )
    from kodepoia.orchestrator.workspaces import WorkspaceRegistry

    app = QApplication.instance() or QApplication([])
    registry = WorkspaceRegistry()
    workspace = registry.register(_project(tmp_path / "alpha", "Alpha"))
    task = OrchestrationTask.for_workspace(
        task_id="inspect",
        workspace=workspace,
        goal="Inspect",
        route=OrchestrationRoute.KODECODE,
        effect=OrchestrationEffect.READ_ONLY,
    )
    plan = OrchestrationPlan(plan_id="workspace", tasks=(task,))
    coordinator = GovernedExecutionCoordinator(
        DestinationServiceRegistry({OrchestrationRoute.KODECODE: lambda _task, _confirmed: "ok"})
    )

    widget = create_orchestration_workspace(
        tmp_path,
        registry=registry,
        plan=plan,
        coordinator=coordinator,
    )
    tabs = widget.findChild(QTabWidget, "orchestrationWorkspaceTabs")
    workspaces = widget.findChild(QTableWidget, "orchestrationWorkspaceTable")
    history = widget.findChild(QTableWidget, "orchestrationHistoryTable")

    assert tabs is not None and tabs.count() == 5
    assert workspaces is not None and workspaces.rowCount() == 1
    assert history is not None and history.rowCount() >= 1
    assert workspaces.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
    assert history.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
    widget.close()
    app.processEvents()


@pytest.mark.parametrize("locale,prefix", [("fr", "Orchestration"), ("en", "Orchestration"), ("qps-ploc", "⟦")])
def test_orchestration_workspace_localization_and_accessibility(tmp_path: Path, locale: str, prefix: str) -> None:
    from PySide6.QtWidgets import QApplication, QPushButton

    from kodepoia.kodestudio.orchestration_workspace import (
        create_orchestration_workspace,
        orchestration_nav_text,
    )

    app = QApplication.instance() or QApplication([])
    widget = create_orchestration_workspace(tmp_path, locale=locale)
    approve = widget.findChild(QPushButton, "orchestrationApproveButton")
    cancel = widget.findChild(QPushButton, "orchestrationCancelButton")

    assert orchestration_nav_text(locale).startswith(prefix)
    assert widget.accessibleName()
    assert widget.accessibleDescription()
    assert approve is not None and approve.accessibleName()
    assert cancel is not None and cancel.accessibleName()
    if locale == "qps-ploc":
        assert approve.text().startswith("⟦") and approve.text().endswith("⟧")
    widget.close()
    app.processEvents()


def test_empty_workspace_is_honest_and_does_not_claim_execution(tmp_path: Path) -> None:
    from PySide6.QtWidgets import QApplication, QLabel

    from kodepoia.kodestudio.orchestration_workspace import create_orchestration_workspace

    app = QApplication.instance() or QApplication([])
    widget = create_orchestration_workspace(tmp_path)
    state = widget.findChild(QLabel, "orchestrationWorkspaceState")

    assert state is not None
    assert "No plan or handoff loaded" in state.text()
    widget.close()
    app.processEvents()
