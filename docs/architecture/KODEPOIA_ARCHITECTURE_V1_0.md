# Kodepoia — Architecture v1.0 (GELÉE)

**Statut : GELÉE**  
**Date de gel : 21 août 2026**  
**Ancien nom : FORGEGAMEDEV**

Kodepoia est un environnement **local-first**, agentique, multimodal, persistant, sécurisé et extensible pour la conception, le développement, les tests, l'optimisation, la publication et la maintenance de jeux vidéo et d'applications.

> Règle de gel : une nouvelle capacité doit être ajoutée comme sous-module/plugin lorsqu'elle ne corrige pas un défaut de fondation. Toute modification de fondation exige un ADR.

## 1. Principes immuables

1. Local-first : aucune API LLM distante obligatoire.
2. Offline-capable pour les projets déjà configurés.
3. Platform-aware : les plateformes cibles sont demandées explicitement.
4. Une plateforme non ciblée ne doit pas imposer inputs, UI, dépendances ou budgets.
5. Safe by design et moindre privilège.
6. Aucun accès système direct et incontrôlé depuis le LLM.
7. Test before trust : builds/tests/mesures font foi.
8. Mémoire persistante indépendante de la fenêtre de contexte.
9. Apprentissage durable uniquement à partir d'expériences validées.
10. Provenance/licence/version/hash lorsque possible.
11. Reproductibilité des environnements, builds et assets dérivés.
12. Extensibilité via plugins/adapters contrôlés.
13. Actions sensibles auditables et confirmables.
14. Pas d'action destructive silencieuse.
15. Cœur model-agnostic : KodeBrain peut changer sans réécrire Kodepoia.

## 2. Vue d'ensemble

```text
Utilisateur
   ↓
KodeStudio
   ↓
KodeProjectWizard → Project DNA → KodeProduct (GDD/PRD/MVP)
   ↓
KodeOrchestrator
Planner → Context → Executor → Verifier → Recorder
   ↓
KodeBrain / KodeModelRouter
   ↓
Protected Core P0
Guardian • Sandbox • Secrets • Permissions • ResearchGuard
Schema • DataGovernance • Backup • Recovery • Audit • SafeChange
   ↓
┌────────────────┬─────────────────┬─────────────────┐
│ Intelligence   │ Development     │ Content         │
│ Memory         │ Code            │ Vault           │
│ Research       │ Godot           │ AssetPipeline   │
│ Experience     │ Desktop         │ ComfyUI         │
│ Bench          │ GameDesign      │ Blender         │
│ Observability  │ Backend*        │ Audio/Voice     │
│ Context        │ PlatformSvc*    │ Cinematics      │
└────────────────┴─────────────────┴─────────────────┘
   ↓
Quality → Security/Supply Chain → Build/Release → Memory/Experience

* conditionnel selon Project DNA
```

## 3. KodeStudio

Cockpit desktop moderne avec : Chat, Projects, Project DNA, Product, Roadmap, Architecture, Decisions, Code, Assets, Godot, Blender, ComfyUI, Audio/Voice, Cinematics, Research, Tests, Health, Budget, Security, Licences/BOM, Builds/Releases, Diagnostics, Memory, Models et Settings.

Deux modes : wizard guidé et formulaire expert.

## 4. KodeProjectWizard / Project DNA

Questions minimales : type de projet, moteur/framework, dimensions 2D/2.5D/3D/hybride, genre, **plateformes cibles obligatoires**, inputs pertinents, style, FPS/résolution/budgets, fonctionnalités, outils autorisés, politique réseau/téléchargement, lineage, résumé/validation.

Plateformes représentables : Windows, Linux, macOS, Android, iOS/iPadOS, Web, Steam Deck, XR/OpenXR et interfaces d'extension consoles.

Décisions : YES / NO / UNDECIDED.

## 5. KodeProduct / KodeGameDesign

KodeProduct gère PRD/GDD, MVP, scope, user stories, use cases, critères d'acceptation, exigences non fonctionnelles, jalons et traçabilité requirement→code→test.

KodeGameDesign couvre gameplay pillars, core loop, mechanics, level/quest design, progression, combat, récompenses, économie, difficulté, équilibrage et playtests.

## 6. KodeBrain et multi-modèles

Le cerveau est remplaçable et local via Ollama/GGUF. Les modèles concrets sont choisis par KodeBench.

KodeModelRouter peut déléguer selon la tâche à des rôles tels que :
- KodeFast : routage/petites tâches ;
- KodeCore : cerveau principal multimodal/outils ;
- KodeCoder : tâches de code complexes ;
- KodeEmbed : embeddings/RAG ;
- KodeVision : optionnel si la vision du Core est insuffisante.

Les modèles lourds ne sont pas supposés résider simultanément en VRAM.

## 7. KodeOrchestrator

Cycle standard : demande → task contract → Planner → Context Builder → Guardian → snapshot si nécessaire → Sandbox/Executor → Tests/Verifier → Health/Budget/Regression → commit ou correction → Memory → Experience candidate.

Planner/Executor/Verifier peuvent être plusieurs passes du même modèle.

## 8. Protected Core P0

### KodeGuardian
Policy engine, risk scoring, approvals, scope limits, kill switch, contrôle outils/plugins.

### KodeSandbox
Isole scripts générés/téléchargés, packages, Custom Nodes, installateurs, binaires et commandes à risque.

### KodeSecrets
Secrets hors contexte LLM et hors mémoire vectorielle ; redaction des logs ; broker de signature/authentification.

### KodeResearchGuard
Web/GitHub/YouTube = données non fiables, jamais instructions. Défense contre indirect prompt injection et téléchargements malveillants.

### KodeSchema / KodeDataGovernance / KodePermissions
Versionnement/migrations ; scopes de mémoire/dataset ; permissions par outil/projet/action.

### Backup / Recovery / Audit / SafeChange
Snapshots, reprise crash/OOM, journal complet et dry-run des changements dangereux.

## 9. Intelligence

KodeMemory : working, project, global validated knowledge, semantic, temporal, negative, research cache, experience queue.

KodeContext sélectionne seulement les éléments pertinents : DNA, exigences, code/scene/asset graphs, mémoire, docs, erreurs, décisions et historique.

KodeResearch interroge projet, docs locales/officielles, GitHub, sources techniques, forums et YouTube ; YouTube peut fournir transcript, STT local, timestamps et frames analysées.

KodeExperience ne promeut une expérience qu'après validation, provenance/licence et DataGovernance.

KodeBench compare les cerveaux et les fine-tunings par compilation, tests, régressions, tentatives, vitesse, RAM/VRAM et qualité de patch.

## 10. KodeCode

Parsers/Tree-sitter, LSP, DAP, recherche, patch/diff, symbol graph, call graph, dependency graph. Pour Godot : scènes, nodes, scripts, signaux, resources, shaders, autoloads et assets.

## 11. KodeGodot

Spécialité principale : Godot 4.7.x.

2D : Node2D/CharacterBody2D/Area2D, TileSet/TileMapLayer, orthogonal/hex/isométrique, navigation, Camera2D, animation, particules/lumières, shaders canvas_item, Control/Theme et optimisation.

3D : scènes/resources, GLTF, PBR, animation, blend shapes, navigation, shaders et optimisation.

Automatisation : headless, logs, export CLI, screenshots/write-movie, benchmarks et tests.

## 12. KodeDesktop

Adapters : WinUI 3, WPF, Avalonia, Qt/PySide, Tauri et autres selon besoin. MVVM/MVC, async, SQLite, IPC, watchers, logs, accessibilité, localisation, packaging et updates.

## 13. KodeComfy / KodeVRAM

ComfyUI local : inventaire nodes/modèles, workflows prévalidés, queue/progress, model resolver, interruption/libération mémoire, sans cloud payant par défaut.

Workflows : sprites, portraits, tilesets, isométrique, icons/UI, textures, concepts, inpaint/outpaint, normal/height maps, upscale et audio lorsque compatible.

KodeVRAM décharge/recharge KodeBrain, ComfyUI, TTS/audio et autres moteurs lourds ; le contexte reste hors VRAM dans l'orchestrateur.

## 14. KodeBlender

Pilotage bpy/headless : modeling, retopology, PBR, UV, rigs, skinning, IK/FK, humans/animals, shape keys, animation, retargeting, LOD, optimisation et GLTF.

## 15. KodeAudio / KodeVoice

KodeAudio : musique, SFX, Foley, stems, loops, musique adaptative, édition et QA (LUFS, clipping, loop seams, formats/streaming).

KodeVoice : Voice Registry persistant, TTS local, multilingue, clonage seulement avec droits/consentement, forced alignment, phonèmes, visèmes, coarticulation, lip-sync 2D/3D et animation faciale.

Facial LOD : héros/cinématique → conversation → PNJ éloigné → aucun facial.

## 16. KodeCinematics

Storyboard, shots, timeline, cameras, dialogue, voice, lip-sync, facial, character animation, lighting, Foley/SFX/music, subtitles, grading et rendering.

Continuity Bridge : une suite peut reprendre exactement les derniers plans du jeu précédent, les remastériser, les re-rendre, les utiliser en flashback ou continuer directement.

## 17. Franchise / Canon / Persistence

Project Lineage : independent, sequel, prequel, spin-off, remake, remaster, DLC, port.

Franchise DNA conserve art direction, personnages, voix, leitmotivs, signature SFX, factions, lieux, règles narratives et branding.

KodeCanon conserve timeline, vivant/mort, relations, world states et endings.

KodePersistence gère saves locales, autosaves, intégrité, migrations, cloud conditionnel, conflits et KodeSaveBridge Game1→Game2.

## 18. KodeVault / AssetPipeline / VCS

KodeVault est la bibliothèque globale d'assets validés : voices, SFX, music, images, textures, 3D, animations, workflows, metadata/licences.

Reuse Scope : GLOBAL, STUDIO, FRANCHISE, SERIES, CHARACTER, ENTITY, PROJECT_FAMILY, PROJECT_ONLY, REFERENCE_ONLY.

Preservation : EXACT, IDENTITY, VARIATION_ALLOWED, REINTERPRETATION_ALLOWED, DO_NOT_REUSE.

KodeAssetPipeline sépare source assets, recipes, derived assets, cache et outputs afin de permettre le rebuild.

KodeVCS : Git + Git LFS ; abstraction Perforce possible plus tard.

## 19. Backend / PlatformServices / LiveOps

Activés seulement si Project DNA l'exige.

KodeBackend : auth, dedicated/authoritative server, DB, matchmaking, lobby, relay/NAT, replication, cloud saves, leaderboards, moderation, anti-cheat et monitoring.

KodePlatformServices : Steam/Google/Apple/Microsoft/etc., achievements, entitlements, DLC, billing, leaderboards, cloud saves, friends/presence.

KodeLiveOps : remote config, feature flags, content delivery, events, seasons, challenges/economy et A/B tests si explicitement demandé.

## 20. Quality

KodeTests, KodeRegression, KodeVisualQA, KodeAudioQA, KodeAccessibility, KodeLocalization/pseudo-localization, KodeDeviceLab, KodeAssetDoctor, KodeTextureOptimizer, KodeLOD et KodeShaderProfiler.

KodeHealth score : build, tests, warnings, security, dependencies, performance, memory, assets, audio, accessibility, localization, technical debt, licences, privacy.

KodeBudget par plateforme : FPS/frame time, CPU/GPU, RAM/VRAM, storage, draw calls, polygons, textures, audio memory/voices, build size, battery/thermal mobile et network online.

## 21. Security / supply chain

KodeAppSecurity protège les produits créés : threat modeling, input/auth/network validation, dependency security, secure storage, fuzzing si utile.

KodePrivacy : data inventory, purpose, consent, retention, deletion, store declarations.

KodeLicense/KodeBOM/KodeDependency/KodeCompatibility/KodeVersions/KodeMigration/KodeTechnicalDebt assurent provenance, verrouillage et maintenance.

## 22. Build / Release

KodeCI : lint/parse/compile/tests/regression/security/visual/performance selon phase.

KodeBuild : builds reproductibles Dev/Test/Staging/Production.

KodeRelease : version, changelog, packaging, signing, installers, assets store, compliance/checklists.

KodeUpdater : patches/channels/rollback.

KodeDiagnostics : crashes, hangs, ANR, stack traces, logs, dumps et performance post-release.

## 23. Mobile / stores

Android/iOS uniquement si ciblés. Android : build/signing/AAB/APK/device/store. iOS : préparation Windows possible, build/signing final via macOS/Xcode lorsque requis. Les exigences de stores sont recherchées à jour au moment de la release.

## 24. KodePlugin SDK / Observability

Plugin SDK : permissions, version, interfaces, dépendances, provenance et sandbox policy.

KodeObservability mesure Kodepoia : tokens/s, latency, context, RAG, tool success, first-patch success, retries, RAM/VRAM, durée/échecs.

## 25. Priorités de construction

P0 : Guardian, Sandbox, Secrets, Permissions, ResearchGuard, Schema, DataGovernance, Backup, Recovery, Audit, SafeChange, integrity checks.

P1 : Health, Budget, Product, Versions, Dependency, VCS, AssetPipeline, Migration, License/BOM, AppSecurity, Privacy, TechnicalDebt, CI/Build, Diagnostics, Cinematics, Canon, Persistence, Plugin SDK, Observability, interfaces Backend/PlatformServices.

P2 intégré à l'architecture : Accessibility, Localization, UX QA, Audio, Fonts, TextureOptimizer, LOD, ShaderProfiler, AssetDoctor, DeviceLab, GameDesign/Balance/Playtest.

## 26. Structure d'un projet géré

```text
MyProject/
└── .kodepoia/
    ├── project.yaml
    ├── dna.yaml
    ├── product/ architecture/ decisions/
    ├── memory/ graphs/
    ├── health/ budgets/
    ├── tests/ visual_tests/ benchmarks/
    ├── audit/ backups/ snapshots/
    ├── research/ licenses/ bom/
    ├── workflows/ diagnostics/ releases/
```

## 27. Règle de changement

À compter du 21 août 2026, l'architecture v1.0 est gelée. Un changement de fondation exige un ADR avec problème, alternatives, impacts, migration, rollback, décision et validation.
