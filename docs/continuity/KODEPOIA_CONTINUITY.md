# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning est la prochaine action autorisée; aucune R12.1 ne peut commencer avant création, validation exacte et merge de `docs/roadmap/R12_PLAN.md`.** R11.14 a été accepté et fusionné via PR #183, merge `03dad4366ff5332b0728f548497f2051b7051138`. Candidat d’implémentation accepté `f2693c8cfd4a7aaa5c73fc0a318ebaeef4ff0bb1`; head final de documentation/preuve `081fe88009aeb0cc89c6f91bd01184646d4aacdd`; rapport canonique `docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json` = PASS, `blockers=[]`, digest sémantique `ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170`. Manuel R11.14 **CONDITIONAL NOT TRIGGERED**.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` est la source de vérité après chaque merge accepté.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED**.
- R11.1–R11.14 : **COMPLETE + NORMALIZED**.
- R11 : **COMPLETE + NORMALIZED**.
- R12–R16 : **PENDING / NOT STARTED**.
- Prochaine phase de roadmap : **R12 — Desktop applications**.

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

## Required local evidence preserved

- R11.5 Piper local TTS evidence : `docs/roadmap/R11_5_LOCAL_ACCEPTANCE.json`; source SHA `a9862b3bf475b259fe154d1e2486116ad04602f3`; digest `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`; PASS.
- R11.9 Godot cinematic evidence : `docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json`; source SHA `087eae19ea03dd544d75a08c1eb348fe187624c5`; digest `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`; Godot `4.7.2.stable.steam.ed1daf0bf`, ffprobe `8.1.1-full_build-www.gyan.dev`, 640×360, 30 FPS, 90 frames / 3.0 s, A/V drift `0.0 s`; PASS.

## R11.13 closure

- Accepted implementation head `79a891eaede7e5ecf7d8daf35846b20b1d3d02f9`: R0 #1447 / `32763810080`, Python #1421 / `32763810070`, UI #1388 / `32763810029` SUCCESS.
- Final docs head `78c60da9c8dfad1f6802207b812bdb84204572a4`: R0 #1448 / `32764105609`, Python #1422 / `32764105564`, UI #1389 / `32764105529` SUCCESS.
- Implementation PR #181 merge `e70a0b112636cd72e92e39f22603b97d6f15e7a5`.
- Post-merge normalization head `d729c889815a3963ffee113012fbc8d22b49d649`: R0 #1450 / `32764420166`, Python #1424 / `32764420139`, UI #1391 / `32764420171` SUCCESS.
- Normalization PR #182 merge `72d17eeda7b72b480b7a2268bec5c57187bc64e9`.
- **R11.13 COMPLETE + NORMALIZED.** Manual NONE.

## R11.14 closure

- Base normalized `main`: `72d17eeda7b72b480b7a2268bec5c57187bc64e9`.
- Branch d’implémentation : `r11/14-adversarial-integrated-acceptance`; PR #183.
- Livré : suite adversariale cross-seam, modèle/verifier d’acceptation intégrée R11 anti-circulaire, schéma JSON Draft 2020-12 strict, liaison des acceptances R11.1–R11.14, des preuves locales REQUIRED R11.5/R11.9 et des rapports intégrés R7–R10.
- Candidat d’implémentation accepté `f2693c8cfd4a7aaa5c73fc0a318ebaeef4ff0bb1`: R0 #1455 / `32769325414`, Python #1429 / `32769325329`, UI #1396 / `32769325281` SUCCESS.
- Head final documentation/preuve `081fe88009aeb0cc89c6f91bd01184646d4aacdd`: R0 #1459 / `32769936597`, Python #1433 / `32769936407`, UI #1400 / `32769936452` SUCCESS.
- Rapport canonique `docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`, digest sémantique `ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170`.
- PR #183 merge `03dad4366ff5332b0728f548497f2051b7051138`.
- Manuel **CONDITIONAL NOT TRIGGERED** : R11.14 ne crée aucun nouveau comportement Piper/Godot/FFmpeg faisant autorité; les preuves réelles R11.5/R11.9 restent les preuves runtime requises.
- Cette mise à jour est l’unique normalisation de continuité post-merge R11.14. Après son exact-head R0 + full Python Core + KodeStudio UI Smoke et son merge, **R11 est COMPLETE + NORMALIZED**.

## R12 — prochaine phase autorisée

Roadmap gelée : **R12 — Desktop applications**. Périmètre de haut niveau autoritatif : adapters WinUI/WPF/Avalonia/Qt/Tauri, MVVM, SQLite, async, IPC, accessibility/localization, installers/update. DoD de roadmap : créer/compiler/tester une application Windows moderne depuis le Wizard.

Le template `docs/roadmap/PHASE_PLAN_TEMPLATE.md` impose qu’un nouveau plan majeur soit créé et fusionné à `main` avant toute implémentation de `RX.1`.

Donc la prochaine action autorisée, après merge de cette normalisation, est **R12 planning uniquement** :

1. créer une branche dédiée depuis le `main` normalisé exact;
2. créer `docs/roadmap/R12_PLAN.md` à partir du template, avec toutes les subdivisions R12 gelées avant implémentation;
3. synchroniser cette continuité dans le même cycle;
4. passer R0 Repository Guard + full Python Core + KodeStudio UI Smoke sur un head exact;
5. merger le plan avec contrôle `expected_head_sha`;
6. effectuer la normalisation de continuité du plan si le cycle établi l’exige;
7. **ne commencer R12.1 qu’après acceptation et merge du plan R12.**

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 governance/security/privacy/license; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key; R5 Godot authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory.

## Execution rule

Chaque subdivision : branche dédiée depuis `main` normalisé → focused tests + exact-head R0/full Python/UI → satisfaire REQUIRED/triggered CONDITIONAL manual state → final docs/evidence et re-gate si le head change → merge avec `expected_head_sha` → exactement une continuity-only normalization + mêmes gates exact-head + merge → seulement ensuite la subdivision suivante.

## Next authorized action

Cycle = **R11.14 post-merge continuity normalization** jusqu’à son merge. Ensuite : **R12 planning only**. Créer et merger `docs/roadmap/R12_PLAN.md` avant toute R12.1.
