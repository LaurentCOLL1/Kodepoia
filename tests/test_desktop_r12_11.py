from __future__ import annotations

import asyncio
import concurrent.futures

import pytest

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.desktop.async_runtime import (
    AsyncOperationDescriptor,
    AsyncOperationKind,
    AsyncOperationRuntime,
    AsyncPolicy,
    CompletionGate,
    DoubleCompletionError,
    OperationState,
    OperationTimeoutError,
    QueueCapacityError,
    StaleCallbackError,
    ThreadAffinity,
    UiThreadAffinityError,
    UiThreadDispatcher,
    canonical_dispatcher_binding,
)
from kodepoia.desktop.contracts import DesktopFramework


def test_policy_digest_and_dispatcher_bindings_are_deterministic() -> None:
    first = AsyncPolicy(max_concurrency=2, queue_capacity=3)
    second = AsyncPolicy(max_concurrency=2, queue_capacity=3)
    assert first.digest == second.digest

    mechanisms = {
        canonical_dispatcher_binding(framework).mechanism for framework in DesktopFramework
    }
    assert mechanisms == {
        "wpf.dispatcher",
        "winui3.dispatcher_queue",
        "avalonia.dispatcher_ui_thread",
        "qt6.queued_thread_affinity",
        "tauri2.main_thread_dispatch",
    }


def test_completion_gate_rejects_double_completion() -> None:
    gate: CompletionGate[str] = CompletionGate()
    assert gate.complete("done") == "done"
    assert gate.result == "done"
    with pytest.raises(DoubleCompletionError):
        gate.complete("again")


def test_bounded_concurrency_and_queue_capacity_are_deterministic() -> None:
    async def scenario() -> None:
        runtime = AsyncOperationRuntime(
            AsyncPolicy(
                max_concurrency=1,
                queue_capacity=1,
                queue_wait_timeout_seconds=1.0,
                operation_timeout_seconds=1.0,
            )
        )
        runtime.open_owner("window")
        release = asyncio.Event()
        started: list[str] = []

        async def work(context):
            started.append(context.descriptor.operation_id)
            context.progress.report(0, 1, "started")
            await release.wait()
            await context.checkpoint()
            context.progress.report(1, 1, "done")
            return context.descriptor.operation_id

        first = runtime.start(
            AsyncOperationDescriptor("op1", "window", AsyncOperationKind.COMPUTE),
            work,
        )
        second = runtime.start(
            AsyncOperationDescriptor("op2", "window", AsyncOperationKind.COMPUTE),
            work,
        )
        with pytest.raises(QueueCapacityError):
            runtime.start(
                AsyncOperationDescriptor("op3", "window", AsyncOperationKind.COMPUTE),
                work,
            )

        await asyncio.sleep(0)
        assert started == ["op1"]
        release.set()
        assert await first.wait() == "op1"
        assert await second.wait() == "op2"
        assert first.state is OperationState.SUCCEEDED
        assert second.state is OperationState.SUCCEEDED
        assert [item.completed for item in first.progress] == [0, 1]
        await runtime.shutdown()
        assert runtime.active_count == 0

    asyncio.run(scenario())


def test_queue_wait_timeout_fails_closed_without_starvation() -> None:
    async def scenario() -> None:
        runtime = AsyncOperationRuntime(
            AsyncPolicy(
                max_concurrency=1,
                queue_capacity=1,
                queue_wait_timeout_seconds=0.02,
                operation_timeout_seconds=1.0,
            )
        )
        runtime.open_owner("window")
        release = asyncio.Event()

        async def blocked(context):
            await release.wait()
            await context.checkpoint()
            return "released"

        first = runtime.start(
            AsyncOperationDescriptor("first", "window", AsyncOperationKind.IO),
            blocked,
        )
        second = runtime.start(
            AsyncOperationDescriptor("second", "window", AsyncOperationKind.IO),
            blocked,
        )
        with pytest.raises(OperationTimeoutError, match="concurrency slot"):
            await second.wait()
        assert second.state is OperationState.TIMED_OUT
        release.set()
        assert await first.wait() == "released"
        await runtime.shutdown()

    asyncio.run(scenario())


def test_explicit_cancellation_propagates_and_cleans_owner() -> None:
    async def scenario() -> None:
        runtime = AsyncOperationRuntime(AsyncPolicy(operation_timeout_seconds=1.0))
        runtime.open_owner("project")
        entered = asyncio.Event()

        async def work(context):
            entered.set()
            await asyncio.Event().wait()
            await context.checkpoint()
            return "unreachable"

        handle = runtime.start(
            AsyncOperationDescriptor("cancel-me", "project", AsyncOperationKind.COMPUTE),
            work,
        )
        await entered.wait()
        assert handle.cancel()
        assert not handle.cancel()
        with pytest.raises(asyncio.CancelledError):
            await handle.wait()
        assert handle.state is OperationState.CANCELLED
        assert handle.token.cancelled
        await runtime.close_owner("project")
        assert runtime.active_count == 0

    asyncio.run(scenario())


def test_operation_timeout_becomes_typed_terminal_state() -> None:
    async def scenario() -> None:
        runtime = AsyncOperationRuntime(
            AsyncPolicy(operation_timeout_seconds=0.02, queue_wait_timeout_seconds=1.0)
        )
        runtime.open_owner("project")

        async def slow(context):
            await asyncio.sleep(0.2)
            await context.checkpoint()
            return "late"

        handle = runtime.start(
            AsyncOperationDescriptor("slow", "project", AsyncOperationKind.IO),
            slow,
        )
        with pytest.raises(OperationTimeoutError, match="exceeded timeout"):
            await handle.wait()
        assert handle.state is OperationState.TIMED_OUT
        assert handle.token.cancelled
        await runtime.shutdown()

    asyncio.run(scenario())


def test_kill_switch_cancels_governed_external_operation_at_checkpoint() -> None:
    async def scenario() -> None:
        kill_switch = KillSwitch()
        runtime = AsyncOperationRuntime(
            AsyncPolicy(operation_timeout_seconds=1.0),
            kill_switch=kill_switch,
        )
        runtime.open_owner("build-run")
        entered = asyncio.Event()
        continue_work = asyncio.Event()

        async def build(context):
            entered.set()
            await continue_work.wait()
            await context.checkpoint()
            return "unreachable"

        handle = runtime.start(
            AsyncOperationDescriptor("build", "build-run", AsyncOperationKind.BUILD),
            build,
        )
        await entered.wait()
        assert kill_switch.trigger() == 0
        continue_work.set()
        with pytest.raises(asyncio.CancelledError):
            await handle.wait()
        assert handle.state is OperationState.CANCELLED
        assert handle.token.cancelled
        await runtime.shutdown()

    asyncio.run(scenario())


def test_close_during_task_invalidates_callbacks_and_leaves_no_orphans() -> None:
    async def scenario() -> None:
        runtime = AsyncOperationRuntime(AsyncPolicy(operation_timeout_seconds=1.0))
        lease = runtime.open_owner("window")
        captured = {}
        entered = asyncio.Event()

        async def work(context):
            captured["progress"] = context.progress
            entered.set()
            await asyncio.Event().wait()
            return "unreachable"

        handle = runtime.start(
            AsyncOperationDescriptor("owned", "window", AsyncOperationKind.COMPUTE),
            work,
        )
        await entered.wait()
        await runtime.close_owner("window")
        assert handle.state is OperationState.CANCELLED
        assert runtime.active_count == 0
        with pytest.raises(StaleCallbackError, match="stale"):
            runtime.assert_lease_current(lease)
        with pytest.raises(StaleCallbackError, match="stale"):
            captured["progress"].report(1, 1, "late")
        assert runtime.open_owner("window").generation > lease.generation
        await runtime.shutdown()

    asyncio.run(scenario())


def test_ui_dispatcher_enforces_affinity_and_rejects_stale_callbacks() -> None:
    async def scenario() -> None:
        runtime = AsyncOperationRuntime()
        lease = runtime.open_owner("window")
        dispatcher = UiThreadDispatcher(runtime, DesktopFramework.WINUI3)

        future = dispatcher.post(lease, lambda left, right: left + right, 2, 3)
        assert await asyncio.wrap_future(future) == 5

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            with pytest.raises(UiThreadAffinityError):
                await loop.run_in_executor(executor, dispatcher.assert_access)

        await runtime.close_owner("window")
        stale = dispatcher.post(lease, lambda: "late")
        with pytest.raises(StaleCallbackError):
            await asyncio.wrap_future(stale)
        await runtime.shutdown()

    asyncio.run(scenario())


def test_descriptor_validation_and_affinity_are_explicit() -> None:
    descriptor = AsyncOperationDescriptor(
        "operation",
        "owner",
        AsyncOperationKind.PERSISTENCE,
        affinity=ThreadAffinity.UI_THREAD,
        timeout_seconds=2.0,
    )
    assert descriptor.affinity is ThreadAffinity.UI_THREAD
    assert not descriptor.governed_external
    assert len(descriptor.digest) == 64

    with pytest.raises(ValueError, match="stable identifier"):
        AsyncOperationDescriptor("../escape", "owner", AsyncOperationKind.IO)
