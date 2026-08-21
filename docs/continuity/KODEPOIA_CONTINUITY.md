# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. R5.1 à R5.5 sont **ACCEPTED AND MERGED**. **R5.6 est IN PROGRESS sur PR #28, branche `agent/r5-6-governed-acceptance`. Deux probes matériels ont donné 4/5 : seul `engine_version` échoue. Le second probe est décisif : le Godot Steam 4.7.2 répond en 0,44 s lorsqu’il est lancé directement par PowerShell, mais l’appel Python/ProcessSandbox reste bloqué jusqu’au timeout 90 s (`timed_out=True`). Ne plus augmenter le timeout. Le blocker est le contexte de lancement Windows. Un diagnostic borné à six variantes de `Godot --version` est maintenant prêt et CI-accepté. Prochaine action : synchroniser la branche et exécuter `scripts/r5_diagnose_godot_process.ps1`, puis fournir `.kodepoia/benchmarks/r5-godot-process-diagnostic.json`.** Ne pas relancer le probe R5, ne pas lancer l’acceptation complète, ne pas fusionner PR #28 et ne pas commencer R6 avant analyse de ce diagnostic.

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

## Permanent architecture boundary

R4 provides WorkspaceBoundary, ProcessSandbox/global kill switch, structured Tool API, LSP, DAP, code graphs, Guardian/Permissions/SafeChange/Audit and governed orchestration. KodeGodot must not bypass these layers.

R5.6 enforces this through `KodeGodotExecutor`, Guardian/PermissionSet, SafeChange snapshots and AuditLog. Godot LSP/DAP/debug services remain fixed to loopback. Default ports are LSP 6005, DAP 6006, debug 6007, all distinct and limited to 1024–49151.

## R5.6 hardware acceptance implementation

Relevant paths:
- acceptance runner: `kodepoia.kodegodot.accept_cli`;
- helper: `scripts/r5_accept_local.ps1`;
- disposable fixture: `.kodepoia/r5-acceptance/project`;
- evidence: `.kodepoia/benchmarks/r5-local-acceptance.json`.

Full R5 acceptance eventually must cover version, project/scene/GDScript inspection, `--check-only`, import, smoke, benchmark, AVI capture, governed scene edit + snapshot, LSP, DAP/debug, Windows export and audit hash-chain verification.

## Hardware environment observed

Target workstation:
- Python `3.12.4`;
- Windows 11 build `26220`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- ports LSP/DAP/debug `6005/6006/6007`.

## Probe #1

Result: 4/5 PASS.
- `project_inspect` PASS;
- `scene_parse` PASS;
- `gdscript_inspect` PASS;
- `export_presets` PASS;
- `engine_version` FAIL at approximately 15.03 s.

Initial response:
- version timeout 15 → 90 s;
- timeout/cancel diagnostics added;
- GDScript check 120 s;
- bounded larger smoke/benchmark/capture/service windows;
- ProcessSandbox preserves only bounded non-secret OS/data-path variables including `APPDATA`, `LOCALAPPDATA`, `USERPROFILE`, home/XDG variables while arbitrary environment variables remain excluded;
- regression test proves arbitrary secret-like variables are not inherited;
- helper measures direct `Godot --version` startup.

That hardening was CI accepted. Important checkpoint `45dc35243a51a5c67830a01f70517a1233a9dac7`:
- Guard `32536200325` SUCCESS;
- Python Core `32536200334` SUCCESS Windows+Ubuntu;
- PowerShell syntax SUCCESS Windows;
- UI Smoke `32536200352` SUCCESS Windows.

## Probe #2 — decisive result

Direct PowerShell:

```text
Godot ver. : 4.7.2.stable.steam.ed1daf0bf (0.44 s direct startup)
```

Sandboxed version operation:
- `elapsed_seconds ≈ 90.031`;
- `timed_out=True`;
- `cancelled=False`;
- `stderr` empty;
- overall still 4/5 PASS.

Therefore the hypothesis “Godot itself simply starts slowly” is rejected as sufficient explanation. **Do not raise the timeout again.** The defect is specific to the Python/ProcessSandbox launch context.

Remaining hypotheses:
1. working directory / automatic project detection;
2. sanitized environment;
3. Windows Python redirected stdout/stderr with the Steam GUI-subsystem Godot executable;
4. if an equivalent direct Python case works, ProcessSandbox polling/kill-switch behavior.

Current web/upstream context:
- Godot CLI docs define `--version` as displaying the version string.
- Project path behavior depends on current working directory and `--path`; `--upwards` searches parents.
- Godot Windows code has special parent-console/stdio redirection logic (`AttachConsole`, redirected handle restoration, console wrapper recognition).
- Godot Windows issues document output differences when Godot is launched programmatically with redirected stdout/stderr.

## Bounded process-launch diagnostic — next gate

Implemented to diagnose instead of guessing.

Files:
- `src/kodepoia/kodegodot/process_diagnostic.py`;
- `tests/test_r5_process_diagnostic.py`;
- `scripts/r5_diagnose_godot_process.ps1`.

Evidence:

```text
.kodepoia/benchmarks/r5-godot-process-diagnostic.json
```

Safety properties:
- only launches fixed `Godot --version`;
- no arbitrary arguments;
- six cases only;
- default 8-second timeout per case, bounded 2–30 seconds;
- environment keys and values are not written to the report;
- arbitrary secret-like variables remain excluded from sanitized cases;
- does not modify a user Godot project.

Cases:
1. `inherited_repo_pipe`;
2. `inherited_project_pipe`;
3. `sanitized_empty_pipe`;
4. `sanitized_project_pipe`;
5. `sanitized_project_file`;
6. `process_sandbox_project`.

Diagnostic checkpoint `4023a7217d647a1be14358496fc74e9c37a6b9b4` is CI accepted:
- Repository Guard `32537407769` SUCCESS;
- Python Core `32537407754` SUCCESS Windows + Ubuntu, including diagnostic tests and helper syntax;
- KodeStudio UI Smoke `32537407790` SUCCESS Windows.

Interpretation:
- `inherited_repo_pipe` PASS + `inherited_project_pipe` FAIL → cwd/project detection;
- inherited PASS + sanitized FAIL → environment allowlist;
- `sanitized_project_pipe` FAIL + `sanitized_project_file` PASS → redirected pipe / Windows console interaction;
- Python inherited cases FAIL while direct PowerShell succeeds → Python child-process/Windows console interaction;
- `process_sandbox_project` differs from equivalent sanitized project pipe → ProcessSandbox loop/kill-switch issue.

## Next manual operation

After syncing the current branch:

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

Send back:

```text
M:\Kodepoia\.kodepoia\benchmarks\r5-godot-process-diagnostic.json
```

Preferably also paste the compact PowerShell summary.

Do NOT:
- rerun `r5_accept_local.ps1` yet;
- run full acceptance;
- raise timeouts;
- copy the whole environment into ProcessSandbox;
- run Godot as Administrator just to force the test;
- disconnect drives/network mappings as a workaround;
- weaken Guardian/Permissions/SafeChange/Sandbox/Audit;
- merge PR #28;
- start R6.

## R5 completion rule

R5 can become COMPLETE only after diagnosis is resolved, a new probe passes 5/5, full hardware acceptance reports `probe_only=false`, `acceptance_completed=true`, `summary.failed=0`, all real Godot/LSP/DAP/export/audit steps pass, final PR #28 CI is green, PR #28 is merged and `main` is verified.

## User operational preference — permanent

Whenever the user must personally perform an operation, explain the entire procedure in detail:
- why intervention is necessary;
- prerequisites;
- exact commands/actions;
- expected result;
- error recovery;
- what output/file to send back;
- what must not be done yet.

Do not ask the user to repeat known information.

## Permanent rules

Update continuity in the same work cycle for phase/PR/acceptance/prerequisite changes. Never declare COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional. Do not return to R4 except for a demonstrated regression or ADR-worthy architecture change. Do not begin R6 before R5 completion.
