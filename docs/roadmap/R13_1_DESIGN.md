# R13.1 — Mobile contracts, identities, capability model + secure toolchain boundaries

## Status

Implementation candidate design. Manual intervention: **NONE**.

## Objective

R13.1 establishes framework-neutral, deterministic mobile/platform/release contracts before any Android or Apple tool is executed. It deliberately does not install SDKs, launch Gradle/Xcode/ADB, access devices, sign artifacts, call stores, or perform network requests.

## Architecture

`src/kodepoia/mobile/contracts.py` defines canonical JSON/SHA-256 identities for:

- Android/iOS/iPadOS target profiles, form factors, source kinds, architectures and package kinds;
- toolchain identities bound to executable name, SHA-256, version, host OS and capabilities;
- capability reports with explicit `NOT_PROBED`, `AVAILABLE`, `UNAVAILABLE`, `UNSUPPORTED`, `BLOCKED`, `FAILED` state;
- application identifiers with platform-specific validation;
- package/artifact descriptors;
- redacted provider/device identities and deterministic test matrices;
- store/release readiness state bound to artifact and compliance digests.

`AVAILABLE` is evidence-bearing: configuration text alone cannot create it. A report in that state requires at least one probed `MobileToolchainIdentity` and cannot contain blockers. Missing evidence is therefore never promoted to PASS.

## Secure toolchain boundary

`src/kodepoia/mobile/boundary.py` mirrors the accepted R12 pattern without executing a process. `MobileToolchainBoundary` owns three explicit roots: approved runtime roots, project root and staging root. Resolved tools must remain inside approved runtime roots and have an allowlisted basename. Project inputs must resolve within the project root. Outputs must resolve within staging.

The tool identity surface is finite: Java, Gradle, adb, sdkmanager, apksigner, keytool, bundletool JAR, xcodebuild and xcrun. Apple `simctl` is intentionally modeled through a typed `xcrun simctl ...` argv rather than as attacker-selected executable input. Android bundletool is modeled as an approved JAR used through an approved Java identity.

Only repository-owned typed argv builders exist. They expose fixed probe/list/build-task forms and bounded operation enums. There is no raw argv, shell string, arbitrary Gradle property, arbitrary `adb shell`, raw Xcode build setting or arbitrary environment surface.

Environment overrides are allowlisted. Path-bearing entries (`JAVA_HOME`, `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `GRADLE_USER_HOME`, `DEVELOPER_DIR`) must resolve under an approved runtime or staging root. Process-control variables such as `PATH`, `CLASSPATH`, `GRADLE_OPTS`, `JAVA_TOOL_OPTIONS` and `ADB_TRACE` are intentionally not accepted through this boundary.

## Durable schemas

R13.1 adds strict JSON Schema 2020-12 definitions for target profiles, capability reports and device test matrices. Schemas use `additionalProperties: false` so a user/model cannot smuggle `raw_argv` or other executable-control fields into durable data.

## Security invariants

1. Resolve-before-trust: symlink resolution occurs before root checks.
2. Name + root identity: a matching filename outside an approved runtime root is rejected.
3. Evidence-bearing capability: `AVAILABLE` cannot be asserted without probed toolchain identity.
4. Platform partitioning: Android and Apple package/API concepts are mutually bounded.
5. Canonical serialization: non-finite/non-serializable values fail closed; collection order is normalized before hashing.
6. No execution: R13.1 only validates and builds typed argv tuples.
7. No secrets: no password/private key/token field exists in R13.1 contracts or argv builders.

## External compatibility rationale

Android officially distributes command-line SDK tooling and Platform-Tools, while Apple documents `xcodebuild`, `xcrun`, `simctl` and device tooling as Xcode command-line surfaces. R13.1 models those stable tool identities but does not freeze mutable ecosystem versions as architecture constants. Version/capability probing occurs in later subdivisions.

## Rollback

R13.1 is additive. Reverting its implementation commits removes `src/kodepoia/mobile`, `schemas/r13` R13.1 schemas, focused tests and R13.1 documentation without migrating existing R1–R12 data. No persistent database or external environment is mutated.
