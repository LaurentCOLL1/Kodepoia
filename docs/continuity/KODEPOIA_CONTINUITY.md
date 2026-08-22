# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R6 sont COMPLETE. Le planning R7 est ACCEPTED. R7.1, R7.2 et R7.3 sont COMPLETE ; R7.4 est NOT STARTED.** R7.1 a été accepté sur `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca` (R0 #959, Python Core #933 5/5, UI #900; PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`). R7.2 a été accepté sur `9101e686a32b24bb33a23d7ac578bf25570e115e` (R0 #964, Python Core #938 5/5, UI #905; PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`). R7.3 a été accepté sur `4efd2cb016e774fa3ef06590ffda377606d875e9` avec R0 #968 / `32586392901`, Python Core #942 / `32586392898` 5/5, Ubuntu full suite `369 passed / 3 skipped / 46 warnings`, UI Smoke #909 / `32586392883` SUCCESS; PR #64 merge `cde4f7fd727c6940c6a434f85fabc2ced27f04c5`; manual NONE. **La prochaine implémentation autorisée est R7.4 — GitHub research adapter.** Lire `docs/architecture/KODEPOIA_ARCHITECTURE.md`, `R6_STATUS.md`, `R6_INTEGRATED_ACCEPTANCE.json`, `R7_PLAN.md`, `R7_PLANNING_ACCEPTANCE.md`, `R7_STATUS.md`, `R7_1_DESIGN.md`, `R7_1_ACCEPTANCE.md`, `R7_2_DESIGN.md`, `R7_2_ACCEPTANCE.md`, `R7_3_DESIGN.md`, `R7_3_ACCEPTANCE.md` et ce fichier avant toute suite.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- `main` : source de vérité après chaque fusion acceptée.
- R1–R5 : COMPLETE.
- R6 : COMPLETE; les détails exacts de R6.1–R6.12 restent dans `docs/roadmap/R6_STATUS.md`, les `R6_X_ACCEPTANCE.md` et `R6_INTEGRATED_ACCEPTANCE.json`.
- R6.12 accepted head : `f57d1c43cfa12a8f9918b80065f4ffa3502046de`; PR #56 merge `e557979ef818d03bc7602a0b96644b0b5863a73e`; normalisation finale R6 PR #57.
- R7 planning : ACCEPTED — head `f86825ffd84c1c814afb5865be95b278c4291314`; R0 #955 / `32584324751`; Python Core #929 / `32584324757` 5/5; UI #896 / `32584324760`; PR #58 merge `9315d801f3a2d13a5441bd87babd2abeb9305995`; normalization #59 `7279412ae751bce739317763462c4a48d7832122`; manual NONE.
- R7.1 : COMPLETE — accepted head `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`; PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`; normalization #61 `69249993cf9a2a45c1d3f89f0540e6f37c882929`; manual NONE.
- R7.2 : COMPLETE — accepted head `9101e686a32b24bb33a23d7ac578bf25570e115e`; R0 #964 / `32585721455`; Python #938 / `32585721645` 5/5; UI #905 / `32585721536`; PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`; normalization #63 merge `0afdf8474a1d6f056c235f7d185ca468080fc966`; manual NONE.
- R7.3 : COMPLETE — accepted head `4efd2cb016e774fa3ef06590ffda377606d875e9`; R0 #968 / `32586392901`; Python #942 / `32586392898` 5/5; UI #909 / `32586392883`; PR #64 merge `cde4f7fd727c6940c6a434f85fabc2ced27f04c5`; manual NONE.
- R7.4–R7.11 : NOT STARTED; next = R7.4.
- R8–R16 : PENDING / NOT STARTED.

## R7 frozen planning structure

| ID | Title | Manual |
| --- | --- | --- |
| R7.1 | KodeResearch contracts + ResearchGuard hardening | NONE |
| R7.2 | Local + official documentation research | NONE |
| R7.3 | Governed Web fetch + extraction | NONE |
| R7.4 | GitHub research adapter | CONDITIONAL |
| R7.5 | Community/forums research normalization | NONE |
| R7.6 | YouTube metadata + transcript ingestion | CONDITIONAL |
| R7.7 | Local STT + frame extraction/analysis hooks | REQUIRED |
| R7.8 | Version-awareness + provenance/conflict model | NONE |
| R7.9 | Research cache + Context/Memory orchestration | NONE |
| R7.10 | CLI + KodeStudio Research UX | NONE |
| R7.11 | Adversarial hardening + R7 integrated acceptance | CONDITIONAL |

No subdivision may être ajoutée, supprimée, fusionnée, scindée ou renumérotée silencieusement. Toute modification de structure doit synchroniser `R7_PLAN.md` + continuité; un changement de fondation exige un ADR.

## R7 planning acceptance invariants

- Le plan exhaustif `R7_PLAN.md` a été fusionné avant toute implémentation R7.1.
- Accepted planning head : `f86825ffd84c1c814afb5865be95b278c4291314`.
- R0 #955, Python Core #929 5/5, UI Smoke #896 SUCCESS sur ce head exact.
- PR #58 fusionnée avec verrou exact-head en `9315d801f3a2d13a5441bd87babd2abeb9305995`.
- `docs/roadmap/R7_PLANNING_ACCEPTANCE.md` est la preuve durable.

## R7.1 accepted research-contract baseline

- Toute donnée externe de recherche est une donnée, jamais une instruction agentique.
- `ResearchGuard` reste l'unique frontière de confiance du contenu et possède une version de guard déterministe.
- `guarded` signifie inspecté/enveloppé, pas autorisé pour changer outils/politiques.
- Source classes : local, official_docs, web, github, community, youtube.
- Status/freshness sont explicites; `READY` décrit la disponibilité, pas la vérité ou une conformité.
- IDs request/source/artifact/citation/finding et digests de report sont SHA-256 canoniques recalculés au round-trip.
- Hash du contenu et preuves de guard sont recalculés; les altérations échouent fermé.
- Les faits source exigent des citations; les reports rejettent les références à des artifacts absents.
- Persistance confinée sous `.kodepoia/research/` via `WorkspaceBoundary` avec remplacements atomiques.
- R7.1 n'a ajouté aucun réseau/processus/UI.

## R7.2 accepted local/official-document baseline

- R7.2 reste offline-first.
- Formats : UTF-8 `.txt`, Markdown, JSON, YAML; invalides/non supportés => `UNAVAILABLE` explicite.
- Les fichiers projet restent confinés par `WorkspaceBoundary`; les snapshots officiels utilisent une seconde boundary ancrée sur leur subtree.
- Les manifestes de docs officielles sont versionnés; leurs URL HTTPS sont de la provenance, pas une permission réseau.
- Les racines absolues/traversals sont rejetées de façon cohérente avec les syntaxes native, POSIX et Windows.
- Les chunks conservent les lignes 1-based et headings Markdown; les citations pointent vers l'artifact immuable.
- Le cache content-addressed conserve le timestamp de récupération original.
- Version exacte = CURRENT; mismatch = STALE; absence de relation = UNKNOWN; l'inférence riche reste R7.8.
- Le head candidat `61eb6fbaf73066274249b3e490695bb0d4ff122c` est rejeté : Python Core #937 avait trouvé un défaut Windows de chemin POSIX absolu. Le head accepté `9101e686...` corrige ce cas.

## R7.3 accepted governed-Web baseline

- Le modèle ne fournit qu'une URL de recherche structurée; aucune méthode HTTP, body, headers, proxy, cookie ou login arbitraire.
- HTTP(S) uniquement; fragments retirés; credentials URL, hostnames locaux et ports hors allowlist rejetés.
- **Toutes** les réponses DNS doivent être globalement routables; loopback/private/link-local/non-global => blocage.
- Le transport de production se connecte à l'IP déjà validée et conserve le hostname original pour TLS, évitant une re-résolution non contrôlée entre policy et socket.
- Chaque redirect est revalidé avant son envoi et la profondeur est bornée.
- `KodeGuardian` + `Capability.NETWORK` sont requis avant toute activité socket réelle.
- GET-only et headers fixes; `Accept-Encoding: identity`; aucune exécution du contenu téléchargé.
- Timeout, Content-Length, octets réels, MIME, charset et encoding sont bornés; pas de retry caché.
- `FixtureWebTransport` fournit un transport déterministe sans Internet pour CI.
- L'extracteur conserve texte visible/titre/headings/auteur/dates/canonical/robots lorsque ces éléments sont prouvés; script/style/noscript/template ne deviennent pas du contenu visible.
- Une canonical metadata vers une cible interdite ne pilote aucun fetch; elle est marquée rejetée.
- ETag et Last-Modified sont uniquement de l'évidence; ils ne fabriquent jamais CURRENT.
- Tout texte extrait devient `ResearchArtifact` et repasse par le `ResearchGuard` R7.1.
- Accepted head `4efd2cb016e774fa3ef06590ffda377606d875e9`; suite Ubuntu 369 passed / 3 skipped / 46 warnings; R0/Python/UI SUCCESS; manual NONE.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste un futur candidat KodeDeepCoder.
- Le Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## Permanent architecture/security boundaries

Préserver sans réinterprétation :

- `WorkspaceBoundary` et rejet des escapes/symlinks hors projet;
- `ProcessSandbox` + global KillSwitch;
- Guardian + `PermissionSet`;
- structured Tool APIs; jamais de commande/argv/cwd/host arbitraire fournie par le modèle;
- SafeChange/Backup/Recovery/Audit lorsque requis;
- secrets OS-backed + redaction et jamais dans prompts/caches;
- Health/Budget/DataGovernance et schémas versionnés;
- exact-head acceptance;
- N/A/UNKNOWN/UNAVAILABLE/BLOCKED/STALE explicites; silence ou absence d'évidence ne fabrique jamais PASS;
- comportement platform-aware;
- ADR obligatoire pour toute modification des fondations de l'architecture v1.0 gelée.

R7 ajoute sans modifier ces fondations : Web/GitHub/forums/YouTube/transcripts restent des données externes non fiables; le `ResearchGuard` reste la frontière unique de confiance; aucun réseau/processus arbitraire n'est exposé au modèle.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance : `19 PASS / 0 FAIL / 19`.
- `ProcessSandbox.run()` draine stdout/stderr via `communicate(timeout=...)`.
- Services longs : exécution background gouvernée sans PIPEs non lus.
- Une preuve real-render REQUIRED ne peut pas être remplacée par headless/dummy.
- Godot LSP/DAP/debug reste loopback-only.

## R6 accepted quality/governance baseline

R6 fournit les fondations acceptées Health, Budget, Tests/Regression, VisualQA, Accessibility, Localization, TechnicalDebt, CI/Build, AppSecurity, Privacy, License/BOM et major-patch/rollback. `docs/roadmap/R6_INTEGRATED_ACCEPTANCE.json` agrège R6.1–R6.12 et lie chaque acceptance source par SHA-256. `tests/test_r6_12_repository_integration.py` recalcule les invariants.

Principes R6 à ne pas régresser :

- état non mesuré = UNKNOWN; N/A explicite et neutre selon contrat;
- champs/digests dérivés sont recalculables et non crus aveuglément au round-trip;
- preuves critiques liées à leurs SHAs/sources;
- gates REQUIRED/CONDITIONAL explicites;
- aucune conclusion juridique/certification universelle inventée;
- major patch : classification déterministe, exact base/head SHAs, matrice de validation, rollback rehearsal, backup/recovery/audit, fail-closed si preuve requise absente/FAIL/SKIP/CANCELLED/N/A;
- aucune rehearsal destructive sur projet réel.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` impose à chaque nouvelle phase majeure à partir de R7 un `RX_PLAN.md` exhaustif fusionné **avant RX.1**, avec subdivisions, dépendances, architecture, implementation, deliverables, acceptance, evidence, rollback, risks et statut manuel.

## Next action

**R7.1–R7.3 sont COMPLETE. R7.4 n'est pas commencé.** Après fusion de la normalisation R7.3 (`R7_3_ACCEPTANCE.md`, `R7_STATUS.md`, continuité), démarrer **R7.4 — GitHub research adapter** depuis le `main` normalisé. R7.4 doit rester strictement read-only et typé : repository metadata, files/blobs, commits, releases/tags, issues, PRs et comments nécessaires à la recherche; pagination/rate-limit state explicites; public unauthenticated par défaut; optional auth uniquement via référence de secret résolue hors contexte modèle; préférence aux locators immuables commit-SHA; README/issue/PR/comment repassés par `ResearchGuard`; aucune écriture GitHub, aucune query GraphQL arbitraire. Manual R7.4 = **CONDITIONAL**, déclenché uniquement si une acceptance autoritative exige réellement une capability privée/authentifiée non testable en CI.