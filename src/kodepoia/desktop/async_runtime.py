from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import inspect
import json
import re
import threading
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Generic, TypeVar

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch

from .contracts import DesktopFramework

_T = TypeVar("_T")
_STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _require_stable_id(value: str, field: str) -> None:
    if not isinstance(value, str) or _STABLE_ID.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")


def _canonical_digest(payload: dict[str, object]) -> str:
    data = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class AsyncOperationKind(StrEnum):
    BUILD = "build"
    TEST = "test"
    PACKAGE = "package"
    PERSISTENCE = "persistence"
    COMPUTE = "compute"
    IO = "io"


class ThreadAffinity(StrEnum):
    UI_THREAD = "ui_thread"
    BACKGROUND = "background"
    ANY = "any"


class OperationState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


class OwnerState(StrEnum):
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


class QueueCapacityError(RuntimeError):
    pass


class OperationTimeoutError(TimeoutError):
    pass


class DoubleCompletionError(RuntimeError):
    pass


class StaleCallbackError(RuntimeError):
    pass


class UiThreadAffinityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AsyncPolicy:
    max_concurrency: int = 4
    queue_capacity: int = 16
    queue_wait_timeout_seconds: float = 5.0
    operation_timeout_seconds: float = 60.0
    max_progress_snapshots: int = 128

    def __post_init__(self) -> None:
        if not 1 <= self.max_concurrency <= 64:
            raise ValueError("max_concurrency must be between 1 and 64")
        if not 0 <= self.queue_capacity <= 4096:
            raise ValueError("queue_capacity must be between 0 and 4096")
        if not 0.001 <= self.queue_wait_timeout_seconds <= 3600:
            raise ValueError("queue_wait_timeout_seconds must be bounded and positive")
        if not 0.001 <= self.operation_timeout_seconds <= 86400:
            raise ValueError("operation_timeout_seconds must be bounded and positive")
        if not 1 <= self.max_progress_snapshots <= 4096:
            raise ValueError("max_progress_snapshots must be between 1 and 4096")

    def canonical(self) -> dict[str, object]:
        return {
            "max_concurrency": self.max_concurrency,
            "max_progress_snapshots": self.max_progress_snapshots,
            "operation_timeout_seconds": self.operation_timeout_seconds,
            "queue_capacity": self.queue_capacity,
            "queue_wait_timeout_seconds": self.queue_wait_timeout_seconds,
        }

    @property
    def digest(self) -> str:
        return _canonical_digest(self.canonical())


@dataclass(frozen=True, slots=True)
class AsyncOperationDescriptor:
    operation_id: str
    owner_id: str
    kind: AsyncOperationKind
    affinity: ThreadAffinity = ThreadAffinity.BACKGROUND
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        _require_stable_id(self.operation_id, "operation_id")
        _require_stable_id(self.owner_id, "owner_id")
        if self.timeout_seconds is not None and not 0.001 <= self.timeout_seconds <= 86400:
            raise ValueError("timeout_seconds must be bounded and positive")

    @property
    def governed_external(self) -> bool:
        return self.kind in {
            AsyncOperationKind.BUILD,
            AsyncOperationKind.TEST,
            AsyncOperationKind.PACKAGE,
        }

    def canonical(self) -> dict[str, object]:
        return {
            "affinity": self.affinity.value,
            "kind": self.kind.value,
            "operation_id": self.operation_id,
            "owner_id": self.owner_id,
            "timeout_seconds": self.timeout_seconds,
        }

    @property
    def digest(self) -> str:
        return _canonical_digest(self.canonical())


@dataclass(frozen=True, slots=True)
class ProgressSnapshot:
    sequence: int
    completed: int
    total: int | None
    message: str
    state: OperationState

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("progress sequence must be positive")
        if self.completed < 0:
            raise ValueError("completed progress cannot be negative")
        if self.total is not None and (self.total < 0 or self.completed > self.total):
            raise ValueError("invalid total progress")
        if len(self.message) > 512 or "\x00" in self.message:
            raise ValueError("progress message must be bounded text")


@dataclass(frozen=True, slots=True)
class CallbackLease:
    owner_id: str
    generation: int

    def __post_init__(self) -> None:
        _require_stable_id(self.owner_id, "owner_id")
        if self.generation < 1:
            raise ValueError("lease generation must be positive")


@dataclass(frozen=True, slots=True)
class DispatcherBinding:
    framework: DesktopFramework
    mechanism: str
    affinity: ThreadAffinity = ThreadAffinity.UI_THREAD

    def __post_init__(self) -> None:
        _require_stable_id(self.mechanism, "mechanism")


_DISPATCHER_BINDINGS = {
    DesktopFramework.WPF: DispatcherBinding(DesktopFramework.WPF, "wpf.dispatcher"),
    DesktopFramework.WINUI3: DispatcherBinding(
        DesktopFramework.WINUI3, "winui3.dispatcher_queue"
    ),
    DesktopFramework.AVALONIA: DispatcherBinding(
        DesktopFramework.AVALONIA, "avalonia.dispatcher_ui_thread"
    ),
    DesktopFramework.QT6: DispatcherBinding(DesktopFramework.QT6, "qt6.queued_thread_affinity"),
    DesktopFramework.TAURI2: DispatcherBinding(
        DesktopFramework.TAURI2, "tauri2.main_thread_dispatch"
    ),
}


def canonical_dispatcher_binding(framework: DesktopFramework) -> DispatcherBinding:
    return _DISPATCHER_BINDINGS[framework]


class CancellationToken:
    def __init__(self) -> None:
        self._cancelled = threading.Event()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    def cancel(self) -> bool:
        already_cancelled = self.cancelled
        self._cancelled.set()
        return not already_cancelled

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise asyncio.CancelledError


class CompletionGate(Generic[_T]):
    def __init__(self) -> None:
        self._completed = False
        self._result: _T | None = None
        self._lock = threading.Lock()

    @property
    def completed(self) -> bool:
        with self._lock:
            return self._completed

    def complete(self, value: _T) -> _T:
        with self._lock:
            if self._completed:
                raise DoubleCompletionError("operation completion is single-assignment")
            self._completed = True
            self._result = value
            return value

    @property
    def result(self) -> _T:
        with self._lock:
            if not self._completed:
                raise RuntimeError("completion result is not available")
            return self._result  # type: ignore[return-value]


@dataclass(slots=True)
class _OwnerRecord:
    generation: int
    state: OwnerState
    tasks: set[asyncio.Task[Any]]


class ProgressReporter:
    def __init__(
        self,
        *,
        lease: CallbackLease,
        lease_validator: Callable[[CallbackLease], None],
        state_getter: Callable[[], OperationState],
        maximum: int,
    ) -> None:
        self._lease = lease
        self._lease_validator = lease_validator
        self._state_getter = state_getter
        self._maximum = maximum
        self._history: list[ProgressSnapshot] = []
        self._sequence = 0

    @property
    def history(self) -> tuple[ProgressSnapshot, ...]:
        return tuple(self._history)

    def report(self, completed: int, total: int | None = None, message: str = "") -> ProgressSnapshot:
        self._lease_validator(self._lease)
        state = self._state_getter()
        if state in {
            OperationState.CANCELLED,
            OperationState.SUCCEEDED,
            OperationState.FAILED,
            OperationState.TIMED_OUT,
        }:
            raise StaleCallbackError("progress callback arrived after terminal completion")
        if self._history and completed < self._history[-1].completed:
            raise ValueError("progress cannot move backwards")
        self._sequence += 1
        snapshot = ProgressSnapshot(self._sequence, completed, total, message, state)
        self._history.append(snapshot)
        if len(self._history) > self._maximum:
            del self._history[: len(self._history) - self._maximum]
        return snapshot


class OperationContext:
    def __init__(
        self,
        descriptor: AsyncOperationDescriptor,
        token: CancellationToken,
        progress: ProgressReporter,
        kill_switch: KillSwitch,
    ) -> None:
        self.descriptor = descriptor
        self.cancellation = token
        self.progress = progress
        self.kill_switch = kill_switch

    async def checkpoint(self) -> None:
        self.cancellation.raise_if_cancelled()
        if self.descriptor.governed_external and self.kill_switch.triggered:
            self.cancellation.cancel()
            raise asyncio.CancelledError
        await asyncio.sleep(0)
        self.cancellation.raise_if_cancelled()


class AsyncOperationHandle(Generic[_T]):
    def __init__(
        self,
        descriptor: AsyncOperationDescriptor,
        token: CancellationToken,
        lease: CallbackLease,
    ) -> None:
        self.descriptor = descriptor
        self.token = token
        self.lease = lease
        self.state = OperationState.PENDING
        self._task: asyncio.Task[_T] | None = None
        self._progress: ProgressReporter | None = None

    @property
    def done(self) -> bool:
        return self.state in {
            OperationState.CANCELLED,
            OperationState.SUCCEEDED,
            OperationState.FAILED,
            OperationState.TIMED_OUT,
        }

    @property
    def progress(self) -> tuple[ProgressSnapshot, ...]:
        return () if self._progress is None else self._progress.history

    def _bind_task(self, task: asyncio.Task[_T]) -> None:
        if self._task is not None:
            raise RuntimeError("operation task already bound")
        self._task = task

    def _bind_progress(self, reporter: ProgressReporter) -> None:
        if self._progress is not None:
            raise RuntimeError("progress reporter already bound")
        self._progress = reporter

    def _finish(self, state: OperationState) -> None:
        if self.done:
            raise DoubleCompletionError("operation already reached a terminal state")
        self.state = state

    def cancel(self) -> bool:
        if self.done:
            return False
        changed = self.token.cancel()
        if self.state in {OperationState.PENDING, OperationState.RUNNING}:
            self.state = OperationState.CANCELLING
        if self._task is not None and not self._task.done():
            self._task.cancel()
        return changed

    async def wait(self) -> _T:
        if self._task is None:
            raise RuntimeError("operation task is not bound")
        return await self._task


OperationCallable = Callable[[OperationContext], Awaitable[_T]]


class AsyncOperationRuntime:
    """Bounded, owner-scoped async operation runtime.

    The runtime creates tasks only for explicitly submitted operations. It does not
    create persistent workers, daemon threads, polling loops or hidden background jobs.
    """

    def __init__(
        self,
        policy: AsyncPolicy | None = None,
        *,
        kill_switch: KillSwitch = GLOBAL_KILL_SWITCH,
    ) -> None:
        self.policy = policy or AsyncPolicy()
        self.kill_switch = kill_switch
        self._semaphore = asyncio.Semaphore(self.policy.max_concurrency)
        self._owners: dict[str, _OwnerRecord] = {}
        self._handles: dict[str, AsyncOperationHandle[Any]] = {}

    @property
    def active_count(self) -> int:
        return sum(not handle.done for handle in self._handles.values())

    @property
    def owner_count(self) -> int:
        return sum(record.state is OwnerState.OPEN for record in self._owners.values())

    def open_owner(self, owner_id: str) -> CallbackLease:
        _require_stable_id(owner_id, "owner_id")
        existing = self._owners.get(owner_id)
        if existing is not None and existing.state is not OwnerState.CLOSED:
            raise RuntimeError(f"owner is already active: {owner_id}")
        generation = 1 if existing is None else existing.generation + 1
        self._owners[owner_id] = _OwnerRecord(generation, OwnerState.OPEN, set())
        return CallbackLease(owner_id, generation)

    def lease(self, owner_id: str) -> CallbackLease:
        record = self._owners.get(owner_id)
        if record is None or record.state is not OwnerState.OPEN:
            raise StaleCallbackError(f"owner is not open: {owner_id}")
        return CallbackLease(owner_id, record.generation)

    def assert_lease_current(self, lease: CallbackLease) -> None:
        record = self._owners.get(lease.owner_id)
        if (
            record is None
            or record.state is not OwnerState.OPEN
            or record.generation != lease.generation
        ):
            raise StaleCallbackError("callback lease is stale")

    def start(
        self,
        descriptor: AsyncOperationDescriptor,
        operation: OperationCallable[_T],
    ) -> AsyncOperationHandle[_T]:
        if descriptor.operation_id in self._handles:
            raise ValueError(f"duplicate operation_id: {descriptor.operation_id}")
        lease = self.lease(descriptor.owner_id)
        record = self._owners[descriptor.owner_id]
        capacity = self.policy.max_concurrency + self.policy.queue_capacity
        owned_pending = sum(1 for handle in self._handles.values() if not handle.done)
        if owned_pending >= capacity:
            raise QueueCapacityError("async operation queue capacity exceeded")
        if descriptor.governed_external and self.kill_switch.triggered:
            raise RuntimeError("Kodepoia kill switch is active")

        token = CancellationToken()
        handle: AsyncOperationHandle[_T] = AsyncOperationHandle(descriptor, token, lease)
        reporter = ProgressReporter(
            lease=lease,
            lease_validator=self.assert_lease_current,
            state_getter=lambda: handle.state,
            maximum=self.policy.max_progress_snapshots,
        )
        handle._bind_progress(reporter)

        task = asyncio.create_task(
            self._run(handle, operation),
            name=f"kodepoia:{descriptor.operation_id}",
        )
        handle._bind_task(task)
        record.tasks.add(task)
        self._handles[descriptor.operation_id] = handle

        def _forget(completed: asyncio.Task[Any]) -> None:
            owner = self._owners.get(descriptor.owner_id)
            if owner is not None:
                owner.tasks.discard(completed)

        task.add_done_callback(_forget)
        return handle

    async def _run(
        self,
        handle: AsyncOperationHandle[_T],
        operation: OperationCallable[_T],
    ) -> _T:
        descriptor = handle.descriptor
        try:
            try:
                async with asyncio.timeout(self.policy.queue_wait_timeout_seconds):
                    await self._semaphore.acquire()
            except TimeoutError as exc:
                if not handle.done:
                    handle._finish(OperationState.TIMED_OUT)
                raise OperationTimeoutError("operation timed out waiting for concurrency slot") from exc

            try:
                self.assert_lease_current(handle.lease)
                handle.token.raise_if_cancelled()
                if descriptor.governed_external and self.kill_switch.triggered:
                    handle.token.cancel()
                    raise asyncio.CancelledError
                handle.state = OperationState.RUNNING
                context = OperationContext(
                    descriptor,
                    handle.token,
                    handle._progress,  # type: ignore[arg-type]
                    self.kill_switch,
                )
                timeout = descriptor.timeout_seconds or self.policy.operation_timeout_seconds
                try:
                    async with asyncio.timeout(timeout):
                        value = await operation(context)
                        await context.checkpoint()
                except TimeoutError as exc:
                    handle.token.cancel()
                    if not handle.done:
                        handle._finish(OperationState.TIMED_OUT)
                    raise OperationTimeoutError(
                        f"operation exceeded timeout: {descriptor.operation_id}"
                    ) from exc
                if not handle.done:
                    handle._finish(OperationState.SUCCEEDED)
                return value
            finally:
                self._semaphore.release()
        except asyncio.CancelledError:
            handle.token.cancel()
            if not handle.done:
                handle._finish(OperationState.CANCELLED)
            raise
        except OperationTimeoutError:
            if not handle.done:
                handle._finish(OperationState.TIMED_OUT)
            raise
        except StaleCallbackError:
            if not handle.done:
                handle._finish(OperationState.CANCELLED)
            raise
        except Exception:
            if not handle.done:
                handle._finish(OperationState.FAILED)
            raise

    async def close_owner(self, owner_id: str) -> None:
        record = self._owners.get(owner_id)
        if record is None or record.state is OwnerState.CLOSED:
            return
        record.state = OwnerState.CLOSING
        record.generation += 1
        tasks = tuple(record.tasks)
        for handle in self._handles.values():
            if handle.descriptor.owner_id == owner_id and not handle.done:
                handle.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        record.tasks.clear()
        record.state = OwnerState.CLOSED

    async def shutdown(self) -> None:
        for owner_id in tuple(self._owners):
            await self.close_owner(owner_id)
        if self.active_count:
            raise RuntimeError("shutdown left orphan operations")


class UiThreadDispatcher:
    """Thread-safe bridge into one captured asyncio UI loop.

    Callbacks are synchronous by contract. Returning an awaitable is rejected so
    dispatcher usage cannot manufacture hidden lifetime-unowned tasks.
    """

    def __init__(
        self,
        runtime: AsyncOperationRuntime,
        framework: DesktopFramework,
    ) -> None:
        self.runtime = runtime
        self.binding = canonical_dispatcher_binding(framework)
        self._loop = asyncio.get_running_loop()
        self._thread_id = threading.get_ident()

    def assert_access(self) -> None:
        if threading.get_ident() != self._thread_id:
            raise UiThreadAffinityError("UI callback executed on the wrong thread")

    def post(
        self,
        lease: CallbackLease,
        callback: Callable[..., _T],
        *args: object,
    ) -> concurrent.futures.Future[_T]:
        future: concurrent.futures.Future[_T] = concurrent.futures.Future()

        def invoke() -> None:
            if future.cancelled():
                return
            try:
                self.runtime.assert_lease_current(lease)
                self.assert_access()
                value = callback(*args)
                if inspect.isawaitable(value):
                    raise TypeError("UI dispatcher callback must be synchronous")
                future.set_result(value)
            except BaseException as exc:
                future.set_exception(exc)

        self._loop.call_soon_threadsafe(invoke)
        return future
