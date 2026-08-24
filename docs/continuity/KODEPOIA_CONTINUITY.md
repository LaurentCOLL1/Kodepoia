# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1–R11.10 COMPLETE + NORMALIZED. R11.11 implementation is ACCEPTED + MERGED via PR #177; exactly one continuity-only R11.11 normalization is now pending. R11.12 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11.11 final documentation head `dd184f6cd854437a0085720545f5d09b135cb81c` passed R0 #1438 / `32761068571`, Python #1412 / `32761068622`, UI #1379 / `32761068582`; PR #177 merge `7140ddec12d313760ae84e942c7180c63dbce78e`. Current work must be R11.11 continuity normalization only.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée le 21 août 2026; `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED**.
- R11.1–R11.4 : **COMPLETE + NORMALIZED**.
- R11.5 : **COMPLETE + NORMALIZED** — manual REQUIRED SATISFIED.
- R11.6–R11.8 : **COMPLETE + NORMALIZED**.
- R11.9 : **COMPLETE + NORMALIZED** — manual REQUIRED SATISFIED; normalization PR #174 merge `470d8c63eda6bbc3e1a8151c6e050df334a94dba`.
- R11.10 : **COMPLETE + NORMALIZED** — normalization PR #176 merge `5020bf6e46c7078b045bea77437e9b063169a9e5`; manual NONE.
- R11.11 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — PR #177 merge `7140ddec12d313760ae84e942c7180c63dbce78e`; manual NONE.
- R11.12–R11.14 : **FROZEN / NOT STARTED** until authorized sequentially.
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

## R11.9 closure

- Accepted manual candidate `087eae19ea03dd544d75a08c1eb348fe187624c5`.
- REQUIRED local Godot gate SATISFIED with Godot `4.7.2.stable.steam.ed1daf0bf`, ffprobe `8.1.1-full_build-www.gyan.dev`, 640×360/30 FPS/90 frames/3.0 s, A/V drift `0.0 s`.
- Evidence `docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json`; digest `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`.
- PR #173 merge `5b491cee157e4ba9200a5608cca3721321b768e3`; normalization PR #174 merge `470d8c63eda6bbc3e1a8151c6e050df334a94dba`.

## R11.10 closure

- Delivered typed continuity snapshots/facts, explicit ACTIVE/STALE/MISSING/DELETED/CONFLICTED states, deterministic diffs and R8 revision-bound cross-project packages with fixed `compare_only_no_canon_mutation`.
- Initial head `089ab8bb5bedc74d1b2750ae201b5176ad51216b` rejected because a JSON Schema `$ref` attempted network resolution; schema was made self-contained/offline with `$defs` without weakening behavior.
- Accepted implementation `5fb1b80a212880bd510977d54a570859c532c206`; final docs `04c9c7fa68723b2bcc02962325a1a21f8593e9ff` passed R0 #1433 / `32759464634`, Python #1407 / `32759464632`, UI #1374 / `32759464653`.
- PR #175 merge `b6169b790b6f4afccd305c33d1c51cf4aa7a5bbd`; normalization PR #176 merge `5020bf6e46c7078b045bea77437e9b063169a9e5`.
- **R11.10 COMPLETE + NORMALIZED.**

## R11.11 closure in progress

- Base normalized main `5020bf6e46c7078b045bea77437e9b063169a9e5`; branch `r11/11-franchise-dna-canon`; PR #177.
- Delivered deterministic Franchise DNA identities separate from R2 Project DNA; immutable/versioned Canon records and snapshot chain; authority tiers `RESEARCH < PROJECT < FRANCHISE`; temporal validity; bounded supersedes/deprecates graph with missing/self/cycle rejection; deterministic conflict/query policy; one-way `PROPOSED -> REVIEWED -> CANONICAL -> DEPRECATED`; R7 research cannot directly promote to Canon.
- Durable Canon persistence reuses existing `KodeGuardian` + `PermissionSet`, `SafeChangeManager` and append-only `AuditLog`; no parallel governance subsystem.
- Schemas are JSON Schema Draft 2020-12 and self-contained/offline.
- Accepted implementation head `38dc7dce1bf288b61eabfa3b174add11ade4ae49`: R0 #1437 / `32760860029`, Python #1411 / `32760860051`, UI #1378 / `32760859982` SUCCESS.
- Final documentation head `dd184f6cd854437a0085720545f5d09b135cb81c`: R0 #1438 / `32761068571`, Python #1412 / `32761068622`, UI #1379 / `32761068582` SUCCESS.
- PR #177 merged as `7140ddec12d313760ae84e942c7180c63dbce78e`.
- Manual **NONE**.
- Current branch `r11/11-postmerge-continuity-normalization` changes only this continuity file. Its accepted merge makes **R11.11 COMPLETE + NORMALIZED** and authorizes R11.12.

## Runtime discovery convention

External runtimes resolve in order: explicit governed configured path → `PATH` → fixed provider-specific known locations. Windows Steam drive letters are variable; bounded product-relative probes are allowed without recursive crawling of arbitrary user data.

## Permanent boundaries

`WorkspaceBoundary`/R8 VaultBoundary; `ProcessSandbox` + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key authority; R5 Godot authority all remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Foundation changes R1–R10 require ADR.

## Execution rule

Each subdivision: dedicated branch from normalized `main` → focused tests + R0 + full Python Core + UI Smoke on exact head → satisfy REQUIRED/triggered CONDITIONAL manual state → final docs/evidence and re-gate if head changes → expected-SHA merge → exactly one continuity-only normalization + exact-head re-gate + merge → only then next subdivision.

## Next authorized action

Cycle = **R11.11 continuity normalization only**. Gate exact head of `r11/11-postmerge-continuity-normalization` with R0 + full Python Core + KodeStudio UI Smoke and merge with expected SHA. **Only that merge authorizes R11.12.**
