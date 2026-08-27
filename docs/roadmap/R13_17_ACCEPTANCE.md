# R13.17 — Integrated release-readiness acceptance

**Status:** PENDING INDEPENDENT EXACT-HEAD GATES  
**Manual:** CONDITIONAL / NOT TRIGGERED  
**Integrated PASS report:** NOT CREATED  
**CI PASS manifest:** NOT CREATED

This document is intentionally pending. Its presence defines the frozen acceptance contract; it is **not** evidence that R13.17 or R13 has passed.

## Candidate acceptance contract

A technical R13.17 implementation candidate is eligible for evidence creation only when the same immutable source SHA independently passes:

- R0 Repository Guard;
- full Python Core, including both OS test/package jobs and its internal KodeStudio smoke;
- KodeStudio UI Smoke;
- R13 Android Build Acceptance;
- R13 Android Signing Acceptance;
- R13 Android Device Acceptance;
- R13 Google Play Readiness Acceptance;
- R13 Apple Xcode Acceptance;
- R13 Apple SwiftUI Scaffold Acceptance;
- R13 Apple Signing Archive Acceptance;
- R13 Apple XCTest Acceptance;
- R13 Integrated Release Readiness.

No success from another SHA is reusable as decision evidence.

## Required exact-head platform semantics

Android evidence must prove the canonical governed API 36 build/package path with AAB+APK state and the accepted virtual Android runtime/device path. The integrated claim remains `android_device_scope=VIRTUAL` and `android_physical_device_claim=false`.

iOS evidence must prove the canonical hosted macOS Xcode/SwiftUI/XCTest simulator path. The integrated claim remains `ios_scope=SIMULATOR` and `apple_physical_device_claim=false`.

Core acceptance must also keep `live_store_query_attempted=false` and `production_signing_credential_used=false`. Account-free/store-free readiness cannot be edited into a live publication or production-signing claim.

## Evidence creation after candidate gates

After all candidate gates are successful:

1. record each required workflow name, unique Actions run ID and run number;
2. fetch and verify uploaded artifact identities/digests for Android Build, Android Device and Apple XCTest;
3. generate `docs/roadmap/R13_17_CI_ACCEPTANCE.json` with the exact technical candidate source SHA;
4. update this document with the accepted candidate/run/artifact authority and truthful manual state;
5. end-synchronize `R13_PLAN.md` and continuity;
6. generate `docs/roadmap/R13_INTEGRATED_ACCEPTANCE.json`, binding all R13.1–R13.17 acceptance documents, continuity, the CI manifest and the accepted R12 integrated digest;
7. verify the report against repository bytes and its JSON Schema;
8. rerun all required exact-head gates on the resulting final documentation/evidence head before merge with `expected_head_sha`.

The canonical report must have `status=pass`, `blockers=[]` and a stable semantic digest. `generated_at` is non-semantic; changing any bound source byte, source SHA, run/artifact identity, claim, manual state, status or blocker changes or invalidates the semantic authority.

## Focused adversarial requirements

The R13.17 tests must demonstrate failure for acceptance/continuity/prior-phase/CI substitution, report/CI digest forgery, duplicate run IDs, wrong artifact/workflow binding, path traversal, virtual-to-physical DeviceLab proof escalation and KodeRelease evidence substitution. Full Python Core must rerun prior R13 focused suites so Gradle/Xcode/signing/store-policy/diagnostics attack coverage remains in the integrated decision set.

## Anti-circular invariant

`docs/roadmap/R13_INTEGRATED_ACCEPTANCE.json` is excluded from its own source bindings. Neither this pending document nor the integrated workflow may manufacture a checked-in PASS report before the technical candidate has independently passed its gates.

## Post-merge closure

R13 is not `COMPLETE + NORMALIZED` immediately after the implementation/evidence PR merges. Exactly one post-merge branch may modify only `docs/continuity/KODEPOIA_CONTINUITY.md`; that normalization head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke and merge with `expected_head_sha`. Only then is R14 planning authorized.

## Current decision

**PENDING.** No accepted R13.17 technical candidate, CI manifest, canonical integrated report, final semantic digest or implementation PR merge is recorded yet. Manual remains **CONDITIONAL / NOT TRIGGERED** because the frozen core claims are expected to be demonstrable in hosted CI without a physical device, live store account or production signing credential.
