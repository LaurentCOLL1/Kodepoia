# R9.8 — VRAM telemetry, admission scheduler + Ollama coexistence

Status: implementation in progress. Manual acceptance remains **REQUIRED**.

## Scope

R9.8 implements the frozen R9 plan without changing the v1.0 architecture. The resource layer is local-only and backend-agnostic: Kodepoia consumes ComfyUI's own `/system_stats` byte counters and the already accepted R3 `OllamaClient` running-model evidence. It does not add NVML/CUDA/ROCm driver control, process killing, driver reset, overclock/undervolt, paging mutation, arbitrary environment mutation, model download, custom-node installation, or runtime/driver installation.

## Upstream facts used by the design

- Current ComfyUI exposes the visible devices through `/system_stats`; the primary device remains first while additional visible devices can be reported. This is why R9.8 preserves each upstream device index rather than assuming a single CUDA/NVIDIA device.
- ComfyUI `/free` is a request, not proof of reclaimed bytes. Upstream records unload/free flags and the queue worker subsequently unloads models/resets execution state and empties caches. R9.8 therefore always re-reads `/system_stats` after cleanup and never derives reclaimed bytes from the HTTP acknowledgement.
- Current ComfyUI model management has its own reserved-memory and minimum-inference-memory behavior. R9.8 does not attempt to replace it; Kodepoia's reserve/headroom is an admission policy above ComfyUI, not a hidden rewrite of ComfyUI memory management.
- Ollama `/api/ps` exposes already-running model memory evidence including `size_vram`; existing R3 `OllamaClient.unload()` uses the accepted `keep_alive: 0` behavior. R9.8 never loads a model merely to make coexistence testable.

Upstream references:

- https://github.com/Comfy-Org/ComfyUI/pull/10589
- https://github.com/Comfy-Org/ComfyUI/blob/master/main.py
- https://github.com/Comfy-Org/ComfyUI/blob/master/comfy/model_management.py
- https://github.com/Comfy-Org/comfy-mcp/blob/main/README.md
- https://docs.ollama.com/api/ps

## Resource contracts

`ComfyVramTelemetryAdapter` accepts only the already fixed loopback ComfyUI client. It normalizes each visible device to exact integer byte evidence:

- device name and backend type;
- stable reported device index;
- `vram_total` / `vram_free`;
- optional torch total/free counters;
- ComfyUI/Python version context;
- canonical SHA-256 snapshot identity.

Impossible telemetry such as duplicate device indexes, negative counters, unbounded counters, or free VRAM greater than total VRAM fails closed as protocol error.

`GpuResourceProfile` is explicit and typed:

- `estimate_bytes`: expected workflow GPU-memory need;
- `reserve_bytes`: memory reserved from Kodepoia admission;
- `headroom_bytes`: additional safety margin;
- `device_index`: exact upstream device index;
- optional `total_limit_bytes`: user/project policy cap below measured physical VRAM.

The effective policy total is `min(measured_total, total_limit)` when a limit exists. A limit can only make admission more conservative.

## Admission semantics

`GpuAdmissionPolicy` has exactly four outcomes:

- `ADMIT`: measured/policy free VRAM covers estimate + reserve + headroom;
- `DEFER`: the job fits total policy capacity but currently lacks enough free VRAM;
- `REJECT`: estimate + reserve + headroom exceeds measured/configured total capacity;
- `UNKNOWN`: required authoritative device telemetry is unavailable.

No UNKNOWN/DEFER result is converted into PASS by heuristic. OOM observations can only maintain or increase a workflow estimate; they never lower reserve/headroom or silently widen a budget.

`GpuResourceCoordinator` serializes the local GPU admission domain with one in-process lease. For a DEFER result the only accepted cleanup sequence is:

1. capture exact pre-cleanup telemetry;
2. inspect already-running Ollama workload;
3. unload only model names explicitly authorized by the caller and proven present in that captured workload;
4. request ComfyUI model unload/free through the accepted R9.7 lifecycle route;
5. re-read authoritative ComfyUI telemetry;
6. recompute ADMIT/DEFER/REJECT/UNKNOWN from the new measurement.

The coordinator never kills ComfyUI/Ollama and never invokes global `/interrupt`. Ollama restoration is a separate opt-in operation and is limited exactly to models that the same scheduler trace recorded as unloaded.

## Health, Budget and audit integration

R9.8 reuses frozen v1.0 contracts instead of introducing parallel governance:

- `vram_budget_observation()` emits the existing `BudgetMetric.VRAM_MB` from measured used VRAM;
- `vram_health_metric()` maps scheduler evidence to the existing `HealthDimension.MEMORY` with UNKNOWN/WARN/FAIL/PASS semantics;
- resource actions append to the existing tamper-evident `AuditLog` category `comfyui.vram`;
- terminal ComfyUI cleanup continues to use the accepted R9.7 `ComfyLifecycleAuditStore` chain.

The frozen root `schemas/comfy-vram-evidence-v1.schema.json` is unchanged. R9.8 adds only `schemas/comfy-vram-evidence-payload-v1.schema.json` as the strict adjunct payload contract.

## REQUIRED local GPU acceptance

Hosted CI covers deterministic policy/protocol/storage invariants but cannot prove real GPU allocation/release/backend behavior. The authoritative local gate is therefore implemented by `r9-local-vram-acceptance` and must run on the exact candidate head.

The runner:

1. verifies the current Git HEAD through the accepted R8 structured VCS adapter and rejects a dirty worktree/index;
2. captures a CURRENT R9.3 ComfyUI capability snapshot;
3. loads exactly one explicit workspace-confined R9.4 workflow definition;
4. applies only declared scalar inputs/parameters and explicit model selections;
5. evaluates R9.8 admission and bounded cleanup/re-measure;
6. executes exactly one R9.5 run with bounded polling;
7. samples free VRAM before/during/after execution;
8. retrieves one exact run output and records SHA-256 + byte length;
9. performs terminal R9.7 cleanup and re-measures;
10. verifies resource and lifecycle audit evidence;
11. records Ollama coexistence as `tested`, `n/a`, or `unavailable` without manufacturing a workload;
12. writes a tamper-checked `kodepoia.comfy-vram-evidence` envelope inside the workspace.

The exact candidate SHA and concrete command are intentionally not frozen in this design file; they are supplied only after all hosted implementation gates are green. R9.9 remains forbidden until the returned local evidence is reviewed and accepted.
