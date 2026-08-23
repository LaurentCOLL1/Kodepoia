# R9.2 Design — Typed HTTP/WebSocket client, health, queue/history + protocol state

## Status

Implementation candidate on `r9/2-comfy-client`, based on normalized R9.1 `main` `2d646a08412b18709b5a1d3aa0c9a4bfed30ea05`.

Frozen manual state: **CONDITIONAL**. The condition is not considered triggered while current upstream behavior required by R9.2 is established by official/current ComfyUI source/tests and deterministic loopback fixtures cover Kodepoia's accepted protocol surface.

## Scope

R9.2 adds the smallest fixed read/progress protocol client needed before workflow execution exists:

- GET `/system_stats`, `/features`, `/prompt`, `/queue`, `/history`, `/history/{prompt_id}`;
- bounded GET `/view` output retrieval from inert R9.1 output references;
- WebSocket `/ws?clientId=...` progress/event consumption;
- queue/history reconciliation independent of WebSocket availability;
- bounded reconnect/backoff/cancellation and operation budgets;
- deterministic protocol fixtures and fake loopback HTTP/WebSocket server;
- minimal `comfy-probe` diagnostic required by the frozen conditional manual gate.

R9.2 does **not** submit production prompts/workflows, mutate/delete queue entries, interrupt execution, invoke `/free`, inventory nodes/models, resolve model names, promote outputs to the R8 Vault, manage VRAM, or add KodeStudio ComfyUI UX.

## Fixed boundary

`ComfyUIClient` exposes no generic HTTP method/path or socket surface. Its public protocol methods are limited to:

- `system_stats()`;
- `features()`;
- `prompt_metadata()`;
- `queue()`;
- `history(prompt_id)`;
- `history_index()`;
- `retrieve_output(reference)`;
- `reconcile_prompt_state(prompt_id)`;
- `iter_events(client_id, ...)`;
- `probe()`.

All network access composes the accepted R9.1 `ComfyEndpoint`, therefore only explicit `127.0.0.1` or `::1`, explicit port, HTTP/HTTPS, and exact-origin redirects are accepted. Prompt IDs are percent-encoded before entering a path segment. Output metadata reaches `/view` only through encoded query parameters and accepted `output`/`temp` storage classes.

## HTTP transport

The internal transport uses Python's standard library and introduces no dependency or arbitrary request API. Connect/read timeouts and JSON/binary byte limits come from `ComfyTransportLimits`.

- declared `Content-Length` over budget is rejected before body consumption;
- bodies are read at most `limit + 1` bytes;
- redirect/error bodies are discarded only within a fixed 64 KiB bound;
- redirects are limited to three and validated against the exact accepted origin;
- non-2xx responses, malformed JSON and non-object JSON fail closed;
- connection/timeouts surface `ComfyUnavailableError`, never success.

## WebSocket transport

R9.2 implements only the RFC 6455 subset needed by the current local ComfyUI server: HTTP upgrade, text/binary messages, fragmentation, ping/pong and close. Client control frames are masked; server frames must be unmasked. Extensions/RSV bits are rejected.

The announced WebSocket payload length is checked against `max_websocket_frame_bytes` **before** reading the payload. Fragmented message aggregate size is also bounded. The handshake reads exactly through `\r\n\r\n` so a first frame coalesced with the HTTP 101 response remains unread for the frame parser.

Reconnect count is bounded (`0..8`), backoff entries are bounded, cancellation is cooperative, and the entire iterator remains under `total_timeout_seconds`.

## Event normalization and authority

Normalized events include current ComfyUI execution/status names where present: `status`, `execution_start`, `execution_cached`, `executing`, `progress`, `executed`, `execution_error`, `execution_interrupted`, `execution_success`, `progress_state`, and `progress_text`. Unknown bounded event types remain explicit `UNKNOWN` rather than being reinterpreted.

Prompt-scoped events validate prompt ID and impossible terminal regressions. Binary preview frames are bounded but are not interpreted as execution-state events.

**WebSocket completion is never the final source of truth.** `reconcile_prompt_state()` checks queue running/pending state and then persisted history. This is deliberate because current ComfyUI execution/history sequencing and a recent upstream WebSocket-stall report demonstrate that WebSocket delivery can be absent or precede durable history availability while HTTP remains functional.

## Probe evidence

`python -m kodepoia.cli comfy-probe` writes a versioned `kodepoia.comfy-protocol-probe` envelope under the current workspace only. Absolute paths, traversal and resolved parent escape are rejected. Writing is atomic through a workspace-local temporary file.

Transient connection failures become explicit `UNAVAILABLE` capability states with null digests and `ready=false`. Protocol-shape errors still fail closed rather than being downgraded to availability failures.

Schema: `schemas/comfy-protocol-probe-v1.schema.json`.

## Deterministic fixture

Fixture: `tests/fixtures/comfyui/r9_2_protocol.json`.

- fixture version: `1`;
- SHA-256: `1b5b6947e6af1440f59ffc1d6a9d3ed3502fdc057e1bd08a5680300cb42fd656`;
- covers system/features/prompt metadata, running/pending queue tuples, success/error history, output retrieval metadata and representative WebSocket events.

The fake server is loopback-only and is started by tests. It never needs a real ComfyUI install, model, GPU, custom node, external network service or user credential.

## Compatibility evidence reviewed

Current upstream ComfyUI source/tests were reviewed during R9.2 implementation. They continue to use `/ws?clientId=...`, `/prompt`, `/view`, `/history/{prompt_id}`, `/queue`, `/history`, system statistics and execution events. Newer job-oriented API surfaces also exist; R9.2 does not depend on them and does not treat them as architecture authority.

An August 2026 upstream report documents a long-running ComfyUI process where `/prompt`, `/queue` and `/history/{prompt_id}` remained functional while post-connect WebSocket events stopped arriving. A separate upstream report documents `execution_success` preceding persistence into prompt history. Both cases reinforce the frozen R9.2 rule that pollable queue/history state remains authoritative.

## Test strategy

R9.2 tests cover:

- fixed health/system/features/prompt/queue/history/output operations;
- queue/history reconciliation without manufactured completion;
- prompt-ID route encoding;
- same-origin redirect and cross-origin rejection;
- HTTP 4xx/5xx, malformed JSON, timeout and oversized body handling;
- explicit `UNAVAILABLE` probe states;
- normalized event parsing, progress bounds, prompt mismatch and terminal regression rejection;
- WebSocket reconnect after drop, binary-preview skip, bounded retry and cancellation;
- oversized announced WebSocket frame rejection before payload read;
- absence of a public arbitrary request surface;
- fixture digest stability;
- probe schema validation and workspace-confined output.

## Manual intervention decision

Frozen state remains **CONDITIONAL**.

The condition is triggered only if exact-head CI reveals behavior that deterministic fixtures cannot establish, implementation requires undocumented/drift-sensitive upstream behavior, or current official source/tests contradict the protocol assumptions above. If triggered, stop before merge and run the exact frozen probe command on the candidate head against an already-running loopback ComfyUI. Do not install/update models or custom nodes and do not expose ComfyUI to LAN/Internet.

If all required behavior is proven by deterministic loopback fixtures plus current upstream contract evidence and no drift-sensitive dependency is introduced, the condition resolves to **CONDITIONAL NOT TRIGGERED**.

## Acceptance

R9.2 implementation is accepted only when R0 Repository Guard, full Python Core and KodeStudio UI Smoke are all SUCCESS on the same exact implementation head. Then `R9_2_ACCEPTANCE.md` and continuity pin that exact evidence, and the final documentation head is re-gated before merge.
