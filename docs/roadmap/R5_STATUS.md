# R5 — KodeGodot 4.7.x — Status

**Phase:** R5  
**Status:** IN PROGRESS — R5.1–R5.5 ACCEPTED AND MERGED; R5.6 IMPLEMENTED / PROCESS-LAUNCH DIAGNOSTIC PENDING  
**Started:** 2026-08-21

R4 remains COMPLETE and is not reopened. R6 is NOT STARTED and must not begin before R5 hardware-local acceptance is reviewed and R5.6 is merged.

## Acceptance subdivisions

1. **R5.1 — Engine/project foundation** — ACCEPTED AND MERGED (PR #22).
2. **R5.2 — Scene/resource intelligence** — ACCEPTED AND MERGED (PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`).
3. **R5.3 — GDScript + Godot LSP/DAP specialization** — ACCEPTED AND MERGED (PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`).
4. **R5.4 — 2D/3D domain intelligence and safe edits** — ACCEPTED AND MERGED (PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`).
5. **R5.5 — Headless automation/import/export/capture/benchmarks** — ACCEPTED AND MERGED (PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`).
6. **R5.6 — Governed orchestration + real Godot acceptance** — IMPLEMENTED; hardware acceptance BLOCKED on Windows process-launch behavior; bounded diagnostic ready.

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
- CI syntax validation and regression coverage for permissions, snapshots, audit, schemas, loopback command construction, orchestration and fixture generation.

## CI before hardware probes

Pre-probe checkpoint `532bb7fedc9519d89778a971c0c457ec8f6c1c2b`:
- Repository Guard `32533944821` — SUCCESS;
- Python Core `32533944780` — SUCCESS Windows + Ubuntu;
- PowerShell R5 syntax — SUCCESS Windows;
- embedded UI smoke — SUCCESS Windows;
- standalone UI Smoke `32533944764` — SUCCESS Windows.

## Hardware probe #1 — 22 August 2026

Target workstation:
- Python 3.12.4;
- Windows 11 build 26220;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- ports 6005/6006/6007.

Result: **4/5 PASS**. `project_inspect`, `scene_parse`, `gdscript_inspect` and `export_presets` passed. `engine_version` alone failed after about 15.03 s.

Initial hardening after probe #1:
- version timeout 15 → 90 s, kill-switch controlled;
- explicit timeout/cancellation diagnostics;
- GDScript check timeout 120 s;
- bounded larger acceptance windows for smoke/benchmark/capture/services;
- ProcessSandbox retains a bounded set of non-secret desktop path variables (`APPDATA`, `LOCALAPPDATA`, `USERPROFILE`, home/XDG paths) while arbitrary parent variables remain excluded;
- regression coverage proves arbitrary secret-like environment variables do not leak;
- PowerShell helper measures direct `Godot --version` startup duration.

That hardening was fully CI-accepted, including checkpoint `45dc35243a51a5c67830a01f70517a1233a9dac7`:
- Repository Guard `32536200325` — SUCCESS;
- Python Core `32536200334` — SUCCESS Windows + Ubuntu;
- PowerShell syntax — SUCCESS Windows;
- standalone UI Smoke `32536200352` — SUCCESS Windows.

## Hardware probe #2 — decisive evidence

The hardened probe was rerun on the same workstation.

Direct PowerShell invocation:

```text
Godot ver. : 4.7.2.stable.steam.ed1daf0bf (0.44 s direct startup)
```

Sandboxed `GodotRuntime.version()`:
- elapsed: approximately 90.03 s;
- `timed_out=True`;
- `cancelled=False`;
- `stderr` empty;
- summary remains **4/5 PASS**.

Conclusion: the first hypothesis, “Godot 4.7.2 itself simply needs more startup time”, is **rejected as sufficient explanation**. The same executable returns in ~0.44 s when invoked directly but does not terminate through the current Python/ProcessSandbox launch path even at 90 s. Increasing the timeout again is prohibited because it would mask the defect.

The blocker is now isolated to **Windows process-launch context**. Remaining suspects are:
1. current working directory / project detection;
2. sanitized environment;
3. Python Windows stdout/stderr capture / GUI-subsystem interaction;
4. only if the previous cases match, ProcessSandbox polling/kill-switch behavior itself.

Godot documentation confirms `--version` is a direct version-string operation and that project path behavior depends on current directory/`--path`. Upstream Windows code also has special console/stdio attachment logic, and historical Godot Windows issues document different stdout behavior when Godot is launched programmatically with redirected streams.

## R5.6 bounded process diagnostic

A non-destructive diagnostic has been added. It runs **only fixed `Godot --version`** and records no environment keys or values.

Files:
- Python: `src/kodepoia/kodegodot/process_diagnostic.py`;
- Windows helper: `scripts/r5_diagnose_godot_process.ps1`;
- tests: `tests/test_r5_process_diagnostic.py`;
- evidence: `.kodepoia/benchmarks/r5-godot-process-diagnostic.json`.

Six cases are compared, each with a bounded timeout:
1. `inherited_repo_pipe`;
2. `inherited_project_pipe`;
3. `sanitized_empty_pipe`;
4. `sanitized_project_pipe`;
5. `sanitized_project_file`;
6. `process_sandbox_project`.

Diagnostic functional checkpoint `4023a7217d647a1be14358496fc74e9c37a6b9b4`:
- Repository Guard `32537407769` — SUCCESS;
- Python Core `32537407754` — SUCCESS Windows + Ubuntu, including diagnostic tests and PowerShell syntax;
- KodeStudio UI Smoke `32537407790` — SUCCESS Windows.

Interpretation:
- repo PASS + project FAIL ⇒ working-directory/project-detection problem;
- inherited PASS + sanitized FAIL ⇒ environment allowlist problem;
- sanitized project pipe FAIL + sanitized project file PASS ⇒ redirected-pipe/Windows console interaction;
- inherited Python cases FAIL while PowerShell direct succeeds ⇒ Python child-process/Windows console behavior;
- sandbox differs from equivalent sanitized pipe case ⇒ ProcessSandbox loop/kill-switch behavior.

## Next gate

Do **not** rerun the full R5 probe yet. Do **not** run full acceptance.

Next required hardware evidence is:

```text
.kodepoia/benchmarks/r5-godot-process-diagnostic.json
```

Procedure is documented in `docs/roadmap/R5_LOCAL_ACCEPTANCE.md` and continuity.

## Completion rule

R5 is **not COMPLETE** until reviewed target-workstation evidence proves:
- `metadata.phase == "R5-local-acceptance"`;
- `metadata.probe_only == false`;
- `metadata.acceptance_completed == true`;
- `summary.failed == 0`;
- all real Godot version/check/import/smoke/benchmark/capture steps pass;
- governed edit creates SafeChange snapshot;
- real LSP and DAP pass;
- Windows release export produces non-empty executable;
- audit chain verifies;
- final PR #28 CI is green;
- PR #28 is merged and `main` verified.

Until then:
- PR #28 remains open;
- R5 remains IN PROGRESS;
- R6 remains NOT STARTED.
