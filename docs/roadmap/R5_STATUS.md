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

## Hardware probes

Target workstation:
- Python 3.12.4;
- Windows 11 build 26220;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- ports 6005/6006/6007.

Probe #1: **4/5 PASS**. Four structural checks passed; `engine_version` failed at ~15.03 s.

Hardening after probe #1:
- version timeout 15 → 90 s, kill-switch controlled;
- explicit timeout/cancellation diagnostics;
- GDScript check timeout 120 s;
- bounded larger acceptance windows for smoke/benchmark/capture/services;
- ProcessSandbox retains a bounded set of non-secret desktop path variables while arbitrary parent variables remain excluded;
- regression coverage proves arbitrary secret-like environment variables do not leak;
- PowerShell helper measures direct `Godot --version` startup duration.

Probe #2: **4/5 PASS again**, but decisive:

```text
Direct PowerShell Godot --version : ~0.44 s
Python/ProcessSandbox version     : ~90.03 s -> timed_out=True
cancelled=False, stderr empty
```

Conclusion: “Godot itself is simply slow” is rejected as sufficient explanation. Increasing the timeout again is prohibited because it would mask the defect. The blocker is Windows process-launch context.

Remaining suspects:
1. cwd / automatic project detection;
2. sanitized environment;
3. Python Windows stdout/stderr capture / GUI-subsystem interaction;
4. only if equivalent direct Python cases work, ProcessSandbox polling/kill-switch behavior.

Godot's CLI documentation defines `--version` as a direct version-string command and documents cwd/`--path` project behavior. Upstream Windows code has special console/stdio attachment logic, and Godot Windows issues document different output behavior when launched programmatically with redirected streams.

## Bounded process-launch diagnostic

Files:
- `src/kodepoia/kodegodot/process_diagnostic.py`;
- `tests/test_r5_process_diagnostic.py`;
- `scripts/r5_diagnose_godot_process.ps1`;
- evidence `.kodepoia/benchmarks/r5-godot-process-diagnostic.json`.

Safety:
- fixed `Godot --version` only;
- no arbitrary Godot args;
- no environment keys/values persisted;
- default 8-second timeout per case, bounded 2–30 s;
- no user project mutation.

Cases:
1. `inherited_repo_pipe`;
2. `inherited_project_pipe`;
3. `sanitized_empty_pipe`;
4. `sanitized_project_pipe`;
5. `sanitized_project_file`;
6. `process_sandbox_project`.

Diagnostic functional checkpoint `4023a7217d647a1be14358496fc74e9c37a6b9b4`:
- Repository Guard `32537407769` — SUCCESS;
- Python Core `32537407754` — SUCCESS Windows + Ubuntu, including diagnostic tests and helper syntax;
- KodeStudio UI Smoke `32537407790` — SUCCESS Windows.

Current documentation/continuity commits may be newer than this functional checkpoint; use the current remote branch head after `git pull`, never reset backward to the checkpoint.

Interpretation:
- repo PASS + project FAIL ⇒ cwd/project detection;
- inherited PASS + sanitized FAIL ⇒ environment allowlist;
- sanitized project pipe FAIL + sanitized project file PASS ⇒ redirected pipe/Windows console interaction;
- inherited Python cases FAIL while direct PowerShell succeeds ⇒ Python child-process/Windows console interaction;
- sandbox differs from equivalent sanitized pipe case ⇒ ProcessSandbox loop/kill-switch behavior.

## Next gate

Do **not** rerun the normal R5 probe yet. Do **not** run full acceptance.

Next required hardware evidence:

```text
.kodepoia/benchmarks/r5-godot-process-diagnostic.json
```

Run only the dedicated helper documented in `R5_LOCAL_ACCEPTANCE.md` and continuity, then return the JSON for review.

## Completion rule

R5 is **not COMPLETE** until:
- process-launch blocker is resolved with a minimal safe fix;
- a new probe passes 5/5;
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
