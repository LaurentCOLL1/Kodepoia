# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. R5.1 à R5.5 sont **ACCEPTED AND MERGED**. **R5.6 est IN PROGRESS sur PR #28, branche `agent/r5-6-governed-acceptance`. Le probe matériel post-fix est ACCEPTED 5/5. Le premier full hardware acceptance a donné 12/19, mais les 7 échecs se réduisent à deux causes indépendantes : (A) `capture_movie` utilisait `--headless` avec `--write-movie`, ce qui a crashé dans le RenderingServer dummy; correction : Movie Maker utilise maintenant un renderer réel. (B) `services_start` lançait le Godot editor persistant avec des stdout/stderr PIPE non drainés alors que LSP/DAP passent par sockets; correction : nouveau `ProcessSandbox.spawn_background()` avec DEVNULL, même sandbox/kill switch, plus `--log-file .kodepoia/logs/godot-services.log`. Les 5 échecs LSP/DAP suivants étaient des cascades du seul échec `services_start`. Le head fonctionnel `6b968d284a5f10195cbe465d5c94208f65c3a94e` est entièrement vert Windows+Ubuntu. Toujours `git pull` le head courant, ne jamais reset vers un checkpoint. Prochaine action locale, uniquement après CI verte du head documentaire courant : relancer le full acceptance sans `-ProbeOnly` avec le Godot Steam connu. Si `services_start` échoue encore, fournir aussi `.kodepoia/r5-acceptance/project/.kodepoia/logs/godot-services.log`.** Ne pas fusionner PR #28 et ne pas commencer R6 avant revue d'un full report 19/19, CI final, merge et vérification de `main`.

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
- R5.6 : IMPLEMENTED / CI ACCEPTED / HARDWARE PROBE 5/5 ACCEPTED / FULL ACCEPTANCE ATTEMPT #1 = 12/19 / TWO ROOT CAUSES FIXED / FULL RETEST PENDING.
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

## ProcessSandbox foreground incident — closed

Initial probes failed only `engine_version`. A bounded diagnostic proved the sandbox foreground launcher was waiting on child exit before draining PIPEs. `ProcessSandbox.run()` now uses `communicate(timeout=...)`, stops through the global kill switch on timeout, drains again, and has a 512 KiB stdout + 512 KiB stderr regression test passing on Windows and Ubuntu.

Fresh hardware probe after this fix passed **5/5**, including Godot 4.7.2 version detection in ~0.094 s. That probe is ACCEPTED.

## Full hardware acceptance attempt #1 — diagnostic evidence

Generated `2026-08-22T01:01:59.706424+00:00`, `probe_only=false`, `acceptance_completed=false`.

Summary: **12 PASS / 7 FAIL / 19**.

Passed:
- engine version;
- project + scene + domain inspection;
- GDScript inspection and real `--check-only`;
- import;
- smoke;
- benchmark (~103.8 effective FPS on fixture);
- governed scene edit with SafeChange snapshot;
- real Windows release export;
- audit verification.

The release export produced `.kodepoia/exports/r5-acceptance.exe` with **109,127,680 bytes**, proving export templates are installed and functional.

The 7 failed checks represent only two causes:

### A. Movie capture renderer mismatch — fixed

Observed crash:
- Windows code `3221225477`;
- `texture_2d_get` in Godot `dummy/storage/texture_storage.h`;
- Godot signal 11 backtrace.

Cause: Kodepoia combined `--headless` with `--write-movie`. Headless selects the dummy rendering path, while Movie Maker needs actual rendered frames.

Fix: `GodotRuntime.capture_movie()` no longer passes `--headless`; it remains sandboxed, output-confined, frame/FPS/timeout bounded, and still writes only to `.kodepoia/captures/`.

### B. Persistent Godot service stdio backpressure — fixed

Observed:
- `services_start` timed out after ~120.5 s waiting for port 6005;
- `lsp_symbols`, `lsp_diagnostics`, `dap_initialize`, `dap_launch_project`, `dap_threads` then failed only because services were not running.

Cause candidate confirmed architecturally: `GodotEditorServices` used `spawn_piped()` for a process whose protocol is socket-based and never drained stdout/stderr. A verbose editor could therefore block on pipe backpressure before opening LSP/DAP ports.

Fix:
1. add `ProcessSandbox.spawn_background()`;
2. reuse `_validate_launch`, sanitized environment, allowlist and global kill-switch registration;
3. set stdin/stdout/stderr to DEVNULL for background network services;
4. keep `spawn_piped()` for real stdio protocols;
5. Godot services use `spawn_background()`;
6. add `--log-file .kodepoia/logs/godot-services.log` so startup remains diagnosable;
7. startup failure includes a bounded tail of that log.

Regression test launches a background child that writes 2 MiB to stdout and 2 MiB to stderr; it must terminate without backpressure and remain kill-switch managed.

## Functional checkpoint after both fixes

`6b968d284a5f10195cbe465d5c94208f65c3a94e`:
- Repository Guard `32543313597` SUCCESS;
- Python Core `32543313587` SUCCESS Windows + Ubuntu, including PowerShell syntax and background-process regression;
- KodeStudio UI Smoke `32543313595` SUCCESS Windows.

Documentation commits may make the current branch head newer. Always pull current head; never reset backward to this checkpoint.

## Next manual operation — full acceptance retest

Only after current documentation head is fully CI-green:

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

Run the complete acceptance **without `-ProbeOnly`**:

```powershell
.\scripts\r5_accept_local.ps1 `
  -GodotPath "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
```

Expected final gate:

```text
probe_only=false
acceptance_completed=true
summary.failed=0
Passed 19/19
```

Pay special attention to:
- `capture_movie` PASS and non-empty AVI;
- `services_start` PASS;
- LSP symbols/diagnostics PASS;
- DAP initialize/launch/threads PASS.

Send `.kodepoia/benchmarks/r5-local-acceptance.json` and the PowerShell summary. If `services_start` still fails, also send:

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
