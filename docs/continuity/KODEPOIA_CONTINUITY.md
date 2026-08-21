# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 21 août 2026**

## Prompt de reprise

> Nous développons **Kodepoia**. Architecture v1.0 gelée depuis le 21 août 2026. R1, R2 et R3 sont COMPLETE. **R4 — KodeCode est IN PROGRESS**. R4.1 et R4.2 sont ACCEPTED AND MERGED. **R4.3 LSP est IMPLEMENTED / PENDING CI ACCEPTANCE** sur `agent/r4-3-lsp`. Lire Architecture, Decisions, Roadmap, `R4_STATUS.md` et ce fichier avant reprise. Toute modification de fondation exige un ADR.

## Source de vérité

- Dépôt : `LaurentCOLL1/Kodepoia`.
- Visibilité GitHub : **PUBLIC volontairement** ; ne pas tenter de la rendre privée automatiquement.
- `main` avant R4.3 : `1ec80dcef878a1bac4affb062834c9cc8e75ad7b`.
- Branche active : `agent/r4-3-lsp`.
- R1/R2/R3 : COMPLETE.
- R4 : IN PROGRESS.
- R4.1 : ACCEPTED AND MERGED.
- R4.2 : ACCEPTED AND MERGED.
- R4.3 : IMPLEMENTED / PENDING CI ACCEPTANCE.
- R4.4/R4.5/R4.6 : NOT STARTED.

## Modèles R3 acceptés

- KodeFast → `granite4.1:3b`.
- KodeCore → `gpt-oss:20b`.
- KodeCoder → `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste candidat futur KodeDeepCoder.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## R4.1 — ACCEPTED AND MERGED

PR #11, merge `91f3d77cc375021efcb24172b2859a27748843b8`.
Fondation : WorkspaceBoundary, safe files/search/patch, Git worktrees via ProcessSandbox, Tool API structurée.

## R4.2 — ACCEPTED AND MERGED

PR #13, merge `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.
Tree-sitter : runtime 0.26.x, Python/JavaScript/TypeScript/TSX, registry provider-based, ABI checks, tolerant/incremental parsing, GDScript provider optionnel.

## R4.3 — IMPLEMENTED / PENDING CI ACCEPTANCE

Branche : `agent/r4-3-lsp`.

Implémenté :
- framing commun `Content-Length` + UTF-8 JSON avec limites ;
- `FramedMessageChannel` avec reader thread et timeout ;
- `ProcessSandbox.spawn_piped()` et `ManagedProcess` pour processus stdio persistants sous allowlist/cwd confinement/global kill switch ;
- `LanguageServerSpec` et registry explicites ;
- lifecycle LSP initialize/initialized/shutdown/exit ;
- document symbols, definition, references, publishDiagnostics ;
- gestion baseline des requêtes serveur vers client ;
- didOpen et URI confinées au workspace ;
- Tool API structurée LSP ;
- tests framing, lifecycle factice et vrai processus stdio sandboxé.

Sécurité : aucun argv arbitraire exposé au modèle, aucun transport réseau LSP, seuls les serveurs pré-enregistrés peuvent être lancés, timeout et taille des messages bornés.

Ne pas marquer R4.3 ACCEPTED tant que le head exact n'a pas Repository Guard + Python Core Ubuntu/Windows + UI Smoke en SUCCESS.

## Suite R4

- R4.4 DAP : NEXT après acceptation/merge R4.3.
- R4.5 Graphs : après R4.4.
- R4.6 Orchestration + final R4 acceptance : après R4.5.

## Règles permanentes

Mettre à jour ce fichier dans le même cycle à tout changement de phase/PR/acceptation/prérequis. Ne jamais déclarer COMPLETE sur CI partielle. Ne pas contourner Guardian/Sandbox/Secrets/Health/Budget. Ne pas introduire d'accès système direct hors Tool API. La visibilité publique actuelle du dépôt est intentionnelle.
