# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R12 COMPLETE + NORMALIZED.** R12 canonical integrated evidence has semantic digest `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`; R12.16 implementation/evidence PR #217 merged as `2250d782a65c4aa0d849cc98f7d87e6f3d68c07e`, and its single continuity-only normalization PR #218 passed 9/9 exact-head gates on `f9a1fc05708be3a4b4048b2b33e6ac228485285e` and merged as normalized `main` `997db5a5ad9f847037de79057bcdc7aefd1ddeb9`. **R13 planning is now the sole active work.** Branch `r13/00-phase-plan` was created exactly from that normalized main. `docs/roadmap/R13_PLAN.md` freezes 17 subdivisions, R13.1–R13.17, all PLANNED. R13.1 is FORBIDDEN until the R13 planning PR passes exact-head R0/full Python/KodeStudio UI, merges with expected SHA, then exactly one continuity-only planning normalization also passes those exact-head gates and merges. No R13 implementation may start before that normalized planning merge.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : **frozen**.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 : **COMPLETE + NORMALIZED**.
- R12 canonical integrated digest: `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R12 normalized final `main`: **`997db5a5ad9f847037de79057bcdc7aefd1ddeb9`**.
- R13 planning: **IN PROGRESS on `r13/00-phase-plan`**.
- R13.1–R13.17: **PLANNED / NOT STARTED**.
- R14 planning: **FORBIDDEN until R13 COMPLETE + NORMALIZED**.

## R12 final closure authority

- Accepted R12.16 implementation source: `1927d9ab673228101c932b1cb6b89243296ac957`.
- Final evidence head: `f12132b777569a6a03171e759dd1b36d3a1858b4`.
- Canonical report: `docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json`, `status=pass`, `blockers=[]`, manual `conditional_not_triggered`, semantic digest `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- PR #217 merged with expected head as `2250d782a65c4aa0d849cc98f7d87e6f3d68c07e`.
- Single post-merge normalization head: `f9a1fc05708be3a4b4048b2b33e6ac228485285e`.
- Normalization exact-head gates all SUCCESS: R0 #1594 / `32844549399`; Python Core #1568 / `32844549531`; KodeStudio UI #1535 / `32844549411`; WPF #82 / `32844549655`; WinUI3 #72 / `32844549414`; Avalonia #68 / `32844549519`; Qt6 #63 / `32844549568`; Tauri2 #54 / `32844549393`; Integrated Windows #7 / `32844549496`.
- PR #218 merged as **`997db5a5ad9f847037de79057bcdc7aefd1ddeb9`**.
- Therefore R12 is authoritatively **COMPLETE + NORMALIZED** and R13 planning is authorized.

## Permanent R-phase plan status synchronization rule

For every R phase, the phase plan is live execution authority and MUST be updated both **at the beginning** and **at the end** of every subdivision.

- **Subdivision start, before implementation:** update phase-level `Status`, `Complete subdivision index`, and execution checkpoint so all prior normalized subdivisions are `COMPLETE`, the active subdivision is `IN_PROGRESS`, and later subdivisions remain `PLANNED`/`NOT STARTED`; synchronize continuity in the same work cycle.
- **Subdivision end, before final documentation re-gates:** update the same plan fields so the accepted active subdivision is `COMPLETE`; the next subdivision remains `PLANNED` until its own dedicated branch starts; synchronize continuity in the same work cycle.
- A triggered conditional manual gate must set truthful `BLOCKED`/`MANUAL_REQUIRED`, never synthetic `COMPLETE`.
- Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status.
- A stale subdivision index or stale phase status is a governance defect and blocks acceptance.

This rule applies to R13 and all later R phases unless a later accepted ADR explicitly changes it.

## R13 planning authority

### Frozen roadmap scope

The v1.0 roadmap defines R13 exactly as **Mobile / Platform / Release**:

- Android export/signing/AAB/APK/device tests/store;
- interface iOS/Mac/Xcode;
- DeviceLab;
- KodeRelease/Updater/Diagnostics;
- current compliance.

`docs/roadmap/R13_PLAN.md` expands this frozen scope without moving R14 backend/live-service work into R13.

### Planning branch and source

- normalized planning base: `997db5a5ad9f847037de79057bcdc7aefd1ddeb9`;
- dedicated planning branch: `r13/00-phase-plan`;
- plan file: `docs/roadmap/R13_PLAN.md`;
- R13.1 implementation: **FORBIDDEN until planning merge + single planning normalization merge**.

### Current external baseline — date-aware, not architecture constants

- Google Play: new apps/updates must target Android 16 / API 36 from **2026-08-31**; R13 store-ready acceptance therefore starts at API 36 rather than accepting a target that becomes obsolete six days after planning.
- Android Compose planning baseline: stable BOM `2026.08.00`; Compose 1.12 uses current compileSdk/AGP compatibility, but R13 capability-probes these values instead of freezing them forever.
- New Google Play apps use Android App Bundle; signing state separates upload key and Play App Signing distribution key; no production secret may enter repo/evidence/argv.
- Apple: App Store Connect requires Xcode 26+ with iOS/iPadOS 26 SDK+ since 2026-04-28. Xcode 27 beta/TestFlight capability is distinct from stable production capability.
- Apple privacy manifests and required-reason API declarations are first-class compliance data.
- Firebase Test Lab is an optional DeviceLab provider for Android/iOS hosted devices; provider credentials/paid quota are not global phase prerequisites.
- Google Play Data safety, target API, permissions/content ratings and Apple privacy/age-rating/SDK minimum rules are versioned compliance snapshots with official-source provenance and effective dates.

### Frozen R13 subdivision index

| ID | Title | Status | Manual |
| --- | --- | --- | --- |
| R13.1 | Mobile contracts, identities, capability model + secure toolchain boundaries | PLANNED | NONE |
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

R13 can become COMPLETE only when the existing Project Wizard creates accepted Android/iOS mobile intent; a canonical Android project builds/tests and yields validated APK/AAB release state; a canonical iOS SwiftUI/Xcode project compiles/tests on accepted hosted macOS simulator evidence; DeviceLab/release/diagnostics/compliance evidence is truthful and provider-scoped; any triggered manual gate is reviewed; canonical `R13_INTEGRATED_ACCEPTANCE.json` has `status=pass`, `blockers=[]`; the implementation/evidence merge is followed by exactly one accepted continuity-only normalization.

Actual public Play/App Store publication is explicit user-controlled behavior, never an automatic acceptance prerequisite. Live store/account/signing operations stay capability-gated and may trigger bounded manual evidence only when a frozen claim truly requires them.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + global KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence; R12 desktop/package/update authority remain in force. Structured APIs only. Network off by default. No arbitrary shell/Gradle/Xcode/store commands. Missing evidence never manufactures PASS.

## R13 execution rule

Each subdivision: dedicated branch from normalized `main` -> start plan+continuity status sync -> implementation + focused tests -> exact-head standard and platform-specific gates -> truthful manual state -> end plan+continuity status sync -> fresh evidence/re-gates if bytes changed -> merge with `expected_head_sha` -> exactly one continuity-only post-merge normalization + exact-head gates + merge -> only then next subdivision.

If a CONDITIONAL manual gate triggers, stop before the next subdivision and provide bounded prerequisites, exact commands/actions, expected evidence, recovery/privacy instructions; never request passwords/private keys/tokens in chat.

## R13 planning acceptance sequence

1. Freeze one exact planning head containing `R13_PLAN.md` + this synchronized continuity.
2. Require exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke.
3. If any byte changes after recording evidence, re-gate the resulting final planning head.
4. Merge planning PR with `expected_head_sha`.
5. Create exactly one planning post-merge normalization changing only this continuity file.
6. Require fresh exact-head R0/full Python/UI on the normalization.
7. Merge normalization with expected SHA.
8. Only then set R13 planning **ACCEPTED + NORMALIZED** and authorize R13.1.

## Next authorized action

**R13 planning only:** freeze the current `r13/00-phase-plan` head, open the planning PR, require exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, merge with expected SHA, then perform the single continuity-only planning normalization and the same exact-head gates. Do not start R13.1 before that normalization merges.