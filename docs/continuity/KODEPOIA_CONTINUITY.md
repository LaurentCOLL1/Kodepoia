# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1–R11.11 COMPLETE + NORMALIZED. R11.12 implementation is ACCEPTED + MERGED via PR #179; exactly one continuity-only R11.12 normalization is now pending. R11.13 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11.12 final documentation head `a7809c9411bcc4c2ee392acf6d03d1c2800635c7` passed R0 #1443 / `32762206491`, Python #1417 / `32762206588`, UI #1384 / `32762206575`; PR #179 merge `562a15393daa9ca8892ca1ec6dfcda4986fa9e0e`. Manual CONDITIONAL NOT TRIGGERED because only synthetic SaveBridge/R5 contract fixtures are claimed.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée le 21 août 2026; `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED**.
- R11.1–R11.10 : **COMPLETE + NORMALIZED**.
- R11.11 : **COMPLETE + NORMALIZED** — PR #177 merge `7140ddec12d313760ae84e942c7180c63dbce78e`; normalization PR #178 merge `7fa6d1294d10a9b0e602b412db644cf68fb66ede`; manual NONE.
- R11.12 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — PR #179 merge `562a15393daa9ca8892ca1ec6dfcda4986fa9e0e`; manual CONDITIONAL NOT TRIGGERED.
- R11.13–R11.14 : **FROZEN / NOT STARTED** until authorized sequentially.
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

## R11.9 required evidence

- Accepted manual candidate `087eae19ea03dd544d75a08c1eb348fe187624c5`.
- Godot `4.7.2.stable.steam.ed1daf0bf`; ffprobe `8.1.1-full_build-www.gyan.dev`; 640×360, 30 FPS, 90 frames, 3.0 s, A/V drift `0.0 s`.
- Evidence `docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json`; digest `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`.
- PR #173 merge `5b491cee157e4ba9200a5608cca3721321b768e3`; normalization PR #174 merge `470d8c63eda6bbc3e1a8151c6e050df334a94dba`.

## R11.10–R11.11 closure

- R11.10 delivered typed continuity snapshots, explicit stale/missing/conflict states, deterministic diffs and R8 revision-bound cross-project packages with `compare_only_no_canon_mutation`. Final docs `04c9c7fa68723b2bcc02962325a1a21f8593e9ff`; PR #175 merge `b6169b790b6f4afccd305c33d1c51cf4aa7a5bbd`; normalization #176 merge `5020bf6e46c7078b045bea77437e9b063169a9e5`.
- R11.11 delivered Franchise DNA separate from Project DNA, immutable/versioned Canon snapshots, authority/conflict policy, bounded supersession graph, R7 non-promotion, and durable Guardian/SafeChange/Audit persistence. Final docs `dd184f6cd854437a0085720545f5d09b135cb81c`; R0 #1438 / `32761068571`, Python #1412 / `32761068622`, UI #1379 / `32761068582`; PR #177 merge `7140ddec12d313760ae84e942c7180c63dbce78e`; normalization #178 merge `7fa6d1294d10a9b0e602b412db644cf68fb66ede`.

## R11.12 closure in progress

- Base normalized main `7fa6d1294d10a9b0e602b412db644cf68fb66ede`; branch `r11/12-savebridge-migrations`; PR #179.
- Delivered checksummed SaveBridge documents, namespaced extensions, explicit `COMPATIBLE/MIGRATION_REQUIRED/UNSUPPORTED_NEWER/CORRUPT`, trusted typed migration registry, cycle/path-budget protection, deterministic/idempotent migration, dry-run, and runtime-save/Canon separation.
- Durable migration is Guardian-authorized and uses SafeChange snapshot + verified BackupManager archive + RecoveryJournal + atomic replace + post-write verification + Audit; injected failure restores exact prior bytes.
- Accepted implementation head `66ccd03bf486ac325ee2fba7133a6fc2a9c244b0`: R0 #1442 / `32762000034`, Python #1416 / `32762000036`, UI #1383 / `32762000071` SUCCESS.
- Final docs head `a7809c9411bcc4c2ee392acf6d03d1c2800635c7`: R0 #1443 / `32762206491`, Python #1417 / `32762206588`, UI #1384 / `32762206575` SUCCESS.
- Manual CONDITIONAL **NOT TRIGGERED**: no concrete existing user Godot save format is claimed or touched.
- PR #179 merged as `562a15393daa9ca8892ca1ec6dfcda4986fa9e0e`.
- Current branch `r11/12-postmerge-continuity-normalization` changes only this continuity file. Its accepted merge makes **R11.12 COMPLETE + NORMALIZED** and authorizes R11.13.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 governance/security/privacy/license; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key; R5 Godot authority remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory.

## Execution rule

Each subdivision: dedicated branch from normalized `main` → focused tests + exact-head R0/full Python/UI → satisfy manual state → final docs/evidence and re-gate if head changes → expected-SHA merge → exactly one continuity-only normalization + same exact-head gates + merge → only then next subdivision.

## Next authorized action

Cycle = **R11.12 continuity normalization only**. Gate exact head of `r11/12-postmerge-continuity-normalization`; merge it with expected SHA. **Only that merge authorizes R11.13.**
