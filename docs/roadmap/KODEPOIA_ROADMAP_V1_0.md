# Kodepoia — Roadmap v1.0

Architecture de référence : **v1.0 gelée le 21 août 2026**.

Principe : construire le système autour du modèle, mesurer, puis spécialiser le modèle. Aucun fine-tuning massif avant benchmark et outillage.

## R0 — Repository & Governance

Livrables : dépôt, docs gelées, ADR template, Git/LFS policy, sécurité repo, CI bootstrap, module skeleton, validation locale, branches.  
DoD : structure valide, documents présents, checks PASS, aucun secret/poids modèle, gros binaires couverts par LFS policy.

## R1 — KodeStudio minimal + Protected Core

Ordre : Guardian → Permissions → Audit → SafeChange → Sandbox → Secrets → Schema → DataGovernance → Backup → Recovery → ResearchGuard → KodeStudio minimal.

DoD : actions interdites bloquées, actions à risque contrôlées, secrets redacted, crash/recovery testés, kill switch opérationnel.

## R2 — Project Wizard + DNA + Product

Wizard adaptatif, plateformes cibles obligatoires, inputs conditionnels, style, budgets, features, outils IA, policies download/install, lineage. PRD/GDD/MVP/requirements/acceptance criteria.

Test clé : Windows-only n'ajoute aucune logique tactile/mobile.

## R3 — Brain + ModelRouter + Memory + Context

Abstraction Ollama, streaming, tool calling, structured outputs, registry/router multi-modèles, SQLite/vector memory, scopes/governance, Context Builder. Baseline KodeBench sur 2–3 modèles locaux.

## R4 — KodeCode

Files/search/patch, Git worktrees, parsers/Tree-sitter, LSP/DAP, symbol/call/dependency graphs et outils structurés. Aucun accès direct hors tool API.

## R5 — KodeGodot 4.7.x

2D : GDScript typé, TileSet/TileMapLayer, isométrique, UI/Theme, shaders, navigation, animation, QA.  
3D : scenes/resources, GLTF, PBR, animation/blend shapes, navigation, shaders.  
Automation : headless, parse, export, logs, screenshots/write-movie, benchmarks.

## R6 — Quality / Health / Budget / CI

Health, Budget, Tests, Regression, VisualQA, Accessibility, Localization, TechnicalDebt, CI/Build, AppSecurity baseline, Privacy baseline, License/BOM. Tout patch majeur doit avoir validation et rollback.

## R7 — Research sécurisé

Docs locales/officielles, Web, GitHub, forums, YouTube. Transcript/STT/frames/version-awareness. ResearchGuard empêche contenu externe de devenir instruction agentique.

## R8 — Vault / AssetPipeline / VCS

Vault inter-projets, reuse scope/preservation, versioning, duplicate detection, semantic search. Source vs derived assets, reproducible transforms/cache/rebuild. Git + LFS.

## R9 — ComfyUI + VRAM

Connexion locale, queue/progress, inventory nodes/models, workflows validés, model resolver, interruption/free memory. Graphisme 2D/UI/textures/concepts. VRAM scheduling unload/reload.

## R10 — Blender / 3D

bpy/headless, geometry, UV/PBR, rigs, animation, retarget, humans/animals, LOD, GLTF et validation topology/normals/weights/budgets.

## R11 — Audio / Voice / Cinematics / Franchise

Music/SFX/Foley/QA, Voice Profiles, multilingual TTS, lip-sync, visèmes, facial LOD, shots/timelines, Continuity Bridge, Franchise DNA, Canon et Persistence/SaveBridge.

## R12 — Desktop applications

Adapters WinUI/WPF/Avalonia/Qt/Tauri, MVVM, SQLite, async, IPC, accessibility/localization, installers/update. DoD : créer/compile/test une application Windows moderne depuis le Wizard.

## R13 — Mobile / Platform / Release

Android export/signing/AAB/APK/device tests/store ; interface iOS/Mac/Xcode ; DeviceLab ; KodeRelease/Updater/Diagnostics et compliance actuelle.

## R14 — Backend / Platform Services / LiveOps

Conditionnel. Auth, DB, authoritative server, matchmaking/lobby, cloud saves, achievements/entitlements/billing, remote config/feature flags/content delivery/events.

## R15 — Experience / Bench / Fine-tuning

Collecte des expériences validées → nettoyage/déduplication/licence/governance → benchmark des lacunes → QLoRA si utile → conversion/GGUF/Ollama → KodeBench avant/après. Rejeter tout fine-tuning qui régresse les domaines critiques.

## R16 — Hardening / Beta / v1.0

Red-team prompt injection/malicious repo/secrets/plugins/destructive commands/corrupted memory/recovery. Tests sur vrais projets Godot 2D/3D, vraie app Windows, ComfyUI, audio/voice et projet long terme.

## Ordre d'exécution

1. **Fondation utilisable : R0→R6**
2. **Recherche et multimédia : R7→R11**
3. **Apps/plateformes/services : R12→R14**
4. **Spécialisation et stabilisation : R15→R16**

La phase active au moment de la création de ce fichier est **R0**.
