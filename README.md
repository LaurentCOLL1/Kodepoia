# Kodepoia

**Studio local-first de développement assisté par IA pour jeux vidéo, applications et médias.**

Kodepoia rassemble dans **KodeStudio** la conception d'une Vision, la programmation, la recherche, les contenus numériques, la mémoire des projets et les outils IA locaux. Un projet peut évoluer de l'idée au prototype, puis aux tests et à la maintenance, avec validation humaine et actions gouvernées.

[**Télécharger Kodepoia 1.1.1 (Windows)**](https://github.com/LaurentCOLL1/Kodepoia/releases/tag/v1.1.1) · [Guide utilisateur](docs/user/KODEPOIA_USER_GUIDE.md) · [Roadmap V2](docs/roadmap/KODEPOIA_ROADMAP_V2.md)

> **État au 8 octobre 2026 :** Kodepoia **1.1.1 stable est publiée**. La roadmap V2 et R1–R20 sont **COMPLETE + NORMALIZED**. L'upgrade réel installé **1.1.0 → 1.1.1** reste en qualification avant de pouvoir déclarer cette release elle-même **COMPLETE + NORMALIZED**.

## Différentes utilisations de Kodepoia

| Usage | Ce que Kodepoia aide à faire |
| --- | --- |
| **Jeux vidéo 2D** | Concevoir, programmer, tester et faire évoluer un projet Godot 2D : gameplay, scènes, scripts, prototypes. |
| **Jeux vidéo 3D** | Organiser un projet Godot 3D, ses systèmes et scènes ; intégrer et contrôler les ressources graphiques et animations disponibles. |
| **Applications Windows** | Définir une application de bureau, son interface et sa logique ; employer selon le projet Qt, WPF, WinUI 3, Avalonia ou Tauri, puis tester et préparer le packaging. |
| **Projets Android et iOS** | Choisir la cible dès la création ; préparer code, builds et contrôles selon les outils disponibles. SDK, environnement Apple, signature et publication nécessitent leurs prérequis propres. |
| **Utilitaires et logiciels métier** | Transformer un besoin en Vision, exigences, code, tests et maintenance traçable. |
| **Recherche et documentation** | Découvrir des sources, inspecter et sélectionner des preuves, produire des synthèses citées et enregistrer des *Research Packs*. |
| **Connaissances et mémoire de projet** | Rechercher dans les sources et fichiers gouvernés, composer un contexte traçable pour Chat, KodeCode et les espaces spécialisés. |
| **Images, sons, voix et cinématiques** | Planifier et intégrer des ressources médias avec les workflows et outils (dont ComfyUI) réellement installés. |
| **IA locale avec Ollama** | Choisir les modèles installés, attribuer FAST/CORE/CODE/HEAVY, dialoguer et comparer leurs capacités. |
| **Amélioration de modèles IA** | Curater explicitement les données, benchmarker, décider TRAIN/NO_TRAIN, encadrer SFT/LoRA/QLoRA, évaluer/exporter/promouvoir un candidat avec contrôles de régression ; Kaggle reste conditionnel. |
| **Orchestration de projet** | Coordonner plusieurs espaces de travail, dépendances, transferts de contexte, approbations et reprises contrôlées. |

### Exemples concrets

- **Créer un jeu d'aventure 2D** : créer un projet Godot, rédiger la Vision et le MVP, programmer les mécaniques, tester et conserver les décisions.
- **Construire un jeu 3D narratif** : définir les scènes et interactions, travailler modèles/animations/audio avec des outils compatibles, puis vérifier leur provenance et leur intégration.
- **Développer une application Windows** : choisir la pile technique, concevoir les écrans, programmer les fonctionnalités et préparer les tests et l'installateur.
- **Conduire une recherche sourcée** : chercher des références, les examiner et produire un Research Pack avec citations pour le projet.
- **Spécialiser une IA locale** : comparer les modèles Ollama, détecter les lacunes, puis préparer un entraînement seulement si l'utilisateur approuve les données et si le matériel et les évaluations le permettent.

### Les espaces de travail

**Projets / Project DNA / Vision** structurent les objectifs, exigences et contraintes ; **Chat / KodeCode** aident à concevoir et programmer ; **Research / Evidence / Project Knowledge** assurent recherche, citations, contexte et mémoire ; **Model Lab** couvre modèles, benchmarks, tuning, évaluation, export et rollback ; les **spécialistes** couvrent jeux, applications et médias selon les dépendances ; **Orchestration** coordonne les espaces avec contrôle des mutations.

Kodepoia **n'est pas une promesse de génération automatique d'un jeu AAA à partir d'une phrase**. Les résultats et actions sensibles doivent être vérifiés et approuvés. Les fichiers de projet, conversations et Research Packs ne sont jamais automatiquement considérés comme des données d'entraînement. Ollama, ComfyUI, GPU, Kaggle, recherche web et SDK restent optionnels ou dépendants de leur disponibilité ; les usages local-first compatibles peuvent fonctionner hors ligne.

## Installer Kodepoia sous Windows

### Version stable actuelle : `v1.1.1`

Télécharger exclusivement **`KodepoiaSetup.exe`** depuis la [Release GitHub Kodepoia 1.1.1](https://github.com/LaurentCOLL1/Kodepoia/releases/tag/v1.1.1).

| Vérification | Valeur |
| --- | --- |
| Canal et version | `stable` / `1.1.1` |
| Source exacte | `aa1c80389b10f5ef44737241bf192c04f847e4ec` |
| Taille | `38880869` octets |
| SHA-256 | `c8e7949ead2e1e14adece7cb9826f0b1be689b81ac814eef2f041760b9f738cd` |
| Authenticode | `NotSigned`, `production_signed=false` |
| Exception TUF ciblée | `allow-unsigned` pour cet installateur exact |
| WinGet | Pas de publication pour 1.1.1 |

1. Télécharger l'installateur depuis la release officielle.
2. Vérifier si souhaité l'empreinte avec `Get-FileHash .\KodepoiaSetup.exe -Algorithm SHA256`.
3. Ouvrir l'assistant et choisir librement le **lecteur et dossier** d'installation.
4. Lancer **KodeStudio** depuis le menu Démarrer ou le raccourci créé.

L'installateur intègre le runtime : **Python et pip ne sont pas nécessaires** sur la machine cible. Il n'a pas de signature Authenticode de production ; Windows peut donc afficher un avertissement. Contrôler la provenance et l'empreinte plutôt que supposer une signature inexistante.

### Chaîne de mises à jour TUF

La génération publique 1.1.1 comprend **Root v2, Targets v10, Snapshot v12 et Timestamp v12**. Elle lie la cible stable à sa source, sa version, sa taille et son SHA-256 exacts ; l'updater refuse métadonnées expirées, rollback, signatures incorrectes et payloads modifiés. Snapshot et Timestamp sont à validité courte et exigent des renouvellements signés. Une indisponibilité de la recherche de mises à jour ne doit pas empêcher le travail local.

**La preuve live installée 1.1.0 → 1.1.1 (découverte, téléchargement, upgrade, relance, dossier personnalisé conservé, `up-to-date`, smoke et désinstallation) est encore en cours** ; sa validation ne doit pas être remplacée par les tests historiques.

### Versions historiques et désinstallation

La dernière version stable avant 1.1.1 était [Kodepoia 1.1.0](https://github.com/LaurentCOLL1/Kodepoia/releases/tag/v1.1.0). `v1.1.0-rc8` est une ancienne beta ayant servi aux qualifications `rc7 → rc8` et `rc8 → 1.1.0`, pas la version recommandée. Le `KodepoiaSetup.exe` présent à la racine du dépôt est un miroir historique de `rc1`, à ne pas confondre avec l'asset stable.

Pour désinstaller : **Paramètres Windows → Applications → Applications installées → Kodepoia**, ou le raccourci de désinstallation.

## Français / English

KodeStudio v1.1 choisit automatiquement le français sur un système français et conserve l'anglais comme langue disponible. La langue peut être modifiée dans **Paramètres**.

La couverture française de R17 cible en priorité :

- navigation principale et onboarding ;
- création de projet ;
- listes et aides contextuelles ;
- Chat & Vision ;
- actions de sécurité principales.

Les panneaux spécialisés hérités de v1.0 conservent leur fallback anglais lorsqu'un catalogue français spécialisé n'existe pas encore : Kodepoia préfère afficher un libellé anglais exact plutôt qu'une traduction inventée.

## Création de projet guidée

Le bouton **Nouveau projet…** ouvre le Wizard accepté de Kodepoia, enrichi sans casser son contrat R12–R14.

Les champs restent éditables librement, mais des listes aident les débutants à démarrer :

- **Genres** : RPG / jeu de rôle, Simulation, Sexe / adulte, Stratégie, Action, Aventure, Gestion, Sandbox, Survie, Horreur, FPS/TPS, Plateforme, Puzzle, Visual novel, Course, Sport, Éducatif, etc. ;
- **Styles graphiques** : Réaliste, Photoréaliste, Stylisé, Anime/manga, Cel shading, Peint à la main, Pixel art, Low poly, Isométrique, Cartoon, Rétro, Minimaliste ;
- **Portée** : Prototype, Vertical slice, Petit projet indépendant, Projet indépendant ambitieux, AA, AAA / très ambitieux ;
- **Public** : Grand public, Famille, Joueurs expérimentés, Adultes, Professionnels, Éducation/étudiants.

Ces listes sont des **suggestions**, jamais des restrictions. L'utilisateur peut toujours saisir sa propre formulation.

## Chat & Vision du projet

Le menu **Chat** de v1.1 est fonctionnel. Il sert notamment à transformer une idée libre en une Vision structurée :

- Summary / Résumé ;
- Goals / Objectifs ;
- Success metrics / Mesures de réussite ;
- Constraints / Contraintes ;
- MVP ;
- Out of scope / Hors périmètre ;
- Requirements / Exigences ;
- Acceptance criteria / Critères d'acceptation.

Kodepoia demande des précisions quand une décision importante manque : public, objectif, mesure de réussite, contraintes, portée du MVP, éléments hors périmètre, etc. Une modification ultérieure de la Vision est traitée comme une nouvelle intention à réconcilier avec le brouillon existant.

Deux modes sont disponibles :

- **Mode guidé** : fonctionne sans modèle IA et pose des questions déterministes pour éviter un écran vide ou bloquant.
- **Ollama local** : si Ollama et un modèle local sont disponibles, Kodepoia utilise l'API locale structurée pour proposer et mettre à jour la Vision. Aucune API cloud n'est requise pour ce flux.

Les brouillons de Vision peuvent être conservés localement sous `.kodepoia/vision/` dans le projet.

## Ollama — optionnel

Kodepoia reste model-agnostic. Ollama est optionnel pour l'installation de base mais permet d'utiliser les fonctions IA locales.

Diagnostic :

```powershell
kodepoia ollama-status
```

Benchmark de modèles locaux :

```powershell
kodepoia bench-models --model <candidate1> --model <candidate2> --model <candidate3>
```

Les poids de modèles (`*.gguf`, `*.safetensors`, checkpoints…) ne sont pas intégrés au dépôt Git ni à `KodepoiaSetup.exe`.

## Installation développeur depuis les sources

Prérequis recommandés : Python 3.12, Git et Git LFS.

```powershell
git clone https://github.com/LaurentCOLL1/Kodepoia.git
cd Kodepoia
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,ui,code]"
kodepoia-studio
```

Validation locale :

```powershell
python -m pip install -r scripts/requirements-r0.txt
./scripts/check_repo.ps1
pytest
```

## Construire `KodepoiaSetup.exe`

La construction Windows utilise Nuitka/PySide6 pour figer KodeStudio puis Inno Setup 6 pour créer l'installateur.

```powershell
./scripts/build_windows_installer.ps1
```

Sorties attendues :

```text
dist/windows/KodepoiaSetup.exe
dist/windows/installer-manifest.json
```

Le workflow `.github/workflows/windows-installer.yml` effectue en plus une installation silencieuse temporaire dans un dossier personnalisé, vérifie la présence des ressources TUF de l'updater, lance un smoke test de l'exécutable installé puis valide la désinstallation avant de publier l'artefact CI.

### Signature

Le candidat stable 1.1.1 est `NotSigned` (`production_signed=false`). L'exception TUF `allow-unsigned` est limitée à cet artefact exact et ne constitue pas une autorisation générale d'accepter des exécutables non signés.

## Principes non négociables

1. Local-first et utilisable hors ligne pour les fonctions qui le permettent.
2. Création de projet consciente des plateformes cibles.
3. Sécurité par conception et principe du moindre privilège.
4. Aucun accès incontrôlé du modèle au système hôte.
5. **Test before trust** : builds, tests et mesures font foi.
6. Mémoire de projet persistante.
7. Apprentissage uniquement à partir d'expériences validées.
8. Provenance, licences et reproductibilité.
9. Aucune action destructive silencieuse.
10. Extensibilité via plugins/adapters contrôlés.

## Structure du dépôt

```text
Kodepoia/
├── docs/                 Architecture, ADR, continuité et roadmap
├── src/                  Modules du produit
├── tests/                Tests automatisés
├── scripts/              Vérifications et outils de build
├── packaging/            Packaging/installateurs natifs
├── schemas/              Schémas versionnés lisibles par machine
├── configs/              Configurations non secrètes et exemples
└── .github/              CI et workflows
```

## Gouvernance

L'architecture v1.0 reste gelée. Une évolution ne réécrit pas rétroactivement R1–R16. Les changements de fondation passent par un ADR et les phases suivantes utilisent des branches, des tests exact-head, des merges protégés par SHA et une continuité normalisée.

Documents principaux :

- `docs/user/KODEPOIA_USER_GUIDE.md` — guide complet d’utilisation ;
- `docs/continuity/STATE.md` — autorité immédiate de reprise ;
- `docs/continuity/NEXT.md` — prochaine frontière autorisée et prompt de reprise ;
- `docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md` — résumé compact de l'autorité publique courante ;
- `docs/release/V1_1_1_V2_CONSOLIDATION.md` — autorité de release 1.1.1 ;
- `docs/release/V2_6_6_TERMINAL_PUBLICATION.md` — clôture V2 et historique rc8 → 1.1.0 ;
- `docs/release/RC8_WINDOWS_E2E_ACCEPTANCE.md` — historique rc7 → rc8 ;
- `docs/architecture/KODEPOIA_ARCHITECTURE_V1_0.md` ;
- `docs/architecture/KODEPOIA_ARCHITECTURE_DECISIONS.md` ;
- `docs/roadmap/KODEPOIA_ROADMAP_V1_0.md` ;
- `docs/roadmap/R17_PLAN.md` ;
- `docs/roadmap/R18_PLAN.md` ;
- `docs/roadmap/R19_PLAN.md` ;
- `docs/roadmap/R20_PLAN.md` ;
- `docs/continuity/KODEPOIA_CONTINUITY_R20.md` — autorité terminale R20 + historique des opérations post-R20 ;
- `docs/continuity/KODEPOIA_CONTINUITY_R19.md` — autorité R19 gelée ;
- `docs/continuity/KODEPOIA_CONTINUITY.md` — grande archive historique R1–R18.

## Sécurité

Ne jamais committer de clé API, token, clé de signature, keystore, certificat privé, fichier `.env` ou autre credential. Voir `SECURITY.md`.

## Licence

Voir `LICENSE` pour le statut de licence du projet.