# R9.10 — CLI + KodeStudio ComfyUI/VRAM UX — Acceptance

## Decision

R9.10 implementation is **ACCEPTED** on exact head:

`dda09a1728ba63640f68a979af57d70f12b4c603`

Manual intervention: **NONE**.

This document is a post-acceptance documentation-hardening artifact required by the frozen R9.10 deliverables. It records the already-accepted implementation and does not alter the accepted R9.10 runtime contract.

## Accepted base and merge lineage

- Base normalized R9.9 `main`: `5831e958c45ac63f6d2bcfd7da0a7934330c7586`.
- Implementation branch: `r9/10-cli-kodestudio-comfyui-vram-ux`.
- Exact accepted implementation head: `dda09a1728ba63640f68a979af57d70f12b4c603`.
- Implementation PR: #123.
- Implementation merge: `4372fa9067acf6aabf242f178be0d9f7ac041fc7`.
- Post-merge continuity normalization head: `7515b2bdec0d9eaec32820feb4563869f050be00`.
- Normalization PR: #124.
- Normalization merge: `4df1217cde078812af6882b812f640310aa45b61`.

## Authoritative implementation gates

All required implementation gates succeeded on exactly `dda09a1728ba63640f68a979af57d70f12b4c603`:

| Gate | Run | Result |
| --- | --- | --- |
| R0 Repository Guard | #1199 / `32657273588` | SUCCESS, Ubuntu + Windows |
| Python Core | #1173 / `32657273603` | SUCCESS, all 5 jobs |
| KodeStudio UI Smoke | #1140 / `32657273614` | SUCCESS |

Python Core Ubuntu evidence on the accepted implementation head:

- compile: SUCCESS;
- R7 integrated acceptance: PASS;
- R8 integrated acceptance: PASS;
- pytest: **729 passed / 7 skipped / 46 warnings**;
- package build Ubuntu: SUCCESS;
- package build Windows: SUCCESS;
- Python Core Windows tests: SUCCESS;
- embedded Windows KodeStudio smoke: SUCCESS.

The warning baseline remained 46; R9.10 did not hide or increase the existing warning baseline.

## Accepted post-merge normalization gates

The continuity-only R9.10 normalization head `7515b2bdec0d9eaec32820feb4563869f050be00` independently passed:

| Gate | Run | Result |
| --- | --- | --- |
| R0 Repository Guard | #1201 / `32657536700` | SUCCESS |
| Python Core | #1175 / `32657536745` | SUCCESS |
| KodeStudio UI Smoke | #1142 / `32657536723` | SUCCESS |

PR #124 then merged as `4df1217cde078812af6882b812f640310aa45b61`.

## Accepted scope

The accepted R9.10 implementation provides:

- one shared governed `ComfyService` façade over accepted R9.1–R9.9 services;
- a bounded `kodepoia comfy` CLI;
- a dedicated KodeStudio ComfyUI + VRAM page;
- non-blocking Qt workers with worker-safe service `fork()` semantics;
- protocol/capability status visibility;
- explicit model-resolution state;
- governed workflow selection and typed scalar parameters;
- persisted run/progress/reconciliation visibility;
- targeted cancellation;
- typed VRAM telemetry and admission state;
- conservative free-memory lifecycle operation;
- Ollama coexistence evidence visibility;
- persisted run/lifecycle/output/capability evidence;
- accessibility and pseudo-localization integration;
- dedicated R9.10 KodeStudio smoke coverage.

## CLI acceptance

The accepted CLI surface is limited to:

- `status`;
- `inventory`;
- `workflows`;
- `validate`;
- `run`;
- `run-status`;
- `cancel`;
- `vram`;
- `free-memory`;
- `evidence`.

CLI output is JSON-compatible and machine-readable. Governance/protocol/unavailable/value failures produce explicit fail-closed result states and non-zero status.

No CLI option exposes an arbitrary ComfyUI endpoint, URL, route, graph, process, executable, model downloader/installer or custom-node installer.

## KodeStudio acceptance

KodeStudio calls `ComfyService`; it does not import or construct a second direct ComfyUI transport path.

Long operations use `QThreadPool` workers. A worker calls `facade.fork()` where available so the worker owns independent transport state rather than sharing a mutable client with the GUI thread.

The accepted page exposes connection/capability/model/VRAM/admission/Ollama states, governed workflow parameters, run submission/refresh, targeted cancellation, free-memory and persisted evidence.

A one-second timer requests non-blocking run reconciliation. Run progress/state comes from the accepted persisted execution model rather than UI-local guesses.

## Security and governance acceptance

R9.10 did **not** introduce:

- arbitrary endpoint or route access;
- embedded ComfyUI web UI;
- arbitrary graph editor/execution;
- raw prompt/workflow JSON as an execution entry point;
- arbitrary executable or process launch;
- custom-node installation automation;
- model installation or download automation;
- a second run store, model resolver, workflow validator, VRAM scheduler or lifecycle subsystem.

The fixed loopback boundary, accepted R9.9 workflow catalog, governed model resolution, persisted run evidence and R9.8 admission semantics remain authoritative.

A persisted run whose capability identity or reconstructed workflow-instance digest no longer matches its manifest fails closed.

## Rejected candidates and recovered defects

The acceptance history deliberately preserves two failed candidates.

### Rejected candidate `d62a688092ceec9a90b4d78fb4e8feac8fddd24e`

R0 passed, while KodeStudio UI Smoke and the embedded Python Core KodeStudio UI job failed. The failures exposed newly introduced UI contract regressions:

- named R9.10 interactive controls were not all registered through the existing accessibility contract;
- the pseudo-locale navigation test still expected seven navigation entries after the new ComfyUI page was added.

Service/CLI Python jobs and package builds remained green. No gate was weakened.

### Rejected candidate `4394401510e34f3050040ebedd8799b91e3c0f51`

The next UI run reduced the remaining defect to one control:

- `comfyEvidenceView` had accessible text but was not registered through `mark_accessible`.

The implementation was fixed by registering that control with the existing accessibility contract. The UI workflow was also corrected to explicitly execute `tests/test_comfyui_r9_10_kodestudio.py`; this strengthened coverage rather than bypassing it.

### Accepted candidate

`dda09a1728ba63640f68a979af57d70f12b4c603` passed all three exact-head gates and became the immutable accepted R9.10 implementation head.

## Manual state

The frozen R9.10 manual mode is **NONE**.

No user-side ComfyUI, GPU, model or local command is required as additional acceptance for R9.10. Hardware-facing VRAM/workflow evidence remains governed by the already-accepted R9.8 REQUIRED evidence and R9.9 conditional rules.

## Documentation-hardening defect

While preparing R9.11 integrated acceptance, the repository was found to be missing two planned R9.10 deliverables:

- `docs/roadmap/R9_10_DESIGN.md`;
- `docs/roadmap/R9_10_ACCEPTANCE.md`.

The implementation, its exact-head gates, merge and post-merge continuity normalization had already succeeded. The missing files were therefore treated as a closure/documentation defect, not silently ignored and not used to fabricate integrated evidence.

This documentation-hardening branch adds only the missing R9.10 design/acceptance records. It must independently pass R0 Repository Guard, full Python Core and KodeStudio UI Smoke on one exact documentation head before merge.

Because recording those documentation-hardening gate IDs inside this file would change the head being certified, the final gate IDs and merge SHA are intentionally recorded in the subsequent continuity-only normalization instead.

## R9.11 authorization rule

R9.11 remains **NOT STARTED / UNAUTHORIZED** until:

1. this R9.10 documentation-hardening branch passes exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke;
2. its PR is merged;
3. continuity is normalized with the exact documentation-hardening head, gate IDs and merge SHA;
4. that continuity-only normalization independently passes the same three gates and is merged.

Only the resulting normalized `main` may be used as the R9.11 branch point.
