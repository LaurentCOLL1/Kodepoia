# R9.1 Acceptance — ComfyUI contracts, local endpoint boundary + capability schema

**Status:** ACCEPTED IMPLEMENTATION — final documentation gates pending  
**Manual intervention:** NONE  
**Base normalized R9 planning main:** `e3f7bf6039cee918a5d505fb47ed536cde087e0e`  
**Exact accepted implementation head:** `dfde39746f0ec909a865a9f0ef75b6856e77c88f`

## Scope accepted

R9.1 establishes only the transport-independent ComfyUI foundation required by the merged `R9_PLAN.md`:

- immutable capability/queue/run/resource states;
- typed bounded prompt/history/output references;
- deterministic canonical JSON + SHA-256 identity helpers;
- strict versioned envelope parsing;
- explicit unavailable/protocol/version/resource/governance/boundary errors;
- explicit loopback-only `ComfyEndpoint` accepting `127.0.0.1` or `::1` with explicit port;
- HTTP/HTTPS origin normalization and derived WS/WSS origin without opening a connection;
- exact-origin redirect validation;
- bounded transport timeout/body/frame limits for later R9.2;
- Draft 2020-12 schema roots for capability snapshot, workflow definition, run manifest and VRAM evidence;
- offline/security/state/schema regression tests;
- `R9_1_DESIGN.md`.

No HTTP/WebSocket request, DNS lookup, socket construction, subprocess launch, ComfyUI probe, node/model inventory, workflow execution, output retrieval, GPU/VRAM action or UI implementation is part of R9.1.

## Exact-head implementation gates

All required implementation gates succeeded on exactly `dfde39746f0ec909a865a9f0ef75b6856e77c88f`:

| Gate | Run | Result |
| --- | --- | --- |
| R0 Repository Guard | #1108 / `32624052368` | SUCCESS, Ubuntu + Windows |
| Python Core | #1082 / `32624052364` | SUCCESS, all 5 jobs |
| KodeStudio UI Smoke | #1049 / `32624052378` | SUCCESS |

Python Core Ubuntu evidence:

- compile: SUCCESS;
- R7 integrated acceptance: PASS;
- R8 integrated acceptance: PASS;
- pytest: **612 passed / 6 skipped / 46 warnings**;
- package build Ubuntu: SUCCESS;
- package build Windows: SUCCESS;
- Python Core Windows tests: SUCCESS;
- integrated Windows KodeStudio smoke: SUCCESS.

The prior accepted R8 Ubuntu baseline was `588 passed / 6 skipped / 46 warnings`; R9.1 therefore adds test coverage without increasing the warning count.

## Security acceptance

Accepted boundary behavior is fail-closed:

- `localhost` is rejected rather than DNS-resolved;
- wildcard, LAN/private and public hosts are rejected;
- `127.0.0.2` is rejected; R9.1 accepts the two explicitly frozen literals only (`127.0.0.1`, `::1`);
- missing port, credentials, non-root origin path, query and fragment are rejected;
- redirect targets must retain the exact accepted scheme + loopback literal + port;
- canonical JSON rejects NaN/Infinity;
- unsupported envelope versions and unexpected root keys fail closed;
- PREPARED cannot jump directly to SUCCEEDED and terminal run states cannot become active again;
- server filenames/subfolders remain inert evidence and are never interpreted as local paths in R9.1;
- tests monkeypatch DNS lookup, socket construction and subprocess launch to fail if the R9.1 contract path touches them.

## Schema acceptance

These schema roots are accepted at version 1:

- `schemas/comfy-capability-snapshot-v1.schema.json` → `kodepoia.comfy-capability-snapshot`;
- `schemas/comfy-workflow-definition-v1.schema.json` → `kodepoia.comfy-workflow-definition`;
- `schemas/comfy-run-manifest-v1.schema.json` → `kodepoia.comfy-run-manifest`;
- `schemas/comfy-vram-evidence-v1.schema.json` → `kodepoia.comfy-vram-evidence`.

Each root requires exactly `schema`, `version`, `payload`. Detailed payload members remain owned by their frozen downstream subdivisions (R9.3/R9.4/R9.5/R9.8) and are intentionally not invented early in R9.1.

## External compatibility evidence

Current ComfyUI material reviewed during implementation continues to document `127.0.0.1` as the default server listen address and that an unqualified `--listen` broadens listening to wildcard IPv4/IPv6. Current server/API material also retains prompt/queue/history/object-info/system-statistics/WebSocket surfaces while newer job-oriented API surfaces exist.

This evidence informed the strict local origin contract only. R9.1 does not execute or make authoritative any upstream API route; typed network compatibility belongs to R9.2.

## Manual state

**NONE.** No real ComfyUI installation, model, GPU or local command is required or authoritative for R9.1 because this subdivision intentionally performs no transport or hardware operation.

## Regression / architecture determination

- R1–R8 frozen foundations remain unchanged.
- R7 and R8 integrated verifiers remain PASS.
- No second asset identity/store was introduced.
- No second arbitrary network/process surface was introduced.
- No ADR is required.

## Final documentation gate

This acceptance document changes the branch head, so `dfde39746f0ec909a865a9f0ef75b6856e77c88f` remains the immutable accepted **implementation** head while the final documentation head must independently pass R0 Repository Guard, full Python Core and KodeStudio UI Smoke before PR #105 may merge.

After merge, continuity must be normalized with the exact implementation evidence, final documentation gate evidence and PR merge SHA before R9.2 begins.
