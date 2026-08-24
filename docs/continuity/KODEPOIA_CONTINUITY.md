# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1–R11.6 COMPLETE + NORMALIZED. R11.7 implementation is ACCEPTED and PR #169 is MERGED; exactly one continuity-only R11.7 normalization is now pending. R11.8 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11.6 normalization head `d8162c2015895594b66949ca3daf3a4f7995dd11` passed R0 #1406 / `32747513911`, Python #1380 / `32747514129`, UI #1347 / `32747513746`; PR #168 merged as `956fbf296a1ffc312fdd1e17e20ec39fb7fe20cc`. R11.7 implementation candidate `1d2347178b804ae46e8696a8fd78e88e8cb2d84b` passed R0 #1408 / `32748232176`, Python #1382 / `32748232050`, UI #1349 / `32748231962`; Ubuntu reported 990 passed / 8 skipped / 46 warnings and R7/R8/R9 PASS. Final documentation head `49f52432df1d3345dcd69e8862d14f9477d0d342` passed R0 #1409 / `32748449061`, Python #1383 / `32748449069`, UI #1350 / `32748449063`; PR #169 merged as `2ec8ea6b3718a08f31cfad969bc86d97992e46ab`. Manual R11.7 CONDITIONAL was NOT TRIGGERED because no real R10/Godot playback/render claim was accepted.

## État

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée le 21 août 2026; `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED** — plan PR #155 merge `523048121613a07554787a07701d1334c59cd2dd`; normalization PR #156 merge `95d582d864fe7a68f79e74d1383d4a2a2db7cee2`.
- R11.1 : **COMPLETE + NORMALIZED** — PR #157 merge `f1638f962e30e9f191dfc2a061fbe564e36efd0d`; normalization PR #158 merge `ce702323a134934c7543df30caa232ded391a831`; manual NONE.
- R11.2 : **COMPLETE + NORMALIZED** — PR #159 merge `b1c600a907431dc2202938cba038cd374145852b`; normalization PR #160 merge `b796a073b1d752fec02770a5102d651dda6d0949`; manual CONDITIONAL NOT TRIGGERED.
- R11.3 : **COMPLETE + NORMALIZED** — PR #161 merge `dee8b2148597fd3cc9d6b45f5525f7f89003a7bb`; normalization PR #162 merge `9c0436b039492c161da95cdcc706552b82d408e2`; manual NONE.
- R11.4 : **COMPLETE + NORMALIZED** — PR #163 merge `9ea0d35dbcde42282a9fab0f87ac950ab36d7275`; normalization PR #164 merge `354a0ec2f6889561afcee3b1f547e0b77ca3804b`; manual NONE.
- R11.5 : **COMPLETE + NORMALIZED** — PR #165 merge `cd55311f8103266fec3cc1c33893cb052d490a92`; normalization PR #166 merge `e12a575314afd511bb752f263c9e5b7e60c75d51`; manual REQUIRED SATISFIED.
- R11.6 : **COMPLETE + NORMALIZED** — PR #167 merge `742ea5b5e1e3b6ffa73f499198464295131e91bf`; normalization PR #168 merge `956fbf296a1ffc312fdd1e17e20ec39fb7fe20cc`; manual CONDITIONAL NOT TRIGGERED.
- R11.7 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — PR #169 merge `2ec8ea6b3718a08f31cfad969bc86d97992e46ab`; manual CONDITIONAL NOT TRIGGERED.
- R11.8–R11.14 : **FROZEN / NOT STARTED**; R11.8 waits for R11.7 normalization.
- R12–R16 : **PENDING / NOT STARTED**.

## Autorité historique

Les acceptances détaillées, preuves locales, rapports JSON et PR restent autoritatifs dans `docs/roadmap/R7_*`, `R8_*`, `R9_*`, `R10_*`, `R11_*` et l'historique GitHub. Cette continuité résume l'état de reprise sans réécrire les preuves historiques.

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

## R11.5 closure

- Accepted implementation candidate `a9862b3bf475b259fe154d1e2486116ad04602f3`: R0 #1394 / `32740559995`, Python #1368 / `32740559969`, UI #1335 / `32740559942` SUCCESS; Ubuntu **970 passed / 8 skipped / 46 warnings**; R7/R8/R9 PASS.
- REQUIRED local TTS acceptance **SATISFIED** with `tts.piper.fr-FR.siwis-medium`; canonical evidence digest `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`.
- Final evidence-bound head `e58954e4c144d00f3747b9918b5657f495075452`: R0 #1399 / `32744397834`, Python #1373 / `32744397841`, UI #1340 / `32744397831` SUCCESS.
- PR #165 merge `cd55311f8103266fec3cc1c33893cb052d490a92`; normalization `ea26ac0444e8b85797538fddde44979e16278082`: R0 #1401 / `32744856545`, Python #1375 / `32744856464`, UI #1342 / `32744856455`; PR #166 merge `e12a575314afd511bb752f263c9e5b7e60c75d51`.
- **R11.5 COMPLETE + NORMALIZED.**

## R11.6 closure

- Base normalized main `e12a575314afd511bb752f263c9e5b7e60c75d51`; PR #167.
- Delivered strict speech-alignment/phoneme/viseme timelines, bounded coarticulation, lip-sync QA and caption timing bridge; no external aligner accuracy claim.
- Implementation `ea86762ecaa5ab16f6637701638c3461eea9d5ce`: R0 #1403 / `32745871626`, Python #1377 / `32745871312`, UI #1344 / `32745871357` SUCCESS; Ubuntu **981 passed / 8 skipped / 46 warnings**; R7/R8/R9 PASS.
- Final docs `85a0d1b793f0ec9aa657bfc0f56d1be22424534a`: R0 #1404 / `32746087783`, Python #1378 / `32746087766`, UI #1345 / `32746088179` SUCCESS.
- PR #167 merge `742ea5b5e1e3b6ffa73f499198464295131e91bf`.
- Normalization `d8162c2015895594b66949ca3daf3a4f7995dd11`: R0 #1406 / `32747513911`, Python #1380 / `32747514129`, UI #1347 / `32747513746` SUCCESS; PR #168 merge `956fbf296a1ffc312fdd1e17e20ec39fb7fe20cc`.
- Manual CONDITIONAL **NOT TRIGGERED**. **R11.6 COMPLETE + NORMALIZED.**

## R11.7 closure in progress

- Base normalized main `956fbf296a1ffc312fdd1e17e20ec39fb7fe20cc`; branch `r11/7-facial-performance-lod`; PR #169.
- Delivered strict R10 facial target catalog adapter, `FacialPerformanceProfile`, target/range validation, facial LOD with critical-semantic preservation, deterministic R11.6 viseme→curve generation, explicit clipping accounting, facial QA and typed R5 Godot animation intents without raw script/resource/path surface.
- No topology/rig generation, Blender editing or real Godot import/playback/render claim.
- Implementation `1d2347178b804ae46e8696a8fd78e88e8cb2d84b`: R0 #1408 / `32748232176`, Python #1382 / `32748232050`, UI #1349 / `32748231962` SUCCESS; Ubuntu **990 passed / 8 skipped / 46 warnings**; Windows Python/internal UI/package builds SUCCESS; R7/R8/R9 PASS.
- Final documentation head `49f52432df1d3345dcd69e8862d14f9477d0d342`: R0 #1409 / `32748449061`, Python #1383 / `32748449069`, UI #1350 / `32748449063` SUCCESS.
- PR #169 merge `2ec8ea6b3718a08f31cfad969bc86d97992e46ab`.
- Manual CONDITIONAL **NOT TRIGGERED** because accepted behavior is fully proved from synthetic R10-shaped metadata and deterministic CI; no real R10/Godot behavior claim is made.
- Current branch `r11/7-continuity-normalization` changes only this continuity file. Its accepted merge makes **R11.7 COMPLETE + NORMALIZED** and authorizes R11.8.

## Baselines externes R11

- Godot 4.7 remains the R5 engine target.
- FFmpeg/ffprobe are capability-probed external runtimes; structured ffprobe JSON is preferred when used; no automatic install/download.
- TTS is backend-neutral; Piper remains an external configured runtime, never auto-downloaded by Kodepoia.
- R11.6 remains aligner-neutral unless a later triggered conditional gate accepts a real backend/native aligner.
- R11.7 emits only typed facial animation intent; R10 remains authoritative for target identity/ranges and R5 for Godot materialization.
- R11.9 still requires real Godot 4.7 movie-capture evidence.

## Permanent boundaries

`WorkspaceBoundary`/R8 VaultBoundary; `ProcessSandbox` + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key authority; R5 Godot authority all remain in force. Structured APIs only: no raw shell/argv/filter/TTS/Godot scripts supplied by a model. Network off by default; no automatic codecs/TTS/model/voice/plugin download. Exact-head evidence mandatory; missing evidence never means PASS; foundation change R1–R10 requires ADR.

## Execution rule

Each subdivision: dedicated branch from normalized `main` → frozen scope → focused tests + R0 + full Python Core + UI Smoke on one exact head → satisfy REQUIRED/triggered CONDITIONAL → final docs/evidence and re-gate if head changes → merge with expected SHA → exactly one continuity-only normalization + re-gate + merge → only then next subdivision.

Normalization run IDs remain in PR/merge metadata; do not create recursive commits solely to restate a normalization's own runs.

## Next authorized action

Cycle = **R11.7 continuity normalization only**. Gate exact head of `r11/7-continuity-normalization` with R0 + full Python Core + KodeStudio UI Smoke and merge with expected SHA. **That merge alone makes R11.7 COMPLETE + NORMALIZED and authorizes R11.8 (manual NONE).**
