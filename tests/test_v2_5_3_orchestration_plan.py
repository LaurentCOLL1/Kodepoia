from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.orchestrator.plan import (
    ROUTE_CATALOG,
    OrchestrationEffect,
    OrchestrationPlan,
    OrchestrationRoute,
    OrchestrationTask,
)
from kodepoia.orchestrator.workspaces import WorkspaceIdentity


def _project(root: Path, name: str) -> Path:
    (root / ".kodepoia").mkdir(parents=True)
    (root / ".kodepoia" / "project.yaml").write_text(
        f"schema_version: 1\nname: {name}\nproject_type: tool\nplatforms:\n  - windows\n",
        encoding="utf-8",
    )
    return root


def test_plan_builds_deterministic_dag_and_preview(tmp_path: Path) -> None:
    alpha = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    beta = WorkspaceIdentity.from_project_root(_project(tmp_path / "beta", "Beta"))
    inspect = OrchestrationTask.for_workspace(
        task_id="inspect",
        workspace=alpha,
        goal="Inspect governed project context",
        route=OrchestrationRoute.PROJECT_CONTEXT,
        effect=OrchestrationEffect.READ_ONLY,
    )
    propose = OrchestrationTask.for_workspace(
        task_id="propose-change",
        workspace=beta,
        goal="Propose a bounded code change",
        route=OrchestrationRoute.KODECODE,
        effect=OrchestrationEffect.MUTATION_PROPOSED,
        dependencies=("inspect",),
        source_workspace_ids=(alpha.workspace_id,),
    )

    plan = OrchestrationPlan(plan_id="cross-project-review", tasks=(propose, inspect))
    preview = plan.preview()

    assert preview.topological_order == ("inspect", "propose-change")
    assert preview.ready_tasks == ("inspect",)
    assert preview.blocked_tasks == ("propose-change",)
    assert preview.blockers["propose-change"] == ("inspect",)
    assert preview.mutation_proposed_tasks == ("propose-change",)
    assert len(plan.digest_sha256) == 64


def test_plan_rejects_unknown_dependency_and_cycle(tmp_path: Path) -> None:
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    missing = OrchestrationTask.for_workspace(
        task_id="a",
        workspace=workspace,
        goal="A",
        route=OrchestrationRoute.RESEARCH,
        effect=OrchestrationEffect.READ_ONLY,
        dependencies=("missing",),
    )
    with pytest.raises(ValueError, match="unknown dependencies"):
        OrchestrationPlan(plan_id="missing", tasks=(missing,))

    first = OrchestrationTask.for_workspace(
        task_id="a",
        workspace=workspace,
        goal="A",
        route=OrchestrationRoute.RESEARCH,
        effect=OrchestrationEffect.READ_ONLY,
        dependencies=("b",),
    )
    second = OrchestrationTask.for_workspace(
        task_id="b",
        workspace=workspace,
        goal="B",
        route=OrchestrationRoute.RESEARCH,
        effect=OrchestrationEffect.READ_ONLY,
        dependencies=("a",),
    )
    with pytest.raises(ValueError, match="cycle"):
        OrchestrationPlan(plan_id="cycle", tasks=(first, second))


def test_route_catalog_is_fixed_and_effects_fail_closed(tmp_path: Path) -> None:
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))

    assert set(ROUTE_CATALOG) == {
        OrchestrationRoute.PROJECT_CONTEXT,
        OrchestrationRoute.RESEARCH,
        OrchestrationRoute.KODECODE,
        OrchestrationRoute.KODEGODOT,
        OrchestrationRoute.MODEL_LAB,
        OrchestrationRoute.SPECIALIST,
    }
    with pytest.raises(ValueError, match="not allowed"):
        OrchestrationTask.for_workspace(
            task_id="invalid-write",
            workspace=workspace,
            goal="Attempt unsupported mutation",
            route=OrchestrationRoute.RESEARCH,
            effect=OrchestrationEffect.MUTATION_PROPOSED,
        )


def test_task_scope_must_bind_workspace(tmp_path: Path) -> None:
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    with pytest.raises(ValueError, match="scope must bind"):
        OrchestrationTask(
            task_id="wrong-scope",
            workspace_id=workspace.workspace_id,
            workspace_scope="project:other",
            goal="Inspect",
            route=OrchestrationRoute.PROJECT_CONTEXT,
            effect=OrchestrationEffect.READ_ONLY,
        )


def test_plan_serialization_is_stable(tmp_path: Path) -> None:
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    task = OrchestrationTask.for_workspace(
        task_id="inspect",
        workspace=workspace,
        goal="Inspect",
        route=OrchestrationRoute.PROJECT_CONTEXT,
        effect=OrchestrationEffect.READ_ONLY,
    )
    first = OrchestrationPlan(plan_id="stable", tasks=(task,))
    second = OrchestrationPlan(plan_id="stable", tasks=(task,))
    assert first.to_dict() == second.to_dict()
    assert first.digest_sha256 == second.digest_sha256
