# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning candidate est accepté sur son premier head mais le head documentaire final doit être re-gaté avant merge; R12.1 reste strictement interdit jusqu’au merge du plan et à sa normalisation de continuité.** Source normalisée de départ : `main` `6d3c7eb557d940641977d18384e4f6d2bad42f3c`. Premier planning head accepté `b085fbdb03d62bd06dbdd045eccded3a0de667ab` : R0 #1463 / `32771732655`, Python Core #1437 / `32771732751`, UI Smoke #1404 / `32771732640`, tous SUCCESS. `docs/roadmap/R12_PLAN.md` fige R12.1–R12.16. Aucun R12.x n’est encore implémenté.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED**.
- R11.1–R11.14 : **COMPLETE + NORMALIZED**.
- R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED CANDIDATE — FINAL DOCUMENTATION HEAD RE-GATE PENDING**.
- R12.1–R12.16 : **PLANNED / NOT STARTED**.
- R13–R16 : **PENDING / NOT STARTED**.

## R11 closure authority

- R11 canonical integrated report : `docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json` — `status=pass`, `blockers=[]`, semantic digest `ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170`.
- R11.14 accepted implementation head `f2693c8cfd4a7aaa5c73fc0a318ebaeef4ff0bb1`: R0 #1455 / `32769325414`, Python #1429 / `32769325329`, UI #1396 / `32769325281` SUCCESS.
- R11.14 final docs/evidence head `081fe88009aeb0cc89c6f91bd01184646d4aacdd`: R0 #1459 / `32769936597`, Python #1433 / `32769936407`, UI #1400 / `32769936452` SUCCESS.
- R11.14 implementation/evidence PR #183 merge `03dad4366ff5332b0728f548497f2051b7051138`.
- R11.14 continuity normalization head `b406ea16538843bbce8c75b0633c151e3bab2eb4`: R0 #1461 / `32771013589`, Python #1435 / `32771013516`, UI #1402 / `32771013711` SUCCESS.
- R11.14 normalization PR #184 merge `6d3c7eb557d940641977d18384e4f6d2bad42f3c`.
- R11.14 manual **CONDITIONAL NOT TRIGGERED**.
- Required preserved R11.5 TTS digest `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe` and R11.9 cinematic digest `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5` remain authoritative.

## R12 planning authority

Roadmap title : **R12 — Desktop applications**. Roadmap DoD : **créer, compiler et tester une application Windows moderne depuis le Project Wizard**.

- Planning branch : `r12/00-phase-plan`, créée exactement depuis normalized `main` `6d3c7eb557d940641977d18384e4f6d2bad42f3c`.
- Planning PR : #185.
- Plan candidate : `docs/roadmap/R12_PLAN.md`.
- Premier exact planning head accepté : `b085fbdb03d62bd06dbdd045eccded3a0de667ab`.
- R0 Repository Guard #1463 / `32771732655` — **SUCCESS**.
- Python Core #1437 / `32771732751` — **SUCCESS**; Python Ubuntu/Windows, package builds Ubuntu/Windows et KodeStudio smoke interne SUCCESS.
- KodeStudio UI Smoke #1404 / `32771732640` — **SUCCESS**.
- Cette mise à jour de continuité change les octets documentaires après le premier triplet; le nouveau head doit donc passer un triplet frais avant merge.

R12 étend les contrats R2 Project DNA/Project Wizard/KodeProduct existants; il ne crée pas un second desktop wizard. Existing Project DNA already has `ProjectType.DESKTOP_APP` and Windows platform semantics. Permanent R1–R11 governance remains in force.

### Frozen R12 subdivision index

| ID | Titre | Manuel |
| --- | --- | --- |
| R12.1 | Desktop contracts, identities, capability model + secure toolchain boundaries | NONE |
| R12.2 | Project DNA/KodeProduct desktop profiles + Project Wizard target selection | NONE |
| R12.3 | Deterministic desktop scaffold/template/workspace manifest engine | NONE |
| R12.4 | Framework-neutral MVVM/state/navigation/command/service contracts | NONE |
| R12.5 | WPF/.NET desktop adapter + build/test bridge | CONDITIONAL |
| R12.6 | WinUI 3/Windows App SDK adapter + Windows identity/deployment bridge | CONDITIONAL |
| R12.7 | Avalonia cross-platform desktop adapter | CONDITIONAL |
| R12.8 | Qt 6/CMake desktop adapter | CONDITIONAL |
| R12.9 | Tauri v2/Rust/WebView2 desktop adapter | CONDITIONAL |
| R12.10 | SQLite persistence, schema migrations, transactions + backup/recovery | NONE |
| R12.11 | Async/concurrency, cancellation, progress + UI-thread lifecycle safety | NONE |
| R12.12 | Local IPC contracts, framing, authorization + lifecycle isolation | CONDITIONAL |
| R12.13 | Accessibility, localization, theming, keyboard/focus + DPI/scaling QA | CONDITIONAL |
| R12.14 | Packaging/install/update/signing-state + rollback model | CONDITIONAL |
| R12.15 | CLI + KodeStudio Desktop workspace and governed Wizard workflow | NONE |
| R12.16 | Adversarial hardening + Wizard-to-Windows integrated acceptance | CONDITIONAL |

`CONDITIONAL` means hosted accepted exact-head evidence is used when sufficient. Manual intervention is triggered only when an authoritative OS/toolchain/runtime semantic required by the claim cannot be proved by CI. A triggered manual gate must freeze exact candidate SHA, bounded collector/commands, prerequisites, output, recovery/privacy steps and must be reviewed before progression. Missing evidence never manufactures PASS.

## R12 frozen technical baseline

- Windows-first phase DoD, without claiming that one Windows result validates Linux/macOS.
- WinUI 3/Windows App SDK is the modern native Windows adapter; WPF remains a supported first-class adapter.
- Avalonia is the cross-platform .NET/XAML adapter.
- Qt 6/CMake is the native cross-platform adapter.
- Tauri v2 is the Rust/WebView desktop adapter; Windows capability requires the relevant Rust/C++ Build Tools/WebView2 prerequisites.
- SQLite is the embedded persistence baseline; no global `sqlite3` CLI requirement.
- Toolchains are capability-probed. Kodepoia does not silently install SDKs, workloads, Qt, Rust, WebView2 or signing credentials.
- External processes always pass through ProcessSandbox + KillSwitch with Kodepoia-owned fixed argv templates; no shell command strings/raw model argv.
- Dependencies are pinned/locked; mutable `latest` dependency semantics are not accepted evidence.
- Network remains off by default for Kodepoia runtime operations. Explicit dependency restore is a governed build action, not an implicit installer.
- Signing states are explicit (`UNSIGNED`, `TEST_SIGNED`, `SIGNED`, `SIGNING_UNAVAILABLE`); phase acceptance does not require a user production certificate.
- R12 does not introduce production updater servers, app-store submission, mobile implementation or cloud/backend services.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Exact-head evidence mandatory.

## Planning acceptance rule

No R12.1 implementation is authorized until all of these are complete:

1. `R12_PLAN.md` and continuity synchronization exist on one planning branch from exact normalized `main`;
2. immutable planning candidate passes R0 Repository Guard + full Python Core + KodeStudio UI Smoke;
3. accepted planning head/run IDs are recorded and resulting documentation head is re-gated;
4. planning PR merges with `expected_head_sha`;
5. exactly one post-merge planning continuity-only normalization passes the same exact-head triplet and merges;
6. only then R12 planning becomes **ACCEPTED + NORMALIZED** and R12.1 becomes authorized.

## Execution rule after planning acceptance

Each subdivision : dedicated branch from normalized `main` → implementation/focused tests → exact-head R0/full Python/UI → satisfy REQUIRED/triggered CONDITIONAL manual state → final docs/evidence and re-gate if head changes → expected-SHA merge → exactly one continuity-only normalization + same gates + merge → only then next subdivision.

R12.16 follows anti-circular integrated acceptance: implementation head accepted before `R12_INTEGRATED_ACCEPTANCE.json` is generated; final evidence head is re-gated; then implementation/evidence merge and one final continuity normalization. Only that closure authorizes R13 planning.

## Next authorized action

Cycle = **R12 planning final documentation re-gate** on PR #185. Merge only after R0 + full Python Core + UI Smoke succeed on the exact new head, then perform exactly one planning continuity normalization. **R12.1 remains forbidden until that normalization merges.**
