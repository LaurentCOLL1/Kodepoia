# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R12 COMPLETE + NORMALIZED. R13 planning ACCEPTED + NORMALIZED. R13.1–R13.3 COMPLETE + NORMALIZED. R13.4 COMPLETE, post-merge continuity normalization in progress.** R13.4 accepted implementation candidate `0a58fd4e2f255786fe10ed00b7665ea49773d52b` passed R0 #1636 / `32888926818`, Python #1610 / `32888926891`, UI #1577 / `32888926909`, and Android Build #38 / `32888926881`; final end-synchronized head `c479d429540b4941d96d3fcc39b8d85561917750` passed R0 #1638 / `32890540226`, Python #1612 / `32890540400`, UI #1579 / `32890540232`, and Android Build #42 / `32890540329`; PR #227 merged with expected head as `b212ae166ee7eceac59ef3c39d56272acfdfdfa6`. Manual remained CONDITIONAL / NOT TRIGGERED. The sole authorized action is exact-head normalization gating and merge of `r13/04-continuity-normalization`; R13.5 remains PLANNED until that normalization merges.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : **frozen**.
- R1–R12 : **COMPLETE + NORMALIZED**.
- R12 canonical integrated digest: `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R13 planning : **ACCEPTED + NORMALIZED**.
- R13 phase status: **IN PROGRESS**.
- R13.1–R13.3: **COMPLETE + NORMALIZED**.
- R13.4: **COMPLETE**, implementation merged; continuity-only normalization in progress; manual **CONDITIONAL / NOT TRIGGERED**.
- R13.5–R13.17: **PLANNED / NOT STARTED**.
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

R13 is exactly **Mobile / Platform / Release**: Android export/signing/AAB/APK/device tests/store; interface iOS/Mac/Xcode; DeviceLab; KodeRelease/Updater/Diagnostics; current compliance. R14 backend/live-service work remains outside R13.

### Accepted planning and normalization

- planning candidate `6f44e8faf8ef675dab5c8079541ce436ff55b4b2` passed R0 #1596 / `32846530810`, Python #1570 / `32846530804`, UI #1537 / `32846530786`;
- PR #219 merged as `9a5c678c226cb845c639b914e6365b475ab20e86`;
- planning normalization `b7ca326ac6f9fbb74bdbe69fefe6faf4aaadf653` passed R0 #1598 / `32846946552`, Python #1572 / `32846946574`, UI #1539 / `32846946557`;
- PR #220 merged as `aef297e385dc49ad6ae0935d4f9ef25a35e5e984`.
- Therefore R13 planning is **ACCEPTED + NORMALIZED**.

### Current external baseline — date-aware, not architecture constants

- Google Play: new apps/updates must target Android 16 / API 36 from **2026-08-31**; R13 store-ready acceptance starts at API 36.
- Android Compose/AGP/compileSdk values are capability-probed and versioned; mutable ecosystem versions are not frozen architecture constants.
- Google Play publication uses Android App Bundle for new apps; upload-key and Play App Signing key states remain separate; production secrets never enter repo/evidence/argv.
- Apple App Store Connect production uploads require Xcode 26+ with iOS/iPadOS 26 SDK+ since 2026-04-28; beta/TestFlight state is distinct from stable production state.
- External device providers are optional; credentials, billing/quota and physical-device availability are not global phase prerequisites.

## R13.1 closure authority

- R13.1 accepted source **`04bee35bba58645f6ef91e8cf5530b5062c6803d`**; PR #221 merged as `029a49e4d6772b2870357e0327acf470ef40e03b`; normalization PR #222 merged as `a63c25e0bb7dfa4f45c87f61f20de9477a64935a`.
- Therefore R13.1 is **COMPLETE + NORMALIZED**.

## R13.2 closure authority

- R13.2 accepted candidate **`27b75959e3240f67330d901c3b4a084242ae28b0`**; final head `3cc31e2ca367bfe97866f4e33a106e9d4c0da870`; PR #223 merged as `12d55b5ed94527b619f4f8259d4443dd6e71931c`; normalization PR #224 merged as **`4a4985b58f449fb1bc1b2a455a41255d40fccfac`**.
- Therefore R13.2 is **COMPLETE + NORMALIZED**.

## R13.3 closure authority

- Authorized base: `4a4985b58f449fb1bc1b2a455a41255d40fccfac`.
- Accepted candidate **`73d9024a1b06711885296775cb9f51370b52c3d0`** passed R0 #1615 / `32880841487`, Python #1589 / `32880841447`, UI #1556 / `32880841420`.
- Final head **`954d907503e4fa92f7eccefd70bfe5f5808e4c11`** passed R0 #1617 / `32883252890`, Python #1591 / `32883252848`, UI #1558 / `32883252862`.
- PR #225 merged as **`e153b5d84d235b529fd8f522315467c766087b92`**.
- Continuity-only normalization **`a5ddc4eacd2eaf4a78dfb4de7224a151d036b5e7`** passed R0 #1619 / `32883829735`, Python #1593 / `32883829471`, UI #1560 / `32883829356`; PR #226 merged as normalized `main` **`634e75cbdc0b05974781b40beecf54ad85766ed8`**.
- Therefore R13.3 is authoritatively **COMPLETE + NORMALIZED**.

## R13.4 closure authority

- Authorized normalized base: **`634e75cbdc0b05974781b40beecf54ad85766ed8`**.
- Dedicated implementation branch: **`r13/04-android-build-export`**; PR #227.
- Manual state: **CONDITIONAL / NOT TRIGGERED**. Hosted CI proved the frozen build/package semantics; no user-machine SDK install, production signing key, Play account or physical Android device was required for R13.4 core acceptance.
- Rejected candidate `8c8e8dc2877f3a8de62d5e2b9fb19197f6b8a24c` failed because the hosted stable SDK manager could not provision API 37; rejected candidate `2d542963978c6eeb2c2ee7284686835f6e1323a9` failed due an ambiguous version-catalog matcher. Their evidence is not reused.
- Accepted implementation candidate **`0a58fd4e2f255786fe10ed00b7665ea49773d52b`** passed R0 #1636 / `32888926818`, Python #1610 / `32888926891`, UI #1577 / `32888926909`, and R13 Android Build Acceptance #38 / `32888926881`.
- Android Build Acceptance #38 succeeded on both `android-build-ubuntu-latest` and `android-build-windows-latest`, provisioning JDK 17, Gradle 9.5.0, Android platform 36/Build Tools 36.0.0, building fixed unit tests/debug APK/release AAB and validating exact-head evidence.
- Final end-synchronized head **`c479d429540b4941d96d3fcc39b8d85561917750`** changed only `docs/roadmap/R13_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` relative to the accepted implementation candidate, then passed R0 #1638 / `32890540226`, Python #1612 / `32890540400`, UI #1579 / `32890540232`, and R13 Android Build Acceptance #42 / `32890540329`; triggered R12 regression workflows also passed.
- PR #227 merged with `expected_head_sha=c479d429540b4941d96d3fcc39b8d85561917750` as **`b212ae166ee7eceac59ef3c39d56272acfdfdfa6`**.
- Scope delivered: bounded JDK/Gradle/Android SDK discovery and fixed build/export tasks; exact R13.3 source-manifest verification; isolated compatibility staging overlay; APK/AAB inspection; manifest/resources/ABI validation; lineage/budget evidence; hosted API 36 build/package proof.
- Single post-merge normalization branch: **`r13/04-continuity-normalization`**, created exactly from merged `main` `b212ae166ee7eceac59ef3c39d56272acfdfdfa6`. It must remain continuity-only and pass exact-head R0/Python/UI before merge. Only then is R13.4 **COMPLETE + NORMALIZED** and R13.5 authorized.

## Frozen R13 subdivision index

| ID | Title | Status | Manual |
| --- | --- | --- | --- |
| R13.1 | Mobile contracts, identities, capability model + secure toolchain boundaries | COMPLETE | NONE |
| R13.2 | Project DNA/KodeProduct mobile profiles + Project Wizard target selection | COMPLETE | NONE |
| R13.3 | Android deterministic native scaffold + Kotlin/Compose shared app model | COMPLETE | NONE |
| R13.4 | Android Gradle build/export, APK/AAB, manifest/resources/ABI validation | COMPLETE | CONDITIONAL |
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

**R13.4 continuity normalization:** require exact-head R0/full Python/KodeStudio UI on `r13/04-continuity-normalization`; if all are SUCCESS, merge its one-file PR with `expected_head_sha`. Only after that merge may `r13/05-android-signing` be created exactly from normalized `main`, followed immediately by the R13.5 start plan+continuity synchronization before any implementation.