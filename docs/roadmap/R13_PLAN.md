# Kodepoia — R13 detailed phase plan

**Phase:** R13  
**Roadmap title:** Mobile / Platform / Release  
**Status:** IN PROGRESS  
**Phase planning started:** 2026-08-25  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `997db5a5ad9f847037de79057bcdc7aefd1ddeb9`  
**Execution checkpoint:** R13.1–R13.3 `COMPLETE + NORMALIZED`; R13.4 `COMPLETE` on its dedicated branch after exact-head acceptance of `0a58fd4e2f255786fe10ed00b7665ea49773d52b`, manual `CONDITIONAL / NOT TRIGGERED`; R13.5 remains `PLANNED` until R13.4 merge and continuity-only normalization complete.

## Purpose and authority

R13 implements the frozen-roadmap capability **“Android export/signing/AAB/APK/device tests/store; interface iOS/Mac/Xcode; DeviceLab; KodeRelease/Updater/Diagnostics and current compliance.”** It extends, and does not replace, the accepted R1–R12 foundations.

This plan is the exhaustive execution and recovery authority for R13. The subdivision list R13.1–R13.17 became frozen when the planning PR and its single normalization were accepted and merged. No subdivision may be silently added, removed, merged, split, or renumbered. Any scope/status/manual-state change must update this file and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle; any change to a frozen R1–R12 architecture boundary requires an ADR.

R13 planning is **ACCEPTED + NORMALIZED** on `main` `aef297e385dc49ad6ae0935d4f9ef25a35e5e984`; R13.1–R13.3 are **COMPLETE + NORMALIZED**; R13.4 is **COMPLETE / NOT NORMALIZED** pending final documentation re-gates, merge and its single continuity-only normalization; R13.5 remains **PLANNED**.

## Permanent subdivision status synchronization rule

The phase plan is live execution authority. For every R13 subdivision:

1. **Start, before implementation:** set prior normalized subdivisions to `COMPLETE`, active subdivision to `IN_PROGRESS`, later subdivisions to `PLANNED`; update the phase-level status/checkpoint and synchronize continuity in the same work cycle.
2. **End, before final evidence/documentation re-gates:** set the accepted active subdivision to `COMPLETE`; later subdivisions stay `PLANNED`; synchronize continuity in the same work cycle.
3. A triggered manual gate uses truthful `BLOCKED` / `MANUAL_REQUIRED`, never synthetic `COMPLETE`.
4. Post-merge normalization is continuity-only and MUST NOT rewrite the phase-plan status.
5. A stale subdivision index or phase status is an acceptance blocker.

## Phase objective

Deliver a deterministic, auditable, local-first mobile/platform release pipeline that lets Kodepoia:

- extend Project DNA, KodeProduct and the existing Project Wizard with Android/iOS mobile target intent;
- generate governed native Android projects and Apple Xcode projects without arbitrary shell/template execution;
- build, package, test and inspect Android APK/AAB artifacts on accepted toolchains;
- model Android signing, Play App Signing/upload-key separation and store-ready release state without exposing secrets;
- generate and validate iOS/iPadOS SwiftUI/Xcode projects and compile/test them on accepted macOS/Xcode CI where possible;
- model Apple bundle identity, entitlements, signing/provisioning/archive/export/TestFlight/App Store states without requiring production credentials for ordinary acceptance;
- provide a provider-neutral `DeviceLab` across local emulators/simulators, hosted CI and optional external physical-device providers;
- add `KodeRelease` release trains, version/build numbering, immutable artifact promotion, staged channels, rollback and provenance;
- add release/update semantics that respect platform rules: no silent self-updating executable on iOS, no store-bypass behavior, and no hidden installer actions;
- collect structured mobile diagnostics (logs, crashes, ANRs, test failures, performance/device metadata) without leaking secrets or user data;
- continuously validate current Google Play and Apple App Store compliance data as versioned evidence with effective dates and official-source provenance;
- expose mobile/release workflows through structured CLI and KodeStudio surfaces;
- close R13 with adversarial cross-platform integrated acceptance tied to exact-head evidence.

## Explicitly out of scope

R13 does **not** implement R14 backend/live services: authoritative auth, cloud database, matchmaking/lobbies, cloud saves, achievements/entitlements/billing backends, remote config, feature flags, content-delivery services or event pipelines remain R14. R13 may model store metadata or client-side capability declarations but cannot silently create a backend.

Also out of scope unless separately accepted by ADR: Flutter/React Native as new primary frameworks; arbitrary package-manager scripts; model-supplied Gradle/Xcode flags; automatic production store publication; unattended certificate/key creation; Apple notarization for non-mobile macOS distribution beyond the interface needed by this roadmap phase; bypassing App Store/Play policies; self-modifying mobile binaries; mandatory paid cloud accounts for core acceptance.

## Current external compatibility baseline — 2026-08-25

External requirements are **versioned/effective-date evidence**, not permanent architecture constants. R13 must capability-probe tools and evaluate current compliance rules rather than hard-coding one mutable ecosystem version forever.

### Android / Google Play

- Google Play requires new apps and updates to target **Android 16 / API 36 or later starting 2026-08-31**. Because that deadline is six days after phase planning, the R13 store-ready acceptance baseline is API 36 from the outset; lower targets cannot be promoted as store-ready merely because they were technically accepted before the deadline.
- Current Jetpack Compose stable BOM is `2026.08.00`; Compose 1.12 requires `compileSdk 37` and Android Gradle Plugin 9.x, with current Android guidance identifying AGP 9.1.2 as the compatible floor for the August 2026 release. R13 must probe actual supported stable toolchains rather than freeze those values as eternal architecture.
- New Google Play apps use Android App Bundle (`.aab`) as the publication format. APK remains a valid install/test/export artifact where applicable.
- Android artifacts must be signed before install/update. A Play App Bundle is signed with an upload key before upload; Play App Signing manages the distribution signing key when enabled. Production keys/tokens never enter Project DNA, source control, logs, acceptance reports or raw argv.
- Google Play Data safety/user-data declarations must reflect app and third-party SDK behavior. Target API, sensitive-permission policy, content rating and other policy requirements are date-aware compliance inputs.

Official planning references:

- https://support.google.com/googleplay/android-developer/answer/11926878
- https://developer.android.com/google/play/requirements/target-sdk
- https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler
- https://developer.android.com/guide/app-bundle
- https://developer.android.com/studio/publish/app-signing
- https://support.google.com/googleplay/android-developer/answer/10144311

### Apple / Xcode / App Store Connect

- Since 2026-04-28, App Store Connect uploads must be built with **Xcode 26 or later** using the iOS/iPadOS 26 SDK or later. Stable production capability and beta/TestFlight capability must remain distinct.
- Xcode 27 beta builds are currently accepted for TestFlight testing, but beta acceptance does not manufacture a production App Store-ready claim.
- SwiftUI remains declarative and architecture-agnostic; R13 maps existing Kodepoia state/navigation/service contracts rather than inventing a second global architecture.
- Apps/SDKs using covered required-reason APIs must declare approved reasons in `PrivacyInfo.xcprivacy`; privacy manifests are first-class generated/validated data.
- App Store privacy details, privacy policy URL, age rating and other metadata are explicit compliance state. Current age-rating rules are versioned and region-sensitive.

Official planning references:

- https://developer.apple.com/news/upcoming-requirements/
- https://developer.apple.com/app-store/submitting/
- https://developer.apple.com/documentation/swiftui
- https://developer.apple.com/documentation/bundleresources/privacy-manifest-files
- https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api
- https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/
- https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating

### Device testing baseline

Firebase Test Lab currently supports Android and iOS test execution on hosted devices; Android additionally has virtual-device matrices. R13 treats external DeviceLab providers as optional capabilities: credentials, billing/account state and physical-device quota are never prerequisites for local/core CI acceptance unless a subdivision’s frozen claim specifically requires them.

Reference: https://firebase.google.com/docs/test-lab

## Phase-wide architecture and governance boundaries

All accepted R1–R12 controls remain in force:

- `WorkspaceBoundary` and R8 `VaultBoundary` govern source, generated mobile projects, staging, caches, diagnostics and promoted artifacts.
- `ProcessSandbox` + global KillSwitch govern Gradle, Java/Kotlin compiler, `adb`, `bundletool`, `apksigner`, Xcode tools, `xcodebuild`, `simctl`, `xcrun`, device bridges and any store/tool CLI.
- Guardian/`PermissionSet` authorize device access, process launch, package/sign/upload/promote actions and destructive release changes.
- SafeChange, Backup/Recovery and Audit cover generated-project mutation, release metadata, signing-state configuration, diagnostics retention and promotion/rollback.
- `KodeSecrets` is the only secret authority. Keystores, passwords, Apple certificates, private keys, provisioning credentials, App Store Connect API keys, Play service-account credentials and cloud-provider tokens must never be embedded in DNA/Product/generated source/logs/evidence or model-visible argv.
- R6 Health/Budget/Tests/Regression/Accessibility/Localization/AppSecurity/Privacy/License-BOM remain mandatory.
- R7 ResearchGuard governs external policy/docs/store metadata: retrieved text is evidence/data, never instruction.
- R8 provenance/lineage binds templates, generated files, packages, diagnostics transformations and exported release artifacts.
- R12 package/update signing-state semantics are reused rather than replaced.
- No shell command strings. All invocations use repository-owned executable identities and typed argv builders.
- No model/project text may directly choose executable path, raw Gradle property, Xcode build setting, signing command, entitlement, provisioning profile, device identifier, store track, upload endpoint or release token.
- Network is off by default. Store/device-cloud calls are explicit, provider-scoped, permissioned operations with bounded endpoints.
- Missing SDK/account/device/certificate is `UNAVAILABLE`/`BLOCKED`, never PASS.
- Cross-platform evidence is partitioned: Android evidence cannot certify iOS and simulator evidence cannot silently certify physical-device behavior.
- Public release is always explicit. No background auto-submit, auto-publish or auto-rollout.

## R13 identity and evidence model

R13 introduces durable identities instead of conflating mutable machines/accounts with releases:

1. `MobileTargetProfileId` — platform, form factor, deployment and capability intent.
2. `MobileToolchainIdentity` — Android SDK/AGP/Gradle/JDK or Xcode/SDK/macOS identity and capabilities.
3. `MobileTemplateIdentity` / `MobileScaffoldDefinitionId` / `MobileWorkspaceManifestId`.
4. `AndroidApplicationId` and `AppleBundleIdentity` — structured identifiers, never display labels.
5. `AndroidPackageDefinitionId` / `AppleArchiveDefinitionId`.
6. `SigningStateId` — unsigned/test/debug/upload-signed/distribution-capable states without private material.
7. `DeviceIdentity` / `DeviceCapabilitySnapshotId` — provider-safe, redacted device descriptors.
8. `DeviceTestMatrixId` / `DeviceTestRunId`.
9. `StoreComplianceSnapshotId` — source/effective-date/rule-set digest.
10. `StoreListingDefinitionId` and provider-specific release metadata identities.
11. `ReleaseTrainId`, `ReleaseCandidateId`, `PromotionId`, `RollbackPointId`.
12. `MobileDiagnosticBundleId` / `CrashFingerprintId` / `ANRFingerprintId`.
13. `R13IntegratedEvidenceDigest` — anti-circular phase evidence identity.

## Mobile/release budget model

R13 extends R6 Budget with bounded metrics: source/generated-file count and bytes, Gradle/Xcode configure/build/test wall time, APK/AAB/IPA/archive bytes, install/test wall time, device-matrix count/cost quota, emulator/simulator boot time, startup time where safely measurable, memory/CPU/battery/network observations where supported, diagnostics bytes/retention, crash/ANR counts, permission/compliance issue counts, signing/promotion latency, release artifact retention and rollback storage.

Budget overrun is explicit `BUDGET_EXCEEDED`, not PASS.

## Global prerequisites

Before R13.1 implementation:

- R1–R12 are `COMPLETE + NORMALIZED` on `main`.
- canonical R12 integrated acceptance remains `status=pass` with semantic digest `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R13 planning PR and its single continuity-only planning normalization are merged.
- Python baseline remains 3.12.x unless separately changed by accepted ADR/phase decision.
- hosted CI may provision public SDK/toolchain dependencies as CI infrastructure, but Kodepoia runtime may not silently install toolchains.
- production Google/Apple accounts, signing keys and paid physical-device cloud access are **not** global prerequisites; subdivisions declare conditional gates when a claim truly requires them.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R13.1 | Mobile contracts, identities, capability model + secure toolchain boundaries | COMPLETE | NONE | R12 COMPLETE + normalized planning |
| R13.2 | Project DNA/KodeProduct mobile profiles + Project Wizard target selection | COMPLETE | NONE | R13.1 + R2 |
| R13.3 | Android deterministic native scaffold + Kotlin/Compose shared app model | COMPLETE | NONE | R13.1–R13.2 + R8/R12 patterns |
| R13.4 | Android Gradle build/export, APK/AAB, manifest/resources/ABI validation | COMPLETE | CONDITIONAL | R13.1–R13.3 + R6 |
| R13.5 | Android signing states, keystore boundary + Play App Signing model | PLANNED | CONDITIONAL | R13.4 + R1/R6/R12 |
| R13.6 | Android emulator/device testing + adb/instrumentation adapter | PLANNED | CONDITIONAL | R13.4–R13.5 |
| R13.7 | Google Play release tracks, metadata + policy/compliance readiness | PLANNED | CONDITIONAL | R13.4–R13.6 + R7 |
| R13.8 | Apple platform/Xcode capability bridge + macOS execution boundary | PLANNED | CONDITIONAL | R13.1–R13.2 + R6 |
| R13.9 | iOS/iPadOS SwiftUI/Xcode deterministic scaffold + shared app model | PLANNED | CONDITIONAL | R13.8 + R8/R12 patterns |
| R13.10 | Apple identity, entitlements, signing/provisioning, archive/export model | PLANNED | CONDITIONAL | R13.8–R13.9 + R1/R6/R12 |
| R13.11 | iOS Simulator/XCTest, device/TestFlight evidence adapter | PLANNED | CONDITIONAL | R13.9–R13.10 |
| R13.12 | DeviceLab provider-neutral matrices, physical/virtual routing + evidence | PLANNED | CONDITIONAL | R13.6 + R13.11 |
| R13.13 | KodeRelease versioning, release trains, promotion, rollout + rollback | PLANNED | NONE | R13.4–R13.12 + R8/R12 |
| R13.14 | Mobile diagnostics: logs, crash/ANR/test/performance bundles + redaction | PLANNED | CONDITIONAL | R13.6/R13.11/R13.12 + R6 |
| R13.15 | Current store compliance engine: privacy, ratings, permissions, SDK/policy evidence | PLANNED | NONE | R13.7/R13.10 + R7/R6 |
| R13.16 | CLI + KodeStudio Mobile/DeviceLab/Release workspace | PLANNED | NONE | R13.1–R13.15 |
| R13.17 | Adversarial hardening + Android/iOS integrated release-readiness acceptance | PLANNED | CONDITIONAL | R13.1–R13.16 + R6/R8/R12 evidence |

---

# R13.1 — Mobile contracts, identities, capability model + secure toolchain boundaries

**Objective.** Establish framework-neutral mobile/release contracts before any external tool is invoked.

**Deliver:** versioned schemas/models for targets, toolchains, package/archive state, device identity, test matrices, store/release status; strict platform enums; structured tool discovery; allowlisted executables/roots; typed argv/environment builders; path-safe staging/output boundaries; capability states `NOT_PROBED/AVAILABLE/UNAVAILABLE/UNSUPPORTED/BLOCKED/FAILED`.

**Acceptance:** traversal/symlink/executable substitution/raw-argv/env injection rejected; capability cannot become AVAILABLE from config text alone; schema round-trips deterministic; R0 + full Python + KodeStudio UI exact-head gates.

**Manual:** NONE.

**Completion record:** accepted implementation source `04bee35bba58645f6ef91e8cf5530b5062c6803d`; rejected predecessor `97e3f0a48be3a888b0f2974e04bcf1317f3e6296` is not reused. Candidate gates R0 #1601 / `32849189652`, Python #1575 / `32849189637`, UI #1542 / `32849189598`; final end-synchronized head `a20ff45bc62e578c3aa58c8ef41927b08bfe2d2a` passed R0 #1603 / `32849778906`, Python #1577 / `32849779035`, UI #1544 / `32849778909`; PR #221 merged as `029a49e4d6772b2870357e0327acf470ef40e03b`; continuity-only normalization `3bc39e88391d05cc97992881fdb8c0ba61f49457` passed R0 #1605 / `32873745343`, Python #1579 / `32873745171`, UI #1546 / `32873745103`, and PR #222 merged as normalized `main` `a63c25e0bb7dfa4f45c87f61f20de9477a64935a`. R13.1 is **COMPLETE + NORMALIZED**.

# R13.2 — Project DNA/KodeProduct mobile profiles + Project Wizard target selection

**Objective.** Extend existing Wizard/DNA/Product rather than creating a parallel mobile wizard.

**Deliver:** backward-compatible mobile profile fields for Android/iOS, minimum/target OS/API intent, form factor, native-app vs Godot-export source, permissions/capabilities, offline/network intent, package/release channel, signing intent and budgets; conditional Wizard controls; game-only/mobile-app-only fields remain properly gated.

**Acceptance:** legacy DNA round-trips without drift; impossible platform/source/framework combinations fail; mobile selection creates intent only, no SDK install/build; UI accessibility/localization/pseudo-localization tests; exact-head gates.

**Manual:** NONE.

**Completion record:** rejected candidate `9c8820aaa8d75e88b48b6a3ed730a7e724b16605` failed R0 #1607 / `32875664321` because `schemas/project-dna-v1.schema.json` was invalid JSON; no evidence from that head is reused. Rejected candidate `4e48fc7520351b3d7445130ee691dca9d1b402c0` fixed the schema but failed the Python/UI smoke because the first R13 `app.py` integration regressed the accepted pseudo-localized navigation minimum width; no evidence from that head is reused. Accepted implementation candidate **`27b75959e3240f67330d901c3b4a084242ae28b0`** passed R0 #1609 / `32876034828`, Python #1583 / `32876034855`, UI #1550 / `32876034882`; final end-synchronized head **`3cc31e2ca367bfe97866f4e33a106e9d4c0da870`** passed R0 #1611 / `32878929674`, Python #1585 / `32878929659`, UI #1552 / `32878929665`; PR #223 merged as `12d55b5ed94527b619f4f8259d4443dd6e71931c`. Continuity-only normalization **`90eec4db1c9a8546abfa4c2046f162c48001c817`** passed R0 #1613 / `32879324825`, Python #1587 / `32879324859`, UI #1554 / `32879325025`; PR #224 merged as normalized `main` **`4a4985b58f449fb1bc1b2a455a41255d40fccfac`**. R13.2 is **COMPLETE + NORMALIZED**.

# R13.3 — Android deterministic native scaffold + Kotlin/Compose shared app model

**Objective.** Generate a repository-owned Android project from mobile DNA/Product and existing shared app contracts.

**Deliver:** deterministic Gradle Kotlin DSL project, Kotlin/Compose UI mapping, package/application ID normalization, resources/localization, manifest generation, adaptive layout/accessibility baseline, locked dependency catalog/BOM identity, user-owned/generated-region policy, Godot Android export bridge definition without replacing R5.

**Acceptance:** identical definition -> identical semantic workspace manifest; path/resource/identifier/template injection rejected; no arbitrary Gradle script execution during render; current stable Compose dependency set represented by capability evidence, not mutable unbounded `latest`; exact-head gates.

**Manual:** NONE.

**Completion record:** accepted implementation candidate **`73d9024a1b06711885296775cb9f51370b52c3d0`** passed R0 #1615 / `32880841487`, Python #1589 / `32880841447`, UI #1556 / `32880841420`; final end-synchronized head **`954d907503e4fa92f7eccefd70bfe5f5808e4c11`** passed R0 #1617 / `32883252890`, Python #1591 / `32883252848`, UI #1558 / `32883252862`; PR #225 merged as `e153b5d84d235b529fd8f522315467c766087b92`. Continuity-only normalization **`a5ddc4eacd2eaf4a78dfb4de7224a151d036b5e7`** passed R0 #1619 / `32883829735`, Python #1593 / `32883829471`, UI #1560 / `32883829356`; PR #226 merged as normalized `main` **`634e75cbdc0b05974781b40beecf54ad85766ed8`**. R13.3 is **COMPLETE + NORMALIZED**.

# R13.4 — Android Gradle build/export, APK/AAB, manifest/resources/ABI validation

**Objective.** Turn accepted Android workspaces into validated install/test and publication artifacts.

**Deliver:** bounded Gradle/JDK/SDK discovery; compileSdk/targetSdk/minSdk model; fixed build/test/export tasks; APK/AAB manifest and contents inspection; ABI/native-library matrix; bundletool/APK validation; build artifact lineage and budget evidence.

**Acceptance:** hosted Linux/Windows Android build where supported; store-ready fixture targets API 36+; canonical release AAB and test/install APK validate; missing/incompatible SDK is not PASS; dependency/Gradle property/env substitution attacks fail closed.

**Manual:** CONDITIONAL — only if a required real Android build/device semantic cannot be proven in accepted hosted CI. Toolchain installation on the user machine is never silently requested.

**Completion record:** accepted implementation candidate **`0a58fd4e2f255786fe10ed00b7665ea49773d52b`** passed R0 #1636 / `32888926818`, Python #1610 / `32888926891`, UI #1577 / `32888926909`, and R13 Android Build Acceptance #38 / `32888926881` with both `android-build-ubuntu-latest` and `android-build-windows-latest` SUCCESS. Manual state is **CONDITIONAL / NOT TRIGGERED** because the frozen hosted build/package claim was proven without user-machine tooling. End plan+continuity synchronization marks R13.4 COMPLETE; fresh exact-head R0/Python/UI/Android gates are required on the resulting documentation head before merge #227.

# R13.5 — Android signing states, keystore boundary + Play App Signing model

**Objective.** Model signing safely without normalizing secret exposure.

**Deliver:** signing states (`UNSIGNED`, `DEBUG_SIGNED`, `TEST_SIGNED`, `UPLOAD_SIGNED`, `PLAY_APP_SIGNING_READY`, `SIGNING_UNAVAILABLE`); certificate/public fingerprint evidence; keystore references through KodeSecrets; upload-key vs app-signing-key separation; key rotation/recovery metadata; no private material in reports.

**Acceptance:** APK/AAB unsigned/signed state detected truthfully; secret/path/password leakage tests; wrong certificate/substitution rejected; test keystore may be CI-generated and ephemeral; no production key required for phase acceptance.

**Manual:** CONDITIONAL — production upload/distribution signing requires user/account-owned credentials if that claim is explicitly requested; otherwise acceptance remains test-signing/state-model based.

# R13.6 — Android emulator/device testing + adb/instrumentation adapter

**Objective.** Provide governed test execution on Android runtime targets.

**Deliver:** device/emulator discovery, redacted device capability snapshot, fixed `adb`/instrumentation operations, install/uninstall/test/log collection, locale/orientation/density/network-profile matrix, timeout/cancellation, device lease/cleanup, emulator evidence.

**Acceptance:** hosted emulator or accepted equivalent runs canonical tests; stale/offline/wrong-device substitution fails; no arbitrary `adb shell`; KillSwitch cleanup leaves no owned test process; physical-only claims remain separate.

**Manual:** CONDITIONAL — only for hardware-only behavior unavailable in CI.

# R13.7 — Google Play release tracks, metadata + policy/compliance readiness

**Objective.** Model Google Play release preparation and optional controlled submission without auto-publishing.

**Deliver:** release-track model (internal/closed/open/production where applicable), staged rollout intent, AAB upload candidate identity, store listing/localizations/assets metadata, target-API effective-date rules, Data safety declaration model, content rating/permissions/SDK policy findings, Play App Signing readiness, optional API capability adapter with KodeSecrets.

**Acceptance:** API 36 deadline logic evaluated by effective date; stale policy snapshot cannot claim CURRENT; metadata/package mismatch and unsafe permission declarations block readiness; dry-run works with no Play account; public publish is never automatic.

**Manual:** CONDITIONAL — live Play Console/API account operations require explicit authorized credentials and may be omitted from core readiness acceptance.

# R13.8 — Apple platform/Xcode capability bridge + macOS execution boundary

**Objective.** Establish a truthful Mac/Xcode bridge for iOS/iPadOS work.

**Deliver:** Xcode/macOS/SDK/tool identity, `xcodebuild`/`xcrun`/`simctl` fixed invocation builders, simulator/device capabilities, stable-vs-beta channel state, remote/hosted mac executor contract, output/staging boundaries and cancellation.

**Acceptance:** hosted macOS CI capability probe proves supported Xcode/SDK state; beta toolchain cannot manufacture production-ready state; raw build settings/destination/command injection rejected.

**Manual:** CONDITIONAL — only if a required Xcode/device semantic cannot be demonstrated by accepted hosted macOS CI.

# R13.9 — iOS/iPadOS SwiftUI/Xcode deterministic scaffold + shared app model

**Objective.** Generate an Xcode project/workspace for iOS/iPadOS from the existing Wizard and shared state/navigation/service model.

**Deliver:** SwiftUI app/scene/view scaffold, Observation-compatible state mapping, bundle/resource/localization generation, deterministic project settings, asset catalogs, deployment-target intent, generated/user-owned file policy, optional Godot iOS Xcode-export bridge definition.

**Acceptance:** deterministic semantic manifest; hosted macOS Xcode build of canonical simulator fixture; project/bundle/path/build-setting injection rejected; no signing required for simulator compile/test.

**Manual:** CONDITIONAL only if hosted macOS cannot prove the frozen compile/test claim.

# R13.10 — Apple identity, entitlements, signing/provisioning, archive/export model

**Objective.** Model real Apple release prerequisites without storing or fabricating credentials.

**Deliver:** bundle/team/signing/provisioning state contracts, entitlement allowlist, capability-to-entitlement mapping, certificate/profile public identity, archive/export definition, signing readiness states, KodeSecrets references, privacy-manifest inclusion checks.

**Acceptance:** simulator build remains independent of production signing; wrong bundle/team/profile/entitlement substitution fails; secrets absent from argv/log/evidence; test fixtures validate archive/export metadata without claiming App Store acceptance.

**Manual:** CONDITIONAL — device/distribution signing or live archive export may require an Apple Developer account and user-owned credentials; phase acceptance does not require production secrets unless such a claim is explicitly frozen.

# R13.11 — iOS Simulator/XCTest, device/TestFlight evidence adapter

**Objective.** Execute structured Apple-platform tests and model optional TestFlight/device evidence.

**Deliver:** simulator creation/selection, XCTest plan/run parsing, install/launch where deterministic, logs/result bundles, device-vs-simulator partitioning, TestFlight build-state interface, optional App Store Connect capability adapter with explicit credentials.

**Acceptance:** canonical SwiftUI fixture compiles/tests on hosted macOS simulator; simulator evidence never certifies physical sensors/device-only behavior; TestFlight/live account state remains unavailable rather than synthetic when credentials are absent.

**Manual:** CONDITIONAL for required physical-device/TestFlight-only behavior not provable in CI.

# R13.12 — DeviceLab provider-neutral matrices, physical/virtual routing + evidence

**Objective.** Unify runtime test targets without binding Kodepoia to one vendor.

**Deliver:** provider-neutral DeviceLab contract; local Android emulator/ADB provider; Xcode Simulator provider; hosted CI provider; optional Firebase Test Lab provider for Android/iOS physical/virtual targets; matrix scheduling, quotas/cost budgets, retries, leases, result normalization, redaction and provenance.

**Acceptance:** deterministic provider selection; unavailable account/quota/device is explicit; matrix identity includes model/OS/locale/orientation; provider result cannot be replayed against a different artifact digest; no mandatory paid account for core acceptance.

**Manual:** CONDITIONAL when a frozen acceptance claim requires a real physical device/provider account unavailable to CI.

# R13.13 — KodeRelease versioning, release trains, promotion, rollout + rollback

**Objective.** Create a common release authority over accepted mobile artifacts.

**Deliver:** semantic/product version + Android versionCode + Apple build-number mapping; release train/channel/candidate identities; immutable artifact digest set; promotion gates; staged rollout intent; rollback point; changelog/provenance/SBOM/compliance binding; release lock/concurrency rules.

**Platform rule:** KodeRelease coordinates stores; it does not implement a forbidden self-updater. iOS binary updates are store/TestFlight mediated. Android install/update actions are explicit dev/test or store-mediated operations.

**Acceptance:** promotion requires all bound evidence; version/build regressions and artifact substitution rejected; failed promotion leaves prior release authoritative; concurrent promotion conflict deterministic.

**Manual:** NONE for local release-state acceptance; live store publication remains capability-gated elsewhere.

# R13.14 — Mobile diagnostics: logs, crash/ANR/test/performance bundles + redaction

**Objective.** Produce supportable mobile evidence without turning diagnostics into surveillance.

**Deliver:** structured Android logcat/crash/ANR/test reports, Apple XCTest/result/log/crash ingestion, common diagnostic envelope, fingerprint/dedup, device/toolchain/artifact binding, redaction, bounded retention/export, performance snapshots and release correlation.

**Acceptance:** secrets/personal data patterns redacted; diagnostic bundle source digests verified; cross-release crash substitution rejected; corrupt/oversized log handling bounded; no continuous hidden telemetry introduced.

**Manual:** CONDITIONAL only for device-only diagnostics required by a frozen claim.

# R13.15 — Current store compliance engine: privacy, ratings, permissions, SDK/policy evidence

**Objective.** Make “current compliance” a versioned research/evidence system rather than hard-coded folklore.

**Deliver:** provider rule schema with source URL, retrieved/effective/expires dates, platform/region/app-category scope, severity and remediation; Google target API/Data safety/permission/content-rating checks; Apple SDK minimum/privacy manifest/required-reason API/App Privacy/privacy-policy/age-rating checks; third-party SDK declaration inventory; accessibility/localization/store-asset checks; R7 ResearchGuard provenance.

**Acceptance:** stale or unofficial-only evidence cannot claim CURRENT; rule effective dates tested around boundaries (including 2026-08-31 API 36); conflicting sources surface blocker instead of arbitrary resolution; compliance output is advisory/readiness evidence, never legal certification.

**Manual:** NONE for deterministic compliance evaluation. Account-only forms may remain `NEEDS_ACCOUNT_CONFIRMATION` without blocking non-live readiness.

# R13.16 — CLI + KodeStudio Mobile/DeviceLab/Release workspace

**Objective.** Expose the accepted R13 model without raw tooling surfaces.

**Deliver:** structured `kodepoia r13` status/scaffold/build/test/package/device/compliance/release intents; stable JSON/exit codes; KodeStudio Mobile/DeviceLab/Release pages driven by Wizard output; explicit passive refresh vs execute; read-only evidence; blockers/capability matrix; cancellation; accessibility/localization/pseudo-localization.

**Acceptance:** no raw executable/argv/Gradle/Xcode/signing/store-token parameter; passive refresh launches no external process; unavailable capability returns explicit blocked state; evidence cannot be edited into PASS; UI smoke exact-head.

**Manual:** NONE.

# R13.17 — Adversarial hardening + Android/iOS integrated release-readiness acceptance

**Objective.** Close R13 with anti-circular evidence proving the phase-level roadmap capability.

**Deliver:** adversarial suite spanning DNA -> mobile scaffold -> build -> package/sign state -> device tests -> compliance -> release promotion -> diagnostics; attacks on identifiers, paths, Gradle/Xcode settings, signing refs, device IDs, store tracks, policy snapshots and evidence; canonical `R13_INTEGRATED_ACCEPTANCE.json` schema/model/verifier; prior R12 integrated digest binding; canonical Android hosted build/test/package flow and canonical iOS hosted macOS simulator build/test flow; anti-circular report creation only after implementation head independently passes gates.

**Phase DoD evidence target:**

- existing Project Wizard creates accepted Android and iOS mobile intent;
- Android canonical project/scaffold builds and tests, with validated APK/AAB artifact state and current API/store readiness;
- iOS canonical Xcode/SwiftUI project scaffolds and compiles/tests on accepted hosted macOS simulator evidence;
- DeviceLab abstractions and release/compliance/diagnostics evidence are bound without fabricating physical-device/store-account claims;
- canonical R13 integrated report has `status=pass`, `blockers=[]` and a stable semantic digest.

**Manual:** CONDITIONAL — trigger only if the final frozen phase claim requires a physical-device, live-store, signing/provisioning or macOS runtime semantic that accepted hosted CI cannot establish. If triggered, freeze one exact candidate SHA and provide one bounded collector with prerequisites, commands, expected evidence path, recovery/privacy instructions; stop before R14 planning until reviewed.

## Required artifact pattern per subdivision

Every R13.x implementation must include:

- `docs/roadmap/R13_<n>_DESIGN.md`;
- `docs/roadmap/R13_<n>_ACCEPTANCE.md`;
- focused tests named for the subdivision;
- schemas for new durable data;
- workflow/evidence artifact only when the subdivision introduces a new real tool/platform seam;
- local/manual JSON only when a REQUIRED/triggered CONDITIONAL seam truly exists;
- no checked-in PASS evidence before its exact implementation source has independently passed the required gates.

## Exact-head gate policy

Planning and every R13 subdivision use the same anti-drift rule:

- R0 Repository Guard SUCCESS on exact head;
- full Python Core SUCCESS, including the workflow’s OS/package matrices;
- KodeStudio UI Smoke SUCCESS;
- relevant Android/macOS/device/release adapter workflows SUCCESS when introduced/affected;
- all decision-making runs must refer to the exact same final head;
- any byte change after evidence recording creates a new head and requires fresh gates before merge;
- merges use `expected_head_sha`;
- exactly one continuity-only post-merge normalization is allowed;
- no next subdivision/phase starts until that normalization passes and merges.

## Planning acceptance / recovery sequence

1. branch `r13/00-phase-plan` from normalized `main` `997db5a5ad9f847037de79057bcdc7aefd1ddeb9`;
2. create `docs/roadmap/R13_PLAN.md` and synchronize continuity in the same planning candidate;
3. accepted planning candidate `6f44e8faf8ef675dab5c8079541ce436ff55b4b2` passed R0 #1596 / `32846530810`, Python #1570 / `32846530804`, UI #1537 / `32846530786`;
4. planning PR #219 merged with expected head as `9a5c678c226cb845c639b914e6365b475ab20e86`;
5. single continuity-only planning normalization head `b7ca326ac6f9fbb74bdbe69fefe6faf4aaadf653` passed R0 #1598 / `32846946552`, Python #1572 / `32846946574`, UI #1539 / `32846946557`;
6. normalization PR #220 merged as `aef297e385dc49ad6ae0935d4f9ef25a35e5e984`;
7. therefore R13 planning is **ACCEPTED + NORMALIZED** and R13.1 is authorized.

## Phase completion rule

R13 is `COMPLETE + NORMALIZED` only when all R13.1–R13.17 rows are COMPLETE with authoritative evidence, canonical integrated acceptance is PASS, the Android and iOS phase-DoD evidence above is bound, any triggered manual evidence is reviewed, the implementation/evidence merge is followed by exactly one accepted continuity-only normalization, and no frozen R1–R12 boundary has changed without ADR.

Only then may R14 planning begin.

## Ongoing maintenance rule

Update `R13_PLAN.md` and continuity in the same work cycle whenever subdivision scope/status/manual prerequisites, current compliance baselines, important recovered defects, or phase ordering changes. Mutable ecosystem values belong to evidence snapshots with effective dates; they do not silently rewrite frozen architecture.