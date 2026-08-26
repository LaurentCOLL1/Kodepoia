# R13.11 — iOS Simulator/XCTest, device/TestFlight evidence adapter — Acceptance

## Status

Subdivision status: **IN_PROGRESS**. This document defines the acceptance contract; it does not predeclare PASS.

Manual state: **CONDITIONAL / NOT TRIGGERED**.

## Frozen core acceptance claim

R13.11 is accepted only when one exact source head proves all of the following:

1. the canonical accepted R13.9 SwiftUI fixture is rendered from the shared application model;
2. the R13.11 deterministic XCTest overlay adds a valid application-hosted test target without arbitrary project/settings injection;
3. an actual iOS Simulator available on hosted `macos-26` is selected from structured `simctl` evidence;
4. `xcodebuild test` executes the canonical XCTest suite against that simulator with signing disabled;
5. the requested `.xcresult` bundle exists and `xcresulttool get test-results summary` reports PASS with at least the two canonical tests and zero failures;
6. durable evidence binds exact source SHA, XCTest plan digest, R13.9 workspace manifest digest, shared app-model digest, hashed simulator identity and result-bundle content digest;
7. simulator evidence explicitly reports `physical_device_capability_proven=false` and cannot be upgraded into physical-device proof;
8. the optional TestFlight/App Store Connect capability is `UNAVAILABLE` in core acceptance because no live credential is supplied, with `live_query_attempted=false` and `remote_build_state_proven=false`;
9. no production signing/account credential is used or persisted.

## Explicit non-claims

R13.11 core acceptance does **not** claim:

- physical-device sensors, radios, thermal/performance or hardware-only behavior;
- device/distribution signing;
- Apple Developer membership readiness;
- App Store Connect authentication;
- upload or processing of a build in App Store Connect;
- TestFlight beta-group/tester enrollment or installation;
- App Store review/acceptance.

Those states are separate conditional evidence. Missing live-account capability must remain `UNAVAILABLE`, never synthetic PASS.

## Focused deterministic/adversarial tests

`tests/test_r13_11_apple_testing.py` must pass and cover at minimum:

- strict `simctl` JSON validation;
- deterministic available-simulator selection;
- raw simulator UDID excluded from durable public evidence;
- malformed/unavailable target rejection;
- bounded/truthful `xcresulttool` summary parsing;
- passing summary cannot contain failures;
- TestFlight without credentials becomes `UNAVAILABLE`, not PASS;
- credential reference alone becomes only `READY_TO_QUERY`, never remote proof;
- simulator evidence schema cannot claim physical-device capability;
- deterministic R13.9 XCTest overlay and shared-model digest binding;
- fail-closed PBX renderer drift handling;
- typed Xcode/simctl/xcresult argv;
- raw destination, scheme injection and staging-path escape rejection.

## Hosted macOS tool acceptance

Workflow: `.github/workflows/r13-apple-xctest-acceptance.yml`.

It must execute on `macos-26` and:

1. checkout the exact evidence head;
2. install the repository dev dependencies under Python 3.12;
3. run the focused R13.11 tests;
4. run `scripts/r13_11_apple_xctest_acceptance.py` using the exact head SHA;
5. verify the resulting JSON is simulator-only, passed, unsigned and TestFlight-unavailable;
6. upload both the structured JSON and native `.xcresult` bundle under an exact-head artifact name.

The native `.xcresult` is evidence data, not a checked-in PASS artifact.

## Exact-head required gates

The accepted technical candidate must have, on the **same exact SHA**:

- R0 Repository Guard — SUCCESS;
- Python Core — SUCCESS;
- KodeStudio UI Smoke — SUCCESS;
- R13 Apple Xcode Acceptance — SUCCESS;
- R13 Apple SwiftUI Scaffold Acceptance — SUCCESS;
- R13 Apple Signing Archive Acceptance — SUCCESS;
- R13 Apple XCTest Acceptance — SUCCESS.

Any byte change after those results creates a new candidate and invalidates them for the merge decision.

## End synchronization and merge

After a technical candidate passes the gates above:

1. update `R13_PLAN.md` and continuity in the same work cycle so R13.11 becomes `COMPLETE` and R13.12 remains `PLANNED`;
2. record the accepted exact-head run identities and hosted XCTest artifact digest;
3. rerun all required gates on the new end-synchronized exact head;
4. merge the implementation PR using `expected_head_sha` only if every required gate is SUCCESS;
5. create exactly one continuity-only post-merge normalization branch/PR;
6. require fresh exact-head R0 + Python Core + KodeStudio UI Smoke on that normalization head;
7. merge normalization with `expected_head_sha`;
8. only then may R13.12 start.

## Manual gate

**CONDITIONAL / NOT TRIGGERED** unless hosted CI proves unable to establish a frozen required R13.11 claim that specifically requires a physical Apple device or live TestFlight state. If triggered, stop before R13.12 and provide bounded prerequisites/actions/evidence instructions. Never request passwords, private keys or tokens in chat.
