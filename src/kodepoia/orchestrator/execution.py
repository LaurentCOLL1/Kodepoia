from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.secret_guard import SecretTaintGuard
from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend
from kodepoia.orchestrator.handoff import WorkspaceContextHandoff
from kodepoia.orchestrator.plan import (
    OrchestrationEffect,
    OrchestrationPlan,
    OrchestrationRoute,
    OrchestrationTask,
)
from kodepoia.orchestrator.workspaces import WorkspaceRegistry

EXECUTION_SCHEMA_VERSION = 1


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


class ExecutionState(StrEnum):
    PROPOSED = "proposed"
    AWAITING_APPROVAL = "awaiting_approval"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class MutationApproval:
    plan_digest_sha256: str
    task_digest_sha256: str
    workspace_id: str
    input_handoff_digests: tuple[str, ...]
    confirmed: bool
    schema_version: int = EXECUTION_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != EXECUTION_SCHEMA_VERSION:
            raise ValueError("Unsupported mutation approval schema version")
        if not self.confirmed:
            raise ValueError("Mutation approval must represent explicit confirmation")
        payload = self._payload_without_digest()
        object.__setattr__(self, "digest_sha256", _sha256_payload(payload))

    @classmethod
    def for_task(cls, plan: OrchestrationPlan, task: OrchestrationTask) -> MutationApproval:
        return cls(
            plan_digest_sha256=plan.digest_sha256,
            task_digest_sha256=task.digest_sha256,
            workspace_id=task.workspace_id,
            input_handoff_digests=task.input_handoff_digests,
            confirmed=True,
        )

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plan_digest_sha256": self.plan_digest_sha256,
            "task_digest_sha256": self.task_digest_sha256,
            "workspace_id": self.workspace_id,
            "input_handoff_digests": list(self.input_handoff_digests),
            "confirmed": self.confirmed,
        }


@dataclass(frozen=True, slots=True)
class ExecutionEvidence:
    plan_digest_sha256: str
    task_digest_sha256: str
    workspace_id: str
    route: str
    effect: str
    state: ExecutionState
    output: Any = None
    error_type: str = ""
    schema_version: int = EXECUTION_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "digest_sha256", _sha256_payload(self._payload_without_digest()))

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plan_digest_sha256": self.plan_digest_sha256,
            "task_digest_sha256": self.task_digest_sha256,
            "workspace_id": self.workspace_id,
            "route": self.route,
            "effect": self.effect,
            "state": self.state.value,
            "output": self.output,
            "error_type": self.error_type,
        }


@dataclass(frozen=True, slots=True)
class RecoveryBinding:
    plan_digest_sha256: str
    task_digest_sha256: str
    workspace_id: str
    input_handoff_digests: tuple[str, ...]
    schema_version: int = EXECUTION_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "digest_sha256",
            _sha256_payload(
                {
                    "schema_version": self.schema_version,
                    "plan_digest_sha256": self.plan_digest_sha256,
                    "task_digest_sha256": self.task_digest_sha256,
                    "workspace_id": self.workspace_id,
                    "input_handoff_digests": list(self.input_handoff_digests),
                }
            ),
        )

    @classmethod
    def for_task(cls, plan: OrchestrationPlan, task: OrchestrationTask) -> RecoveryBinding:
        return cls(
            plan_digest_sha256=plan.digest_sha256,
            task_digest_sha256=task.digest_sha256,
            workspace_id=task.workspace_id,
            input_handoff_digests=task.input_handoff_digests,
        )

    def assert_compatible(self, plan: OrchestrationPlan, task: OrchestrationTask) -> None:
        expected = RecoveryBinding.for_task(plan, task)
        if self.digest_sha256 != expected.digest_sha256:
            raise ValueError("Recovery binding is incompatible with current plan/task/workspace/handoff lineage")


DestinationHandler = Callable[[OrchestrationTask, bool], Any]


class DestinationServiceRegistry:
    """Fixed typed routing to destination-owned service adapters."""

    def __init__(self, handlers: Mapping[OrchestrationRoute, DestinationHandler]) -> None:
        self._handlers = dict(handlers)

    def execute(self, task: OrchestrationTask, *, confirmed: bool) -> Any:
        handler = self._handlers.get(task.route)
        if handler is None:
            raise KeyError(f"No destination service registered for route: {task.route.value}")
        return handler(task, confirmed)


class GovernedExecutionCoordinator:
    """Coordinate approved plan tasks without exposing raw process-launch configuration."""

    def __init__(
        self,
        services: DestinationServiceRegistry,
        *,
        max_concurrency: int = 2,
        kill_switch: KillSwitch | None = None,
        workspace_registry: WorkspaceRegistry | None = None,
        handoffs: Mapping[str, WorkspaceContextHandoff] | None = None,
        secret_guard: SecretTaintGuard | None = None,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")
        self.services = services
        self.kill_switch = kill_switch or KillSwitch()
        self.workspace_registry = workspace_registry
        self.handoffs = dict(handoffs or {})
        self.secret_guard = secret_guard or SecretTaintGuard(
            KodeSecrets(MemorySecretBackend())
        )
        self._slots = threading.BoundedSemaphore(max_concurrency)
        self._lock = threading.RLock()
        self._workspace_locks: set[str] = set()
        self._cancelled_plans: set[str] = set()
        self._evidence: dict[str, ExecutionEvidence] = {}

    @staticmethod
    def _task(plan: OrchestrationPlan, task_id: str) -> OrchestrationTask:
        for task in plan.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"Unknown orchestration task: {task_id}")

    @staticmethod
    def _approval_matches(
        approval: MutationApproval | None,
        plan: OrchestrationPlan,
        task: OrchestrationTask,
    ) -> bool:
        if approval is None:
            return False
        expected = MutationApproval.for_task(plan, task)
        return approval.digest_sha256 == expected.digest_sha256

    def _preflight_error(self, task: OrchestrationTask) -> str:
        if self.workspace_registry is not None:
            try:
                self.workspace_registry.assert_current(task.workspace_id)
            except (KeyError, ValueError):
                return "WorkspaceIdentityDrift"
        for digest in task.input_handoff_digests:
            handoff = self.handoffs.get(digest)
            if handoff is None:
                return "MissingHandoffEvidence"
            if handoff.digest_sha256 != digest:
                return "HandoffDigestMismatch"
            try:
                handoff.assert_usable_for(
                    task.workspace_id,
                    source_workspace_ids=task.source_workspace_ids,
                )
            except ValueError:
                return "InvalidHandoffEvidence"
        return ""

    def _sanitize_output(self, output: Any) -> Any:
        return self.secret_guard.sanitize_payload(output)

    def cancel_plan(self, plan: OrchestrationPlan) -> int:
        with self._lock:
            self._cancelled_plans.add(plan.digest_sha256)
        return self.kill_switch.trigger()

    def execute(
        self,
        plan: OrchestrationPlan,
        task_id: str,
        *,
        approval: MutationApproval | None = None,
    ) -> ExecutionEvidence:
        task = self._task(plan, task_id)

        preflight_error = self._preflight_error(task)
        if preflight_error:
            evidence = self._make_evidence(
                plan,
                task,
                ExecutionState.BLOCKED,
                error_type=preflight_error,
            )
            self._evidence[task.task_id] = evidence
            return evidence

        if plan.digest_sha256 in self._cancelled_plans or self.kill_switch.triggered:
            evidence = self._make_evidence(plan, task, ExecutionState.CANCELLED)
            self._evidence[task.task_id] = evidence
            return evidence

        for dependency in task.dependencies:
            dependency_evidence = self._evidence.get(dependency)
            if dependency_evidence is None or dependency_evidence.state is not ExecutionState.COMPLETED:
                evidence = self._make_evidence(plan, task, ExecutionState.BLOCKED)
                self._evidence[task.task_id] = evidence
                return evidence

        confirmed = task.effect is OrchestrationEffect.READ_ONLY
        if task.effect is OrchestrationEffect.MUTATION_PROPOSED:
            confirmed = self._approval_matches(approval, plan, task)
            if not confirmed:
                evidence = self._make_evidence(plan, task, ExecutionState.AWAITING_APPROVAL)
                self._evidence[task.task_id] = evidence
                return evidence

        with self._slots:
            with self._lock:
                if task.workspace_id in self._workspace_locks:
                    evidence = self._make_evidence(plan, task, ExecutionState.BLOCKED)
                    self._evidence[task.task_id] = evidence
                    return evidence
                self._workspace_locks.add(task.workspace_id)
            try:
                if plan.digest_sha256 in self._cancelled_plans or self.kill_switch.triggered:
                    evidence = self._make_evidence(plan, task, ExecutionState.CANCELLED)
                else:
                    try:
                        output = self.services.execute(task, confirmed=confirmed)
                    except Exception as exc:
                        evidence = self._make_evidence(
                            plan,
                            task,
                            ExecutionState.FAILED,
                            error_type=type(exc).__name__,
                        )
                    else:
                        state = (
                            ExecutionState.CANCELLED
                            if self.kill_switch.triggered
                            else ExecutionState.COMPLETED
                        )
                        evidence = self._make_evidence(
                            plan,
                            task,
                            state,
                            output=self._sanitize_output(output),
                        )
            finally:
                with self._lock:
                    self._workspace_locks.discard(task.workspace_id)

        self._evidence[task.task_id] = evidence
        return evidence

    def recover(
        self,
        plan: OrchestrationPlan,
        task_id: str,
        binding: RecoveryBinding,
        *,
        approval: MutationApproval | None = None,
    ) -> ExecutionEvidence:
        task = self._task(plan, task_id)
        binding.assert_compatible(plan, task)
        prior = self._evidence.get(task_id)
        if prior is not None and prior.state is ExecutionState.COMPLETED:
            raise ValueError("Completed task cannot be recovered")
        return self.execute(plan, task_id, approval=approval)

    @staticmethod
    def _make_evidence(
        plan: OrchestrationPlan,
        task: OrchestrationTask,
        state: ExecutionState,
        *,
        output: Any = None,
        error_type: str = "",
    ) -> ExecutionEvidence:
        return ExecutionEvidence(
            plan_digest_sha256=plan.digest_sha256,
            task_digest_sha256=task.digest_sha256,
            workspace_id=task.workspace_id,
            route=task.route.value,
            effect=task.effect.value,
            state=state,
            output=output,
            error_type=error_type,
        )


__all__ = [
    "EXECUTION_SCHEMA_VERSION",
    "DestinationServiceRegistry",
    "ExecutionEvidence",
    "ExecutionState",
    "GovernedExecutionCoordinator",
    "MutationApproval",
    "RecoveryBinding",
]
