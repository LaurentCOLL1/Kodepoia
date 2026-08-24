# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1 COMPLETE + NORMALIZED. R11.2 implementation ACCEPTED + MERGED; its continuity-only normalization is in progress. R11.3 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11.1 normalization head `638789fc43fe364cc236b27f0f7149dab9bdc887` passed R0 #1342 / `32725211522`, Python #1316 / `32725211401`, UI #1283 / `32725211509`; PR #158 merged as `ce702323a134934c7543df30caa232ded391a831`. R11.2 implementation head `103365dc7d5e3d725e0a9d23a839283079fe959c` passed R0 #1344 / `32725655275`, Python #1318 / `32725655403`, UI #1285 / `32725655286`; final docs head `cab6128d16b243e57aa12592bb3d4bf8e5cfa01e` passed R0 #1345 / `32725827200`, Python #1319 / `32725827205`, UI #1286 / `32725827120`; PR #159 merged as `b1c600a907431dc2202938cba038cd374145852b`. R11.2 manual CONDITIONAL was NOT TRIGGERED. Current cycle is continuity-only normalization; its accepted merge will make R11.2 COMPLETE + NORMALIZED and authorize R11.3.

## État

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée le 21 août 2026; `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED** — plan PR #155 merge `523048121613a07554787a07701d1334c59cd2dd`; normalization PR #156 merge `95d582d864fe7a68f79e74d1383d4a2a2db7cee2`.
- R11.1 : **COMPLETE + NORMALIZED** — manual NONE; implementation/docs PR #157 merge `f1638f962e30e9f191dfc2a061fbe564e36efd0d`; normalization PR #158 merge `ce702323a134934c7543df30caa232ded391a831`.
- R11.2 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — manual CONDITIONAL NOT TRIGGERED; PR #159 merge `b1c600a907431dc2202938cba038cd374145852b`.
- R11.3–R11.14 : FROZEN / NOT STARTED; R11.3 waits for R11.2 normalization.
- R12–R16 : PENDING / NOT STARTED.

## Autorité historique

Les acceptances détaillées, preuves locales, rapports JSON et PR restent autoritatifs dans `docs/roadmap/R7_*`, `R8_*`, `R9_*`, `R10_*`, `R11_*` et l'historique GitHub. Cette continuité ne remplace pas ces preuves.

- R7, R8, R9 : COMPLETE + NORMALIZED; rapports intégrés PASS.
- R10 : COMPLETE + NORMALIZED; `R10_INTEGRATED_ACCEPTANCE.json` a `status=pass`, `blockers=[]`, digest `48c18aacc916fb064810b36ada5a179f1d3b149912bea8a19a3295da1826a3c8`; final normalization PR #154 merge `d627f26a086c46273ce378a2d4d9919db0e9dd3a`.

## R11 structure gelée

Plan autoritatif : `docs/roadmap/R11_PLAN.md`.

| ID | Titre | Manuel |
| --- | --- | --- |
| R11.1 | Media/voice/cinematic contracts, identities + secure runtime boundaries | NONE |
| R11.2 | Audio ingest/transcode/analysis + deterministic QA | CONDITIONAL |
| R11.3 | Music/SFX/Foley cue system + loops/variants/spatialization packaging | NONE |
| R11.4 | Voice Profiles, pronunciation/prosody + rights/provenance governance | NONE |
| R11.5 | Multilingual local TTS adapters, synthesis cache + real-runtime acceptance | REQUIRED |
| R11.6 | Speech alignment, phoneme/viseme timeline + lip-sync QA | CONDITIONAL |
| R11.7 | Facial performance mapping + facial LOD + R10/R5 integration | CONDITIONAL |
| R11.8 | Cinematic shots, sequences + deterministic timeline model | NONE |
| R11.9 | Godot 4.7 cinematic assembly, movie capture + A/V sync acceptance | REQUIRED |
| R11.10 | Continuity Bridge across scenes/projects | NONE |
| R11.11 | Franchise DNA + versioned Canon graph/conflict policy | NONE |
| R11.12 | Persistence/SaveBridge schemas, migrations + compatibility/rollback | CONDITIONAL |
| R11.13 | CLI + KodeStudio Audio/Voice/Cinematics/Franchise UX | NONE |
| R11.14 | Adversarial hardening + R11 integrated acceptance | CONDITIONAL |

## R11.1 closure

- Base normalized main `95d582d864fe7a68f79e74d1383d4a2a2db7cee2`.
- Contracts/serialization/runtime boundary under `src/kodepoia/media/`; boundary never launches arbitrary commands and reuses `kodepoia.core.sandbox.ProcessSandbox` for future execution.
- Implementation `46ee14f3e94ed8c5c1cadbf139a890fab853929f`: R0 #1339, Python #1313, UI #1280 SUCCESS; Ubuntu 914 passed / 8 skipped / 46 warnings.
- Final docs `70969202b8d604f7b91ca47aa980f96850879a5b`: R0 #1340, Python #1314, UI #1281 SUCCESS.
- PR #157 merge `f1638f962e30e9f191dfc2a061fbe564e36efd0d`.
- Normalization `638789fc43fe364cc236b27f0f7149dab9bdc887`: R0 #1342 / `32725211522`, Python #1316 / `32725211401`, UI #1283 / `32725211509` SUCCESS; PR #158 merge `ce702323a134934c7543df30caa232ded391a831`.
- Manual NONE. **R11.1 COMPLETE + NORMALIZED.**

## R11.2 closure in progress

- Base normalized main `ce702323a134934c7543df30caa232ded391a831`; branch `r11/2-audio-pipeline-qa`; PR #159.
- Delivered deterministic pure-Python WAV/PCM inspection, bounded representative ffprobe JSON parsing, typed allowlisted transform recipes, deterministic audio QA, schemas/tests/docs.
- No arbitrary FFmpeg filter/argv surface; no real FFmpeg codec/transcode behavior claimed.
- Implementation `103365dc7d5e3d725e0a9d23a839283079fe959c`: R0 #1344 / `32725655275`, Python #1318 / `32725655403`, UI #1285 / `32725655286` SUCCESS; Ubuntu **924 passed / 8 skipped / 46 warnings**, R7/R8/R9 PASS.
- Final docs `cab6128d16b243e57aa12592bb3d4bf8e5cfa01e`: R0 #1345 / `32725827200`, Python #1319 / `32725827205`, UI #1286 / `32725827120`, all SUCCESS.
- Manual CONDITIONAL **NOT TRIGGERED**, because acceptance does not assert actual FFmpeg runtime behavior.
- PR #159 merge `b1c600a907431dc2202938cba038cd374145852b`.
- Current branch `r11/2-continuity-normalization` must modify continuity only; its accepted merge makes **R11.2 COMPLETE + NORMALIZED** and authorizes R11.3.

## Baselines externes R11

- Godot 4.7 remains the R5 engine target.
- FFmpeg/ffprobe are capability-probed external runtimes; structured ffprobe JSON is preferred when used; no automatic install/download.
- TTS is backend-neutral. Piper is an optional local adapter candidate; runtimes and voice models are external resources with explicit license/provenance.
- Voice cloning/impersonation from arbitrary human recordings is outside R11 v1.0.
- R11.5 requires real local TTS evidence with an explicitly approved/configured voice; R11.9 requires real Godot 4.7 cinematic capture evidence.

## Permanent boundaries

`WorkspaceBoundary`/R8 VaultBoundary; `ProcessSandbox` + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key authority; R5 Godot authority all remain in force. Structured APIs only: no raw shell/argv/filter/TTS/Godot scripts supplied by a model. Network off by default; no automatic codecs/TTS/model/voice/plugin download. Exact-head evidence mandatory; missing evidence never means PASS; foundation change R1–R10 requires ADR.

## Execution rule

Each subdivision: dedicated branch from normalized `main` → frozen scope → focused tests + R0 + full Python Core + UI Smoke on one exact head → satisfy REQUIRED/triggered CONDITIONAL → final docs/evidence and re-gate if head changes → merge with expected SHA → exactly one continuity-only normalization + re-gate + merge → only then next subdivision.

Normalization run IDs remain in PR/merge metadata; do not create recursive commits solely to restate a normalization's own runs.

## Next authorized action

Cycle = **R11.2 continuity normalization only**. Gate exact head of `r11/2-continuity-normalization` with R0 + full Python Core + UI Smoke and merge with expected SHA. **That merge alone makes R11.2 COMPLETE + NORMALIZED and authorizes R11.3 (manual NONE).**
