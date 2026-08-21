# Kodepoia — Registre des décisions d'architecture

**Synthèse : 21 août 2026**  
La spécification gelée prévaut sur les discussions antérieures sauf ADR ultérieur accepté.

1. **Nom** — le produit s'appelle Kodepoia ; FORGEGAMEDEV est abandonné.
2. **Local-first** — aucune API LLM distante n'est requise au quotidien.
3. **Offline-capable** — un projet configuré reste exploitable sans Internet.
4. **Machine grand public** — architecture compatible Windows/GPU VRAM limitée ; pas d'hypothèse datacenter.
5. **Model-agnostic** — le modèle de base n'est pas figé ; plusieurs candidats sont benchmarkés.
6. **Pas de fine-tuning en premier** — outils, mémoire, sécurité et benchmark précèdent QLoRA.
7. **Godot 4.7.x** — spécialité principale 2D/3D, GDScript typé, UI, shaders, isométrique et optimisation.
8. **Plateformes explicites** — la plateforme est demandée avant architecture gameplay/input/performance.
9. **No unwanted platform support** — une cible non choisie n'ajoute aucune contrainte implicite.
10. **Wizard + Project DNA** — questionnaire adaptatif/expert ; Project DNA constitue la référence technique.
11. **KodeProduct** — GDD/PRD/MVP/acceptance criteria font partie du système.
12. **Protected Core P0** — Guardian, Sandbox, Secrets, Permissions, ResearchGuard, Schema, Governance, Backup, Recovery, Audit, SafeChange dès le départ.
13. **Guardian non contournable** — pas de shell/files/network privilégié directement depuis KodeBrain.
14. **Sandbox** — scripts/packages/nodes/binaires non fiables sont isolés avant confiance.
15. **Secrets hors LLM** — tokens, keystores, certificats et clés ne vont ni dans prompts ni dans mémoire vectorielle.
16. **ResearchGuard** — contenu externe = donnée non fiable, jamais instruction ; défense indirect prompt injection.
17. **Mémoire persistante multi-niveaux** — working/project/global/semantic/temporal/negative/research/experience.
18. **Learning via mémoire d'abord** — pas de modification de poids après chaque erreur.
19. **Experience validée** — seules corrections testées/provenancées peuvent devenir dataset.
20. **Context Builder** — sélection ciblée, pas de dump systématique du dépôt.
21. **Code/Scene/Asset Graphs** — Kodepoia comprend dépendances, scènes, signaux, resources et assets.
22. **Git + snapshots + audit** — changements importants isolés, testés et réversibles.
23. **Git LFS** — gros binaires en LFS ; poids de modèles hors dépôt et gérés par registry.
24. **KodeHealth** — santé explicable du projet dès les premières phases.
25. **KodeBudget** — budgets techniques par plateforme dès les premières phases.
26. **P0/P1/P2 dans l'architecture initiale** — sécurité, QA, accessibilité, localisation et asset optimisation ne sont pas oubliés.
27. **ComfyUI local** — atelier graphique/audio compatible ; inventaire local avant téléchargement ; nodes tiers contrôlés.
28. **VRAM scheduler** — chargement séquentiel des moteurs lourds ; contexte stocké hors GPU.
29. **Blender** — moteur 3D piloté par bpy/headless plutôt que génération brute de vertices par LLM.
30. **Audio natif** — musique, SFX, Foley, stems, adaptive music et QA.
31. **Voix/lip-sync natifs** — Voice Registry, TTS, multilingue, phonèmes/visèmes, animation faciale 2D/3D.
32. **KodeVault global** — assets validés partageables entre projets avec provenance/version/licence.
33. **Reuse Scope** — GLOBAL/STUDIO/FRANCHISE/SERIES/CHARACTER/ENTITY/PROJECT_FAMILY/PROJECT_ONLY/REFERENCE_ONLY.
34. **Preservation Policy** — EXACT/IDENTITY/VARIATION_ALLOWED/REINTERPRETATION_ALLOWED/DO_NOT_REUSE.
35. **Franchise/Canon/Lineage** — suites, préquelles, spin-offs, remakes, remasters, DLC et ports sont explicitement représentés.
36. **Continuity Bridge** — une suite peut reprendre/remasteriser/re-rendre les derniers plans d'une cinématique précédente.
37. **Persistence/SaveBridge** — migrations de saves et import Game1→Game2 avec canon par défaut.
38. **Desktop apps** — Kodepoia ne se limite pas au GameDev ; WinUI/WPF/Avalonia/Qt/Tauri sont des adapters possibles.
39. **Mobile conditionnel** — Android/iOS seulement si ciblés ; iOS final via macOS/Xcode lorsque requis.
40. **Recherche Web/GitHub/YouTube** — permise sous contrôle ; priorité aux sources officielles et adaptation à la version réelle.
41. **CI/CD + diagnostics** — build, tests, release, updater et diagnostic post-release font partie de v1.
42. **Sécurité produit ≠ sécurité agent** — KodeGuardian protège l'hôte ; KodeAppSecurity protège le logiciel produit.
43. **DataGovernance ≠ Privacy** — gouvernance des données de Kodepoia distincte des données collectées par les produits créés.
44. **Backend/LiveOps conditionnels** — interfaces présentes, activation seulement si Project DNA le demande.
45. **Plugin SDK** — nouveaux moteurs/modèles/outils s'ajoutent sans casser les fondations.
46. **Multi-modèles autorisés** — KodeModelRouter peut sélectionner Fast/Core/Coder/Embed/Vision selon benchmark et ressources.
47. **Pas de simultanéité GPU supposée** — les modèles lourds sont chargés/déchargés selon KodeVRAM.
48. **Architecture v1.0 gelée** — toute modification de fondation nécessite un ADR.
