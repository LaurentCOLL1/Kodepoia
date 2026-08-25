# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R12 COMPLETE + NORMALIZED. R13 planning ACCEPTED + NORMALIZED. R13.1–R13.2 COMPLETE + NORMALIZED. R13.3 COMPLETE, post-merge normalization in progress.** R13.3 accepted candidate `73d9024a1b06711885296775cb9f51370b52c3d0` passed R0 #1615 / `32880841487`, Python #1589 / `32880841447`, UI #1556 / `32880841420`; final end-synchronized head `954d907503e4fa92f7eccefd70bfe5f5808e4c11` passed R0 #1617 / `32883252890`, Python #1591 / `32883252848`, UI #1558 / `32883252862`; PR #225 merged as `e153b5d84d235b529fd8f522315467c766087b92`. The sole authorized action is this continuity-only normalization; R13.4 remains PLANNED until its exact-head R0/Python/UI gates pass and it merges.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : **frozen**.
- R1–R12 : **COMPLETE + NORMALIZED**.
- R12 canonical integrated digest: `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R13 planning : **ACCEPTED + NORMALIZED**.
- R13 phase status: **IN PROGRESS**.
- R13.1–R13.2: **COMPLETE + NORMALIZED**, manual **NONE**.
- R13.3: **COMPLETE**, implementation merged; continuity-only normalization in progress, manual **NONE**.
- R13.4–R13.17: **PLANNED / NOT STARTED**.
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
- PR #220 merged as `aef297e385dc49ad6ae0935d4f9ef25a35e5e984`.
- Therefore R13 planning is **ACCEPTED + NORMALIZED**.

### Current external baseline — date-aware, not architecture constants

- Google Play: new apps/updates must target Android 16 / API 36 from **2026-08-31**; R13 store-ready acceptance starts at API 36.
- Android Compose/AGP/compileSdk values are capability-probed and versioned; mutable ecosystem versions are not frozen architecture constants.
- Google Play publication uses Android App Bundle for new apps; upload-key and Play App Signing key states remain separate; production secrets never enter repo/evidence/argv.
- Apple App Store Connect production uploads require Xcode 26+ with iOS/iPadOS 26 SDK+ since 2026-04-28; beta/TestFlight state is distinct from stable production state.
- Apple privacy manifests/required-reason APIs, Google Play Data safety, target API, permissions/content ratings, Apple privacy/age-rating/SDK minimums are versioned compliance evidence with effective dates and official provenance.
- External device providers are optional; credentials, billing/quota and physical-device availability are not global phase prerequisites.

## R13.1 closure authority

- Authorized base normalized `main`: `aef297e385dc49ad6ae0935d4f9ef25a35e5e984`.
- Dedicated branch: `r13/01-mobile-contracts`; PR #221.
- Manual state: **NONE**.
- Accepted implementation source: **`04bee35bba58645f6ef91e8cf5530b5062c6803d`**.
- Final end-synchronized head: **`a20ff45bc62e578c3aa58c8ef41927b08bfe2d2a`**.
- PR #221 merged as **`029a49e4d6772b2870357e0327acf470ef40e03b`**.
- Single normalization head: **`3bc39e88391d05cc97992881fdb8c0ba61f49457`**; PR #222 merged as normalized `main` **`a63c25e0bb7dfa4f45c87f61f20de9477a64935a`**.
- Therefore R13.1 is authoritatively **COMPLETE + NORMALIZED**.

## R13.2 closure authority

- Authorized base normalized `main`: **`a63c25e0bb7dfa4f45c87f61f20de9477a64935a`**.
- Dedicated implementation branch: `r13/02-mobile-profiles`; PR #223.
- Manual state: **NONE**.
- Rejected candidates `9c8820aaa8d75e88b48b6a3ed730a7e724b16605` and `4e48fc7520351b3d7445130ee691dca9d1b402c0` are not evidence.
- Accepted implementation candidate **`27b75959e3240f67330d901c3b4a084242ae28b0`** passed R0 #1609 / `32876034828`, Python #1583 / `32876034855`, UI #1550 / `32876034882`.
- Final end-synchronized head **`3cc31e2ca367bfe97866f4e33a106e9d4c0da870`** passed R0 #1611 / `32878929674`, Python #1585 / `32878929659`, UI #1552 / `32878929665`.
- PR #223 merged as **`12d55b5ed94527b619f4f8259d4443dd6e71931c`**.
- Continuity-only normalization head **`90eec4db1c9a8546abfa4c2046f162c48001c817`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1613 / `32879324825`, Python #1587 / `32879324859`, UI #1554 / `32879325025`, and PR #224 merged as normalized `main` **`4a4985b58f449fb1bc1b2a455a41255d40fccfac`**.
- Therefore R13.2 is authoritatively **COMPLETE + NORMALIZED**.

## R13.3 closure authority

- Authorized normalized base: **`4a4985b58f449fb1bc1b2a455a41255d40fccfac`**.
- Dedicated branch: **`r13/03-android-scaffold`**; PR #225.
- Manual state: **NONE**.
- Accepted implementation candidate **`73d9024a1b06711885296775cb9f51370b52c3d0`** passed R0 #1615 / `32880841487`, Python #1589 / `32880841447`, UI #1556 / `32880841420`.
- Final end-synchronized head **`954d907503e4fa92f7eccefd70bfe5f5808e4c11`** passed R0 #1617 / `32883252890`, Python #1591 / `32883252848`, UI #1558 / `32883252862`.
- PR #225 merged with the expected head as **`e153b5d84d235b529fd8f522315467c766087b92`**.
- Scope delivered: deterministic repository-owned Android scaffold from accepted mobile DNA/Product and shared app contracts; Gradle Kotlin DSL, version catalog, Compose projection, application/package normalization, manifest/resources/localization, adaptive/accessibility baseline, explicit dependency evidence, semantic workspace manifest, generated/user ownership, SafeChange/backup/audit regeneration.
- No Gradle/JDK/SDK process, signing, device or store claim belongs to R13.3.
- Single post-merge branch: **`r13/03-continuity-normalization`**. It must remain continuity-only and pass exact-head R0/Python/UI before merge. Only then is R13.3 **COMPLETE + NORMALIZED** and R13.4 authorized.

## Frozen R13 subdivision index

| ID | Title | Status | Manual |
| --- | --- | --- | --- |
| R13.1 | Mobile contracts, identities, capability model + secure toolchain boundaries | COMPLETE | NONE |
| R13.2 | Project DNA/KodeProduct mobile profiles + Project Wizard target selection | COMPLETE | NONE |
| R13.3 | Android deterministic native scaffold + Kotlin/Compose shared app model | COMPLETE | NONE |
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

**R13.3 normalization:** require exact-head R0/full Python/KodeStudio UI on `r13/03-continuity-normalization`; if all are SUCCESS, merge that one-file PR with `expected_head_sha`, then create `r13/04-android-build-export` exactly from normalized `main` and perform R13.4 start plan+continuity synchronization before implementation.