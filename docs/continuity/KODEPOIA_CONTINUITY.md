# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1–R6.7 sont COMPLETE. R6.8 — KodeCI + KodeBuild foundation est IN PROGRESS sur PR #47 depuis le main normalisé `fc7bd4d5803c451b4d343d08bcc212868ad24412`.** Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_8_DESIGN.md`, `R6_8_ACCEPTANCE.md`, l'architecture gelée et ce fichier avant reprise. Le diagnostic R6.8 durci sur `fe084cfbe8f3bafddbf6075ad4c8596ba3998b5a` a prouvé les builds package Ubuntu+Windows, le binding exact du checkout au source SHA, la validation wheel+sdist et l'upload des artefacts. Il reste à exécuter les mêmes gates sur le head final après synchronisation plan/status/continuité, inspecter les artefacts finaux, décider explicitement le gate manuel CONDITIONAL, fusionner #47 puis normaliser. Ne pas commencer R6.9 ou R7 auparavant.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- Source de vérité avant R6.8 : normalized `main` `fc7bd4d5803c451b4d343d08bcc212868ad24412`.
- R1–R5 : COMPLETE.
- R6 : IN PROGRESS.
- R6.1 : COMPLETE — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
- R6.2 : COMPLETE — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
- R6.3 : COMPLETE — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
- R6 plan : ACCEPTED — PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`; normalization #38 `e96e7c3b168975869c911f880044b7ef8e322157`.
- R6.4 : COMPLETE — PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`; manual REQUIRED SATISFIED.
- R6.5 : COMPLETE — PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`; manual REQUIRED SATISFIED.
- R6.6 : COMPLETE — accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`; manual NONE.
- R6.7 : COMPLETE — accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`; manual NONE.
- R6.8 : IN PROGRESS — branch `feature/r6-8-ci-build`, PR #47 — manual CONDITIONAL, currently expected NOT TRIGGERED but not final until exact-final-head evidence.
- R6.9–R6.12 : PLANNED.
- R7–R16 : PENDING.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not route to Granite.

## Permanent architecture/security boundaries

Preserve:

- `WorkspaceBoundary` confinement and symlink-escape rejection;
- `ProcessSandbox` + global KillSwitch;
- Guardian + `PermissionSet`;
- structured Tool APIs; no arbitrary model-supplied commands/argv/cwd/host;
- SafeChange before sensitive mutations;
- AuditLog hash chain;
- secrets redaction/exclusion;
- schema/DataGovernance discipline;
- structured Health/Budget/Test/Regression/VisualQA/Accessibility/Localization/TechnicalDebt/CI/Build evidence;
- platform-aware non-target behavior;
- ADR for foundation architecture changes;
- exact-head final CI and no completion from partial/wrong-environment evidence.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance 19/19 PASS.
- `ProcessSandbox.run()` drains PIPEs with `communicate(timeout=...)`.
- Long-lived socket services use sandboxed background execution.
- Real-render Godot evidence cannot be replaced by dummy/headless rendering when real rendering is required.
- DAP sequencing and loopback-only Godot services remain protected.

## Frozen R6 structure

1. R6.1 KodeHealth — COMPLETE — NONE.
2. R6.2 KodeBudget — COMPLETE — NONE.
3. R6.3 KodeTests + KodeRegression — COMPLETE — NONE.
4. R6.4 KodeVisualQA — COMPLETE — REQUIRED SATISFIED.
5. R6.5 KodeAccessibility — COMPLETE — REQUIRED SATISFIED.
6. R6.6 KodeLocalization + pseudo-localization — COMPLETE — NONE.
7. R6.7 KodeTechnicalDebt — COMPLETE — NONE.
8. R6.8 KodeCI + KodeBuild — IN PROGRESS — CONDITIONAL.
9. R6.9 KodeAppSecurity — PLANNED — NONE.
10. R6.10 KodePrivacy — PLANNED — NONE.
11. R6.11 KodeLicense + KodeBOM — PLANNED — CONDITIONAL.
12. R6.12 major-patch validation/rollback + integrated R6 acceptance — PLANNED — CONDITIONAL.

Do not silently add/remove/merge/split/renumber any R6.N.

## R6.4–R6.7 accepted evidence

- R6.4 head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; hosted gates SUCCESS; local VisualQA 8/8 PASS; merge #39 `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`.
- R6.5 head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; hosted gates SUCCESS; Windows accessibility 15/15 PASS; merge #41 `db1a1ab78eb2ac7d90f75ab294074dec0238268c`.
- R6.6 head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; R0 #733, Python Core #707, UI Smoke #674 SUCCESS; merge #43 `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
- R6.7 head `0da49c7526b54f562827d63477b7ce8f1865de43`; R0 #756, Python Core #730, UI Smoke #697 SUCCESS; merge #45 `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`.

## R6.8 current implementation contract

R6.8 now implements:

- `KodeCI` statuses `queued/in_progress/pass/fail/cancelled/skipped/unknown` with required skipped/cancelled never PASS;
- exact source-SHA binding, canonical evidence SHA-256, derived counts/blockers and R6.3 hooks;
- `KodeBuild` manifest with source SHA/platform/Python/backend, source/dependency-input SHA-256, artifact name/size/SHA-256/validation;
- structural wheel and sdist validation; missing/invalid required package artifacts block;
- recursive secret redaction before persistence;
- `.kodepoia/workflows/` and `.kodepoia/releases/` through `WorkspaceBoundary`;
- Health `build` and stable R6.3 build hooks;
- `ci-report-v1` and `build-manifest-v1` schemas;
- fixed `scripts/r6_8_collect_build.py` collector with no arbitrary model-supplied command/path surface;
- additive Python Core `package-build` matrix for Ubuntu+Windows using `python -m build` and `actions/upload-artifact@v4`;
- exact package-build checkout set to `${{ github.event.pull_request.head.sha || github.sha }}` so the built bytes and manifest source SHA refer to the same commit.

Diagnostic evidence on `fe084cfbe8f3bafddbf6075ad4c8596ba3998b5a`:

- R0 #779 `32571588986` SUCCESS Windows+Ubuntu;
- Python Core #753 `32571588989` SUCCESS for both core tests, integrated UI and both package-build matrix jobs;
- UI Smoke #720 `32571588982` SUCCESS Windows;
- Ubuntu package build checked out exact `fe084cfb...`, Python 3.12.14, wheel `kodepoia-0.1.0a4-py3-none-any.whl` SHA-256 `35489ed602a9ade3816a4562f5cd751fbfb8924cd8ad780fba5bc7aa26a2a095`, sdist SHA-256 `c3895dea87a633a995f398959f21e841b99c7a218eccd41c024feae489ff3b37`, build evidence `5ca1057472a36020a1717ae4b8ba69b0dd802ea0c62c54a6001edd274adfcf88`, CI evidence `657e15c1426f9d4e95b81d6cb618d44eca31c9b12124a27105985abf94fbe45e`, both PASS;
- Windows package build checked out exact `fe084cfb...`, hosted Windows Server 2025, Python 3.12.10, wheel SHA-256 `1406f5a2f180b56c611fb3a0cd8a9d23436682903405f52dadc26257c5b676fb`, sdist SHA-256 `c19a3ee995cba931a139cfb0f9a52e236858bc659d4194617eeb1dbafb6a18f8`, build evidence `d9ec1e985e55634db7a51eeacb57967ebcf88f4adfe46178e2c85c10c257fb1d`, CI evidence `919b887754e87a8835c48bb64e9c8a7bc9879e5637b96cfd7c8b5fc4d63dcbe3`, both PASS;
- both jobs uploaded package+evidence bundles successfully.

Do not treat cross-platform archive SHA differences as a failure by themselves; R6.8 records per-platform digests and exact inputs instead of falsely claiming byte-identical outputs across different runner/Python environments.

## R6.8 conditional manual gate

Manual intervention remains **CONDITIONAL**. The diagnostic hosted Windows job has already demonstrated the acceptance-critical Windows package behavior, so no local user action is presently justified. Final decision becomes **NOT TRIGGERED** only after the final implementation head repeats Windows build/validation/hash/upload successfully and its artifact is inspected.

If a final hosted limitation appears, freeze the exact head before requesting any local action and provide prerequisites, exact commands, expected output, recovery, evidence and do-not-do-yet instructions.

## External reference baselines

- Unicode CLDR stable releases: locale-data context only for R6.6.
- WCAG 2.2 + WCAG2ICT 2.2: accessibility interpretation.
- SLSA concepts: provenance context for R6.8; no SLSA-level claim without complete independent proof.
- GitHub artifact attestations can bind artifacts to repository/workflow/commit provenance, but GitHub states attestations alone are not a security guarantee and recommends not attesting frequent builds used only for automated testing. R6.8 therefore does not make PR-build attestation a completion gate.
- OWASP ASVS 5.0.0: later applicable AppSecurity surfaces.
- SPDX 3.0: later BOM baseline.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` requires every new major phase from R7 onward to create and merge `docs/roadmap/RX_PLAN.md` before `RX.1`, enumerate all RX.N, detail scope/deliverables/acceptance/rollback/manual gates, and keep plan+continuity synchronized.

## Next action

Synchronize `R6_PLAN.md` for active R6.8, freeze the final implementation head, run final R0/Python Core/UI/package-build gates, inspect both uploaded package/evidence artifacts, decide the conditional manual gate, then merge PR #47 and perform post-merge R6.8 normalization. Do not start R6.9 or R7 earlier.