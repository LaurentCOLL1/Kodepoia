from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.orchestrator.execution import (
    DestinationServiceRegistry,
    ExecutionState,
    GovernedExecutionCoordinator,
    MutationApproval,
    RecoveryBinding,
)
from kodepoia.orchestrator.plan import (
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


def _task(
    workspace: WorkspaceIdentity,
    task_id: str,
    *,
    effect: OrchestrationEffect = OrchestrationEffect.READ_ONLY,
    dependencies: tuple[str, ...] = (),
    handoffs: tuple[str, ...] = (),
) -> OrchestrationTask:
    return OrchestrationTask.for_workspace(
        task_id=task_id,
        workspace=workspace,
        goal=task_id,
        route=OrchestrationRoute.KODECODE,
        effect=effect,
        dependencies=dependencies,
        input_handoff_digests=handoffs,
    )


def test_mutation_requires_exact_approval(tmp_path: Path) -> None:
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    task = _task(workspace, "mutate", effect=OrchestrationEffect.MUTATION_PROPOSED)
    plan = OrchestrationPlan(plan_id="p", tasks=(task,))
    calls: list[bool] = []
    services = DestinationServiceRegistry(
        {OrchestrationRoute.KODECODE: lambda _task, confirmed: calls.append(confirmed) or "ok"}
    )
    coordinator = GovernedExecutionCoordinator(services)

    pending = coordinator.execute(plan, "mutate")
    assert pending.state is ExecutionState.AWAITING_APPROVAL
    assert calls == []

    approval = MutationApproval.for_task(plan, task)
    completed = coordinator.execute(plan, "mutate", approval=approval)
    assert completed.state is ExecutionState.COMPLETED
    assert calls == [True]


def test_dependency_failure_blocks_downstream(tmp_path: Path) -> None:
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    first = _task(workspace, "first")
    second = _task(workspace, "second", dependencies=("first",))
    plan = OrchestrationPlan(plan_id="p", tasks=(first, second))

    def fail(_task: OrchestrationTask, _confirmed: bool) -> str:
        raise RuntimeError("boom")

    coordinator = GovernedExecutionCoordinator(
        DestinationServiceRegistry({OrchestrationRoute.KODECODE: fail})
    )
    assert coordinator.execute(plan, "first").state is ExecutionState.FAILED
    assert coordinator.execute(plan, "second").state is ExecutionState.BLOCKED


def test_cancel_plan_uses_kill_switch_and_blocks_new_work(tmp_path: Path) -> None:
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    task = _task(workspace, "read")
    plan = OrchestrationPlan(plan_id="p", tasks=(task,))
    kill_switch = KillSwitch()
    coordinator = GovernedExecutionCoordinator(
        DestinationServiceRegistry({OrchestrationRoute.KODECODE: lambda _task, _confirmed: "ok"}),
        kill_switch=kill_switch,
    )

    assert coordinator.cancel_plan(plan) == 0
    assert kill_switch.triggered is True
    assert coordinator.execute(plan, "read").state is ExecutionState.CANCELLED


def test_recovery_is_lineage_bound(tmp_path: Path) -> None:
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    task = _task(workspace, "read", handoffs=("a" * 64,))
    plan = OrchestrationPlan(plan_id="p", tasks=(task,))
    binding = RecoveryBinding.for_task(plan, task)

    coordinator = GovernedExecutionCoordinator(
        DestinationServiceRegistry({OrchestrationRoute.KODECODE: lambda _task, _confirmed: "ok"})
    )
    completed = coordinator.recover(plan, "read", binding)
    assert completed.state is ExecutionState.COMPLETED

    changed_task = _task(workspace, "read", handoffs=("b" * 64,))
    changed_plan = OrchestrationPlan(plan_id="p", tasks=(changed_task,))
    with pytest.raises(ValueError, match="incompatible"):
        binding.assert_compatible(changed_plan, changed_task)


def test_destination_service_registry_is_fixed_by_route(tmp_path: Path) -> None:
    workspace = WorkspaceIdentity.from_project_root(_project(tmp_path / "alpha", "Alpha"))
    task = _task(workspace, "read")
    plan = OrchestrationPlan(plan_id="p", tasks=(task,))
    coordinator = GovernedExecutionCoordinator(DestinationServiceRegistry({}))

    evidence = coordinator.execute(plan, "read")
    assert evidence.state is ExecutionState.FAILED
    assert evidence.error_type == "KeyError"
