# Kodepoia

**Environnement local-first de création et de développement assisté par IA pour jeux et applications.**

Kodepoia accompagne un projet depuis l'idée initiale jusqu'à sa maintenance. KodeStudio réunit création guidée, Project DNA, Vision produit, développement, recherche, médias, plateformes, sécurité, tests et outils IA locaux dans une interface unique. Kodepoia n'est pas un simple frontend de LLM : les actions restent gouvernées par les limites et preuves définies par l'architecture.

## État du projet

- Architecture **v1.0 : COMPLETE + NORMALIZED et gelée**.
- Roadmap R1–R16 : **COMPLETE + NORMALIZED**.
- `main` v1.0 canonique au démarrage de R17 : `11194ec5bbb6a986d0fa206517ad3759378a80cf`.
- Évolution en cours : **v1.1 / R17 — Distribution & Guided Creation UX**.
- R17 ajoute l'installation Windows autonome, le français, la création guidée et le Chat/Vision local.
- Ancien nom de travail : `FORGEGAMEDEV`.

La fin de la phase v1.0 ne signifie pas qu'une release publique signée a été publiée. La signature de production et la publication restent des actions séparées et explicitement gouvernées.

## Installer Kodepoia sur Windows — utilisateur final

L'objectif de R17 est qu'un utilisateur **n'ait pas besoin d'installer Python ni d'utiliser `pip`**.

1. Ouvrir le workflow GitHub Actions **R17 Windows Installer**.
2. Télécharger l'artefact **`KodepoiaSetup-Windows`** du run accepté.
3. Extraire l'artefact et lancer **`KodepoiaSetup.exe`**.
4. Suivre l'assistant d'installation en français ou en anglais.
5. Lancer **Kodepoia** depuis le menu Démarrer ou le raccourci Bureau.

`KodepoiaSetup.exe` installe KodeStudio dans le profil utilisateur, crée une entrée de désinstallation et les raccourcis. L'exécutable embarque le runtime nécessaire : Python n'est pas requis sur la machine cible.

> Tant qu'aucune release GitHub publique n'a été explicitement publiée, l'artefact CI accepté est la source de l'installateur. Ne pas confondre un artefact de CI avec une release publique signée.

### Désinstallation

Utiliser **Paramètres Windows → Applications → Applications installées → Kodepoia**, ou le raccourci **Désinstaller Kodepoia** du menu Démarrer.

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

Le workflow `.github/workflows/windows-installer.yml` effectue en plus une installation silencieuse temporaire, un smoke test de l'exécutable installé et une vérification de l'uninstallateur avant de publier l'artefact CI.

### Signature

Le manifeste indique actuellement `production_signed=false`. Une véritable signature Windows ne sera revendiquée qu'après utilisation explicite d'un certificat/identité de signature réel et validation des preuves correspondantes.

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

- `docs/architecture/KODEPOIA_ARCHITECTURE_V1_0.md`
- `docs/architecture/KODEPOIA_ARCHITECTURE_DECISIONS.md`
- `docs/roadmap/KODEPOIA_ROADMAP_V1_0.md`
- `docs/roadmap/R17_PLAN.md`
- `docs/continuity/KODEPOIA_CONTINUITY.md`

## Sécurité

Ne jamais committer de clé API, token, clé de signature, keystore, certificat privé, fichier `.env` ou autre credential. Voir `SECURITY.md`.

## Licence

Voir `LICENSE` pour le statut de licence du projet.
