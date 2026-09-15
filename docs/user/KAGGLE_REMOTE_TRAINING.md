# Kodepoia — entraînement distant avec Kaggle

Kodepoia peut utiliser Kaggle comme capacité de calcul GPU distante pour les entraînements SFT et QLoRA gouvernés par R15. Kaggle n'est pas la source de vérité du modèle : Kodepoia prépare et signe logiquement le plan par son digest, Kaggle exécute le même worker R15.9 que l'entraînement local, puis Kodepoia télécharge et revalide les artefacts avant toute qualification ou promotion.

## Principes de sécurité

- Le dataset Kaggle créé par Kodepoia est privé. La commande d'upload n'utilise jamais `--public`.
- Le kernel Kaggle est privé et utilise un accélérateur explicite. Le choix recommandé et par défaut est `NvidiaTeslaT4`, qui correspond dans l'interface Kaggle actuelle à **GPU T4 x2**.
- Aucun token, mot de passe, clé Kaggle ou secret Hugging Face n'est écrit dans le bundle d'entraînement.
- Pour un modèle Hugging Face nécessitant une authentification, configurez `HF_TOKEN` dans **Kaggle Secrets**. Le script Kaggle le lit à l'exécution et ne le rapatrie pas dans les artefacts.
- Les exports train et validation sont contrôlés par SHA-256 avant l'upload puis de nouveau dans le worker R15.9.
- Après téléchargement, Kodepoia vérifie l'identité du plan, les digests de l'adapter et des checkpoints, les nombres de lignes, le nombre d'étapes et le fait que seul le split train a été optimisé.
- Un résultat modifié, incomplet ou lié à un autre plan est rejeté avant le registre de modèles et avant toute promotion Ollama.

## Accélérateurs Kaggle pertinents

L'interface Kaggle peut actuellement proposer **GPU T4 x2** et **TPU v5e-8** selon le compte. Pour Kodepoia R15, le chemin validé est le GPU T4 x2 : le moteur actuel utilise PyTorch, CUDA et, pour QLoRA, bitsandbytes/NF4.

Le champ API `machine_shape` reste `NvidiaTeslaT4` même lorsque l'interface affiche `GPU T4 x2`. Kaggle fournit alors deux GPU T4 de 16 Go chacun. Il faut les considérer comme **deux mémoires VRAM distinctes de 16 Go**, et non comme un GPU unique de 32 Go.

Le TPU v5e-8 n'est pas encore utilisé par Kodepoia R15. L'ajouter proprement demanderait un backend XLA/JAX ou PyTorch/XLA séparé et une nouvelle acceptance ; Kodepoia ne convertira donc jamais silencieusement un plan CUDA/QLoRA en entraînement TPU.

`NvidiaL4` reste compris par le backend pour les contextes Kaggle où il est réellement disponible, mais Kodepoia ne doit pas supposer qu'il est proposé à tous les comptes. Le T4 x2 demeure la cible portable par défaut.

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

## Quota GPU/TPU dans KodeStudio

La page **Paramètres** de KodeStudio affiche maintenant un panneau **Calcul distant Kaggle**. La lecture est volontairement manuelle : aucune requête Kaggle n'est effectuée au démarrage de KodeStudio. Cliquez sur **Actualiser le quota GPU/TPU** pour interroger la CLI officielle.

Kodepoia exécute alors :

```powershell
kaggle quota --format json
```

Cette commande, disponible à partir de Kaggle CLI 2.2.1, renvoie le quota hebdomadaire d'accélérateur avec les champs `resource`, `used`, `remaining`, `total` et `refreshAt`. KodeStudio présente séparément les lignes GPU et TPU et borne le temps restant à zéro si le serveur signale un dépassement.

La lecture de quota reste strictement observationnelle : elle ne démarre aucun notebook, ne change aucun `TrainingPlan`, ne choisit pas silencieusement un accélérateur et ne participe pas à la décision de promotion d'un modèle. Les identifiants restent gérés exclusivement par la CLI Kaggle déjà authentifiée.

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

## Utilisation des deux T4

La première acceptance du backend Kaggle valide l'allocation T4 x2, la confidentialité du bundle et la chaîne d'intégrité. L'exploitation multi-GPU doit rester explicite : Kodepoia ne doit pas additionner artificiellement les 2 × 16 Go de VRAM ni prétendre qu'un modèle nécessitant plus de 16 Go sur un seul device est automatiquement compatible.

Une phase suivante pourra qualifier un mode multi-GPU dédié (data parallel ou stratégie de sharding compatible PEFT/QLoRA) avec métriques séparées par GPU. Tant que cette phase n'est pas validée, le dimensionnement conservateur d'un entraînement doit rester basé sur 16 Go de VRAM par device.

## Internet et modèles

Le kernel active Internet par défaut parce que le worker peut devoir télécharger le modèle de base et les dépendances Python. Les données d'entraînement restent dans le dataset privé attaché au kernel. Une évolution ultérieure pourra fournir un mode totalement pré-emballé avec Internet désactivé lorsque toutes les dépendances et tous les poids nécessaires sont disponibles comme sources Kaggle privées.

## Limites Kaggle

Les quotas GPU, les accélérateurs disponibles et les limites de session sont gérés par Kaggle et peuvent varier dans le temps et selon le compte. Kodepoia doit donc traiter Kaggle comme un backend opportuniste : un manque de quota ou de GPU ne doit jamais modifier le plan, les données ou les règles de promotion. Dans ce cas, le run reste non qualifié et peut être relancé localement ou sur un autre backend compatible.
