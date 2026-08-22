# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R6 sont COMPLETE après fusion de la normalisation finale PR #57. R7 est NOT STARTED.** R6.12 — Major-patch validation + rollback gate and R6 integration acceptance — a été accepté sur le head exact `f57d1c43cfa12a8f9918b80065f4ffa3502046de`, avec R0 #934 / `32580881005`, Python Core #908 / `32580881007` cinq jobs et UI Smoke #875 / `32580881010` SUCCESS, puis PR #56 fusionnée avec verrou exact-head en `e557979ef818d03bc7602a0b96644b0b5863a73e`. La normalisation finale #57 contient `R6_INTEGRATED_ACCEPTANCE.json`, lié par SHA-256 aux 12 documents `R6_X_ACCEPTANCE.md`; le test repository-integration exige 12/12 PASS, accepted heads, manual satisfaction et `R6.12 accepted_head == source_sha`. Manual R6.12 = CONDITIONAL NOT TRIGGERED. **Ne pas commencer R7.1 directement : créer et fusionner d'abord `docs/roadmap/R7_PLAN.md` exhaustif, puis seulement démarrer R7.1.** Lire l'architecture gelée, `R6_PLAN.md`, `R6_STATUS.md`, `R6_12_DESIGN.md`, `R6_12_ACCEPTANCE.md`, `R6_INTEGRATED_ACCEPTANCE.json` et ce fichier avant toute suite.

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
- R7–R16 : PENDING / NOT STARTED.

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

**R7 n'est pas commencé.** La prochaine action autorisée, lorsque l'utilisateur demande de poursuivre, est de créer `docs/roadmap/R7_PLAN.md` exhaustif depuis le template, synchroniser la continuité, ouvrir une PR de planification, obtenir R0 + Python Core + UI Smoke sur son head final et fusionner ce plan. **R7.1 ne doit commencer qu'après cette fusion.**
