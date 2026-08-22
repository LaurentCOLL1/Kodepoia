# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. R5.1 à R5.5 sont **ACCEPTED AND MERGED**. **R5.6 est IN PROGRESS sur PR #28, branche `agent/r5-6-governed-acceptance`. Le défaut ProcessSandbox qui bloquait `engine_version` a été isolé puis corrigé (`communicate(timeout=...)`, kill-switch conservé, test de backpressure 512 KiB stdout + 512 KiB stderr vert Windows+Ubuntu). Le nouveau probe matériel post-correctif est maintenant 5/5 PASS : `engine_version` 4.7.2 PASS en ~0.094 s, project/scene/GDScript/export presets PASS, `failed=0`, report `probe_only=true`, `acceptance_completed=false`. Ce probe est ACCEPTED et ferme la gate ProcessSandbox/probe. La prochaine et seule action locale autorisée est désormais l'acceptation complète via `scripts/r5_accept_local.ps1` **sans** `-ProbeOnly`, avec le Godot Steam connu. Les export templates Godot 4.7.x doivent être installés car l'acceptation fait un vrai export Windows release. Après exécution, fournir `.kodepoia/benchmarks/r5-local-acceptance.json`.** Ne pas fusionner PR #28 et ne pas commencer R6 avant revue du rapport complet, CI final, merge et vérification de `main`.

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
- R5.6 : IMPLEMENTED / CI ACCEPTED / PROCESS-SANDBOX FIXED / HARDWARE PROBE 5/5 ACCEPTED / FULL ACCEPTANCE AUTHORIZED.
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

## ProcessSandbox incident — closed

Probes #1/#2 were 4/5 because `engine_version` timed out only through ProcessSandbox. A six-case diagnostic proved all equivalent direct Python launch variants passed while only `process_sandbox_project` timed out after already capturing the correct version string.

Root cause: `ProcessSandbox.run()` polled for process exit before draining `stdout=PIPE` / `stderr=PIPE`, allowing pipe-backpressure deadlock.

Fix:
1. launch and register process with global kill switch;
2. call `communicate(timeout=...)` so stdout/stderr are drained while waiting;
3. on `TimeoutExpired`, stop through kill switch and call `communicate()` again;
4. unregister only after completion.

Regression coverage writes 512 KiB to stdout and 512 KiB to stderr and passes on Windows + Ubuntu.

Functional fix checkpoint `c6ec8f25b8447c68f644ddf7d05aef9995e41861`:
- Guard `32539678111` SUCCESS;
- Python Core `32539678095` SUCCESS Windows + Ubuntu;
- UI Smoke `32539678096` SUCCESS Windows.

Always `git pull` current branch head; never reset backward to a checkpoint.

## Hardware probe post-fix — ACCEPTED

Evidence generated `2026-08-22T00:28:38.116174+00:00`:

```text
engine_version      PASS  ~0.094 s  4.7.2.stable.steam.ed1daf0bf
project_inspect     PASS
scene_parse         PASS
gdscript_inspect    PASS
export_presets      PASS
summary             5/5 PASS, failed=0
```

Metadata:
- `probe_only=true`;
- `acceptance_completed=false`;
- Python 3.12.4;
- Windows 11 build 26220;
- LSP/DAP/debug 6005/6006/6007.

This result closes the ProcessSandbox/probe gate and authorizes full R5 local acceptance. It does **not** make R5 COMPLETE by itself.

## Next manual operation — full acceptance

Synchronize first:

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

Prerequisite: install Godot 4.7.x export templates if they are not already installed. Full acceptance performs a real Windows release export.

Run the complete acceptance **without `-ProbeOnly`**:

```powershell
.\scripts\r5_accept_local.ps1 `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

The runner exercises:
- Godot version and project/document/domain inspection;
- GDScript `--check-only`;
- real import;
- project smoke run;
- benchmark;
- movie capture;
- governed scene mutation with SafeChange snapshot;
- loopback services start;
- LSP symbols + diagnostics;
- DAP initialize + launch + threads;
- real Windows release export to a non-empty executable;
- audit hash-chain verification.

Expected report:

```text
probe_only=false
acceptance_completed=true
summary.failed=0
```

Send:

```text
M:\Kodepoia\.kodepoia\benchmarks\r5-local-acceptance.json
```

Also send complete PowerShell output if any step fails. If the failure is `export_release` and reports missing export templates, install the exact Godot 4.7.x export templates and rerun the full acceptance; do not change the preset or bypass export validation.

Do NOT rerun the process diagnostic unless specifically requested. Do NOT increase timeouts, copy the whole parent environment, run as Administrator, weaken Guardian/Sandbox/Permissions, merge PR #28, or start R6.

## R5 completion rule

R5 can become COMPLETE only after full acceptance reports `probe_only=false`, `acceptance_completed=true`, `summary.failed=0`, all real Godot/LSP/DAP/export/audit steps pass, final PR #28 CI is green, PR #28 is merged and `main` is verified.

## User operational preference — permanent

Whenever the user must intervene, explain why, prerequisites, exact commands/actions, expected result, error recovery, what to send back, and what must not be done yet. Do not ask the user to repeat known information.

## Permanent rules

Update continuity in the same work cycle for phase/PR/acceptance/prerequisite changes. Never declare COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional. Do not return to R4 except for a demonstrated regression or ADR-worthy architecture change. Do not begin R6 before R5 completion.
