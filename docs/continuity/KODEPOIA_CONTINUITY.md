# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R6 sont COMPLETE. Le planning R7 est ACCEPTED. R7.1 et R7.2 sont COMPLETE ; R7.3 est NOT STARTED.** Le planning head exact R7 `f86825ffd84c1c814afb5865be95b278c4291314` a obtenu R0 #955 / `32584324751`, Python Core #929 / `32584324757` 5/5 et UI Smoke #896 / `32584324760` SUCCESS, puis PR #58 a été fusionnée avec verrou exact-head en `9315d801f3a2d13a5441bd87babd2abeb9305995` et normalisée par PR #59 merge `7279412ae751bce739317763462c4a48d7832122`. R7.1 a été accepté sur `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca` avec R0 #959, Python Core #933 5/5 et UI Smoke #900 SUCCESS; PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`; manual NONE. R7.2 a été accepté sur `9101e686a32b24bb33a23d7ac578bf25570e115e` avec R0 #964 / `32585721455`, Python Core #938 / `32585721645` 5/5 et UI Smoke #905 / `32585721536` SUCCESS; PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`; manual NONE. Le head précédent R7.2 `61eb6fbaf73066274249b3e490695bb0d4ff122c` a été rejeté car Python Core #937 a trouvé un unique défaut Windows de validation d'un chemin POSIX absolu; le head accepté valide nativement les syntaxes native/POSIX/Windows. **La prochaine implémentation autorisée est R7.3 — Governed Web fetch + extraction.** Lire l'architecture gelée, `R6_PLAN.md`, `R6_STATUS.md`, `R6_12_DESIGN.md`, `R6_12_ACCEPTANCE.md`, `R6_INTEGRATED_ACCEPTANCE.json`, `R7_PLAN.md`, `R7_PLANNING_ACCEPTANCE.md`, `R7_STATUS.md`, `R7_1_DESIGN.md`, `R7_1_ACCEPTANCE.md`, `R7_2_DESIGN.md`, `R7_2_ACCEPTANCE.md` et ce fichier avant toute suite.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- `main` : source de vérité après chaque fusion acceptée.
- R1–R5 : COMPLETE.
- R6 : COMPLETE — effectif avec la fusion de la normalisation finale PR #57.
- R6 plan : ACCEPTED / EXECUTED — PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`; normalization initiale #38 `e96e7c3b168975869c911f880044b7ef8e322157`.
- R6.1 : COMPLETE — accepted head `802de4ba3110ace657c4e16306a0ca29850ce2bd`; PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`; manual NONE.
- R6.2 : COMPLETE — accepted head `8ac3772e98c70260c320519a214bb25b6cedbb38`; PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`; manual NONE.
- R6.3 : COMPLETE — accepted head `7150237c263dd3ac96af4662d74909e05f3cf991`; PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`; manual NONE.
- R6.4 : COMPLETE — accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; manual REQUIRED SATISFIED; real-render `8 PASS / 0 FAIL / 8`.
- R6.5 : COMPLETE — accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; manual REQUIRED SATISFIED; accessibility `15 PASS / 0 FAIL / 15`.
- R6.6 : COMPLETE — accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`; manual NONE.
- R6.7 : COMPLETE — accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`; manual NONE.
- R6.8 : COMPLETE — accepted head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; normalization #48/#49; manual CONDITIONAL NOT TRIGGERED.
- R6.9 : COMPLETE — accepted head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`; PR #50 merge `f5c135edf0be464a02b4b46d67c14e665f236009`; normalization #51; manual NONE.
- R6.10 : COMPLETE — accepted head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`; PR #52 merge `cefc60266cb191cf0ee5a099e0d8923a2f14745a`; normalization #53 `36524978a963d8c759d36902bc1ab00989da0549`; manual NONE.
- R6.11 : COMPLETE — accepted head `d0590ed3eda663ad713fc36d962c8dac1df109eb`; PR #54 merge `248b1331fe2b26229b932c36aefb83c70065c52a`; normalization #55 merge `264f129d3e32e38c8867871fc4dcf9a03ef2b5b9`; manual CONDITIONAL NOT TRIGGERED.
- R6.12 : COMPLETE — accepted head `f57d1c43cfa12a8f9918b80065f4ffa3502046de`; R0 #934, Python Core #908 5/5, UI #875 SUCCESS; PR #56 merge `e557979ef818d03bc7602a0b96644b0b5863a73e`; manual CONDITIONAL NOT TRIGGERED.
- R7 planning : ACCEPTED — accepted planning head `f86825ffd84c1c814afb5865be95b278c4291314`; R0 #955 / `32584324751`; Python Core #929 / `32584324757` 5/5; UI Smoke #896 / `32584324760`; PR #58 merge `9315d801f3a2d13a5441bd87babd2abeb9305995`; planning normalization PR #59 merge `7279412ae751bce739317763462c4a48d7832122`; manual NONE.
- R7 plan : `docs/roadmap/R7_PLAN.md` — structure R7.1–R7.11 frozen.
- R7.1 : COMPLETE — accepted head `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`; R0 #959 / `32584754313`; Python Core #933 / `32584754311` 5/5; UI Smoke #900 / `32584754325`; PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`; manual NONE.
- R7.2 : COMPLETE — accepted head `9101e686a32b24bb33a23d7ac578bf25570e115e`; R0 #964 / `32585721455`; Python Core #938 / `32585721645` 5/5; UI Smoke #905 / `32585721536`; PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`; manual NONE.
- R7.3–R7.11 : NOT STARTED; next = R7.3.
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

No subdivision may be silently added, removed, merged, split or renumbered. Any scope change must synchronize `R7_PLAN.md` + continuity; an architecture/foundation change requires un ADR.

## R7 planning acceptance invariants

- `R7_PLAN.md` was present before any R7.1 source implementation.
- Accepted planning head: `f86825ffd84c1c814afb5865be95b278c4291314`.
- R0 Repository Guard #955 / `32584324751`: SUCCESS on Ubuntu + Windows.
- Python Core #929 / `32584324757`: SUCCESS, 5/5 jobs.
- KodeStudio UI Smoke #896 / `32584324760`: SUCCESS on Windows.
- Planning PR #58 merged with exact-head lock as `9315d801f3a2d13a5441bd87babd2abeb9305995`.
- Planning normalization PR #59 merged as `7279412ae751bce739317763462c4a48d7832122`.
- Manual planning gate: NONE.
- `docs/roadmap/R7_PLANNING_ACCEPTANCE.md` is the durable planning evidence record.

## R7.1 accepted research-contract baseline

- External research material is data, never agent instruction.
- `ResearchGuard` remains the single content trust boundary and carries deterministic guard version 1.
- `guarded` means inspected/wrapped, not trusted for tool authorization or policy changes.
- Source classes are local, official_docs, web, github, community and youtube.
- Research status/freshness remains explicit; `ready` is availability, not factual correctness or compliance PASS.
- Request/source/artifact/citation/finding IDs and report digests are canonical SHA-256 values recomputed on round-trip.
- Artifact content SHA-256 and serialized guard evidence are recomputed; tampering fails closed.
- Source facts require citations; reports reject references to absent artifacts.
- Persistent research state is confined under `.kodepoia/research/` through `WorkspaceBoundary` with atomic replacement writes.
- R7.1 introduced no live network, provider, subprocess or UI execution surface.
- Accepted implementation head `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`; PR #60 merge `86a5453b2fd8ce414e73277199fdd55bd210aeba`; manual NONE.
- Hosted authoritative suite on Ubuntu: 310 passed / 3 skipped / 46 warnings; workflow successful.

## R7.2 accepted local/official-document baseline

- R7.2 is offline-first: no general Web transport is present.
- Supported local evidence formats are UTF-8 `.txt`, `.md`/`.markdown`, `.json`, `.yaml`/`.yml`; malformed/unsupported inputs return explicit `UNAVAILABLE`.
- Local project paths remain confined by `WorkspaceBoundary`; official snapshots add a second `WorkspaceBoundary` rooted at the configured snapshot subtree.
- Official-document manifests are versioned configuration/provenance records. Canonical HTTPS bases do not grant network permission or perform retrieval.
- Snapshot-root validation rejects parent traversal and absolute roots using native, POSIX and Windows path semantics consistently across hosts.
- Stable local locators do not persist absolute host paths.
- `DocumentChunk` preserves exact 1-based line anchors and Markdown heading labels; citations point back to the immutable research artifact/source locator.
- Cache reuse is content-addressed and preserves original retrieval timestamps instead of manufacturing freshness.
- Exact source-version match = CURRENT; mismatch = STALE; missing version relation = UNKNOWN. Richer version inference remains R7.8.
- Accepted implementation head `9101e686a32b24bb33a23d7ac578bf25570e115e`; PR #62 merge `25741ab9c39300483b62eb2cc07b9d2c9fcfb20c`; R0 #964, Python Core #938 5/5 and UI Smoke #905 SUCCESS; manual NONE.
- Preceding head `61eb6fbaf73066274249b3e490695bb0d4ff122c` is explicitly rejected acceptance evidence, not an accepted implementation head.

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
- structured Tool APIs, jamais une commande/argv/cwd/host arbitraire fournie par le modèle;
- SafeChange avant mutations sensibles lorsque requis;
- AuditLog à chaîne de hashes;
- Secrets OS-backed + redaction;
- Health/Budget/DataGovernance et schemas versionnés;
- exact-head acceptance;
- N/A/UNKNOWN explicites : silence, skip ou non-applicabilité ne doivent jamais fabriquer PASS;
- comportement platform-aware : une plateforme non ciblée n'impose pas ses dépendances/gates;
- ADR obligatoire pour tout changement de fondation de l'architecture v1.0 gelée.

R7 ajoute sans modifier la fondation : tout contenu Web/GitHub/forums/YouTube/transcript est une donnée externe non fiable, jamais une instruction agentique; le `ResearchGuard` existant reste la frontière unique de confiance; aucun nouvel accès réseau/processus arbitraire ne doit être exposé au modèle.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance `19 PASS / 0 FAIL / 19`.
- `ProcessSandbox.run()` draine stdout/stderr via `communicate(timeout=...)`.
- Les services longs utilisent l'exécution background gouvernée sans PIPEs non lus.
- Une preuve real-render requise ne peut pas être remplacée par headless/dummy.
- Godot LSP/DAP/debug reste loopback-only; aucun host/program/cwd arbitraire depuis le modèle.

## R6 accepted quality/governance baseline

R6 fournit désormais les fondations acceptées Health, Budget, Tests/Regression, VisualQA, Accessibility, Localization, TechnicalDebt, CI/Build, AppSecurity, Privacy, License/BOM et le major-patch validation/rollback gate. Les preuves persistantes restent confinées sous `.kodepoia/` via `WorkspaceBoundary` quand le composant le requiert.

Principes transversaux à ne pas régresser :

- un état non mesuré reste UNKNOWN; N/A reste explicite et neutre selon le contrat du composant;
- les rapports dérivés sont recalculables et leurs champs/hash ne sont pas simplement crus lors du round-trip;
- les preuves critiques sont liées aux sources/SHAs appropriés;
- les gates manuels REQUIRED/CONDITIONAL restent explicites et ne sont jamais implicitement satisfaits;
- les builds packages R6.8 restent liés au SHA source exact;
- aucune conclusion juridique, certification universelle ou conformité officielle n'est inventée par AppSecurity/Privacy/License/BOM.

## R6.11 accepted BOM/license contract

- BOM components project/package/asset; resolved/unresolved/N/A; exact version uniquement si resolved.
- N/A exige N/A integrity, ne contribue pas au score/applicable/license decision/SPDX package; all-N/A = UNKNOWN; R6.3 = SKIP.
- Integrity : recorded/mismatch/unknown/N/A; recorded ne signifie pas independently verified; mismatch bloque.
- Declared et concluded license evidence restent distincts; NOASSERTION/NONE explicites avec provenance/rationale.
- Un custom license text hash ne lie qu'un `LicenseRef-*` autonome.
- `KodeBOM.from_pyproject()` collecte build/runtime/all optional groups déterministiquement; les version ranges restent unresolved.
- LicensePolicy exact-expression n'a pas de default ALLOW silencieux; seul DENY bloque.
- SPDX 3.0 family reste la baseline R6; 3.0.1 est la référence patch-level; CycloneDX 1.7 contexte optionnel uniquement.

## R6.12 accepted major-patch / rollback contract

1. classification major/minor déterministe depuis path/domain/operation/risk/platform, jamais opinion LLM libre;
2. rapport patch lié aux exact base/head SHAs;
3. matrice de validation requise sélectionnée par domaines/plateformes et réutilisant les gates R6 existants;
4. major ajoute toujours rollback, regression et technical-debt;
5. required fail/missing/skip/cancelled/N/A échoue fermé; WARN reste WARN;
6. toute preuve mesurée PASS/WARN/FAIL exige `source_sha` + SHA-256; le report exige la correspondance au head exact;
7. major PASS impossible sans stratégie rollback explicite avec snapshot/audit/verification et rehearsal PASS;
8. rehearsal uniquement sur fixture marquée `.kodepoia-r6-rollback-fixture`, avec rejet parent/absolute/Windows-drive et overlap support tree;
9. réutiliser `SafeChangeManager`, `BackupManager`, `RecoveryJournal`, `AuditLog`, `WorkspaceBoundary`; aucun second rollback engine;
10. file-set/content hashes avant/après identiques, backup vérifié, checkpoint cleared, AuditLog chain valide;
11. patch/integration reports versionnés, schema-bound et SHA-256 anti-tamper;
12. PASS subdivision exige accepted head; R6.12 accepted head = integrated report `source_sha`;
13. aucun shell/argv/cwd/host/network arbitraire et aucune rehearsal destructive sur projet réel.

## Final integrated R6 acceptance

`docs/roadmap/R6_INTEGRATED_ACCEPTANCE.json` est la preuve machine finale de fermeture de R6. Elle contient R6.1–R6.12 avec :

- `status=pass` pour chaque subdivision;
- accepted implementation head;
- `manual_satisfied=true` après REQUIRED satisfait ou CONDITIONAL non déclenché;
- source `docs/roadmap/R6_X_ACCEPTANCE.md`;
- SHA-256 exact des octets de chaque source;
- R6.12 accepted head égal au `source_sha` du rapport;
- statut global PASS, aucun blocker, digest canonique anti-tamper.

`tests/test_r6_12_repository_integration.py` recalcule et valide ces invariants dès que le fichier est présent. Le rapport ne remplace pas les preuves détaillées; il les agrège et les lie.

## External reference context

- SLSA v1.2 reste uniquement un contexte de provenance/source traceability; Kodepoia ne revendique aucun niveau SLSA.
- CycloneDX 1.7 reste un contexte BOM stable optionnel; il ne remplace pas la baseline SPDX déjà acceptée.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` impose à toute nouvelle phase majeure à partir de R7 de créer et fusionner un `RX_PLAN.md` exhaustif **avant RX.1**. Le plan doit énumérer toutes les subdivisions RX.N, dépendances, architecture, implementation, deliverables, acceptance, evidence, rollback, risks et statut manuel `NONE` / `REQUIRED` / `CONDITIONAL`. Toute modification de structure doit être synchronisée dans le plan + continuité et utiliser un ADR si elle change une fondation.

## Next action

**R7.1 et R7.2 sont COMPLETE. R7.3 n'est pas commencé.** Après fusion de la normalisation R7.2 qui ajoute `R7_2_ACCEPTANCE.md`, met à jour `R7_STATUS.md` et cette continuité, la prochaine action autorisée est de démarrer **R7.3 — Governed Web fetch + extraction** depuis le `main` normalisé. R7.3 doit ajouter uniquement un transport HTTP(S) en lecture seule, typé et borné, avec protections SSRF/redirect/timeout/size/MIME/rate-limit, faux transport déterministe pour CI et passage de tout texte externe extrait par le `ResearchGuard` existant.