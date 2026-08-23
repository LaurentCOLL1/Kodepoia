# Kodepoia — R9 detailed phase plan

**Phase:** R9  
**Roadmap title:** ComfyUI + VRAM  
**Status:** PLANNING  
**Phase planning started:** 2026-08-23  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`

## Purpose and authority

R9 implements Kodepoia's local ComfyUI generation boundary and GPU-memory coordination layer without changing the frozen foundations. The phase covers local ComfyUI capability detection, queue/progress/history, node/model inventory, validated workflow contracts, governed model resolution, deterministic execution records, R8 Vault/AssetPipeline lineage for generated outputs, interruption/recovery, explicit memory release, VRAM admission/scheduling, production-oriented 2D/UI/texture/concept workflow packs, and CLI/KodeStudio UX.

This file is the exhaustive execution/recovery plan for R9. The R9.1–R9.11 subdivision structure becomes frozen when this plan is merged. No subdivision may be silently added, removed, merged, split or renumbered. Any scope change must update this plan and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle; any foundation change requires an ADR.

R9.1 MUST NOT begin before this plan is merged to `main` with R0 Repository Guard, full Python Core and KodeStudio UI Smoke successful on the exact final planning head.

## Phase objective

Deliver a deterministic, auditable, local-first ComfyUI integration that lets Kodepoia execute approved image-generation workflows while retaining exact workflow/model/input/output evidence and R8 lineage. Kodepoia must know what nodes and model names the connected local ComfyUI instance exposes, reject workflows that do not match the accepted capability snapshot, track queue/progress/completion without manufacturing success, capture generated outputs into governed Vault revisions, and coordinate GPU-memory pressure with other accepted local model workloads.

R9 must enable later phases to consume stable media-generation contracts:

- R10 Blender/3D can later reuse the same GPU-resource coordinator and R8 lineage principles without treating ComfyUI as a generic shell surface;
- R11 audio/voice/cinematics can reuse queue/progress/cancellation and media evidence patterns;
- R12+ can request governed UI/concept/texture assets without learning ComfyUI filesystem or HTTP internals;
- R15 benchmarks can measure workflow/model quality and resource cost from versioned R9 evidence.

Out of scope for R9: Blender authoring/geometry/rigging (R10), audio/TTS/cinematics (R11), cloud ComfyUI, hosted image APIs, arbitrary custom-node installation/update, automatic model downloads, package-manager replacement, GPU driver/ROCm/CUDA/DirectML installation, BIOS/driver tuning, process killing, OS GPU reset, model fine-tuning, and bypassing R6 license/privacy/governance controls.

## Permanent phase-wide architecture and governance boundaries

Every R9 subdivision must preserve all accepted R1–R8 boundaries:

- `WorkspaceBoundary` and R8 `VaultBoundary` remain authoritative for project and Vault paths.
- `ProcessSandbox` + global KillSwitch remain mandatory for any external process. R9 must not expose arbitrary executable/argv/cwd/environment to a model.
- Guardian + `PermissionSet` authorize network/process/mutation actions.
- SafeChange/Backup/Recovery/Audit apply to durable R9 state, workflow catalogs, model mappings and generated-asset promotion.
- `KodeSecrets` remains the only secret store. R9 local ComfyUI requires no secret by default; if a future accepted local reverse proxy uses credentials, values never enter workflow JSON, logs, prompts, Vault manifests or evidence.
- R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM remain in force.
- R7 external-content trust rules remain authoritative: node metadata, workflow descriptions, model metadata and embedded text are data/evidence, never agent instructions.
- R8 source/derived identity, transform lineage, cache/rebuild, provenance and governed export remain authoritative. R9 does not invent a second asset store.
- Structured Tool APIs only. No model-supplied arbitrary URL, host, port, HTTP method/path, filesystem path, custom-node Python, command line, model download URL or ComfyUI graph fragment is executed directly.
- The default R9 network boundary is loopback-only (`127.0.0.1` / `::1`) with an explicit configured port. Non-loopback endpoints are `BLOCKED` unless a future ADR and dedicated trust model explicitly permit them.
- HTTP redirects that leave the accepted loopback origin are rejected.
- ComfyUI workflow execution is allowlisted by validated workflow definition/recipe IDs and typed parameters; raw model-generated ComfyUI API graphs are not directly executable.
- Versioned schemas are required for capability snapshots, workflow definitions, model mappings, run manifests, VRAM policy/evidence and local acceptance reports.
- Explicit `UNKNOWN`, `N/A`, `UNAVAILABLE`, `BLOCKED`, `STALE`, `MISSING`, `CORRUPT`, `CANCELLED` and `FAILED` states are used where applicable. Missing queue/history/output evidence never becomes PASS.
- Generated bytes are verified before promotion to R8 Vault. A ComfyUI filename/path is never asset identity.
- No model weights, generated production media or large external fixtures are committed to the Kodepoia repository merely to make CI pass.
- ADR required if implementation would alter a frozen R1–R8 foundation rather than add an R9-scoped capability.

## Local transport and trust model

R9 treats ComfyUI as a local external service, not as an extension of Kodepoia's own trust boundary.

The only accepted transport surface is a typed `ComfyUIClient` configured with a validated loopback origin. The client owns the fixed endpoint set required by R9. Callers select typed operations, never arbitrary routes.

Planned fixed endpoint families are:

- health/version/system information;
- node definitions/capabilities;
- model folder/type inventory;
- workflow prompt submission;
- queue status;
- WebSocket progress/status events;
- prompt history/output references;
- generated-output retrieval;
- targeted queue deletion where supported by the accepted contract;
- running-work interruption;
- memory/model release.

Protocol parsing is fail-closed and size-bounded. Unknown fields are tolerated only where the accepted schema explicitly permits forward-compatible extension; malformed required fields, impossible state transitions, oversized responses and cross-origin redirects are rejected.

WebSocket events provide timely progress but are not the sole completion authority. Durable completion is reconciled against the prompt's queue/history/output evidence before an R9 run can become `SUCCEEDED`.

## Workflow and execution identity model

R9 separates these concepts:

1. **WorkflowDefinitionId** — immutable identity of a normalized, versioned Kodepoia workflow definition.
2. **WorkflowInstance** — one typed parameterization of an accepted definition.
3. **CapabilitySnapshot** — exact ComfyUI/node/model environment evidence against which validation occurred.
4. **ModelResolutionSet** — exact mapping from logical model requirements to discovered local ComfyUI model identities and optional R8 Vault revisions/digests.
5. **ComfyRunId** — Kodepoia run identity bound to prompt ID, workflow instance, capability snapshot, resolved models, inputs, seed/settings and environment evidence.
6. **Generated output revision(s)** — verified R8 derived asset revisions produced from the run and linked by explicit transform lineage.

A repeated workflow request may reuse R8 transform-cache results only when R8.3's exact identity rules prove that the inputs, workflow definition/version, model resolutions, relevant ComfyUI/provider environment, deterministic settings, logical output identity and output digest all match. ComfyUI's own internal cache is an execution optimization, never Kodepoia's acceptance authority.

## Model-resolution policy

R9 distinguishes:

- logical model requirement (for example a role/type and compatibility constraints);
- ComfyUI inventory name/path token returned by the local service;
- optional R8 Vault model/asset revision with exact SHA-256 and provenance;
- external local model that is present in ComfyUI but not governed in Vault.

A model resolver may select only from discovered inventory matching an accepted typed requirement. It never guesses a filename, recursively scans arbitrary drives or downloads a model. External local models may be usable for local generation when explicitly authorized, but missing provenance/license is retained as `NOASSERTION`/unknown and generated assets cannot silently become unrestricted/exportable.

Model resolution evidence must bind enough identity to prevent silent substitution. When the ComfyUI API does not expose content hashes, R9 records the inventory token plus configured model-root identity and any available filesystem/Vault digest evidence; unresolved identity strength is explicit rather than fabricated.

## VRAM coordination policy

R9 introduces one structured local GPU-resource coordinator, not a generic hardware-control API.

The coordinator:

- reads accepted ComfyUI system/VRAM telemetry when available;
- may read already accepted local-model telemetry (for example Ollama running-model evidence);
- applies configured reserve/headroom and phase budgets;
- admits, defers or rejects R9 jobs before execution;
- uses only typed unload/release operations already exposed by accepted clients;
- may request ComfyUI model unload/free-memory through the fixed R9 client operation;
- may request unload of specifically identified inactive Ollama models through the accepted `OllamaClient.unload` boundary;
- may optionally restore only explicitly recorded/authorized prior Ollama workloads through an accepted preload path;
- never kills processes, edits driver settings, resets GPUs, changes global environment variables, installs runtimes, or overrides OS memory management.

VRAM telemetry is evidence, not a promise. OOM/failure remains possible and must produce `FAILED`/`RESOURCE_EXHAUSTED`, trigger bounded cleanup, and preserve diagnostics.

## External-reference planning notes (non-normative)

Current official ComfyUI material checked during R9 planning documents:

- an HTTP prompt queue plus WebSocket progress/event flow and history-based output retrieval;
- node/model inventory and system statistics surfaces;
- explicit interruption and free-memory/model-unload operations;
- VRAM-related launch options including reserve/headroom controls;
- multiple local GPU backends with backend/hardware-specific support constraints.

These references guide the compatibility layer but do not override Kodepoia's frozen architecture. R9 does not auto-install or mutate the user's ComfyUI/GPU stack. Backend-specific behavior must be detected and recorded, not assumed.

## Global prerequisites

Before R9.1 implementation begins:

- R1–R8 are COMPLETE on normalized `main`;
- R8 final normalization PR #102 is merged and `main` is `359e9eb8225e4eaf3f518888da0ebf43e4605e9e` at the planning branch point;
- `docs/roadmap/R8_INTEGRATED_ACCEPTANCE.json` remains valid and R8 integrated acceptance stays PASS;
- Python baseline remains 3.12.x unless a separately accepted compatibility change is made;
- R3 `OllamaClient`, registry/router and local-model telemetry/unload paths remain available for GPU coexistence;
- R6 Health/Budget/Regression/CI/Privacy/AppSecurity/License-BOM contracts remain accepted;
- R8 Vault/AssetService/transform lineage and governed export remain accepted;
- no mandatory cloud service, account or API key is introduced;
- hosted CI uses deterministic protocol fixtures/fake loopback servers and small generated bytes only;
- real-GPU/real-ComfyUI evidence is required only at the subdivision explicitly marked REQUIRED;
- no ComfyUI model or custom-node download is performed by R9 planning or CI.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R9.1 | ComfyUI contracts, local endpoint boundary + capability schema | PLANNED | NONE | R8 COMPLETE + planning PR merged |
| R9.2 | Typed HTTP/WebSocket client, health, queue/history + protocol state | PLANNED | CONDITIONAL | R9.1 |
| R9.3 | Node/model inventory + capability snapshots | PLANNED | NONE | R9.1–R9.2 |
| R9.4 | Validated workflow catalog + governed model resolver | PLANNED | NONE | R9.1–R9.3 + R8 governance |
| R9.5 | Execution engine, queue/progress/reconciliation + run manifests | PLANNED | CONDITIONAL | R9.1–R9.4 |
| R9.6 | Generated-output capture + R8 Vault/AssetPipeline lineage bridge | PLANNED | NONE | R9.4–R9.5 + R8.2/R8.3/R8.6 |
| R9.7 | Cancellation, interruption, crash recovery + free-memory semantics | PLANNED | NONE | R9.2–R9.6 |
| R9.8 | VRAM telemetry, admission scheduler + Ollama coexistence | PLANNED | REQUIRED | R9.2–R9.7 + R3/R6 |
| R9.9 | Production 2D/UI/texture/concept workflow packs | PLANNED | CONDITIONAL | R9.4–R9.8 |
| R9.10 | CLI + KodeStudio ComfyUI/VRAM UX | PLANNED | NONE | R9.1–R9.9 |
| R9.11 | Adversarial hardening + R9 integrated acceptance | PLANNED | CONDITIONAL | R9.1–R9.10 |

---

# R9.1 — ComfyUI contracts, local endpoint boundary + capability schema

## Objective and rationale

Create one typed ComfyUI domain and network boundary before any workflow can execute. Freeze local endpoint validation, state enums, schema versions and transport-independent contracts so later subdivisions cannot turn ComfyUI into an arbitrary HTTP or graph-execution surface.

## In scope

- `ComfyEndpoint`, `ComfyCapabilityState`, `ComfyQueueState`, `ComfyRunState`, typed prompt/history/output references and resource-status contracts;
- loopback-origin parser/validator with fixed scheme/host/port policy;
- response/request size budgets and timeout policy;
- versioned JSON schemas for capability snapshot, workflow definition, run manifest and VRAM evidence roots;
- R9 package namespace, expected `src/kodepoia/comfyui/`;
- stable exception taxonomy for unavailable/protocol/version/resource/governance failures;
- canonical JSON/digest helpers for R9 identities.

## Out of scope

No network calls, model inventory, workflow execution, generated output, GPU scheduling or UI.

## Dependencies and prerequisites

R8 COMPLETE, merged R9 plan, normalized `main`, existing R1–R8 security/governance contracts.

## Detailed implementation plan

Implement frozen dataclasses/enums and canonical serializers. `ComfyEndpoint` accepts loopback literal/name only, normalizes scheme/port and rejects credentials, paths, query/fragment, wildcard bind addresses and non-loopback hosts. Endpoint identity is configuration evidence, not user/model text.

Define run-state transitions with terminal `SUCCEEDED`, `FAILED`, `CANCELLED`, plus explicit unavailable/resource/protocol conditions. Schemas include `schema_version` and reject unknown major versions. Persisted digests are recomputed on load.

## Deliverables

- `src/kodepoia/comfyui/contracts.py`, `boundary.py`, `serialization.py`, package exports;
- R9 schemas under `schemas/`;
- unit/schema/tamper/endpoint-boundary tests;
- `docs/roadmap/R9_1_DESIGN.md` and `R9_1_ACCEPTANCE.md`.

## Acceptance gates / Definition of Done

R0 + full Python Core + UI Smoke SUCCESS on exact head; deterministic canonical digests; schema round-trip; non-loopback/credential/path/redirect-origin rejection tests; transition-table tests; no process/network request executed by R9.1.

## Validation and evidence

Accepted head SHA, CI run IDs, test counts, schema IDs/versions, representative canonical digest, endpoint-negative-case evidence.

## Rollback / recovery

Remove R9 contracts/schemas/exports. No durable runtime state exists yet.

## Risks and regression traps

Hostname normalization accidentally allowing remote resolution; URL parser ambiguity; mutable fields entering identity; accepting impossible state transitions; duplicating R8 asset identity.

## Manual intervention

**NONE**.

---

# R9.2 — Typed HTTP/WebSocket client, health, queue/history + protocol state

## Objective and rationale

Implement the smallest fixed local ComfyUI protocol client required by R9, with pollable source-of-truth state and WebSocket progress as a convenience layer.

## In scope

- typed fixed-route HTTP operations for health/system info, prompt metadata, queue, history and output retrieval;
- WebSocket connection scoped to the accepted loopback origin/client ID;
- bounded JSON/binary frame parsing;
- typed event normalization for status/start/executing/progress/executed/error/interrupted/cached events where present;
- reconnect/backoff with cancellation and hard time budgets;
- protocol compatibility/version/capability evidence;
- deterministic fake-loopback server fixtures for CI.

## Out of scope

Submitting production workflows, deleting queue items, interrupting work, `/free`, model resolution or Vault promotion.

## Dependencies and prerequisites

R9.1 COMPLETE. Current upstream endpoint semantics are treated as external compatibility input, not architecture authority.

## Detailed implementation plan

Create `ComfyUIClient` with a fixed method set; it does not expose a generic `_request(method, arbitrary_path)` publicly. All redirects are inspected and must remain same-origin loopback. HTTP bodies and WebSocket frames have configured maximum sizes. Invalid JSON, mismatched prompt IDs, impossible event ordering and truncated streams become protocol errors.

Completion must remain pollable through queue/history even if WebSocket disconnects. The normalized client reports `UNAVAILABLE` on connection failure and never converts a timeout into completion.

## Deliverables

Client/transport/event parser modules, deterministic fake server, protocol fixtures, reconnect/timeout/oversize tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Exact-head gates; fake server covers success, 4xx/5xx, timeout, malformed JSON, unexpected redirect, dropped WebSocket, duplicate/out-of-order events and history reconciliation; no arbitrary route surface; bounded retries.

## Validation and evidence

Accepted head, CI IDs, protocol fixture version/digest, compatibility snapshot against the documented external contract.

## Rollback / recovery

Remove client modules/fixtures; no production queue is mutated in this subdivision.

## Risks and regression traps

Treating WebSocket silence as success; SSRF through redirects; unbounded frames; retry storms; coupling to undocumented tuple positions without validation.

## Manual intervention

**CONDITIONAL**.

1. **Reason:** hosted CI validates the protocol through deterministic loopback fixtures; a real local ComfyUI smoke is required only if implementation depends on behavior that current official contract/fixtures cannot establish or upstream API drift is detected.
2. **Prerequisites:** accepted R9.2 candidate head; user-owned local ComfyUI already installed and running; loopback-only endpoint; no model download required.
3. **Exact actions/commands:** at the gate, use the exact candidate head and run the implemented `python -m kodepoia.cli comfy-probe --endpoint http://127.0.0.1:8188 --output .kodepoia/evidence/r9-2-comfy-probe.json`.
4. **Expected output:** exit code 0; endpoint loopback; health/system/queue/history capability states explicit; no protocol error; evidence JSON created.
5. **Failure recovery:** stop the probe, leave ComfyUI unchanged, preserve the JSON/log, do not weaken parsers or allow remote endpoints.
6. **Evidence to send back:** evidence JSON and redacted console output only.
7. **Do not do yet:** do not install/update custom nodes/models or expose ComfyUI to LAN/Internet for acceptance.
8. **Privacy/security note:** redact local usernames/paths where present; never send credentials/tokens.

Condition is NOT TRIGGERED when all accepted behavior is proven by current contract-compatible deterministic fixtures and no drift-sensitive behavior is introduced.

---

# R9.3 — Node/model inventory + capability snapshots

## Objective and rationale

Capture exactly what the connected ComfyUI instance can execute so workflow validation never relies on assumed nodes, model families or stale names.

## In scope

- node-definition/object-info inventory;
- model folder/type/name inventory;
- system/backend/version metadata available from the accepted client;
- normalized `CapabilitySnapshot` with digest, timestamp-as-evidence and explicit missing/unsupported states;
- snapshot comparison and `STALE` detection;
- safe cache/persistence of rebuildable capability snapshots;
- filters for allowed node classes/categories without executing them.

## Out of scope

Custom-node installation/update, model download, arbitrary filesystem scans, workflow execution.

## Dependencies and prerequisites

R9.1–R9.2 COMPLETE.

## Detailed implementation plan

Normalize discovered node schemas into typed required/optional inputs and output metadata needed for validation. Preserve unknown extension metadata as inert evidence only. Normalize model inventories by ComfyUI-reported model type and token. Snapshot identity binds ComfyUI/version evidence plus normalized inventories.

A snapshot becomes `STALE` when the service/version/node/model inventory changes. Missing endpoints are `UNAVAILABLE`/`UNKNOWN`, not empty-success.

## Deliverables

Inventory/snapshot modules, schemas, snapshot diff tool, fixtures for core-only/custom-node/changed-model cases, tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Exact-head gates; deterministic snapshot digest; stale detection; malformed node/model records rejected or isolated; unknown metadata never becomes executable instruction; no filesystem scan or download.

## Validation and evidence

Accepted head, CI IDs, fixture snapshot digests, stale-transition evidence.

## Rollback / recovery

Delete rebuildable snapshot cache; canonical external/Vault data unaffected.

## Risks and regression traps

Treating an empty inventory as authoritative absence; executable text from metadata; path traversal in model tokens; snapshot identity depending on timestamps.

## Manual intervention

**NONE**.

---

# R9.4 — Validated workflow catalog + governed model resolver

## Objective and rationale

Create Kodepoia-owned, versioned workflow definitions that can be validated against capability snapshots and resolve only explicitly available local models.

## In scope

- immutable `WorkflowDefinition` and typed parameter schema;
- normalized API-graph template owned by Kodepoia;
- allowlisted node classes and per-node parameter constraints;
- typed input/output slots and deterministic seed policy;
- validation against `CapabilitySnapshot`;
- logical `ModelRequirement` and `ModelResolution`;
- optional mapping to exact R8 Vault revisions/digests;
- external-local model state with explicit provenance/license uncertainty;
- workflow/version/model-resolution digests;
- catalog loading and tamper checks.

## Out of scope

Executing workflows, auto-installing custom nodes, downloading models, editing arbitrary user workflows, quality scoring.

## Dependencies and prerequisites

R9.1–R9.3 COMPLETE; R8 provenance/governance contracts available.

## Detailed implementation plan

Workflow templates are data checked into the repository or created through governed future UX, never raw model-generated graphs. Parameters are substituted only into typed declared slots; node IDs/classes/connections are immutable per definition version unless a new definition revision is created.

The resolver matches logical requirements to discovered ComfyUI inventory. It may use configured exact aliases and R8 Vault evidence. Ambiguous candidates remain unresolved until deterministic policy or explicit user choice exists. Exportability is inherited from R8/R6 evidence, not inferred from a model filename.

## Deliverables

Workflow catalog/validator/model resolver modules, workflow schema, safe sample fixture workflows with no large model dependency, tamper/ambiguity tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Exact-head gates; raw unknown node injection rejected; undeclared parameter mutation rejected; missing/ambiguous model explicit; deterministic workflow instance digest; no download/network beyond accepted local inventory calls.

## Validation and evidence

Accepted head, CI IDs, workflow definition IDs/digests, resolution fixture evidence, representative blocked/ambiguous cases.

## Rollback / recovery

Remove catalog/resolver additions; no external service or Vault bytes modified.

## Risks and regression traps

Graph injection through parameter fields; model filename spoofing; conflating inventory token with content identity; silently accepting changed custom-node semantics.

## Manual intervention

**NONE**.

---

# R9.5 — Execution engine, queue/progress/reconciliation + run manifests

## Objective and rationale

Execute only validated workflow instances and make every run auditable from submission through terminal reconciliation.

## In scope

- `ComfyExecutionService`;
- validated prompt submission with generated client/prompt correlation IDs;
- queue admission record and typed progress stream;
- poll/WebSocket reconciliation;
- terminal history/output reconciliation;
- durable `ComfyRunManifest` with workflow/model/input/seed/environment evidence;
- operation budgets, deadlines and cooperative cancellation token;
- retry policy limited to safe pre-submission/idempotent reads;
- duplicate-submission protection.

## Out of scope

Output promotion to Vault, VRAM scheduler policy, queue deletion/interruption/free memory.

## Dependencies and prerequisites

R9.1–R9.4 COMPLETE.

## Detailed implementation plan

Before submission, recompute workflow/capability/model-resolution digests and reject stale or tampered state. Record a PREPARED run manifest, then submit exactly once. After a prompt ID is returned, persist QUEUED/RUNNING transitions. WebSocket events update live progress but terminal state is confirmed through history/output references. If submission outcome is ambiguous after a connection break, query queue/history by correlation evidence before any resubmission.

No terminal `SUCCEEDED` state exists until required output references are present and protocol reconciliation is consistent.

## Deliverables

Execution service, run store/schema, progress/correlation logic, fake-server execution fixtures, crash/ambiguous-submit tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Exact-head gates; one logical request cannot create duplicate prompt submission under tested retry failures; progress is monotonic per normalized contract where applicable; dropped WebSocket still resolves through polling; malformed/mismatched history fails closed.

## Validation and evidence

Accepted head, CI IDs, representative run-manifest digest/state trace, ambiguous-submit recovery evidence.

## Rollback / recovery

Pending local test jobs are fixture-only. Runtime manifests are append-only/recoverable and may be marked abandoned/failed without erasing history.

## Risks and regression traps

Double submission, race between WebSocket and history, stale capability snapshot between validation and submit, treating queue acceptance as completion.

## Manual intervention

**CONDITIONAL**, with the same trigger discipline as R9.2: only if a real ComfyUI behavior required by the implementation cannot be established by the accepted protocol fixtures/current contract. If triggered, use an explicitly supplied safe no-production workflow on the exact candidate head; no model/custom-node installation is permitted solely for this gate.

---

# R9.6 — Generated-output capture + R8 Vault/AssetPipeline lineage bridge

## Objective and rationale

Turn completed ComfyUI outputs into verified R8 derived assets without creating a second media store or losing generation provenance.

## In scope

- output-reference validation and safe retrieval through `ComfyUIClient`;
- byte-size/type/hash verification;
- managed staging beneath accepted boundaries;
- R8 `AssetService` ingest of generated bytes as DERIVED revisions;
- R8 transform lineage binding source inputs, workflow definition/version, model resolution, environment, seed/settings and output digest;
- governed metadata/provenance/license propagation;
- multi-output run handling;
- failed/cancelled run cleanup without promoting partial READY assets.

## Out of scope

Quality judgement, remote publishing, arbitrary ComfyUI output-directory scans.

## Dependencies and prerequisites

R9.4–R9.5 COMPLETE; R8.2/R8.3/R8.6 accepted services unchanged.

## Detailed implementation plan

Retrieve only output references belonging to the reconciled prompt ID. Reject traversal/absolute paths and unexpected output types. Stage bytes, hash, validate size/type, then call the accepted R8 service boundary. The R9 run manifest records resulting asset/revision IDs; R8 remains canonical for bytes/provenance/governance.

A partial multi-output failure does not silently promote an incomplete logical output set. Promotion policy is explicit per workflow definition.

## Deliverables

Output bridge modules, transform/provider adapter, R8 lineage integration tests, small binary fixtures, design/acceptance docs.

## Acceptance gates / Definition of Done

Exact-head gates; cross-prompt output reference rejected; path escape rejected; hash/size mismatch rejected; failed/cancelled run leaves no READY derived revision; successful fixture produces reconstructable R8 lineage.

## Validation and evidence

Accepted head, CI IDs, run digest, source/input/output revision IDs/digests, lineage verification evidence.

## Rollback / recovery

Use R8 deletion/reference rules for promoted test revisions; staged unpromoted bytes are safe to discard. No source revision is mutated.

## Risks and regression traps

Trusting filenames, accepting outputs from another prompt, promoting before verification, losing model/workflow provenance, bypassing R8 governance.

## Manual intervention

**NONE**.

---

# R9.7 — Cancellation, interruption, crash recovery + free-memory semantics

## Objective and rationale

Make cancellation and cleanup explicit, bounded and recoverable while distinguishing pending queue deletion, running interruption and asynchronous memory-release requests.

## In scope

- typed pending-job deletion/cancellation where supported;
- targeted running interruption where supported by the accepted contract;
- `/free` model-unload/free-memory request;
- cancellation state machine and audit events;
- restart/reconciliation of in-flight run manifests;
- orphan/unknown prompt handling;
- cleanup ordering after failure/OOM/cancel;
- proof that memory-release request completion is not misreported as guaranteed reclaimed bytes.

## Out of scope

VRAM admission policy, process termination, GPU reset, driver/runtime control.

## Dependencies and prerequisites

R9.2–R9.6 COMPLETE.

## Detailed implementation plan

Cancellation first identifies whether a run is pending or running. Pending work uses the supported queue operation; running work uses targeted interruption when available. After action, reconcile queue/history before setting terminal state. `/free` is recorded as a request and followed by telemetry/poll evidence where available; its HTTP success alone does not prove memory was reclaimed.

At startup, non-terminal manifests are reconciled against local service state and become recovered RUNNING/QUEUED, FAILED, CANCELLED or UNKNOWN according to evidence.

## Deliverables

Cancellation/recovery modules, audit integration, deterministic failure/OOM/restart fixtures, design/acceptance docs.

## Acceptance gates / Definition of Done

Exact-head gates; cancellation race tests; restart reconciliation; no global interrupt used when a targeted safe operation is available; `/free` response never fabricates reclaimed-VRAM measurement; bounded cleanup.

## Validation and evidence

Accepted head, CI IDs, state traces for pending delete/running interrupt/disconnect/restart/OOM cleanup.

## Rollback / recovery

Cancellation is inherently operational; manifests/audit remain append-only. No forceful process or driver mutation exists to recover.

## Risks and regression traps

Interrupting the wrong prompt; global interruption due missing correlation; conflating request accepted with memory actually free; retrying destructive queue operations blindly.

## Manual intervention

**NONE**.

---

# R9.8 — VRAM telemetry, admission scheduler + Ollama coexistence

## Objective and rationale

Implement the roadmap's VRAM unload/reload scheduling with measurable policy, not heuristic hidden behavior, and validate it on a real local GPU because hosted CI cannot authoritatively prove GPU-memory behavior.

## In scope

- `GpuResourceCoordinator`;
- normalized ComfyUI VRAM/system telemetry adapter;
- accepted Ollama running-model memory evidence integration;
- configurable total/reserve/headroom/job-estimate policy;
- `ADMIT`, `DEFER`, `REJECT`, `UNKNOWN` decisions with reasons;
- typed cleanup sequence: inactive approved Ollama unload → ComfyUI free/unload request → remeasure → admit/defer;
- optional restoration of explicitly recorded authorized prior Ollama workload;
- OOM feedback updating evidence/estimates without silently widening budgets;
- per-workflow observed peak/starting/ending memory evidence where telemetry permits;
- Health/Budget integration and audit events.

## Out of scope

Killing ComfyUI/Ollama, driver reset, overclock/undervolt, OS paging changes, arbitrary environment mutation, runtime/driver installation.

## Dependencies and prerequisites

R9.2–R9.7 COMPLETE; R3 Ollama unload/preload/running-model contracts and R6 budgets accepted.

## Detailed implementation plan

Create a lease-based coordinator around one local GPU resource domain. A job supplies a typed resource estimate/profile. The coordinator samples telemetry and applies reserve/headroom. If insufficient, only explicitly configured inactive workloads may be asked to release memory. Re-sample before admission. Never assume an unload succeeded because the request returned.

Record backend/device/total memory, available evidence, actions taken, timings and terminal result. Restoration is opt-in and limited to workloads recorded before the lease.

CI uses deterministic telemetry fixtures to prove policy. Authoritative acceptance additionally requires a real local ComfyUI/GPU run on the exact head.

## Deliverables

Coordinator/policy/profile/evidence modules and schemas; fake telemetry fixtures; Ollama coexistence tests; OOM/release/remeasure tests; `r9-local-vram-acceptance` CLI; design/acceptance docs.

## Acceptance gates / Definition of Done

R0 + full Python Core + UI Smoke on exact head; deterministic scheduler-policy tests; no arbitrary process/hardware control; **REQUIRED local GPU evidence** on the exact candidate head with real ComfyUI, proving service discovery, one bounded generation, telemetry capture, cleanup/re-measure and audit-chain validity. If an Ollama model is already loaded, coexistence/unload/restore is tested only when explicitly safe/authorized; absence of a loaded Ollama model does not require downloading/loading one solely for acceptance.

## Validation and evidence

Accepted head; CI run IDs; local evidence JSON SHA-256/size; ComfyUI version/backend/device; VRAM total/free samples; scheduler decision/action trace; bounded workflow/run identity; output digest; audit verification; explicit Ollama coexistence state (`TESTED`, `N/A`, or `UNAVAILABLE`) with reason.

## Rollback / recovery

Disable R9 scheduling and fall back to `UNKNOWN/DEFER`; never force admission. Local acceptance creates only bounded test output, which can be removed through accepted R8 rules after evidence is preserved.

## Risks and regression traps

Backend telemetry units; stale free-memory readings; OOM despite apparent capacity; model unload latency; restoring an unintended Ollama model; assuming NVIDIA-specific semantics on AMD/other backends.

## Manual intervention

**REQUIRED**.

1. **Reason:** GitHub-hosted CI does not provide the user's authoritative GPU/ComfyUI environment and cannot prove real VRAM allocation, unload/release, OOM behavior or backend compatibility.
2. **Prerequisites:** exact R9.8 candidate head supplied by ChatGPT; repository clean; Python environment installed; local ComfyUI already installed by the user and reachable only on loopback; at least one already-installed compatible image model/workflow chosen explicitly; sufficient free disk; no secrets required. Do not install/update drivers, ComfyUI, custom nodes or models merely for the gate.
3. **Exact actions/commands:** after ChatGPT supplies the exact head, checkout that head and run:
   `python -m kodepoia.cli r9-local-vram-acceptance --endpoint http://127.0.0.1:8188 --output .kodepoia/evidence/r9-8-local-vram.json`
   using the implemented command's explicit safe model/workflow selection flags if the command reports that selection is required.
4. **Expected output:** exit code 0; all planned acceptance checks PASS; evidence JSON exists; endpoint is loopback; real ComfyUI version/backend/device and memory samples recorded; bounded test generation reaches reconciled success; output digest verifies; cleanup/re-measure completes; audit chain valid.
5. **Failure recovery:** stop further R9 work; keep evidence/logs; allow the command's bounded cleanup to finish; do not weaken budgets or install random packages/models. Restart ComfyUI only if the tool reports the service is unavailable and the user's normal installation requires it.
6. **Evidence to send back:** `r9-8-local-vram.json` plus redacted console output. If the command emits a separate audit/evidence file, send that too.
7. **Do not do yet:** do not proceed to R9.9, expose ComfyUI remotely, change GPU drivers/runtime, install custom nodes, or download replacement models until the evidence is reviewed.
8. **Privacy/security note:** redact usernames/absolute private paths if present; never send passwords, tokens, private keys or unrelated files.

Because R9.8 is REQUIRED, implementation must stop before R9.9 until this evidence is reviewed and accepted.

---

# R9.9 — Production 2D/UI/texture/concept workflow packs

## Objective and rationale

Deliver the user-facing R9 media capability promised by the frozen roadmap through a small set of validated, versioned workflow families rather than arbitrary graphs.

## In scope

At minimum, workflow-definition families for:

- concept/key art generation;
- UI/icon/illustration generation;
- texture/material-source generation suitable for later Godot/Blender processing;
- 2D sprite/asset generation where supported by the selected local model stack;
- deterministic seed/settings capture;
- dimension/aspect/output-count/budget constraints;
- model requirements expressed through R9.4 resolver;
- generated outputs routed through R9.6 R8 lineage;
- workflow compatibility reports against current capability snapshot.

Workflow packs may support multiple compatible model families only through explicit versioned variants. No model is downloaded by the workflow pack.

## Out of scope

Claiming artistic quality without evidence, 3D mesh generation/Blender pipelines, video/cinematics, custom-node installation automation.

## Dependencies and prerequisites

R9.4–R9.8 COMPLETE including accepted R9.8 local hardware evidence.

## Detailed implementation plan

Check in workflow definitions/typed parameter schemas and small non-model test fixtures. Prefer core ComfyUI nodes where feasible; custom-node requirements must be explicit, version-aware and `UNAVAILABLE` when missing. Each pack defines output semantics and R8 asset kind/lineage mapping.

CI validates graphs and parameter constraints against synthetic capability fixtures. A real local smoke is required only if the selected production pack introduces a node/model family not already exercised by accepted R9.8 evidence.

## Deliverables

Versioned workflow-pack files, catalog metadata, parameter schemas, compatibility tests, R8 output mapping tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Exact-head gates; each mandatory family validates; missing custom node/model is explicit; no raw graph execution; deterministic identity; R8 output lineage; budget limits.

## Validation and evidence

Accepted head, CI IDs, workflow-definition IDs/digests, compatibility matrix, optional local output/evidence digests if CONDITIONAL is triggered.

## Rollback / recovery

Remove/disable workflow definition version; existing generated R8 assets retain immutable lineage.

## Risks and regression traps

Workflow drift across ComfyUI versions; hidden custom-node dependency; model-family parameter mismatch; large default dimensions causing OOM; texture outputs mislabeled as production-ready PBR maps without validation.

## Manual intervention

**CONDITIONAL**.

Trigger only when a mandatory workflow pack depends on a real node/model family not already covered by accepted R9.8 local evidence. If triggered, use the exact candidate head and the implemented bounded `r9-local-workflow-acceptance` command with an already-installed user-selected compatible model; do not install/download a model or custom node solely to satisfy acceptance.

---

# R9.10 — CLI + KodeStudio ComfyUI/VRAM UX

## Objective and rationale

Expose R9 capabilities through one safe service façade and non-blocking KodeStudio UX without duplicating networking, workflow or GPU-control code in the UI.

## In scope

- `ComfyService` façade over capability/inventory/catalog/resolver/execution/output/cancel/VRAM components;
- CLI: probe/status/inventory/workflow validate/run/status/cancel/free-memory/evidence commands with typed options;
- KodeStudio panel for local service health, capability staleness, model resolution, workflow selection/typed parameters, queue/progress, outputs, cancellation and VRAM budget evidence;
- explicit warnings for unavailable models/nodes, uncertain provenance/license and required local acceptance;
- threaded/async-safe UI execution following accepted R8.10 worker pattern;
- accessibility/pseudo-localization and UI smoke extension.

## Out of scope

Embedded ComfyUI web UI, arbitrary graph editor, arbitrary endpoint/route console, custom-node/model installer.

## Dependencies and prerequisites

R9.1–R9.9 COMPLETE.

## Detailed implementation plan

CLI/KodeStudio call only `ComfyService`. KodeStudio must not open direct HTTP/WebSocket/process/filesystem paths. Long operations run off the GUI thread with independent service/client state as needed. Progress/cancel uses R9 state, not UI-local guesses.

Destructive/expensive actions require explicit confirmation according to policy. Raw prompt/workflow JSON is not an execution entry point.

## Deliverables

Service façade, CLI commands, KodeStudio panel/widgets, accessibility/i18n updates, smoke tests, design/acceptance docs.

## Acceptance gates / Definition of Done

Exact-head gates; UI Smoke covers disconnected/local-ready/stale/missing-model/queued/running/success/failure/cancel/resource-blocked states; no GUI freeze in deterministic long-operation fixture; no second direct networking/process path; CLI output machine-readable where applicable.

## Validation and evidence

Accepted head, CI IDs, UI smoke evidence, representative CLI JSON output digests.

## Rollback / recovery

Remove UI/CLI wiring; lower-level accepted R9 services remain intact.

## Risks and regression traps

GUI blocking on WebSocket/polling; UI bypassing service validation; accidental arbitrary JSON execution field; cancellation button affecting wrong job.

## Manual intervention

**NONE**.

---

# R9.11 — Adversarial hardening + R9 integrated acceptance

## Objective and rationale

Prove R9 as an integrated phase under hostile/malformed protocol, workflow, model, output and resource conditions, then emit canonical exact-head acceptance evidence.

## In scope

Adversarial/integrated coverage for at least:

- non-loopback/redirect endpoint attack;
- malformed/oversized HTTP and WebSocket payload;
- forged/mismatched prompt/history/output IDs;
- stale capability snapshot and swapped model inventory;
- graph/parameter injection attempt;
- poisoned workflow/model mapping manifest;
- cross-run output reference;
- output path traversal and corrupt bytes;
- duplicate-submit race;
- cancel/complete race and reconnect;
- fake `/free` success without memory recovery;
- stale/contradictory VRAM telemetry;
- OOM cleanup path;
- attempted arbitrary executable/URL/custom-node/model-install surface;
- bounded many-job fixture proving queue/resource state does not grow unbounded;
- R8 lineage/governance verification for generated outputs.

Create R9 integrated acceptance schema/report/verifier following the accepted R7/R8 exact-head pattern without modifying frozen earlier integrated reports.

## Out of scope

R10+ features or destructive red-team actions against real user projects/hardware.

## Dependencies and prerequisites

R9.1–R9.10 COMPLETE; R9.8 REQUIRED local evidence accepted; any triggered R9.2/R9.5/R9.9 manual evidence accepted.

## Detailed implementation plan

Add `scripts/r9_integrated_acceptance.py`, canonical `docs/roadmap/R9_INTEGRATED_ACCEPTANCE.json`, acceptance docs and CI invocation. The report binds exactly R9.1–R9.11 accepted source docs/evidence, exact source SHA, manual-state satisfaction, blockers and deterministic digest. Validation reads canonical Git blobs and fails closed on missing/mismatched bytes/head/manual evidence.

R9 integrated report never rewrites R8 evidence.

## Deliverables

Adversarial tests, integrated verifier/script/schema/report, `R9_11_ACCEPTANCE.md`, continuity updates and phase completion evidence.

## Acceptance gates / Definition of Done

R0 Repository Guard, full Python Core including `R9 integrated acceptance: PASS`, KodeStudio UI Smoke on one exact final documentation head; all R9.1–R9.11 acceptance records valid; `blockers=[]`; required local R9.8 evidence referenced by digest; no regression in R8 integrated verifier; PR merged; final continuity-only normalization if required by exact-head documentation policy.

## Validation and evidence

Exact implementation/final documentation heads, CI run IDs, test counts/warnings/skips, integrated report digest, manual evidence digest(s), PR/merge SHA, final continuity normalization evidence.

## Rollback / recovery

If any integrated gate fails, R9 remains IN PROGRESS; do not weaken earlier gates or edit accepted R1–R8 evidence. Fix forward on a dedicated R9.11 candidate and regenerate only R9 evidence.

## Risks and regression traps

Circular self-attestation; report generated from working tree instead of Git blobs; manual evidence inferred from absence; adversarial tests mutating user ComfyUI; R8 regression hidden by R9-only testing.

## Manual intervention

**CONDITIONAL**.

Normally no new user-side run is required if accepted R9.8 REQUIRED evidence and any triggered earlier conditional evidence remain valid for the exact implemented contracts. Trigger a new local integrated smoke only if R9.11 changes hardware-facing semantics, invalidates prior evidence, or hosted CI cannot exercise a newly authoritative path. If triggered, stop before phase completion until exact-head evidence is reviewed.

## Phase completion rule

R9 can be marked COMPLETE only when every R9.1–R9.11 subdivision is COMPLETE with exact required evidence, R9.8 REQUIRED hardware-local acceptance is satisfied, all triggered CONDITIONAL manual gates are satisfied, the canonical R9 integrated report is PASS with no blockers, final R0/Python Core/UI Smoke pass on the exact documentation head, and the implementation/acceptance PR plus any required continuity normalization are merged.

No hidden or undocumented ComfyUI/custom-node/model/runtime step may be used to claim R9 completion.

## Ongoing maintenance rule

Update `R9_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, supported protocol assumptions, manual prerequisites, acceptance requirements, important recovered defects, or phase ordering changes. Foundation changes require an ADR.

## Planning acceptance rule

This planning branch changes planning/continuity only. It MUST pass R0 Repository Guard, full Python Core and KodeStudio UI Smoke on one exact head containing both `R9_PLAN.md` and synchronized continuity. Only after all three are SUCCESS may the planning PR be merged. R9.1 begins from the resulting normalized `main`, never from an unmerged planning branch.
