# R5 — Hardware-local Godot acceptance

R5.6 is not complete until this procedure has been executed on the target Windows workstation and the resulting JSON evidence has been reviewed.

## Why local acceptance is mandatory

GitHub CI validates Kodepoia's Python code, PowerShell syntax, safety boundaries and deterministic command construction, but it does not prove the target workstation can actually run the selected Godot 4.7.x binary, import a real project, start the native GDScript LSP/DAP services, capture frames, run a debug session or export a Windows build with the locally installed export templates.

The acceptance runner therefore creates a disposable Godot project under:

```text
.kodepoia/r5-acceptance/project
```

It does not modify a user game project. Local evidence is written to:

```text
.kodepoia/benchmarks/r5-local-acceptance.json
```

Both locations are local runtime state and are ignored by Git.

## Required source state

Do not run R5 acceptance from `main` or from an older R5 branch.

Required branch:

```text
agent/r5-6-governed-acceptance
```

PR #28 must remain open until the report has been reviewed.

## Prerequisites

- Windows target workstation.
- Python 3.12 or newer.
- Current Kodepoia checkout and development dependencies.
- Godot **4.7.x** standard build. Another Godot family is rejected by the helper.
- For the complete acceptance only: matching Godot 4.7.x export templates capable of the `Windows Desktop` export preset.
- TCP loopback ports 6005, 6006 and 6007 available, unless alternate distinct ports in the documented 1024–49151 range are supplied.

The helper never accepts a remote host for LSP/DAP/debugging. The services are constructed against `127.0.0.1` only.

## 1. Synchronize the acceptance branch

From PowerShell:

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

Do not continue from a different branch.

## 2. Activate the Python environment when needed

If `.venv` already exists:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current process only:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Do not weaken the machine-wide PowerShell execution policy.

If the environment does not yet exist:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,code]"
```

## 3. Run the non-destructive preflight

First try:

```powershell
.\scripts\r5_accept_local.ps1 -ProbeOnly
```

If Godot is not on `PATH`, provide its executable explicitly:

```powershell
.\scripts\r5_accept_local.ps1 -ProbeOnly -GodotPath "C:\path\to\Godot_v4.7.x-stable_win64.exe"
```

The PowerShell helper verifies Python 3.12+, the exact R5.6 branch, Godot 4.7.x and the three loopback port bounds before invoking the Python probe.

The probe creates only the disposable acceptance fixture and JSON report. It inspects the engine/project/GDScript/scene/export-preset metadata but does not run the complete import/capture/debug/export sequence.

Expected evidence path:

```text
M:\Kodepoia\.kodepoia\benchmarks\r5-local-acceptance.json
```

A probe report intentionally contains:

```json
"acceptance_completed": false,
"probe_only": true
```

This does not mean the probe failed. It means hardware acceptance has not yet been executed.

## 4. Run the complete hardware acceptance

After a successful probe:

```powershell
.\scripts\r5_accept_local.ps1
```

Or, when Godot is not on `PATH`:

```powershell
.\scripts\r5_accept_local.ps1 -GodotPath "C:\path\to\Godot_v4.7.x-stable_win64.exe"
```

The full acceptance exercises:

1. Godot 4.7.x version verification.
2. Project inspection.
3. `.tscn` parsing and 2D/3D domain analysis.
4. GDScript structural inspection.
5. Real Godot `--check-only --script`.
6. Real headless `--import`.
7. Bounded scene smoke execution.
8. Bounded scene benchmark.
9. Real `--write-movie` AVI capture and artifact verification.
10. Governed scene mutation with SHA-256 precondition, Guardian permission check, SafeChange snapshot and audit entry.
11. Managed Godot editor services using loopback LSP/DAP/debug ports.
12. Real LSP initialize, symbols and diagnostics.
13. Real DAP initialize, pre-registered project launch and thread query.
14. Real Windows Desktop release export and non-empty `.exe` verification.
15. Audit hash-chain verification.

The acceptance fixture is regenerated on each run, so an earlier scene mutation cannot contaminate a later run.

## 5. Export templates

A real Godot CLI export requires matching export templates. If the full run fails on `export_release` with a missing-template error, install the templates for the exact Godot 4.7.x version using Godot's **Editor → Manage Export Templates…** workflow, then rerun the complete acceptance.

Do not install unrelated templates, change Kodepoia source code or weaken export/security checks just to make the test pass.

## 6. Port conflicts

Defaults:

```text
LSP   6005
DAP   6006
DEBUG 6007
```

If another local process owns one of them, choose three distinct ports in 1024–49151, for example:

```powershell
.\scripts\r5_accept_local.ps1 -LspPort 6105 -DapPort 6106 -DebugPort 6107
```

The host remains fixed to loopback; there is no remote-host option.

## 7. Acceptance evidence rule

A report is structurally eligible for R5 completion only when all of the following are true:

- `metadata.phase == "R5-local-acceptance"`
- `metadata.probe_only == false`
- `metadata.acceptance_completed == true`
- `summary.failed == 0`
- every recorded step passed
- real capture and Windows export artifacts were produced
- LSP and DAP initialization succeeded
- governed write produced a snapshot
- audit hash chain verified

Even then, do not edit `R5_STATUS.md` or merge PR #28 manually. The report must first be reviewed against the acceptance criteria.

## What to send back

After the probe or complete run, provide either:

- `.kodepoia/benchmarks/r5-local-acceptance.json`, preferably as a file; or
- the complete PowerShell output if the helper stopped before a usable report was produced.

For a failure, include both when available.

## Do not do yet

Until target-workstation evidence has been reviewed:

- do not merge PR #28;
- do not mark R5 COMPLETE;
- do not edit `R5_STATUS.md` manually;
- do not start R6;
- do not expose LSP/DAP/debug services to a non-loopback address;
- do not weaken Guardian, PermissionSet, SafeChange, ProcessSandbox or Audit controls to make acceptance pass.
