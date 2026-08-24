# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1–R11.4 COMPLETE + NORMALIZED. R11.5 implementation + REQUIRED local TTS acceptance are ACCEPTED and PR #165 is MERGED; exactly one continuity-only R11.5 normalization is now pending. R11.6 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11.5 accepted implementation candidate `a9862b3bf475b259fe154d1e2486116ad04602f3` passed R0 #1394 / `32740559995`, Python #1368 / `32740559969`, UI #1335 / `32740559942`; the REQUIRED local Piper evidence passed with digest `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`. Final evidence-bound PR head `e58954e4c144d00f3747b9918b5657f495075452` passed R0 #1399 / `32744397834`, Python #1373 / `32744397841`, UI #1340 / `32744397831`, then PR #165 merged as `cd55311f8103266fec3cc1c33893cb052d490a92`. Current cycle is continuity-only normalization; its accepted merge will make R11.5 COMPLETE + NORMALIZED and authorize R11.6.

## État

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée le 21 août 2026; `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED** — plan PR #155 merge `523048121613a07554787a07701d1334c59cd2dd`; normalization PR #156 merge `95d582d864fe7a68f79e74d1383d4a2a2db7cee2`.
- R11.1 : **COMPLETE + NORMALIZED** — PR #157 merge `f1638f962e30e9f191dfc2a061fbe564e36efd0d`; normalization PR #158 merge `ce702323a134934c7543df30caa232ded391a831`; manual NONE.
- R11.2 : **COMPLETE + NORMALIZED** — PR #159 merge `b1c600a907431dc2202938cba038cd374145852b`; normalization PR #160 merge `b796a073b1d752fec02770a5102d651dda6d0949`; manual CONDITIONAL NOT TRIGGERED.
- R11.3 : **COMPLETE + NORMALIZED** — PR #161 merge `dee8b2148597fd3cc9d6b45f5525f7f89003a7bb`; normalization PR #162 merge `9c0436b039492c161da95cdcc706552b82d408e2`; manual NONE.
- R11.4 : **COMPLETE + NORMALIZED** — PR #163 merge `9ea0d35dbcde42282a9fab0f87ac950ab36d7275`; normalization PR #164 merge `354a0ec2f6889561afcee3b1f547e0b77ca3804b`; manual NONE.
- R11.5 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — PR #165 merge `cd55311f8103266fec3cc1c33893cb052d490a92`; manual REQUIRED **SATISFIED**.
- R11.6–R11.14 : **FROZEN / NOT STARTED**; R11.6 waits for R11.5 normalization.
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

## R11.4 closure

- Implementation `a662046c9fd38a198cc76c33b9012774f254407c`: R0 #1354 / `32729014444`, Python #1328 / `32729014573`, UI #1295 / `32729014540` SUCCESS; Ubuntu 944 passed / 8 skipped / 46 warnings; R7/R8/R9 PASS.
- Final docs `b3f2c0fb36e879dcaa5e3b42ba2bef387ab3c022`: R0 #1355 / `32729365291`, Python #1329 / `32729365293`, UI #1296 / `32729365309` SUCCESS.
- PR #163 merge `9ea0d35dbcde42282a9fab0f87ac950ab36d7275`.
- Normalization head `1fa19e9400e2c4ef1ee9c84840bb4b03084e1f27`: R0 #1357, Python #1331, UI #1298 SUCCESS; PR #164 merge `354a0ec2f6889561afcee3b1f547e0b77ca3804b`.
- Manual NONE. **R11.4 COMPLETE + NORMALIZED.**

## R11.5 closure in progress

- Base normalized main `354a0ec2f6889561afcee3b1f547e0b77ca3804b`; branch `r11/5-local-tts-adapters`; PR #165.
- Delivered backend-neutral TTS registry/capabilities, Piper-compatible fixed-argv adapter under `ProcessSandbox`, ephemeral `--input-file` text channel, deterministic request/cache identity, Godot/system-TTS accessibility-only capability path, bounded WAV/PCM QA, repository-local `models/` physical catalog and `KodeModelRegistry`, schemas/tests/docs and real local collector.
- Heavy model payloads live physically under `<repo>/models/` but are ignored by Git; tracked manifests carry stable model id, relative paths, SHA-256, license/provenance/use metadata and byte budgets. Existing logical `kodepoia.models.router.ModelRegistry` remains the LLM routing registry.
- Candidate 1 `441ea87436c6851cd106654454f955a91460f7af`: hosted gates SUCCESS but first real local evidence FAIL because generic R11.2 zero-clipping QA blocked one isolated full-scale endpoint sample. This remains rejected historical evidence and was never reclassified.
- Accepted implementation candidate 2 `a9862b3bf475b259fe154d1e2486116ad04602f3`: R0 #1394 / `32740559995`, Python #1368 / `32740559969`, UI #1335 / `32740559942` SUCCESS; Ubuntu **970 passed / 8 skipped / 46 warnings**; Windows Python, both package builds and internal KodeStudio smoke SUCCESS; R7/R8/R9 PASS.
- Candidate 2 keeps generic R11.2 `max_clipped_samples=0` unchanged and adds only `tts.local.v2`, bounded to at most 10 ppm full-scale endpoints with absolute cap 16; repeated saturation remains BLOCKED.
- REQUIRED local acceptance: **SATISFIED** on exact candidate 2 using catalog model `tts.piper.fr-FR.siwis-medium`.
  - evidence `docs/roadmap/R11_5_LOCAL_ACCEPTANCE.json`: 2865 bytes, repository LF SHA-256 `6406884deb38ab5be22fe99d5f3c50187953b4aa9cb8f59f5f21b4a396309e2e`;
  - canonical evidence digest `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`;
  - model SHA-256 `641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99`;
  - config SHA-256 `39479916c2db192b5ac9764daddd0c744d83e023ad890c6976c0633ae4df8959`;
  - synthesis return code 0, QA `tts.local.v2` PASS, no blockers, no timeout/cancel, no text in argv, ephemeral input deleted, no private recording/voice clone/collector download/audio retention.
- Evidence-bound final head `e58954e4c144d00f3747b9918b5657f495075452`: R0 #1399 / `32744397834`, Python #1373 / `32744397841`, UI #1340 / `32744397831` SUCCESS. Cross-platform LF normalization is explicit for `*_LOCAL_ACCEPTANCE.json` so raw evidence SHA is deterministic on Windows/Linux.
- PR #165 merge `cd55311f8103266fec3cc1c33893cb052d490a92`.
- Current branch `r11/5-continuity-normalization` changes only this continuity file. Its accepted merge makes **R11.5 COMPLETE + NORMALIZED** and authorizes R11.6.

## Baselines externes R11

- Godot 4.7 remains the R5 engine target.
- FFmpeg/ffprobe are capability-probed external runtimes; structured ffprobe JSON is preferred when used; no automatic install/download.
- TTS is backend-neutral. Piper is a local external runtime; Kodepoia performs no automatic collector-time download/install.
- Each voice/model's own model card/license/provenance is authoritative; repository-level licensing is not substituted for per-resource rights.
- Voice cloning/impersonation from arbitrary human recordings is outside R11 v1.0.
- R11.9 still requires real Godot 4.7 cinematic capture evidence.

## Permanent boundaries

`WorkspaceBoundary`/R8 VaultBoundary; `ProcessSandbox` + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key authority; R5 Godot authority all remain in force. Structured APIs only: no raw shell/argv/filter/TTS/Godot scripts supplied by a model. Network off by default; no automatic codecs/TTS/model/voice/plugin download. Exact-head evidence mandatory; missing evidence never means PASS; foundation change R1–R10 requires ADR.

## Execution rule

Each subdivision: dedicated branch from normalized `main` → frozen scope → focused tests + R0 + full Python Core + UI Smoke on one exact head → satisfy REQUIRED/triggered CONDITIONAL → final docs/evidence and re-gate if head changes → merge with expected SHA → exactly one continuity-only normalization + re-gate + merge → only then next subdivision.

Normalization run IDs remain in PR/merge metadata; do not create recursive commits solely to restate a normalization's own runs.

## Next authorized action

Cycle = **R11.5 continuity normalization only**. Gate exact head of `r11/5-continuity-normalization` with R0 + full Python Core + KodeStudio UI Smoke and merge with expected SHA. **That merge alone makes R11.5 COMPLETE + NORMALIZED and authorizes R11.6 (manual CONDITIONAL).**
