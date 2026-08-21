# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. **R5 — KodeGodot 4.7.x est IN PROGRESS. R5.1 à R5.5 sont ACCEPTED AND MERGED. R5.6 est IMPLEMENTED / CI ACCEPTED / HARDWARE-LOCAL ACCEPTANCE PENDING sur PR #28, branche `agent/r5-6-governed-acceptance`.** Ne pas fusionner PR #28, ne pas marquer R5 COMPLETE et ne pas commencer R6 avant revue du rapport `.kodepoia/benchmarks/r5-local-acceptance.json`. Lire architecture, ADR, `R5_STATUS.md`, `R5_LOCAL_ACCEPTANCE.md` puis ce fichier avant reprise.

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
- R5.6 : **IMPLEMENTED / CI ACCEPTED / HARDWARE-LOCAL ACCEPTANCE PENDING**.
- Active R5.6 branch: `agent/r5-6-governed-acceptance`.
- Active R5.6 PR: **#28**, OPEN, DO NOT MERGE YET.
- R6 : **NOT STARTED**.
- Modèles acceptés : KodeFast=`granite4.1:3b`, KodeCore=`gpt-oss:20b`, KodeCoder=`ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste candidat futur KodeDeepCoder.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## R4 boundary remains mandatory

R4 supplies WorkspaceBoundary, ProcessSandbox/global kill switch, structured Tool API, LSP, DAP, code graphs, Guardian/Permissions/SafeChange/Audit and governed orchestration.

KodeGodot must not bypass that boundary. R5.6 now enforces it through `KodeGodotExecutor` rather than calling mutable/executable Godot tools directly from the Brain.

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

### R5.6 CI evidence

First CI exposed one obsolete R5.3 test which monkeypatched the old private `_wait_loopback` method. The code was not weakened. The regression test was migrated to the stronger protocol-ready service contract.

Accepted functional head:
`c8bd7c090bc9618970fb355eee2ed1a5523e5e79`

- Repository Guard `32533673288` SUCCESS;
- Python Core `32533673215` SUCCESS Windows+Ubuntu;
- PowerShell acceptance-runner syntax SUCCESS Windows;
- embedded UI smoke SUCCESS Windows;
- standalone UI Smoke `32533673205` SUCCESS Windows.

Later helper/documentation commits add direct Godot 4.7.x preflight and the final local acceptance procedure. Their final branch head must also remain CI-green before asking the user to run the hardware acceptance.

## Godot 4.7 external contract confirmed on 22 August 2026

Official Godot documentation/current upstream references confirm:
- `--lsp-port` and `--dap-port` exist and recommend ports 1024–49151;
- `--debug-server <uri>` accepts a loopback URI such as `tcp://127.0.0.1:6007`;
- Godot native LSP/DAP requires a running project/editor instance;
- common/default integration ports are LSP 6005 and DAP 6006, with project debug server 6007 in the official VS Code launch example;
- CLI export uses an existing named preset from `export_presets.cfg`;
- real export requires matching installed export templates.

Do not expose these services to a non-loopback host.

## Target-workstation procedure — next manual operation

Detailed source of truth:
`docs/roadmap/R5_LOCAL_ACCEPTANCE.md`

The user should only run this after final PR #28 CI is green.

Repository synchronization:

```powershell
cd M:\Kodepoia
git fetch --all --prune
git switch agent/r5-6-governed-acceptance
git pull
git branch --show-current
git status
```

Expected branch:

```text
agent/r5-6-governed-acceptance
```

First run the probe:

```powershell
.\scripts\r5_accept_local.ps1 -ProbeOnly
```

If Godot is not on PATH:

```powershell
.\scripts\r5_accept_local.ps1 -ProbeOnly -GodotPath "C:\path\to\Godot_v4.7.x-stable_win64.exe"
```

After a successful probe, run full acceptance:

```powershell
.\scripts\r5_accept_local.ps1
```

or with explicit Godot path:

```powershell
.\scripts\r5_accept_local.ps1 -GodotPath "C:\path\to\Godot_v4.7.x-stable_win64.exe"
```

If default ports are occupied, use three distinct ports in 1024–49151, e.g.:

```powershell
.\scripts\r5_accept_local.ps1 -LspPort 6105 -DapPort 6106 -DebugPort 6107
```

Full acceptance requires matching Godot 4.7.x Windows export templates. If `export_release` is the only missing step because templates are absent, install the exact matching templates through Godot **Editor → Manage Export Templates…**, then rerun. Do not weaken Kodepoia export checks.

Expected report:

```text
M:\Kodepoia\.kodepoia\benchmarks\r5-local-acceptance.json
```

User must send back that JSON or, if no usable report exists, the complete PowerShell output.

Do not manually edit status or merge the PR.

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
