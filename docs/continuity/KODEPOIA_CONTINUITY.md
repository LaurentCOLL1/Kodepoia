# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1–R6.11 sont COMPLETE. R6.12 — Major-patch validation + rollback gate and R6 integration acceptance est NEXT / NOT STARTED après fusion de la normalisation post-R6.11.** R6.11 a démarré depuis le main normalisé `36524978a963d8c759d36902bc1ab00989da0549`, a été accepté sur le head net `d0590ed3eda663ad713fc36d962c8dac1df109eb`, avec R0 #885 `32578903951`, Python Core #859 `32578903981` cinq jobs et UI Smoke #826 `32578903942` SUCCESS, puis PR #54 fusionnée avec verrou exact-head en `248b1331fe2b26229b932c36aefb83c70065c52a`. R6.11 fournit BOM/licences/provenance/hashes, resolved/unresolved/N/A, declared/concluded licence, `SPDX_EXPRESSION/NOASSERTION/NONE`, `LicenseRef-*`, politique allow/warn/deny/unknown, Health dependencies/licenses, cas R6.3 et stores WorkspaceBoundary. Les plages restent unresolved, N/A reste neutral/UNKNOWN/SKIP, recorded hash ≠ verified, aucune licence ou compatibilité juridique n'est inventée. Manual R6.11 = CONDITIONAL NOT TRIGGERED. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_11_DESIGN.md`, `R6_11_ACCEPTANCE.md`, l'architecture gelée et ce fichier. R6.12 doit réutiliser SafeChange/Backup/Recovery/Audit/Guardian et toutes les preuves R6 existantes, pas créer un second système de rollback. R7 est interdit avant R6 COMPLETE; au démarrage de R7, créer/fusionner `R7_PLAN.md` exhaustif avant R7.1.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
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
- R6.11 : COMPLETE — accepted head `d0590ed3eda663ad713fc36d962c8dac1df109eb`; R0 #885, Python #859 5/5, UI #826 SUCCESS; PR #54 merge `248b1331fe2b26229b932c36aefb83c70065c52a`; manual CONDITIONAL NOT TRIGGERED; post-merge normalization active on `feature/r6-11-post-merge-normalization`.
- R6.12 : NEXT / NOT STARTED after normalization merge — manual CONDITIONAL.
- R7–R16 : PENDING.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste un futur candidat KodeDeepCoder.
- Le Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## Permanent architecture/security boundaries

Préserver `WorkspaceBoundary`, `ProcessSandbox` + KillSwitch, Guardian + `PermissionSet`, structured Tool APIs, SafeChange lorsque requis, AuditLog hash chain, Secrets OS-backed/redaction, schema/DataGovernance, N/A/UNKNOWN explicites, exact-head acceptance et ADR pour changement de fondation. Ne jamais ajouter de commande/argv/cwd/host/scanner URL arbitrairement fournie par le modèle ni contourner la gouvernance.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance 19/19 PASS.
- `ProcessSandbox.run()` draine stdout/stderr via `communicate(timeout=...)`.
- Les services longs utilisent l'exécution background gouvernée sans PIPEs non lus.
- Une preuve real-render requise ne peut pas être remplacée par headless/dummy.
- Godot LSP/DAP/debug reste loopback-only; aucun host/program/cwd arbitraire depuis le modèle.

## R6.11 accepted contract / anti-regression

- BOM components: project/package/asset, resolved/unresolved/N/A, exact version only if resolved.
- N/A requires N/A integrity, never contributes to applicable PASS/score/license decision/SPDX package; all-N/A = UNKNOWN; R6.3 = SKIP.
- Integrity: recorded/mismatch/unknown/N/A; recorded does not mean independently verified; mismatch blocks.
- Declared and concluded license evidence stay distinct; NOASSERTION/NONE remain explicit and require provenance/rationale.
- A custom license text hash binds only one standalone `LicenseRef-*`.
- `KodeBOM.from_pyproject()` collects build/runtime/all optional groups deterministically; version ranges stay unresolved.
- Exact-expression policy cannot silently default to ALLOW; only DENY blocks.
- BOM/license reports are SHA-256-bound and stored only through `WorkspaceBoundary`.
- Current Kodepoia manifest legitimately produces WARN dependency resolution/integrity until exact artifacts are available.
- SPDX 3.0 family is frozen R6 baseline; 3.0.1 is current patch-level interoperability reference; CycloneDX 1.7 is optional context only. No legal or official-conformance claim.

## R6.12 frozen execution contract

R6.12 must make “tout patch majeur a validation + rollback” enforceable and then close R6. Required design constraints:

1. deterministic major/minor classification from changed scope/risk, never free model opinion;
2. patch manifest tied to exact base/head SHAs;
3. validation matrix selected by changed domains and target platforms: tests, regression, visual, accessibility, localization, technical debt, build/CI, security, privacy, license/BOM, Health/Budget as applicable;
4. major patch cannot PASS without explicit rollback strategy;
5. missing, failed, skipped or cancelled required evidence blocks acceptance;
6. sensitive mutable changes use existing SafeChange snapshots; rollback/recovery should reuse existing `SafeChangeManager`, `BackupManager`, `RecoveryJournal` and `AuditLog` rather than introduce parallel mechanisms;
7. controlled rollback rehearsal restores expected files/state/hashes in a safe fixture;
8. no destructive production rollback rehearsal and no Guardian bypass;
9. integrated R6 report enumerates evidence from R6.1–R6.12 and rejects stale/wrong-SHA evidence;
10. all R6 regression suites and final R0/Python Core/UI gates must be green before R6 COMPLETE.

Manual R6.12 remains **CONDITIONAL**. Prefer hosted/temp-fixture proof. Trigger user intervention only if an acceptance-critical property truly depends on local hardware or an explicit Guardian/user approval that hosted CI cannot prove.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` requires every new major phase starting with R7 to create and merge an exhaustive `RX_PLAN.md` **before RX.1**, detailing every RX.X subdivision, dependencies, deliverables, acceptance, rollback and manual-intervention needs. The continuity file must be updated in the same work cycle.

## Next action

Finish `feature/r6-11-post-merge-normalization`: synchronize `R6_11_ACCEPTANCE.md`, `R6_STATUS.md`, `R6_PLAN.md` and this file, open a documentation-only PR, require exact-head R0 + Python Core five jobs + UI Smoke, merge with expected head SHA. Only then create the R6.12 branch from normalized main. R7 remains forbidden until R6.12 and final R6 normalization are COMPLETE.
