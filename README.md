# Kodepoia

**Environnement local-first de création et de développement assisté par IA pour jeux et applications.**

Kodepoia accompagne un projet depuis l'idée initiale jusqu'à sa maintenance. KodeStudio réunit création guidée, Project DNA, Vision produit, développement, recherche, médias, plateformes, sécurité, tests et outils IA locaux dans une interface unique. Kodepoia n'est pas un simple frontend de LLM : les actions restent gouvernées par les limites et preuves définies par l'architecture.

## État du projet

- Architecture **v1.0 : COMPLETE + NORMALIZED et gelée**.
- Roadmap R1–R20 : **COMPLETE + NORMALIZED**. R20 est terminal ; aucun `R20.7` n'est autorisé.
- R17 — Distribution & Guided Creation UX, R18 — Trusted Release, Updates & Distribution Channels, R19 — Trusted Self-Update Corrective Release et R20 — Continuous Trusted Update Operations sont **COMPLETE + NORMALIZED**.
- R17 a livré l'installation Windows autonome, le français, la création guidée et le Chat/Vision local.
- R18 a livré l'identité de release canonique, bundles/manifests vérifiables, SBOM/provenance, frontière Authenticode, staging/promotion gouvernés, métadonnées TUF anti-rollback/freeze, découverte et installation consentie des mises à jour, préparation WinGet, drills de révocation/rollback et acceptance adversariale intégrée.
- R19 a établi le correctif de release et le parcours d'auto-mise-à-jour vérifié ; R20 a transformé cette chaîne en opération continue avec Root/Targets hors ligne, Snapshot/Timestamp en rôles online distincts, renouvellement planifié, monitoring/UX et acceptance long-offline.
- Release publique beta actuelle : **`v1.1.0-rc8`**, source exacte `fa787ab7ef76f2556b56ac1f058916a1425455af`.
- Le vrai E2E Windows installé **rc7 → rc8 est PASS** : découverte via métadonnées TUF, téléchargement, vérification, consentement explicite, lancement de l'installateur, upgrade, redémarrage en rc8 et nouvelle recherche confirmant rc8 comme version courante.
- La clôture canonique de cet incident updater est enregistrée par la PR #467, fusionnée comme `e40477699d98bda2f804c269339929de719556b5`. Toute reprise doit néanmoins re-fetcher le `main` live plutôt que supposer que ce SHA restera éternellement HEAD.
- Ancien nom de travail : `FORGEGAMEDEV`.

La clôture des phases ne signifie pas qu'une release stable signée de production existe. Les releases `rc` restent des **préreleases / beta** et le manifeste de l'installateur rc8 indique `production_signed=false`.

## Installer Kodepoia sur Windows — utilisateur final

### Méthode recommandée — GitHub Release `v1.1.0-rc8`

Télécharger **`KodepoiaSetup.exe`** depuis la release publique **[Kodepoia 1.1.0-rc8](https://github.com/LaurentCOLL1/Kodepoia/releases/tag/v1.1.0-rc8)**.

Installateur rc8 accepté :

- version : `1.1.0-rc8` ;
- source exacte : `fa787ab7ef76f2556b56ac1f058916a1425455af` ;
- taille : `37 730 750` octets ;
- SHA-256 : `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422` ;
- canal : `beta` ;
- signature de production revendiquée : **non** (`production_signed=false`) ;
- politique TUF Authenticode ciblée pour cet artefact exact : `allow-unsigned`.

`v1.1.0-rc8` est un candidat de validation sans nouvelle fonctionnalité updater. Il a été construit pour confirmer le parcours réel de mise à jour depuis la baseline corrective rc7. Le parcours installé rc7 → rc8 a été exécuté avec succès sur Windows sans substitution manuelle de l'installateur rc8. Les correctifs précédents restent hérités, notamment l'embarquement des ressources TUF requises par l'updater et le choix du lecteur/dossier d'installation.

1. Télécharger `KodepoiaSetup.exe` depuis la release rc8.
2. Facultatif mais recommandé : calculer son SHA-256 et le comparer à la valeur ci-dessus.
3. Exécuter `KodepoiaSetup.exe`.
4. Choisir le dossier d'installation souhaité dans l'assistant.
5. Suivre l'assistant d'installation en français ou en anglais.
6. Lancer **Kodepoia** depuis le menu Démarrer ou le raccourci Bureau.

Cette version est une **prérelease / beta**. Elle ne doit pas être présentée comme une release stable signée de production ; Windows/SmartScreen peut afficher un avertissement de réputation ou de signature.

`KodepoiaSetup.exe` installe KodeStudio dans le dossier choisi, crée une entrée de désinstallation et les raccourcis. L'exécutable embarque le runtime nécessaire : Python et `pip` ne sont pas requis sur la machine cible.

### Miroir historique à la racine du dépôt

Le fichier `KodepoiaSetup.exe` présent à la racine du dépôt et `KodepoiaSetup.exe.sha256` restent un **miroir historique de `v1.1.0-rc1`**. Ils ne constituent plus la méthode d'installation recommandée et ne doivent pas être confondus avec l'asset rc8 actuel.

Le checksum historique du miroir racine est `3d11af229392a6756a2bbc161af0150aca92168d843a42a3944ab5c01660b8e0`.

### Mise à jour intégrée et confiance TUF

La chaîne publique de mise à jour actuelle est :

- Root **v2** — rôle haute autorité conservé hors ligne et protégé par seuil ;
- Targets **v8** — signé hors ligne, préserve les targets rc3 à rc7 et autorise rc8 ;
- Snapshot **v10** — rôle online dédié, lié aux octets/version/hash/longueur exacts de Targets v8 ;
- Timestamp **v10** — rôle online séparé, lié aux octets/version/hash/longueur exacts de Snapshot v10 ;
- rc8 est autorisé par Targets avec la taille `37 730 750` et le SHA-256 exacts ci-dessus, `withdrawn=false` et `authenticode_policy="allow-unsigned"` ciblé sur cet artefact.

Les mises à jour refusent les métadonnées expirées, les rollbacks, les vues mixtes Snapshot/Targets et les artefacts dont le hash ou la taille ne correspondent pas à l'autorité TUF. Une indisponibilité du service de mise à jour ne doit pas empêcher le démarrage de Kodepoia ni le travail local.

Le vrai E2E Windows rc7 → rc8 est documenté dans `docs/release/RC8_WINDOWS_E2E_ACCEPTANCE.md`. L'ancien essai rc5 → rc6 reste historiquement **failed/incomplete** et ne doit pas être requalifié rétrospectivement comme succès.

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

Le workflow `.github/workflows/windows-installer.yml` effectue en plus une installation silencieuse temporaire dans un dossier personnalisé, vérifie la présence des ressources TUF de l'updater, lance un smoke test de l'exécutable installé puis valide la désinstallation avant de publier l'artefact CI.

### Signature

Le manifeste rc8 indique `production_signed=false`. Une véritable signature Windows ne sera revendiquée qu'après utilisation explicite d'un certificat/identité de signature réel et validation des preuves correspondantes. L'exception `allow-unsigned` utilisée par TUF pour rc8 est strictement target-scoped et ne vaut pas autorisation générale d'accepter des exécutables non signés.

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

- `docs/continuity/STATE.md` — autorité immédiate de reprise ;
- `docs/continuity/NEXT.md` — prochaine frontière autorisée et prompt de reprise ;
- `docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md` — résumé compact de l'autorité publique courante ;
- `docs/release/RC8_WINDOWS_E2E_ACCEPTANCE.md` — preuve terminale du vrai E2E rc7 → rc8 ;
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