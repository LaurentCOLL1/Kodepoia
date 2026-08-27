# R13.17 — Integrated release-readiness design

**Status:** IMPLEMENTATION CANDIDATE DESIGN — no integrated PASS is recorded by this document.  
**Authorized base:** normalized `main` `b202af1b4d6fd8d34e351c710db4c0ec719dd8f4`.  
**Branch:** `r13/17-integrated-release-readiness`.  
**Manual:** CONDITIONAL / NOT TRIGGERED at implementation start.

## Objective

Close R13 with one anti-circular, adversarial, phase-level authority spanning the already accepted R13.1–R13.16 capabilities without replacing their narrower evidence. The final report must prove that Android and iOS mobile intent, scaffold/build/test/package state, signing state, DeviceLab routing, store compliance, release authority and diagnostics remain mutually bound and fail closed under substitution.

## Anti-circular evidence sequence

1. Commit the R13.17 model, schemas, builders, focused tests, this design, the pending acceptance contract and the integrated hosted workflow. **Do not create** `docs/roadmap/R13_INTEGRATED_ACCEPTANCE.json` or `docs/roadmap/R13_17_CI_ACCEPTANCE.json` in the technical implementation candidate.
2. Open the implementation PR and freeze one exact technical candidate SHA.
3. On that exact SHA require SUCCESS for all standard and R13 platform gates listed below. Existing workflows must independently re-prove their own seams; the new integrated workflow is additive, not a replacement.
4. Inspect the Android build, Android device and Apple XCTest uploaded artifacts and bind their immutable GitHub artifact IDs/names/archive SHA-256 values.
5. Only after steps 2–4 are satisfied, generate `R13_17_CI_ACCEPTANCE.json` with `scripts/r13_17_build_ci_evidence.py`. Its semantic digest excludes only `generated_at`.
6. End-synchronize `R13_17_ACCEPTANCE.md`, `R13_PLAN.md` and continuity, then generate `R13_INTEGRATED_ACCEPTANCE.json` with `scripts/r13_17_build_integrated_report.py`. The report is explicitly excluded from its own source bindings.
7. Because those evidence/document bytes create a new head, run all required exact-head gates again before merge with `expected_head_sha`.
8. After the implementation/evidence merge, perform exactly one continuity-only normalization, run fresh R0 + full Python Core + KodeStudio UI Smoke on that normalization head, and merge it. Only that normalized merge makes R13 `COMPLETE + NORMALIZED` and authorizes R14 planning.

## Canonical CI authority

`R13_17_CI_ACCEPTANCE.json` requires exactly these successful workflow identities, in order:

1. R0 Repository Guard
2. Python Core
3. KodeStudio UI Smoke
4. R13 Android Build Acceptance
5. R13 Android Signing Acceptance
6. R13 Android Device Acceptance
7. R13 Google Play Readiness Acceptance
8. R13 Apple Xcode Acceptance
9. R13 Apple SwiftUI Scaffold Acceptance
10. R13 Apple Signing Archive Acceptance
11. R13 Apple XCTest Acceptance
12. R13 Integrated Release Readiness

Run IDs must be unique and all refer to the same immutable implementation source SHA. The CI authority additionally binds uploaded archive digests for Android Build, Android Device and Apple XCTest. A workflow name, run ID, artifact ID/name/digest or source-SHA substitution invalidates the evidence.

## Deliberately bounded phase claims

The core integrated PASS is allowed to claim only the semantics actually demonstrated by accepted hosted CI:

- Android hosted build is proven at target API 36 with both AAB and APK state.
- Android runtime evidence is **VIRTUAL**, never physical-device proof.
- iOS hosted build/test is **SIMULATOR** evidence, never physical-device proof.
- no live Play Console, App Store Connect or TestFlight query is part of the core PASS;
- no production signing/provisioning credential is used or claimed;
- actual public store publication remains user-controlled and outside core acceptance.

Any attempt to change those limitations in the CI evidence fails closed at schema/model validation. Google Play's current ordinary new-app/update target requirement becomes API 36 on 2026-08-31, and Apple's current App Store Connect upload minimum has required Xcode 26 with platform SDK 26+ since 2026-04-28; these remain dated provider evidence rather than architecture constants.

Official sources checked for this R13.17 design cycle:

- https://support.google.com/googleplay/android-developer/answer/11926878
- https://developer.android.com/google/play/requirements/target-sdk
- https://developer.apple.com/news/upcoming-requirements/

## Final report bindings

`R13_INTEGRATED_ACCEPTANCE.json` binds:

- immutable R13.17 implementation `source_sha`;
- `docs/continuity/KODEPOIA_CONTINUITY.md` by bytes + SHA-256;
- all 17 `R13_<n>_ACCEPTANCE.md` documents, ordered R13.1 through R13.17, by bytes + SHA-256;
- `R13_17_CI_ACCEPTANCE.json` by file SHA-256/size plus its semantic digest and source SHA;
- prior `R12_INTEGRATED_ACCEPTANCE.json` by file identity and accepted semantic digest `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`;
- truthful conditional manual state;
- `status=pass`, `blockers=[]` only after all required evidence exists;
- a stable canonical semantic SHA-256 that excludes only the non-semantic generation timestamp.

The final report is never included in its own binding set.

## Adversarial hardening

R13.17 adds focused cross-phase tests and relies on full Python Core to rerun every previously accepted R13 subdivision test. The integrated layer specifically rejects:

- acceptance/continuity/prior-phase/CI file replacement;
- semantic-digest forgery and timestamp confusion;
- duplicate/replayed workflow run IDs;
- mismatched workflow-to-artifact identity and artifact digest replacement;
- repository path traversal in evidence sources;
- virtual/simulator evidence upgraded into physical-device claims;
- live-store or production-signing claim escalation;
- DeviceLab artifact/matrix/proof substitution;
- KodeRelease evidence-set substitution.

The existing R13.1–R13.16 focused suites continue to cover identifier/path/template, Gradle/Xcode-setting, signing-reference, device identifier, store-track/policy, redaction and diagnostics attacks. Full Python Core is therefore part of the integrated gate rather than a replaceable smoke subset.

## Hosted integrated workflow

`.github/workflows/r13-integrated-release-readiness.yml` has two real jobs on the exact source SHA:

- Ubuntu: focused R13.17 tests, accepted JDK/Gradle/Android SDK setup, governed Android staging, API 36 release AAB + debug APK + unit tests, collection and exact-head verification.
- `macos-26`: focused R13.17 tests plus the canonical real iOS Simulator XCTest collector, with explicit simulator-only/no-signing/no-live-TestFlight assertions.

The workflow uploads evidence but cannot write the canonical repository PASS report.

## Manual gate

Manual remains **CONDITIONAL / NOT TRIGGERED** while the frozen DoD is satisfied by hosted Android emulator/build and hosted macOS simulator/XCTest evidence. If a frozen claim is discovered that genuinely requires a physical device, live store/account operation, production signing/provisioning secret or unavailable macOS runtime semantic, freeze the exact candidate, set `MANUAL_REQUIRED`, provide one bounded collector and stop before R14. Never place passwords, tokens, private keys, keystores or provisioning secrets in chat, source, argv, logs or evidence.
