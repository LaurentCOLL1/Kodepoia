# R9.7 — Cancellation, interruption, crash recovery + free-memory semantics

Status: implementation candidate; exact-head acceptance pending.

## Scope

R9.7 adds only bounded lifecycle operations around the accepted R9.2–R9.6 ComfyUI stack. It does not add VRAM admission policy, process termination, GPU reset, driver/runtime control, arbitrary HTTP routing, or model/custom-node installation.

## Cancellation authority

`ComfyLifecycleService.cancel()` first loads the canonical R9.5 run manifest, verifies that the client origin equals the persisted capability endpoint, and reconciles queue/history immediately before any cancellation side effect.

For current ComfyUI, R9.7 prefers the atomic and idempotent `POST /api/jobs/{job_id}/cancel` operation. The response must be exactly a boolean `cancelled` field. A terminal or unknown job remains a no-op and is reconciled rather than fabricated as `CANCELLED`.

For an older server that returns 404 for the job-cancel API, only a *pending* prompt may use legacy `/queue` deletion with the exact persisted prompt ID. Legacy `/interrupt` is intentionally never used: upstream legacy `/interrupt` is global and ignores prompt correlation, so using it would risk interrupting another job. A running job on such a server is therefore explicit `UNSUPPORTED`/blocked rather than globally interrupted.

No caller supplies an arbitrary route, HTTP method, host, prompt ID, executable, argv, cwd, environment, or filesystem location to these internal side-effect paths.

## Lifecycle audit

`ComfyLifecycleAuditStore` persists one root-confined audit per logical run. Events form an append-only SHA-256 chain over sequence, action, outcome, observed run state, request/response evidence digests, and previous-event digest. The whole audit is separately digest-sealed and validated on load.

Actions are typed as `NONE`, `JOB_CANCEL`, `QUEUE_DELETE`, `TARGETED_INTERRUPT`, `RECOVER`, and `FREE_REQUEST`; outcomes distinguish `NOOP`, `DISPATCHED`, `RECONCILED`, `AMBIGUOUS`, `BLOCKED`, and `UNSUPPORTED`.

The strict adjunct payload schema is `schemas/comfy-lifecycle-audit-payload-v1.schema.json`. Frozen R9.1/R9.5 envelopes are unchanged.

## Restart recovery and orphan handling

`recover()` uses the accepted R9.5 append-only run history. If the mutable current pointer is damaged, `ComfyRunStore.recover()` reconstructs it from validated immutable revisions. Non-terminal state is then reconciled through the accepted queue/history authority. Missing or unavailable evidence never manufactures a terminal result.

If a prompt is absent from both queue and history, R9.7 preserves the last evidence-backed state/UNKNOWN semantics; disappearance alone is not treated as cancellation or failure.

## Cleanup and `/free`

`request_free_memory()` is allowed only when every explicitly supplied Kodepoia run is terminal. Active known runs block cleanup. The request is fixed to `/free` and records the exact `unload_models` / `free_memory` request digest.

HTTP acknowledgement is not interpreted as reclaimed VRAM. R9.7 samples `system_stats` before and after the request and persists only those evidence digests. `ComfyFreeMemoryEvidence.reclaimed_bytes` is deliberately always `None` in R9.7. Authoritative byte-level VRAM telemetry belongs to R9.8.

`cleanup_terminal_run()` gives failure/OOM/cancel paths one bounded ordering: prove terminal run -> request unload/free -> re-read system evidence -> append lifecycle audit. If acknowledgement or re-read is unavailable/ambiguous, the audit records `AMBIGUOUS`; no fabricated release is emitted.

## Deterministic acceptance coverage

`tests/test_comfyui_r9_7.py` covers:

- atomic pending cancellation;
- atomic running cancellation without global interrupt;
- safe legacy pending queue deletion;
- legacy running cancellation blocked rather than global interrupt;
- cancellation/terminal race;
- disappeared/unknown prompt without fabricated terminal state;
- corrupted current-pointer restart recovery;
- `/free` acknowledgement without fabricated reclaimed bytes;
- cleanup blocked for active runs;
- FAILED/OOM-style terminal cleanup ordering;
- strict schema validation and audit tamper rejection.

## Security and architecture invariants

R9.7 preserves loopback-only endpoint confinement, R9.5 queue/history terminal authority, operation budgets, immutable run history, and exact-head evidence discipline. It introduces no process kill, driver mutation, arbitrary socket route, arbitrary filesystem path, model download, custom-node installation, or R8 bypass.

## Rollback

Removing the lifecycle module/schema/tests and their package exports restores the normalized R9.6 tree. Runtime audit files are evidence only and can remain; no source asset or R8 Vault revision is mutated by rollback.

## Manual intervention

**NONE.** All R9.7 acceptance properties are deterministic protocol/state/audit invariants and are covered by hosted fixtures on Ubuntu/Windows. Real GPU-memory behavior is intentionally deferred to the REQUIRED R9.8 local gate.
