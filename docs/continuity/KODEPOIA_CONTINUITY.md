# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. R5.1 à R5.5 sont **ACCEPTED AND MERGED**. **R5.6 est IN PROGRESS sur PR #28, branche `agent/r5-6-governed-acceptance`. Le probe matériel post-fix est ACCEPTED 5/5. Le premier full hardware acceptance a donné 12/19, mais les 7 échecs se réduisent à deux causes indépendantes : (A) `capture_movie` utilisait `--headless` avec `--write-movie`, ce qui a crashé dans le RenderingServer dummy; correction : Movie Maker utilise maintenant un renderer réel. (B) `services_start` lançait le Godot editor persistant avec des stdout/stderr PIPE non drainés alors que LSP/DAP passent par sockets; correction : `ProcessSandbox.spawn_background()` avec DEVNULL, même sandbox/kill switch, plus `--log-file .kodepoia/logs/godot-services.log`. Les 5 échecs LSP/DAP suivants étaient des cascades du seul échec `services_start`. Les corrections ont passé Guard, Python Core Windows+Ubuntu et UI Smoke. Toujours `git pull` le head courant de la branche; les SHAs documentés ci-dessous sont des checkpoints CI, jamais une cible de reset. Prochaine action locale autorisée : relancer le full acceptance sans `-ProbeOnly` avec le Godot Steam connu. Si `services_start` échoue encore, fournir aussi `.kodepoia/r5-acceptance/project/.kodepoia/logs/godot-services.log`.** Ne pas fusionner PR #28 et ne pas commencer R6 avant revue d'un full report 19/19, CI final, merge et vérification de `main`.

## Source de vérité

- Dépôt : `LaurentCOLL1/Kodepoia`.
- Visibilité GitHub : PUBLIC volontairement.
- Architecture : v1.0 gelée.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local acceptance passed.
- R4 : COMPLETE — governed orchestration acceptance passed.
- R5 : IN PROGRESS.
- R5.1 : ACCEPTED AND MERGED, PR #22.
- R5.2 : ACCEPTED AND MERGED, PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`.
- R5.3 : ACCEPTED AND MERGED, PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`.
- R5.4 : ACCEPTED AND MERGED, PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`.
- R5.5 : ACCEPTED AND MERGED, PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`.
- R5.6 : IMPLEMENTED / CI ACCEPTED / PROBE 5/5 ACCEPTED / FULL ATTEMPT #1 = 12/19 / TWO ROOT CAUSES FIXED / FULL RETEST AUTHORIZED.
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

## Closed foreground ProcessSandbox incident

Initial probes failed only `engine_version`. Diagnostic evidence proved `ProcessSandbox.run()` waited for process exit before draining stdout/stderr PIPEs. It now uses `communicate(timeout=...)`, stops through the global kill switch on timeout, drains remaining output and unregisters after completion. Regression coverage writes 512 KiB to both stdout and stderr and passes on Windows+Ubuntu.

The post-fix hardware probe then passed **5/5**, including Godot 4.7.2 version detection in ~0.094 s.

## Full hardware acceptance attempt #1

Generated `2026-08-22T01:01:59.706424+00:00`, with `probe_only=false`, `acceptance_completed=false`.

Summary: **12 PASS / 7 FAIL / 19**.

Already proven on the target PC:
- engine version;
- project/scene/domain/GDScript inspection;
- real `--check-only`;
- import;
- smoke;
- benchmark (~103.8 effective FPS on fixture);
- governed scene edit + SafeChange snapshot;
- real Windows release export;
- audit chain.

The release export produced `.kodepoia/exports/r5-acceptance.exe`, **109,127,680 bytes**, so export templates are installed and functional.

### Cause A — Movie Maker + headless — fixed

`capture_movie` crashed in Godot `dummy/storage/texture_storage.h::texture_2d_get`, Windows code `3221225477`. Kodepoia combined `--headless` with `--write-movie`. Movie capture now omits `--headless` so Godot uses a real renderer, while all path/output/frame/FPS/timeout and ProcessSandbox constraints remain.

### Cause B — background editor PIPE backpressure — fixed

`services_start` timed out waiting for LSP 6005; five later LSP/DAP failures were cascades. `GodotEditorServices` had used `spawn_piped()` for a socket-based long-lived service without draining the pipes.

Fix:
1. `ProcessSandbox.spawn_background()` reuses allowlist, sanitized environment, cwd boundary and global kill-switch registration;
2. stdin/stdout/stderr are DEVNULL for socket services;
3. `spawn_piped()` remains for genuine stdio protocols;
4. Godot LSP/DAP uses `spawn_background()`;
5. Godot writes `.kodepoia/logs/godot-services.log` via `--log-file`;
6. failures include a bounded log tail.

Regression coverage includes a background child writing 2 MiB stdout + 2 MiB stderr without blocking.

## CI checkpoints

Functional correction checkpoint `6b968d284a5f10195cbe465d5c94208f65c3a94e`:
- Guard `32543313597` SUCCESS;
- Python Core `32543313587` SUCCESS Windows + Ubuntu;
- UI Smoke `32543313595` SUCCESS.

Retest-gate checkpoint `b12c0511cdab1d3c73826afaa402259b26824a33`:
- Guard `32543664412` SUCCESS;
- Python Core `32543664439` SUCCESS Windows + Ubuntu, PowerShell syntax and embedded UI smoke;
- UI Smoke `32543664411` SUCCESS.

These are proof checkpoints only. **Always pull the current remote branch head; never reset backward to a checkpoint.**

## Next manual operation — full acceptance retest

```powershell
cd M:\Kodepoia
git fetch --all --prune
git switch agent/r5-6-governed-acceptance
git pull
git branch --show-current
git status
git log -1 --oneline
```

Do not require an old checkpoint SHA; the branch must simply be current with `origin/agent/r5-6-governed-acceptance` and clean.

If needed:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run complete acceptance **without `-ProbeOnly`**:

```powershell
.\scripts\r5_accept_local.ps1 `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

Expected gate:

```text
probe_only=false
acceptance_completed=true
summary.failed=0
Passed 19/19
```

Corrected checks to watch:
- `capture_movie` PASS + non-empty AVI;
- `services_start` PASS;
- `lsp_symbols` and `lsp_diagnostics` PASS;
- `dap_initialize`, `dap_launch_project`, `dap_threads` PASS.

Send `.kodepoia/benchmarks/r5-local-acceptance.json` and the PowerShell summary. If `services_start` fails, also send:

```text
M:\Kodepoia\.kodepoia\r5-acceptance\project\.kodepoia\logs\godot-services.log
```

Do NOT rerun the old process diagnostic unless specifically requested. Do NOT increase timeouts, run as Administrator, weaken Guardian/Sandbox/Permissions, merge PR #28, or start R6.

## R5 completion rule

R5 can become COMPLETE only after full acceptance reports `probe_only=false`, `acceptance_completed=true`, `summary.failed=0`, all real Godot/LSP/DAP/export/audit steps pass, final PR #28 CI is green, PR #28 is merged and `main` is verified.

## User operational preference — permanent

Whenever the user must intervene, explain why, prerequisites, exact commands/actions, expected result, error recovery, what to send back, and what must not be done yet. Do not ask the user to repeat known information.

## Permanent rules

Update continuity in the same work cycle for phase/PR/acceptance/prerequisite changes. Never declare COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional. Do not return to R4 except for a demonstrated regression or ADR-worthy architecture change. Do not begin R6 before R5 completion.
