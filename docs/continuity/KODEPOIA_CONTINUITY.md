# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1–R11.9 COMPLETE + NORMALIZED. R11.10 implementation is ACCEPTED + MERGED via PR #175; exactly one continuity-only R11.10 normalization is now pending. R11.11 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11.10 accepted implementation head `5fb1b80a212880bd510977d54a570859c532c206`; final docs head `04c9c7fa68723b2bcc02962325a1a21f8593e9ff` passed R0 #1433 / `32759464634`, Python #1407 / `32759464632`, UI #1374 / `32759464653`; PR #175 merge `b6169b790b6f4afccd305c33d1c51cf4aa7a5bbd`. Current work must be R11.10 continuity normalization only.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée le 21 août 2026.
- `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED**.
- R11.1 : **COMPLETE + NORMALIZED** — manual NONE.
- R11.2 : **COMPLETE + NORMALIZED** — manual CONDITIONAL NOT TRIGGERED.
- R11.3 : **COMPLETE + NORMALIZED** — manual NONE.
- R11.4 : **COMPLETE + NORMALIZED** — manual NONE.
- R11.5 : **COMPLETE + NORMALIZED** — manual REQUIRED SATISFIED.
- R11.6 : **COMPLETE + NORMALIZED** — manual CONDITIONAL NOT TRIGGERED.
- R11.7 : **COMPLETE + NORMALIZED** — manual CONDITIONAL NOT TRIGGERED.
- R11.8 : **COMPLETE + NORMALIZED** — manual NONE.
- R11.9 : **COMPLETE + NORMALIZED** — manual REQUIRED SATISFIED; normalization PR #174 merge `470d8c63eda6bbc3e1a8151c6e050df334a94dba`.
- R11.10 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — manual NONE.
- R11.11–R11.14 : **FROZEN / NOT STARTED** until authorized sequentially.
- R12–R16 : **PENDING / NOT STARTED**.

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

## R11.5–R11.8 closure

- R11.5: local Piper TTS acceptance SATISFIED; evidence digest `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`; PR #165 merge `cd55311f8103266fec3cc1c33893cb052d490a92`; normalization #166 merge `e12a575314afd511bb752f263c9e5b7e60c75d51`.
- R11.6: PR #167 merge `742ea5b5e1e3b6ffa73f499198464295131e91bf`; normalization #168 merge `956fbf296a1ffc312fdd1e17e20ec39fb7fe20cc`.
- R11.7: PR #169 merge `2ec8ea6b3718a08f31cfad969bc86d97992e46ab`; normalization #170 merge `c3d091fb88acfc2bd054521fd3c76904eff0b885`.
- R11.8: PR #171 merge `7d7a421e069a9d8beaf4d9160b06351752946e73`; normalization merge `e01f18ee5b7fbd7df513e10ad96c1ac35d83d6e5`.

## R11.9 closure

- Accepted manual candidate `087eae19ea03dd544d75a08c1eb348fe187624c5`.
- REQUIRED local Godot gate SATISFIED on Windows with Godot `4.7.2.stable.steam.ed1daf0bf` and ffprobe `8.1.1-full_build-www.gyan.dev`.
- Accepted evidence `docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json`; digest `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`.
- Capture: 640×360, 30 FPS, 90/90 frames, 3.0 s video/audio/container, stereo 48 kHz, A/V drift `0.0 s`, SHA-256 `2f383635f2ee94def1ee832ffd742f0fc2cf41af18ef939078f72746e6e8a194`.
- Final evidence-bound head `c0934fcedc05368acbfe94529e6f971bf426e546`: R0 #1426 / `32757919223`, Python #1400 / `32757919234`, UI #1367 / `32757919306` SUCCESS.
- PR #173 merge `5b491cee157e4ba9200a5608cca3721321b768e3`.
- Normalization head `94bfd68f35a2581cec1e0b76c33ef904044e42b6`: R0 #1428 / `32758284107`, Python #1402 / `32758284020`, UI #1369 / `32758284142` SUCCESS; PR #174 merge `470d8c63eda6bbc3e1a8151c6e050df334a94dba`.
- **R11.9 COMPLETE + NORMALIZED.**

## R11.10 closure in progress

- Base normalized main `470d8c63eda6bbc3e1a8151c6e050df334a94dba`; branch `r11/10-continuity-bridge`; PR #175.
- Delivered typed `ContinuityFact`/`ContinuitySnapshot`, explicit ACTIVE/STALE/MISSING/DELETED/CONFLICTED states, canonical snapshot SHA-256, deterministic structural findings, target/digest-bound cross-project bridge packages tied to R8 revision identity, and fixed `compare_only_no_canon_mutation` promotion policy.
- Initial head `089ab8bb5bedc74d1b2750ae201b5176ad51216b` rejected because one new schema test tried to resolve `kodepoia.local` through the network; core tests otherwise had 1023 PASS. Bridge schema was made self-contained with local `$defs` and no semantics were weakened.
- Accepted implementation head `5fb1b80a212880bd510977d54a570859c532c206`: R0 #1432 / `32759111326`, Python #1406 / `32759111337`, UI #1373 / `32759111321` SUCCESS.
- Final documentation head `04c9c7fa68723b2bcc02962325a1a21f8593e9ff`: R0 #1433 / `32759464634`, Python #1407 / `32759464632`, UI #1374 / `32759464653` SUCCESS.
- PR #175 merge `b6169b790b6f4afccd305c33d1c51cf4aa7a5bbd`.
- Manual NONE.
- Current branch `r11/10-postmerge-continuity-normalization` changes only this continuity file. Its accepted merge makes **R11.10 COMPLETE + NORMALIZED** and authorizes R11.11.

## Runtime discovery convention

External runtimes resolve in order: explicit governed configured path → `PATH` → fixed provider-specific known locations. For Windows Steam libraries, drive letters are variable; bounded product-relative paths such as `<drive>:\SteamLibrary\steamapps\common\<Product>\<Executable>` are allowed across mounted filesystem drives without arbitrary recursive user-data crawling.

## Permanent boundaries

`WorkspaceBoundary`/R8 VaultBoundary; `ProcessSandbox` + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key authority; R5 Godot authority remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Foundation changes R1–R10 require ADR.

## Execution rule

Each subdivision: dedicated branch from normalized `main` → focused tests + R0 + full Python Core + UI Smoke on exact head → satisfy manual state → docs/evidence re-gate if head changes → expected-SHA merge → exactly one continuity-only normalization + exact-head re-gate + merge → only then next subdivision.

## Next authorized action

Cycle = **R11.10 continuity normalization only**. Gate exact head of `r11/10-postmerge-continuity-normalization` with R0 + full Python Core + KodeStudio UI Smoke and merge with expected SHA. **Only that merge authorizes R11.11.**
