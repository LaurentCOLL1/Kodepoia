# R9.7 Acceptance — Cancellation, interruption, crash recovery + free-memory semantics

Status: **IMPLEMENTATION ACCEPTED**. Final documentation/continuity exact-head gates remain required before merge.

## Exact implementation head

`20cc4bbc93e547fac9fee28d7be44268358d29e4`

Base normalized R9.6 `main`: `c94bca7c71ad9fea1782130eecd2079dbd710570`.

## Required hosted gates on the exact implementation head

- R0 Repository Guard #1154 / run `32631945349`: **SUCCESS**.
- Python Core #1128 / run `32631945259`: **SUCCESS**, all 5 jobs green.
  - Ubuntu pytest: **680 passed / 6 skipped / 46 warnings**.
  - Windows pytest: SUCCESS.
  - Ubuntu package build: SUCCESS.
  - Windows package build: SUCCESS.
  - integrated KodeStudio Windows smoke job: SUCCESS.
  - R7 integrated acceptance: PASS.
  - R8 integrated acceptance: PASS.
- KodeStudio UI Smoke #1095 / run `32631945367`: **SUCCESS**.

## Accepted properties

1. Current ComfyUI targeted cancellation uses the atomic/idempotent job-cancel endpoint bound to the exact persisted prompt ID.
2. Cancellation reconciles queue/history immediately before the side effect and again afterwards; a terminal race becomes a no-op/reconciled terminal state rather than a destructive late cancel.
3. Legacy fallback is safe: pending prompts may use exact-ID `/queue` deletion, while a running prompt on a server without targeted job cancellation is explicit `UNSUPPORTED` and **never** falls back to global `/interrupt`.
4. Unknown/disappeared prompts do not fabricate `CANCELLED` or `FAILED`.
5. Restart recovery can reconstruct a damaged mutable current pointer from the accepted append-only R9.5 run history and then reconcile service state.
6. Lifecycle actions/outcomes are stored in a root-confined, tamper-evident append-only SHA-256 audit chain with a strict adjunct schema.
7. `/free` is a bounded cleanup request only. HTTP acknowledgement never becomes a claimed reclaimed-byte measurement; `reclaimed_bytes` remains `None` in R9.7.
8. Cleanup is blocked while an explicitly known Kodepoia run is non-terminal. FAILED/OOM-style terminal cleanup follows terminal proof -> unload/free request -> system re-read -> audit.
9. Ambiguous/unavailable cleanup evidence remains explicit and does not manufacture successful memory release.
10. R9.7 adds no process kill, global interrupt, GPU reset, driver/runtime mutation, arbitrary HTTP route, arbitrary host, model download, custom-node installation, or R8 governance bypass.

## Deterministic acceptance coverage

`tests/test_comfyui_r9_7.py` covers atomic pending/running cancellation, safe legacy pending deletion, legacy running block, terminal cancellation race, unknown prompt handling, damaged-pointer recovery, conservative `/free`, active-run cleanup block, FAILED/OOM-style cleanup ordering, schema validation and audit tamper rejection.

Strict adjunct schema: `schemas/comfy-lifecycle-audit-payload-v1.schema.json`.

## Manual intervention

**NONE**.

All frozen R9.7 acceptance properties are deterministic protocol/state/audit invariants covered by hosted Ubuntu/Windows CI. Real GPU VRAM allocation/release/backend behavior is deliberately not claimed here; that authority belongs to the REQUIRED R9.8 local GPU gate.

## Merge discipline

Before PR #117 may merge, this acceptance document and synchronized continuity must be committed, then R0 Repository Guard, full Python Core and KodeStudio UI Smoke must all succeed on that **same final documentation head**. Merge must use exact-head locking, followed by a continuity-only post-merge normalization before R9.8 begins.
