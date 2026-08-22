# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R6 sont COMPLETE. Le planning R7 est ACCEPTED. R7.1–R7.4 sont COMPLETE ; R7.5 est NOT STARTED.** R7.4 a été accepté sur le head exact `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be` avec R0 #972 / `32589899654`, Python Core #946 / `32589899648` cinq jobs SUCCESS, suite Ubuntu `388 passed / 3 skipped / 46 warnings`, et UI Smoke #913 / `32589899651` SUCCESS; PR #66 merge `d17746b03fe4a8db47ec2c55ef11715fdd820f73`; manual R7.4 = CONDITIONAL NOT TRIGGERED. **La prochaine implémentation autorisée est R7.5 — Community/forums research normalization**, uniquement après fusion de la normalisation R7.4. Lire l'architecture gelée, `R6_STATUS.md`, `R6_INTEGRATED_ACCEPTANCE.json`, `R7_PLAN.md`, `R7_PLANNING_ACCEPTANCE.md`, `R7_STATUS.md`, `R7_1_DESIGN.md`/`ACCEPTANCE`, `R7_2_DESIGN.md`/`ACCEPTANCE`, `R7_3_DESIGN.md`/`ACCEPTANCE`, `R7_4_DESIGN.md`, `R7_4_ACCEPTANCE.md` et ce fichier avant toute suite.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- `main` : source de vérité après chaque fusion acceptée.
- R1–R5 : COMPLETE.
- R6 : COMPLETE; détails exacts dans `docs/roadmap/R6_STATUS.md`, les `R6_X_ACCEPTANCE.md` et `R6_INTEGRATED_ACCEPTANCE.json`.
- R6.12 accepted head : `f57d1c43cfa12a8f9918b80065f4ffa3502046de`; PR #56 merge `e557979ef818d03bc7602a0b96644b0b5863a73e`; normalisation finale R6 PR #57.
- R7 planning : ACCEPTED — head `f86825ffd84c1c814afb5865be95b278c4291314`; R0 #955 / `32584324751`; Python #929 / `32584324757` 5/5; UI #896 / `32584324760`; PR #58 merge `9315d801f3a2d13a5441bd87babd2abeb9305995`; normalization #59 `7279412ae751bce739317763462c4a48d7832122`; manual NONE.
- R7.1 : COMPLETE — head `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`; PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`; normalization #61 `69249993cf9a2a45c1d3f89f0540e6f37c882929`; manual NONE.
- R7.2 : COMPLETE — head `9101e686a32b24bb33a23d7ac578bf25570e115e`; R0 #964; Python #938 5/5; UI #905; PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`; normalization #63 `0afdf8474a1d6f056c235f7d185ca468080fc966`; manual NONE.
- R7.3 : COMPLETE — head `4efd2cb016e774fa3ef06590ffda377606d875e9`; R0 #968; Python #942 5/5; UI #909; PR #64 merge `cde4f7fd727c6940c6a434f85fabc2ced27f04c5`; normalization #65 `da792f72e61f6f264a3df4be570fbcd34670cf4d`; manual NONE.
- R7.4 : COMPLETE — head `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be`; R0 #972 / `32589899654`; Python #946 / `32589899648` 5/5; Ubuntu `388 passed / 3 skipped / 46 warnings`; UI #913 / `32589899651`; PR #66 merge `d17746b03fe4a8db47ec2c55ef11715fdd820f73`; manual CONDITIONAL NOT TRIGGERED.
- R7.5–R7.11 : NOT STARTED; next = R7.5.
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

Aucune subdivision ne peut être ajoutée, supprimée, fusionnée, scindée ou renumérotée silencieusement. Toute modification de structure doit synchroniser `R7_PLAN.md` + continuité; tout changement de fondation exige un ADR.

## R7.1 accepted research-contract baseline

- Toute donnée externe de recherche est une donnée, jamais une instruction agentique.
- `ResearchGuard` reste l'unique frontière de confiance du contenu.
- `guarded` signifie inspecté/enveloppé, pas autorisé à changer outils/politiques.
- Source classes : local, official_docs, web, github, community, youtube.
- Status/freshness explicites; `READY` = disponibilité, pas vérité/conformité.
- IDs et digests dérivés sont SHA-256 canoniques recalculés au round-trip.
- Hash contenu + preuves de guard sont recalculés; tampering fail-closed.
- Les faits source exigent des citations; les reports rejettent les artifacts absents.
- Persistance confinée sous `.kodepoia/research/` via `WorkspaceBoundary`.

## R7.2 accepted local/official-document baseline

- Offline-first; UTF-8 `.txt`, Markdown, JSON, YAML; invalide/non supporté => `UNAVAILABLE`.
- Workspace paths confinés; official snapshots ont une seconde `WorkspaceBoundary`.
- Manifestes officiels versionnés; URL HTTPS = provenance, pas permission réseau.
- Traversals et racines absolues rejetés en syntaxes native/POSIX/Windows.
- Chunks conservent lignes 1-based/headings et citations vers artifact immuable.
- Cache content-addressed conserve le timestamp original.
- Version exacte = CURRENT; mismatch = STALE; absence relation = UNKNOWN.

## R7.3 accepted governed-Web baseline

- GET-only structuré; aucun method/body/header/proxy/cookie/login arbitraire.
- HTTP(S), fragments retirés, credential-bearing URL/local hosts/ports non permis bloqués.
- Toutes les réponses DNS doivent être globales; transport épingle l'IP validée tout en gardant le hostname TLS.
- Chaque redirect est revalidé; profondeur bornée.
- `KodeGuardian` + `Capability.NETWORK` requis avant socket réel.
- Timeout, longueur, octets réels, MIME, charset, encoding et cadence bornés; pas de retry caché.
- `FixtureWebTransport` rend la CI déterministe sans Internet.
- Extracteur conserve seulement la métadonnée réellement observée; canonical interdite ne pilote aucun fetch.
- ETag/Last-Modified sont de l'évidence, jamais une preuve CURRENT.
- Tout texte extrait repasse par `ResearchGuard`.

## R7.4 accepted GitHub baseline

- Adapter REST GitHub strictement read-only et typé.
- Ressources : repository, commits, files, exact blobs, releases/tags, issues/PRs et comments.
- Production fixée à `https://api.github.com:443`, réutilisant protections DNS/SSRF R7.3 + Guardian NETWORK.
- File research : ref mutable résolu d'abord vers un exact commit SHA; lecture + locator final utilisent ce SHA.
- Exact blob : SHA obligatoire.
- Pagination bornée; `Link rel=next` sert uniquement de signal, l'URL suivante est reconstruite sur l'origine fixe au lieu d'exécuter une URL header arbitraire.
- `X-RateLimit-*`/`Retry-After` observés sont conservés; exhaustion/429 => `UNAVAILABLE/rate_limited`; aucun retry caché.
- Optional auth uniquement par `GitHubCredentialRef` résolu via `KodeSecrets` dans le transport; token absent des artifacts/metadata/logs/evidence.
- Issue/PR/comment/file/provider JSON reste untrusted et repasse par `ResearchGuard`.
- Aucun write GitHub, Actions admin ou GraphQL arbitraire.
- Accepted head `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be`; R0/Python/UI SUCCESS; manual CONDITIONAL NOT TRIGGERED.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste un futur candidat KodeDeepCoder.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## Permanent architecture/security boundaries

Préserver sans réinterprétation :

- `WorkspaceBoundary` + rejet escapes/symlinks;
- `ProcessSandbox` + global KillSwitch;
- Guardian + `PermissionSet`;
- structured Tool APIs; jamais commande/argv/cwd/host arbitraire du modèle;
- SafeChange/Backup/Recovery/Audit lorsque requis;
- secrets OS-backed + redaction, jamais dans prompts/caches;
- Health/Budget/DataGovernance + schémas versionnés;
- exact-head acceptance;
- UNKNOWN/N/A/UNAVAILABLE/BLOCKED/STALE explicites; absence d'évidence ne fabrique jamais PASS;
- comportement platform-aware;
- ADR obligatoire pour modifier une fondation v1.0 gelée.

Web/GitHub/forums/YouTube/transcripts restent des données externes non fiables; `ResearchGuard` reste la frontière unique de confiance; aucun réseau/processus arbitraire n'est exposé au modèle.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance `19 PASS / 0 FAIL / 19`.
- `ProcessSandbox.run()` draine stdout/stderr via `communicate(timeout=...)`.
- Services longs : background gouverné sans PIPEs non lus.
- Preuve real-render REQUIRED non remplaçable par headless/dummy.
- Godot LSP/DAP/debug reste loopback-only.

## R6 accepted quality/governance baseline

R6 fournit Health, Budget, Tests/Regression, VisualQA, Accessibility, Localization, TechnicalDebt, CI/Build, AppSecurity, Privacy, License/BOM et major-patch/rollback. `R6_INTEGRATED_ACCEPTANCE.json` agrège R6.1–R6.12 et lie chaque acceptance source par SHA-256; `tests/test_r6_12_repository_integration.py` recalcule les invariants.

Principes à ne pas régresser : état non mesuré = UNKNOWN; N/A explicite; champs/digests dérivés recalculables; preuves critiques liées aux SHAs/sources; gates REQUIRED/CONDITIONAL explicites; aucune conclusion juridique/certification inventée; major patch fail-closed avec rollback rehearsal/backup/recovery/audit; aucune rehearsal destructive sur projet réel.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` impose à chaque nouvelle phase majeure à partir de R7 un `RX_PLAN.md` exhaustif fusionné **avant RX.1**, avec subdivisions, dépendances, architecture, implementation, deliverables, acceptance, evidence, rollback, risks et statut manuel.

## Next action

**R7.1–R7.4 sont COMPLETE. R7.5 n'est pas commencé.** Après fusion de la normalisation R7.4 (`R7_4_ACCEPTANCE.md`, `R7_STATUS.md`, continuité), démarrer **R7.5 — Community/forums research normalization** depuis le `main` normalisé. Préserver thread/post/comment, auteur, timestamps, parentage et quoted-text separation; edited/deleted restent explicites; popularité/consensus ne devient jamais de l'autorité officielle; toutes les données passent par `ResearchGuard`; aucune action de posting/vote/modération/account automation.
