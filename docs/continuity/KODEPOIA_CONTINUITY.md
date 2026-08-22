# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1–R6.10 sont COMPLETE. R6.11 — KodeLicense + KodeBOM est NEXT / NOT STARTED après fusion de la normalisation post-R6.10.** R6.10 a démarré depuis le main normalisé `4df229e431d2d54e4268607f38bac4045ac590d1`, a été accepté sur le head exact `e9363e0e00f592b39a7a094b7520b3d515fb02f0`, avec R0 #844 `32575111465`, Python Core #818 `32575111540` cinq jobs et UI Smoke #785 `32575111597` SUCCESS, puis PR #52 fusionnée avec verrou `expected_head_sha` en `cefc60266cb191cf0ee5a099e0d8923a2f14745a`. R6.10 conserve inventaire `collected/none/not_applicable`, lifecycle source/purpose/storage/recipients/retention/deletion, sensibilité, base légale/consentement `unspecified/declared/not_applicable`, preuve explicite `inventory_complete` + `inventory_review_source`, issues privacy, préparation Apple/Google, redaction des secrets/valeurs personnelles, SHA-256 anti-tamper, Health PRIVACY et cas R6.3. Un inventaire incomplet reste WARN; un ensemble uniquement N/A reste UNKNOWN; N/A est neutre dans le score et reste SKIP dans R6.3. Aucun fondement légal n'est inféré, aucune donnée personnelle réelle n'est nécessaire, aucun envoi store/service privacy distant n'est ajouté. Manual R6.10 = NONE. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_10_DESIGN.md`, `R6_10_ACCEPTANCE.md`, l'architecture gelée et ce fichier avant reprise. Ne pas commencer R6.11 avant fusion de la normalisation post-R6.10; ne pas commencer R7 avant R6 COMPLETE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- Source de vérité de départ R6.10 : normalized `main` `4df229e431d2d54e4268607f38bac4045ac590d1`.
- R1–R5 : COMPLETE.
- R6 : IN PROGRESS.
- R6 plan : ACCEPTED — PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`; normalization #38 `e96e7c3b168975869c911f880044b7ef8e322157`.
- R6.1 : COMPLETE — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
- R6.2 : COMPLETE — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
- R6.3 : COMPLETE — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
- R6.4 : COMPLETE — PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`; manual REQUIRED SATISFIED.
- R6.5 : COMPLETE — PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`; manual REQUIRED SATISFIED.
- R6.6 : COMPLETE — head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`; manual NONE.
- R6.7 : COMPLETE — head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`; manual NONE.
- R6.8 : COMPLETE — head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; normalization #48 `92effbde1e432a8fcb6c794038d77367d034bcb0`; wording #49 `616899291fc3b4dc40695415a5008d6fdd599230`; manual CONDITIONAL NOT TRIGGERED.
- R6.9 : COMPLETE — head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`; PR #50 merge `f5c135edf0be464a02b4b46d67c14e665f236009`; normalization #51 `4df229e431d2d54e4268607f38bac4045ac590d1`; manual NONE.
- R6.10 : COMPLETE — head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`; PR #52 merge `cefc60266cb191cf0ee5a099e0d8923a2f14745a`; manual NONE; post-merge normalization in progress.
- R6.11 : NEXT / NOT STARTED — manual CONDITIONAL.
- R6.12 : PLANNED.
- R7–R16 : PENDING.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste un futur candidat KodeDeepCoder.
- Le Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## Permanent architecture/security boundaries

Préserver `WorkspaceBoundary`, `ProcessSandbox` + KillSwitch, Guardian + `PermissionSet`, structured Tool APIs, SafeChange lorsque requis, AuditLog hash chain, secrets délégués/OS-backed, redaction/exclusion des secrets, schema/DataGovernance, N/A/UNKNOWN explicites, exact-head acceptance et ADR pour changement d'architecture foundation. Ne jamais ajouter de commande/argv/cwd/host/scanner URL fournie arbitrairement par le modèle ni contourner la gouvernance.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance 19/19 PASS.
- `ProcessSandbox.run()` draine stdout/stderr avec `communicate(timeout=...)`.
- Les services longs utilisent l'exécution background gouvernée sans PIPEs non lus.
- Une preuve real-render ne peut pas être remplacée par du headless/dummy lorsqu'elle est requise.
- Godot LSP/DAP/debug reste loopback-only; aucun host/program/cwd arbitraire depuis le modèle.

## Frozen R6 structure

1. R6.1 KodeHealth — COMPLETE — NONE.
2. R6.2 KodeBudget — COMPLETE — NONE.
3. R6.3 KodeTests + KodeRegression — COMPLETE — NONE.
4. R6.4 KodeVisualQA — COMPLETE — REQUIRED SATISFIED.
5. R6.5 KodeAccessibility — COMPLETE — REQUIRED SATISFIED.
6. R6.6 KodeLocalization + pseudo-localization — COMPLETE — NONE.
7. R6.7 KodeTechnicalDebt — COMPLETE — NONE.
8. R6.8 KodeCI + KodeBuild — COMPLETE — CONDITIONAL NOT TRIGGERED.
9. R6.9 KodeAppSecurity — COMPLETE — NONE.
10. R6.10 KodePrivacy — COMPLETE — NONE.
11. R6.11 KodeLicense + KodeBOM — NEXT / NOT STARTED — CONDITIONAL.
12. R6.12 major-patch validation/rollback + integrated R6 acceptance — PLANNED — CONDITIONAL.

Ne pas ajouter/supprimer/fusionner/scinder/renuméroter silencieusement un R6.N.

## R6.9 accepted evidence

Accepted final implementation head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`:

- R0 #812 `32573265598` SUCCESS Windows+Ubuntu;
- Python Core #786 `32573265793` SUCCESS core Ubuntu, core Windows, integrated Windows UI, package-build Ubuntu et package-build Windows;
- UI Smoke #753 `32573265579` SUCCESS Windows;
- implementation PR #50 merge `f5c135edf0be464a02b4b46d67c14e665f236009`;
- normalization #51 head `f42e2d2027c3a3601f22446cbbeee9f702e8458f`: R0 #819, Python Core #793 cinq jobs, UI Smoke #760 SUCCESS; merge `4df229e431d2d54e4268607f38bac4045ac590d1`;
- manual NONE.

## R6.10 accepted evidence

Accepted final implementation head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`:

- R0 #844 `32575111465` SUCCESS Windows+Ubuntu;
- Python Core #818 `32575111540` SUCCESS pour les cinq jobs: core Ubuntu, core Windows avec validation PowerShell, KodeStudio UI intégré Windows, package-build Ubuntu, package-build Windows;
- UI Smoke #785 `32575111597` SUCCESS Windows;
- implementation PR #52 fusionnée avec `expected_head_sha=e9363e0e00f592b39a7a094b7520b3d515fb02f0` en `cefc60266cb191cf0ee5a099e0d8923a2f14745a`;
- manual NONE.

## R6.10 accepted contract

R6.10 construit une fondation de preuve et non un moteur de conclusion juridique:

- `PrivacyDataItem` avec ID stable, catégorie, disposition `collected/none/not_applicable`, plateformes et provenance;
- si `collected`: source, purpose, storage, recipients, retention, deletion et sensitivity selon le contrat;
- `PrivacyBasisState`: `unspecified`, `declared`, `not_applicable`; aucune base légale/consentement inférée du silence; une base déclarée exige provenance;
- `PrivacyReport.inventory_complete` est une preuve distincte; `true` exige `inventory_review_source`; un inventaire incomplet reste WARN et ne peut pas fabriquer PASS;
- `PrivacyIssue`: applicability/status/severity; N/A distinct de PASS; PASS/WARN/FAIL mesuré exige evidence source; seul FAIL peut bloquer;
- `StorePrivacyDeclaration`: préparation Apple (`collected`, linked-to-user, tracking, purposes) et Google Play (`collected`, shared, optionality, purposes), valeurs `yes/no/unknown/not_applicable`, readiness dérivée;
- cohérence stricte store/platform/data-category/inventory;
- N/A est neutre dans le score, un rapport uniquement N/A reste UNKNOWN, et une déclaration N/A reste SKIP dans R6.3 même si elle est structurellement ready;
- redaction recursive des secrets et valeurs personnelles évidentes dans `details`; aucune donnée personnelle réelle n'est requise comme fixture;
- `PrivacyReport` v1 avec counts/blockers/status/readiness dérivés, SHA-256 canonique et anti-tamper;
- `.kodepoia/diagnostics/privacy/` via `WorkspaceBoundary`;
- Health `privacy` adapter + stable R6.3 cases; UNKNOWN/N/A/pending ne deviennent jamais un faux PASS;
- schéma `privacy-report-v1.schema.json` et tests ciblés;
- aucun scanner, remote privacy SaaS, analytics collector ni store submission.

## R6.10 design hardening record

- First diagnostic head `935d6b4fc7a29ad832df501f605c3648cde05988`: R0 #830, Python Core #804 cinq jobs et UI Smoke #771 SUCCESS.
- Independent design review found a potential false-green path around N/A scoring and unproven inventory completeness; this was hardened instead of accepted.
- Hardened head `48daa4f82194e1875211f205b99ba19089f42d92`: R0 #836 `32574885601`, Python Core #810 `32574885605` all five jobs, UI Smoke #777 `32574885624` SUCCESS.
- Final head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`: R0 #844, Python Core #818 cinq jobs, UI Smoke #785 SUCCESS.

Références externes utilisées uniquement comme contexte de modèle: principes GDPR (purpose limitation, minimisation, storage limitation, integrity/confidentiality/accountability), Google Play Data safety et Apple App Privacy/privacy manifests. Un PASS KodePrivacy signifie seulement que les preuves structurées sont complètes selon ce contrat, pas une conformité juridique.

## R6.11 reference baseline recheck

Au 22 août 2026, les références officielles revalidées pour R6.11 sont:

- SPDX: version courante 3.0, standard international ISO/IEC 5962:2021;
- CycloneDX: version stable 1.7 (ECMA-424, 2nd Edition); CycloneDX 2.0 est annoncé pour 2026 mais n'est pas encore la baseline stable.

R6.11 doit conserver SPDX 3.0 comme baseline gelée du plan. CycloneDX 1.7 peut servir de format d'interopérabilité/validation additionnel sans remplacer silencieusement la baseline SPDX. Aucun changement de standard ne doit être adopté sans décision explicite et mise à jour de la continuité.

## Manual forecast

- R6.4 REQUIRED SATISFIED.
- R6.5 REQUIRED SATISFIED.
- R6.6 NONE COMPLETE.
- R6.7 NONE COMPLETE.
- R6.8 CONDITIONAL NOT TRIGGERED.
- R6.9 NONE COMPLETE.
- R6.10 NONE COMPLETE.
- R6.11 CONDITIONAL seulement si une ambiguïté provenance/licence critique reste non résolue après inspection des sources de confiance.
- R6.12 CONDITIONAL seulement si les gates finaux sélectionnés requièrent hardware local ou approbation explicite.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` impose à chaque phase majeure depuis R7 de fusionner son `RX_PLAN.md` exhaustif avant `RX.1`.

## Next action

Finir et fusionner la normalisation post-R6.10. Une fois son CI exact-head vert et son merge effectué, R6.11 — KodeLicense + KodeBOM peut démarrer depuis le nouveau `main` normalisé. R7 reste interdit avant R6.12.