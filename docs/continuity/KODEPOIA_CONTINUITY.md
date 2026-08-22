# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1–R6.8 sont COMPLETE. R6.9 — KodeAppSecurity baseline est IN PROGRESS sur `feature/r6-9-appsecurity` depuis le main normalisé `616899291fc3b4dc40695415a5008d6fdd599230`.** Lire `docs/roadmap/R6_PLAN.md`, `R6_STATUS.md`, `R6_9_DESIGN.md`, `R6_9_ACCEPTANCE.md`, l'architecture gelée et ce fichier avant reprise. R6.9 introduit un modèle de menaces structuré, des exigences applicables/N/A distinctes, des observations de vulnérabilité dépendance horodatées/provenancées, anti-tamper SHA-256, redaction des secrets, Health `security` et cas R6.3. Le risque résiduel du modèle de menaces reste UNKNOWN par défaut : ne pas transformer une mitigation architecturale en PASS automatique. OWASP ASVS 5.0.0 est utilisé uniquement comme catalogue lorsque pertinent, avec références `v5.0.0-x.y.z`; N/A n'est jamais PASS. Manual R6.9 = NONE. Ne pas commencer R6.10 avant acceptation/fusion/normalisation R6.9 et ne pas commencer R7 avant R6 COMPLETE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- Source de vérité avant R6.9 : normalized `main` `616899291fc3b4dc40695415a5008d6fdd599230`.
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
- R6.8 : COMPLETE — accepted head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; normalization #48 merge `92effbde1e432a8fcb6c794038d77367d034bcb0`; final normalized-state wording PR #49 merge `616899291fc3b4dc40695415a5008d6fdd599230`; manual CONDITIONAL NOT TRIGGERED.
- R6.9 : IN PROGRESS — branch `feature/r6-9-appsecurity` — manual NONE.
- R6.10–R6.12 : PLANNED.
- R7–R16 : PENDING.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not route to Granite.

## Permanent architecture/security boundaries

Preserve:

- `WorkspaceBoundary` path confinement and symlink-escape rejection;
- `ProcessSandbox` + global KillSwitch;
- Guardian + `PermissionSet` authorization/risk control;
- structured Tool APIs; no arbitrary model-supplied commands/argv/cwd/host;
- SafeChange before sensitive mutations;
- AuditLog hash chain;
- raw secret reads denied; delegated secret operations via `KodeSecrets`/OS keyring;
- secrets redaction/exclusion from model context and persistent evidence;
- schema/DataGovernance discipline;
- structured Health/Budget/Test/Regression/VisualQA/Accessibility/Localization/TechnicalDebt/CI/Build/Security evidence;
- platform-aware behavior and explicit N/A/UNKNOWN rather than fake PASS;
- exact-head acceptance;
- ADR for foundation architecture changes.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance 19/19 PASS.
- `ProcessSandbox.run()` drains stdout/stderr with `communicate(timeout=...)`.
- long-lived socket services use background execution without unread PIPEs;
- real-render evidence cannot be replaced by headless/dummy when real rendering is required;
- Godot LSP/DAP/debug remains loopback-only and no arbitrary host/program/cwd is accepted from model input.

## Frozen R6 structure

1. R6.1 KodeHealth — COMPLETE — NONE.
2. R6.2 KodeBudget — COMPLETE — NONE.
3. R6.3 KodeTests + KodeRegression — COMPLETE — NONE.
4. R6.4 KodeVisualQA — COMPLETE — REQUIRED SATISFIED.
5. R6.5 KodeAccessibility — COMPLETE — REQUIRED SATISFIED.
6. R6.6 KodeLocalization + pseudo-localization — COMPLETE — NONE.
7. R6.7 KodeTechnicalDebt — COMPLETE — NONE.
8. R6.8 KodeCI + KodeBuild — COMPLETE — CONDITIONAL NOT TRIGGERED.
9. R6.9 KodeAppSecurity — IN PROGRESS — NONE.
10. R6.10 KodePrivacy — PLANNED — NONE.
11. R6.11 KodeLicense + KodeBOM — PLANNED — CONDITIONAL.
12. R6.12 major-patch validation/rollback + integrated R6 acceptance — PLANNED — CONDITIONAL.

Do not silently add/remove/merge/split/renumber any R6.N.

## R6.8 accepted evidence

Accepted final implementation head `d632669b93fda7b8397b9c3de43d78ca8726323f`:

- R0 #783 `32571710663` SUCCESS Windows+Ubuntu;
- Python Core #757 `32571710718` SUCCESS for core Ubuntu, core Windows, integrated Windows UI, package-build Ubuntu and package-build Windows;
- separate UI Smoke #724 `32571710650` SUCCESS Windows;
- Windows Actions bundle ID `9475485133`, ZIP SHA-256 `aae159bd0d8a04ee4cec6c65f7a20f104c4679a9081432640419c4a6e74ccbe5`;
- Ubuntu Actions bundle ID `9475481332`, ZIP SHA-256 `cdeef82ace3e0ca2ef0275b3111bf6d2c8f50213b20e777ddb436477e48261d8`;
- both downloaded bundles inspected: wheel + sdist + build manifest + CI report, Build/CI PASS, zero blockers, exact source SHA;
- manual CONDITIONAL gate NOT TRIGGERED.

Normalization #48 head `0580f930d6dfaa387c1eda1cf8ad56de79cc42b9` passed R0 #790, Python Core #764 and UI Smoke #731 and merged as `92effbde1e432a8fcb6c794038d77367d034bcb0`. Final wording #49 head `beb431d19c487c55b92c86a7a0eead90c7529b6e` passed R0 #797, Python Core #771 including both package builds and UI Smoke #738, then merged as `616899291fc3b4dc40695415a5008d6fdd599230`.

## R6.9 current implementation contract

R6.9 currently implements:

- `SecurityApplicability`: `applicable` / `not_applicable`;
- requirement statuses `pass/warn/fail/unknown/not_applicable` and report statuses `unknown/pass/warn/fail`;
- stable lowercase IDs and version-pinned ASVS refs only (`v5.0.0-x.y.z`) when used;
- typed threat assets, trust boundaries, entry points and threats with cross-reference validation;
- initial Kodepoia threats: path traversal, arbitrary process execution, secret disclosure, loopback exposure and downloaded-code governance bypass;
- residual-risk UNKNOWN default so architecture intent does not auto-pass;
- measured PASS/WARN/FAIL requires `evidence_source`; N/A requires rationale and cannot block;
- dependency-vulnerability evidence with exact component/version, timezone-aware check time, provenance and advisory IDs for AFFECTED;
- conservative aggregate FAIL on failed requirement / affected dependency / blocking threat;
- recursive secret redaction using the accepted R6.8 evidence-redaction helper;
- canonical SHA-256 report with derived-count/blocker/status tamper rejection;
- `.kodepoia/diagnostics/security/` through `WorkspaceBoundary`;
- Health `security` adapter with UNKNOWN score semantics;
- stable R6.3 IDs for requirements, dependencies and threats; N/A/WARN/UNKNOWN are SKIP, not PASS;
- `security-report-v1.schema.json`;
- `tests/test_r6_9_appsecurity.py` covering cross refs, N/A semantics, ASVS versioning, secure storage, dependency evidence, status aggregation, tamper, redaction, Health/R6.3, store and malformed payloads;
- `docs/roadmap/R6_9_DESIGN.md` and `R6_9_ACCEPTANCE.md`;
- no unrestricted security scanner/network/process path.

### ASVS interpretation

OWASP ASVS 5.0.0 was rechecked as the current stable release on 2026-08-22. It is a Web-application/service standard, so Kodepoia applies individual controls only where a real surface exists. Representative mappings recorded in R6.9 include:

- `v5.0.0-1.2.5` for OS-command injection/process construction;
- `v5.0.0-5.3.2` for trusted/validated file-path construction and path-traversal exposure;
- `v5.0.0-13.3.1` for secrets-management solution / keeping secrets out of source or build artifacts.

No full ASVS compliance or certification claim is made.

## R6.9 manual gate

**NONE.** Hosted Windows + Ubuntu CI are authoritative for this foundation. Do not ask for local user execution merely to duplicate hosted evidence.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` requires every major phase from R7 onward to merge its exhaustive `RX_PLAN.md` before `RX.1`.

## Next action

Finish R6.9 implementation/testing, run exact-final-head R0/Python Core/UI/package-build gates, merge the implementation PR, then perform post-merge R6.9 normalization. Only after normalized R6.9 may R6.10 begin. R6 remains IN PROGRESS; R7 must not start before R6.12.
