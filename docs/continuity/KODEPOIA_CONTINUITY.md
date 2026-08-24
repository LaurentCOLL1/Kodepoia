# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1–R11.3 COMPLETE + NORMALIZED. R11.4 implementation ACCEPTED + MERGED; exactly one continuity-only R11.4 normalization is now pending. R11.5 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11.3 normalization head `d6d50578cf3d16838edffce8e126c1e2d92ac9a0` passed R0 #1352 / `32728384648`, Python #1326 / `32728384577`, UI #1293 / `32728384620`; PR #162 merged as `9c0436b039492c161da95cdcc706552b82d408e2`, authorizing R11.4. R11.4 implementation head `a662046c9fd38a198cc76c33b9012774f254407c` passed R0 #1354 / `32729014444`, Python #1328 / `32729014573`, UI #1295 / `32729014540`; Ubuntu reported 944 passed / 8 skipped / 46 warnings. Final R11.4 documentation head `b3f2c0fb36e879dcaa5e3b42ba2bef387ab3c022` passed R0 #1355 / `32729365291`, Python #1329 / `32729365293`, UI #1296 / `32729365309`; PR #163 merged as `9ea0d35dbcde42282a9fab0f87ac950ab36d7275`. Manual R11.4 = NONE. Current cycle is continuity-only normalization; its accepted merge will make R11.4 COMPLETE + NORMALIZED and authorize R11.5, whose manual state is REQUIRED.

## État

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée le 21 août 2026; `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED** — plan PR #155 merge `523048121613a07554787a07701d1334c59cd2dd`; normalization PR #156 merge `95d582d864fe7a68f79e74d1383d4a2a2db7cee2`.
- R11.1 : **COMPLETE + NORMALIZED** — PR #157 merge `f1638f962e30e9f191dfc2a061fbe564e36efd0d`; normalization PR #158 merge `ce702323a134934c7543df30caa232ded391a831`; manual NONE.
- R11.2 : **COMPLETE + NORMALIZED** — PR #159 merge `b1c600a907431dc2202938cba038cd374145852b`; normalization PR #160 merge `b796a073b1d752fec02770a5102d651dda6d0949`; manual CONDITIONAL NOT TRIGGERED.
- R11.3 : **COMPLETE + NORMALIZED** — PR #161 merge `dee8b2148597fd3cc9d6b45f5525f7f89003a7bb`; normalization PR #162 merge `9c0436b039492c161da95cdcc706552b82d408e2`; manual NONE.
- R11.4 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — PR #163 merge `9ea0d35dbcde42282a9fab0f87ac950ab36d7275`; manual NONE.
- R11.5–R11.14 : **FROZEN / NOT STARTED**; R11.5 waits for R11.4 normalization.
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

## R11.1 closure

- Implementation `46ee14f3e94ed8c5c1cadbf139a890fab853929f`: R0 #1339, Python #1313, UI #1280 SUCCESS; Ubuntu 914 passed / 8 skipped / 46 warnings.
- Final docs `70969202b8d604f7b91ca47aa980f96850879a5b`: R0 #1340, Python #1314, UI #1281 SUCCESS.
- PR #157 merge `f1638f962e30e9f191dfc2a061fbe564e36efd0d`.
- Normalization `638789fc43fe364cc236b27f0f7149dab9bdc887`: R0 #1342 / `32725211522`, Python #1316 / `32725211401`, UI #1283 / `32725211509` SUCCESS; PR #158 merge `ce702323a134934c7543df30caa232ded391a831`.
- Manual NONE. **R11.1 COMPLETE + NORMALIZED.**

## R11.2 closure

- Implementation `103365dc7d5e3d725e0a9d23a839283079fe959c`: R0 #1344 / `32725655275`, Python #1318 / `32725655403`, UI #1285 / `32725655286` SUCCESS; Ubuntu 924 passed / 8 skipped / 46 warnings.
- Final docs `cab6128d16b243e57aa12592bb3d4bf8e5cfa01e`: R0 #1345 / `32725827200`, Python #1319 / `32725827205`, UI #1286 / `32725827120` SUCCESS.
- PR #159 merge `b1c600a907431dc2202938cba038cd374145852b`.
- Normalization `dfbba473c5c6055475489f0773ec0ec81280d532`: R0 #1347 / `32726075236`, Python #1321 / `32726075380`, UI #1288 / `32726075297` SUCCESS; PR #160 merge `b796a073b1d752fec02770a5102d651dda6d0949`.
- Manual CONDITIONAL **NOT TRIGGERED**. **R11.2 COMPLETE + NORMALIZED.**

## R11.3 closure

- Implementation `a835ab4491b5c49268ac85e389a2584ba379fcf3`: R0 #1349 / `32726607784`, Python #1323 / `32726607816`, UI #1290 / `32726607841` SUCCESS; Ubuntu 934 passed / 8 skipped / 46 warnings.
- Final docs `f43707da56b5268677fa1104a5234025d7167025`: R0 #1350 / `32728038957`, Python #1324 / `32728038903`, UI #1291 / `32728039219` SUCCESS.
- PR #161 merge `dee8b2148597fd3cc9d6b45f5525f7f89003a7bb`.
- Normalization `d6d50578cf3d16838edffce8e126c1e2d92ac9a0`: R0 #1352 / `32728384648`, Python #1326 / `32728384577`, UI #1293 / `32728384620` SUCCESS; PR #162 merge `9c0436b039492c161da95cdcc706552b82d408e2`.
- Manual NONE. **R11.3 COMPLETE + NORMALIZED.**

## R11.4 closure in progress

- Base normalized main `9c0436b039492c161da95cdcc706552b82d408e2`; branch `r11/4-voice-profiles-governance`; PR #163.
- Delivered engine-neutral VoiceProfile/prosody, bounded BCP-47-shaped locale normalization/fallbacks, Unicode NFC with bidi/control rejection, locale-aware pronunciation lexicon, VoiceModelBinding separated from profile identity, explicit provenance/license/allowed-use/authorization governance with `RIGHTS_BLOCKED`, typed text/pause/emphasis markup with raw XML/SSML rejection, schemas/tests/docs.
- No real synthesis, cloning/training, biometric inference or reference-recording surface.
- Implementation `a662046c9fd38a198cc76c33b9012774f254407c`: R0 #1354 / `32729014444`, Python #1328 / `32729014573`, UI #1295 / `32729014540` SUCCESS; Ubuntu **944 passed / 8 skipped / 46 warnings**; Windows Python/internal UI/package builds SUCCESS; R7/R8/R9 PASS.
- Final docs `b3f2c0fb36e879dcaa5e3b42ba2bef387ab3c022`: R0 #1355 / `32729365291`, Python #1329 / `32729365293`, UI #1296 / `32729365309` SUCCESS.
- Manual **NONE**.
- PR #163 merge `9ea0d35dbcde42282a9fab0f87ac950ab36d7275`.
- Current branch `r11/4-continuity-normalization` changes only this continuity file. Its accepted merge makes **R11.4 COMPLETE + NORMALIZED** and authorizes R11.5.

## Baselines externes R11

- Godot 4.7 remains the R5 engine target.
- FFmpeg/ffprobe are capability-probed external runtimes; structured ffprobe JSON is preferred when used; no automatic install/download.
- TTS is backend-neutral. Current Piper development is compatible with a local adapter target, but runtime and voice/model bytes remain external and explicitly configured; Kodepoia performs no automatic download/install.
- Each voice/model's own model card/license/provenance is authoritative; repository-level licensing is not substituted for per-resource rights.
- Voice cloning/impersonation from arbitrary human recordings is outside R11 v1.0.
- R11.5 requires real local TTS evidence with an explicitly approved/configured voice; R11.9 requires real Godot 4.7 cinematic capture evidence.

## Permanent boundaries

`WorkspaceBoundary`/R8 VaultBoundary; `ProcessSandbox` + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key authority; R5 Godot authority all remain in force. Structured APIs only: no raw shell/argv/filter/TTS/Godot scripts supplied by a model. Network off by default; no automatic codecs/TTS/model/voice/plugin download. Exact-head evidence mandatory; missing evidence never means PASS; foundation change R1–R10 requires ADR.

## Execution rule

Each subdivision: dedicated branch from normalized `main` → frozen scope → focused tests + R0 + full Python Core + UI Smoke on one exact head → satisfy REQUIRED/triggered CONDITIONAL → final docs/evidence and re-gate if head changes → merge with expected SHA → exactly one continuity-only normalization + re-gate + merge → only then next subdivision.

Normalization run IDs remain in PR/merge metadata; do not create recursive commits solely to restate a normalization's own runs.

## Next authorized action

Cycle = **R11.4 continuity normalization only**. Gate exact head of `r11/4-continuity-normalization` with R0 + full Python Core + KodeStudio UI Smoke and merge with expected SHA. **That merge alone makes R11.4 COMPLETE + NORMALIZED and authorizes R11.5 (manual REQUIRED).**
