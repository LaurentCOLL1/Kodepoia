# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 21 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. **R5 — KodeGodot 4.7.x est IN PROGRESS. R5.1 Engine/project foundation est ACCEPTED ON BRANCH / PR #22 MERGE PENDING sur `agent/r5-1-godot-foundation`.** R5.2 est NEXT / NOT STARTED. R5.3–R5.6 ne sont pas commencées. Lire architecture, ADR, roadmap, `R4_STATUS.md`, `R5_STATUS.md`, puis ce fichier avant de reprendre. Ne pas rouvrir R4 sans nouvelle preuve ou ADR.

## Source de vérité et contraintes

- Dépôt : `LaurentCOLL1/Kodepoia`.
- Visibilité GitHub : **PUBLIC volontairement** ; ne pas traiter ce choix comme une anomalie.
- `main` de départ R5 : `0b03de919721d3a292a00b4a1544100779416a53`.
- Branche active : `agent/r5-1-godot-foundation`.
- PR active : #22 — R5.1 protected Godot 4.7 engine/project foundation.
- Architecture : v1.0 gelée.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local acceptance passed.
- R4 : COMPLETE — final governed orchestration acceptance passed.
- R5 : **IN PROGRESS**.
- R5.1 : **ACCEPTED ON BRANCH / MERGE PENDING**.
- R5.2 : NEXT / NOT STARTED.
- R5.3–R5.6 : NOT STARTED.
- Modèles acceptés : KodeFast=`granite4.1:3b`, KodeCore=`gpt-oss:20b`, KodeCoder=`ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste candidat futur KodeDeepCoder.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## R4 — KodeCode — COMPLETE

R4.1 à R4.6 sont ACCEPTED AND MERGED. R4 fournit la frontière obligatoire pour R5 : WorkspaceBoundary, ProcessSandbox/kill switch, structured Tool API, Tree-sitter, LSP, DAP, code graphs, Guardian/Permissions/SafeChange/Audit et orchestration gouvernée.

Principaux merges R4 :
- R4.1 PR #11 — `91f3d77cc375021efcb24172b2859a27748843b8`;
- R4.2 PR #13 — `ae1cfaa914962dec75950ec11d609c6b6fb929fb`;
- R4.3 PR #15 — `1074533e9930549b71af281003b74c6ed049ba9b`;
- R4.4 PR #17 — `0b16277c00782382780c2b5f2b1aa7a616b4f9da`;
- R4.5 PR #18 — `344a29022c6e96f447944d3e064ebeb1933a4600`;
- R4.6 PR #19 — `80931d3f4302456783a884f117976ad0f4fed340`.

Do not bypass the R4 executor/security boundary when adding Godot-specific operations.

## R5 subdivision

1. R5.1 Engine/project foundation — ACCEPTED ON BRANCH / MERGE PENDING.
2. R5.2 Scene/resource intelligence — NEXT / NOT STARTED.
3. R5.3 GDScript + Godot LSP/DAP specialization — NOT STARTED.
4. R5.4 2D/3D domain intelligence and safe edits — NOT STARTED.
5. R5.5 Headless automation/import/export/capture/benchmarks — NOT STARTED.
6. R5.6 Governed orchestration + real Godot acceptance — NOT STARTED.

## R5.1 — ACCEPTED ON BRANCH / PR #22 MERGE PENDING

Implemented on `agent/r5-1-godot-foundation`:
- new `src/kodepoia/kodegodot/` package;
- `GodotProjectInspector` parses `project.godot` without evaluating Godot Variant expressions;
- project metadata includes config version, application name, main scene, rendering methods, feature strings and Godot asset counts;
- `GodotRuntime` uses R1 `ProcessSandbox` and global kill switch;
- Godot version parser with explicit `4.7.x` compatibility check;
- named CLI operations only: engine version, GDScript `--check-only --script`, headless `--import`, bounded headless project/scene smoke;
- all script/scene paths are confined through `WorkspaceBoundary`;
- `GodotToolAPI` exposes only named structured functions, `additionalProperties=false`, no arbitrary `argv`, `args` or `flags` input;
- runtime timeout and smoke frame count are bounded in implementation, not only JSON schema;
- tests cover metadata, 4.7 compatibility, exact CLI construction, workspace escape, bounds and Tool API secrecy.

Accepted functional head `041728735d761d1f17abeb38cce86f9b951db36a`:
- Repository Guard `32525599593` SUCCESS;
- Python Core `32525599591` SUCCESS Ubuntu+Windows;
- UI Smoke `32525599578` SUCCESS Windows.

The final documentation head after recording this evidence must also pass the same required checks before PR #22 is merged.

R5.1 intentionally does not yet expose general export, movie, LSP/DAP ports, scene mutation or arbitrary command execution. Those belong to later accepted sub-phases.

## Godot 4.7 external contract used by R5

Official Godot 4.7 documentation confirms the CLI capabilities needed by the frozen R5 roadmap: `--version`, `--path`, `--headless`, `--check-only` with `--script`, `--import`, `--quit-after`, `--scene`, `--lsp-port`, `--dap-port`, `--export-release`/`--export-debug`/`--export-pack` and `--write-movie`. Godot may ignore unknown CLI arguments, therefore Kodepoia must continue constructing allowlisted commands itself rather than forwarding arbitrary model-supplied flags.

Godot 4 text scenes/resources use format 3 and string UIDs; R5.2 should model descriptors, external/internal resources, nodes and connections with provenance rather than editing them as unstructured text.

## Next sequence

1. Wait for required CI on the exact final PR #22 documentation head.
2. If all checks are green and PR #22 remains mergeable, merge it.
3. Normalize R5 status/continuity on `main`: R5.1 ACCEPTED AND MERGED; R5.2 NEXT / NOT STARTED.
4. Start R5.2 from normalized `main` only.
5. Do not mark R5 COMPLETE before R5.1–R5.6 including real Godot acceptance are all accepted and merged.
6. R6 must not start before R5 completion.

## Permanent rules

Update continuity in the same cycle for phase/PR/acceptance/prerequisite changes. Never declare COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional. Do not return to R4 except for a demonstrated regression or an ADR-worthy architecture change.
