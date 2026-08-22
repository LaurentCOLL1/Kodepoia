# R6.5 — KodeAccessibility foundation — Acceptance

**Status:** IN PROGRESS — FINAL-HEAD CI AND REQUIRED MANUAL WINDOWS/NARRATOR EVIDENCE PENDING  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** REQUIRED

R6.5 MUST NOT be marked COMPLETE or merged until both the final-head hosted CI and the required real interactive Windows keyboard/focus/Narrator evidence pass on the exact same implementation head.

## Acceptance matrix

| Gate | Required | Current state |
| --- | --- | --- |
| Stable rule/target IDs and duplicate rejection | yes | IMPLEMENTED — PENDING FINAL CI |
| PASS/WARN/FAIL/UNKNOWN/NOT_APPLICABLE semantics | yes | IMPLEMENTED — PENDING FINAL CI |
| `not_applicable` requires an explicit reason | yes | IMPLEMENTED — PENDING FINAL CI |
| Blocking state allowed only for FAIL | yes | IMPLEMENTED — PENDING FINAL CI |
| Aggregate status/counts/blockers deterministic | yes | IMPLEMENTED — PENDING FINAL CI |
| Report evidence SHA-256 and tamper rejection | yes | IMPLEMENTED — PENDING FINAL CI |
| `accessibility-report-v1` JSON Schema | yes | IMPLEMENTED — PENDING FINAL CI |
| Workspace and symlink escape protection | yes | IMPLEMENTED — PENDING FINAL CI |
| R6.3 stable accessibility test hooks | yes | IMPLEMENTED — PENDING FINAL CI |
| Explicit sRGB contrast helper | yes | IMPLEMENTED — PENDING FINAL CI |
| Explicit direct-rectangle target-size helper | yes | IMPLEMENTED — PENDING FINAL CI |
| KodeStudio explicit accessible metadata | yes | IMPLEMENTED — PENDING FINAL CI |
| Project Wizard explicit accessible metadata | yes | IMPLEMENTED — PENDING FINAL CI |
| Dynamic budget/requirement controls registered | yes | IMPLEMENTED — PENDING FINAL CI |
| QAccessible interface/name/role/state audit | yes | IMPLEMENTED — PENDING FINAL CI |
| Visible enabled registered controls are tab-focusable | yes | IMPLEMENTED — PENDING FINAL CI |
| Hidden/disabled adaptive controls are explicit N/A | yes | IMPLEMENTED — PENDING FINAL CI |
| Named application controls cannot silently bypass registration | yes | IMPLEMENTED — PENDING FINAL CI |
| Qt-owned tab-scroll internals excluded narrowly | yes | IMPLEMENTED — PENDING FINAL CI |
| R0 Repository Guard final head | yes | PENDING |
| Python Core Windows + Ubuntu final head | yes | PENDING |
| PowerShell acceptance-runner syntax final head | yes | PENDING |
| Integrated KodeStudio UI accessibility smoke | yes | PENDING |
| Separate KodeStudio UI Smoke final head | yes | PENDING |
| Real keyboard-only navigation on Windows | yes | PENDING USER |
| Real visible focus check | yes | PENDING USER |
| Real focus-not-obscured check | yes | PENDING USER |
| Real Windows Narrator names/roles/states | yes | PENDING USER |
| Narrator table/action checks | yes | PENDING USER |
| Manual evidence tied to exact final source head | yes | PENDING USER |
| Final local result `acceptance_completed=true` | yes | PENDING USER |

## Why manual intervention is mandatory

Qt metadata and offscreen CI can prove structural accessibility evidence, but they cannot authoritatively prove the human-observable behavior of the real Windows desktop session.

The required local gate checks:

- actual keyboard-only operation;
- actual visible focus;
- actual focus not being obscured/clipped;
- actual Narrator speech for KodeStudio controls;
- actual Narrator table context and action names.

This boundary follows the R6 plan and is informed by W3C WCAG2ICT guidance for non-Web software and Microsoft's Narrator documentation.

## Exact final-head rule

Do **not** run the manual gate until ChatGPT supplies the exact final R6.5 PR head after all final-head hosted workflows are green.

The user must test exactly that SHA. Any later code/documentation commit that changes the implementation PR head requires final-hosted-CI reevaluation and, if it can affect the acceptance behavior or evidence contract, a new manual run.

## Local prerequisites

- the Windows workstation used for prior Kodepoia hardware-local acceptance;
- Python 3.12.x;
- active Kodepoia virtual environment or ability to create/activate one;
- PySide6 via `.[dev,ui]`;
- exact final R6.5 implementation head supplied by ChatGPT;
- existing project-local `.kodepoia/` directory preserved;
- Windows Narrator available;
- no edits to R6.5 accessibility metadata, checklist, report files or response JSON before acceptance.

## Planned commands

The final `<R6_5_FINAL_HEAD>` placeholder will be replaced in the user-facing instructions after final-head CI is green.

```powershell
git fetch origin
git checkout <R6_5_FINAL_HEAD>
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui]"
powershell -ExecutionPolicy Bypass -File .\scripts\r6_5_accept_local.ps1
```

If no suitable virtual environment is active:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui]"
```

## What the script does

1. resolves the exact current Git head;
2. builds deterministic offscreen KodeStudio + Project Wizard accessibility reports;
3. requires both automated reports to PASS with zero blocking failures;
4. stores hashed evidence under `.kodepoia/diagnostics/accessibility/`;
5. launches KodeStudio as a real interactive Windows process;
6. presents 13 stable keyboard/focus/Narrator checklist items one by one;
7. records the user's actual PASS/FAIL observation for every item;
8. writes responses under the confined accessibility evidence directory;
9. finalizes only if the source head and automated hashes still match and every required check passes;
10. emits the final machine-readable acceptance JSON.

The script does **not** simulate Narrator and does **not** activate the emergency KillSwitch.

## Manual checklist categories

### Keyboard

- `keyboard.main_navigation`
- `keyboard.project_wizard_open`
- `keyboard.wizard_general`
- `keyboard.wizard_sections`
- `keyboard.wizard_actions`

### Focus

- `focus.visible`
- `focus.not_obscured`

### Narrator

- `narrator.enabled`
- `narrator.main_navigation`
- `narrator.security_actions`
- `narrator.wizard_fields`
- `narrator.wizard_tables`
- `narrator.wizard_actions`

Every check is blocking for R6.5 acceptance.

## Narrator commands used

Microsoft's current Narrator documentation identifies:

- `Win+Ctrl+Enter` — start/stop Narrator;
- `Narrator+Alt+X` — open Speech Recap / live transcription.

Speech Recap is optional support for reviewing what was actually spoken; it does not replace listening/observing the real interaction.

## Safety rule for the emergency stop

The checklist may focus the Security buttons so Narrator can announce their names/roles/descriptions.

**Do not activate `STOP ALL PROTECTED PROCESSES` during this acceptance.**

The test is about accessibility metadata and focus, not KillSwitch execution.

## Expected successful output

Successful finalization must include at minimum:

- `metadata.phase = "R6.5-local-acceptance"`;
- `metadata.source_head = <exact final head>`;
- `metadata.acceptance_completed = true`;
- `automated.passed = true`;
- two automated report entries;
- both automated reports status `pass`;
- both automated report `blocking_failures = 0`;
- non-empty automated `evidence_sha256` values;
- `manual.total = 13`;
- `manual.passed = 13`;
- `manual.failed = 0`;
- `manual.blocking_failures = 0`;
- `summary.failed = 0`;
- `summary.passed = 15`;
- `summary.total = 15`;
- output path `.kodepoia/diagnostics/accessibility/r6-5-local-acceptance.json`.

## Evidence to send back

After the final-head run, send ChatGPT:

1. the complete final JSON printed by the script;
2. if requested for investigation, `.kodepoia/diagnostics/accessibility/r6-5-local-acceptance.json`;
3. if a check fails, preserve the generated manifest, responses and automated reports and provide the failure note/output needed for diagnosis.

Do not send passwords, API tokens, private keys or unrelated personal files.

## Failure recovery

If automated preparation fails:

- preserve the printed JSON/output;
- do not manually edit the generated accessibility report to make it PASS;
- do not disable a rule or mark it N/A without an implementation rationale;
- send the exact error/result to ChatGPT.

If a keyboard/focus/Narrator manual check fails:

- answer `FAIL` truthfully;
- enter a short note describing what was unreachable, invisible, obscured, unnamed, incorrectly announced or otherwise wrong;
- preserve the final failed JSON and generated evidence;
- do not edit the response JSON afterward to manufacture PASS;
- do not repeatedly reinterpret a failed observation as success.

If Narrator does not start with `Win+Ctrl+Enter`, stop and report that environmental failure rather than marking the Narrator checks PASS.

If KodeStudio exits unexpectedly, preserve terminal output and report the failure.

## What must not happen yet

Until final hosted CI and the required manual evidence have both been reviewed:

- do not merge PR #41;
- do not mark R6.5 COMPLETE;
- do not start R6.6;
- do not edit checklist answers to manufacture PASS;
- do not activate the KillSwitch merely to test its accessible name;
- do not delete `.kodepoia/diagnostics/accessibility/` evidence.

## Completion record

PENDING. After authoritative final-head CI + user manual acceptance + PR merge, this section will be normalized with:

- exact accepted implementation head;
- PR number and merge SHA;
- exact R0/Python Core/KodeStudio run IDs;
- automated accessibility report hashes/counts;
- final manual 13/13 result;
- final 15/15 integrated local result;
- evidence path(s);
- R6.5 COMPLETE and R6.6 NEXT / NOT STARTED.
