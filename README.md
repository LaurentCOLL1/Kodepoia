# Kodepoia

**Local-first AI development environment for games and applications.**

Kodepoia est un environnement local-first de conception et de développement assisté par IA capable d'accompagner un projet de l'idée initiale jusqu'à sa maintenance. Il est conçu comme un système agentique outillé, persistant, sécurisé, multimodal et extensible, et non comme un simple frontend vers un LLM.

## État du projet

- Architecture : **v1.0 — GELÉE**
- Date de gel : **2026-08-21**
- R0 — Repository & Governance : **COMPLETE**
- Phase d'implémentation active : **R1 — KodeStudio minimal + Protected Core**
- Ancien nom de travail : `FORGEGAMEDEV`

L'architecture est volontairement **model-agnostic** : KodeBrain est remplaçable et les modèles locaux concrets seront sélectionnés par KodeBench plutôt que figés dans la plateforme.

## Principes non négociables

1. Local-first et utilisable hors ligne.
2. Création de projet consciente des plateformes cibles.
3. Sécurité par conception et principe du moindre privilège.
4. Aucun accès incontrôlé du modèle au système hôte.
5. Test before trust : les builds/tests/mesures font foi.
6. Mémoire de projet persistante.
7. Apprentissage uniquement à partir d'expériences validées.
8. Provenance, licences et reproductibilité.
9. Aucune action destructive silencieuse.
10. Extensibilité via plugins/adapters contrôlés.

## Priorités du cœur

- **KodeGuardian** — policy/risk gate
- **KodeSandbox** — exécution isolée
- **KodeSecrets** — secret broker et redaction
- **KodeHealth** — score de santé du projet
- **KodeBudget** — budgets techniques par plateforme

## Structure du dépôt

```text
Kodepoia/
├── docs/                 Architecture, ADR, continuité et roadmap
├── src/                  Modules du produit
├── tests/                Tests automatisés
├── scripts/              Vérifications locales et outils de développement
├── schemas/              Schémas versionnés lisibles par machine
├── configs/              Configurations non secrètes et exemples
└── .github/              CI, modèles d'issues et pull requests
```

## Gouvernance d'architecture

L'architecture v1.0 est gelée. Toute modification d'une fondation doit passer par un Architecture Decision Record (ADR) documentant contexte, options, impacts, migration, rollback et décision.

Documents de référence :

- `docs/architecture/KODEPOIA_ARCHITECTURE_V1_0.md`
- `docs/architecture/KODEPOIA_ARCHITECTURE_DECISIONS.md`
- `docs/roadmap/KODEPOIA_ROADMAP_V1_0.md`
- `docs/continuity/KODEPOIA_CONTINUITY.md`
- `docs/roadmap/R0_STATUS.md`

## Workflow Git

Les changements normaux passent par branches/worktrees et validation avant merge. `main` doit rester releasable et être protégé par règles/status checks lorsque les paramètres GitHub du dépôt le permettent.

Branches :

- `feature/<name>`
- `fix/<name>`
- `refactor/<name>`
- `research/<name>`
- `release/<version>`
- `agent/<task-id>`

## Gros fichiers

Les binaires lourds sont destinés à Git LFS. Les poids de modèles IA (`*.gguf`, `*.safetensors`, checkpoints, etc.) sont exclus du dépôt Git et seront gérés par KodeModelRegistry.

## Validation R0

```powershell
python -m pip install -r scripts/requirements-r0.txt
./scripts/check_repo.ps1
```

Le bootstrap est également exécuté par GitHub Actions sur Windows et Ubuntu.

## Sécurité

Ne jamais committer de clé API, token, clé de signature, keystore, certificat privé, fichier `.env` ou autre credential. Voir `SECURITY.md`.

## Licence

Le dépôt est actuellement privé. Voir `LICENSE` pour le statut de licence du projet.
