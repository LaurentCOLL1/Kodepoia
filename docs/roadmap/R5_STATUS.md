# R5 — KodeGodot 4.7.x — Status

**Phase:** R5  
**Status:** IN PROGRESS — R5.1–R5.5 ACCEPTED AND MERGED; R5.6 IMPLEMENTED / CI ACCEPTED / HARDWARE PROBE 5/5 ACCEPTED / FULL ACCEPTANCE RETEST AUTHORIZED AFTER TWO ROOT-CAUSE FIXES  
**Started:** 2026-08-21

R4 remains COMPLETE and is not reopened. R6 is NOT STARTED and must not begin before R5 hardware-local full acceptance is reviewed, PR #28 is merged and `main` is verified.

## Acceptance subdivisions

1. **R5.1 — Engine/project foundation** — ACCEPTED AND MERGED (PR #22).
2. **R5.2 — Scene/resource intelligence** — ACCEPTED AND MERGED (PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`).
3. **R5.3 — GDScript + Godot LSP/DAP specialization** — ACCEPTED AND MERGED (PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`).
4. **R5.4 — 2D/3D domain intelligence and safe edits** — ACCEPTED AND MERGED (PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`).
5. **R5.5 — Headless automation/import/export/capture/benchmarks** — ACCEPTED AND MERGED (PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`).
6. **R5.6 — Governed orchestration + real Godot acceptance** — IMPLEMENTED; CI accepted; ProcessSandbox foreground blocker fixed; hardware probe 5/5 accepted; first full acceptance reached 12/19 with two root causes; both fixes are implemented and CI accepted; full hardware-local retest authorized.

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

The post-ProcessSandbox-fix hardware probe passed **5/5**, including Godot 4.7.2 engine version detection in ~0.094 s. Evidence used `probe_only=true`, `acceptance_completed=false` as expected.

## Full hardware acceptance attempt #1 — 12/19 PASS

Full report generated `2026-08-22T01:01:59.706424+00:00`.

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

The 7 failures represent only two root causes:

### A — Movie Maker + headless — fixed

`capture_movie` crashed in Godot `dummy/storage/texture_storage.h::texture_2d_get`, Windows code `3221225477`. Kodepoia had combined `--headless` with `--write-movie`. Movie capture now omits `--headless` so Godot uses a real renderer, while ProcessSandbox, path confinement and frame/FPS/timeout bounds remain.

### B — background editor PIPE backpressure — fixed

`services_start` timed out waiting for LSP port 6005. Five later LSP/DAP failures were cascades because services were not running. The long-lived Godot editor had used `spawn_piped()` even though its protocol is socket-based and the pipes were unread.

Fix:
- `ProcessSandbox.spawn_background()` reuses allowlist, sanitized environment, workspace boundary and global kill-switch registration;
- unused stdin/stdout/stderr use DEVNULL;
- `spawn_piped()` remains for actual stdio protocols;
- Godot services use `spawn_background()`;
- `--log-file .kodepoia/logs/godot-services.log` preserves bounded startup diagnostics.

## CI proof checkpoints

Functional correction checkpoint `6b968d284a5f10195cbe465d5c94208f65c3a94e`:
- Guard `32543313597` SUCCESS;
- Python Core `32543313587` SUCCESS Windows + Ubuntu;
- UI Smoke `32543313595` SUCCESS.

Later green checkpoint `170f0608cabd7810227eb47ed198d68000aeb071`:
- Guard `32543888864` SUCCESS;
- Python Core `32543888938` SUCCESS Windows + Ubuntu, PowerShell syntax and embedded UI smoke;
- UI Smoke `32543888867` SUCCESS.

These SHAs are proof checkpoints only. **Always pull the current remote branch head and never reset backward to a checkpoint.**

## Next gate — full hardware-local acceptance retest

The next authorized local action is to rerun the full acceptance, without `-ProbeOnly`:

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

R5 is **not COMPLETE** until full target report has `probe_only=false`, `acceptance_completed=true`, `summary.failed=0`, all real Godot/LSP/DAP/export/audit steps pass, final PR #28 CI is green, PR #28 is merged and `main` verified.
