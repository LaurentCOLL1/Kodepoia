# R13.8 — Acceptance

## Scope

R13.8 accepts only the Apple **host/toolchain capability bridge and execution boundary**. It does not claim application signing, provisioning, archive/export, TestFlight submission, App Store review, publication or physical-device behavior.

## Required implementation artifacts

- `src/kodepoia/mobile/apple_xcode.py`
- R13.8 Apple additions to `src/kodepoia/mobile/boundary.py`
- public exports in `src/kodepoia/mobile/__init__.py`
- `schemas/r13/apple-xcode-capability.schema.json`
- `tests/test_r13_8_apple_xcode_bridge.py`
- `scripts/r13_8_apple_xcode_acceptance.py`
- `.github/workflows/r13-apple-xcode-acceptance.yml`
- this acceptance document and `R13_8_DESIGN.md`

## Focused deterministic acceptance

The focused tests must prove:

1. strict parsing of `xcodebuild -version` and SDK version output;
2. stable Xcode 26 + iOS/iPadOS 26+ SDK evidence can produce `PRODUCTION_UPLOAD_TOOLCHAIN_READY` **only as a toolchain claim**;
3. recognized Xcode 27 beta evidence can produce `TESTFLIGHT_BETA_TOOLCHAIN_READY` but never stable production capability;
4. an unrecognized future Xcode major fails closed until dated policy evidence is refreshed;
5. stale policy cannot claim current production/TestFlight readiness;
6. missing iOS simulator runtime/device does not produce `AVAILABLE`;
7. tool architecture substitution is rejected;
8. executable-name substitution is rejected;
9. SDK injection is rejected;
10. raw destination/build-setting content cannot be supplied through the bounded scheme API;
11. executor contract is bounded, non-interactive and secret-free;
12. report ordering/digest is deterministic;
13. durable schema validates canonical evidence and rejects unexpected account/signing fields.

## Real hosted macOS acceptance

Workflow: `R13 Apple Xcode Acceptance`.

Canonical runner: `macos-26`.

The workflow must:

- checkout the exact PR/source SHA;
- install Kodepoia test dependencies without installing Xcode itself;
- run the focused R13.8 tests;
- resolve and boundary-validate host `xcodebuild` and `xcrun`;
- execute only fixed probe/list operations;
- collect actual Xcode version/build, `iphoneos` SDK, `iphonesimulator` SDK, iOS simulator runtimes and available simulator-device count;
- bind public executable SHA-256 identities and host architecture;
- classify stable/beta state using the dated policy snapshot;
- validate `schemas/r13/apple-xcode-capability.schema.json`;
- verify exact `source_sha`;
- upload one exact-head JSON artifact.

For the canonical stable hosted acceptance, the evidence must satisfy:

- `policy_freshness == CURRENT`;
- `channel == STABLE`;
- `capability_state == AVAILABLE`;
- `readiness == PRODUCTION_UPLOAD_TOOLCHAIN_READY`;
- `production_upload_toolchain_capable == true`;
- `testflight_beta_toolchain_capable == false`;
- `physical_device_capability_proven == false`;
- `blockers == []`.

If the hosted runner instead exposes a beta/future toolchain that cannot truthfully meet the frozen canonical stable claim, that run is not accepted as production-toolchain evidence. Do not rewrite the classifier to force PASS.

## Exact-head subdivision gates

An R13.8 candidate is decision-capable only when the same exact SHA has:

- R0 Repository Guard — SUCCESS;
- Python Core — SUCCESS;
- KodeStudio UI Smoke — SUCCESS;
- R13 Apple Xcode Acceptance — SUCCESS.

Any byte change after those gates requires fresh exact-head runs.

## End synchronization and merge

After an accepted technical candidate:

1. update `R13_PLAN.md` and continuity in the same end-sync work cycle;
2. mark R13.8 `COMPLETE`; keep R13.9 `PLANNED / NOT STARTED`;
3. record exact accepted run IDs and truthful manual state;
4. run fresh exact-head R0 + Python + UI + Apple/Xcode acceptance on the end-synchronized head;
5. merge the implementation PR with `expected_head_sha`;
6. create exactly one continuity-only normalization branch from the implementation merge;
7. prove only `docs/continuity/KODEPOIA_CONTINUITY.md` changed;
8. pass exact-head R0 + Python + UI;
9. merge normalization;
10. only normalized `main` may authorize R13.9.

## Manual gate

Initial state: **CONDITIONAL / NOT TRIGGERED**.

A manual gate is triggered only if accepted hosted macOS CI cannot prove a frozen R13.8 Xcode/macOS semantic. Production Apple credentials, certificates, private keys, provisioning profiles, App Store Connect access and physical devices are not required for core R13.8 acceptance.
