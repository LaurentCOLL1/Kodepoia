# R13.4 — Android Gradle build/export acceptance

## Claim

R13.4 is accepted only when one exact implementation head proves that the canonical R13.3 native Android workspace can be transformed into an isolated, deterministic R13.4 build staging tree and built on hosted CI into a structurally validated debug APK and release AAB, with targetSdk 36+ and explicit toolchain/lineage evidence.

## Required automated gates

The exact candidate head must pass all of:

1. R0 Repository Guard;
2. full Python Core, including Ubuntu/Windows and package builds;
3. KodeStudio UI Smoke;
4. `R13 Android Build Acceptance`, with both `android-build-ubuntu-latest` and `android-build-windows-latest` successful on that same source SHA.

Any candidate failure rejects that candidate. Evidence from rejected SHAs is not reused.

## Focused acceptance

Automated tests must prove:

- source workspace manifest and every listed generated file digest are checked before staging;
- source tampering, traversal and staging overlap fail closed;
- overlay output is deterministic and leaves source bytes unchanged;
- effective AGP/Gradle/Kotlin/Compose/SDK/JDK versions are explicit and official-source bound;
- dynamic versions and unofficial sources fail closed;
- Gradle argv is a closed enum mapping with no raw task/property/init-script escape;
- dangerous Gradle/JVM environment injection is rejected;
- malformed/fake/traversing APK/AAB inputs are rejected;
- artifact byte size, ZIP entry count, entry size and total uncompressed size are bounded;
- real APK/AAB evidence records exact SHA-256, package structure and ABI set;
- `PASS` cannot be formed without both APK and AAB and targetSdk >= 36;
- evidence validates against `schemas/r13/android-build-evidence.schema.json`;
- hosted evidence is tied to the exact PR head.

## Hosted-CI acceptance artifact

Each supported runner uploads `R13_4_ANDROID_CI_ACCEPTANCE.json` as a workflow artifact. It is evidence produced after checkout/build of the exact PR head; no canonical checked-in PASS report is created before independent gates.

The evidence contains no signing secret, keystore, Play credential, account identifier or user content.

## Manual decision

**CONDITIONAL / NOT TRIGGERED at implementation start.**

The gate remains NOT TRIGGERED if hosted Ubuntu and Windows establish the required build/package semantics. A local Android SDK installation is not required. R13.4 does not claim physical-device behavior, production signing or live Play publication.

If hosted CI cannot establish a frozen required semantic, R13.4 must become `BLOCKED / MANUAL_REQUIRED` and execution must stop before R13.5. No synthetic PASS is allowed.

## Completion sequence

After one candidate satisfies all required gates:

1. update `R13_PLAN.md` and continuity to R13.4 `COMPLETE`, R13.5 still `PLANNED`, and record the accepted candidate/run evidence;
2. because those bytes change, run fresh exact-head R0/Python/UI/Android Build gates;
3. merge the implementation PR with `expected_head_sha`;
4. create exactly one continuity-only post-merge normalization;
5. run fresh exact-head gates on the normalization and merge it;
6. only then begin R13.5.
