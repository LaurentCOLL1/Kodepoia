# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1–R11.8 COMPLETE + NORMALIZED. R11.9 implementation/manual acceptance is ACCEPTED + MERGED via PR #173, and exactly one continuity-only R11.9 normalization is now pending. R11.10 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11.9 accepted manual candidate `087eae19ea03dd544d75a08c1eb348fe187624c5`; real Godot 4.7.2 Steam capture PASS; evidence digest `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`. Final evidence-bound head `c0934fcedc05368acbfe94529e6f971bf426e546` passed R0 #1426 / `32757919223`, Python #1400 / `32757919234`, UI #1367 / `32757919306`; PR #173 merge `5b491cee157e4ba9200a5608cca3721321b768e3`. Current work must be R11.9 continuity normalization only.

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
- R11.5 : **COMPLETE + NORMALIZED** — manual REQUIRED SATISFIED; Piper local TTS evidence accepted.
- R11.6 : **COMPLETE + NORMALIZED** — manual CONDITIONAL NOT TRIGGERED.
- R11.7 : **COMPLETE + NORMALIZED** — manual CONDITIONAL NOT TRIGGERED.
- R11.8 : **COMPLETE + NORMALIZED** — manual NONE; normalization merge `e01f18ee5b7fbd7df513e10ad96c1ac35d83d6e5`.
- R11.9 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — manual REQUIRED SATISFIED.
- R11.10–R11.14 : **FROZEN / NOT STARTED** until authorized sequentially.
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

## R11.5 closure

- Accepted implementation candidate `a9862b3bf475b259fe154d1e2486116ad04602f3`.
- REQUIRED local TTS acceptance SATISFIED with `tts.piper.fr-FR.siwis-medium`; evidence digest `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`.
- Final accepted head `e58954e4c144d00f3747b9918b5657f495075452`; PR #165 merge `cd55311f8103266fec3cc1c33893cb052d490a92`.
- Normalization PR #166 merge `e12a575314afd511bb752f263c9e5b7e60c75d51`.
- `models/` is the local project model catalog; manifests/metadata are versioned while heavy weights remain local/ignored by normal Git. `KodeModelRegistry` carries physical/provenance identity while the existing model router keeps logical role routing.

## R11.6–R11.8 closure

- R11.6 final docs head `85a0d1b793f0ec9aa657bfc0f56d1be22424534a`; PR #167 merge `742ea5b5e1e3b6ffa73f499198464295131e91bf`; normalization PR #168 merge `956fbf296a1ffc312fdd1e17e20ec39fb7fe20cc`.
- R11.7 final docs head `49f52432df1d3345dcd69e8862d14f9477d0d342`; PR #169 merge `2ec8ea6b3718a08f31cfad969bc86d97992e46ab`; normalization PR #170 merge `c3d091fb88acfc2bd054521fd3c76904eff0b885`.
- R11.8 final docs head `80e7d60b2e6bf75d26f36a28cc2d77f7dac2945e`; PR #171 merge `7d7a421e069a9d8beaf4d9160b06351752946e73`; normalization merge `e01f18ee5b7fbd7df513e10ad96c1ac35d83d6e5`.

## R11.9 closure in progress

- Base normalized main: `e01f18ee5b7fbd7df513e10ad96c1ac35d83d6e5`.
- Branch: `r11/9-godot-cinematic-capture`; PR #173.
- Accepted implementation/manual candidate: `087eae19ea03dd544d75a08c1eb348fe187624c5`.
- Candidate hosted gates: R0 #1419 / `32753163815`; Python #1393 / `32753163940`; UI #1360 / `32753163936` — all SUCCESS.
- REQUIRED real local gate SATISFIED on Windows with Godot `4.7.2.stable.steam.ed1daf0bf` and ffprobe `8.1.1-full_build-www.gyan.dev`.
- Accepted local evidence: `docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json`.
- Evidence digest: `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`.
- Real capture facts: 640×360, 30 FPS, 90/90 frames, 3.0 s video/audio/container, stereo 48 kHz, A/V sync error `0.0 s`, output bytes `1021734`, output SHA-256 `2f383635f2ee94def1ee832ffd742f0fc2cf41af18ef939078f72746e6e8a194`.
- Final evidence-bound head `c0934fcedc05368acbfe94529e6f971bf426e546`: R0 #1426 / `32757919223`, Python #1400 / `32757919234`, UI #1367 / `32757919306` — all SUCCESS.
- PR #173 merged as `5b491cee157e4ba9200a5608cca3721321b768e3`.
- Current branch `r11/9-postmerge-continuity-normalization` changes only this continuity file. Its accepted merge makes **R11.9 COMPLETE + NORMALIZED** and authorizes R11.10.

## Runtime discovery convention

External runtimes should be resolved in this order:

1. explicit governed configured path;
2. executable available through `PATH`;
3. fixed provider-specific known locations.

For Windows Steam libraries, the drive letter is not stable. Probe bounded product-relative paths such as `<drive>:\SteamLibrary\steamapps\common\<Product>\<Executable>` and standard Steam roots across mounted filesystem drives; do not recursively crawl arbitrary user data. Godot Steam uses the product directory `Godot Engine` and Windows 64-bit executable `godot.windows.opt.tools.64.exe` in the accepted R11.9 evidence.

## Permanent boundaries

`WorkspaceBoundary`/R8 VaultBoundary; `ProcessSandbox` + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; Secrets/redaction; R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rig/shape-key authority; R5 Godot authority all remain in force. Structured APIs only: no raw shell/argv/filter/TTS/Godot scripts supplied by a model. Network off by default; no automatic codecs/TTS/model/voice/plugin download. Exact-head evidence mandatory; missing evidence never means PASS; foundation change R1–R10 requires ADR.

## Execution rule

Each subdivision: dedicated branch from normalized `main` → frozen scope → focused tests + R0 + full Python Core + UI Smoke on one exact head → satisfy REQUIRED/triggered CONDITIONAL → final docs/evidence and re-gate if head changes → merge with expected SHA → exactly one continuity-only normalization + re-gate + merge → only then next subdivision.

Normalization run IDs remain in PR/merge metadata; do not create recursive commits solely to restate a normalization's own runs.

## Next authorized action

Cycle = **R11.9 continuity normalization only**. Gate exact head of `r11/9-postmerge-continuity-normalization` with R0 + full Python Core + KodeStudio UI Smoke and merge with expected SHA. **Only that merge authorizes R11.10.**
