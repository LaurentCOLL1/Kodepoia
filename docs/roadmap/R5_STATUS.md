# R5 — KodeGodot 4.7.x — Status

**Phase:** R5  
**Status:** IN PROGRESS — R5.1–R5.5 ACCEPTED AND MERGED; R5.6 IMPLEMENTED / STARTUP-LATENCY FIX CI ACCEPTED / HARDWARE PROBE RE-RUN PENDING  
**Started:** 2026-08-21

R4 remains COMPLETE and is not reopened. R6 is NOT STARTED and must not begin before R5 hardware-local acceptance is reviewed and R5.6 is merged.

## Acceptance subdivisions

1. **R5.1 — Engine/project foundation** — ACCEPTED AND MERGED.
2. **R5.2 — Scene/resource intelligence** — ACCEPTED AND MERGED.
3. **R5.3 — GDScript + Godot LSP/DAP specialization** — ACCEPTED AND MERGED.
4. **R5.4 — 2D/3D domain intelligence and safe edits** — ACCEPTED AND MERGED.
5. **R5.5 — Headless automation/import/export/capture/benchmarks** — ACCEPTED AND MERGED.
6. **R5.6 — Governed orchestration + real Godot acceptance** — IMPLEMENTED; FIRST TARGET-WORKSTATION PROBE EXPOSED A STARTUP-TIMEOUT DEFECT; FIX CI ACCEPTED; PROBE RE-RUN PENDING.

## R5.1 — Engine/project foundation

PR #22 is merged. Delivered the protected `kodepoia.kodegodot` foundation: project inspection, Godot 4.7.x version gate, `ProcessSandbox` integration, named `--check-only`, `--import` and bounded smoke operations, workspace confinement and a structured no-arbitrary-argv Tool API.

## R5.2 — Scene/resource intelligence

PR #24 merged at `7720bfc90951e2180b909004b7fa8320d93a6e27`.

Delivered:
- structural parser for Godot 4 text `.tscn` and `.tres` documents;
- format 3 validation;
- scene/resource descriptors, `ext_resource`, `sub_resource`, nodes and connections;
- string UID/path/ID preservation;
- raw Variant-value preservation without evaluation;
- source-line provenance and declared dependency extraction;
- workspace and document-size bounds;
- structured parse/dependency tools.

Accepted CI after the R5.1 regression test was correctly generalized:
- R0 Repository Guard `32528439136` — SUCCESS;
- Python Core `32528439126` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32528439139` — SUCCESS Windows.

## R5.3 — GDScript + native Godot LSP/DAP

PR #25 merged at `d2641862b98a969b9adfc905f818e01b3d7e4730`.

Delivered:
- lightweight non-executing GDScript structure/typing inspector;
- managed Godot editor service process;
- loopback-only LSP/DAP integration reusing the R4 protocol clients;
- document symbols and diagnostics;
- DAP initialize, pre-registered project launch and thread inspection;
- no model-supplied remote host, program, command, cwd or arbitrary argv surface.

Accepted CI:
- R0 Repository Guard `32528908533` — SUCCESS;
- Python Core `32528908562` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32528908573` — SUCCESS Windows.

## R5.4 — 2D/3D domain intelligence and guarded edits

PR #26 merged at `b81cf430249e341219dcb759cb49f67697c27782`.

Delivered:
- conservative 2D/3D/hybrid scene classification;
- CharacterBody, collision, navigation, TileMap/TileMapLayer, UI, camera, mesh and light awareness;
- warnings for selected structural risks;
- guarded `.tscn` mutation limited to one existing property on one uniquely selected node;
- mandatory SHA-256 stale-write precondition;
- protected-property/multiline/NUL rejection;
- provenance-based single-line atomic write.

Accepted CI:
- R0 Repository Guard `32529333497` — SUCCESS;
- Python Core `32529333471` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32529333485` — SUCCESS Windows.

## R5.5 — Headless automation, export, capture and benchmark

PR #27 merged at `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`.

Delivered:
- non-secret `export_presets.cfg` metadata inspection;
- named release/debug/pack export using existing preset names only;
- generated export confinement to `.kodepoia/exports`;
- bounded AVI capture using Godot movie-writing CLI into `.kodepoia/captures`;
- bounded scene execution benchmark;
- Kodepoia-constructed commands through `ProcessSandbox` only;
- path-free output names and ignored local generated evidence.

Accepted CI:
- R0 Repository Guard `32529677551` — SUCCESS;
- Python Core `32529677569` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32529677534` — SUCCESS Windows.

## R5.6 — Governed orchestration + real Godot acceptance

PR #28 — `R5.6 governed Godot orchestration and local acceptance` — OPEN / DO NOT MERGE YET.  
Branch: `agent/r5-6-governed-acceptance`.

Implemented:
- `KodeGodotExecutor` with deterministic per-tool policy;
- `KodeGuardian`, `PermissionSet`, `SafeChange` snapshot and `AuditLog` enforcement around Godot Tool API calls;
- explicit extra write permissions for Godot operations which write indirectly (`--import`, export and capture);
- Orchestrator aggregation/routing of KodeCode and KodeGodot tools without bypassing their governed executors;
- loopback-only Godot service command with LSP, DAP and project debug server;
- default ports LSP 6005, DAP 6006, debug 6007;
- documented port range enforcement 1024–49151 and distinct-port requirement;
- real LSP/DAP protocol initialization with retry rather than dummy TCP readiness connections;
- disposable hardware-local fixture under `.kodepoia/r5-acceptance/project`;
- dedicated local acceptance CLI and Windows PowerShell helper;
- CI PowerShell syntax validation for both R3 and R5 acceptance helpers;
- regression coverage for permissions, snapshots, audit, schemas, exact loopback command, orchestration routing and fixture generation.

A first R5.6 CI run exposed an obsolete R5.3 regression test which monkeypatched the removed private `_wait_loopback` implementation detail. The test was migrated to the protocol-ready service contract rather than restoring the weaker dummy-TCP design.

Pre-hardware-probe final head `532bb7fedc9519d89778a971c0c457ec8f6c1c2b` was fully green:
- R0 Repository Guard `32533944821` — SUCCESS;
- Python Core `32533944780` — SUCCESS Windows + Ubuntu;
- R5 PowerShell acceptance-runner syntax — SUCCESS Windows;
- embedded KodeStudio UI smoke — SUCCESS Windows;
- standalone KodeStudio UI Smoke `32533944764` — SUCCESS Windows.

### First target-workstation probe — defect exposed

The first real probe was executed on 22 August 2026 with:
- Python 3.12.4;
- Windows 11 build 26220;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- LSP/DAP/debug ports 6005/6006/6007.

Result: **4/5 probe steps passed**. Project inspection, scene parsing, GDScript inspection and export-preset inspection all succeeded. `engine_version` alone failed after approximately `15.03 s` because the sandboxed `--version` invocation hit the old fixed 15-second timeout and was terminated with no stderr.

This strongly matches upstream Godot issue `godotengine/godot#120649`: Godot 4.7 on Windows 11 build 26200-class systems can spend many seconds probing drives, especially disconnected/network drives. Upstream fix `godotengine/godot#121192` was merged to `master` and labeled for possible future 4.7 cherry-pick; Kodepoia therefore must tolerate the affected 4.7.x runtime rather than weakening the version check.

Hardening implemented on PR #28:
- Godot version timeout increased from 15 s to 90 s while remaining kill-switch controlled;
- timeout/cancellation state included in version errors;
- default GDScript check timeout increased to 120 s;
- local acceptance smoke/benchmark/capture/service startup windows enlarged where appropriate;
- `ProcessSandbox` still sanitizes environment variables, but preserves only the bounded non-secret desktop path variables Godot needs (`APPDATA`, `LOCALAPPDATA`, `USERPROFILE`, home/XDG paths) rather than inheriting the whole parent environment;
- regression test proves arbitrary secret-like environment variables remain absent from subprocesses;
- PowerShell helper measures direct `Godot --version` startup duration and validates distinct ports unambiguously.

### Startup-latency fix — CI accepted

Hardened functional/documentation head `25ddef21718eb09d361830259e62fa0e703469f1`:
- R0 Repository Guard `32536038483` — SUCCESS;
- Python Core `32536038479` — SUCCESS Windows + Ubuntu;
- R5 PowerShell acceptance-runner syntax — SUCCESS Windows;
- embedded KodeStudio UI smoke — SUCCESS Windows;
- standalone KodeStudio UI Smoke `32536038474` — SUCCESS Windows.

Next gate: rerun **ProbeOnly only** on the target workstation. Do not run full acceptance until the new probe is reviewed and has zero failed steps.

## Godot 4.7 external contract used by R5.6

Current official Godot documentation confirms:
- `--lsp-port` and `--dap-port` with recommended port range 1024–49151;
- `--debug-server <uri>`, including a loopback TCP URI such as `tcp://127.0.0.1:6007`;
- a running Godot project/editor instance is required for native LSP/DAP workflows;
- common defaults are LSP 6005, DAP 6006 and project debug port 6007;
- CLI export uses named presets from `export_presets.cfg` and actual release export requires matching export templates;
- Windows editor/user data is stored under Godot's normal user data/settings locations, including `%APPDATA%\Godot`.

Kodepoia keeps the host fixed to loopback and never relays arbitrary model-provided engine flags.

## Hardware-local acceptance

Procedure: `docs/roadmap/R5_LOCAL_ACCEPTANCE.md`.

Evidence path:

```text
.kodepoia/benchmarks/r5-local-acceptance.json
```

The full acceptance must prove the actual target workstation can perform version verification, scene/GDScript inspection, `--check-only`, import, smoke, benchmark, AVI capture, governed scene mutation with snapshot, LSP, DAP/project debugging, Windows release export and audit-chain verification.

## Completion rule

R5 is **not COMPLETE** until target-workstation evidence is reviewed and confirms:

- `metadata.phase == "R5-local-acceptance"`;
- `metadata.probe_only == false`;
- `metadata.acceptance_completed == true`;
- `summary.failed == 0`;
- all recorded acceptance steps pass;
- R5.6 final branch CI is green;
- PR #28 is then merged and `main` is verified.

Until then:
- PR #28 remains open;
- R5 remains IN PROGRESS;
- R6 remains NOT STARTED.
