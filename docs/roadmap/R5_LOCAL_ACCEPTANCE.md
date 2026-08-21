# R5 — Hardware-local Godot acceptance

R5.6 is not complete until the target Windows workstation passes the governed Godot acceptance and the resulting JSON evidence has been reviewed.

## Current state — diagnostic gate

Two non-destructive R5 probes have been run on the target workstation.

Environment:
- Python 3.12.4;
- Windows 11 build 26220;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- default ports LSP 6005 / DAP 6006 / debug 6007.

Both probes returned **4/5**: `project_inspect`, `scene_parse`, `gdscript_inspect` and `export_presets` pass; `engine_version` fails.

The second probe is decisive:
- direct PowerShell `Godot --version`: about **0.44 s**;
- Python/ProcessSandbox version call: about **90.03 s**, then `timed_out=True`, `cancelled=False`, empty stderr.

Therefore **do not increase the timeout again** and **do not run another identical R5 probe yet**. The remaining blocker is Windows process-launch context: cwd/project detection, sanitized environment, redirected stdio, or ProcessSandbox-specific polling/kill-switch behavior.

A bounded diagnostic now isolates those variables.

## Why local acceptance is mandatory

GitHub CI validates Kodepoia's Python code, PowerShell syntax, safety boundaries and deterministic command construction, but it cannot prove the target workstation can run its real Godot build, native LSP/DAP services, capture, debug and export workflow.

The normal acceptance fixture is disposable:

```text
.kodepoia/r5-acceptance/project
```

Normal acceptance evidence is:

```text
.kodepoia/benchmarks/r5-local-acceptance.json
```

The new process diagnostic evidence is:

```text
.kodepoia/benchmarks/r5-godot-process-diagnostic.json
```

All are local runtime state ignored by Git.

## Required source state

Required branch:

```text
agent/r5-6-governed-acceptance
```

PR #28 remains open and must not be merged until final hardware acceptance succeeds.

The process diagnostic functional checkpoint `4023a7217d647a1be14358496fc74e9c37a6b9b4` is CI accepted:
- Repository Guard `32537407769` SUCCESS;
- Python Core `32537407754` SUCCESS Windows + Ubuntu, including diagnostic tests and PowerShell syntax;
- KodeStudio UI Smoke `32537407790` SUCCESS Windows.

Later documentation/continuity commits may advance the branch head; always `git pull` current remote branch rather than resetting backward to a checkpoint.

## 1. Synchronize the branch

PowerShell:

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

Do not continue from another branch.

## 2. Activate Python environment if needed

If `.venv` already exists:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation only for the current process:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Do not weaken machine-wide execution policy.

If `.venv` does not exist:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,code]"
```

## 3. Current required action — process-launch diagnostic

Run **only**:

```powershell
.\scripts\r5_diagnose_godot_process.ps1 `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

The helper runs only fixed `Godot --version` commands. It does not accept arbitrary Godot arguments and does not modify a user project.

Each case is capped at 8 seconds by default. The diagnostic compares:

1. `inherited_repo_pipe` — full inherited environment, repository cwd, captured pipes;
2. `inherited_project_pipe` — full inherited environment, acceptance-project cwd, captured pipes;
3. `sanitized_empty_pipe` — sanitized environment, empty cwd, captured pipes;
4. `sanitized_project_pipe` — sanitized environment, project cwd, captured pipes;
5. `sanitized_project_file` — sanitized environment, project cwd, stdout/stderr redirected to temporary files instead of pipes;
6. `process_sandbox_project` — actual ProcessSandbox behavior.

The report deliberately does **not** store environment keys or values.

Expected evidence path:

```text
M:\Kodepoia\.kodepoia\benchmarks\r5-godot-process-diagnostic.json
```

Send that JSON back for review, preferably together with the compact PowerShell summary.

### How the result will be interpreted

- `inherited_repo_pipe` PASS but `inherited_project_pipe` FAIL → cwd / automatic project detection is implicated.
- inherited cases PASS but sanitized cases FAIL → environment allowlist is implicated.
- `sanitized_project_pipe` FAIL but `sanitized_project_file` PASS → Windows redirected-pipe/console interaction is implicated.
- Python inherited cases FAIL while direct PowerShell succeeds → Python child-process / Windows console-subsystem behavior is implicated.
- `process_sandbox_project` differs from equivalent sanitized project pipe → ProcessSandbox polling/kill-switch layer is implicated.

Do not try to correct the environment manually before this matrix is reviewed; its purpose is to isolate the minimal safe fix.

## 4. R5 probe — blocked until diagnostic review

Do **not** rerun this yet:

```powershell
.\scripts\r5_accept_local.ps1 -ProbeOnly -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

After the process-launch defect is fixed and CI accepted, this probe will be run again. It must reach 5/5 before full acceptance is authorized.

A probe report intentionally has:

```json
"probe_only": true,
"acceptance_completed": false
```

but must also have:

```json
"summary": {
  "failed": 0
}
```

## 5. Full hardware acceptance — not authorized yet

Only after a reviewed 5/5 probe will the complete acceptance be authorized.

It eventually exercises:
1. Godot 4.7.x version verification;
2. project inspection;
3. `.tscn` parsing and domain analysis;
4. GDScript inspection;
5. real `--check-only --script`;
6. real headless `--import`;
7. bounded scene smoke;
8. bounded benchmark;
9. real AVI capture;
10. governed scene mutation with SHA-256 precondition, Guardian, SafeChange snapshot and Audit;
11. loopback LSP/DAP/debug services;
12. real LSP symbols and diagnostics;
13. real DAP initialize/project launch/threads;
14. Windows Desktop release export;
15. audit hash-chain verification.

A real Windows export requires export templates matching the exact Godot 4.7.x build. Do not install or change templates specifically until the earlier acceptance gates pass unless later instructed.

## Acceptance completion rule

R5 is structurally eligible for COMPLETE only when:
- process-launch diagnostic is resolved with a minimal safe fix;
- a new probe passes 5/5;
- final full report has `metadata.phase == "R5-local-acceptance"`;
- `metadata.probe_only == false`;
- `metadata.acceptance_completed == true`;
- `summary.failed == 0`;
- every real acceptance step passes;
- capture and export artifacts are non-empty;
- LSP/DAP succeed;
- governed write creates a snapshot;
- audit hash chain verifies;
- final PR #28 CI is green;
- PR #28 is merged and `main` is verified.

## Do not do yet

- do not rerun the R5 probe until diagnostic review;
- do not run full R5 acceptance;
- do not increase Godot timeouts again;
- do not copy the entire parent environment into ProcessSandbox;
- do not run Godot as Administrator just to force a pass;
- do not disconnect drives/network mappings as a workaround;
- do not weaken Guardian, PermissionSet, SafeChange, ProcessSandbox or Audit;
- do not merge PR #28;
- do not mark R5 COMPLETE;
- do not start R6.
