# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. **R5 — KodeGodot 4.7.x est IN PROGRESS. R5.1 à R5.5 sont ACCEPTED AND MERGED. R5.6 est sur PR #28, branche `agent/r5-6-governed-acceptance`. Le premier probe matériel réel a trouvé un unique défaut : `engine_version` a été tué au timeout fixe de 15 s sur Godot 4.7.2 Steam / Windows 11 build 26220, alors que les 4 autres étapes du probe passaient. Le correctif R5.6 augmente le timeout version à 90 s, préserve seulement les chemins desktop nécessaires dans le sandbox et conserve les secrets hors environnement enfant. Le correctif et la documentation sont maintenant CI ACCEPTED sur le head final `45dc35243a51a5c67830a01f70517a1233a9dac7`.** Prochaine action : synchroniser la branche et rerun `-ProbeOnly` uniquement avec le Godot Steam déjà identifié. Ne pas fusionner PR #28, ne pas marquer R5 COMPLETE et ne pas commencer R6 avant revue du rapport `.kodepoia/benchmarks/r5-local-acceptance.json`.

## Source de vérité et contraintes

- Dépôt : `LaurentCOLL1/Kodepoia`.
- Visibilité GitHub : **PUBLIC volontairement** ; ne pas traiter ce choix comme une anomalie.
- Architecture : v1.0 gelée.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local acceptance passed.
- R4 : COMPLETE — final governed orchestration acceptance passed.
- R5 : **IN PROGRESS**.
- R5.1 : ACCEPTED AND MERGED.
- R5.2 : ACCEPTED AND MERGED — PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`.
- R5.3 : ACCEPTED AND MERGED — PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`.
- R5.4 : ACCEPTED AND MERGED — PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`.
- R5.5 : ACCEPTED AND MERGED — PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`.
- R5.6 : **IMPLEMENTED; STARTUP-LATENCY FIX + FINAL DOCS CI ACCEPTED; HARDWARE PROBE RE-RUN PENDING**.
- Active R5.6 branch: `agent/r5-6-governed-acceptance`.
- Active R5.6 PR: **#28**, OPEN, MERGEABLE, DO NOT MERGE YET.
- Pre-probe fully green head: `532bb7fedc9519d89778a971c0c457ec8f6c1c2b`.
- Startup-latency hardened functional head: `25ddef21718eb09d361830259e62fa0e703469f1`.
- Final probe-rerun head: `45dc35243a51a5c67830a01f70517a1233a9dac7`.
- Final head CI: Repository Guard `32536200325` SUCCESS; Python Core `32536200334` SUCCESS Windows+Ubuntu incl. PowerShell + embedded UI; standalone UI Smoke `32536200352` SUCCESS Windows.
- R6 : **NOT STARTED**.
- Modèles acceptés : KodeFast=`granite4.1:3b`, KodeCore=`gpt-oss:20b`, KodeCoder=`ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste candidat futur KodeDeepCoder.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## R4 boundary remains mandatory

R4 supplies WorkspaceBoundary, ProcessSandbox/global kill switch, structured Tool API, LSP, DAP, code graphs, Guardian/Permissions/SafeChange/Audit and governed orchestration.

KodeGodot must not bypass that boundary. R5.6 enforces it through `KodeGodotExecutor` rather than calling mutable/executable Godot tools directly from the Brain.

## R5 delivered state

### R5.1 — Engine/project foundation

Accepted and merged. Protected Godot 4.7.x runtime/project inspection, named CLI operations, workspace confinement and no-arbitrary-argv Tool API.

### R5.2 — Scene/resource intelligence

Accepted and merged via PR #24.

Delivered:
- Godot 4 text `.tscn/.tres` structural parser;
- format 3 validation;
- ext/sub resources, nodes, connections, IDs/UIDs/paths;
- raw Variant preservation without evaluation;
- provenance lines and dependency extraction;
- bounded workspace-scoped document tools.

Accepted CI:
- Repository Guard `32528439136` SUCCESS;
- Python Core `32528439126` SUCCESS Windows+Ubuntu;
- UI Smoke `32528439139` SUCCESS Windows.

### R5.3 — GDScript + native Godot LSP/DAP

Accepted and merged via PR #25.

Delivered:
- GDScript structure/static-typing inspector;
- Godot native LSP/DAP specialization using R4 protocol clients;
- symbols, diagnostics, DAP initialize/project launch/threads;
- loopback-only host policy and no arbitrary launch fields.

Accepted CI:
- Repository Guard `32528908533` SUCCESS;
- Python Core `32528908562` SUCCESS Windows+Ubuntu;
- UI Smoke `32528908573` SUCCESS Windows.

### R5.4 — 2D/3D intelligence + guarded scene edits

Accepted and merged via PR #26.

Delivered:
- 2D/3D/hybrid node/domain analysis;
- CharacterBody/collision/navigation/TileMap/UI/camera/mesh/light awareness;
- guarded existing-property-only `.tscn` edit;
- SHA-256 stale precondition;
- unique node/property target and provenance line;
- atomic write and protected-property rejection.

Accepted CI:
- Repository Guard `32529333497` SUCCESS;
- Python Core `32529333471` SUCCESS Windows+Ubuntu;
- UI Smoke `32529333485` SUCCESS Windows.

### R5.5 — Headless automation/export/capture/benchmark

Accepted and merged via PR #27.

Delivered:
- non-secret export preset inspection;
- named release/debug/pack exports into `.kodepoia/exports`;
- bounded AVI movie capture into `.kodepoia/captures`;
- bounded headless benchmark;
- Kodepoia-constructed commands only;
- output-name/path confinement.

Accepted CI:
- Repository Guard `32529677551` SUCCESS;
- Python Core `32529677569` SUCCESS Windows+Ubuntu;
- UI Smoke `32529677534` SUCCESS Windows.

## R5.6 — Current active acceptance gate

PR #28 adds:
- `KodeGodotExecutor` with per-tool policy;
- Guardian + PermissionSet + SafeChange + Audit enforcement;
- additional FILE_WRITE checks for indirect Godot writes (`--import`, export, capture);
- Orchestrator tool catalog/routing for KodeCode + KodeGodot without executor bypass;
- explicit managed Godot service command:

```text
godot --headless --editor --path . --lsp-port 6005 --dap-port 6006 --debug-server tcp://127.0.0.1:6007
```

- `GodotServicePorts` defaults: LSP 6005, DAP 6006, debug 6007;
- allowed service port range: 1024–49151; all three distinct;
- fixed host `127.0.0.1`, no remote-host Tool API field;
- real protocol LSP/DAP initialization with retry, replacing earlier dummy TCP readiness connections;
- disposable local fixture: `.kodepoia/r5-acceptance/project`;
- Python runner: `kodepoia.kodegodot.accept_cli`;
- Windows helper: `scripts/r5_accept_local.ps1`;
- report: `.kodepoia/benchmarks/r5-local-acceptance.json`;
- PowerShell helper validates Python 3.12+, exact R5.6 branch, selected Godot executable family 4.7.x and port bounds before running acceptance.

### R5.6 CI before hardware probe

A first CI exposed one obsolete R5.3 test which monkeypatched the old private `_wait_loopback` method. The code was not weakened. The regression test was migrated to the stronger protocol-ready service contract.

Pre-probe fully green head:
`532bb7fedc9519d89778a971c0c457ec8f6c1c2b`

- Repository Guard `32533944821` SUCCESS;
- Python Core `32533944780` SUCCESS Windows+Ubuntu;
- PowerShell acceptance-runner syntax SUCCESS Windows;
- embedded UI smoke SUCCESS Windows;
- standalone UI Smoke `32533944764` SUCCESS Windows.

## First real target-workstation probe — 22 August 2026

Environment observed by the report:
- Python `3.12.4`;
- Windows `Windows-11-10.0.26220-SP0`;
- Godot executable family `godot.windows.opt.tools.64.exe`;
- PowerShell preflight identified Godot `4.7.2.stable.steam.ed1daf0bf`;
- LSP/DAP/debug ports `6005/6006/6007`.

Probe result:
- `project_inspect` PASS;
- `scene_parse` PASS;
- `gdscript_inspect` PASS;
- `export_presets` PASS;
- `engine_version` FAIL after about `15.03 s` with `RuntimeError: Unable to query Godot version: rc=1 stderr=`.

Summary: **4 passed / 1 failed / 5 total**. `acceptance_completed=false` and `probe_only=true` are expected for a probe, but the failed version step means this probe is not accepted.

Strong upstream match:
- Godot issue `#120649` documents a Godot 4.7 Windows regression where editor startup probes drives and can block ~8 seconds per disconnected/network-drive query; reported environment includes Windows 11 build 26200.
- upstream PR `#121192` avoids `GetVolumeInformationW` on network drives, was merged to `master` on 10 July 2026, and was labeled `cherrypick:4.7` for possible future 4.7.x inclusion.
- Godot 4.7.2 release was published 18 August 2026; the visible release highlights do not list this specific fix.

Do not diagnose this as a version mismatch: PowerShell already read the exact 4.7.2 version successfully. The Kodepoia defect was the too-short fixed sandbox timeout and insufficient desktop path environment for a real Windows editor process.

## R5.6 hardening after first hardware probe

Implemented on the same PR #28 branch:
- `GodotRuntime.version()` default timeout: **90 seconds** instead of 15;
- version errors now report `timed_out`, `cancelled` and timeout value;
- `GodotRuntime.check_script()` default timeout: **120 seconds**;
- local acceptance smoke/benchmark/capture windows enlarged;
- local LSP/DAP service startup timeout raised to the existing 120-second API maximum;
- ProcessSandbox remains sanitized and does **not** inherit the full parent environment;
- bounded non-secret desktop path variables are preserved: `APPDATA`, `LOCALAPPDATA`, `USERPROFILE`, `HOMEDRIVE`, `HOMEPATH`, HOME and XDG data/config/cache paths, plus existing system/temp/PATH variables;
- regression test explicitly proves an arbitrary secret-like environment variable is not inherited;
- helper records direct `Godot --version` startup time;
- helper distinct-port validation was rewritten unambiguously.

### Final hardened CI accepted

Exact branch head authorized for probe rerun:
`45dc35243a51a5c67830a01f70517a1233a9dac7`

- Repository Guard `32536200325` SUCCESS;
- Python Core `32536200334` SUCCESS Windows+Ubuntu;
- PowerShell acceptance-runner syntax SUCCESS Windows;
- embedded UI smoke SUCCESS Windows;
- standalone KodeStudio UI Smoke `32536200352` SUCCESS Windows.

Next action is now authorized: rerun **ProbeOnly only**. Do not jump directly to full acceptance.

## Godot 4.7 external contract confirmed on 22 August 2026

Official Godot documentation/current upstream references confirm:
- `--version` prints the version string;
- `--lsp-port` and `--dap-port` exist and recommend ports 1024–49151;
- `--debug-server <uri>` accepts a loopback URI such as `tcp://127.0.0.1:6007`;
- Godot native LSP/DAP requires a running project/editor instance;
- common/default integration ports are LSP 6005 and DAP 6006, with project debug server 6007 in the official VS Code launch example;
- CLI export uses an existing named preset from `export_presets.cfg`;
- real export requires matching installed export templates;
- on Windows, Godot editor data/settings use `%APPDATA%\Godot` by default.

Do not expose these services to a non-loopback host.

## Target-workstation procedure — next manual operation

Detailed source of truth:
`docs/roadmap/R5_LOCAL_ACCEPTANCE.md`

Synchronize:

```powershell
cd M:\Kodepoia
git fetch --all --prune
git switch agent/r5-6-governed-acceptance
git pull
git branch --show-current
git status
git log -1 --oneline
```

Expected branch:

```text
agent/r5-6-governed-acceptance
```

Expected exact head for this rerun:

```text
45dc35243a51a5c67830a01f70517a1233a9dac7
```

Rerun the probe using the already-known Steam Godot path:

```powershell
.\scripts\r5_accept_local.ps1 -ProbeOnly -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

The new helper prints direct Godot version startup duration. Expected successful report has `summary.failed == 0`; `acceptance_completed=false` remains normal because this is still only the probe.

Only after review of a green probe should the full acceptance be run.

If the hardened 90-second version step still times out, send the full PowerShell output and JSON. Do not run PowerShell as Administrator just to bypass the Godot drive-probing regression; do not disconnect drives or weaken Kodepoia security controls unless later diagnosis explicitly requires a safe local test.

## Hardware acceptance completion rule

R5 can move to COMPLETE only when reviewed evidence proves:
- phase `R5-local-acceptance`;
- `probe_only == false`;
- `acceptance_completed == true`;
- zero failed steps;
- actual Godot 4.7.x check/import/smoke/benchmark/capture succeed;
- governed scene edit creates a SafeChange snapshot;
- real LSP symbols/diagnostics succeed;
- real DAP initialize/project launch/threads succeed;
- Windows Desktop release export produces a non-empty executable;
- audit hash chain verifies;
- final PR #28 CI is green.

Then and only then:
1. update R5 status to COMPLETE;
2. update continuity with acceptance evidence;
3. merge PR #28;
4. verify `main` CI/state;
5. normalize continuity if required;
6. authorize R6.

## User operational preference — permanent

Whenever the user must personally perform an operation, explain the entire procedure in detail:
- why intervention is necessary;
- prerequisites;
- exact commands/actions;
- expected result;
- error recovery;
- what output/file to send back;
- what must **not** be done yet.

Do not ask the user to repeat information already known.

## Permanent rules

Update continuity in the same work cycle for phase/PR/acceptance/prerequisite changes. Never declare COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional. Do not return to R4 except for a demonstrated regression or ADR-worthy architecture change. Do not begin R6 before R5 completion.
