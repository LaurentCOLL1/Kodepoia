# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1–R11.12 COMPLETE + NORMALIZED. R11.13 implementation is ACCEPTED + MERGED via PR #181; exactly one continuity-only R11.13 normalization is now pending. R11.14 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11.13 final documentation head `78c60da9c8dfad1f6802207b812bdb84204572a4` passed R0 #1448 / `32764105609`, Python #1422 / `32764105564`, UI #1389 / `32764105529`; PR #181 merge `e70a0b112636cd72e92e39f22603b97d6f15e7a5`. Manual NONE.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED**.
- R11.1–R11.11 : **COMPLETE + NORMALIZED**.
- R11.12 : **COMPLETE + NORMALIZED** — implementation PR #179 merge `562a15393daa9ca8892ca1ec6dfcda4986fa9e0e`; normalization PR #180 merge `3ca78857de17280c758912d35705881f8d31c73a`; manual CONDITIONAL NOT TRIGGERED.
- R11.13 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — PR #181 merge `e70a0b112636cd72e92e39f22603b97d6f15e7a5`; manual NONE.
- R11.14 : **FROZEN / NOT STARTED** until R11.13 normalization merges.
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

## Required local evidence already accepted

- R11.5 Piper local TTS evidence: `docs/roadmap/R11_5_LOCAL_ACCEPTANCE.json`; accepted digest `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`.
- R11.9 Godot cinematic evidence: `docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json`; digest `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`; Godot `4.7.2.stable.steam.ed1daf0bf`, ffprobe `8.1.1-full_build-www.gyan.dev`, 640×360 at 30 FPS, 90 frames / 3.0 s, A/V drift `0.0 s`.

## R11.12 closure

- Final docs head `a7809c9411bcc4c2ee392acf6d03d1c2800635c7`: R0 #1443 / `32762206491`, Python #1417 / `32762206588`, UI #1384 / `32762206575` SUCCESS.
- PR #179 merge `562a15393daa9ca8892ca1ec6dfcda4986fa9e0e`.
- Normalization head `f30bfc93ed05f05b098ecbea9d8dfb9b696742a4`: R0 #1445 / `32762570082`, Python #1419 / `32762570009`, UI #1386 / `32762570019` SUCCESS; PR #180 merge `3ca78857de17280c758912d35705881f8d31c73a`.
- **R11.12 COMPLETE + NORMALIZED.** Manual CONDITIONAL NOT TRIGGERED because no concrete user Godot save format was claimed.

## R11.13 closure in progress

- Base normalized main `3ca78857de17280c758912d35705881f8d31c73a`; branch `r11/13-cli-kodestudio-ux`; PR #181.
- Delivered structured `kodepoia r11` groups for all 11 frozen capabilities with stable JSON/exit semantics and no raw argv/executable/filter/model-path/script/migration-code surfaces.
- Added a shared read-only R11 workspace registry and KodeStudio **Media / Franchise** navigation entry (intentional navigation 9→10) with Audio, Voice, Cinematics, Franchise/Canon and Persistence tabs.
- R11.5/R11.9 evidence is surfaced without manufacturing a live runtime claim; runtime state defaults `NOT_PROBED`.
- Refresh does not launch an external runtime. Cancel reuses the global KillSwitch.
- Added dedicated accessibility and pseudo-localization coverage; no raw command or migration-code editor exists.
- Accepted implementation head `79a891eaede7e5ecf7d8daf35846b20b1d3d02f9`: R0 #1447 / `32763810080`, Python #1421 / `32763810070`, UI #1388 / `32763810029` SUCCESS.
- Final docs head `78c60da9c8dfad1f6802207b812bdb84204572a4`: R0 #1448 / `32764105609`, Python #1422 / `32764105564`, UI #1389 / `32764105529` SUCCESS.
- PR #181 merged as `e70a0b112636cd72e92e39f22603b97d6f15e7a5`.
- Manual **NONE**.
- Current branch `r11/13-postmerge-continuity-normalization` changes only this continuity file. Its accepted merge makes **R11.13 COMPLETE + NORMALIZED** and authorizes R11.14.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 governance/security/privacy/license; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key; R5 Godot authority remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory.

## Execution rule

Each subdivision: dedicated branch from normalized `main` → focused tests + exact-head R0/full Python/UI → satisfy REQUIRED/triggered CONDITIONAL manual state → final docs/evidence and re-gate if head changes → expected-SHA merge → exactly one continuity-only normalization + same exact-head gates + merge → only then next subdivision.

## Next authorized action

Cycle = **R11.13 continuity normalization only**. Gate exact head of `r11/13-postmerge-continuity-normalization`; merge it with expected SHA. **Only that merge authorizes R11.14.**
