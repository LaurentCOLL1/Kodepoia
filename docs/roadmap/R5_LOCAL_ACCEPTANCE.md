# R5 — Hardware-local Godot acceptance

R5.6 is not complete until the target Windows workstation passes the governed Godot acceptance and the resulting JSON evidence has been reviewed.

## Current gate

Two non-destructive probes on the target workstation have both returned **4/5**. The four structural inspections pass; `engine_version` alone fails.

Environment:
- Python 3.12.4;
- Windows 11 build 26220;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- ports 6005/6006/6007.

The second probe proves this is not ordinary Godot startup latency:

```text
Direct PowerShell Godot --version : ~0.44 s
Python/ProcessSandbox version     : ~90.03 s, timed_out=True
```

Do not increase the timeout again. Do not rerun the normal R5 probe yet. The current blocker is Windows process-launch context.

## Current required evidence

A bounded diagnostic compares cwd, environment and output-capture modes using only fixed `Godot --version` calls.

Evidence path:

```text
M:\Kodepoia\.kodepoia\benchmarks\r5-godot-process-diagnostic.json
```

Functional checkpoint `4023a7217d647a1be14358496fc74e9c37a6b9b4` is CI accepted:
- Repository Guard `32537407769` SUCCESS;
- Python Core `32537407754` SUCCESS Windows + Ubuntu, including diagnostic tests and PowerShell syntax;
- KodeStudio UI Smoke `32537407790` SUCCESS Windows.

Later docs/continuity commits may advance the branch. Always pull the current remote head; never reset backward to the checkpoint.

## 1. Synchronize branch

```powershell
cd M:\Kodepoia
git fetch --all --prune
git switch agent/r5-6-governed-acceptance
git pull
```

Verify:

```powershell
git branch --show-current
git status
git log -1 --oneline
```

Expected branch:

```text
agent/r5-6-governed-acceptance
```

If `git pull` is blocked by local modifications to tracked files, do not use `git reset --hard`; send `git status` for review.

## 2. Activate Python environment if needed

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current process:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Do not change machine-wide execution policy.

If `.venv` is absent:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,code]"
```

## 3. Run only the process-launch diagnostic

```powershell
.\scripts\r5_diagnose_godot_process.ps1 `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

The helper:
- launches only fixed `Godot --version`;
- accepts no arbitrary Godot flags;
- uses six controlled cases;
- caps each case at 8 seconds by default;
- stores no environment keys or values;
- does not modify a user project.

Cases:
1. `inherited_repo_pipe` — inherited environment, repo cwd, captured pipes;
2. `inherited_project_pipe` — inherited environment, acceptance-project cwd, captured pipes;
3. `sanitized_empty_pipe` — sanitized environment, empty cwd, captured pipes;
4. `sanitized_project_pipe` — sanitized environment, project cwd, captured pipes;
5. `sanitized_project_file` — sanitized environment, project cwd, temporary files instead of pipes;
6. `process_sandbox_project` — actual ProcessSandbox.

## Interpretation

- repo inherited PASS + project inherited FAIL → cwd/project detection;
- inherited PASS + sanitized FAIL → environment allowlist;
- sanitized project pipe FAIL + sanitized project file PASS → Windows redirected-pipe/console interaction;
- inherited Python cases FAIL while direct PowerShell succeeds → Python child-process/Windows console-subsystem behavior;
- sandbox differs from equivalent sanitized project pipe → ProcessSandbox polling/kill-switch layer.

## What to send back

Upload:

```text
M:\Kodepoia\.kodepoia\benchmarks\r5-godot-process-diagnostic.json
```

Preferably also paste the compact PowerShell summary.

If the helper fails before producing JSON, send the complete PowerShell output.

## Normal probe — blocked until diagnostic review

Do not run this yet:

```powershell
.\scripts\r5_accept_local.ps1 -ProbeOnly -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

After a minimal safe process-launch fix is implemented and CI accepted, the normal probe will be run again. It must pass 5/5 before full acceptance is authorized.

## Full hardware acceptance — not authorized yet

Eventually the full acceptance must prove:
- Godot 4.7.x version;
- project/scene/GDScript inspection;
- real `--check-only`;
- import;
- smoke and benchmark;
- AVI capture;
- governed scene mutation + snapshot;
- real loopback LSP/DAP/debug;
- Windows Desktop release export;
- audit hash-chain verification.

Normal full evidence remains:

```text
.kodepoia/benchmarks/r5-local-acceptance.json
```

A completion-eligible report must have `probe_only=false`, `acceptance_completed=true`, `summary.failed=0`, every step passing, final PR #28 CI green, PR merged and `main` verified.

## Do not do yet

- do not rerun the normal R5 probe;
- do not run full acceptance;
- do not increase Godot timeouts;
- do not copy the full parent environment into ProcessSandbox;
- do not run Godot as Administrator to force a pass;
- do not disconnect drives/network mappings as a workaround;
- do not weaken Guardian, PermissionSet, SafeChange, ProcessSandbox or Audit;
- do not merge PR #28;
- do not mark R5 COMPLETE;
- do not start R6.
