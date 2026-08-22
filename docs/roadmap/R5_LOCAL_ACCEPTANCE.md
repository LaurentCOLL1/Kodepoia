# R5 — Hardware-local Godot acceptance

R5.6 is not complete until the target Windows workstation passes the governed Godot acceptance and the resulting JSON evidence has been reviewed.

## Target environment

- Python 3.12.4;
- Windows 11 build 26220;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- loopback ports LSP 6005 / DAP 6006 / debug 6007.

## Accepted probe

After correcting the original foreground `ProcessSandbox.run()` pipe-draining defect, the fresh probe passed **5/5**:

```text
engine_version      PASS  ~0.094 s
project_inspect     PASS
scene_parse         PASS
gdscript_inspect    PASS
export_presets      PASS
summary             5/5 PASS, failed=0
```

The probe report correctly had `probe_only=true` and `acceptance_completed=false`.

## Full acceptance attempt #1 — 12/19

The first complete run generated `2026-08-22T01:01:59.706424+00:00` and reached **12 PASS / 7 FAIL / 19**.

Already proven on the real target workstation:
- Godot 4.7.2 version PASS;
- project/scene/domain/GDScript inspection PASS;
- real GDScript `--check-only` PASS;
- real import PASS;
- headless smoke PASS;
- 120-frame benchmark PASS (~103.8 effective FPS on the disposable fixture);
- governed scene mutation PASS with SafeChange snapshot;
- Windows release export PASS, non-empty artifact `.kodepoia/exports/r5-acceptance.exe` of 109,127,680 bytes;
- audit hash chain PASS.

The seven failures reduce to exactly two independent root causes.

### A. Movie capture used headless/dummy rendering — fixed

Observed failure:
- `capture_movie` returned Windows code `3221225477`;
- Godot crashed in `dummy/storage/texture_storage.h::texture_2d_get`.

Cause: Kodepoia combined `--headless` with `--write-movie`. Godot's headless mode disables normal rendering, while Movie Maker requires actual rendered frames.

Fix:
- remove `--headless` from Movie Maker only;
- retain ProcessSandbox governance, project path, confined output name, bounded frames/FPS/timeout and scene validation;
- continue using headless mode for import, smoke and export where appropriate.

### B. Persistent socket services used unread PIPEs — fixed

Observed failure:
- `services_start` timed out waiting for LSP port 6005;
- the five later LSP/DAP checks failed only because services had not started.

Cause: the long-lived Godot editor used `spawn_piped()` even though LSP/DAP communicate over loopback sockets. Its stdout/stderr were never drained, creating the same pipe-backpressure class previously fixed for foreground `run()`.

Fix:
- add `ProcessSandbox.spawn_background()`;
- reuse command allowlist, sanitized environment, workspace cwd validation and global kill-switch registration;
- set stdin/stdout/stderr to DEVNULL because these background services do not use stdio as a protocol;
- keep `spawn_piped()` unchanged for genuine stdio protocols;
- launch Godot LSP/DAP with `spawn_background()`;
- add `--log-file .kodepoia/logs/godot-services.log` so startup remains diagnosable;
- include a bounded log tail in service-start errors.

## CI checkpoints

Functional head after both fixes: `6b968d284a5f10195cbe465d5c94208f65c3a94e`:
- Repository Guard `32543313597` — SUCCESS;
- Python Core `32543313587` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32543313595` — SUCCESS.

Documentation/continuity head `c6b04c8b79b6566db535e792b0c14745fd48cbb2`:
- Repository Guard `32543456882` — SUCCESS;
- Python Core `32543456800` — SUCCESS Windows + Ubuntu, PowerShell syntax and embedded UI smoke;
- KodeStudio UI Smoke `32543456787` — SUCCESS.

A later documentation commit may make the branch head newer. Always pull the current remote head; never reset backward to a checkpoint.

## Full acceptance retest — authorized

### 1. Synchronize

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

If `git pull` is blocked by tracked local changes, do not use `git reset --hard`; send `git status` for review.

### 2. Activate Python if necessary

```powershell
.\.venv\Scripts\Activate.ps1
```

Do not change machine-wide PowerShell execution policy.

### 3. Run the complete acceptance

Run **without `-ProbeOnly`**:

```powershell
.\scripts\r5_accept_local.ps1 `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

The runner recreates the disposable fixture below:

```text
.kodepoia/r5-acceptance/project
```

and writes evidence to:

```text
.kodepoia/benchmarks/r5-local-acceptance.json
```

## Expected final gate

```text
probe_only=false
acceptance_completed=true
summary.failed=0
Passed 19/19
```

The corrected steps that specifically need confirmation are:
- `capture_movie` PASS and non-empty AVI;
- `services_start` PASS with LSP/DAP initialized;
- `lsp_symbols` PASS;
- `lsp_diagnostics` PASS;
- `dap_initialize` PASS;
- `dap_launch_project` PASS;
- `dap_threads` PASS.

The previously passing checks must remain passing, including real Windows export and audit verification.

## If services still fail

Always send the JSON report and PowerShell summary. Also attach:

```text
M:\Kodepoia\.kodepoia\r5-acceptance\project\.kodepoia\logs\godot-services.log
```

The runner's error should also contain a bounded tail of this file.

## What not to do

- Do not merge PR #28.
- Do not start R6.
- Do not weaken Guardian, PermissionSet, SafeChange, ProcessSandbox or Audit.
- Do not run Godot as Administrator as a workaround.
- Do not increase timeouts without a new diagnostic reason.
- Do not rerun the old process diagnostic unless specifically requested.

R5 can be marked COMPLETE only after a full 19/19 report is reviewed, final PR #28 CI is green, PR #28 is merged and `main` is verified.
