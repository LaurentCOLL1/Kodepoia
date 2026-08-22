# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1–R6.10 sont COMPLETE. R6.11 — KodeLicense + KodeBOM est IN PROGRESS sur `feature/r6-11-license-bom` depuis le main normalisé `36524978a963d8c759d36902bc1ab00989da0549`.** R6.10 a été accepté sur `e9363e0e00f592b39a7a094b7520b3d515fb02f0`, R0 #844, Python Core #818 cinq jobs et UI #785 SUCCESS, PR #52 merge `cefc60266cb191cf0ee5a099e0d8923a2f14745a`; normalisation #53 head `03d1c75547e667ceaa1842b1f39b12500e3ee103`, R0 #851, Python Core #825 cinq jobs et UI #792 SUCCESS, merge `36524978a963d8c759d36902bc1ab00989da0549`. R6.11 implémente BOM provenance/version/source/hash, licences déclarées/conclues, `SPDX_EXPRESSION/NOASSERTION/NONE`, `LicenseRef-*`, intégrité recorded/mismatch/unknown/N/A, collecte déterministe `pyproject.toml`, politique exacte allow/warn/deny/unknown, SHA-256 anti-tamper, Health dependencies/licenses, cas R6.3, `.kodepoia/bom/` et `.kodepoia/licenses/`. Une plage de version reste UNRESOLVED; aucune licence web courante n'est copiée sur une plage non résolue; aucune licence libre/propriétaire n'est interprétée juridiquement. SPDX 3.0 reste la baseline R6, la référence de sérialisation courante est 3.0.1; CycloneDX 1.7 est contexte d'interopérabilité optionnel. Manual R6.11 = CONDITIONAL NOT TRIGGERED sauf ambiguïté réelle acceptance-critical. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_11_DESIGN.md`, `R6_11_ACCEPTANCE.md`, l'architecture gelée et ce fichier avant reprise. Ne pas commencer R6.12 avant acceptation/fusion/normalisation R6.11; ne pas commencer R7 avant R6 COMPLETE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- Source de vérité de départ R6.11 : normalized `main` `36524978a963d8c759d36902bc1ab00989da0549`.
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
- R6.10 : COMPLETE — head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`; PR #52 merge `cefc60266cb191cf0ee5a099e0d8923a2f14745a`; normalization #53 `36524978a963d8c759d36902bc1ab00989da0549`; manual NONE.
- R6.11 : IN PROGRESS — branch `feature/r6-11-license-bom`; manual CONDITIONAL NOT TRIGGERED.
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
11. R6.11 KodeLicense + KodeBOM — IN PROGRESS — CONDITIONAL NOT TRIGGERED.
12. R6.12 major-patch validation/rollback + integrated R6 acceptance — PLANNED — CONDITIONAL.

Ne pas ajouter/supprimer/fusionner/scinder/renuméroter silencieusement un R6.N.

## R6.10 accepted evidence

Accepted final implementation head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`:

- R0 #844 `32575111465` SUCCESS Windows+Ubuntu;
- Python Core #818 `32575111540` SUCCESS pour les cinq jobs: core Ubuntu, core Windows avec validation PowerShell, KodeStudio UI intégré Windows, package-build Ubuntu, package-build Windows;
- UI Smoke #785 `32575111597` SUCCESS Windows;
- implementation PR #52 merge `cefc60266cb191cf0ee5a099e0d8923a2f14745a`;
- normalization #53 head `03d1c75547e667ceaa1842b1f39b12500e3ee103`: R0 #851, Python Core #825 cinq jobs, UI #792 SUCCESS; merge `36524978a963d8c759d36902bc1ab00989da0549`;
- manual NONE.

R6.10 anti-regression permanent: inventaire incomplet reste WARN; all-N/A UNKNOWN; N/A score-neutral; `inventory_complete=true` exige provenance; aucune base légale/consentement inférée; aucune donnée personnelle réelle requise.

## R6.11 current implementation contract

- `BomComponent`: stable ID, project/package/asset, resolved/unresolved/N/A, exact version uniquement si résolu, purl, provenance, source SHA-256, requirements/groups;
- `IntegrityEvidence`: `recorded`, `mismatch`, `unknown`, `not_applicable`; recorded ≠ verified; mismatch bloque;
- licence déclarée optionnelle + licence conclue obligatoire;
- `LicenseAssertion`: `spdx_expression`, `noassertion`, `none`; NOASSERTION/NONE exigent rationale+provenance;
- `LicenseRef-*` avec hash du texte custom possible; aucun free-text→SPDX automatique;
- `KodeBOM.from_pyproject()` via `WorkspaceBoundary` + `tomllib`, couvrant build-system/runtime/tous optional groups;
- un même package normalisé dans plusieurs groupes est fusionné tout en conservant chaque requirement;
- une plage `>=...<...` reste unresolved; aucune version exacte/hash/licence externe n'est inventée;
- BOM complet explicite + provenance de revue;
- rapport BOM canonique SHA-256, counts/blockers/status dérivés et anti-tamper;
- policy licence exacte allow/warn/deny/unknown; default ALLOW interdit; unmatched/NOASSERTION reste unknown; seul DENY bloque;
- rapport licence lié au hash BOM + fingerprint policy;
- Health `dependencies` et `licenses`; cas R6.3 `bom:<id>` / `license:<id>`;
- stores `.kodepoia/bom/` et `.kodepoia/licenses/` via `WorkspaceBoundary`;
- schémas `bom-report-v1` + `license-report-v1`;
- test du `pyproject.toml` réel Kodepoia, qui doit rester WARN pour résolution/intégrité tant qu'aucun lock/artifact exact n'est fourni;
- SPDX family baseline 3.0; serialization/reference current 3.0.1; compatibility view avec `conformance_claim=false`;
- aucun shell, installer, scanner, fetch URL arbitraire, exécution d'instructions de page de licence ou publishing.

## Standards / provenance interpretation

Recheck officiel du 22 août 2026:

- SPDX Specification courante: 3.0.1; la baseline gelée R6 reste la famille SPDX 3.0;
- JSON-LD context courant: `https://spdx.org/rdf/3.0.1/spdx-context.jsonld`;
- SPDX distingue explicitement `NoAssertionLicense` d'une information absente et permet les `LicenseRef-*`;
- CycloneDX 1.7 est le contexte stable optionnel; 2.0 n'est pas adopté silencieusement.

Les pages PyPI courantes peuvent servir de recherche/provenance pour une version exacte lorsque pertinente, mais R6.11 n'applique jamais la licence de la version courante à une plage non résolue. Le moteur ne fait aucune interprétation juridique de compatibilité entre licences.

## Manual forecast

- R6.4 REQUIRED SATISFIED.
- R6.5 REQUIRED SATISFIED.
- R6.6 NONE COMPLETE.
- R6.7 NONE COMPLETE.
- R6.8 CONDITIONAL NOT TRIGGERED.
- R6.9 NONE COMPLETE.
- R6.10 NONE COMPLETE.
- R6.11 CONDITIONAL NOT TRIGGERED — seulement si une conclusion de licence précise devient acceptance-critical et reste ambiguë après sources de confiance.
- R6.12 CONDITIONAL seulement si les gates finaux sélectionnés requièrent hardware local ou approbation explicite.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` impose à chaque phase majeure depuis R7 de fusionner son `RX_PLAN.md` exhaustif avant `RX.1`.

## Next action

Ouvrir une PR draft R6.11, utiliser la CI comme diagnostic sur Windows+Ubuntu, corriger uniquement les défauts démontrés sans réduire UNKNOWN/NOASSERTION/provenance/intégrité, figer un head final exact, obtenir R0 + Python Core cinq jobs + UI Smoke, fusionner avec `expected_head_sha`, puis normaliser `R6_11_ACCEPTANCE.md`, `R6_STATUS.md`, `R6_PLAN.md` et ce fichier. R6.12 ne commence qu'après ce merge de normalisation. R7 reste interdit avant R6 COMPLETE.
