# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1–R6.9 sont COMPLETE. R6.10 — KodePrivacy baseline est NEXT / NOT STARTED après fusion de la normalisation post-R6.9.** R6.9 a été accepté sur le head exact `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`; R0 #812, Python Core #786 avec les cinq jobs et UI Smoke #753 ont réussi; PR #50 a été fusionnée en `f5c135edf0be464a02b4b46d67c14e665f236009`; manual R6.9 = NONE. R6.9 conserve `not_applicable` distinct de PASS, risque résiduel UNKNOWN par défaut, provenance obligatoire pour les résultats mesurés, dépendances horodatées/provenancées, redaction des secrets, anti-tamper SHA-256, Health SECURITY et cas R6.3. OWASP ASVS 5.0.0 reste un catalogue applicable, pas une certification globale. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_9_DESIGN.md`, `R6_9_ACCEPTANCE.md`, l'architecture gelée et ce fichier avant reprise. Ne pas rouvrir R1–R6.9 sans régression démontrée/ADR, ne pas commencer R6.10 avant fusion de la normalisation R6.9, et ne pas commencer R7 avant R6 COMPLETE.

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
- R6.6 : COMPLETE — accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`; manual NONE.
- R6.7 : COMPLETE — accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`; manual NONE.
- R6.8 : COMPLETE — accepted head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; normalization #48 `92effbde1e432a8fcb6c794038d77367d034bcb0`; wording #49 `616899291fc3b4dc40695415a5008d6fdd599230`; manual CONDITIONAL NOT TRIGGERED.
- R6.9 : COMPLETE — accepted head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`; PR #50 merge `f5c135edf0be464a02b4b46d67c14e665f236009`; manual NONE; post-merge normalization in progress.
- R6.10 : NEXT / NOT STARTED — manual NONE.
- R6.11–R6.12 : PLANNED.
- R7–R16 : PENDING.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not route to Granite.

## Permanent architecture/security boundaries

Preserve `WorkspaceBoundary`, `ProcessSandbox` + KillSwitch, Guardian + `PermissionSet`, structured Tool APIs, SafeChange where required, AuditLog hash chain, delegated OS-backed secrets, secret redaction/exclusion, schema/DataGovernance discipline, explicit N/A/UNKNOWN semantics, exact-head acceptance and ADR for foundation architecture changes. Never add arbitrary model-supplied command/argv/cwd/host/scanner URL or bypass governance.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance 19/19 PASS.
- `ProcessSandbox.run()` drains stdout/stderr with `communicate(timeout=...)`.
- Long-lived services use governed background execution without unread PIPEs.
- Real-render evidence cannot be replaced by headless/dummy where real rendering is required.
- Godot LSP/DAP/debug remains loopback-only; no arbitrary host/program/cwd from model input.

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
10. R6.10 KodePrivacy — NEXT / NOT STARTED — NONE.
11. R6.11 KodeLicense + KodeBOM — PLANNED — CONDITIONAL.
12. R6.12 major-patch validation/rollback + integrated R6 acceptance — PLANNED — CONDITIONAL.

Do not silently add/remove/merge/split/renumber any R6.N.

## R6.8 accepted evidence

Accepted final implementation head `d632669b93fda7b8397b9c3de43d78ca8726323f`: R0 #783, Python Core #757 (five jobs), UI Smoke #724 SUCCESS; Windows Actions bundle ID `9475485133` SHA-256 `aae159bd0d8a04ee4cec6c65f7a20f104c4679a9081432640419c4a6e74ccbe5`; Ubuntu bundle ID `9475481332` SHA-256 `cdeef82ace3e0ca2ef0275b3111bf6d2c8f50213b20e777ddb436477e48261d8`; both bundles inspected and exact-source-SHA-bound; manual conditional gate NOT TRIGGERED. Normalization #48 merge `92effbde1e432a8fcb6c794038d77367d034bcb0`; final wording #49 merge `616899291fc3b4dc40695415a5008d6fdd599230`.

## R6.9 accepted evidence

Accepted final implementation head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`:

- R0 #812 `32573265598` SUCCESS Windows+Ubuntu;
- Python Core #786 `32573265793` SUCCESS for core Ubuntu, core Windows, integrated Windows UI, package-build Ubuntu and package-build Windows;
- UI Smoke #753 `32573265579` SUCCESS Windows;
- implementation PR #50 merge `f5c135edf0be464a02b4b46d67c14e665f236009`;
- manual NONE.

Accepted security foundation:

- typed assets/trust boundaries/entry points/threats with duplicate/cross-reference rejection;
- threats for workspace path traversal, arbitrary process execution, raw secret disclosure, loopback exposure and downloaded-code governance bypass;
- residual risk UNKNOWN by default;
- stable requirement IDs, `applicable` / `not_applicable`, N/A rationale, N/A never PASS;
- measured PASS/WARN/FAIL requires provenance;
- optional ASVS refs pinned to `v5.0.0-x.y.z`;
- dependency observations require component/version/time/provenance; AFFECTED requires advisory IDs and fails the report;
- recursive secret redaction, canonical evidence SHA-256, derived count/blocker/status tamper rejection;
- `.kodepoia/diagnostics/security/` through `WorkspaceBoundary`;
- Health SECURITY adapter and stable R6.3 cases; N/A/WARN/UNKNOWN become SKIP, not PASS;
- no arbitrary security scanner/process/network path.

Development finding: initial test expected a blocking Health score `0.0`, but deterministic aggregate score was correctly `75.0` while status remained FAIL + blocking. Only the assertion was corrected; no security rule or formula changed. Diagnostic head `0251a62c92230a486abfdd8b151e59a1adb98bb3` passed R0 #810, Python Core #784 and UI #751 before the final head.

### ASVS interpretation

OWASP ASVS 5.0.0 was rechecked as current stable on 2026-08-22. It is used only as an applicable-control catalogue. Representative mappings: `v5.0.0-1.2.5` command injection, `v5.0.0-5.3.2` trusted/validated file paths, `v5.0.0-13.3.1` secrets management. No full ASVS compliance/certification claim.

## Manual forecast

- R6.4 REQUIRED SATISFIED.
- R6.5 REQUIRED SATISFIED.
- R6.6 NONE COMPLETE.
- R6.7 NONE COMPLETE.
- R6.8 CONDITIONAL NOT TRIGGERED.
- R6.9 NONE COMPLETE.
- R6.10 NONE NEXT / NOT STARTED.
- R6.11 CONDITIONAL only for unresolved acceptance-critical license/provenance ambiguity.
- R6.12 CONDITIONAL only if final selected gates require local hardware or explicit approval.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` requires every major phase from R7 onward to merge its exhaustive `RX_PLAN.md` before `RX.1`.

## Next action

Finish and merge the R6.9 post-merge normalization. Only then may R6.10 begin. R6 remains IN PROGRESS and R7 must not start before R6.12 integrated acceptance/final normalization.
