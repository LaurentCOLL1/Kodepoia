# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R12 COMPLETE + NORMALIZED. R13 planning ACCEPTED + NORMALIZED.** R12 canonical integrated digest: `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`. R13 planning candidate `6f44e8faf8ef675dab5c8079541ce436ff55b4b2` passed R0 #1596 / `32846530810`, Python #1570 / `32846530804`, UI #1537 / `32846530786`; PR #219 merged as `9a5c678c226cb845c639b914e6365b475ab20e86`. Single planning normalization `b7ca326ac6f9fbb74bdbe69fefe6faf4aaadf653` passed R0 #1598 / `32846946552`, Python #1572 / `32846946574`, UI #1539 / `32846946557`; PR #220 merged as normalized `main` `aef297e385dc49ad6ae0935d4f9ef25a35e5e984`. **R13.1 is now IN_PROGRESS** on dedicated branch `r13/01-mobile-contracts`, based exactly on that normalized main. R13.2–R13.17 remain PLANNED. No next subdivision may start before R13.1 exact-head acceptance, merge and its single continuity-only post-merge normalization.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : **frozen**.
- R1–R12 : **COMPLETE + NORMALIZED**.
- R12 canonical integrated digest: `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R13 planning : **ACCEPTED + NORMALIZED**.
- R13 normalized planning `main`: **`aef297e385dc49ad6ae0935d4f9ef25a35e5e984`**.
- R13 phase status: **IN PROGRESS**.
- R13.1: **IN_PROGRESS**, manual **NONE**.
- R13.2–R13.17: **PLANNED / NOT STARTED**.
- R14 planning: **FORBIDDEN until R13 COMPLETE + NORMALIZED**.

## R12 final closure authority

- Accepted R12.16 implementation source: `1927d9ab673228101c932b1cb6b89243296ac957`.
- Final R12 evidence head: `f12132b777569a6a03171e759dd1b36d3a1858b4`.
- Canonical report `docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json`: `status=pass`, `blockers=[]`, semantic digest `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R12.16 PR #217 merged as `2250d782a65c4aa0d849cc98f7d87e6f3d68c07e`.
- R12 normalization head `f9a1fc05708be3a4b4048b2b33e6ac228485285e` passed R0 #1594 / `32844549399`, Python #1568 / `32844549531`, UI #1535 / `32844549411`, WPF #82 / `32844549655`, WinUI3 #72 / `32844549414`, Avalonia #68 / `32844549519`, Qt6 #63 / `32844549568`, Tauri2 #54 / `32844549393`, Integrated Windows #7 / `32844549496`, all SUCCESS.
- R12 normalization PR #218 merged as `997db5a5ad9f847037de79057bcdc7aefd1ddeb9`.
- Therefore R12 is authoritatively **COMPLETE + NORMALIZED**.

## Permanent R-phase plan status synchronization rule

For every R phase, the phase plan is live execution authority and MUST be updated both **at the beginning** and **at the end** of every subdivision.

- **Subdivision start, before implementation:** update phase-level `Status`, `Complete subdivision index`, and execution checkpoint so all prior normalized subdivisions are `COMPLETE`, the active subdivision is `IN_PROGRESS`, and later subdivisions remain `PLANNED`/`NOT STARTED`; synchronize continuity in the same work cycle.
- **Subdivision end, before final documentation re-gates:** update the same plan fields so the accepted active subdivision is `COMPLETE`; the next subdivision remains `PLANNED` until its own dedicated branch starts; synchronize continuity in the same work cycle.
- A triggered conditional manual gate must set truthful `BLOCKED`/`MANUAL_REQUIRED`, never synthetic `COMPLETE`.
- Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status.
- A stale subdivision index or stale phase status is a governance defect and blocks acceptance.

This rule applies to R13 and all later R phases unless a later accepted ADR explicitly changes it.

## R13 planning closure authority

### Frozen roadmap scope

R13 is exactly **Mobile / Platform / Release**:

- Android export/signing/AAB/APK/device tests/store;
- interface iOS/Mac/Xcode;
- DeviceLab;
- KodeRelease/Updater/Diagnostics;
- current compliance.

R14 backend/live-service work remains outside R13.

### Accepted planning and normalization

- normalized planning base: `997db5a5ad9f847037de79057bcdc7aefd1ddeb9`;
- planning branch: `r13/00-phase-plan`;
- accepted planning candidate: `6f44e8faf8ef675dab5c8079541ce436ff55b4b2`;
- planning gates all SUCCESS: R0 #1596 / `32846530810`; Python #1570 / `32846530804`; UI #1537 / `32846530786`;
- planning PR #219 merged as `9a5c678c226cb845c639b914e6365b475ab20e86`;
- single planning normalization branch: `r13/00-planning-continuity-normalization`;
- normalization head: `b7ca326ac6f9fbb74bdbe69fefe6faf4aaadf653`;
- normalization gates all SUCCESS: R0 #1598 / `32846946552`; Python #1572 / `32846946574`; UI #1539 / `32846946557`;
- PR #220 merged as **`aef297e385dc49ad6ae0935d4f9ef25a35e5e984`**.
- Therefore R13 planning is **ACCEPTED + NORMALIZED**.

### Current external baseline — date-aware, not architecture constants

- Google Play: new apps/updates must target Android 16 / API 36 from **2026-08-31**; R13 store-ready acceptance starts at API 36.
- Android Compose/AGP/compileSdk values are capability-probed and versioned; mutable ecosystem versions are not frozen architecture constants.
- Google Play publication uses Android App Bundle for new apps; upload-key and Play App Signing key states remain separate; production secrets never enter repo/evidence/argv.
- Apple App Store Connect production uploads require Xcode 26+ with iOS/iPadOS 26 SDK+ since 2026-04-28; beta/TestFlight state is distinct from stable production state.
- Apple privacy manifests/required-reason APIs, Google Play Data safety, target API, permissions/content ratings, Apple privacy/age-rating/SDK minimums are versioned compliance evidence with effective dates and official provenance.
- External device providers are optional; credentials, billing/quota and physical-device availability are not global phase prerequisites.

## R13.1 execution authority

- Authorized base normalized `main`: **`aef297e385dc49ad6ae0935d4f9ef25a35e5e984`**.
- Dedicated branch: `r13/01-mobile-contracts`.
- Manual state: **NONE**.
- Start status synchronization: **DONE before implementation**; `R13_PLAN.md` phase `IN PROGRESS`, R13.1 `IN_PROGRESS`, R13.2–R13.17 `PLANNED`.
- Frozen scope: framework-neutral mobile target/toolchain/device/test/release contracts; deterministic canonical identities/digests; capability states; allowlisted Android/Apple toolchain identities and roots; typed argv/environment builders; path-safe project/staging boundaries; no process launch in the boundary layer.
- Acceptance must reject traversal, symlink escape, executable substitution, raw-argv/environment injection and config-only manufactured `AVAILABLE`; deterministic schema round-trips; exact-head R0/full Python/KodeStudio UI.
- No R13.2 work before R13.1 merge + single continuity-only normalization.

## Frozen R13 subdivision index

| ID | Title | Status | Manual |
| --- | --- | --- | --- |
| R13.1 | Mobile contracts, identities, capability model + secure toolchain boundaries | IN_PROGRESS | NONE |
| R13.2 | Project DNA/KodeProduct mobile profiles + Project Wizard target selection | PLANNED | NONE |
| R13.3 | Android deterministic native scaffold + Kotlin/Compose shared app model | PLANNED | NONE |
| R13.4 | Android Gradle build/export, APK/AAB, manifest/resources/ABI validation | PLANNED | CONDITIONAL |
| R13.5 | Android signing states, keystore boundary + Play App Signing model | PLANNED | CONDITIONAL |
| R13.6 | Android emulator/device testing + adb/instrumentation adapter | PLANNED | CONDITIONAL |
| R13.7 | Google Play release tracks, metadata + policy/compliance readiness | PLANNED | CONDITIONAL |
| R13.8 | Apple platform/Xcode capability bridge + macOS execution boundary | PLANNED | CONDITIONAL |
| R13.9 | iOS/iPadOS SwiftUI/Xcode deterministic scaffold + shared app model | PLANNED | CONDITIONAL |
| R13.10 | Apple identity, entitlements, signing/provisioning, archive/export model | PLANNED | CONDITIONAL |
| R13.11 | iOS Simulator/XCTest, device/TestFlight evidence adapter | PLANNED | CONDITIONAL |
| R13.12 | DeviceLab provider-neutral matrices, physical/virtual routing + evidence | PLANNED | CONDITIONAL |
| R13.13 | KodeRelease versioning, release trains, promotion, rollout + rollback | PLANNED | NONE |
| R13.14 | Mobile diagnostics: logs, crash/ANR/test/performance bundles + redaction | PLANNED | CONDITIONAL |
| R13.15 | Current store compliance engine: privacy, ratings, permissions, SDK/policy evidence | PLANNED | NONE |
| R13.16 | CLI + KodeStudio Mobile/DeviceLab/Release workspace | PLANNED | NONE |
| R13.17 | Adversarial hardening + Android/iOS integrated release-readiness acceptance | PLANNED | CONDITIONAL |

### R13 phase DoD target

R13 is COMPLETE only when the existing Project Wizard creates accepted Android/iOS intent; a canonical Android project scaffolds/builds/tests with validated APK/AAB release state; a canonical iOS SwiftUI/Xcode project scaffolds/compiles/tests on accepted hosted macOS simulator evidence; DeviceLab/release/diagnostics/compliance evidence is truthful and provider-scoped; any triggered manual gate is reviewed; canonical `R13_INTEGRATED_ACCEPTANCE.json` has `status=pass`, `blockers=[]`; and the final R13 implementation/evidence merge is followed by exactly one accepted continuity-only normalization.

Actual public Play/App Store publication remains explicit user-controlled behavior, not an automatic core acceptance prerequisite.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + global KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence; R12 desktop/package/update authority remain in force. Structured APIs only. Network off by default. No arbitrary shell/Gradle/Xcode/store commands. Missing evidence never manufactures PASS.

## R13 execution rule

Each subdivision: dedicated branch from normalized `main` -> start plan+continuity status sync -> implementation + focused tests -> exact-head standard/platform gates -> truthful manual state -> end plan+continuity status sync -> fresh evidence/re-gates if bytes changed -> merge with `expected_head_sha` -> exactly one continuity-only post-merge normalization + exact-head gates + merge -> only then next subdivision.

If a CONDITIONAL manual gate triggers, stop before the next subdivision and provide bounded prerequisites, exact commands/actions, expected evidence and recovery/privacy instructions. Never request passwords/private keys/tokens in chat.

## Next authorized action

**R13.1 only:** implement mobile contracts/identities/capability reports and the secure toolchain boundary on `r13/01-mobile-contracts`; add focused tests, schemas, design and acceptance docs; freeze one exact implementation head; require exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke; if accepted, perform end status sync and final re-gates, merge with expected SHA, then exactly one continuity-only post-merge normalization and its exact-head gates. Do not start R13.2 before that normalization merges.