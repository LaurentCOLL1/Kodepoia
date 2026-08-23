# R9.11 — Adversarial hardening + R9 integrated acceptance — Acceptance

## Decision

R9.11 implementation is **ACCEPTED** on exact head:

`e8e7e83c107bdb8bcb29882936720bc9eeb1c246`

Manual intervention: **CONDITIONAL NOT TRIGGERED**.

Integrated evidence, final documentation gates, PR #127 merge and final post-merge continuity normalization remain pending. R9 is therefore still **IN PROGRESS** at this document commit.

## Accepted base

- Fully normalized R9.10 `main`: `8cd01c5f5d1ae667602d2e13c1d86219d86748cf`.
- Dedicated branch: `r9/11-adversarial-integrated-acceptance`.
- Pull request: #127.
- Exact accepted R9.11 implementation head: `e8e7e83c107bdb8bcb29882936720bc9eeb1c246`.

No later implementation code is accepted unless R0 Repository Guard, full Python Core and KodeStudio UI Smoke are rerun on the replacement exact head and this acceptance record is deliberately superseded.

## Authoritative implementation gates

All required gates succeeded on exactly `e8e7e83c107bdb8bcb29882936720bc9eeb1c246`:

| Gate | Run | Result |
| --- | --- | --- |
| R0 Repository Guard | #1207 / `32658452681` | SUCCESS, Ubuntu + Windows |
| Python Core | #1181 / `32658452650` | SUCCESS, all 5 jobs |
| KodeStudio UI Smoke | #1148 / `32658452730` | SUCCESS |

Python Core Ubuntu evidence:

- compile: SUCCESS;
- R7 integrated acceptance: PASS;
- R8 integrated acceptance: PASS;
- pytest: **745 passed / 7 skipped / 46 warnings**;
- package build Ubuntu: SUCCESS;
- package build Windows: SUCCESS;
- Python Core Windows tests: SUCCESS;
- embedded Windows KodeStudio smoke: SUCCESS.

The accepted R9.10 Ubuntu baseline was `729 passed / 7 skipped / 46 warnings`; R9.11 therefore adds 16 passing tests without increasing the warning baseline.

## R9.11 additions accepted

The implementation head adds:

- `kodepoia.comfyui.acceptance` with a dedicated R9 phase-integration model rather than modifying frozen R7/R8 evidence models;
- `schemas/r9-integration-report-v1.schema.json`;
- R9 integrated report round-trip/schema/tamper/manual-state tests;
- mandatory R9.8 reviewed-local-evidence digest/byte-length binding in a passing R9 report;
- cross-subsystem adversarial seam tests;
- `R9_11_DESIGN.md` mapping the frozen R9.11 attack matrix to the full accepted regression suite.

No generation feature, ComfyUI wire route, GPU action, model/node requirement, output-promotion rule or user-project mutation path is added by R9.11.

## Adversarial result

R9.11 relies on two evidence layers.

### Full regression layer

The full Python Core suite re-executes the detailed adversarial tests accepted throughout R9.1–R9.10, including:

- strict loopback endpoint/redirect boundaries;
- malformed/oversized HTTP and WebSocket payload rejection;
- prompt/event/history correlation and terminal-state monotonicity;
- lost/ambiguous submission reconciliation without blind duplicate submit;
- unknown-node/graph-marker/connection-type/parameter injection rejection;
- stale capability and ambiguous/missing/invalid model resolution;
- workflow-catalog path/tamper rejection;
- production pack prompt/dimension/output/pixel budgets;
- cross-prompt output-reference rejection;
- output path traversal, corrupt bytes and hash/length mismatch before R8 promotion;
- R8 DERIVED lineage for successful generated outputs;
- targeted cancellation, cancel/complete race handling and restart recovery;
- `/free` active-run blocking and acknowledgement-only semantics;
- impossible/contradictory VRAM telemetry rejection;
- explicit ADMIT/DEFER/REJECT/UNKNOWN admission states;
- explicit Ollama unload authorization;
- OOM estimate monotonicity and terminal cleanup;
- run/capture/lifecycle/resource evidence tamper rejection.

### R9.11 cross-subsystem seam layer

The new R9.11 tests additionally prove:

- neither `ComfyUIClient` nor `ComfyService` exposes an arbitrary public request/process/install/download/graph-execution escape;
- the CLI parser rejects an arbitrary `--endpoint` option;
- the default façade endpoint remains fixed to `http://127.0.0.1:8188`, while LAN and `localhost` endpoints remain rejected by the frozen boundary;
- production requests carrying `graph`, `url`, `command`, `model_download` or `custom_node_install` fields are rejected before execution;
- R9.10 model selection remains the single governed `checkpoint` token mapping;
- cross-run output references still fail through the R9.6 identity guard;
- façade-level free-memory requests are bound to the bounded persisted known-run set and preserve `reclaimed_bytes = null`;
- known-run enumeration is deterministic at the configured bound and fails closed at bound + 1;
- VRAM reserve/headroom values cannot escape the accepted 0–65536 MiB façade bounds.

No gate was weakened to obtain this result.

## R9 integrated acceptance contract

The accepted `R9IntegrationReport` requires exactly R9.1 through R9.11 in order. Every subdivision binds:

- canonical `docs/roadmap/R9_<n>_ACCEPTANCE.md` path;
- SHA-256 of the canonical acceptance Git blob;
- exact acceptance byte length;
- exact accepted implementation head;
- explicit manual state and reason;
- derived manual satisfaction;
- optional reviewed manual-evidence digest/byte length.

Passing evidence cannot contain explicit or derived blockers. R9.11's accepted head must equal report `source_sha`.

R9.8 is additionally required to carry the already-reviewed local GPU evidence reference:

- SHA-256: `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`;
- byte length: **5744 bytes**.

Hosted repository validation does not pretend to possess that operator-local file. Instead it requires the canonical R9.8 acceptance Git blob to match its recorded hash/length and to explicitly contain the reviewed local evidence digest and byte length.

## Manual state

R9.11's frozen mode is CONDITIONAL. It resolves to **CONDITIONAL NOT TRIGGERED** because:

- R9.2, R9.5 and R9.9 inherited conditionals remain resolved as NOT TRIGGERED;
- R9.8 REQUIRED hardware-local acceptance is already SATISFIED by the reviewed evidence above;
- R9.10 manual mode is NONE;
- R9.11 changes no hardware-facing ComfyUI/GPU/node/model/output semantics that would invalidate R9.8 evidence;
- all newly added hostile cases execute with hosted deterministic fixtures or pure contracts and do not mutate a real user ComfyUI/GPU/Ollama environment.

Therefore no intervention is required from the operator for this R9.11 candidate. If a later fix changes an authoritative hardware-facing path, this determination must be revisited before phase completion.

## Integrated-evidence sequence

This document deliberately freezes the R9.11 implementation head before the canonical phase report is created.

Remaining sequence:

1. add `scripts/r9_integrated_acceptance.py` with the accepted R9.1–R9.11 implementation heads/manual states and Git-blob validation;
2. add the Linux Python Core hook after the existing R7/R8 verifiers;
3. while `docs/roadmap/R9_INTEGRATED_ACCEPTANCE.json` is absent, let the script print the exact canonical candidate;
4. check in that exact candidate and synchronize continuity;
5. rerun R0 Repository Guard, full Python Core and KodeStudio UI Smoke on one final exact documentation/evidence head;
6. require `R9 integrated acceptance: PASS`, `blockers=[]`, R7 PASS and R8 PASS;
7. merge PR #127 only after those final exact-head gates succeed;
8. perform a final continuity-only post-merge normalization with the same three gates;
9. only then mark R9 COMPLETE and authorize R10 planning/work.

## Result

R9.11 **implementation** is accepted on `e8e7e83c107bdb8bcb29882936720bc9eeb1c246`. R9 phase completion remains pending integrated evidence, final exact-head gates, merge and final continuity normalization.
