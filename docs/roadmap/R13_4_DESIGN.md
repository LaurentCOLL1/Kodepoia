# R13.4 — Android Gradle build/export design

## Scope

R13.4 turns the deterministic R13.3 Android source workspace into real hosted-CI build evidence. It owns build-toolchain discovery/evidence, a deterministic build compatibility overlay, fixed Gradle tasks, APK/AAB inspection, artifact lineage and build budgets. It does not own production signing (R13.5), device execution (R13.6), Play publication (R13.7) or arbitrary Gradle execution.

## Source authority

The build starts only from a R13.3 workspace whose `.kodepoia/mobile/android/workspace-manifest.json` is present and whose listed file digests still match the source tree. Any changed, missing, duplicated or escaping source entry blocks staging.

The source workspace is never modified for toolchain compatibility. R13.4 creates an isolated staging tree and records a deterministic `AndroidBuildOverlayManifest` that binds:

- R13.3 source workspace semantic digest;
- the effective toolchain evidence digest;
- every staged generated file digest.

The overlay updates only repository-owned build compatibility coordinates required for the accepted hosted toolchain: AGP, Compose BOM, Kotlin Compose compiler plugin, compileSdk and the two fixed plugin declarations. Project/user content and source semantics remain unchanged.

## Current hosted toolchain evidence — 2026-08-25

R13.4 deliberately treats these values as evidence, not architecture constants.

The accepted R13.3 source definition remains bound to the then-current Compose `2026.08.00` / compileSdk 37 evidence. Hosted R13.4 acceptance subsequently proved that the stable `sdkmanager` repository exposed to the Ubuntu runner did **not** provide `platforms;android-37`. That rejected candidate is evidence of capability unavailability, not a reason to mutate R13.3 history or request a user-machine SDK.

The hosted stable R13.4 build overlay therefore uses:

- Android Gradle Plugin: `9.3.1` stable release line;
- Gradle: `9.5.0` for AGP 9.3;
- JDK: 17;
- SDK compile platform: API 36;
- Android Build Tools: `36.0.0`;
- Compose BOM: `2026.06.00`, the last stable Compose baseline documented before Compose 1.12 moved to compileSdk 37;
- Compose compiler/Kotlin plugin: `2.3.21`;
- canonical targetSdk: API 36, satisfying the Google Play mobile deadline effective 2026-08-31.

AGP 9.3 can support newer API levels, but support in AGP is not treated as proof that a particular hosted SDK repository currently exposes that platform. Actual provisioning is capability evidence.

The source URLs are restricted to HTTPS `developer.android.com` and are serialized in `AndroidBuildToolchainEvidence`. Dynamic versions such as `9.3.+`, `latest` or mutable unofficial URLs are not representable.

## Fixed build operations

`AndroidBuildTask` is a closed enum:

- `unit_test` -> `:app:testDebugUnitTest`;
- `apk_debug` -> `:app:assembleDebug`;
- `aab_release` -> `:app:bundleRelease`.

`AndroidBuildRequest.argv()` adds only `--no-daemon` and `--stacktrace`. There is no raw task, raw Gradle option, `-P`, init script, build script, executable path or model-supplied command field.

Dangerous environment injection is fail-closed. `GRADLE_OPTS`, `JAVA_TOOL_OPTIONS`, `JAVA_OPTS`, `_JAVA_OPTIONS` and every `ORG_GRADLE_PROJECT_*` variable are rejected. Only a small path/temp allowlist can be forwarded by a future runtime adapter.

Hosted CI itself may install public SDK/toolchain packages as CI infrastructure. Kodepoia runtime does not silently install them.

## Staging boundary

Source and staging must be fully disjoint. R13.4 rejects all three dangerous shapes before deleting or creating staging content:

- staging equals source;
- staging is inside source;
- source is inside staging.

This prevents staging cleanup from deleting source-owned data and prevents generated build output from contaminating the accepted source workspace.

## Artifact inspection

APK and AAB are treated as untrusted ZIP containers. Inspection enforces:

- bounded artifact bytes;
- bounded entry count, individual entry bytes and total uncompressed bytes;
- no absolute/traversing/backslash/NUL path;
- no duplicate normalized path;
- required package structure;
- SHA-256 over exact artifact bytes;
- ABI extraction from `lib/<abi>/...` or `base/lib/<abi>/...`.

Required APK entries are `AndroidManifest.xml`, `classes.dex`, `resources.arsc`. Required AAB entries are `base/manifest/AndroidManifest.xml`, `base/dex/classes.dex`, `base/resources.pb`.

R13.4 structural evidence does not claim a signature state; R13.5 owns that distinction.

## Exact-head hosted acceptance

`.github/workflows/r13-android-build-acceptance.yml` uses a matrix of `ubuntu-latest` and `windows-latest`. Each job:

1. checks out the exact pull-request head;
2. installs Python evidence dependencies;
3. provisions JDK 17, Gradle 9.5.0 and Android SDK API 36 / Build Tools 36.0.0;
4. renders the canonical R13.3 fixture;
5. verifies it and creates the deterministic R13.4 staging overlay;
6. executes the three fixed Gradle tasks;
7. inspects the real debug APK and release AAB;
8. validates `AndroidBuildEvidence` against its Draft 2020-12 schema;
9. checks `source_sha == pull-request head` and `status == pass`;
10. uploads the evidence as a workflow artifact.

A Linux success cannot certify Windows and vice versa; the workflow result is successful only after both matrix jobs pass.

## Rejected hosted candidates

- A workflow candidate was rejected before jobs because `runner.temp` was incorrectly used in job-level `env`; GitHub Actions only exposes `runner` in supported step/job keys. The paths were moved to step-level contexts.
- Candidate `8c8e8dc2877f3a8de62d5e2b9fb19197f6b8a24c` was rejected because the stable Ubuntu `sdkmanager` repository returned `Failed to find package 'platforms;android-37'`. No success from that SHA is reused.

These failures do not trigger a manual gate because both are hosted-CI configuration/capability issues with deterministic fixes.

## Manual gate

Manual state starts `CONDITIONAL / NOT TRIGGERED`. It remains not triggered if hosted CI proves the frozen build/package semantics. Missing Android tools on the user's computer are irrelevant to this decision. A manual gate may be triggered only if a required real semantic cannot be established on accepted hosted runners after supported CI paths are exhausted.
