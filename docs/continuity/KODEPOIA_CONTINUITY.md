# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. R5.1 à R5.5 sont **ACCEPTED AND MERGED**. **R5.6 est IN PROGRESS sur PR #28, branche `agent/r5-6-governed-acceptance`. Les deux probes R5 précédents ont donné 4/5 car `engine_version` bloquait dans ProcessSandbox. Le diagnostic borné à six variantes de `Godot --version` a isolé le défaut : cinq lancements Python directs passent en 0.06–0.44 s, y compris environnement filtré/cwd projet/pipe et fichier, tandis que seul `process_sandbox_project` timeoute à 8.02 s alors qu'il a déjà capturé la bonne version. Cause : `ProcessSandbox.run()` attendait `poll()` avant de drainer stdout/stderr. Correctif appliqué : `communicate(timeout=...)`, arrêt via kill switch sur `TimeoutExpired`, puis drain final. Test de régression 512 KiB stdout + 512 KiB stderr ajouté. Checkpoint fonctionnel `c6ec8f25b8447c68f644ddf7d05aef9995e41861` entièrement vert sur Windows+Ubuntu. Toujours `git pull` le head courant, ne jamais reset vers le checkpoint. Prochaine et seule action locale autorisée : relancer `scripts/r5_accept_local.ps1 -ProbeOnly` avec le Godot Steam connu et fournir `.kodepoia/benchmarks/r5-local-acceptance.json`.** Ne pas lancer l'acceptation complète, ne pas fusionner PR #28 et ne pas commencer R6 avant revue d'un probe 5/5.

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
- R5.6 : IMPLEMENTED / CI ACCEPTED / PROCESS-SANDBOX FIXED / NEW HARDWARE PROBE PENDING.
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

## Probes R5 #1 and #2

Both were 4/5 PASS. `project_inspect`, `scene_parse`, `gdscript_inspect`, `export_presets` passed; only `engine_version` failed.

Probe #2 established:
- direct PowerShell `Godot --version` ≈ 0.44 s;
- ProcessSandbox call ≈ 90 s timeout;
- `timed_out=True`, `cancelled=False`, stderr empty.

Timeout escalation was rejected as a workaround.

## Process diagnostic — decisive

Evidence:

```text
.kodepoia/benchmarks/r5-godot-process-diagnostic.json
```

Results:

```text
inherited_repo_pipe          PASS ~0.44 s
inherited_project_pipe       PASS ~0.06 s
sanitized_empty_pipe         PASS ~0.09 s
sanitized_project_pipe       PASS ~0.06 s
sanitized_project_file       PASS ~0.09 s
process_sandbox_project      FAIL 8.02 s timeout=True
```

The failing sandbox case already captured stdout `4.7.2.stable.steam.ed1daf0bf`. Therefore:
- cwd/project detection is not the blocker;
- sanitized environment is not the blocker;
- pipe vs file capture is not the blocker;
- Python/Windows Godot launch itself is not the blocker;
- the difference is specifically `ProcessSandbox.run()`.

## ProcessSandbox root cause and fix

Old behavior:
1. launch with `stdout=PIPE`, `stderr=PIPE`;
2. poll until child exits or timeout;
3. only then call `communicate()`.

This can deadlock on pipe backpressure because the parent does not drain stdout/stderr while waiting.

New behavior:
1. launch and register process with the global kill switch;
2. call `communicate(timeout=...)` so stdout/stderr are drained while waiting;
3. on `TimeoutExpired`, stop through the existing kill switch and call `communicate()` again;
4. keep kill-switch registration active until completion/unregister.

A generic regression test writes 512 KiB to stdout and 512 KiB to stderr and must complete without timeout on Windows and Ubuntu.

Functional checkpoint `c6ec8f25b8447c68f644ddf7d05aef9995e41861`:
- Guard `32539678111` SUCCESS;
- Python Core `32539678095` SUCCESS Windows + Ubuntu, including the new backpressure regression test and PowerShell syntax validation;
- UI Smoke `32539678096` SUCCESS Windows.

Documentation commits may make the branch head newer than this checkpoint. Always pull the current remote branch; never reset backward.

## Next manual operation

Synchronize current branch:

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

Run **only the normal probe**:

```powershell
.\scripts\r5_accept_local.ps1 -ProbeOnly `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

Expected gate:
- `engine_version` PASS;
- overall 5/5, failed=0;
- report remains `probe_only=true`, `acceptance_completed=false`.

Send:

```text
M:\Kodepoia\.kodepoia\benchmarks\r5-local-acceptance.json
```

Preferably also paste the PowerShell summary. If no JSON is produced, send complete PowerShell output.

Do NOT rerun the process diagnostic unless specifically requested later. Do NOT run full acceptance yet. Do NOT increase timeouts, copy the whole parent environment, run as Administrator, disconnect drives as workaround, weaken security layers, merge PR #28, or start R6.

## R5 completion rule

R5 can become COMPLETE only after a new probe passes 5/5, full acceptance reports `probe_only=false`, `acceptance_completed=true`, `summary.failed=0`, all real Godot/LSP/DAP/export/audit steps pass, final PR #28 CI is green, PR #28 is merged and `main` is verified.

## User operational preference — permanent

Whenever the user must intervene, explain why, prerequisites, exact commands/actions, expected result, error recovery, what to send back, and what must not be done yet. Do not ask the user to repeat known information.

## Permanent rules

Update continuity in the same work cycle for phase/PR/acceptance/prerequisite changes. Never declare COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional. Do not return to R4 except for a demonstrated regression or ADR-worthy architecture change. Do not begin R6 before R5 completion.
