# R5 — KodeGodot 4.7.x — Status

**Phase:** R5  
**Status:** IN PROGRESS — R5.1–R5.5 ACCEPTED AND MERGED; R5.6 IMPLEMENTED / CI ACCEPTED / HARDWARE PROBE 5/5 ACCEPTED / FULL ACCEPTANCE RETEST PENDING AFTER TWO ROOT-CAUSE FIXES  
**Started:** 2026-08-21

R4 remains COMPLETE and is not reopened. R6 is NOT STARTED and must not begin before R5 hardware-local full acceptance is reviewed, PR #28 is merged and `main` is verified.

## Acceptance subdivisions

1. **R5.1 — Engine/project foundation** — ACCEPTED AND MERGED (PR #22).
2. **R5.2 — Scene/resource intelligence** — ACCEPTED AND MERGED (PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`).
3. **R5.3 — GDScript + Godot LSP/DAP specialization** — ACCEPTED AND MERGED (PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`).
4. **R5.4 — 2D/3D domain intelligence and safe edits** — ACCEPTED AND MERGED (PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`).
5. **R5.5 — Headless automation/import/export/capture/benchmarks** — ACCEPTED AND MERGED (PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`).
6. **R5.6 — Governed orchestration + real Godot acceptance** — IMPLEMENTED; CI accepted; ProcessSandbox `run()` blocker fixed; hardware probe 5/5 accepted; first full acceptance reached 12/19 with two root causes; both fixes are implemented and CI accepted; full hardware-local retest pending.

## R5.6 scope

PR #28 — `R5.6 governed Godot orchestration and local acceptance` — **OPEN / DO NOT MERGE YET**.  
Branch: `agent/r5-6-governed-acceptance`.

Implemented:
- `KodeGodotExecutor` with deterministic per-tool policy;
- `KodeGuardian`, `PermissionSet`, `SafeChange` snapshots and `AuditLog` around Godot Tool API calls;
- explicit additional write permission only for indirect writes (`--import`, export, capture);
- Orchestrator routing for KodeCode + KodeGodot without governed-executor bypass;
- loopback-only Godot services, defaults LSP 6005 / DAP 6006 / debug 6007;
- port range 1024–49151 and distinct-port validation;
- real LSP/DAP initialization with retry rather than dummy TCP readiness;
- disposable local fixture `.kodepoia/r5-acceptance/project`;
- local acceptance CLI and `scripts/r5_accept_local.ps1`;
- local evidence `.kodepoia/benchmarks/r5-local-acceptance.json`;
- bounded process-launch diagnostic `scripts/r5_diagnose_godot_process.ps1`;
- `ProcessSandbox.run()` pipe draining via `communicate(timeout=...)`;
- `ProcessSandbox.spawn_background()` for persistent socket services whose stdio is not a protocol channel;
- Godot service log `.kodepoia/logs/godot-services.log` for bounded startup diagnostics;
- movie capture with a real renderer instead of headless/dummy RenderingServer;
- CI regression coverage for permissions, snapshots, audit, schemas, loopback command construction, orchestration, fixture generation, foreground pipe draining and background-process backpressure.

## Target workstation

- Python 3.12.4;
- Windows 11 build 26220;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- ports 6005/6006/6007.

## Hardware probe — ACCEPTED

After fixing the original `ProcessSandbox.run()` deadlock, the fresh hardware probe generated `2026-08-22T00:28:38.116174+00:00` passed 5/5:

```text
engine_version      PASS  ~0.094 s  4.7.2.stable.steam.ed1daf0bf
project_inspect     PASS
scene_parse         PASS
gdscript_inspect    PASS
export_presets      PASS
summary             5/5 PASS, failed=0
```

Evidence: `.kodepoia/benchmarks/r5-local-acceptance.json` with `probe_only=true`, `acceptance_completed=false`.

## Full hardware acceptance attempt #1 — 12/19 PASS

Full report generated `2026-08-22T01:01:59.706424+00:00`:

Passed:
- engine version;
- project inspection;
- scene parse + 2D domain analysis;
- GDScript inspection + real `--check-only`;
- real project import;
- headless scene smoke;
- 120-frame benchmark (~103.8 effective FPS on the disposable fixture);
- governed scene edit with SafeChange snapshot;
- real Windows release export;
- audit hash-chain verification.

The real export produced `.kodepoia/exports/r5-acceptance.exe`, 109,127,680 bytes.

Failed: 7 steps, but only **two independent root causes**:

### Root cause A — movie capture used a dummy renderer

`capture_movie` crashed inside Godot `dummy/storage/texture_storage.h::texture_2d_get` with Windows exit code `3221225477`.

Kodepoia had combined `--headless` with `--write-movie`. Godot documents that `--headless` selects the headless display/audio drivers and disables normal rendering, while Movie Maker requires actual rendered frames. Fix:
- remove `--headless` only from the Movie Maker command;
- keep `--path`, confined output, bounded frames/FPS/timeout and ProcessSandbox governance;
- keep headless mode for import, smoke, export and other operations where it is appropriate.

### Root cause B — persistent Godot editor services used unread pipes

`services_start` timed out waiting for LSP port 6005. The five later LSP/DAP failures were cascading `Godot editor services are not running` failures, not independent defects.

`GodotEditorServices` communicated with Godot over loopback sockets but launched the persistent editor with `spawn_piped()`, leaving stdout/stderr PIPEs unread. This recreates the same backpressure class previously fixed for foreground `run()`.

Fix:
- add `ProcessSandbox.spawn_background()` using the same command validation, sanitized environment and global kill-switch registration, but stdin/stdout/stderr are `DEVNULL` because socket services do not use stdio as their protocol;
- keep `spawn_piped()` unchanged for genuine stdio protocols;
- start Godot LSP/DAP via `spawn_background()`;
- add official `--log-file .kodepoia/logs/godot-services.log` so service startup remains diagnosable despite DEVNULL;
- on startup failure, include a bounded tail of that log in the raised error.

## Post-attempt functional CI

Functional correction head `6b968d284a5f10195cbe465d5c94208f65c3a94e`:
- Repository Guard `32543313597` — SUCCESS;
- Python Core `32543313587` — SUCCESS Windows + Ubuntu, including PowerShell validation and background-process backpressure regression;
- KodeStudio UI Smoke `32543313595` — SUCCESS Windows.

Regression coverage includes:
- foreground process: 512 KiB stdout + 512 KiB stderr must drain without deadlock;
- background process: 2 MiB stdout + 2 MiB stderr must terminate without pipe backpressure because unused stdio is DEVNULL;
- Movie Maker command must not include `--headless`;
- Godot network services must use `spawn_background()`, loopback-only ports and confined service log.

Current documentation/continuity commits may be newer than this functional checkpoint. Always pull the current branch head; never reset backward to a checkpoint.

## Next gate — full hardware-local acceptance retest

After the current documentation head is CI-green, the next authorized local action is to rerun the full acceptance, without `-ProbeOnly`:

```powershell
.\scripts\r5_accept_local.ps1 `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

Expected final report:
- `probe_only=false`;
- `acceptance_completed=true`;
- `summary.failed=0`;
- movie capture produces a non-empty AVI using a real renderer;
- services start with LSP/DAP initialized;
- LSP symbols/diagnostics and DAP initialize/launch/threads pass;
- governed edit still creates a SafeChange snapshot;
- real Windows release export still produces a non-empty executable;
- audit chain verifies.

If `services_start` still fails, also send:

```text
M:\Kodepoia\.kodepoia\r5-acceptance\project\.kodepoia\logs\godot-services.log
```

Do **not** merge PR #28 even if the retest passes. Final review, final CI, merge and `main` verification remain separate gates. Do not start R6.

## Completion rule

R5 is **not COMPLETE** until:
- full target report has `probe_only=false`, `acceptance_completed=true`, `summary.failed=0`;
- all real Godot version/check/import/smoke/benchmark/capture steps pass;
- governed edit creates SafeChange snapshot;
- real LSP and DAP pass;
- Windows release export produces a non-empty executable;
- audit chain verifies;
- final PR #28 CI is green;
- PR #28 is merged and `main` verified.

Until then:
- PR #28 remains open;
- R5 remains IN PROGRESS;
- R6 remains NOT STARTED.
