# R5 — KodeGodot 4.7.x — Status

**Phase:** R5  
**Status:** IN PROGRESS — R5.1–R5.5 ACCEPTED AND MERGED; R5.6 IMPLEMENTED / PROCESS-SANDBOX FIX CI ACCEPTED / HARDWARE PROBE 5/5 ACCEPTED / FULL ACCEPTANCE AUTHORIZED  
**Started:** 2026-08-21

R4 remains COMPLETE and is not reopened. R6 is NOT STARTED and must not begin before R5 hardware-local full acceptance is reviewed, PR #28 is merged and `main` is verified.

## Acceptance subdivisions

1. **R5.1 — Engine/project foundation** — ACCEPTED AND MERGED (PR #22).
2. **R5.2 — Scene/resource intelligence** — ACCEPTED AND MERGED (PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`).
3. **R5.3 — GDScript + Godot LSP/DAP specialization** — ACCEPTED AND MERGED (PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`).
4. **R5.4 — 2D/3D domain intelligence and safe edits** — ACCEPTED AND MERGED (PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`).
5. **R5.5 — Headless automation/import/export/capture/benchmarks** — ACCEPTED AND MERGED (PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`).
6. **R5.6 — Governed orchestration + real Godot acceptance** — IMPLEMENTED; CI accepted; ProcessSandbox blocker fixed; fresh hardware probe 5/5 accepted; full hardware-local acceptance authorized and pending.

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

## Hardware evidence

Probe #1: **4/5 PASS**. Four structural checks passed; `engine_version` failed at ~15.03 s.

Probe #2: **4/5 PASS** again. Direct PowerShell `Godot --version` took ~0.44 s, while the ProcessSandbox call timed out at ~90 s. Increasing the timeout again was rejected.

Bounded process diagnostic: **5/6 PASS**, decisively isolating the defect to `ProcessSandbox.run()` because all equivalent direct Python launches passed while the sandbox case timed out after already capturing the correct version string.

ProcessSandbox was corrected to drain stdout/stderr through `communicate(timeout=...)`, stop through the existing kill switch on `TimeoutExpired`, then drain remaining output. A generic 512 KiB stdout + 512 KiB stderr regression test passes on Windows and Ubuntu.

Functional fix checkpoint `c6ec8f25b8447c68f644ddf7d05aef9995e41861`:
- Repository Guard `32539678111` — SUCCESS;
- Python Core `32539678095` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32539678096` — SUCCESS Windows.

Fresh hardware probe after the fix — generated `2026-08-22T00:28:38.116174+00:00`:

```text
engine_version      PASS  ~0.094 s  4.7.2.stable.steam.ed1daf0bf
project_inspect     PASS
scene_parse         PASS
gdscript_inspect    PASS
export_presets      PASS
summary             5/5 PASS, failed=0
```

Evidence: `.kodepoia/benchmarks/r5-local-acceptance.json` with `probe_only=true`, `acceptance_completed=false`, Python 3.12.4, Windows 11 build 26220 and ports 6005/6006/6007.

This closes the ProcessSandbox/hardware-probe gate. The probe result is **ACCEPTED**. R5 itself is not yet COMPLETE because the full hardware-local acceptance has not run.

## Next gate — full hardware-local acceptance

The next and only authorized local action is the full acceptance runner, without `-ProbeOnly`:

```powershell
.\scripts\r5_accept_local.ps1 `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

Prerequisites:
- current branch is `agent/r5-6-governed-acceptance` and is fully pulled;
- Python 3.12+ / project venv available;
- Godot 4.7.x editor executable available at the known path;
- Godot 4.7.x export templates installed, because full acceptance performs a real Windows release export;
- ports 6005/6006/6007 are available and remain loopback-only.

Expected final report:
- `probe_only=false`;
- `acceptance_completed=true`;
- `summary.failed=0`;
- all real Godot version/check/import/smoke/benchmark/capture steps pass;
- governed scene edit creates a SafeChange snapshot;
- services start and real LSP/DAP operations pass;
- Windows release export produces a non-empty executable;
- audit chain verifies.

After the run, send `.kodepoia/benchmarks/r5-local-acceptance.json` and the complete PowerShell summary/output if any step fails.

Do **not** merge PR #28 even if the full acceptance passes. Final review, final CI on the resulting branch head, merge and `main` verification remain separate gates. Do not start R6.

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
