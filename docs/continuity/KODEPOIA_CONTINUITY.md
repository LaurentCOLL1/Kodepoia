# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 26 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R12 COMPLETE + NORMALIZED. R13 planning ACCEPTED + NORMALIZED. R13.1–R13.6 COMPLETE + NORMALIZED. R13.7 IN_PROGRESS.** R13.6 accepted technical candidate `91fac3fe1f80b04b570636002f4ba98e0c64724a`; final end-synchronized head `05238743d01f71d6feaa4dc6d832efbab1633c81` passed R0 #1654 / `32906607557`, Python #1628 / `32906607562`, UI #1595 / `32906607621`, Android Build #74 / `32906607561`, Android Signing #27 / `32906607601`, and Android Device #12 / `32906607620`; PR #231 merged as `8c5751bfe4c795f3386ea97caa92beb9c29be23d`; the single continuity-only normalization `4c97fea1d7e47cdb85aed6d9c096012592a6a11c` passed R0 #1656 / `32907230177`, Python #1630 / `32907230212`, UI #1597 / `32907230236`; PR #232 merged as normalized `main` `6b943e29528245318904c86913eb5783d238797c`. R13.7 branch `r13/07-google-play-readiness` is created exactly from that normalized head and is the sole active subdivision.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : **frozen**.
- R1–R12 : **COMPLETE + NORMALIZED**.
- R12 canonical integrated digest: `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R13 planning : **ACCEPTED + NORMALIZED**.
- R13 phase status: **IN PROGRESS**.
- R13.1–R13.6: **COMPLETE + NORMALIZED**.
- R13.7: **IN_PROGRESS**, branch `r13/07-google-play-readiness`, manual **CONDITIONAL / NOT TRIGGERED** at start.
- R13.8–R13.17: **PLANNED / NOT STARTED**.
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
- Final end-synchronized head **`c479d429540b4941d96d3fcc39b8d85561917750`** passed R0 #1638 / `32890540226`, Python #1612 / `32890540400`, UI #1579 / `32890540232`, and R13 Android Build Acceptance #42 / `32890540329`; PR #227 merged as **`b212ae166ee7eceac59ef3c39d56272acfdfdfa6`**.
- Continuity-only normalization **`98f347616a389960c4627b424d12757fd73a4d33`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1640 / `32891329175`, Python #1614 / `32891329245`, UI #1581 / `32891329226`; PR #228 merged as normalized `main` **`939565f6409a45c93d0168546c1b4bb947d13ad4`**.
- Therefore R13.4 is authoritatively **COMPLETE + NORMALIZED**.

## R13.5 closure authority

- Authorized normalized base: **`939565f6409a45c93d0168546c1b4bb947d13ad4`**.
- Dedicated implementation branch: **`r13/05-android-signing`**; PR #229.
- Initial technical candidate **`a58227cd21112a65710002d2e673a1466889d7ce`** passed technical gates but was not accepted as final because required subdivision artifacts `R13_5_DESIGN.md` and `R13_5_ACCEPTANCE.md` were missing.
- Accepted implementation candidate **`1b299f5ab69bd5ac90d8ea805d59c216643f68e3`** passed R0 #1643 / `32894851393`, Python Core #1617 / `32894851604`, KodeStudio UI Smoke #1584 / `32894851851`, R13 Android Build Acceptance #51 / `32894851296`, and R13 Android Signing Acceptance #4 / `32894851385`; both Android workflows succeeded on Ubuntu and Windows.
- Final end-synchronized head **`030a3c548aebd77b736f139f995bf3951b17c33d`** passed fresh R0 #1645 / `32895748636`, Python Core #1619 / `32895748542`, KodeStudio UI Smoke #1586 / `32895748608`, R13 Android Build Acceptance #55 / `32895748735`, and R13 Android Signing Acceptance #8 / `32895748633`; both Android workflows again succeeded on Ubuntu and Windows.
- PR #229 merged with `expected_head_sha=030a3c548aebd77b736f139f995bf3951b17c33d` as **`bc354a48d6cd52b04462d58ced2a855770217d5f`**.
- The single continuity-only normalization head **`2517fb071f091c7a2312301504126bd4c8f70bbd`** changed only `docs/continuity/KODEPOIA_CONTINUITY.md`, passed R0 #1647 / `32896670665`, Python Core #1621 / `32896670704`, and KodeStudio UI Smoke #1588 / `32896670776`; PR #230 merged as normalized `main` **`56d6da4184709a54841ed36b21128477c78c6e9d`**.
- Manual remained **CONDITIONAL / NOT TRIGGERED**. Hosted CI proved the frozen signing/state-model semantics with an ephemeral test identity; production keystore/private-key/password material and a live Play account were not required.
- Therefore R13.5 is authoritatively **COMPLETE + NORMALIZED**.

## R13.6 closure authority

- Authorized normalized base: **`56d6da4184709a54841ed36b21128477c78c6e9d`**.
- Dedicated implementation branch: **`r13/06-android-device-testing`**; implementation PR #231.
- Manual state: **CONDITIONAL / NOT TRIGGERED**. Hosted emulator evidence established the frozen R13.6 core claim; no physical device or external account was required.
- Rejected candidate **`6367d8df1c691b3701d30f21e0cb6ffec2b468fb`** passed its standard/build/signing gates but Device #2 / `32899713104` failed because collection began before the launched emulator registered ONLINE in ADB. Evidence is rejected and not reused.
- Rejected candidate **`8e3092855279feaa8bfeb45350410d22cb18b6d4`** passed its other required gates but Device #4 / `32900347557` timed out with `R13.6 emulator did not register online in ADB: not-visible`; cleanup succeeded. Evidence is rejected and not reused.
- Rejected candidate **`5a2869253c10d841049e78fa53f15f4d87105eec`** proved hosted KVM/SDK/build but the emulator could not discover the AVD created by `avdmanager`; evidence is rejected and not reused.
- Rejected candidate **`22512f22d225c79fc69f9b7ca337d7838d13bb4d`** fixed deterministic AVD discovery and boot, but the CI helper missed the already-online `device` state due a literal-tab matcher; evidence is rejected and not reused.
- Accepted technical candidate **`91fac3fe1f80b04b570636002f4ba98e0c64724a`** reuses governed `parse_adb_devices` and passed R0 #1653 / `32903990807`, Python #1627 / `32903990720`, UI #1594 / `32903990770`, Android Build #72 / `32903990739`, Android Signing #25 / `32903990787`, and Android Device #10 / `32903990871`, all SUCCESS on exact head.
- End-synchronized head **`05238743d01f71d6feaa4dc6d832efbab1633c81`** changed only `docs/roadmap/R13_PLAN.md` and continuity, marked R13.6 COMPLETE/R13.7 PLANNED, and passed fresh R0 #1654 / `32906607557`, Python #1628 / `32906607562`, UI #1595 / `32906607621`, Android Build #74 / `32906607561`, Android Signing #27 / `32906607601`, and Android Device #12 / `32906607620`, all SUCCESS.
- PR #231 merged with **`expected_head_sha=05238743d01f71d6feaa4dc6d832efbab1633c81`** as **`8c5751bfe4c795f3386ea97caa92beb9c29be23d`**.
- Single continuity-only normalization **`4c97fea1d7e47cdb85aed6d9c096012592a6a11c`** changed exactly one file (`docs/continuity/KODEPOIA_CONTINUITY.md`) relative to the implementation merge, passed R0 #1656 / `32907230177`, Python Core #1630 / `32907230212`, and KodeStudio UI Smoke #1597 / `32907230236`, all SUCCESS.
- Normalization PR #232 merged with `expected_head_sha=4c97fea1d7e47cdb85aed6d9c096012592a6a11c` as normalized **`main` `6b943e29528245318904c86913eb5783d238797c`**.
- Therefore R13.6 is authoritatively **COMPLETE + NORMALIZED**.

## R13.7 execution authority

- Authorized normalized base: **`6b943e29528245318904c86913eb5783d238797c`**.
- Dedicated branch: **`r13/07-google-play-readiness`**.
- Start status: **IN_PROGRESS** before implementation.
- Manual state: **CONDITIONAL / NOT TRIGGERED**. Core R13.7 acceptance is local/dry-run and must not require Play Console login, service-account credentials, API tokens, tester enrollment, billing or real publication. If a frozen live-account-only semantic becomes necessary, stop before R13.8 and request bounded user-controlled evidence; never request credentials in chat.
- Objective: model Google Play track intent, staged rollout, AAB upload-candidate identity, localized listing metadata/assets, date-aware official-policy evidence, Data safety/content-rating/permission/SDK findings, Play App Signing readiness and an optional credential-gated API capability boundary without automatic upload or publication.
- Current official policy facts used as **versioned evidence**, not architecture constants: ordinary new apps/updates must target Android 16/API 36+ from 2026-08-31; current listing maximums are 30 characters for app name, 80 for short description and 4000 for full description; published apps require IARC content rating/questionnaire. These values must remain source/effective-date scoped and cannot silently claim CURRENT when stale.

## Frozen R13 subdivision index

| ID | Title | Status | Manual |
| --- | --- | --- | --- |
| R13.1 | Mobile contracts, identities, capability model + secure toolchain boundaries | COMPLETE | NONE |
| R13.2 | Project DNA/KodeProduct mobile profiles + Project Wizard target selection | COMPLETE | NONE |
| R13.3 | Android deterministic native scaffold + Kotlin/Compose shared app model | COMPLETE | NONE |
| R13.4 | Android Gradle build/export, APK/AAB, manifest/resources/ABI validation | COMPLETE | CONDITIONAL |
| R13.5 | Android signing states, keystore boundary + Play App Signing model | COMPLETE | CONDITIONAL |
| R13.6 | Android emulator/device testing + adb/instrumentation adapter | COMPLETE | CONDITIONAL |
| R13.7 | Google Play release tracks, metadata + policy/compliance readiness | IN_PROGRESS | CONDITIONAL |
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

**R13.7 implementation:** after this start synchronization, implement the local/dry-run Google Play readiness model on `r13/07-google-play-readiness`: add `R13_7_DESIGN.md`, `R13_7_ACCEPTANCE.md`, focused tests, strict durable schema(s), date-aware official-policy snapshot/readiness evaluation, store-listing/Data-safety/content-rating/policy findings, AAB/signing binding, and optional non-executing/capability-gated Play API request descriptors if needed. Do not perform live Play API calls or publication. Run exact-head R0 + Python + UI and affected Android build/signing/readiness gates. If a live-account-only requirement appears, mark manual REQUIRED/BLOCKED and stop before R13.8.