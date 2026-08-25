# R12.11 — Acceptance

## Scope

Framework-neutral async/concurrency contracts with bounded capacity, cancellation propagation, deterministic progress, explicit UI-thread affinity, owner-scoped lifecycle cleanup and KillSwitch integration for governed external desktop work.

Manual intervention: **NONE**.

## Required acceptance

- async policy and operation descriptors are bounded, canonically serializable and digest-stable;
- operation identity is unique within one runtime and owner identity uses stable bounded identifiers;
- concurrency is semaphore-bounded and total running + queued work is capacity-bounded;
- queue wait and operation execution have independent bounded timeouts with typed terminal state;
- `CancelledError` is propagated after terminal-state cleanup rather than swallowed;
- cancellation is idempotent, but terminal completion is single-assignment and double completion fails closed;
- BUILD/TEST/PACKAGE operation checkpoints bridge the existing process-wide KillSwitch state;
- progress sequence is deterministic, monotonic and history-bounded;
- owner closure invalidates callback leases before cancelling and awaiting every owned task;
- stale progress/UI callbacks after owner closure or generation replacement fail closed;
- no operation task can remain owned after `close_owner()`/`shutdown()` completes;
- UI callbacks execute only on the captured UI loop/thread and async callbacks are rejected to avoid hidden unowned tasks;
- WPF, WinUI 3, Avalonia, Qt 6 and Tauri v2 have explicit framework binding identities without serializing native framework objects into shared contracts;
- focused R12.11 tests plus exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke succeed; existing desktop adapter workflows remain regression evidence.

## Web-researched implementation basis

- Python 3.12 asyncio documents that task cancellation raises `CancelledError` at the next opportunity and that caught cancellation should generally be re-propagated after cleanup; `asyncio.timeout()` uses cancellation internally;
- Windows App SDK `DispatcherQueue` is explicitly the mechanism for serial work on a thread and for background threads to enqueue code onto a thread with UI object affinity;
- framework-specific dispatcher names are identity/mapping metadata only in R12.11; R12.11 does not claim new native runtime behavior beyond the already accepted R12.5–R12.9 adapter evidence.

Official references:

- https://docs.python.org/3.12/library/asyncio-task.html
- https://learn.microsoft.com/windows/apps/develop/dispatcherqueue
- https://docs.avaloniaui.net/docs/guides/development-guides/accessing-the-ui-thread
- https://doc.qt.io/qt-6/qobject.html#thread-affinity
- https://docs.rs/tauri/latest/tauri/struct.AppHandle.html#method.run_on_main_thread

## Evidence state

Base normalized `main`: `25b3e94b58d6ac08511b2510a98148354f5144f2`.
Branch: `r12/11-async-concurrency`.
Manual state: **NONE**.

Exact implementation SHA and workflow run IDs are **PENDING** until the branch is frozen and independently gated.

## Merge / normalization rule

Freeze one immutable implementation head and require exact-head gates. Record accepted run IDs here and in continuity, then re-gate the resulting final documentation head because bytes changed. Merge with `expected_head_sha`, perform exactly one continuity-only post-merge normalization, gate that exact head and merge it. R12.12 remains forbidden until R12.11 normalization merges.
