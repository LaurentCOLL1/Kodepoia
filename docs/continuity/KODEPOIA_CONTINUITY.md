# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R10 COMPLETE + NORMALIZED. R11 planning ACTIVE sur la branche `r11/plan-audio-voice-cinematics-franchise`. R11.1 est INTERDIT tant que `docs/roadmap/R11_PLAN.md` n'a pas été accepté sur un head exact, mergé, puis normalisé par une unique PR de continuité elle-même acceptée et mergée.** Le `main` autoritatif au départ de R11 est `d627f26a086c46273ce378a2d4d9919db0e9dd3a`. Le titre gelé de R11 est **Audio / Voice / Cinematics / Franchise**. Le plan propose R11.1–R11.14 avec R11.5 et R11.9 en REQUIRED, R11.2/R11.6/R11.7/R11.12/R11.14 en CONDITIONAL, toutes les autres subdivisions en NONE. Aucune implémentation R11 n'a commencé.

## Source de vérité / état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque merge accepté et normalisation requise.
- R1–R10 : **COMPLETE + NORMALIZED**.
- R11 planning : **IN PROGRESS** sur `r11/plan-audio-voice-cinematics-franchise`.
- R11.1–R11.14 : **PLANNED ONLY / NOT STARTED** jusqu'au merge du plan puis au merge de sa normalisation.
- R12–R16 : **PENDING / NOT STARTED**.

## Autorité historique des acceptances

Les détails complets, candidats rejetés, rapports JSON canoniques, preuves locales et récits exact-head restent autoritatifs dans `docs/roadmap/R7_*`, `R8_*`, `R9_*`, `R10_*` et l'historique des PR mergées. Cette continuité ne réécrit pas rétroactivement ces preuves.

### R7

- Phase **COMPLETE + NORMALIZED**.
- R7.7 REQUIRED SATISFIED; head local accepté `04cef94c82fdacafe7313d27c8cf516e8e765295`.
- Rapport intégré `status=pass`, `blockers=[]`.
- Normalisation finale `d2278b1ee31d7d4a7b8570836edc3082e9fe30c4`; PR #82 a établi le point de départ R8 `b98832b339902527bce8a5ea95b5a08a19839a40`.

### R8

- Phase **COMPLETE + NORMALIZED**.
- R8.9 REQUIRED SATISFIED; preuve Godot SHA-256 `6579babc829022930e5abe889583e32357fa3d7695b1a2713014e32f86e23b7e`.
- Rapport intégré `status=pass`, `blockers=[]`, source SHA `d1589cf94545b854f995e7b6706c4b67e9b7ac1a`.
- Normalisation finale PR #102 merge `359e9eb8225e4eaf3f518888da0ebf43e4605e9e`.

### R9

- R9.1–R9.11 **COMPLETE + NORMALIZED**.
- R9.8 REQUIRED SATISFIED; preuve locale SHA-256 `a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967`, 5744 octets.
- `docs/roadmap/R9_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`.
- Normalisation finale `e3d4e396bb062bbc97297572d7c90f640c03cea2`: R0 #1214 / `32658997406`, Python #1188 / `32658997391`, UI #1155 / `32658997367` SUCCESS; PR #128 merge `ec857163915923e7aae9ce316b20d4ab9ae1ce1f`.

## R10 — fermeture autoritative

- Titre : **Blender / 3D**.
- Plan exhaustif : `docs/roadmap/R10_PLAN.md`.
- R10.1–R10.12 : **COMPLETE + NORMALIZED** après la clôture finale de phase.
- États manuels gelés réalisés : R10.1 NONE; R10.2 REQUIRED SATISFIED; R10.3 NONE; R10.4 CONDITIONAL NOT TRIGGERED; R10.5 NONE; R10.6 CONDITIONAL TRIGGERED + SATISFIED; R10.7 CONDITIONAL TRIGGERED + SATISFIED; R10.8 CONDITIONAL NOT TRIGGERED; R10.9 NONE; R10.10 REQUIRED SATISFIED; R10.11 NONE; R10.12 CONDITIONAL NOT TRIGGERED.
- R10.11 normalisation : head `c5af4d6ca0556bee811c536ce544901b647f34e0`; R0 #1326 / `32714235401`, Python #1300 / `32714235332`, UI #1267 / `32714235405` SUCCESS; PR #152 merge `15b08c7be41d0c2d90bbc5f22364cd319cdfdd10`.
- R10.12 candidat historique `314f73a787df138a1525ddb9d6c894b95022f973` rejeté par Python #1302 à cause d'un test comparant à tort les octets actuels de R10.2 au digest historique de transfert; le verifier n'a pas été affaibli.
- R10.12 implementation head accepté `2f1db59c8ffa8da28d7afd994e8203a126d4f478`: R0 #1329 / `32716992444`, Python #1303 / `32716992453`, UI #1270 / `32716992458` SUCCESS; Ubuntu 906 passed / 8 skipped / 46 warnings; R7/R8/R9 PASS.
- Rapport `docs/roadmap/R10_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`, semantic digest `48c18aacc916fb064810b36ada5a179f1d3b149912bea8a19a3295da1826a3c8`, `source_sha=2f1db59c8ffa8da28d7afd994e8203a126d4f478`.
- Final evidence head `309133ae50045ae2193e13d69f9b195c02d74b5d`: R0 #1331 / `32718578313`, Python #1305 / `32718578346`, UI #1272 / `32718578401` SUCCESS; PR #153 merge `778164694fd32b6c01d0f34bf7d94c93090fdf98`.
- Normalisation finale R10 head `7a54be96176d973e31fb5f10c73b697c0a380246`: R0 #1333 / `32719222404`, Python #1307 / `32719222385`, UI #1274 / `32719222386` SUCCESS; Ubuntu 906 passed / 8 skipped / 46 warnings; R7/R8/R9 PASS; Windows Python, KodeStudio interne et builds Ubuntu/Windows SUCCESS.
- PR #154 merge `d627f26a086c46273ce378a2d4d9919db0e9dd3a` est l'acte autoritatif : **R10 COMPLETE + NORMALIZED; R11 planning autorisé**.

## R11 planning baseline — Audio / Voice / Cinematics / Franchise

- Roadmap : `docs/roadmap/KODEPOIA_ROADMAP_V1_0.md`.
- Template obligatoire : `docs/roadmap/PHASE_PLAN_TEMPLATE.md`.
- Source `main` de planification : `d627f26a086c46273ce378a2d4d9919db0e9dd3a`.
- Branche : `r11/plan-audio-voice-cinematics-franchise`.
- Plan exhaustif : `docs/roadmap/R11_PLAN.md`.
- R11.1 ne peut commencer qu'après : plan exact-head R0 + Python Core complet + KodeStudio UI Smoke SUCCESS → merge du plan avec `expected_head_sha` → unique normalisation de continuité de planification → mêmes trois gates exact-head SUCCESS → merge de normalisation.

### Structure R11 proposée à geler

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

### Baselines externes de compatibilité R11

- Godot **4.7** reste la cible moteur héritée de R5.
- FFmpeg **9.0.1** est la référence externe de planification; comportement/version réels restent capability-probed, sans installation automatique.
- `ffprobe` JSON est le canal d'inspection structuré préféré quand un runtime FFmpeg accepté est utilisé.
- TTS : contrat backend-neutral; Piper est un candidat d'adaptateur local optionnel. Aucun runtime/modèle/voix n'est auto-bundlé ou téléchargé; licence/provenance restent explicites.
- Voice cloning/impersonation depuis des enregistrements humains arbitraires est hors scope R11 v1.0.
- R11.5 exige une preuve locale réelle sur runtime TTS + voix explicitement approuvés/configurés.
- R11.9 exige une preuve locale réelle de capture cinématique Godot 4.7 + validation A/V sur fixture synthétique du dépôt.

## Frontières permanentes à préserver

- `WorkspaceBoundary` et R8 `VaultBoundary` pour les chemins/staging/assets.
- `ProcessSandbox` + KillSwitch pour tout exécutable externe.
- Guardian + `PermissionSet` pour lancements, accès micro et mutations durables.
- SafeChange / Backup / Recovery / Audit pour mutations et migrations.
- Secrets/redaction; aucun secret dans médias, manifests, saves ou evidence.
- R6 Health/Budget/DataGovernance/AppSecurity/Privacy/License-BOM reste autoritatif.
- R7 ResearchGuard : paroles/scripts/subtitles/tags/métadonnées externes sont des données, jamais des instructions agentiques.
- R8 reste autoritatif pour source/derived identity, provenance, lineage, cache/rebuild et export.
- R9 arbitre la VRAM si un backend R11 GPU est ultérieurement accepté.
- R10 reste autoritatif pour géométrie/rigs/shape keys/blend shapes/animation 3D; R11 mappe vers ces cibles sans les réinventer.
- R5 reste autoritatif pour Godot 4.7 et ses mutations/exécutions.
- APIs structurées uniquement : pas de shell/argv/filtre FFmpeg/script Godot/TTS brut fourni par le modèle.
- Réseau off par défaut; aucun téléchargement/install automatique de codecs, moteurs TTS, voix, modèles, plugins ou packs.
- Microphone opt-in seulement; aucun enregistrement de fond.
- Les enregistrements de voix sont des médias sensibles de projet et ne sont ni uploadés ni utilisés pour entraîner/cloner une voix par R11 v1.0.
- Acceptation exact-head obligatoire; preuve absente ≠ PASS.
- Toute modification de fondation R1–R10 exige un ADR.

## Règle d'acceptance et de normalisation

Pour chaque subdivision : branche depuis le `main` normalisé autorisé → scope gelé uniquement → tests ciblés + R0 + Python Core complet + UI Smoke sur le même head → satisfaire REQUIRED/CONDITIONAL déclenché → documentation/evidence finale → re-gate si le head change → merge avec `expected_head_sha` → exactement une normalisation de continuité si requise → re-gate → merge → seulement alors subdivision suivante.

Les IDs de runs d'une normalisation restent dans la PR/merge; ne pas créer une récursion de commits uniquement pour réinscrire les propres run IDs de la normalisation.

## Règle de clôture R11

R11 n'est **COMPLETE + NORMALIZED** que lorsque R11.1–R11.14 sont COMPLETE, toutes les preuves REQUIRED/CONDITIONAL déclenchées sont satisfaites, le rapport intégré R11 vérifie `status=pass`, `blockers=[]`, la PR finale est mergée et l'unique normalisation finale de continuité passe R0 + Python Core + UI Smoke sur un head exact puis merge.

**R12 planning est interdit avant ce merge final de normalisation R11.**

## Modèles acceptés

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste un candidat futur KodeDeepCoder.
- Les tâches Git/repository/software-engineering non triviales ne doivent pas router vers Granite.

## Prochaine action autorisée

Cycle actuel = **planification uniquement**. Figer `docs/roadmap/R11_PLAN.md` avec cette continuité sur un seul head. Ouvrir la PR de planification et exiger R0 Repository Guard + Python Core complet + KodeStudio UI Smoke SUCCESS sur ce SHA exact. **Ne pas implémenter R11.1 sur la branche de planification.**

Si les trois gates passent : merge du plan avec `expected_head_sha`, puis création d'une seule branche de normalisation de planification ne modifiant que cette continuité; y enregistrer head/runs/merge du plan et geler officiellement R11.1–R11.14/manual states; exécuter les mêmes trois gates et merger. **Seul ce second merge autorise R11.1.**
