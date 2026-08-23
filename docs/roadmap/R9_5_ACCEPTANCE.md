# R9.5 — Acceptance

## Decision

**IMPLEMENTATION ACCEPTED** on exact head `525a4c48ae0ff714fe4b3ee7bca34b2e8c62c112`.

Manual gate: **CONDITIONAL NOT TRIGGERED**.

R9.5 is accepted at implementation level only. PR #113 must still pass the required exact-head documentation/continuity gates before merge, followed by a continuity-only post-merge normalization before R9.6 may start.

## Accepted base

- Normalized R9.4 `main`: `920267d9096d340e50379f28c0f9506b9347f9f0`.
- Implementation branch: `r9/5-execution-engine`.
- Exact accepted implementation head: `525a4c48ae0ff714fe4b3ee7bca34b2e8c62c112`.

## Exact-head CI evidence

- R0 Repository Guard #1142 / run `32629125994`: **SUCCESS**.
- Python Core #1116 / run `32629126032`: **SUCCESS**, 5/5 jobs.
  - Ubuntu core tests: `654 passed / 6 skipped / 46 warnings`.
  - Windows core tests: SUCCESS.
  - Package build Ubuntu: SUCCESS.
  - Package build Windows: SUCCESS.
  - Integrated KodeStudio UI job inside Python Core: SUCCESS.
  - R7 integrated acceptance verifier: PASS.
  - R8 integrated acceptance verifier: PASS.
- KodeStudio UI Smoke #1083 / run `32629125952`: **SUCCESS**.

## Deterministic fixture

- Fixture: `tests/fixtures/comfyui/r9_5_execution.json`.
- Version: `1`.
- SHA-256: `549eab22a20f34ad367baf8f46d5c1a5166cd9fb8cbb90fdb983b9bd1129d50a`.
- Exact byte length: `542`.
- The fixture is inert local protocol evidence only; it does not execute a model, install a custom node, download content or require a GPU.

## Accepted implementation

R9.5 adds the bounded execution layer over the already accepted R9.2–R9.4 foundations:

- `ComfyUIClient.submit_prompt()` exposes only the fixed local `POST /prompt` route and refuses redirects for the side-effecting request.
- Caller-generated `run_id`, `prompt_id` and `client_id` correlation is persisted before the POST.
- A logical run permits **exactly one POST attempt**. The durable outcome is one of `NOT_ATTEMPTED`, `ATTEMPTING`, `ACCEPTED`, `AMBIGUOUS` or `RECOVERED`.
- A response loss after a possibly side-effecting POST never causes automatic resubmission. Only bounded idempotent queue/history reads are allowed until the exact prompt is recovered or the state remains explicitly ambiguous.
- Repeating `submit()` after an unresolved ambiguous POST still cannot produce a second POST.
- WebSocket events are telemetry/progress only. Progress is monotonic locally and a WebSocket success/error/interruption message is not terminal authority.
- Queue plus prompt-specific history are the reconciliation authority. Contradictory active-queue/terminal-history evidence fails closed.
- Terminal history must match the persisted prompt digest and Kodepoia correlation (`run_id`, workflow definition ID, workflow-instance digest).
- `SUCCEEDED` additionally requires every explicitly required output-node reference to be present in reconciled history.
- The validated R9.3 capability endpoint is bound to the exact `ComfyUIClient` origin at preparation and is rechecked for submission, polling/waiting and WebSocket observation. A manifest cannot be resumed against a different ComfyUI origin.
- `ComfyRunManifest` records explicit workflow, capability/environment, model-resolution, parameters, inputs, seeds, submission, queue/history, progress and output-reference evidence instead of only opaque digests.
- Frozen R9.1 `comfy-run-manifest-v1` root envelope remains unchanged; strict R9.5 payload validation is separate in `schemas/comfy-run-manifest-payload-v1.schema.json`.
- `ComfyRunStore` keeps immutable digest-named revisions linked by `previous_manifest_digest_sha256`, plus an atomic current pointer. The immutable chain can recover a missing/corrupt current pointer and rejects symlinks, gaps, conflicting bytes and digest tampering.
- Poll/reconciliation attempts, intervals and elapsed time are explicitly bounded. Pre-submit cooperative cancellation can stop a prepared run without network side effects; remote interruption remains deferred to R9.7.

## Adversarial acceptance coverage

The R9.5 tests establish at least the following properties on the accepted head:

1. prepared manifests carry explicit parameter/input/seed/model/environment evidence and validate against the strict payload schema;
2. successful execution can complete through polling/history without relying on WebSocket delivery;
3. a lost POST response after server-side acceptance is recovered from the exact prompt ID with one and only one POST;
4. an invisible ambiguous POST remains explicit and a second `submit()` call still does not resubmit;
5. WebSocket progress is monotonic and `execution_success` alone cannot make a run terminal;
6. mismatched stored prompt or Kodepoia correlation in terminal history fails closed;
7. success with a missing required output reference fails closed;
8. the manifest revision chain is append-only and can rebuild a corrupt current pointer;
9. manifest tampering is rejected while immutable revision evidence remains recoverable;
10. execution against an origin different from the validated capability snapshot is rejected.

## Rejected precursor

Head `4d0a5e0f66603387893d1633ba283c0e5d5d5078` was **not accepted**.

- R0 Repository Guard #1140: SUCCESS.
- KodeStudio UI Smoke #1081: SUCCESS.
- Python Core #1114 / run `32628835669`: FAILURE.
- Ubuntu result: `652 passed / 2 failed / 6 skipped / 46 warnings`.

The two failures were deliberately not bypassed:

1. **Production defect:** an R9.4 workflow validated against one ComfyUI capability endpoint could be prepared by a service pointing to another accepted loopback origin. The production fix now binds snapshot and persisted manifest endpoints to the exact execution-client origin across preparation, submission and reconciliation.
2. **Fixture assertion defect:** the revision-chain test used `zip(..., strict=True)` on an `N`-element sequence and its `N-1` tail, which necessarily raises. The assertion was corrected to compare adjacent pairs without changing production behavior or weakening any guard.

## Conditional manual gate resolution

The frozen R9.5 gate becomes **CONDITIONAL NOT TRIGGERED**.

Reason:

- deterministic loopback tests execute the required submit/recovery/duplicate-prevention/history/output/progress/restart properties on hosted Ubuntu and Windows;
- current ComfyUI behavior supports caller-supplied prompt IDs in prompt submission and retains prompt IDs in queue/history lifecycle evidence;
- current upstream evidence also shows why WebSocket completion cannot be authoritative: WebSocket event delivery can stall while HTTP/history continue, and `execution_success` may precede durable history/output availability;
- therefore no acceptance property depends on a GPU, a production workflow, a real checkpoint/custom node, a user-specific ComfyUI installation or a privileged local environment.

Upstream evidence reviewed on 23 August 2026:

- Comfy-Org/ComfyUI issue #15240 — WebSocket delivery can stall while prompts execute and history reports success;
- Comfy-Org/ComfyUI issue #11540 — `execution_success` may precede output persistence in history;
- Comfy-Org/ComfyUI RFC #15341 — integrations currently rely on history polling and/or client WebSocket interpretation for execution lifecycle;
- current ComfyUI `execution.py` — success event emission precedes construction of the final history result.

No local/manual R9.5 execution is required.

## Merge rule

Do not merge PR #113 until R0 Repository Guard, full Python Core and KodeStudio UI Smoke all succeed on the same exact final documentation/continuity head. After merge, perform and gate a continuity-only normalization before starting R9.6.
