# Guide d’utilisation de Kodepoia

> Guide utilisateur de référence pour Kodepoia / KodeStudio. La release publique Windows actuellement validée reste `v1.1.0-rc8`. Les fonctions **Ouvrir un projet existant**, **Projets récents** et le **gestionnaire graphique de modèles Ollama** décrites ici sont introduites après rc8 dans le code source et seront disponibles dans la première build/release qui intégrera cette évolution.

## 1. À quoi sert Kodepoia ?

Kodepoia est un environnement **local-first** de création et de développement assisté par IA pour les jeux et les applications. Son interface principale, **KodeStudio**, regroupe la définition du produit, le Project DNA, le Chat/Vision, le développement, la recherche, la génération de contenus, la sécurité, les tests, l’évaluation de modèles et le tuning local.

Kodepoia n’accorde pas un accès libre au système à un modèle. Les opérations sensibles restent soumises aux contrats, validations, confirmations et preuves définis par l’architecture.

## 2. Installation sous Windows

La release publique beta de référence est `v1.1.0-rc8`.

1. Télécharger `KodepoiaSetup.exe` depuis la release GitHub officielle de Kodepoia.
2. Facultatif mais recommandé : vérifier le SHA-256 indiqué dans le README de la release.
3. Lancer l’installateur.
4. Choisir le **lecteur et le dossier d’installation** voulus.
5. Terminer l’installation puis lancer Kodepoia depuis le menu Démarrer ou le raccourci Bureau.

La build rc8 est une prerelease/beta et son installateur n’est pas signé avec un certificat de production. Windows peut donc afficher un avertissement de réputation ou de signature.

L’exécutable Windows embarque son runtime : Python et `pip` ne sont pas nécessaires pour l’utilisation normale de l’application installée.

## 3. Premier démarrage de KodeStudio

Au démarrage, KodeStudio :

- charge les préférences utilisateur ;
- choisit la langue enregistrée ou la langue du système ;
- restaure le dernier projet Kodepoia encore valide lorsqu’un projet actif a été mémorisé ;
- démarre même si Ollama ou le service de mise à jour sont indisponibles ;
- conserve le fonctionnement guidé des écrans qui ne nécessitent pas de modèle IA.

La langue se change dans **Paramètres**. Un redémarrage peut être proposé afin d’appliquer uniformément la nouvelle langue.

## 4. Comprendre un projet Kodepoia

Un projet Kodepoia possède un dossier racine contenant notamment :

```text
mon-projet/
└── .kodepoia/
    ├── project.yaml
    ├── product/
    ├── vision/
    └── ...
```

Le fichier `.kodepoia/project.yaml` est le marqueur utilisé par KodeStudio pour reconnaître un projet Kodepoia existant. Le dossier racine devient le **project root** utilisé par les outils spécialisés.

Ne sélectionnez pas le dossier d’installation de Kodepoia lorsque KodeStudio demande le dossier d’un projet. Sélectionnez le dossier propre au jeu, à l’application ou à l’outil que vous développez.

## 5. Créer un nouveau projet

Ouvrir **Projets → Nouveau projet…**.

L’assistant permet notamment de définir :

- nom et dossier du projet ;
- type de produit ;
- moteur, version et dimension pour un jeu ;
- plateformes et budgets de performances ;
- fonctionnalités et outils ;
- services backend souhaités ;
- Vision produit ;
- objectifs, contraintes, MVP et hors-périmètre ;
- exigences et critères d’acceptation.

Les listes proposées pour les genres, styles graphiques, portées et publics sont des aides, pas des restrictions.

Après une création réussie, KodeStudio mémorise le nouveau dossier comme **projet actif**, l’ajoute aux **projets récents**, puis recharge l’application sur cette racine afin que tous les panneaux spécialisés utilisent le même projet.

## 6. Reprendre un projet existant

Dans une build intégrant la reprise de projet :

1. ouvrir **Projets** ;
2. cliquer **Ouvrir un projet existant…** ;
3. sélectionner le dossier racine du projet ;
4. KodeStudio vérifie la présence de `.kodepoia/project.yaml` ;
5. si le dossier est valide, il devient le projet actif et est ajouté en tête des projets récents ;
6. KodeStudio redémarre sur cette racine pour que Chat, Vision, Workspaces, tuning et outils spécialisés aient tous le même contexte.

Un dossier qui ne contient pas `.kodepoia/project.yaml` est refusé au lieu d’être silencieusement traité comme un projet Kodepoia.

### Projets récents

La page **Projets** affiche les racines récemment utilisées. Un double-clic ou le bouton **Ouvrir** active le projet sélectionné. **Retirer de la liste** supprime seulement l’entrée de l’historique : les fichiers du projet ne sont pas supprimés.

Si un dossier a été déplacé ou supprimé, KodeStudio le marque comme indisponible et ne le restaure pas automatiquement comme projet actif.

## 7. Chat & Vision

Le menu **Chat** aide à transformer une idée libre en Vision structurée avec :

- résumé ;
- objectifs ;
- mesures de réussite ;
- contraintes ;
- MVP ;
- hors-périmètre ;
- exigences ;
- critères d’acceptation.

Deux modes existent.

**Mode guidé** fonctionne sans IA locale. Il structure les informations de façon déterministe et permet de continuer même si Ollama n’est pas installé.

**Mode Ollama local** utilise un modèle local installé. Le modèle préféré pour le rôle **CORE** est automatiquement présélectionné dans le Chat/Vision lorsqu’il est disponible. L’utilisateur peut toujours sélectionner un autre modèle ou revenir au mode guidé.

Les brouillons de Vision peuvent être enregistrés dans `.kodepoia/vision/` du projet actif.

## 8. Installer et connecter Ollama

Ollama est optionnel pour Kodepoia mais nécessaire pour les fonctions qui exécutent un LLM local.

L’endpoint local par défaut utilisé par Kodepoia est :

```text
http://127.0.0.1:11434
```

Dans une build intégrant le gestionnaire de modèles, ouvrir **Paramètres → IA locale / modèles Ollama**.

L’écran affiche :

- l’adresse du serveur Ollama ;
- l’état de connexion et la version détectée ;
- les modèles installés ;
- un catalogue de modèles recommandés ;
- une zone permettant de saisir n’importe quel nom/tag Ollama ;
- les actions **Installer / mettre à jour**, **Actualiser** et **Supprimer** ;
- l’affectation des modèles aux rôles Kodepoia.

L’installation et la suppression passent par l’API locale d’Ollama. Elles sont exécutées hors du thread graphique pour éviter de bloquer l’interface pendant un téléchargement important.

## 9. Rôles de modèles dans Kodepoia

Kodepoia est conçu pour utiliser plusieurs modèles plutôt qu’un seul modèle pour toutes les tâches.

| Rôle | Usage prévu |
| --- | --- |
| **FAST** | tâches courtes, routage rapide, faible coût local |
| **CORE** | raisonnement général et Chat/Vision |
| **CODE** | génération, analyse et correction de code |
| **HEAVY** | tâches plus longues ou exigeantes lorsque la machine le permet |

Le gestionnaire propose actuellement comme candidats de départ `granite4.1:3b`, `qwen3.5:4b`, `qwen3.5:9b`, `gpt-oss:20b` et `north-mini-code-1.0:Q4_K_M`. Ce sont des **candidats de routage/benchmark**, pas une garantie qu’un tag particulier restera disponible indéfiniment dans un catalogue externe.

L’affectation d’un rôle est une préférence. Kodepoia doit continuer à vérifier qu’un modèle est réellement installé et disponible avant de l’utiliser.

## 10. Évaluer les modèles avant de leur faire confiance

Kodepoia dispose de KodeBench et de benchmarks locaux multi-modèles. Le principe est **test before trust** : un modèle n’est pas considéré meilleur uniquement parce qu’il est plus gros ou plus récent.

Depuis une installation développeur, on peut notamment comparer plusieurs modèles :

```powershell
kodepoia bench-models --role fast --model "granite4.1:3b" --model "qwen3.5:4b"
```

ou :

```powershell
kodepoia bench-models --role core --model "qwen3.5:9b" --model "gpt-oss:20b"
```

Les benchmarks peuvent mesurer la réussite des tâches, la stabilité entre répétitions, les temps de cold-load, les budgets de génération et les cas où le raisonnement consomme tout le budget sans produire de réponse finale satisfaisante.

## 11. Améliorer réellement un modèle : SFT, LoRA et QLoRA

Kodepoia possède déjà un pipeline de tuning local sous `kodepoia.tuning`. Il ne s’agit pas seulement de changer un prompt : le pipeline peut produire de nouveaux **adapters PEFT/LoRA** modifiant effectivement le comportement du modèle.

Trois modes sont prévus :

- `fixture_sft` : fixture déterministe pour tester le pipeline sans prétendre entraîner un vrai modèle ;
- `sft` : Supervised Fine-Tuning avec adapter LoRA ;
- `qlora` : fine-tuning LoRA sur modèle quantifié 4-bit lorsque la machine et les dépendances le permettent.

Le vrai worker de training utilise notamment **PyTorch, Transformers, PEFT, TRL, Datasets et Safetensors**. QLoRA utilise `bitsandbytes` et la quantification NF4 après vérification des capacités.

### Pourquoi Kodepoia ne lance pas l’entraînement automatiquement

Un modèle ne doit pas apprendre aveuglément chaque conversation ou chaque correction. Une mauvaise donnée peut dégrader le modèle, introduire des régressions ou mémoriser des informations qui ne devraient pas devenir des poids permanents.

Kodepoia impose donc une chaîne gouvernée :

```text
expériences/données validées
        ↓
dataset train + validation liés par hash
        ↓
probe des capacités CPU/GPU/RAM/VRAM
        ↓
plan SFT ou QLoRA immuable
        ↓
training + checkpoints
        ↓
évaluation
        ↓
export / conversion
        ↓
benchmark comparatif
        ↓
acceptation ou rejet
        ↓
packaging Ollama du candidat validé
```

Le plan d’entraînement lie explicitement le modèle, le tokenizer, leurs révisions/digests, le dataset, les seeds, les hyperparamètres, les ressources et le rapport de capacités. La reprise depuis checkpoint vérifie la filiation avant de continuer.

### Paramètres LoRA/SFT disponibles

Le moteur possède notamment :

- rank et alpha LoRA ;
- dropout ;
- modules cibles ;
- learning rate ;
- nombre maximal d’étapes ;
- batch train/validation ;
- gradient accumulation ;
- longueur de contexte ;
- gradient checkpointing ;
- fréquence de checkpoint et d’évaluation ;
- completion-only loss ;
- assistant-only loss pour les datasets compatibles ;
- seeds et mode déterministe ;
- limites de ressources et timeout.

## 12. Vérifier la machine avant un tuning

Pour un environnement développeur avec le module de tuning installé :

```powershell
python -m pip install -e ".[tuning]"
```

Pour QLoRA avec le backend bitsandbytes compatible :

```powershell
python -m pip install -e ".[tuning,tuning-bnb]"
```

Une sonde de capacités peut être lancée depuis le dossier racine du projet :

```powershell
python -m kodepoia.tuning --backend cpu --dtype float32
```

ou avec les paramètres GPU/quantification compatibles avec la machine. Le rapport est écrit par défaut dans :

```text
.kodepoia/tuning/r15_8_capability.json
```

Un vrai plan SFT/QLoRA exige une autorisation de training, un rapport de capacités lié par digest et des chemins de dataset train/validation gouvernés. Kodepoia ne doit pas contourner ces préconditions.

## 13. Panneau de tuning R15 dans KodeStudio

KodeStudio possède déjà un panneau R15 de tuning gouverné. Il permet d’inspecter le catalogue d’actions, l’état, les preuves, de lancer un **dry-run**, puis d’exécuter les actions autorisées avec confirmation explicite.

Ce panneau est volontairement plus strict qu’un bouton « améliorer automatiquement ». Une mutation nécessite la confirmation utilisateur et l’autorisation du backend correspondant.

En ligne de commande, le même service expose notamment :

```powershell
kodepoia r15 catalog --project-root .
kodepoia r15 status --project-root .
kodepoia r15 evidence --project-root .
```

Le catalogue indique les sous-commandes de tuning disponibles dans la version courante et permet de vérifier leur contrat avant exécution.

## 14. Exporter et remettre un modèle amélioré dans Ollama

Après entraînement et qualification, Kodepoia sait gérer :

- l’adapter Safetensors ;
- la conversion/export GGUF ;
- l’identité du modèle de base ;
- les digests des artefacts et évaluations ;
- un `Modelfile` Ollama ;
- la création d’un tag candidat Kodepoia ;
- un benchmark comparatif avant/après packaging.

Le pipeline préfère un export fusionné/GGUF validé. L’empaquetage direct d’un adapter est autorisé seulement lorsque l’identité immuable du modèle de base est prouvée et que la politique l’autorise explicitement.

Un candidat est rejeté lorsque la perte de qualité agrégée dépasse le seuil autorisé ou lorsqu’une tâche critique régresse au-delà du seuil critique.

## 15. Les quatre niveaux d’« amélioration » d’un modèle

Il est utile de distinguer quatre mécanismes :

1. **Sélection et routage** : choisir le meilleur modèle existant selon FAST/CORE/CODE/HEAVY.
2. **Contexte/RAG/mémoire projet** : donner de meilleures informations au modèle sans modifier ses poids.
3. **SFT/LoRA/QLoRA** : adapter réellement les poids via un adapter entraîné sur des données validées.
4. **Qualification et promotion** : prouver par benchmark que le modèle adapté est meilleur ou au minimum non régressif avant de l’utiliser comme modèle préféré.

Kodepoia possède déjà des briques pour ces quatre niveaux. La priorité UX restante est de rendre la chaîne complète d’amélioration plus lisible dans un futur **Model Lab** : choix du modèle de base, sélection du dataset validé, estimation RAM/VRAM, dry-run, entraînement, comparaison avant/après et promotion du candidat, sans supprimer les garde-fous R15.

## 16. Recherche, Vault et outils de création

Les panneaux spécialisés utilisent le projet actif comme contexte. Selon la configuration et les composants installés, KodeStudio donne accès aux fonctions de recherche, au Vault, à ComfyUI, aux outils Blender, aux fonctions de code et aux workspaces spécialisés.

Un changement de projet recharge KodeStudio afin d’éviter qu’un panneau ancien continue à écrire dans la racine du projet précédent.

## 17. Sécurité et arrêt d’urgence

Kodepoia est conçu autour du moindre privilège. Les workflows protégés peuvent être interrompus via le **Kill Switch / Arrêt d’urgence**. Un tuning réel utilise également un sandbox de processus, des budgets de ressources, des timeouts et une validation de filiation des checkpoints/artefacts.

Ne stockez jamais de clé privée, token, mot de passe, certificat privé ou secret de production dans un dataset d’entraînement ou dans le dépôt.

## 18. Mises à jour

Les mises à jour Windows reposent sur les métadonnées TUF validées par Kodepoia. La découverte d’une mise à jour ne suffit pas à lancer silencieusement un installateur : le parcours vérifie les métadonnées et l’artefact et demande le consentement utilisateur avant l’installation.

Une panne réseau ou une indisponibilité du service de mise à jour ne doit pas empêcher le démarrage et le travail local.

## 19. Installation développeur

Prérequis principaux : Python 3.12, Git et Git LFS.

```powershell
git clone https://github.com/LaurentCOLL1/Kodepoia.git
cd Kodepoia
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,ui,code]"
kodepoia-studio
```

Ajouter `tuning` et éventuellement `tuning-bnb` seulement sur une machine destinée au fine-tuning local.

## 20. Diagnostic rapide

### KodeStudio refuse un dossier de projet

Vérifier :

```powershell
Test-Path "CHEMIN_DU_PROJET\.kodepoia\project.yaml"
```

Le résultat doit être `True`.

### Ollama apparaît indisponible

Vérifier qu’Ollama est lancé et que l’endpoint configuré dans **Paramètres → IA locale / modèles Ollama** correspond au serveur local. Le défaut Kodepoia est `http://127.0.0.1:11434`.

### Le modèle CORE n’apparaît pas dans Chat/Vision

Cliquer **Actualiser** dans le gestionnaire de modèles, vérifier que le modèle est installé, puis enregistrer son rôle **CORE**. Le Chat/Vision ne sélectionne automatiquement un modèle préféré que s’il est réellement présent dans la liste retournée par Ollama.

### Un tuning est bloqué

Consulter le rapport de capacités et l’état R15. Un blocage de budget RAM/disque/VRAM, un digest incohérent, un dataset non gouverné ou une autorisation absente est un refus intentionnel et ne doit pas être contourné.

### Un projet récent est indiqué indisponible

Le projet a probablement été déplacé, supprimé ou son fichier `.kodepoia/project.yaml` n’est plus présent. Utiliser **Ouvrir un projet existant…** sur sa nouvelle localisation.

## 21. Bonnes pratiques

- conserver un projet par dossier racine clair ;
- versionner le code et la configuration du projet ;
- sauvegarder les données importantes avant un tuning lourd ;
- benchmarker plusieurs modèles avant de choisir les rôles ;
- utiliser RAG/contexte pour les connaissances fréquemment modifiées ;
- réserver le SFT/LoRA aux comportements et compétences que l’on veut stabiliser ;
- séparer strictement train et validation ;
- ne jamais promouvoir un modèle uniquement parce que la loss de training diminue ;
- comparer le candidat au modèle précédent sur KodeBench ;
- conserver provenance, licences et digests des modèles/datasets.

## 22. FAQ

**Dois-je installer Ollama pour ouvrir un projet ?**  
Non. La gestion de projets et le mode guidé fonctionnent sans Ollama.

**Kodepoia entraîne-t-il automatiquement mes modèles à partir de toutes mes conversations ?**  
Non. L’apprentissage automatique non validé serait contraire au principe « apprentissage uniquement à partir d’expériences validées ». Le tuning réel passe par le pipeline R15 gouverné.

**Peut-on réellement rendre un modèle local meilleur pour Kodepoia ?**  
Oui. Le pipeline SFT/LoRA/QLoRA existe, produit des adapters réels, les évalue et sait préparer un candidat Ollama. L’amélioration n’est considérée acceptable qu’après qualification comparative.

**Puis-je installer un modèle qui n’est pas dans la liste recommandée ?**  
Oui. Le gestionnaire accepte un nom/tag Ollama personnalisé. La liste recommandée sert seulement de point de départ.

**Supprimer un projet de “Projets récents” efface-t-il ses fichiers ?**  
Non. Cela retire uniquement l’entrée enregistrée dans les préférences KodeStudio.

**Pourquoi KodeStudio redémarre-t-il après un changement de projet ?**  
Pour garantir que tous les panneaux et services utilisent la même racine et qu’aucun outil ne continue accidentellement à travailler dans le projet précédent.

## 23. Où trouver de l’aide ?

Dans une build intégrant cette documentation : **Aide → Guide d’utilisation de Kodepoia**.

Le dépôt contient également :

- `README.md` pour l’installation, l’état courant et les commandes essentielles ;
- `docs/continuity/STATE.md` et `NEXT.md` pour la continuité de développement ;
- `docs/roadmap/` pour les plans historiques ;
- `docs/release/` pour les preuves de release et d’acceptance.

Pour un diagnostic reproductible, conserver le message d’erreur exact, l’action effectuée, la version de Kodepoia, la racine du projet concerné et, lorsqu’il s’agit d’IA locale, le nom/tag exact du modèle utilisé.
