# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1–R6.8 sont COMPLETE. `docs/roadmap/R6_PLAN.md` reste le plan exhaustif accepté et fige R6.1–R6.12. R6.9 — KodeAppSecurity baseline est NEXT / NOT STARTED après fusion de la normalisation post-R6.8.** R6.8 a été accepté sur le head exact `d632669b93fda7b8397b9c3de43d78ca8726323f`; R0 #783, Python Core #757 avec les cinq jobs y compris les builds package Ubuntu/Windows, et UI Smoke #724 ont réussi. Les deux bundles GitHub Actions ont été téléchargés et inspectés; leurs manifests Build/CI sont PASS, zéro blocker, liés au head exact. PR #47 a été fusionnée en `d570a3930ee63802882b8682e4532004d4fd81d6`. Le gate manuel R6.8 était CONDITIONAL et est **NOT TRIGGERED**. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_8_DESIGN.md`, `R6_8_ACCEPTANCE.md`, l'architecture gelée et ce fichier avant reprise. Ne pas rouvrir R1–R6.8 sans régression démontrée/ADR et ne pas commencer R7 avant R6 COMPLETE.

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
- R6.8 : COMPLETE — accepted head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; manual CONDITIONAL NOT TRIGGERED.
- Normalisation R6.8 : `feature/r6-8-post-merge-normalization`; must become CI-green and merge before R6.9 starts.
- R6.9 : NEXT / NOT STARTED — manual NONE.
- R6.10–R6.12 : PLANNED.
- R7–R16 : PENDING.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not route to Granite.

## Permanent architecture/security boundaries

Preserve `WorkspaceBoundary`, `ProcessSandbox` + KillSwitch, Guardian + `PermissionSet`, structured Tool APIs, SafeChange where required, AuditLog chain, secrets redaction/exclusion, schema/DataGovernance discipline, platform-aware target behavior and exact-head acceptance. No arbitrary model-supplied command/argv/cwd/host, no direct governance bypass and no architecture foundation change without ADR.

## Frozen R6 structure

1. R6.1 KodeHealth — COMPLETE — NONE.
2. R6.2 KodeBudget — COMPLETE — NONE.
3. R6.3 KodeTests + KodeRegression — COMPLETE — NONE.
4. R6.4 KodeVisualQA — COMPLETE — REQUIRED SATISFIED.
5. R6.5 KodeAccessibility — COMPLETE — REQUIRED SATISFIED.
6. R6.6 KodeLocalization + pseudo-localization — COMPLETE — NONE.
7. R6.7 KodeTechnicalDebt — COMPLETE — NONE.
8. R6.8 KodeCI + KodeBuild — COMPLETE — CONDITIONAL NOT TRIGGERED.
9. R6.9 KodeAppSecurity — NEXT / NOT STARTED — NONE.
10. R6.10 KodePrivacy — PLANNED — NONE.
11. R6.11 KodeLicense + KodeBOM — PLANNED — CONDITIONAL.
12. R6.12 major-patch validation/rollback + integrated R6 acceptance — PLANNED — CONDITIONAL.

Do not silently add/remove/merge/split/renumber any R6.N.

## R6.8 accepted evidence

Accepted final head `d632669b93fda7b8397b9c3de43d78ca8726323f`:

- R0 #783 `32571710663` SUCCESS Windows+Ubuntu;
- Python Core #757 `32571710718` SUCCESS for core Ubuntu, core Windows, integrated Windows UI, package-build Ubuntu and package-build Windows;
- separate UI Smoke #724 `32571710650` SUCCESS Windows;
- both package jobs explicitly checked out the exact source SHA above;
- Windows hosted image: Windows Server 2025, Python 3.12.10;
- Ubuntu hosted image: Ubuntu 24.04.4, Python 3.12.14;
- Windows wheel SHA-256 `1406f5a2f180b56c611fb3a0cd8a9d23436682903405f52dadc26257c5b676fb`, sdist `42e63403069e61235cefa71ebbc4099b5e717e1528a6eae54ef0673f20e69edd`, build evidence `248d49db9badfea775d18ca4087eb56ba053c961f888d5641dc42e62c6d8f419`, CI evidence `47ffad9f7f1d2c7af14efdc0f71e065b6b556046404069f2f02ef8b353024160`;
- Ubuntu wheel SHA-256 `35489ed602a9ade3816a4562f5cd751fbfb8924cd8ad780fba5bc7aa26a2a095`, sdist `b803d3f316f46ea461af853240ba8ab8bf3f867e0cff8e88e70f87bf678c1a78`, build evidence `57e11b0a66e1f40d9984ae7aeacbe3874df5ce7b005657a72e6e603a63f983d8`, CI evidence `1a9f0e6dc0c099d5a7d9336d97a1e53ec40563cce90ba2a8c56e80b2eeb58869`;
- Windows Actions bundle ID `9475485133`, ZIP SHA-256 `aae159bd0d8a04ee4cec6c65f7a20f104c4679a9081432640419c4a6e74ccbe5`;
- Ubuntu Actions bundle ID `9475481332`, ZIP SHA-256 `cdeef82ace3e0ca2ef0275b3111bf6d2c8f50213b20e777ddb436477e48261d8`;
- both downloaded bundles inspected: expected four files, Build/CI PASS, zero blockers, exact source SHA.

R6.8 implements explicit CI states, source-SHA-bound CI evidence, wheel/sdist manifests, source/dependency/artifact hashes, secret redaction, WorkspaceBoundary persistence, Health build adapter, R6.3 hooks and an additive Windows+Ubuntu package-build matrix. The fixed collector exposes no arbitrary model-supplied command/path surface.

Cross-platform archive/source-input byte hashes may differ because the hosted images/toolchains/checkouts differ. R6.8 records those per-platform bytes and the immutable Git source SHA; it does not falsely claim byte-identical Windows/Ubuntu packages.

### Conditional manual gate

**NOT TRIGGERED.** Hosted Windows proved every acceptance-critical Windows build operation and its uploaded bundle was independently inspected. Do not ask the user to repeat this locally unless a later demonstrated regression invalidates the evidence.

## External reference context

SLSA provenance concepts and GitHub artifact attestations were reviewed for R6.8. No SLSA level is claimed. GitHub documentation says attestations establish artifact provenance but are not by themselves a guarantee that an artifact is secure, and recommends against attesting frequent builds used only for automated testing; therefore routine PR-build attestation is not an R6.8 completion gate.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` requires every major phase from R7 onward to merge its exhaustive `RX_PLAN.md` before `RX.1`.

## Next action

Finish and merge R6.8 post-merge normalization. Only then may R6.9 begin. R6 remains IN PROGRESS and R7 must not start before R6.12 completes the integrated phase gate.