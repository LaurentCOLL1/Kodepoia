# R5 — KodeGodot 4.7.x — Status

**Phase:** R5  
**Status:** IN PROGRESS — R5.1–R5.5 ACCEPTED AND MERGED; R5.6 IMPLEMENTED / PROCESS-SANDBOX FIX CI ACCEPTED / PROBE RERUN PENDING  
**Started:** 2026-08-21

R4 remains COMPLETE and is not reopened. R6 is NOT STARTED and must not begin before R5 hardware-local acceptance is reviewed and R5.6 is merged.

## Acceptance subdivisions

1. **R5.1 — Engine/project foundation** — ACCEPTED AND MERGED (PR #22).
2. **R5.2 — Scene/resource intelligence** — ACCEPTED AND MERGED (PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`).
3. **R5.3 — GDScript + Godot LSP/DAP specialization** — ACCEPTED AND MERGED (PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`).
4. **R5.4 — 2D/3D domain intelligence and safe edits** — ACCEPTED AND MERGED (PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`).
5. **R5.5 — Headless automation/import/export/capture/benchmarks** — ACCEPTED AND MERGED (PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`).
6. **R5.6 — Governed orchestration + real Godot acceptance** — IMPLEMENTED; CI accepted; hardware acceptance pending a new 5/5 probe after the ProcessSandbox fix.

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
- CI syntax validation and regression coverage for permissions, snapshots, audit, schemas, loopback command construction, orchestration, fixture generation and ProcessSandbox pipe draining.

## Target workstation

- Python 3.12.4;
- Windows 11 build 26220;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- ports 6005/6006/6007.

## Hardware evidence so far

Probe #1: **4/5 PASS**. Four structural checks passed; `engine_version` failed at ~15.03 s.

Probe #2: **4/5 PASS** again. Direct PowerShell `Godot --version` took ~0.44 s, while the ProcessSandbox call timed out at ~90 s. Increasing the timeout again was therefore rejected.

Bounded process diagnostic: **5/6 PASS**, with a decisive isolation result:

```text
inherited_repo_pipe          PASS ~0.44 s
inherited_project_pipe       PASS ~0.06 s
sanitized_empty_pipe         PASS ~0.09 s
sanitized_project_pipe       PASS ~0.06 s
sanitized_project_file       PASS ~0.09 s
process_sandbox_project      FAIL 8.02 s, timed_out=True
```

The failing sandbox case had already captured the correct stdout `4.7.2.stable.steam.ed1daf0bf` before timeout. Therefore cwd, sanitized environment and stdout/stderr redirection are exonerated. The defect was inside `ProcessSandbox.run()`.

## Root cause and fix

Old `ProcessSandbox.run()` waited on `process.poll()` before calling `process.communicate()`. With `stdout=PIPE` and `stderr=PIPE`, this can deadlock when the child is blocked on pipe backpressure. Python's subprocess contract recommends `communicate()` to drain stdout/stderr while waiting.

Fix:
- replace the manual `poll()` loop with `process.communicate(timeout=...)`;
- on `TimeoutExpired`, stop through the existing kill switch and call `communicate()` again to drain remaining output;
- retain global kill-switch registration for the whole operation, so an asynchronous kill-switch trigger still terminates the active process;
- preserve `timeout < 0` as an unbounded wait;
- remove the now-unused polling sleep dependency.

Regression test:
- a child writes 512 KiB to stdout and 512 KiB to stderr;
- sandbox must finish with rc=0, no timeout/cancel, and both complete payloads;
- this test reproduces the class of pipe-backpressure deadlock independently of Godot.

Functional fix checkpoint `c6ec8f25b8447c68f644ddf7d05aef9995e41861`:
- Repository Guard `32539678111` — SUCCESS;
- Python Core `32539678095` — SUCCESS Windows + Ubuntu, including the new pipe-backpressure test and PowerShell syntax validation;
- KodeStudio UI Smoke `32539678096` — SUCCESS Windows.

Current documentation/continuity commits may be newer than this functional checkpoint; always `git pull` the current branch head and never reset backward to a checkpoint.

## Next gate

The process diagnostic has served its purpose. **Do not rerun it unless a later regression requires it.**

The next and only authorized local action is a fresh normal probe:

```powershell
.\scripts\r5_accept_local.ps1 -ProbeOnly `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

Expected gate:
- `engine_version` PASS;
- overall `Passed: 5/5`, `Failed: 0`;
- JSON still has `probe_only=true` and `acceptance_completed=false` because this is only the probe.

Do **not** run full acceptance until this new 5/5 probe has been reviewed.

## Completion rule

R5 is **not COMPLETE** until:
- the new probe passes 5/5;
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
