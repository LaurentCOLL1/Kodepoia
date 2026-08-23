# R9.2 Acceptance — Typed ComfyUI HTTP/WebSocket client and reconciliation

## Decision

R9.2 implementation is **ACCEPTED** on exact head:

`15186ced206f05d8baf764738615e6625aa6d459`

The frozen manual state resolves to **CONDITIONAL NOT TRIGGERED**.

## Base

- normalized R9.1 `main`: `2d646a08412b18709b5a1d3aa0c9a4bfed30ea05`;
- implementation branch: `r9/2-comfy-client`;
- PR: #107.

## Exact-head CI evidence

All required workflows are SUCCESS on `15186ced206f05d8baf764738615e6625aa6d459`:

- R0 Repository Guard #1114 / run `32625248672`: **SUCCESS**;
- Python Core #1088 / run `32625248645`: **SUCCESS**;
- KodeStudio UI Smoke #1055 / run `32625248725`: **SUCCESS**.

Python Core detail:

- Ubuntu Python job `97159491573`: `626 passed / 6 skipped / 46 warnings`; R7 integrated acceptance PASS; R8 integrated acceptance PASS;
- Windows Python job `97159491662`: `623 passed / 9 skipped / 46 warnings`;
- Ubuntu package-build job `97159491647`: SUCCESS;
- Windows package-build job `97159491665`: SUCCESS;
- integrated Windows KodeStudio smoke job `97159491648`: SUCCESS.

The warning baseline remains 46; R9.2 introduced no additional pytest warnings.

## Accepted protocol/security surface

The accepted R9.2 implementation adds:

- a typed fixed loopback-only HTTP client for `/system_stats`, `/features`, GET `/prompt`, `/queue`, `/history`, `/history/{prompt_id}` and bounded `/view` retrieval;
- a minimal bounded WebSocket client for `/ws?clientId=...` with handshake validation, masking rules, text/binary frames, fragmentation, ping/pong, close, bounded reconnect/backoff and cooperative cancellation;
- normalized current execution/status events while preserving unknown bounded event types as explicit `UNKNOWN`;
- prompt-scoped event ordering checks without treating WebSocket delivery as durable completion authority;
- queue/history reconciliation as the pollable source of final execution state;
- exact-origin redirect validation inherited from R9.1, percent-encoded prompt path segments and encoded `/view` query values;
- response/frame size checks before payload consumption where the protocol exposes a declared size;
- a deterministic loopback HTTP/WebSocket test server and pinned protocol fixture;
- a strict versioned `kodepoia.comfy-protocol-probe` schema and a narrow workspace-confined `comfy-probe` diagnostic.

R9.2 exposes no public generic HTTP route/method surface and adds no arbitrary socket/process/model/GPU capability.

## Explicitly deferred

R9.2 does not add:

- production prompt/workflow submission;
- queue deletion/reordering mutation;
- execution interruption or `/free`;
- node/model inventory or model resolution;
- generated-output promotion into the R8 Vault/AssetPipeline;
- VRAM scheduling/telemetry or Ollama coexistence;
- KodeStudio ComfyUI UX.

These remain owned by later frozen R9 subdivisions.

## Deterministic fixture evidence

`tests/fixtures/comfyui/r9_2_protocol.json`:

- fixture version: `1`;
- canonical checkout line ending: LF, pinned by `.gitattributes`;
- SHA-256: `1b5b6947e6af1440f59ffc1d6a9d3ed3502fdc057e1bd08a5680300cb42fd656`.

The fixture plus fake loopback server cover health/capability responses, running/pending queue tuples, success/error history, output metadata and representative WebSocket execution events without a real ComfyUI install, model, GPU, custom node or external network dependency.

## Rejected precursor

First candidate `9b9a79f69ef7c304bd743b74bf0379f5d3688588` is **NOT ACCEPTED**.

- R0 #1113 and UI Smoke #1054 succeeded;
- Python Core #1087 failed only on Windows in `test_fixture_digest_is_stable`;
- Ubuntu was otherwise fully green with `626 passed / 6 skipped / 46 warnings`;
- Windows had `622 passed / 9 skipped / 46 warnings` plus the single fixture-byte digest failure;
- root cause: Git checkout line-ending normalization changed the JSON fixture from LF to CRLF on Windows, producing a different raw-byte SHA despite identical logical JSON.

Correction `15186ced...` pins only the deterministic ComfyUI protocol fixture family to `text eol=lf` in `.gitattributes`. No production protocol safeguard or assertion was weakened.

## Manual conditional decision

Frozen R9.2 manual state: **CONDITIONAL**.

Final resolution: **CONDITIONAL NOT TRIGGERED**.

Reason:

1. current upstream ComfyUI source/tests establish the fixed routes and WebSocket client pattern required by R9.2;
2. current upstream execution code/tests establish the execution event families used by the normalizer;
3. deterministic loopback fixtures validate Kodepoia's HTTP/WebSocket parsing, timeout, size, redirect, reconnect, cancellation, malformed-input and reconciliation behavior on Ubuntu and Windows;
4. upstream reports of WebSocket delivery stalls and execution-success/history timing gaps are handled by design: queue/history polling remains authoritative and WebSocket is telemetry, not durable completion truth;
5. no R9.2 acceptance property depends on GPU/VRAM behavior, installed models, custom nodes or a specific user-local ComfyUI deployment.

Therefore the frozen real-local `comfy-probe` command is not required for R9.2 acceptance. No user intervention is required.

## Final documentation gate

This acceptance file and continuity synchronization move the branch head. The resulting final documentation head must again pass R0 Repository Guard, full Python Core and KodeStudio UI Smoke on that exact SHA before PR #107 may be merged.
