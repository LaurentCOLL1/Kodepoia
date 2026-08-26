# R13.11 — iOS Simulator/XCTest, device/TestFlight evidence adapter — Acceptance

## Status

Subdivision status: **COMPLETE** for end synchronization. R13.12 remains **PLANNED / NOT STARTED** until R13.11 implementation merge and its single continuity-only normalization are accepted.

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

## Accepted technical candidate

Accepted exact-head technical candidate: **`c90a5804473dfbc7ed5da9b739dfd345dfa3a598`**.

Required gates on that exact SHA all completed **SUCCESS**:

- R0 Repository Guard #1687 / `33011155725`;
- Python Core #1661 / `33011155704`;
- KodeStudio UI Smoke #1628 / `33011155662`;
- R13 Apple Xcode Acceptance #78 / `33011155694`;
- R13 Apple SwiftUI Scaffold Acceptance #49 / `33011155773`;
- R13 Apple Signing Archive Acceptance #24 / `33011155762`;
- R13 Apple XCTest Acceptance #4 / `33011155751`.

Apple XCTest #4 ran job `98317467434` on hosted `macos-26`, passed all 8 focused R13.11 Python tests, executed the canonical simulator XCTest acceptance, and produced structured evidence with `scope=SIMULATOR`, `summary.result=PASSED`, `total_test_count=2`, `passed_tests=2`, `failed_tests=0`, `physical_device_capability_proven=false`, `signing_credential_used=false`, `blockers=[]`, and TestFlight `state=UNAVAILABLE`, `live_query_attempted=false`, `remote_build_state_proven=false` because App Store Connect credentials were absent.

The selected hosted simulator was `iPhone Air` on iOS `26.5`; durable evidence stores a hashed device identity rather than the raw simulator UDID. The run uploaded exact-head artifact **`r13-11-apple-xctest-macOS-c90a5804473dfbc7ed5da9b739dfd345dfa3a598`**, artifact ID **`9622789696`**, ZIP SHA-256 **`2b35b9470e7af218688f7b805cc2dabbd3ad5a6f012dcfa38df54bd5276c2b28`**. The evidence also binds app-model digest `3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0`, XCTest-plan digest `2cd0ca39fcdd8fef33cdc1c5e49c3210e569c234dcf5d62764bf04dfe9009137`, workspace-manifest digest `6403b900068c70e59a985e351ac20ef5856f599b65027c1fa1ad2dc242112835`, and `.xcresult` tree digest `4bcb4519d3461b07c652961130167aa08de9ef3b0c5a978e5ffc68efddc9444d`.

Rejected predecessor **`88f58c798cd1329fddb3df131ae622311fd31ec4`** is not reusable: its focused R13.11 test run failed because duplicate-overlay detection happened after canonical-PBX cardinality checks. The corrected candidate checks the already-present XCTest target/scheme marker first and then applies the fail-closed canonical drift checks.

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

The technical candidate has passed. This end-synchronization marks R13.11 `COMPLETE` while R13.12 remains `PLANNED` and records the accepted candidate/run/artifact identities above.

After this documentation change:

1. rerun all seven required gates on the new end-synchronized exact head;
2. merge implementation PR #241 using `expected_head_sha` only if every required gate is SUCCESS;
3. create exactly one continuity-only post-merge normalization branch/PR;
4. require fresh exact-head R0 + Python Core + KodeStudio UI Smoke on that normalization head;
5. merge normalization with `expected_head_sha`;
6. only then may R13.12 start.

## Manual gate

**CONDITIONAL / NOT TRIGGERED.** Hosted CI established every frozen required R13.11 core claim. A physical Apple device and live TestFlight/App Store Connect state remain explicit non-claims, so no user intervention is required for R13.11 acceptance. Never request passwords, private keys or tokens in chat.
