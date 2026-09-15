# Kodepoia — entraînement distant avec Kaggle

Kodepoia peut utiliser Kaggle comme capacité de calcul GPU distante pour les entraînements SFT et QLoRA gouvernés par R15. Kaggle n'est pas la source de vérité du modèle : Kodepoia prépare et signe logiquement le plan par son digest, Kaggle exécute le même worker R15.9 que l'entraînement local, puis Kodepoia télécharge et revalide les artefacts avant toute qualification ou promotion.

## Principes de sécurité

- Le dataset Kaggle créé par Kodepoia est privé. La commande d'upload n'utilise jamais `--public`.
- Le kernel Kaggle est privé et utilise un GPU explicite : `NvidiaTeslaT4` par défaut ou `NvidiaL4`.
- Aucun token, mot de passe, clé Kaggle ou secret Hugging Face n'est écrit dans le bundle d'entraînement.
- Pour un modèle Hugging Face nécessitant une authentification, configurez `HF_TOKEN` dans **Kaggle Secrets**. Le script Kaggle le lit à l'exécution et ne le rapatrie pas dans les artefacts.
- Les exports train et validation sont contrôlés par SHA-256 avant l'upload puis de nouveau dans le worker R15.9.
- Après téléchargement, Kodepoia vérifie l'identité du plan, les digests de l'adapter et des checkpoints, les nombres de lignes, le nombre d'étapes et le fait que seul le split train a été optimisé.
- Un résultat modifié, incomplet ou lié à un autre plan est rejeté avant le registre de modèles et avant toute promotion Ollama.

## Pré-requis

Installez la CLI Kaggle officielle et authentifiez votre compte. La méthode OAuth recommandée par la CLI actuelle est :

```powershell
kaggle auth login
```

Kodepoia ne lit pas et ne stocke pas le jeton. Il appelle uniquement la CLI Kaggle déjà authentifiée.

Vérification :

```powershell
kodepoia-kaggle-training doctor
```

Le diagnostic vérifie la présence de la CLI, sa version et qu'une requête authentifiée vers vos datasets fonctionne. Il n'affiche jamais de jeton d'accès.

## Flux d'entraînement

1. R15 construit un `TrainingPlan` gouverné, avec modèle/révision, tokenizer/révision, digests, dataset, hyperparamètres, quantification, seeds et autorisation `TRAIN`.
2. Kodepoia construit un wheel correspondant au code source à exécuter.
3. `prepare` crée un bundle local contenant seulement le wheel, les exports train/validation, le worker config, leurs digests et les métadonnées Kaggle privées.
4. `upload` crée le dataset privé Kaggle.
5. `dataset-status` vérifie que le dataset est disponible.
6. `run` pousse le kernel privé et déclenche l'exécution GPU.
7. `status` affiche l'état du dernier run Kaggle.
8. `fetch` télécharge les sorties et applique de nouveau le contrat de validation R15.9.
9. Les étapes R15 de benchmark, qualification et promotion restent inchangées : un entraînement Kaggle n'est jamais promu automatiquement.

## Commandes

Préparer un bundle à partir d'un plan R15 sauvegardé :

```powershell
kodepoia-kaggle-training prepare `
  --project-root M:\MonProjet `
  --plan M:\MonProjet\.kodepoia\training-plan.json `
  --wheel M:\Kodepoia\dist\kodepoia-1.1.0rc8-py3-none-any.whl `
  --username MON_COMPTE_KAGGLE `
  --dataset-slug kodepoia-training-data `
  --kernel-slug kodepoia-training-run `
  --accelerator NvidiaTeslaT4 `
  --output M:\MonProjet\.kodepoia\kaggle
```

Puis :

```powershell
kodepoia-kaggle-training upload --bundle <DOSSIER_DU_RUN>
kodepoia-kaggle-training dataset-status --bundle <DOSSIER_DU_RUN>
kodepoia-kaggle-training run --bundle <DOSSIER_DU_RUN>
kodepoia-kaggle-training status --bundle <DOSSIER_DU_RUN>
kodepoia-kaggle-training fetch --bundle <DOSSIER_DU_RUN>
```

Le backend ne lance pas automatiquement `upload` pendant `prepare`. Cette séparation est volontaire : l'envoi des données vers Kaggle reste une action explicite.

## T4 ou L4

Kodepoia accepte actuellement `NvidiaTeslaT4` et `NvidiaL4`. Le T4 est le choix par défaut pour maximiser la disponibilité. Le L4 peut être choisi lorsqu'il est disponible sur le compte Kaggle. Les accélérateurs retirés ou non retenus par la politique Kodepoia ne sont pas acceptés par la configuration.

## Internet et modèles

Le kernel active Internet par défaut parce que le worker peut devoir télécharger le modèle de base et les dépendances Python. Les données d'entraînement restent dans le dataset privé attaché au kernel. Une évolution ultérieure pourra fournir un mode totalement pré-emballé avec Internet désactivé lorsque toutes les dépendances et tous les poids nécessaires sont disponibles comme sources Kaggle privées.

## Limites Kaggle

Les quotas GPU, les accélérateurs disponibles et les limites de session sont gérés par Kaggle et peuvent varier dans le temps et selon le compte. Kodepoia doit donc traiter Kaggle comme un backend opportuniste : un manque de quota ou de GPU ne doit jamais modifier le plan, les données ou les règles de promotion. Dans ce cas, le run reste non qualifié et peut être relancé localement ou sur un autre backend compatible.
