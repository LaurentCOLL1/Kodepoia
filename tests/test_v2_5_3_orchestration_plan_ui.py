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


def test_plan_preview_is_read_only_and_marks_mutation_as_proposal(tmp_path: Path) -> None:
    from PySide6.QtWidgets import QApplication, QLabel, QTableWidget

    from kodepoia.kodestudio.orchestration_plan_preview import (
        create_orchestration_plan_preview_widget,
    )
    from kodepoia.orchestrator.plan import (
        OrchestrationEffect,
        OrchestrationPlan,
        OrchestrationRoute,
        OrchestrationTask,
    )
    from kodepoia.orchestrator.workspaces import WorkspaceIdentity

    app = QApplication.instance() or QApplication([])
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    task = OrchestrationTask.for_workspace(
        task_id="propose",
        workspace=workspace,
        goal="Propose change",
        route=OrchestrationRoute.KODECODE,
        effect=OrchestrationEffect.MUTATION_PROPOSED,
    )
    plan = OrchestrationPlan(plan_id="preview", tasks=(task,))

    widget = create_orchestration_plan_preview_widget(plan)
    table = widget.findChild(QTableWidget, "orchestrationPlanTable")
    state = widget.findChild(QLabel, "orchestrationPlanState")

    assert table is not None and table.rowCount() == 1
    assert table.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
    assert table.item(0, 4).text() == "mutation_proposed"
    assert state is not None and "execution=not authorized" in state.text()
    widget.close()
    app.processEvents()
