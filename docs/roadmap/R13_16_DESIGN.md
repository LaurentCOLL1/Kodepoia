# R13.16 Design — CLI + KodeStudio Mobile/DeviceLab/Release workspace

**Subdivision:** R13.16  
**Status:** IN_PROGRESS  
**Authorized normalized base:** `dce60a60b58ff2c069d689144291f8c682b7e21f`  
**Branch:** `r13/16-cli-kodestudio-workspace`  
**Manual:** NONE

## Objective

R13.16 is the final user-facing orchestration layer over the already accepted R13.1–R13.15 authorities. It does not create a second Android/iOS build stack, a second DeviceLab, a second release engine, or a new store/network provider seam.

The subdivision exposes:

- structured `kodepoia r13` intents for `status`, `scaffold`, `build`, `test`, `package`, `device`, `compliance`, and `release`;
- stable versioned JSON result shape and bounded exit semantics;
- a KodeStudio **Mobile, DeviceLab & Release** workspace driven by existing Project DNA/mobile Wizard output;
- read-only passive evidence summaries and an explicit capability/blocker matrix;
- explicit separation between passive refresh and execution;
- global KillSwitch cancellation for protected execution;
- source English localization, fallback localization and pseudo-localization;
- accessible names/descriptions for interactive controls and read-only evidence.

## Frozen safety boundary

R13.16 deliberately has no user-supplied field for:

- executable paths or command names;
- raw argv or shell fragments;
- Gradle tasks/properties or Xcode build settings/destinations;
- `adb shell` or arbitrary device commands;
- keystore paths/passwords, certificates/private keys or provisioning material;
- Play/App Store tokens, service-account credentials or API keys;
- arbitrary store endpoints, tracks or publication commands;
- editable evidence/PASS fields.

Those operations remain owned by the accepted structured R13 modules and KodeSecrets/ProcessSandbox/Guardian boundaries.

## Passive refresh contract

`MobileWorkspaceService.status()` is side-effect free with respect to external capabilities. It may only:

1. resolve the selected project root;
2. read and validate owned `.kodepoia/project.yaml` Project DNA;
3. read a fixed allowlist of bounded JSON evidence files below `.kodepoia/mobile/evidence/`;
4. return a capability/blocker snapshot.

It must not:

- launch or probe Gradle/JDK/SDK/Xcode/ADB/simulator/store tooling;
- invoke an injected execution backend;
- perform network access;
- mutate release/device/compliance state;
- treat an evidence field reporting `status=pass` as authority to change workspace state to `PASS`.

Evidence files are read through a bounded owned-file check: symlinks/escape are rejected, non-object/corrupt JSON is surfaced as unavailable, and individual passive reads are capped at 1 MiB.

## Structured execution contract

Execution is represented by `MobileWorkspaceOperation` and an injected `MobileWorkspaceExecutor` protocol. The workspace itself passes only a bounded `MobileExecutionContext` derived from accepted Project DNA:

- resolved project root;
- project name;
- Android/iOS target tuple;
- mobile source kind;
- package kinds;
- release channel intent;
- signing intent;
- network intent;
- the global/provided KillSwitch object.

The executor is repository-owned/trusted integration code, not model/project text. If no governed executor is configured, every execution operation returns `BLOCKED` with `EXECUTION_BACKEND_UNAVAILABLE`. R13.16 therefore never falls back to a shell or constructs an ungoverned tool invocation.

If the KillSwitch is already active, execution returns `CANCELLED` before the executor is called. The KodeStudio Cancel control invokes the same KillSwitch authority.

## Result model

`MobileWorkspaceResult` has `schema_version=1` and exposes:

- operation;
- state (`ready`, `pass`, `blocked`, `failed`, `cancelled`);
- project/mobile intent fields;
- capability matrix;
- blockers;
- bounded read-only evidence summary;
- human-readable summary.

`READY` is reserved for passive metadata readiness. `PASS` is a terminal execution receipt from a governed backend only. A PASS result cannot contain blockers. Missing Project DNA/mobile intent/backend remains explicit `BLOCKED`; the workspace never manufactures success.

The CLI emits this JSON representation. Exit code `0` is used only for `READY`/`PASS`, `2` for blocked/failed outcomes, and `130` for cancellation.

## KodeStudio surface

The KodeStudio page contains:

- Project / Platforms / Source / Release channel / Signing intent / Workspace state / Blockers;
- a read-only JSON evidence and capability viewer;
- separate Refresh, Scaffold, Build, Test, Package, DeviceLab, Compliance and Release controls;
- a dedicated protected-operation Cancel control.

The initial page render calls only passive status. Action controls call structured service intents. No editable command/credential/evidence widget exists.

## Localization and accessibility

R13.16 adds a dedicated source catalog plus `qps-ploc` pseudo-localization using the existing `KodeLocalization` authority. Unsupported locales truthfully fall back to source English instead of inventing translations.

Interactive controls use KodeStudio `mark_accessible` metadata. The evidence control is explicitly read-only and carries an accessibility description explaining that reported status is data and cannot be edited into PASS.

## No new real-tool seam

R13.16 introduces no new external runtime/tool/provider seam. Existing Android, Apple, DeviceLab, release, diagnostics and compliance implementations remain authoritative. Therefore no new platform workflow or manual collector is required by this subdivision; standard R0 Repository Guard, full Python Core and KodeStudio UI Smoke exact-head gates are the required acceptance gates unless implementation changes reveal an affected existing platform regression requiring an additional re-gate.

## Recovery rule

Any failure must be corrected on the same dedicated branch. If implementation bytes change after an accepted candidate gate, all required exact-head gates are rerun. After final end synchronization, PR merge uses `expected_head_sha`, followed by exactly one continuity-only normalization and fresh R0 + Python Core + UI Smoke before R13.17 may start.
