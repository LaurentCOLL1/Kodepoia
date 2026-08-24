# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACCEPTED + NORMALIZED. R11.1 implementation ACCEPTED + MERGED; exactly one continuity-only R11.1 normalization is in progress. R11.2 is forbidden until that normalization passes exact-head R0 + full Python Core + KodeStudio UI Smoke and merges.** R11 planning normalization PR #156 merged as `95d582d864fe7a68f79e74d1383d4a2a2db7cee2`, authorizing R11.1. R11.1 implementation head `46ee14f3e94ed8c5c1cadbf139a890fab853929f` passed R0 #1339 / `32724742731`, Python #1313 / `32724743073`, UI #1280 / `32724742770`; final documentation head `70969202b8d604f7b91ca47aa980f96850879a5b` passed R0 #1340 / `32724919759`, Python #1314 / `32724919770`, UI #1281 / `32724919760`; PR #157 merged as `f1638f962e30e9f191dfc2a061fbe564e36efd0d`. Manual R11.1 = NONE. Current branch `r11/1-continuity-normalization` must change continuity only. If its exact head passes the three gates and merges, **R11.1 becomes COMPLETE + NORMALIZED and R11.2 is authorized.**

## Source de vérité / état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque merge accepté et normalisation requise.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **ACCEPTED + NORMALIZED** — PR #155 plan merge `523048121613a07554787a07701d1334c59cd2dd`; PR #156 normalization merge `95d582d864fe7a68f79e74d1383d4a2a2db7cee2`.
- R11.1 : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING** — manual NONE; PR #157 merge `f1638f962e30e9f191dfc2a061fbe564e36efd0d`.
- R11.2–R11.14 : **FROZEN / NOT STARTED**; R11.2 waits for the R11.1 normalization merge.
- R12–R16 : **PENDING / NOT STARTED**.

## Autorité historique des acceptances

Les récits exact-head, candidats rejetés, preuves locales et rapports canoniques restent autoritatifs dans `docs/roadmap/R7_*`, `R8_*`, `R9_*`, `R10_*`, `R11_*` et l'historique des PR mergées. Cette continuité résume l'état de reprise sans réécrire rétroactivement ces preuves.

### R7

- Phase **COMPLETE + NORMALIZED**.
- R7.7 REQUIRED SATISFIED; head local accepté `04cef94c82fdacafe7313d27c8cf516e8e765295`.
- Rapport intégré `status=pass`, `blockers=[]`.
- PR #82 a établi le point de départ R8 `b98832b339902527bce8a5ea95b5a08a19839a40`.

### R8

- Phase **COMPLETE + NORMALIZED**.
- R8.9 REQUIRED SATISFIED; preuve Godot SHA-256 `6579babc829022930e5abe889583e32357fa3d7695b1a2713014e32f86e23b7e`.
- Rapport intégré `status=pass`, `blockers=[]`.
- Normalisation finale PR #102 merge `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`.

### R9

- R9.1–R9.11 **COMPLETE + NORMALIZED**.
- R9.8 REQUIRED SATISFIED; preuve locale SHA-256 `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`.
- `docs/roadmap/R9_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`.
- Normalisation finale PR #128 merge `ec857163915923e7aae9ce316b20d4ab9ae1ce1f`.

## R10 — fermeture autoritative

- Titre : **Blender / 3D**; plan exhaustif `docs/roadmap/R10_PLAN.md`.
- R10.1–R10.12 : **COMPLETE + NORMALIZED**.
- Manuels réalisés : R10.2 REQUIRED SATISFIED; R10.6/R10.7 CONDITIONAL TRIGGERED + SATISFIED; R10.10 REQUIRED SATISFIED; autres CONDITIONAL non déclenchés/NONE selon le plan.
- Rapport `docs/roadmap/R10_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`, semantic digest `48c18aacc916fb064810b36ada5a179f1d3b149912bea8a19a3295da1826a3c8`.
- PR #153 merge `778164694fd32b6c01d0f34bf7d94c93090fdf98`; normalisation finale PR #154 merge `d627f26a086c46273ce378a2d4d9919db0e9dd3a`.
- Ce dernier merge est l'acte autoritatif : **R10 COMPLETE + NORMALIZED; R11 planning autorisé**.

## R11 planning — Audio / Voice / Cinematics / Franchise

- Roadmap : `docs/roadmap/KODEPOIA_ROADMAP_V1_0.md`.
- Plan exhaustif : `docs/roadmap/R11_PLAN.md`.
- Planning head `6d335f9bc025dfff0b5b92b206115ab603d9a8d5`: R0 #1335 / `32722294209`, Python #1309 / `32722294203`, UI #1276 / `32722294224` SUCCESS; Ubuntu 906 passed / 8 skipped / 46 warnings; PR #155 merge `523048121613a07554787a07701d1334c59cd2dd`.
- Planning normalization head `ff81cdb62ada8a7956dcd26769e26ed96ec536b8`: R0 #1337 / `32722608074`, Python #1311 / `32722608223`, UI #1278 / `32722608111` SUCCESS; PR #156 merge `95d582d864fe7a68f79e74d1383d4a2a2db7cee2`.
- **R11 planning ACCEPTED + NORMALIZED**.

### Structure R11 gelée

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

## R11.1 closure — media contracts/runtime boundaries

- Base normalized `main`: `95d582d864fe7a68f79e74d1383d4a2a2db7cee2`.
- Branch: `r11/1-media-contracts-runtime-boundaries`; PR #157.
- Delivered `src/kodepoia/media/` contracts/serialization/boundary, R11 schemas, focused adversarial tests, design and acceptance docs.
- Process architecture reuses `kodepoia.core.sandbox.ProcessSandbox`; R11.1 boundary validates/compiles fixed policies and never launches arbitrary shell/process commands.
- Accepted implementation head `46ee14f3e94ed8c5c1cadbf139a890fab853929f`: R0 #1339 / `32724742731` SUCCESS; Python #1313 / `32724743073` SUCCESS; UI #1280 / `32724742770` SUCCESS. Ubuntu **914 passed / 8 skipped / 46 warnings**; Windows **911 passed / 11 skipped / 46 warnings**.
- Final documentation head `70969202b8d604f7b91ca47aa980f96850879a5b`: R0 #1340 / `32724919759`, Python #1314 / `32724919770`, UI #1281 / `32724919760`, all SUCCESS; both package builds and internal KodeStudio SUCCESS.
- Manual **NONE**; no real ffmpeg/TTS/Godot runtime launched.
- PR #157 merge `f1638f962e30e9f191dfc2a061fbe564e36efd0d`.
- Current branch `r11/1-continuity-normalization` changes only this continuity file. Its accepted merge makes **R11.1 COMPLETE + NORMALIZED** and authorizes R11.2.

### Baselines externes R11 à préserver

- Godot **4.7** reste la cible moteur héritée de R5.
- FFmpeg/ffprobe sont des runtimes externes capability-probed; aucun téléchargement/installation automatique.
- `ffprobe` JSON est le canal structuré préféré quand un runtime accepté est utilisé.
- TTS reste backend-neutral; Piper est un candidat d'adaptateur local optionnel. Runtime et voix/modèles restent des ressources externes avec licence/provenance explicites.
- Voice cloning/impersonation depuis des enregistrements humains arbitraires est hors scope R11 v1.0.
- R11.5 exige une preuve locale réelle sur runtime TTS + voix explicitement approuvés/configurés.
- R11.9 exige une preuve locale réelle de capture cinématique Godot 4.7 + validation A/V sur fixture synthétique du dépôt.

## Frontières permanentes

- `WorkspaceBoundary` et R8 `VaultBoundary` pour chemins/staging/assets.
- `ProcessSandbox` + KillSwitch pour tout exécutable externe; Guardian + `PermissionSet` pour lancement et mutations.
- SafeChange / Backup / Recovery / Audit pour mutations/migrations.
- Secrets/redaction; aucun secret dans médias, manifests, saves ou evidence.
- R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 VRAM; R10 rigs/shape keys/blend shapes; R5 Godot 4.7 restent autoritatifs.
- APIs structurées uniquement : pas de shell/argv/filtre FFmpeg/script Godot/TTS brut fourni par le modèle.
- Réseau off par défaut; aucun téléchargement/install automatique de codecs, moteurs TTS, voix, modèles, plugins ou packs.
- Microphone opt-in seulement; aucun enregistrement de fond; aucune voix personnelle requise pour les acceptances R11 prévues.
- Acceptation exact-head obligatoire; preuve absente ≠ PASS; modification de fondation R1–R10 => ADR.

## Règle d'acceptance et de normalisation

Pour chaque subdivision : branche depuis le `main` normalisé autorisé → scope gelé uniquement → tests ciblés + R0 + Python Core complet + UI Smoke sur le même head → satisfaire REQUIRED/CONDITIONAL déclenché → documentation/evidence finale → re-gate si le head change → merge avec `expected_head_sha` → exactement une normalisation de continuité → re-gate → merge → seulement alors subdivision suivante.

Les IDs de runs d'une normalisation restent dans la PR/merge; ne pas créer une récursion de commits uniquement pour réinscrire les propres run IDs de cette normalisation.

## Règle de clôture R11

R11 n'est **COMPLETE + NORMALIZED** que lorsque R11.1–R11.14 sont COMPLETE, toutes les preuves REQUIRED/CONDITIONAL déclenchées sont satisfaites, le rapport intégré R11 vérifie `status=pass`, `blockers=[]`, la PR finale est mergée et l'unique normalisation finale de continuité passe R0 + Python Core + UI Smoke puis merge.

**R12 planning est interdit avant ce merge final de normalisation R11.**

## Modèles acceptés

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste un candidat futur KodeDeepCoder.
- Les tâches Git/repository/software-engineering non triviales ne doivent pas router vers Granite.

## Prochaine action autorisée

Cycle actuel = **normalisation R11.1 uniquement**. Exiger R0 Repository Guard + Python Core complet + KodeStudio UI Smoke sur le head exact de `r11/1-continuity-normalization`, puis merger avec `expected_head_sha`.

**Seul ce merge rend R11.1 COMPLETE + NORMALIZED et autorise R11.2.** Après ce merge, créer une branche R11.2 dédiée depuis le nouveau `main`; ne jamais empiler R11.2 sur une branche de normalisation non mergée.
