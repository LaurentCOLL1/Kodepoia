# R13.17 — Integrated release-readiness acceptance

**Status:** COMPLETE — ACCEPTED TECHNICAL SOURCE; FINAL DOCUMENTATION/EVIDENCE RE-GATES PENDING
**Manual:** CONDITIONAL / NOT TRIGGERED
**Integrated PASS report:** AUTHORIZED AFTER THIS END-SYNC
**CI PASS manifest:** RECORDED

## Scope

Adversarial hardening plus anti-circular Android/iOS phase-level release-readiness acceptance for the frozen R13 Mobile / Platform / Release capability.

Normalized base: `b202af1b4d6fd8d34e351c710db4c0ec719dd8f4`.
Dedicated branch: `r13/17-integrated-release-readiness`.
Manual intervention: **CONDITIONAL / NOT TRIGGERED**.

The conditional manual trigger was evaluated from the frozen phase Definition of Done and did **not** trigger. Hosted CI proved the required Android API 36 build/package/runtime path and hosted macOS proved the required Xcode/SwiftUI/XCTest simulator path. R13 does not claim Android or Apple physical-device capability, live Play/App Store/TestFlight state, production signing/provisioning credentials, or automatic public publication.

## Accepted immutable technical source

Accepted R13.17 implementation SHA: **`56f829f4395138bf90a1a8e0003bff95b67dd878`**.

The predecessor **`e6d7cb3768d80944692596ef6705f3f95a24c8da`** is rejected and none of its decision evidence is reusable. Its Android integrated build and collection succeeded, but the workflow assertion read `target_sdk` at the wrong JSON level. The correction changed exactly one workflow line to read `request.target_sdk`; all required gates were restarted on the new source SHA.

## Exact-head implementation gates

All required gates completed **SUCCESS** on exactly `56f829f4395138bf90a1a8e0003bff95b67dd878`:

- R0 Repository Guard #1731 / run `33118952255`;
- Python Core #1705 / run `33118952290`;
- KodeStudio UI Smoke #1672 / run `33118952751`;
- R13 Android Build Acceptance #301 / run `33118952332`;
- R13 Android Signing Acceptance #254 / run `33118952213`;
- R13 Android Device Acceptance #239 / run `33118952330`;
- R13 Google Play Readiness Acceptance #222 / run `33118952293`;
- R13 Apple Xcode Acceptance #205 / run `33118952217`;
- R13 Apple SwiftUI Scaffold Acceptance #176 / run `33118953127`;
- R13 Apple Signing Archive Acceptance #151 / run `33118952223`;
- R13 Apple XCTest Acceptance #131 / run `33118952229`;
- R13 Integrated Release Readiness #4 / run `33118952219`.

The integrated workflow itself passed both `r13-integrated-android-ubuntu-latest` and `r13-integrated-apple-macos-26`, including the focused R13.17 adversarial suite, canonical Android build/collection/exact-head assertion, and canonical iOS Simulator XCTest/exact-head assertions.

## Immutable platform artifact authority

The accepted CI manifest binds these GitHub Actions archive identities to the same technical source SHA:

- Android Build Linux artifact `9665811449`, name `r13-4-android-Linux-56f829f4395138bf90a1a8e0003bff95b67dd878`, archive SHA-256 `4675ea1f8c1adcfc6821b66dcc88a4dec5cba1779dbef45d3d729856fc63dc8d`;
- Android Device artifact `9665845148`, name `r13-6-android-device-56f829f4395138bf90a1a8e0003bff95b67dd878`, archive SHA-256 `eb7aa4f43b19a519e85e93e288bc349d41ba2c9369e4c529b73460690081517d`;
- Apple XCTest artifact `9665853659`, name `r13-11-apple-xctest-macOS-56f829f4395138bf90a1a8e0003bff95b67dd878`, archive SHA-256 `f40307954d44d38e80099128b43b5334c8079a72142bfada0d445eb66558cb1b`.

Checked-in CI authority: `docs/roadmap/R13_17_CI_ACCEPTANCE.json`.
Semantic CI digest: **`23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`**.

## Bounded accepted claims

The core PASS is deliberately limited to what the accepted hosted evidence proves:

- `android_hosted_build=true`;
- `android_target_api=36`;
- `android_package_kinds=["aab","apk"]`;
- `android_device_scope="VIRTUAL"` and `android_physical_device_claim=false`;
- `ios_hosted_build_test=true`;
- `ios_scope="SIMULATOR"` and `apple_physical_device_claim=false`;
- `live_store_query_attempted=false`;
- `production_signing_credential_used=false`;
- manual state `conditional_not_triggered`;
- `status=pass`, `blockers=[]` in the accepted CI authority.

No account-free or simulator/virtual evidence may be upgraded into physical-device, live-store, public-release or production-signing proof.

## Anti-circular evidence ordering

1. Freeze the implementation source while both canonical R13 PASS JSON files are absent.
2. Require all 12 exact-head candidate gates on that source SHA.
3. Reject any failed predecessor and restart every decision gate after a source-byte change.
4. Bind the exact Android Build, Android Device and Apple XCTest archive identities/digests.
5. Generate `R13_17_CI_ACCEPTANCE.json` from only that accepted source/run/artifact set.
6. End-synchronize this acceptance, `R13_PLAN.md` and continuity so R13.17 becomes COMPLETE before report generation.
7. Generate `R13_INTEGRATED_ACCEPTANCE.json` with `scripts/r13_17_build_integrated_report.py --source-sha 56f829f4395138bf90a1a8e0003bff95b67dd878`; the report is excluded from its own bindings.
8. Validate the canonical report against current repository bytes and schema/model invariants.
9. Freeze the resulting documentation/evidence head and rerun the same required exact-head gate family before PR #253 may merge with `expected_head_sha`.
10. After merge, create exactly one continuity-only R13 normalization branch, run fresh R0 + full Python Core + KodeStudio UI Smoke, and merge with expected SHA.
11. Only that normalization merge makes R13 **COMPLETE + NORMALIZED** and authorizes R14 planning.

## Evidence state at end-sync

Start-of-subdivision synchronization: **DONE**.
Accepted technical source: **`56f829f4395138bf90a1a8e0003bff95b67dd878`**.
Implementation candidate gates: **12/12 SUCCESS**.
Manual state: **CONDITIONAL / NOT TRIGGERED (`conditional_not_triggered`)**.
CI manifest: **RECORDED / PASS** with semantic digest **`23d3cf13b92f4a1e172c7611f69cba90ea9259c6914051ea444d83d505c6ea6b`**.
End-of-subdivision plan/continuity synchronization: **DONE in this evidence cycle; R13.17 is COMPLETE**.
Canonical integrated report: **generated only after these bound bytes are finalized**.
Final documentation/evidence exact-head gates and merge results: **must be recorded in PR metadata and then in the single post-merge continuity normalization, not by mutating this report-bound acceptance**.

## Failure policy

Any failed final documentation/evidence gate rejects that exact final head. Correct only R13.17 evidence/documentation, freeze a new final head and restart every required final gate. Missing/stale runs, substituted artifacts, forged semantic digests, mutated bound files, physical/live-store claim escalation or prior R12 evidence substitution never manufacture PASS.
