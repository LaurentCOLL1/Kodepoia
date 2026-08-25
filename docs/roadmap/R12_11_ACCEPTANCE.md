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

- Python asyncio documents that task cancellation raises `CancelledError` at the next opportunity and that caught cancellation should generally be re-propagated after cleanup; structured concurrency primitives use cancellation internally;
- Windows App SDK `DispatcherQueue` serializes tasks on its owning thread and permits background threads to enqueue work on the UI-affine thread;
- framework-specific dispatcher names are identity/mapping metadata only in R12.11; R12.11 does not claim new native runtime behavior beyond the already accepted R12.5–R12.9 adapter evidence.

Official references:

- https://docs.python.org/3/library/asyncio-task.html
- https://learn.microsoft.com/windows/apps/develop/dispatcherqueue
- https://docs.avaloniaui.net/docs/guides/development-guides/accessing-the-ui-thread
- https://doc.qt.io/qt-6/qobject.html#thread-affinity
- https://docs.rs/tauri/latest/tauri/struct.AppHandle.html#method.run_on_main_thread

## Evidence state

Base normalized `main`: `25b3e94b58d6ac08511b2510a98148354f5144f2`.
Branch: `r12/11-async-concurrency`.
Manual state: **NONE**.

Accepted implementation candidate: `39461205919b4fbb01354ea39af9a58638cfcd8c`.

Exact-head gates on the accepted candidate:

- R0 Repository Guard #1550 / run `32823338030` — SUCCESS;
- Python Core #1524 / run `32823338014` — SUCCESS, including Linux and Windows test jobs;
- KodeStudio UI Smoke #1491 / run `32823337990` — SUCCESS;
- R12 WPF Acceptance #49 / run `32823337991` — SUCCESS;
- R12 WinUI3 Acceptance #39 / run `32823338016` — SUCCESS;
- R12 Avalonia Acceptance #35 / run `32823338024` — SUCCESS;
- R12 Qt6 Acceptance #30 / run `32823337983` — SUCCESS;
- R12 Tauri2 Acceptance #21 / run `32823338040` — SUCCESS.

The focused suite `tests/test_desktop_r12_11.py` is exercised by Python Core. No manual evidence is required or triggered for R12.11.

Evidence-recording documentation bytes change after the accepted candidate. The resulting final documentation HEAD must therefore pass a fresh exact-head standard gate set plus desktop adapter regressions before merge.

## Merge / normalization rule

Freeze the final documentation head and require exact-head gates. Merge PR #207 with `expected_head_sha`, perform exactly one continuity-only post-merge normalization, gate that exact head and merge it. R12.12 remains forbidden until R12.11 normalization merges.
