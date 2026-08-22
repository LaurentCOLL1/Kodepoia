# R6.4 — KodeVisualQA foundation — Acceptance

**Status:** IN PROGRESS — CI AND REQUIRED HARDWARE-LOCAL EVIDENCE PENDING  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** REQUIRED

R6.4 MUST NOT be marked COMPLETE or merged until both the final-head GitHub CI and the required real-render Windows/Godot evidence pass.

## Implementation acceptance matrix

| Gate | Required | Current state |
| --- | --- | --- |
| Deterministic fixture comparison Windows + Ubuntu | yes | PENDING CI |
| Exact match = PASS | yes | PENDING CI |
| Encoding-only pixel identity remains PASS | yes | PENDING CI |
| Inclusive WARN/FAIL threshold boundaries | yes | PENDING CI |
| Above blocking threshold = FAIL | yes | PENDING CI |
| Resolution/mode/format incompatibility explicit | yes | PENDING CI |
| Missing baseline/current cannot PASS | yes | PENDING CI |
| Baseline mutation detected | yes | PENDING CI |
| Policy/masks hash-bound | yes | PENDING CI |
| Report derived/policy/evidence tampering rejected | yes | PENDING CI |
| Workspace `../` and symlink escape rejected | yes | PENDING CI |
| R6.3 stable test hook | yes | PENDING CI |
| `visual-report-v1` JSON Schema validation | yes | PENDING CI |
| New Godot PNG tool structured and explicitly governed | yes | PENDING CI |
| Existing R5 AVI behavior/regressions remain green | yes | PENDING CI |
| R0 Repository Guard final head | yes | PENDING |
| Python Core Windows + Ubuntu final head | yes | PENDING |
| KodeStudio UI Smoke final head | yes | PENDING |
| Real Godot 4.7.x rendered PNG evidence on accepted workstation | yes | PENDING USER |
| Non-empty renderer/method/video-adapter evidence | yes | PENDING USER |
| Baseline/current/diff/report chain + R6.3 hook PASS | yes | PENDING USER |
| AuditLog hash chain valid | yes | PENDING USER |

## Manual acceptance reason

Hosted CI can prove the comparison engine against deterministic fixture images. It cannot authoritatively replace the previously accepted real Windows/Godot/Radeon rendering environment. R6.4 therefore requires one local acceptance run using the final implementation head.

The local acceptance deliberately uses Godot Movie Maker PNG output **without `--headless`**, records renderer/driver/video-adapter evidence and rejects empty, dummy or headless renderer evidence.

## Prerequisites

Do not run the manual gate until ChatGPT supplies the exact final R6.4 PR head after final-head CI is green.

Required local baseline:

- Windows workstation used for accepted R5 hardware acceptance;
- Python 3.12.x;
- Godot `4.7.2.stable.steam.ed1daf0bf` unless an equivalent 4.7.x path is explicitly reviewed and recorded;
- expected executable path: `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- clean checkout of the exact R6.4 final PR head;
- no changes to the generated acceptance fixture or VisualQA thresholds.

## Exact command contract

`<R6_4_FINAL_HEAD>` is intentionally not guessed in this file. ChatGPT must replace it in the instructions given to the user only after the PR head is final and CI for that exact head is green.

```powershell
git fetch origin
git checkout <R6_4_FINAL_HEAD>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui]"
$env:KODEPOIA_GODOT_EXE="D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
powershell -ExecutionPolicy Bypass -File .\scripts\r6_4_accept_local.ps1
```

If PowerShell blocks environment activation, use only for the current shell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Then rerun the remaining commands unchanged.

## Expected success evidence

The terminal prints one JSON object and writes:

`.kodepoia/visual_tests/r6-4-local-acceptance.json`

Authoritative success requires at minimum:

- `metadata.acceptance_completed = true`;
- Godot version step PASS with compatible 4.7.x;
- non-empty `render.rendering_method`;
- non-empty `render.rendering_driver`;
- non-empty `render.video_adapter` and no dummy/headless evidence;
- `visual.status = "pass"`;
- non-empty baseline/current/evidence SHA-256 fields;
- a diff artifact path;
- a visual report path;
- R6.3 hook step PASS with ID `visual:godot-real-render`;
- audit-chain step PASS;
- `summary.failed = 0`;
- `summary.passed = summary.total`.

## Evidence the user must send back

1. complete final terminal JSON output;
2. `.kodepoia/visual_tests/r6-4-local-acceptance.json`;
3. the generated visual report referenced by `visual.report`;
4. if a comparison fails, preserve and attach the generated diff referenced by `visual.diff`.

Do not send passwords, access tokens, private keys or unrelated project files.

## Failure recovery

If any gate fails:

- **do not** replace or re-approve the baseline to hide the difference;
- **do not** alter thresholds or masks;
- preserve the full printed JSON, visual report and diff;
- if Godot path/version differs, stop and report exact path/version;
- if renderer/method/video adapter is empty or indicates dummy/headless, stop: that capture is not authoritative rendered evidence;
- if the script exits non-zero, send the complete output with secrets redacted;
- do not repeatedly mutate the fixture; the runner recreates its disposable fixture on each invocation.

## What must not happen yet

Until CI and required local evidence are reviewed and accepted:

- do not merge the R6.4 implementation PR;
- do not mark R6.4 COMPLETE;
- do not modify thresholds/masks/baseline to manufacture PASS;
- do not start R6.5.

## Completion record

PENDING. This section will be normalized after authoritative CI + hardware-local acceptance and merge, with exact implementation head, workflow run IDs, local evidence hashes and merge SHA.
