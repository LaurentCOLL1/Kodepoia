# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. R5.1 à R5.5 sont **ACCEPTED AND MERGED**. **R5.6 est IN PROGRESS sur PR #28, branche `agent/r5-6-governed-acceptance`. Deux probes matériels ont donné 4/5 : seul `engine_version` échoue. Le second probe est décisif : le Godot Steam 4.7.2 répond en 0,44 s lorsqu’il est lancé directement par PowerShell, mais l’appel Python/ProcessSandbox reste bloqué jusqu’au timeout 90 s (`timed_out=True`). Ne plus augmenter le timeout. Le blocker est le contexte de lancement Windows. Un diagnostic borné à six variantes de `Godot --version` est prêt et son checkpoint fonctionnel `4023a7217d647a1be14358496fc74e9c37a6b9b4` est CI-accepté. Les commits ultérieurs peuvent être documentation/continuité seulement : toujours `git pull` le head courant, ne jamais reset vers le checkpoint. Prochaine action : exécuter `scripts/r5_diagnose_godot_process.ps1`, puis fournir `.kodepoia/benchmarks/r5-godot-process-diagnostic.json`.** Ne pas relancer le probe R5, ne pas lancer l’acceptation complète, ne pas fusionner PR #28 et ne pas commencer R6 avant analyse de ce diagnostic.

## Source de vérité

- Dépôt : `LaurentCOLL1/Kodepoia`.
- Visibilité GitHub : PUBLIC volontairement.
- Architecture : v1.0 gelée.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local acceptance passed.
- R4 : COMPLETE — final governed orchestration acceptance passed.
- R5 : IN PROGRESS.
- R5.1 : ACCEPTED AND MERGED, PR #22.
- R5.2 : ACCEPTED AND MERGED, PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`.
- R5.3 : ACCEPTED AND MERGED, PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`.
- R5.4 : ACCEPTED AND MERGED, PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`.
- R5.5 : ACCEPTED AND MERGED, PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`.
- R5.6 : IMPLEMENTED / HARDWARE ACCEPTANCE BLOCKED / PROCESS-LAUNCH DIAGNOSTIC PENDING.
- Active branch: `agent/r5-6-governed-acceptance`.
- Active PR: #28, OPEN, DO NOT MERGE YET.
- R6 : NOT STARTED.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not be routed to Granite.

## Architecture boundary

R4 provides WorkspaceBoundary, ProcessSandbox/global kill switch, structured Tool API, LSP, DAP, code graphs, Guardian/Permissions/SafeChange/Audit and governed orchestration. KodeGodot must not bypass these layers.

R5.6 uses `KodeGodotExecutor`, Guardian/PermissionSet, SafeChange snapshots and AuditLog. Godot LSP/DAP/debug remain loopback-only. Defaults: LSP 6005, DAP 6006, debug 6007, all distinct, range 1024–49151.

## Hardware environment

- Python `3.12.4`;
- Windows 11 build `26220`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- ports `6005/6006/6007`.

## Probe #1

4/5 PASS:
- project inspect PASS;
- scene parse PASS;
- GDScript inspect PASS;
- export presets PASS;
- engine version FAIL at ~15.03 s.

Hardening applied:
- version timeout 90 s;
- explicit timeout/cancel diagnostics;
- GDScript check 120 s;
- bounded larger smoke/benchmark/capture/service windows;
- bounded non-secret Windows/user-data environment inheritance;
- regression test against arbitrary secret env leakage;
- direct PowerShell version timing.

Hardening checkpoint `45dc35243a51a5c67830a01f70517a1233a9dac7` was fully green: Guard `32536200325`, Python Core `32536200334` Windows+Ubuntu, UI `32536200352`.

## Probe #2 — decisive

Direct PowerShell:

```text
Godot ver. : 4.7.2.stable.steam.ed1daf0bf (0.44 s direct startup)
```

Sandboxed version:
- ~90.031 s;
- `timed_out=True`;
- `cancelled=False`;
- empty stderr;
- overall 4/5 again.

Therefore Godot is not merely slow. **Do not raise the timeout again.** The blocker is Python/Windows launch context.

Hypotheses to isolate:
1. cwd / automatic project detection;
2. sanitized environment;
3. Python redirected stdout/stderr vs Steam Windows Godot GUI-subsystem behavior;
4. ProcessSandbox-specific polling/kill-switch behavior if equivalent direct Python case passes.

Web/upstream facts used:
- Godot CLI defines `--version` as displaying the version string;
- project path behavior depends on cwd/`--path`;
- Godot Windows code includes special parent-console/stdout/stderr redirection handling;
- Godot Windows issues document differences when processes are launched programmatically with redirected output.

## Process-launch diagnostic — current gate

Files:
- `src/kodepoia/kodegodot/process_diagnostic.py`;
- `tests/test_r5_process_diagnostic.py`;
- `scripts/r5_diagnose_godot_process.ps1`.

Evidence:

```text
.kodepoia/benchmarks/r5-godot-process-diagnostic.json
```

Safety:
- fixed `Godot --version` only;
- no arbitrary args;
- six cases;
- 8-second default timeout per case, bounded 2–30 s;
- no environment keys or values stored;
- no user project mutation.

Cases:
1. `inherited_repo_pipe`;
2. `inherited_project_pipe`;
3. `sanitized_empty_pipe`;
4. `sanitized_project_pipe`;
5. `sanitized_project_file`;
6. `process_sandbox_project`.

Functional checkpoint `4023a7217d647a1be14358496fc74e9c37a6b9b4` CI:
- Guard `32537407769` SUCCESS;
- Python Core `32537407754` SUCCESS Windows + Ubuntu including diagnostic tests/helper syntax;
- UI Smoke `32537407790` SUCCESS Windows.

Interpretation:
- repo inherited PASS + project inherited FAIL → cwd/project detection;
- inherited PASS + sanitized FAIL → env allowlist;
- sanitized project pipe FAIL + sanitized project file PASS → redirected-pipe/console interaction;
- inherited Python cases FAIL while direct PowerShell succeeds → Python/Windows console-subsystem interaction;
- actual sandbox differs from equivalent sanitized pipe → sandbox loop/kill-switch.

## Next manual operation

Synchronize current branch:

```powershell
cd M:\Kodepoia
git fetch --all --prune
git switch agent/r5-6-governed-acceptance
git pull
git branch --show-current
git status
git log -1 --oneline
```

If needed:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run only:

```powershell
.\scripts\r5_diagnose_godot_process.ps1 `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

Send:

```text
M:\Kodepoia\.kodepoia\benchmarks\r5-godot-process-diagnostic.json
```

Preferably also paste the compact summary.

Do NOT rerun normal R5 probe yet, do NOT run full acceptance, do NOT increase timeouts, do NOT copy whole environment, do NOT run as Administrator, do NOT disconnect drives as a workaround, do NOT weaken security layers, do NOT merge PR #28, do NOT start R6.

## R5 completion rule

R5 can become COMPLETE only after the launch blocker is safely fixed, a new probe passes 5/5, full acceptance reports `probe_only=false`, `acceptance_completed=true`, `summary.failed=0`, all real Godot/LSP/DAP/export/audit steps pass, final PR #28 CI is green, PR #28 is merged and `main` is verified.

## User operational preference — permanent

Whenever the user must intervene, explain why, prerequisites, exact commands/actions, expected result, error recovery, what to send back, and what must not be done yet. Do not ask the user to repeat known information.

## Permanent rules

Update continuity in the same work cycle for phase/PR/acceptance/prerequisite changes. Never declare COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional. Do not return to R4 except for a demonstrated regression or ADR-worthy architecture change. Do not begin R6 before R5 completion.
